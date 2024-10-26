import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi import WebSocket
from sqlalchemy.orm import Session
from contextlib import contextmanager
from pyaquarius.vlms import caption
from pyaquarius.models import (
    get_db, Image, Reading, AquariumStatus,
    DBImage, DBReading, DBVLMDescription
)

from .camera import CameraManager
from .config import config


app = FastAPI(title="Aquarius Monitoring System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in config.CORS_ORIGINS.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=config.CORS_MAX_AGE,
)
app.mount("/images", StaticFiles(directory=config.IMAGES_DIR), name="images")

@contextmanager
def get_db_session():
    db = get_db()
    session = next(db)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

camera_manager = CameraManager()

@app.websocket("/ws/camera/{device_index}")
async def camera_websocket(websocket: WebSocket, device_index: int):
    """WebSocket endpoint for camera streaming."""
    stream = await camera_manager.get_stream(device_index)
    await stream.connect(websocket)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up camera streams on shutdown."""
    await camera_manager.stop_all()

@app.websocket("/ws/camera/{device_index}")
async def camera_websocket(websocket: WebSocket, device_index: int):
    """WebSocket endpoint for camera streaming."""
    stream = await camera_manager.get_stream(device_index)
    if stream:
        await stream.connect(websocket)
    else:
        await websocket.close(code=1008)  # Policy violation

@app.post("/capture/{device_index}")
async def capture_image(device_index: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)) -> Image:
    """Capture image endpoint."""
    timestamp = datetime.now(timezone.utc)
    filename = f"{timestamp.isoformat()}.{config.CAMERA_IMG_TYPE}"
    
    if not await camera_manager.save_frame(filename, device_index):
        raise HTTPException(
            status_code=500,
            detail=f"Failed to capture image from device {device_index}"
        )
    
    try:
        filepath = os.path.join(config.IMAGES_DIR, filename)
        db_image = DBImage(
            id=timestamp.isoformat(),
            filepath=filepath,
            width=config.CAMERA_MAX_DIM,
            height=config.CAMERA_MAX_DIM,
            file_size=os.path.getsize(filepath)
        )
        db.add(db_image)
        db.commit()
        background_tasks.add_task(analyze_image, db_image.id, filepath, db)
        return Image.from_orm(db_image)
    
    except Exception as e:
        db.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/devices")
async def list_camera_devices():
    """List all available camera devices."""
    try:
        devices = CameraManager.list_devices_info()
        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def analyze_image(image_id: str, image_path: str, db: Session):
    try:
        this_dir = os.path.dirname(os.path.realpath(__file__))
        prompt = open(os.path.join(this_dir, "prompts/vlm.txt")).read().strip()
        prompt += open(os.path.join(this_dir, "prompts/aquarium.txt")).read().strip()        
        start_time = datetime.now(timezone.utc)
        
        try:
            descriptions = await asyncio.wait_for(caption(image_path, prompt), timeout=config.VLM_API_TIMEOUT)
        except asyncio.TimeoutError:
            descriptions = {"error": "Analysis timeout"}
        except Exception as e:
            descriptions = {"error": f"Analysis failed: {str(e)}"}

        with get_db_session() as session:
            for vlm_name, description in descriptions.items():
                if vlm_name != "error":
                    vlm_desc = DBVLMDescription(
                        id=f"{datetime.now(timezone.utc).isoformat()}_{vlm_name}",
                        image_id=image_id,
                        vlm_name=vlm_name,
                        description=description,
                        prompt=prompt,
                        latency=(datetime.now(timezone.utc) - start_time).total_seconds()
                    )
                    session.add(vlm_desc)
                    concerns = extract_concerns(description)
                    if concerns:
                        vlm_desc.concerns_detected = concerns
    except Exception as e:
        print(f"Failed to analyze image: {e}")
        with get_db_session() as session:
            error_desc = DBVLMDescription(
                id=f"{datetime.now(timezone.utc).isoformat()}_error",
                image_id=image_id,
                vlm_name="system",
                description=f"Analysis failed: {str(e)}",
                prompt=prompt,
                latency=0
            )
            session.add(error_desc)

def extract_concerns(description: str) -> Optional[str]:
    if not description:
        return None
    concerns = []
    keywords = ["concern", "warning", "alert", "problem", "issue", "high", "low", "unsafe", "dangerous", "unhealthy"]
    for line in description.split('\n'):
        if any(keyword in line.lower() for keyword in keywords):
            concerns.append(line.strip())
    return "; ".join(concerns) if concerns else None

@app.get("/healthcheck")
async def health_check():
    return {"status": "ok"}

@app.get("/status")
async def get_status(db: Session = Depends(get_db)) -> AquariumStatus:
    latest_image = db.query(DBImage).order_by(DBImage.timestamp.desc()).first()
    latest_reading = db.query(DBReading).order_by(DBReading.timestamp.desc()).first()
    latest_descriptions = {}
    alerts = []
    if latest_image:
        descriptions = db.query(DBVLMDescription).filter(
            DBVLMDescription.image_id == latest_image.id
        ).all()
        for desc in descriptions:
            if desc.vlm_name != "system":
                latest_descriptions[desc.vlm_name] = desc.description
            if desc.concerns_detected:
                alerts.extend(desc.concerns_detected.split('; '))
    if latest_reading:
        if latest_reading.temperature > config.TANK_TEMP_MAX or latest_reading.temperature < config.TANK_TEMP_MIN:
            alerts.append(f"Temperature outside ideal range: {latest_reading.temperature}°F")
        if latest_reading.ph and (latest_reading.ph < config.TANK_PH_MIN or latest_reading.ph > config.TANK_PH_MAX):
            alerts.append(f"pH outside ideal range: {latest_reading.ph}")
        if latest_reading.ammonia and latest_reading.ammonia > config.TANK_AMMONIA_MAX:
            alerts.append(f"High ammonia level: {latest_reading.ammonia} ppm")
        if latest_reading.nitrite and latest_reading.nitrite > config.TANK_NITRITE_MAX:
            alerts.append(f"High nitrite level: {latest_reading.nitrite} ppm")
        if latest_reading.nitrate and latest_reading.nitrate > config.TANK_NITRATE_MAX:
            alerts.append(f"High nitrate level: {latest_reading.nitrate} ppm")
    return AquariumStatus(
        latest_image=Image.from_orm(latest_image) if latest_image else None,
        latest_reading=Reading.from_orm(latest_reading) if latest_reading else None,
        latest_descriptions=latest_descriptions,
        alerts=list(set(alerts))
    )

@app.get("/images")
async def list_images(limit: int = 10, offset: int = 0, db: Session = Depends(get_db)) -> List[Image]:
    images = db.query(DBImage).order_by(DBImage.timestamp.desc()).offset(offset).limit(limit).all()
    return [Image.from_orm(img) for img in images]

@app.get("/readings/history")
async def get_readings_history(hours: int = 24, db: Session = Depends(get_db)) -> List[Reading]:
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    readings = db.query(DBReading).filter(DBReading.timestamp >= since).order_by(DBReading.timestamp.asc()).all()
    return [Reading.from_orm(r) for r in readings]