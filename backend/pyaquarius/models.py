import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import contextmanager
import json
import re

from pydantic import BaseModel, Field, validator, constr
from sqlalchemy import Column, DateTime, Float, Index, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Directory settings
DATA_DIR = os.getenv('DATA_DIR', 'data')
IMAGES_DIR = os.getenv('IMAGES_DIR', 'data/images')
DATABASE_DIR = os.getenv('DATABASE_DIR', 'data/db')
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///data/db/aquarius.db')
LIFE_CSV_PATH = os.path.join(os.path.dirname(__file__), "ainotes", "life.csv")

if not all([DATA_DIR, IMAGES_DIR, DATABASE_DIR, DATABASE_URL]):
    raise ValueError("Required environment variables not set")

# Create directories if they don't exist
for dir in [DATA_DIR, IMAGES_DIR, DATABASE_DIR]:
    if not os.path.exists(dir):
        os.makedirs(dir, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class BaseMixin:
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DBImage(BaseMixin, Base):
    __tablename__ = "images"
    id = Column(String, primary_key=True)
    device_index = Column(Integer, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    filepath = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)

class DBReading(BaseMixin, Base):
    __tablename__ = "readings"
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature_f = Column(Float)
    temperature_c = Column(Float)
    tank_id = Column(Integer, nullable=False)
    image_id = Column(String, nullable=True)

class DBAIAnalysis(BaseMixin, Base):
    __tablename__ = "ai_responses"
    id = Column(String, primary_key=True)
    image_id = Column(String)
    tank_id = Column(Integer)
    timestamp = Column(DateTime, default=datetime.utcnow)
    ai_model = Column(String)
    analysis = Column(String)
    response = Column(String)

class AIAnalysisBase(BaseModel):
    image_id: str
    tank_id: int
    ai_model: str
    analysis: str
    response: str

class AIAnalysis(AIAnalysisBase):
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    class Config:
        from_attributes = True

class ImageBase(BaseModel):
    filepath: str
    width: int
    height: int
    file_size: int

class Image(ImageBase):
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    class Config:
        from_attributes = True

class ReadingBase(BaseModel):
    temperature_f: float = Field(ge=32, le=120, description="Temperature in Fahrenheit")
    temperature_c: float = Field(ge=0, le=49, description="Temperature in Celsius")
    tank_id: int = Field(ge=1, le=3, description="Tank identifier (1-3)")
    image_id: Optional[str] = None

    @validator('temperature_c', pre=True)
    def validate_celsius(cls, v, values):
        if v is None and 'temperature_f' in values:
            return (values['temperature_f'] - 32) * 5/9
        return v

    @validator('temperature_f', pre=True)
    def validate_fahrenheit(cls, v, values):
        if v is None and 'temperature_c' in values:
            return (values['temperature_c'] * 9/5) + 32
        return v

class Reading(ReadingBase):
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    class Config:
        from_attributes = True

class DBLife(BaseMixin, Base):
    __tablename__ = "life"
    id = Column(String, primary_key=True)
    scientific_name = Column(String)
    common_name = Column(String)
    emoji = Column(String)
    last_seen_at = Column(DateTime, default=datetime.utcnow)
    image_refs = Column(String, default='[]')  # JSON string array of image IDs

class LifeBase(BaseModel):
    scientific_name: str
    common_name: str
    emoji: str

class AquariumStatus(BaseModel):
    latest_images: Dict[int, Image]
    latest_reading: Optional[Reading]
    alerts: List[str]
    timezone: str
    location: str
    scan_enabled: bool = False

class Trajectory(BaseModel):
    name: str
    modified: datetime
    selected: bool = False

    @validator('name')
    def validate_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]{1,64}$', v):
            raise ValueError('Invalid trajectory name. Use only letters, numbers, underscore, or dash (max 64 chars)')
        return v

class RobotCommand(BaseModel):
    command: str = Field(description="Robot command (q/r/c/p/P/s/l/f)")
    trajectory_name: Optional[str] = None

class TrajectoryName(BaseModel):
    name: constr(min_length=1, max_length=64, pattern=r'^[a-zA-Z0-9_-]+$')

class ScanState(BaseModel):
    enabled: bool

def load_life_from_csv(db: Session) -> None:
    log = logging.getLogger(__name__)
    try:
        if db.query(DBLife).count() > 0:
            log.info("Life table already populated, skipping initial load")
            return
        
        with open(LIFE_CSV_PATH, mode='r') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                db_life = DBLife(
                    id=datetime.now(timezone.utc).isoformat(),
                    emoji=row['emoji'],
                    common_name=row['common_name'],
                    scientific_name=row['scientific_name']
                )
                db.add(db_life)
            db.commit()
            log.info("Successfully loaded initial life data")
    except Exception as e:
        log.error(f"Failed to load life data: {str(e)}")
        raise

Base.metadata.create_all(bind=engine)
Index('idx_readings_timestamp', DBReading.timestamp)
Index('idx_images_timestamp', DBImage.timestamp)
Index('idx_life_last_seen_at', DBLife.last_seen_at)

with SessionLocal() as db:
    load_life_from_csv(db)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

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

class Life(LifeBase):
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    image_refs: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True
        
    @validator('image_refs', pre=True)
    def parse_image_refs(cls, v):
        if isinstance(v, str):
            return json.loads(v)
        return v
