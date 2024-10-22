# backend/pyaquarius/config.py
from typing import Dict, Any
import os
from pathlib import Path

class Config:
    DATA_DIR = Path(os.getenv('DATA_DIR', '/data'))
    IMAGES_DIR = DATA_DIR / 'images'
    DB_PATH = DATA_DIR / 'aquarium.db'
    
    CAMERA = {
        'fps': int(os.getenv('CAMERA_FPS', '30')),
        'frame_buffer': int(os.getenv('CAMERA_FRAME_BUFFER', '2')),
        'max_width': int(os.getenv('CAMERA_MAX_WIDTH', '1920')),
        'max_height': int(os.getenv('CAMERA_MAX_HEIGHT', '1080')),
        'max_images': int(os.getenv('CAMERA_MAX_IMAGES', '1000')),
        'min_free_space_mb': int(os.getenv('CAMERA_MIN_FREE_SPACE_MB', '500')),
        'device': {'read_attempts': 3, 'retry_delay': 1},
    }
    
    TANK = {
        'temp_min': float(os.getenv('TANK_TEMP_MIN', '74')),
        'temp_max': float(os.getenv('TANK_TEMP_MAX', '82')),
        'ph_min': float(os.getenv('TANK_PH_MIN', '6.5')),
        'ph_max': float(os.getenv('TANK_PH_MAX', '7.5')),
        'ammonia_max': float(os.getenv('TANK_AMMONIA_MAX', '0.25')),
        'nitrite_max': float(os.getenv('TANK_NITRITE_MAX', '0.25')),
        'nitrate_max': float(os.getenv('TANK_NITRATE_MAX', '40'))
    }
    
    API = {
        'rate_limit': os.getenv('API_RATE_LIMIT', '100/minute'),
        'timeout': int(os.getenv('API_TIMEOUT', '60')),
        'max_retries': int(os.getenv('API_MAX_RETRIES', '3'))
    }
    
    def __init__(self):
        self.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        os.chmod(self.IMAGES_DIR, 0o775)
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = cls.__dict__
        for k in keys:
            value = value.get(k, default)
            if value is None:
                return default
        return value

config = Config()