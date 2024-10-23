from dataclasses import dataclass
from typing import List
import logging
import os

log = logging.getLogger(__name__)

@dataclass
class Config:
    DATA_DIR: str = os.getenv('DATA_DIR')
    IMAGES_DIR: str = os.getenv('IMAGES_DIR')
    DATABASE_DIR: str = os.getenv('DATABASE_DIR')
    DATABASE_URL: str = os.getenv('DATABASE_URL')
    
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
    
    VLM_API_TIMEOUT: int = int(os.getenv('VLM_API_TIMEOUT'))
    VLM_API_MAX_RETRIES: int = int(os.getenv('VLM_API_MAX_RETRIES'))

    CORS_ORIGINS: str = os.getenv('CORS_ORIGINS')
    CORS_MAX_AGE: int = int(os.getenv('CORS_MAX_AGE'))

    def __post_init__(self):
        for dir in [self.DATA_DIR, self.IMAGES_DIR, self.DATABASE_DIR]:
            if os.path.exists(dir):
                log.info(f"found existing directory: {dir}")
            else:
                log.info(f"creating directory: {dir}")
                os.makedirs(dir, parents=True, exist_ok=True)

try:
    config = Config()
except Exception as e:
    raise ValueError(f"One or more config values not set (check your .env): {str(e)}")