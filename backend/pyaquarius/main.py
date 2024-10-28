import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging

# CORS settings
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '')
CORS_MAX_AGE = int(os.getenv('CORS_MAX_AGE', '3600'))

# Tank parameters
TANK_TEMP_MIN = float(os.getenv('TANK_TEMP_MIN', '75.0'))
TANK_TEMP_MAX = float(os.getenv('TANK_TEMP_MAX', '82.0'))
TANK_PH_MIN = float(os.getenv('TANK_PH_MIN', '6.5'))
TANK_PH_MAX = float(os.getenv('TANK_PH_MAX', '7.5'))
TANK_AMMONIA_MAX = float(os.getenv('TANK_AMMONIA_MAX', '0.25'))
TANK_NITRITE_MAX = float(os.getenv('TANK_NITRITE_MAX', '0.25'))
TANK_NITRATE_MAX = float(os.getenv('TANK_NITRATE_MAX', '20.0'))

# Image settings
IMAGES_DIR = os.getenv('IMAGES_DIR', 'data/images')

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import contextmanager
from pyaquarius.vlms import caption
from pyaquarius.models import (
    get_db, Image, Reading, AquariumStatus,
    DBImage, DBReading, DBVLMDescription
)

from .camera import CameraManager, CAMERA_IMG_TYPE, CAMERA_MAX_DIM

log = logging.getLogger(__name__)

app = FastAPI(title="Aquarius Monitoring System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

camera_manager = CameraManager()

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

@app.get("/camera/{device_index}/stream")
async def stream_camera(device_index: int):
    """Stream camera feed as MJPEG."""
    device = camera_manager.get_device(device_index)
    if not device:
        log.error(f"No camera found with index {device_index}. Available devices: {[d.path for d in camera_manager.devices]}")
        raise HTTPException(status_code=404, detail=f"Camera {device_index} not found. Available devices: {[d.path for d in camera_manager.devices]}")
        
    log.info(f"Streaming camera {device_index} from {device.path}")
    return StreamingResponse(
        content=camera_manager.generate_frames(device),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

@app.post("/capture/{device_index}")
async def capture_image(
    device_index: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> Image:
    """Capture and save an image."""
    timestamp = datetime.now(timezone.utc)
    filename = f"{timestamp.isoformat()}.{CAMERA_IMG_TYPE}"
    
    if not await camera_manager.capture_image(filename, device_index):
        raise HTTPException(status_code=500, detail="Failed to capture image")
    
    try:
        filepath = os.path.join(IMAGES_DIR, filename)
        db_image = DBImage(
            id=timestamp.isoformat(),
            filepath=filepath,
            width=CAMERA_MAX_DIM,
            height=CAMERA_MAX_DIM,
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
async def list_devices():
    """List available camera devices."""
    return [
        {
            "index": device.index,
            "name": device.name,
            "path": device.path,
            "width": device.width,
            "height": device.height
        }
        for device in camera_manager.devices
    ]

async def analyze_image(image_id: str, image_path: str, db: Session):
    try:
        this_dir = os.path.dirname(os.path.realpath(__file__))
        prompt = open(os.path.join(this_dir, "prompts/vlm.txt")).read().strip()
        prompt += open(os.path.join(this_dir, "prompts/aquarium.txt")).read().strip()        
        start_time = datetime.now(timezone.utc)
        
        try:
            descriptions = await asyncio.wait_for(caption(image_path, prompt), timeout=VLM_API_TIMEOUT)
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
        if latest_reading.temperature > TANK_TEMP_MAX or latest_reading.temperature < TANK_TEMP_MIN:
            alerts.append(f"Temperature outside ideal range: {latest_reading.temperature}°F")
        if latest_reading.ph and (latest_reading.ph < TANK_PH_MIN or latest_reading.ph > TANK_PH_MAX):
            alerts.append(f"pH outside ideal range: {latest_reading.ph}")
        if latest_reading.ammonia and latest_reading.ammonia > TANK_AMMONIA_MAX:
            alerts.append(f"High ammonia level: {latest_reading.ammonia} ppm")
        if latest_reading.nitrite and latest_reading.nitrite > TANK_NITRITE_MAX:
            alerts.append(f"High nitrite level: {latest_reading.nitrite} ppm")
        if latest_reading.nitrate and latest_reading.nitrate > TANK_NITRATE_MAX:
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
