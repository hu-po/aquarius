import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict
import logging
from zoneinfo import ZoneInfo, available_timezones
import cv2
from pydantic import BaseModel, Field
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from contextlib import contextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from functools import lru_cache
import json

from .robot import RobotClient
from .models import (
    get_db, Image, Reading, AquariumStatus,
    DBImage, DBReading, DBAIAnalysis, DBLife, LifeBase, Life,
    RobotCommand, Trajectory
)
from .camera import CameraManager
from .ai import ENABLED_MODELS, async_inference

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if os.getenv('LOG_LEVEL', 'INFO').upper() == 'DEBUG' else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s - [%(filename)s:%(lineno)d]'
)

# Set debug level for all pyaquarius modules
log = logging.getLogger(__name__)
if os.getenv('LOG_LEVEL', 'INFO').upper() == 'DEBUG':
    for logger_name in ['pyaquarius', 'uvicorn', 'fastapi']:
        logging.getLogger(logger_name).setLevel(logging.DEBUG)

# CORS settings
CORS_ORIGINS = os.getenv('CORS_ORIGINS', '')
CORS_MAX_AGE = int(os.getenv('CORS_MAX_AGE', '3600'))

# Tank parameters
TANK_TEMP_MIN = float(os.getenv('TANK_TEMP_MIN', '75.0'))
TANK_TEMP_MAX = float(os.getenv('TANK_TEMP_MAX', '82.0'))

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
    DBImage, DBReading, DBAIAnalysis, DBLife, LifeBase, Life,
    RobotCommand
)

from .ai import ENABLED_MODELS
from .camera import CameraManager, CAMERA_IMG_TYPE, CAMERA_MAX_DIM
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

app = FastAPI(title="Aquarius Monitoring System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=CORS_MAX_AGE
)
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

camera_manager = CameraManager()
robot_client = RobotClient()

CAPTURE_INTERVAL = int(os.getenv('CAPTURE_INTERVAL', '10'))
CAPTURE_ENABLED = os.getenv('CAPTURE_ENABLED', 'true').lower() == 'true'

async def scheduled_capture():
    """Capture images from all active cameras on schedule."""
    log.debug("Starting scheduled capture")
    try:
        for device in camera_manager.devices.values():
            if device.is_active and not device.is_capturing:
                log.debug(f"Capturing from device {device.index}")
                was_streaming = device.is_streaming
                await device.stop_stream()
                result = await camera_manager.capture_image(device)
                if not result:
                    log.error(f"Scheduled capture failed for device {device.index}")
                else:
                    filepath, width, height, file_size = result
                    log.debug(f"Scheduled capture successful for device {device.index}")
                    with get_db_session() as db:
                        image = DBImage(
                            id=datetime.now(timezone.utc).isoformat(),
                            filepath=filepath,
                            width=width,
                            height=height,
                            file_size=file_size,
                            timestamp=datetime.now(timezone.utc),
                            device_index=device.index
                        )
                        db.add(image)
                        log.debug(f"Image record created in database with id {image.id}")
                
                # Restart stream if it was streaming before
                if was_streaming:
                    await device.start_stream()
                    log.debug(f"Restarted stream for device {device.index}")
    except Exception as e:
        log.error(f"Scheduled capture error: {str(e)}", exc_info=True)

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
    
    if CAPTURE_ENABLED:
        log.info(f"Starting scheduled capture every {CAPTURE_INTERVAL} seconds")
        scheduler = AsyncIOScheduler()
        scheduler.add_job(
            scheduled_capture,
            trigger=IntervalTrigger(seconds=CAPTURE_INTERVAL),
            id='scheduled_capture',
            replace_existing=True
        )
        scheduler.start()

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
    log.debug(f"Capture request received for device {device_index}")
    device = camera_manager.get_device(device_index)
    if not device:
        log.error(f"No camera found with index {device_index}")
        raise HTTPException(status_code=404, detail=f"Camera {device_index} not found")
    
    if not device.is_active:
        log.error(f"Camera {device_index} is not active")
        raise HTTPException(status_code=400, detail=f"Camera {device_index} is not active")
    
    try:
        was_streaming = device.is_streaming
        log.debug(f"Stopping stream on device {device_index}")
        await device.stop_stream()
        
        log.debug(f"Initiating capture on device {device_index}")
        result = await camera_manager.capture_image(device)
        if not result:
            log.error(f"Capture failed for device {device_index}")
            raise HTTPException(status_code=500, detail=f"Failed to capture from camera {device_index}")
            
        filepath, width, height, file_size = result
        log.debug(f"Capture successful - saving to database. Path: {filepath}")
        
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
            log.debug(f"Image record created in database with id {image.id}")
        
        if was_streaming:
            log.debug(f"Restarting stream for device {device_index}")
            await device.start_stream()
            
        return {"filepath": filepath}
        
    except Exception as e:
        log.error(f"Capture error: {str(e)}", exc_info=True)
        # Attempt to restart stream on error if it was streaming
        if was_streaming:
            await device.start_stream()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/{ai_models}/{analyses}")
async def analyze(ai_models: str, analyses: str):
    log.debug(f"Received analysis request - models: {ai_models}, analyses: {analyses}")
    try:
        ai_models_list = ai_models.split(',')
        analyses_list = analyses.split(',')
        
        log.debug(f"Validating requested models: {ai_models_list} against enabled models: {ENABLED_MODELS}")
        invalid_models = [m for m in ai_models_list if m not in ENABLED_MODELS]
        if invalid_models:
            log.error(f"Invalid AI models requested: {invalid_models}")
            raise HTTPException(status_code=400, detail=f"Invalid AI models: {', '.join(invalid_models)}")
            
        with get_db_session() as db:
            log.debug("Querying latest image for analysis")
            latest_image = db.query(DBImage).order_by(DBImage.timestamp.desc()).first()
            
            if not latest_image:
                log.error("No images available for analysis")
                raise HTTPException(status_code=404, detail="No images available")

            log.debug(f"Starting inference on image {latest_image.id}")
            ai_responses = await async_inference(ai_models_list, analyses_list, latest_image.filepath)
            
            log.debug("Processing AI responses")
            responses_with_errors = {
                key: {
                    'success': not isinstance(resp, Exception),
                    'result': str(resp) if not isinstance(resp, Exception) else None,
                    'error': str(resp) if isinstance(resp, Exception) else None
                }
                for key, resp in ai_responses.items()
            }
            
            successful = sum(1 for resp in responses_with_errors.values() if resp['success'])
            failed = sum(1 for resp in responses_with_errors.values() if not resp['success'])
            log.info(f"Analysis complete - {successful} successful, {failed} failed")
            
            return {
                "analysis": {
                    key: resp['result'] 
                    for key, resp in responses_with_errors.items() 
                    if resp['success']
                },
                "errors": {
                    key: resp['error']
                    for key, resp in responses_with_errors.items()
                    if not resp['success']
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Unexpected error in analysis: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/healthcheck")
async def health_check():
    return {"status": "ok"}

@app.get("/status")
async def get_status(db: Session = Depends(get_db)) -> AquariumStatus:
    latest_images = {}
    for device in camera_manager.devices.values():
        latest_image = db.query(DBImage)\
            .filter(DBImage.device_index == device.index)\
            .order_by(DBImage.timestamp.desc())\
            .first()
        if latest_image:
            latest_images[device.index] = Image.from_orm(latest_image)
    
    latest_reading = db.query(DBReading).order_by(DBReading.timestamp.desc()).first()
    
    alerts = []
    if latest_reading:
        if latest_reading.temperature > TANK_TEMP_MAX or latest_reading.temperature < TANK_TEMP_MIN:
            alerts.append(f"Temperature outside ideal range: {latest_reading.temperature}°F")

    return AquariumStatus(
        latest_images=latest_images,
        latest_reading=Reading.from_orm(latest_reading) if latest_reading else None,
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

@app.post("/robot/command")
async def send_robot_command(cmd: RobotCommand) -> Dict[str, str]:
    """Send command to robot client"""
    log.debug(f"Received robot command: {cmd.command}")
    try:
        if cmd.trajectory_name:
            response = robot_client.send_command(cmd.command, cmd.trajectory_name)
        else:
            response = robot_client.send_command(cmd.command)
        return {"message": f"Command sent: {response}"}
    except Exception as e:
        log.error(f"Failed to send robot command: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/robot/trajectories")
async def list_trajectories() -> Dict[str, List[Trajectory]]:
    """Get list of available trajectories"""
    try:
        trajectories = robot_client.get_trajectories()
        trajectory_models = [
            Trajectory(name=t['name'], modified=datetime.fromisoformat(t['modified'])) 
            for t in trajectories
        ]
        return {"trajectories": trajectory_models}
    except Exception as e:
        log.error(f"Failed to get trajectories: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get trajectories")

@app.get("/robot/trajectories/{name}")
async def load_trajectory(name: str) -> Dict[str, str]:
    """Load a saved trajectory"""
    try:
        response = robot_client.send_command('l', name)
        if 'error' in response.lower():
            raise ValueError(response)
        return {"message": f"Loaded trajectory: {name}"}
    except Exception as e:
        log.error(f"Failed to load trajectory {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/robot/trajectories/{name}")
async def save_trajectory(name: str) -> Dict[str, str]:
    """Save current trajectory"""
    try:
        response = robot_client.send_command('s', name)
        if 'error' in response.lower():
            raise ValueError(response)
        return {"message": f"Saved trajectory: {name}"}
    except Exception as e:
        log.error(f"Failed to save trajectory {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/robot/trajectories/{name}")
async def delete_trajectory(name: str) -> Dict[str, str]:
    """Delete a saved trajectory"""
    try:
        response = robot_client.send_command('d', name)
        if 'error' in response.lower():
            raise ValueError(response)
        return {"message": f"Deleted trajectory: {name}"}
    except Exception as e:
        log.error(f"Failed to delete trajectory {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/robot/trajectories/loop")
async def loop_trajectories(names: List[str]) -> Dict[str, str]:
    """Loop through multiple trajectories atomically"""
    try:
        for name in names:
            await load_trajectory(name)
            await send_robot_command(RobotCommand(command='P'))
        return {"message": f"Looping trajectories: {', '.join(names)}"}
    except Exception as e:
        log.error(f"Failed to loop trajectories: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
