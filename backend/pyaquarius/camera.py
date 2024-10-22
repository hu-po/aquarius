import cv2
import os
from datetime import datetime, timedelta
from typing import List, Optional

IMAGES_DIR = os.getenv("IMAGES_DIR", "/tmp/aquarium_images")
os.makedirs(IMAGES_DIR, exist_ok=True)

FPS = 30
FRAME_BUFFERSIZE = 2
RESOLUTION = (1920, 1080) # (3840, 2160) (640, 480)
MAX_IMAGES = 1000
MIN_FREE_SPACE_MB = 500

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

def save_frame(device_index: int, filename: str) -> bool:
    try:
        cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open device /dev/video{device_index}")
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, RESOLUTION[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, RESOLUTION[1])
        cap.set(cv2.CAP_PROP_BUFFERSIZE, FRAME_BUFFERSIZE)
        
        ret, frame = cap.read()
        if not ret:
            raise RuntimeError("Failed to capture frame")
        
        frame = optimize_image(frame)
        
        filepath = os.path.join(IMAGES_DIR, filename)
        cv2.imwrite(filepath, frame)
        
        cleanup_images()
        return True
    except Exception as e:
        print(f"Camera error: {str(e)}")
        return False
    finally:
        if 'cap' in locals():
            cap.release()

def optimize_image(frame, max_dimension: int = 1920):
    height, width = frame.shape[:2]
    if width > max_dimension or height > max_dimension:
        scale = max_dimension / max(width, height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        frame = cv2.resize(frame, (new_width, new_height))
    return frame

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
        for filename in os.listdir(IMAGES_DIR):
            if not filename.endswith(('.jpg', '.png')):
                continue
            
            filepath = os.path.join(IMAGES_DIR, filename)
            timestamp = datetime.fromtimestamp(os.path.getmtime(filepath))
            all_images.append((filepath, timestamp))

        if len(all_images) <= MAX_IMAGES:
            return

        all_images.sort(key=lambda x: x[1], reverse=True)
        
        for filepath, _ in all_images[MAX_IMAGES:]:
            if os.path.exists(filepath):
                os.remove(filepath)
                
        dir_size_mb = get_directory_size_mb(IMAGES_DIR)
        if dir_size_mb > (MAX_IMAGES * 2):  # Assuming average 2MB per image
            for filepath, _ in all_images[MAX_IMAGES // 2:]:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
    except Exception as e:
        print(f"Error during image cleanup: {str(e)}")

if __name__ == "__main__":
    devices = list_devices()
    if devices:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for device in devices:
            try:
                save_frame(device, f"test_device_{device}_{timestamp}.jpg")
            except Exception as e:
                print(f"Failed to process device {device}: {str(e)}")
    else:
        print("No video devices found")