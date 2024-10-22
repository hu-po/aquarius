import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.throttling import ThrottlingMiddleware
from sqlalchemy.orm import Session
import asyncio
from contextlib import contextmanager
from . import camera, vlms
from .models import (
    get_db, Image, Reading, VLMDescription, AquariumStatus,
    DBImage, DBReading, DBVLMDescription
)

required_env_vars = ['ANTHROPIC_API_KEY', 'GOOGLE_SDK_API_KEY', 'OPENAI_API_KEY']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

app = FastAPI(title="Aquarius Monitoring System")
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001").split(",")
allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=3600
)

app.add_middleware(ThrottlingMiddleware, rate_limit="100/minute")

IMAGES_DIR = os.getenv("IMAGES_DIR", "/tmp/aquarium_images")
os.makedirs(IMAGES_DIR, exist_ok=True)
os.chmod(IMAGES_DIR, 0o775)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

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

async def analyze_image(image_id: str, image_path: str, db: Session):
    try:
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
        
        start_time = datetime.utcnow()
        
        try:
            descriptions = await asyncio.wait_for(
                vlms.caption(image_path, prompt),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            descriptions = {"error": "Analysis timeout"}
        except Exception as e:
            descriptions = {"error": f"Analysis failed: {str(e)}"}

        with get_db_session() as session:
            for model_name, description in descriptions.items():
                if model_name != "error":
                    vlm_desc = DBVLMDescription(
                        id=f"{datetime.utcnow().isoformat()}_{model_name}",
                        image_id=image_id,
                        model_name=model_name,
                        description=description,
                        prompt=prompt,
                        latency=(datetime.utcnow() - start_time).total_seconds()
                    )
                    session.add(vlm_desc)

                    concerns = extract_concerns(description)
                    if concerns:
                        vlm_desc.concerns_detected = concerns

    except Exception as e:
        print(f"Failed to analyze image: {e}")
        with get_db_session() as session:
            error_desc = DBVLMDescription(
                id=f"{datetime.utcnow().isoformat()}_error",
                image_id=image_id,
                model_name="system",
                description=f"Analysis failed: {str(e)}",
                prompt=prompt,
                latency=0
            )
            session.add(error_desc)

def extract_concerns(description: str) -> Optional[str]:
    if not description:
        return None
    
    concerns = []
    lower_desc = description.lower()
    
    keywords = [
        "concern", "warning", "alert", "problem", "issue",
        "high", "low", "unsafe", "dangerous", "unhealthy"
    ]
    
    for line in description.split('\n'):
        if any(keyword in line.lower() for keyword in keywords):
            concerns.append(line.strip())
    
    return "; ".join(concerns) if concerns else None

@app.post("/capture")
async def capture_image(
    background_tasks: BackgroundTasks,
    device_id: int = 0,
    db: Session = Depends(get_db)
) -> Image:
    timestamp = datetime.utcnow()
    filename = f"{timestamp.isoformat()}.jpg"
    filepath = os.path.join(IMAGES_DIR, filename)
    
    if not camera.save_frame(device_id, filepath):
        raise HTTPException(status_code=500, detail="Failed to capture image")
    
    try:
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
        
        background_tasks.add_task(analyze_image, db_image.id, filepath, db)
        return Image.from_orm(db_image)
        
    except Exception as e:
        db.rollback()
        if os.path.exists(filepath):
            os.remove(filepath)
        raise HTTPException(status_code=500, detail=str(e))

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
            if desc.model_name != "system":
                latest_descriptions[desc.model_name] = desc.description
            if desc.concerns_detected:
                alerts.extend(desc.concerns_detected.split('; '))
    
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
        alerts=list(set(alerts))  # Remove duplicates
    )

@app.get("/images")
async def list_images(
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db)
) -> List[Image]:
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
    since = datetime.utcnow() - timedelta(hours=hours)
    readings = db.query(DBReading)\
        .filter(DBReading.timestamp >= since)\
        .order_by(DBReading.timestamp.asc())\
        .all()
    return [Reading.from_orm(r) for r in readings]

@app.get("/devices")
async def list_devices() -> List[int]:
    return camera.list_devices()