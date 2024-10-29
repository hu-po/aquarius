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
    def __init__(self, index: int, path: str, width: int = CAMERA_WIDTH, height: int = CAMERA_HEIGHT):
        self.index = index
        self.path = path
        self.width = width
        self.height = height
        self.lock = asyncio.Lock()
        self.name = f"Camera {index}"
        self.is_streaming = False
        self.cap = None  # Store VideoCapture instance

class CameraManager:
    def __init__(self):
        self.devices: Dict[int, CameraDevice] = {}
        self._init_lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        """Initialize available camera devices."""
        async with self._init_lock:
            device_indices = os.getenv('CAMERA_DEVICES', '0').split(',')
            for idx in device_indices:
                try:
                    index = int(idx.strip())
                    path = f"/dev/video{index}"
                    if os.path.exists(path):
                        cap = cv2.VideoCapture(path)
                        if cap.isOpened():
                            device = CameraDevice(index=index, path=path)
                            device.is_active = True
                            self.devices[index] = device
                            log.info(f"Initialized camera device {index} at {path}")
                            cap.release()
                        else:
                            log.error(f"Camera device {index} exists but cannot be opened")
                except ValueError as e:
                    log.error(f"Invalid camera index {idx}: {str(e)}")
                except Exception as e:
                    log.error(f"Failed to initialize camera {idx}: {str(e)}")

    def get_device(self, index: int) -> Optional[CameraDevice]:
        return self.devices.get(index)

    async def capture_image(self, device: CameraDevice) -> Optional[str]:
        """Capture image from camera with proper locking."""
        if device.is_streaming:
            # Wait for any existing stream to finish cleanup
            await asyncio.sleep(0.5)
            
        async with device.lock:
            device.is_streaming = False
            
            try:
                cap = cv2.VideoCapture(device.path)
                if not cap.isOpened():
                    log.error(f"Failed to open camera device {device.path}")
                    return None

                # Set camera properties
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, device.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, device.height)
                
                # Multiple read attempts to ensure good frame
                frame = None
                for _ in range(3):
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        break
                    await asyncio.sleep(0.1)

                if frame is None:
                    log.error(f"Failed to capture frame from device {device.index}")
                    return None

                filename = f"capture_{datetime.now(timezone.utc).isoformat()}.{CAMERA_IMG_TYPE}"
                filepath = os.path.join(IMAGES_DIR, filename)
                
                if cv2.imwrite(filepath, frame):
                    log.info(f"Successfully saved image to {filepath}")
                    await self._cleanup_old_images()
                    return filepath
                
                log.error(f"Failed to write image to {filepath}")
                return None

            except Exception as e:
                log.error(f"Capture error: {str(e)}", exc_info=True)
                return None
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
            cap = cv2.VideoCapture(device.path)
            if not cap.isOpened():
                log.error(f"Failed to open camera device {device.path}")
                return

            cap.set(cv2.CAP_PROP_FRAME_WIDTH, device.width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, device.height)
            cap.set(cv2.CAP_PROP_FPS, CAMERA_FPS)

            async with device.lock:
                device.is_streaming = True
                device.cap = cap

            while device.is_streaming:
                async with device.lock:
                    ret, frame = cap.read()
                    if not ret:
                        log.error(f"Failed to read frame from {device.path}")
                        continue

                    try:
                        _, buffer = cv2.imencode(f'.{CAMERA_IMG_TYPE}', frame)
                        yield b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
                    except Exception as e:
                        log.error(f"Frame encoding error: {str(e)}")
                        break

                await asyncio.sleep(1/CAMERA_FPS)

        except Exception as e:
            log.error(f"Stream error: {str(e)}", exc_info=True)
        finally:
            device.is_streaming = False
            if cap is not None:
                cap.release()
            device.cap = None

    async def _cleanup_old_images(self) -> None:
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
                    log.info(f"Cleaned up old image: {filepath}")

        except Exception as e:
            log.error(f"Image cleanup error: {str(e)}", exc_info=True)
