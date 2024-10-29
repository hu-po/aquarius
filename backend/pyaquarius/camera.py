import asyncio
from typing import Optional, List, Dict, AsyncGenerator
import logging
import cv2
import os
from datetime import datetime, timezone

log = logging.getLogger(__name__)

CAMERA_FPS = int(os.getenv('CAMERA_FPS', '15'))
CAMERA_IMG_TYPE = os.getenv('CAMERA_IMG_TYPE', 'jpg').lower()
CAMERA_MAX_DIM = int(os.getenv('CAMERA_MAX_DIM', '1920'))
CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', '1280'))
CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', '720'))
CAMERA_MAX_IMAGES = int(os.getenv('CAMERA_MAX_IMAGES', '1000'))
IMAGES_DIR = os.getenv('IMAGES_DIR', 'data/images')

class CameraDevice:
    def __init__(self, index: int, path: str, width: int = 640, height: int = 480):
        self.index = index
        self.path = path
        self.width = width
        self.height = height
        self.lock = asyncio.Lock()  # Add lock per device

class CameraManager:
    def __init__(self):
        self.devices: Dict[int, CameraDevice] = {}
        self._init_lock = asyncio.Lock()
        self._stream_locks: Dict[int, asyncio.Lock] = {}
        
    async def capture_image(self, device: CameraDevice) -> bool:
        """Capture image from camera with proper locking."""
        if not device:
            log.error("No camera device provided")
            return False
            
        async with device.lock:  # Use device-specific lock
            cap = None
            try:
                filename = f"capture_{datetime.now(timezone.utc).isoformat()}.jpg"
                cap = cv2.VideoCapture(device.path)
                
                if not cap.isOpened():
                    log.error(f"Failed to open camera device {device.path}")
                    return False

                # Set properties with verification
                for prop, value in [
                    (cv2.CAP_PROP_FRAME_WIDTH, device.width),
                    (cv2.CAP_PROP_FRAME_HEIGHT, device.height)
                ]:
                    if not cap.set(prop, value):
                        log.warning(f"Failed to set camera property {prop} to {value}")
                
                # Multiple read attempts with timeout
                for attempt in range(3):
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        break
                    log.warning(f"Read attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(0.1)
                
                if not ret or frame is None:
                    log.error(f"Failed to read frame from {device.path} after 3 attempts")
                    return False

                # Process frame
                try:
                    height, width = frame.shape[:2]
                    if width > CAMERA_MAX_DIM or height > CAMERA_MAX_DIM:
                        scale = CAMERA_MAX_DIM / max(width, height)
                        new_width = int(width * scale)
                        new_height = int(height * scale)
                        frame = cv2.resize(frame, (new_width, new_height))
                        log.info(f"Resized frame to {new_width}x{new_height}")
                    
                    filepath = os.path.join(IMAGES_DIR, filename)
                    if cv2.imwrite(filepath, frame):
                        log.info(f"Successfully saved image to {filepath}")
                        await self._cleanup_old_images()
                        return True
                    else:
                        log.error(f"Failed to write image to {filepath}")
                        return False
                        
                except Exception as e:
                    log.error(f"Frame processing error: {str(e)}", exc_info=True)
                    return False

            except Exception as e:
                log.error(f"Image capture error: {str(e)}", exc_info=True)
                return False
            finally:
                if cap is not None:
                    cap.release()

    async def generate_frames(self, device: CameraDevice) -> AsyncGenerator[bytes, None]:
        """Generate video frames with proper resource management."""
        if not device:
            log.error("No camera device provided")
            return
            
        cap = None
        try:
            async with device.lock:  # Lock during initialization
                cap = cv2.VideoCapture(device.path)
                if not cap.isOpened():
                    log.error(f"Failed to open camera device {device.path}")
                    return
                
                # Set properties
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, device.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, device.height)
            
            while True:
                async with device.lock:  # Lock for each frame
                    ret, frame = cap.read()
                    if not ret:
                        log.error(f"Failed to read frame from {device.path}")
                        break
                        
                    # Process frame
                    try:
                        _, buffer = cv2.imencode('.jpg', frame)
                        frame_bytes = b'--frame\r\n' + \
                                    b'Content-Type: image/jpeg\r\n\r\n' + \
                                    buffer.tobytes() + \
                                    b'\r\n'
                        yield frame_bytes
                    except Exception as e:
                        log.error(f"Frame encoding error: {str(e)}", exc_info=True)
                        break
                        
                await asyncio.sleep(1/30)  # 30 FPS cap
                
        except Exception as e:
            log.error(f"Stream error: {str(e)}", exc_info=True)
        finally:
            if cap is not None:
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
