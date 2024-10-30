import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging
from zoneinfo import ZoneInfo, available_timezones
import cv2

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
os.chmod(IMAGES_DIR, 0o755)  # Ensure directory is readable

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import contextmanager
from pyaquarius.ai import async_inference
from pyaquarius.models import (
    get_db, Image, Reading, AquariumStatus,
    DBImage, DBReading, DBAIAnalysis, DBLife, LifeBase, Life
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

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

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

@app.on_event("startup")
async def startup_event():
    await camera_manager.initialize()

@app.get("/devices")
async def get_devices():
    """List available camera devices."""
    return [{
        "index": device.index,
        "name": device.name,
        "path": device.path,
        "width": device.width,
        "height": device.height,
        "active": device.is_active
    } for device in camera_manager.devices.values()]

@app.get("/camera/{device_index}/stream")
async def stream_camera(device_index: int, request: Request):
    """Stream camera feed as MJPEG with proper cleanup."""
    device = camera_manager.get_device(device_index)
    if not device:
        log.error(f"No camera found with index {device_index}")
        raise HTTPException(status_code=404, detail=f"Camera {device_index} not found")
    
    async def cleanup(generator):
        try:
            async for frame in generator:
                if await request.is_disconnected():
                    log.info(f"Client disconnected from camera {device_index} stream")
                    break
                yield frame
        except Exception as e:
            log.error(f"Stream error: {str(e)}", exc_info=True)
        finally:
            log.info(f"Cleaning up camera {device_index} stream")
    
    return StreamingResponse(
        cleanup(camera_manager.generate_frames(device)),
        media_type='multipart/x-mixed-replace; boundary=frame'
    )

@app.post("/capture/{device_index}")
async def capture_image(device_index: int):
    """Capture image from specified camera."""
    device = camera_manager.get_device(device_index)
    if not device:
        raise HTTPException(status_code=404, detail=f"Camera {device_index} not found")
    
    if not device.is_active:
        raise HTTPException(status_code=400, detail=f"Camera {device_index} is not active")
    
    try:
        await device.stop_stream()
        result = await camera_manager.capture_image(device)
        if not result:
            raise HTTPException(status_code=500, detail=f"Failed to capture from camera {device_index}")
            
        filepath, width, height, file_size = result
        
        with get_db_session() as db:
            image = DBImage(
                id=datetime.now(timezone.utc).isoformat(),
                filepath=filepath,
                width=width,
                height=height,
                file_size=file_size,
                timestamp=datetime.now(timezone.utc),
                device_index=device_index
            )
            db.add(image)
        
        return {"filepath": filepath}
        
    except Exception as e:
        log.error(f"Capture error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
            
@app.post("/analyze/{ai_models}/{analyses}")
async def analyze(ai_models: str, analyses: str):
    """Analyze latest image."""
    try:
        with get_db_session() as db:
            latest_image = db.query(DBImage)\
                .order_by(DBImage.timestamp.desc())\
                .first()
            
            if not latest_image:
                raise HTTPException(status_code=404, detail="No images available for analysis")

            ai_models = ai_models.split(',')
            analyses = analyses.split(',')
            ai_responses = await async_inference(ai_models, analyses, latest_image.filepath)
            
            if ai_responses:
                for key, response in ai_responses.items():
                    if not isinstance(response, Exception):
                        ai_model, analysis = key.split('.')
                        ai_response = DBAIAnalysis(
                            id=datetime.now(timezone.utc).isoformat(),
                            image_id=latest_image.id,
                            response=response,
                            ai_model=ai_model,
                            analysis=analysis,
                            timestamp=datetime.now(timezone.utc),
                        )
                        db.add(ai_response)
            
            return {
                "analysis": {
                    key: resp for key, resp in ai_responses.items() 
                    if not isinstance(resp, Exception)
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Analysis error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthcheck")
async def health_check():
    return {"status": "ok"}

@app.get("/status")
async def get_status(db: Session = Depends(get_db)) -> AquariumStatus:
    # Get latest image for each device
    latest_images = {}
    for device in camera_manager.devices.values():
        latest_image = db.query(DBImage)\
            .filter(DBImage.device_index == device.index)\
            .order_by(DBImage.timestamp.desc())\
            .first()
        if latest_image:
            latest_images[device.index] = Image.from_orm(latest_image)
    
    latest_reading = db.query(DBReading).order_by(DBReading.timestamp.desc()).first()
    latest_responses = {}
    alerts = []
    
    # Get responses for the most recent image from any device
    if latest_images:
        most_recent_image = max(latest_images.values(), key=lambda x: x.timestamp)
        responses = db.query(DBAIAnalysis).filter(
            DBAIAnalysis.image_id == most_recent_image.id
        ).all()
        for desc in responses:
            if desc.ai_name != "system":
                latest_responses[desc.ai_name] = desc.response

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
        latest_images=latest_images,
        latest_reading=Reading.from_orm(latest_reading) if latest_reading else None,
        latest_responses=latest_responses,
        alerts=list(set(alerts)),
        timezone=validate_timezone(os.getenv('TANK_TIMEZONE', 'UTC'))
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

@app.get("/life")
async def get_life(db: Session = Depends(get_db)) -> List[Life]:
    """Get all life in the aquarium."""
    life = db.query(DBLife).order_by(DBLife.common_name).all()
    return [Life.from_orm(l) for l in life]

@app.post("/life")
async def add_life(life: LifeBase, db: Session = Depends(get_db)) -> Life:
    """Add new life to the aquarium."""
    db_life = DBLife(
        id=datetime.now(timezone.utc).isoformat(),
        **life.dict()
    )
    db.add(db_life)
    db.commit()
    return Life.from_orm(db_life)

@app.put("/life/{life_id}")
async def update_life(life_id: str, life: LifeBase, db: Session = Depends(get_db)) -> Life:
    """Update life details."""
    db_life = db.query(DBLife).filter(DBLife.id == life_id).first()
    if not db_life:
        raise HTTPException(status_code=404, detail="Life not found")
    for key, value in life.dict().items():
        setattr(db_life, key, value)
    db_life.last_seen_at = datetime.now(timezone.utc)
    db.commit()
    return Life.from_orm(db_life)

def validate_timezone(tz: str) -> str:
    try:
        ZoneInfo(tz)
        return tz
    except Exception:
        log.warning(f"Invalid timezone {tz}, falling back to UTC")
        return "UTC"
