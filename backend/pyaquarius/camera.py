import cv2
import os
from datetime import datetime
from typing import List, Dict, Optional

from .config import config


def list_devices() -> List[int]:
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if not cap.read()[0]:
            cap.release()
            break
        arr.append(index)
        cap.release()
        index += 1
    return arr

def get_device_info(index: int) -> Optional[Dict]:
    """Get information about a camera device."""
    try:
        cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
        if not cap.isOpened():
            return None
        
        info = {
            "index": index,
            "name": cap.getBackendName(),
            "available": True,
            "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        }
        cap.release()
        return info
    except Exception as e:
        print(f"Error getting device info for index {index}: {str(e)}")
        return None

def list_devices_info() -> List[Dict]:
    """List all available camera devices with their information."""
    devices = []
    for index in range(10):  # Check first 10 possible indices
        info = get_device_info(index)
        if info:
            devices.append(info)
    return devices

def save_frame(filename: str, device_index: int = 0) -> bool:
    try:
        cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open device /dev/video{device_index}")
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_CAM_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_CAM_HEIGHT)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, config.CAMERA_FRAME_BUFFER)
        
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame")
        
        height, width = frame.shape[:2]
        if width > config.CAMERA_MAX_DIM or height > config.CAMERA_MAX_DIM:
            scale = config.CAMERA_MAX_DIM / max(width, height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            frame = cv2.resize(frame, (new_width, new_height))
        
        filepath = os.path.join(config.IMAGES_DIR, filename)
        cv2.imwrite(filepath, frame)
        
        cleanup_images()
        return True
    except Exception as e:
        print(f"Camera error: {str(e)}")
        return False
    finally:
        if 'cap' in locals():
            cap.release()

def get_directory_size_mb(directory: str) -> float:
    total_size = 0
    for dirpath, _, filenames in os.walk(directory):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total_size += os.path.getsize(fp)
    return total_size / (1024 * 1024)

def cleanup_images():
    try:
        all_images = []
        for filename in os.listdir(config.IMAGES_DIR):
            if not filename.endswith(('.jpg', '.png')):
                continue
            
            filepath = os.path.join(config.IMAGES_DIR, filename)
            timestamp = datetime.fromtimestamp(os.path.getmtime(filepath))
            all_images.append((filepath, timestamp))

        if len(all_images) <= config.CAMERA_MAX_IMAGES:
            return

        all_images.sort(key=lambda x: x[1], reverse=True)
        
        for filepath, _ in all_images[config.CAMERA_MAX_IMAGES:]:
            if os.path.exists(filepath):
                os.remove(filepath)
                
        dir_size_mb = get_directory_size_mb(config.IMAGES_DIR)
        if dir_size_mb > (config.CAMERA_MIN_FREE_SPACE_MB * 2):  # Assuming average 2MB per image
            for filepath, _ in all_images[config.CAMERA_MAX_IMAGES // 2:]:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
    except Exception as e:
        print(f"Error during image cleanup: {str(e)}")

if __name__ == "__main__":
    devices_info = list_devices_info()
    if devices_info:
        for device_info in devices_info:
            print(f"Device {device_info['index']}: {device_info}")
    else:
        print("No video devices found")
    devices = list_devices()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for device in devices:
        try:
            save_frame(f"test_device_{device}_{timestamp}.jpg", device)
        except Exception as e:
            print(f"Failed to process device {device}: {str(e)}")
