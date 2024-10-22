from dataclasses import dataclass
from dotenv import load_dotenv
from typing import List
import os
from pathlib import Path

@dataclass
class Config:
    DATA_DIR: Path = Path(os.getenv('DATA_DIR'))
    IMAGES_DIR: Path = DATA_DIR / 'images'
    DB_PATH: Path = DATA_DIR / 'aquarium.db'
    
    CAMERA_FPS: int = int(os.getenv('CAMERA_FPS'))
    CAMERA_FRAME_BUFFER: int = int(os.getenv('CAMERA_FRAME_BUFFER'))
    CAMERA_MAX_DIM: int = int(os.getenv('CAMERA_MAX_DIM'))
    CAMERA_CAM_WIDTH: int = int(os.getenv('CAMERA_CAM_WIDTH'))
    CAMERA_CAM_HEIGHT: int = int(os.getenv('CAMERA_CAM_HEIGHT'))
    CAMERA_MAX_IMAGES: int = int(os.getenv('CAMERA_MAX_IMAGES'))
    CAMERA_MIN_FREE_SPACE_MB: int = int(os.getenv('CAMERA_MIN_FREE_SPACE_MB'))
    CAMERA_DEVICE_READ_ATTEMPTS: int = 3
    CAMERA_DEVICE_RETRY_DELAY: int = 1
    
    TANK_TEMP_MIN: float = float(os.getenv('TANK_TEMP_MIN'))
    TANK_TEMP_MAX: float = float(os.getenv('TANK_TEMP_MAX'))
    TANK_PH_MIN: float = float(os.getenv('TANK_PH_MIN'))
    TANK_PH_MAX: float = float(os.getenv('TANK_PH_MAX'))
    TANK_AMMONIA_MAX: float = float(os.getenv('TANK_AMMONIA_MAX'))
    TANK_NITRITE_MAX: float = float(os.getenv('TANK_NITRITE_MAX'))
    TANK_NITRATE_MAX: float = float(os.getenv('TANK_NITRATE_MAX'))
    
    API_TIMEOUT: int = int(os.getenv('API_TIMEOUT'))
    API_MAX_RETRIES: int = int(os.getenv('API_MAX_RETRIES'))
    API_ALLOWED_ORIGINS: List[str] = [origin.strip() for origin in os.getenv("CORS_ORIGINS").split(",") if origin.strip()]
    API_CORS_MAX_AGE: int = int(os.getenv('API_CORS_MAX_AGE'))

try:
    env_path = Path(__file__).parent.parent / '.env'
    if not env_path.exists():
        print(f"Failed to load configuration: {env_path} does not exist")
        env_path = Path(__file__).parent.parent / '.env.example'
    load_dotenv(env_path)
    config = Config()
except Exception as e:
    raise RuntimeError(f"Failed to load configuration: {str(e)}")