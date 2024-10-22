# models.py
from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import os

# Initialize SQLite database
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///aquarium.db")
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy Models (for database)
class DBImage(Base):
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

class DBReading(Base):
    __tablename__ = "readings"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    ph = Column(Float, nullable=True)
    ammonia = Column(Float, nullable=True)
    nitrite = Column(Float, nullable=True)
    nitrate = Column(Float, nullable=True)
    image_id = Column(String, nullable=True)

class DBVLMDescription(Base):
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
    temperature: float
    ph: Optional[float] = None
    ammonia: Optional[float] = None
    nitrite: Optional[float] = None
    nitrate: Optional[float] = None
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

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()