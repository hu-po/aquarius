import cv2
import os
import logging
import threading
import time
from typing import Generator, List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

log = logging.getLogger(__name__)

CAMERA_FPS = int(os.getenv('CAMERA_FPS', '15'))
CAMERA_IMG_TYPE = os.getenv('CAMERA_IMG_TYPE', 'jpg').lower()
CAMERA_MAX_DIM = int(os.getenv('CAMERA_MAX_DIM', '1920'))
CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', '1280'))
CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', '720'))
CAMERA_MAX_IMAGES = int(os.getenv('CAMERA_MAX_IMAGES', '1000'))
IMAGES_DIR = os.getenv('IMAGES_DIR', 'data/images')

@dataclass
class CameraDevice:
    index: int
    name: str
    path: str
    width: int = CAMERA_WIDTH
    height: int = CAMERA_HEIGHT

class CameraManager:
    def __init__(self):
        self._locks: Dict[str, threading.Lock] = {}
        self.devices = self._list_devices()

    def _list_devices(self) -> List[CameraDevice]:
        """List available camera devices."""
        devices = []
        try:
            # Get configured device indices
            configured_devices = os.getenv('CAMERA_DEVICES', '0,4').split(',')
            configured_indices = [int(x.strip()) for x in configured_devices]
            
            # Check device permissions
            log.info("Checking video device permissions")
            for device_index in configured_indices:
                path = f"/dev/video{device_index}"
                if not os.path.exists(path):
                    log.error(f"Camera device {path} does not exist")
                    continue
                    
                if not os.access(path, os.R_OK | os.W_OK):
                    log.error(f"Insufficient permissions for {path}")
                    continue
                    
                log.info(f"Attempting to open camera at {path}")
                cap = cv2.VideoCapture(path, cv2.CAP_V4L2)
                if cap.isOpened():
                    # Test reading a frame with timeout
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    for _ in range(3):  # Try up to 3 times
                        ret, _ = cap.read()
                        if ret:
                            name = f"Camera {device_index}"
                            log.info(f"Successfully opened camera {name} at {path}")
                            devices.append(CameraDevice(
                                index=device_index,
                                name=name,
                                path=path
                            ))
                            break
                        time.sleep(0.1)
                    else:
                        log.error(f"Could not read frame from camera at {path} after 3 attempts")
                else:
                    log.error(f"Could not open camera at {path}")
                cap.release()
                
        except Exception as e:
            log.error(f"Error listing camera devices: {str(e)}", exc_info=True)
        
        log.info(f"Found {len(devices)} camera devices: {[d.path for d in devices]}")
        return devices

    def get_lock(self, device_path: str) -> threading.Lock:
        """Get or create a lock for a camera device."""
        if device_path not in self._locks:
            self._locks[device_path] = threading.Lock()
        return self._locks[device_path]

    def get_device(self, device_index: int) -> Optional[CameraDevice]:
        """Get camera device by index."""
        return next((d for d in self.devices if d.index == device_index), None)

    def generate_frames(self, device: CameraDevice) -> Generator[bytes, None, None]:
        """Generate MJPEG frames from camera."""
        cap = None
        try:
            with self.get_lock(device.path):
                # Only lock during camera initialization
                cap = cv2.VideoCapture(device.path, cv2.CAP_V4L2)
                if not cap.isOpened():
                    raise RuntimeError(f"Failed to open camera {device.path}")
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, device.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, device.height)
                cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

            frame_interval = 1.0 / CAMERA_FPS
            last_frame_time = 0

            while True:
                current_time = time.time()
                if current_time - last_frame_time < frame_interval:
                    time.sleep(0.001)
                    continue

                with self.get_lock(device.path):
                    # Lock only during frame capture
                    ret, frame = cap.read()
                    if not ret:
                        break

                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue

                frame_bytes = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                
                last_frame_time = current_time

        except Exception as e:
            log.error(f"Frame generation error: {e}")
        finally:
            if cap:
                with self.get_lock(device.path):
                    cap.release()

    async def capture_image(self, filename: str, device_index: int = 0) -> bool:
        """Capture and save a single image."""
        device = self.get_device(device_index)
        if not device:
            log.error(f"No camera found with index {device_index}")
            return False

        with self.get_lock(device.path):
            try:
                log.info(f"Attempting to capture image from {device.path}")
                cap = cv2.VideoCapture(device.path, cv2.CAP_V4L2)
                if not cap.isOpened():
                    log.error(f"Failed to open camera device {device.path}")
                    return False

                log.info(f"Setting camera properties: width={device.width}, height={device.height}")
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, device.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, device.height)
                
                log.info("Reading frame")
                ret, frame = cap.read()
                if not ret:
                    log.error(f"Failed to read frame from {device.path}")
                    return False

                # Resize if needed
                height, width = frame.shape[:2]
                if width > CAMERA_MAX_DIM or height > CAMERA_MAX_DIM:
                    scale = CAMERA_MAX_DIM / max(width, height)
                    new_width = int(width * scale)
                    new_height = int(height * scale)
                    frame = cv2.resize(frame, (new_width, new_height))
                    log.info(f"Resized frame to {new_width}x{new_height}")

                filepath = os.path.join(IMAGES_DIR, filename)
                log.info(f"Saving image to {filepath}")
                if not cv2.imwrite(filepath, frame):
                    log.error(f"Failed to write image to {filepath}")
                    return False
                
                log.info(f"Successfully captured and saved image to {filepath}")
                await self._cleanup_old_images()
                return True

            except Exception as e:
                log.error(f"Image capture error: {str(e)}", exc_info=True)
                return False
            finally:
                if cap:
                    cap.release()

    async def _cleanup_old_images(self):
        """Remove old images when exceeding maximum count."""
        try:
            images = []
            for filename in os.listdir(IMAGES_DIR):
                if filename.endswith(CAMERA_IMG_TYPE):
                    filepath = os.path.join(IMAGES_DIR, filename)
                    timestamp = datetime.fromtimestamp(os.path.getmtime(filepath))
                    images.append((filepath, timestamp))

            if len(images) <= CAMERA_MAX_IMAGES:
                return

            images.sort(key=lambda x: x[1], reverse=True)
            for filepath, _ in images[CAMERA_MAX_IMAGES:]:
                if os.path.exists(filepath):
                    os.remove(filepath)

        except Exception as e:
            log.error(f"Image cleanup error: {e}")
