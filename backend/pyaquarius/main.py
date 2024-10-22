import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import asyncio
from contextlib import contextmanager
from pyaquarius.camera import save_frame
from pyaquarius.vlms import caption
from pyaquarius.models import (
    get_db, Image, Reading, AquariumStatus,
    DBImage, DBReading, DBVLMDescription
)

from .config import config


app = FastAPI(title="Aquarius Monitoring System")
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.API_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "Authorization"],
    max_age=config.API_CORS_MAX_AGE
)
app.mount("/images", StaticFiles(directory=str(config.IMAGES_DIR)), name="images")

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
            descriptions = await asyncio.wait_for(caption(image_path, prompt), timeout=60.0)
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
    keywords = ["concern", "warning", "alert", "problem", "issue", "high", "low", "unsafe", "dangerous", "unhealthy"]
    for line in description.split('\n'):
        if any(keyword in line.lower() for keyword in keywords):
            concerns.append(line.strip())
    return "; ".join(concerns) if concerns else None

@app.post("/capture")
async def capture_image(background_tasks: BackgroundTasks, device_id: int = 0, db: Session = Depends(get_db)) -> Image:
    timestamp = datetime.utcnow()
    filename = f"{timestamp.isoformat()}.jpg"
    filepath = os.path.join(config.IMAGES_DIR, filename)
    if not save_frame(device_id, filename):
        raise HTTPException(status_code=500, detail="Failed to capture image")
    try:
        db_image = DBImage(
            id=timestamp.isoformat(),
            filepath=filepath,
            width=config.CAMERA_MAX_DIM,
            height=config.CAMERA_MAX_DIM,
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
    since = datetime.utcnow() - timedelta(hours=hours)
    readings = db.query(DBReading).filter(DBReading.timestamp >= since).order_by(DBReading.timestamp.asc()).all()
    return [Reading.from_orm(r) for r in readings]

@app.get("/devices")
async def list_devices() -> List[int]:
    from pyaquarius.camera import list_devices
    return list_devices()