import os
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
import logging
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
import asyncio

from .robot import RobotClient
from .models import (
    get_db, Image, Reading, AquariumStatus,
    DBImage, DBReading, DBAIAnalysis, DBLife, LifeBase, Life,
    RobotCommand, Trajectory, ScanState, AIAnalysis
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

# location
LOCATION = os.getenv('LOCATION', 'Unknown')
log.debug(f"Current location from env: {LOCATION}")
TIMEZONE = os.getenv('TIMEZONE', 'UTC')
log.debug(f"Current timezone from env: {TIMEZONE}")

# Tank parameters
TANK_TEMP_MIN = float(os.getenv('TANK_TEMP_MIN', '75.0'))
TANK_TEMP_MAX = float(os.getenv('TANK_TEMP_MAX', '82.0'))
log.debug(f"Tank temperature range: {TANK_TEMP_MIN}°F - {TANK_TEMP_MAX}°F")

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

SCAN_CAMERA_ID = int(os.getenv('SCAN_CAMERA_ID', '0'))
SCAN_INTERVAL = int(os.getenv('SCAN_INTERVAL', '10'))
SCAN_ENABLED = os.getenv('SCAN_ENABLED', 'false').lower() == 'true'
SCAN_TRAJECTORIES = os.getenv('SCAN_TRAJECTORIES', 'a,b,c,d').split(',')
SCAN_SLEEP_TIME = int(os.getenv('SCAN_SLEEP_TIME', '4'))

scheduler: Optional[AsyncIOScheduler] = None

async def scheduled_scan():
    """Run automated scan with configured parameters."""
    log.debug("Starting scheduled scan")
    try:
        await robot_scan(
            device_index=SCAN_CAMERA_ID,
            trajectories=SCAN_TRAJECTORIES
        )
    except Exception as e:
        log.error(f"Scheduled scan failed: {e}")

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
    """Initialize camera manager and scheduler on startup."""
    global scheduler
    await camera_manager.initialize()
    
    scheduler = AsyncIOScheduler()
    if SCAN_ENABLED:
        log.info(f"Starting scan every {SCAN_INTERVAL} seconds")
        scheduler.add_job(
            scheduled_scan,
            trigger=IntervalTrigger(seconds=SCAN_INTERVAL),
            id='scheduled_scan',
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
    device = camera_manager.get_device(device_index)
    if not device:
        log.error(f"No camera found with index {device_index}")
        raise HTTPException(status_code=404, detail=f"Camera {device_index} not found")
    
    headers = {
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
        'Expires': '0',
        'Connection': 'close',
    }
    
    await device.start_stream()
    
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
            await device.stop_stream()
    
    return StreamingResponse(
        cleanup(camera_manager.generate_frames(device)),
        media_type='multipart/x-mixed-replace; boundary=frame',
        headers=headers
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
        
        # Generate filename first
        image_id = datetime.now(timezone.utc).isoformat()
        filename = f"{image_id}.{CAMERA_IMG_TYPE}"
        
        log.debug(f"Initiating capture on device {device_index}")
        result = await camera_manager.capture_image(device, filename)
        if not result:
            log.error(f"Capture failed for device {device_index}")
            raise HTTPException(status_code=500, detail=f"Failed to capture from camera {device_index}")
            
        filepath, width, height, file_size = result
        log.debug(f"Capture successful - saving to database. Path: {filepath}")
        
        with get_db_session() as db:
            image = DBImage(
                id=image_id,
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
            
        return {"filepath": filepath, "image_id": image_id}
        
    except Exception as e:
        log.error(f"Capture error: {str(e)}", exc_info=True)
        if was_streaming:
            await device.start_stream()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analyze/{ai_models}/{analyses}")
async def analyze(ai_models: str, analyses: str, image_id: Optional[str] = None):
    ai_models_list = ai_models.split(',')
    analyses_list = analyses.split(',')
    
    log.debug(f"Received analysis request - models: {ai_models_list}, analyses: {analyses_list}, image_id: {image_id}")
    
    try:
        invalid_models = [m for m in ai_models_list if m not in ENABLED_MODELS]
        if invalid_models:
            log.error(f"Invalid AI models requested: {invalid_models}")
            raise HTTPException(status_code=400, detail=f"Invalid AI models: {', '.join(invalid_models)}")
            
        with get_db_session() as db:
            if image_id:
                log.debug(f"Querying image with id {image_id}")
                latest_image = db.query(DBImage).filter(DBImage.id == image_id).first()
                if not latest_image:
                    raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
            else:
                log.debug("Querying latest image for analysis")
                latest_image = db.query(DBImage).order_by(DBImage.timestamp.desc()).first()
                if not latest_image:
                    raise HTTPException(status_code=404, detail="No images available")
            
            log.debug(f"Using image {latest_image.id} for analysis")
            # TODO: pass in tank_id, as the first character of image_id
            ai_responses = await async_inference(ai_models_list, analyses_list, latest_image.filepath, tank_id=0)
            
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
        log.error(f"Analysis error: {str(e)}", exc_info=True)
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
        timezone=TIMEZONE,
        location=LOCATION,
        scan_enabled=SCAN_ENABLED
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
    life = db.query(DBLife).order_by(DBLife.last_seen_at.desc()).all()
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

@app.post("/robot/command")
async def send_command(command: RobotCommand) -> Dict[str, str]:
    """Send command to robot"""
    try:
        response = robot_client.send_command(command.command, command.trajectory_name)
        return {"message": response}
    except Exception as e:
        log.error(f"Failed to send command: {str(e)}")
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

@app.post("/robot/scan")
async def robot_scan(
    device_index: int,
    trajectories: List[str],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Execute robot trajectories while capturing and analyzing images."""
    results = []
    try:
        for trajectory in trajectories:
            robot_client.send_command('p', trajectory)
            await asyncio.sleep(SCAN_SLEEP_TIME)
            
            # Get tank_id from first character of trajectory name
            tank_id = int(trajectory[0]) if trajectory[0].isdigit() else 0
            
            # Capture image and get image_id
            capture_result = await capture_image(device_index)
            image_id = capture_result.get('image_id')
            
            robot_client.send_command('h')  # return home
            
            if not image_id:
                log.error(f"No image_id returned from capture for trajectory {trajectory}")
                continue
                
            if 'temp' in trajectory:
                ai_responses = await async_inference(
                    ENABLED_MODELS,
                    ['estimate_temperature'],
                    capture_result['filepath'],
                    tank_id=tank_id,
                    image_id=image_id
                )
            else:
                ai_responses = await async_inference(
                    ENABLED_MODELS,
                    ['identify_life'],
                    capture_result['filepath'],
                    tank_id=tank_id,
                    image_id=image_id
                )
                
            results.append({
                'trajectory': trajectory,
                'image_id': image_id,
                'filepath': capture_result['filepath'],
                'analysis': ai_responses
            })

        robot_client.send_command('h')  # return home
        robot_client.send_command('f')  # release robot
        return {"scans": results}
        
    except Exception as e:
        log.error(f"Scan error: {e}")
        robot_client.send_command('f')  # release robot
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/robot/scan/toggle")
async def toggle_scan(state: ScanState) -> Dict[str, bool]:
    """Toggle the scheduled scan behavior."""
    global SCAN_ENABLED, scheduler
    try:
        SCAN_ENABLED = state.enabled
        
        if scheduler:
            if state.enabled:
                log.info(f"Starting scan every {SCAN_INTERVAL} seconds")
                scheduler.add_job(
                    scheduled_scan,
                    trigger=IntervalTrigger(seconds=SCAN_INTERVAL),
                    id='scheduled_scan',
                    replace_existing=True
                )
                scheduler.start()
            else:
                log.info("Stopping scheduled scan")
                scheduler.remove_job('scheduled_scan')
                scheduler.shutdown()
                scheduler = AsyncIOScheduler()
        
        return {"enabled": SCAN_ENABLED}
    except Exception as e:
        log.error(f"Failed to toggle scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analyses")
async def get_analyses(limit: int = 5):
    with get_db_session() as db:
        analyses = (db.query(DBAIAnalysis)
                   .order_by(DBAIAnalysis.timestamp.desc())
                   .limit(limit)
                   .all())
        return [AIAnalysis.from_orm(analysis) for analysis in analyses]