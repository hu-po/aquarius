import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.throttling import ThrottlingMiddleware
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from sqlalchemy.orm import Session
import cv2

from . import camera
from . import vlms
from .models import (
    get_db, Image, Reading, VLMDescription, AquariumStatus,
    DBImage, DBReading, DBVLMDescription
)

# Load environment variables
load_dotenv()

# Add to main.py at startup
required_env_vars = ['ANTHROPIC_API_KEY', 'GOOGLE_SDK_API_KEY', 'OPENAI_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Initialize FastAPI app
app = FastAPI(title="Aquarius Monitoring System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=3600
)
app.add_middleware(
    ThrottlingMiddleware,
    rate_limit="100/minute"
)

# Setup static file serving for images
IMAGES_DIR = os.getenv("IMAGES_DIR", "/tmp/aquarium_images")
if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR, exist_ok=True)  # Ensure directory exists and is created if missing
    os.chmod(IMAGES_DIR, 0o777)  # Set full permissions for all users
app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

# Background Tasks
async def analyze_image(image_id: str, image_path: str, db: Session):
    try:
        # Prompt setup and image processing
        with open("prompts/tank-info.txt") as f:
            base_prompt = f.read().strip()
    
        prompt = f"""Given this aquarium setup: {base_prompt}

        Please analyze this image and:
        1. Describe what you see
        2. Note any changes from ideal conditions
        3. List any concerns that need attention
        4. Estimate the number of fish visible
        5. Assess plant health
        """
        
        # Get descriptions from VLMs
        start_time = datetime.utcnow()
        descriptions = await vlms.caption(image_path, prompt)

        # Store descriptions in the database
        for model_name, description in descriptions.items():
            vlm_desc = DBVLMDescription(
                id=f"{datetime.utcnow().isoformat()}_{model_name}",
                image_id=image_id,
                model_name=model_name,
                description=description,
                prompt=prompt,
                latency=(datetime.utcnow() - start_time).total_seconds()
            )
            db.add(vlm_desc)

        db.commit()
    except Exception as e:
        print(f"Failed to analyze image: {e}")

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost")
    FastAPICache.init(RedisBackend(redis), prefix="aquarius-cache:")
    
# API Routes
@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "Aquarium Monitor Backend is Running",
        "version": "1.0.0"
    }

@app.post("/capture")
async def capture_image(
    background_tasks: BackgroundTasks,
    device_id: int = 0,
    db: Session = Depends(get_db)
) -> Image:
    """Capture new image and trigger analysis"""
    # Generate filename with timestamp
    timestamp = datetime.utcnow()
    filename = f"{timestamp.isoformat()}.jpg"
    filepath = os.path.join(IMAGES_DIR, filename)
    
    # Capture image
    success = camera.save_frame(device_id, filepath)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to capture image")
    
    # Create database entry
    db_image = DBImage(
        id=timestamp.isoformat(),
        filepath=filepath,
        width=camera.RESOLUTION[0],
        height=camera.RESOLUTION[1],
        device_id=device_id,
        file_size=os.path.getsize(filepath)
    )
    db.add(db_image)
    db.commit()
    
    # Trigger background analysis
    background_tasks.add_task(
        analyze_image,
        db_image.id,
        filepath,
        db
    )
    
    return Image.from_orm(db_image)

@app.post("/readings")
async def add_reading(
    reading: Reading,
    db: Session = Depends(get_db)
) -> Reading:
    """Add new sensor readings"""
    db_reading = DBReading(
        id=datetime.utcnow().isoformat(),
        temperature=reading.temperature,
        ph=reading.ph,
        ammonia=reading.ammonia,
        nitrite=reading.nitrite,
        nitrate=reading.nitrate,
        image_id=reading.image_id
    )
    db.add(db_reading)
    db.commit()
    return Reading.from_orm(db_reading)

@app.get("/status")
async def get_status(db: Session = Depends(get_db)) -> AquariumStatus:
    """Get current aquarium status"""
    # Get latest image
    latest_image = db.query(DBImage).order_by(DBImage.timestamp.desc()).first()
    
    # Get latest reading
    latest_reading = db.query(DBReading).order_by(DBReading.timestamp.desc()).first()
    
    # Get latest VLM descriptions if we have an image
    latest_descriptions = {}
    alerts = []
    
    if latest_image:
        descriptions = db.query(DBVLMDescription).filter(
            DBVLMDescription.image_id == latest_image.id
        ).all()
        
        for desc in descriptions:
            latest_descriptions[desc.model_name] = desc.description
            if desc.concerns_detected:
                alerts.append(desc.concerns_detected)
    
    # Add alerts for concerning readings
    if latest_reading:
        if latest_reading.temperature > 82 or latest_reading.temperature < 74:
            alerts.append(f"Temperature outside ideal range: {latest_reading.temperature}°F")
        if latest_reading.ph and (latest_reading.ph < 6.5 or latest_reading.ph > 7.5):
            alerts.append(f"pH outside ideal range: {latest_reading.ph}")
        if latest_reading.ammonia and latest_reading.ammonia > 0.25:
            alerts.append(f"High ammonia level: {latest_reading.ammonia} ppm")
        if latest_reading.nitrite and latest_reading.nitrite > 0.25:
            alerts.append(f"High nitrite level: {latest_reading.nitrite} ppm")
        if latest_reading.nitrate and latest_reading.nitrate > 40:
            alerts.append(f"High nitrate level: {latest_reading.nitrate} ppm")
    
    return AquariumStatus(
        latest_image=Image.from_orm(latest_image) if latest_image else None,
        latest_reading=Reading.from_orm(latest_reading) if latest_reading else None,
        latest_descriptions=latest_descriptions,
        alerts=alerts
    )

@app.get("/images")
async def list_images(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[Image]:
    """Get recent images"""
    images = db.query(DBImage)\
        .order_by(DBImage.timestamp.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    return [Image.from_orm(img) for img in images]

@app.get("/readings/history")
async def get_readings_history(
    hours: int = 24,
    db: Session = Depends(get_db)
) -> List[Reading]:
    """Get sensor reading history"""
    since = datetime.utcnow() - timedelta(hours=hours)
    readings = db.query(DBReading)\
        .filter(DBReading.timestamp >= since)\
        .order_by(DBReading.timestamp.asc())\
        .all()
    return [Reading.from_orm(r) for r in readings]

@app.get("/devices")
async def list_devices() -> List[int]:
    """List available camera devices"""
    return camera.list_devices()