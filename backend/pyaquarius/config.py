from dataclasses import dataclass
from typing import List
import os
from pathlib import Path

@dataclass
class Config:
    DATA_DIR: Path = Path(os.get_env('DATA_DIR'))
    IMAGES_DIR: Path = DATA_DIR / 'images'
    DB_PATH: Path = DATA_DIR / 'aquarium.db'
    
    CAMERA_FPS: int = int(os.get_env('CAMERA_FPS'))
    CAMERA_FRAME_BUFFER: int = int(os.get_env('CAMERA_FRAME_BUFFER'))
    CAMERA_MAX_DIM: int = int(os.get_env('CAMERA_MAX_DIM'))
    CAMERA_CAM_WIDTH: int = int(os.get_env('CAMERA_CAM_WIDTH'))
    CAMERA_CAM_HEIGHT: int = int(os.get_env('CAMERA_CAM_HEIGHT'))
    CAMERA_MAX_IMAGES: int = int(os.get_env('CAMERA_MAX_IMAGES'))
    CAMERA_MIN_FREE_SPACE_MB: int = int(os.get_env('CAMERA_MIN_FREE_SPACE_MB'))
    CAMERA_DEVICE_READ_ATTEMPTS: int = 3
    CAMERA_DEVICE_RETRY_DELAY: int = 1
    
    TANK_TEMP_MIN: float = float(os.get_env('TANK_TEMP_MIN'))
    TANK_TEMP_MAX: float = float(os.get_env('TANK_TEMP_MAX'))
    TANK_PH_MIN: float = float(os.get_env('TANK_PH_MIN'))
    TANK_PH_MAX: float = float(os.get_env('TANK_PH_MAX'))
    TANK_AMMONIA_MAX: float = float(os.get_env('TANK_AMMONIA_MAX'))
    TANK_NITRITE_MAX: float = float(os.get_env('TANK_NITRITE_MAX'))
    TANK_NITRATE_MAX: float = float(os.get_env('TANK_NITRATE_MAX'))
    
    API_TIMEOUT: int = int(os.get_env('API_TIMEOUT'))
    API_MAX_RETRIES: int = int(os.get_env('API_MAX_RETRIES'))
    API_ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in os.get_env("CORS_ORIGINS").split(",") if origin.strip()]
    API_CORS_MAX_AGE: int = int(os.get_env('API_CORS_MAX_AGE'))

try:
    config = Config()
except Exception as e:
    raise RuntimeError(f"Failed to load configuration: {str(e)}")