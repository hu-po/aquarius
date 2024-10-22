# models.py
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from sqlalchemy import Index
import os

# Initialize SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///aquarium.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Add version tracking column to all tables
class BaseMixin:
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# SQLAlchemy Models (for database)
class DBImage(BaseMixin, Base):
    __tablename__ = "images"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    filepath = Column(String)
    width = Column(Integer)
    height = Column(Integer)
    device_id = Column(Integer)
    file_size = Column(Integer)
    water_level = Column(Float, nullable=True)
    fish_count = Column(Integer, nullable=True)

class DBReading(BaseMixin, Base):
    __tablename__ = "readings"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    ph = Column(Float, nullable=True)
    ammonia = Column(Float, nullable=True)
    nitrite = Column(Float, nullable=True)
    nitrate = Column(Float, nullable=True)
    image_id = Column(String, nullable=True)

class DBVLMDescription(BaseMixin, Base):
    __tablename__ = "vlm_descriptions"
    
    id = Column(String, primary_key=True)
    image_id = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    model_name = Column(String)  # claude, openai, gemini, mistral
    description = Column(String)
    prompt = Column(String)
    latency = Column(Float)  # seconds
    concerns_detected = Column(String, nullable=True)

# Pydantic Models (for API)
class ImageBase(BaseModel):
    filepath: str
    width: int
    height: int
    device_id: int
    file_size: int
    water_level: Optional[float] = None
    fish_count: Optional[int] = None

class Image(ImageBase):
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True

class ReadingBase(BaseModel):
    temperature: float = Field(ge=32, le=120)  # Valid temperature range
    ph: Optional[float] = Field(None, ge=0, le=14)
    ammonia: Optional[float] = Field(None, ge=0)
    nitrite: Optional[float] = Field(None, ge=0)
    nitrate: Optional[float] = Field(None, ge=0)
    image_id: Optional[str] = None

class Reading(ReadingBase):
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True

class VLMDescriptionBase(BaseModel):
    image_id: str
    model_name: str
    description: str
    prompt: str
    latency: float
    concerns_detected: Optional[str] = None

class VLMDescription(VLMDescriptionBase):
    id: str = Field(default_factory=lambda: datetime.now().isoformat())
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True

class AquariumStatus(BaseModel):
    """Combined status response for frontend"""
    latest_image: Optional[Image] = None
    latest_reading: Optional[Reading] = None
    latest_descriptions: Dict[str, str] = {}
    alerts: List[str] = []

# Create all tables
Base.metadata.create_all(bind=engine)
Index('idx_readings_timestamp', DBReading.timestamp)
Index('idx_images_timestamp', DBImage.timestamp)

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()