import asyncio
from typing import Optional, List, Dict, AsyncGenerator
import logging
import cv2
import os
from datetime import datetime

log = logging.getLogger(__name__)

CAMERA_FPS = int(os.getenv('CAMERA_FPS', '15'))
CAMERA_IMG_TYPE = os.getenv('CAMERA_IMG_TYPE', 'jpg').lower()
CAMERA_MAX_DIM = int(os.getenv('CAMERA_MAX_DIM', '1024'))
CAMERA_WIDTH = int(os.getenv('CAMERA_WIDTH', '1280'))
CAMERA_HEIGHT = int(os.getenv('CAMERA_HEIGHT', '720'))
CAMERA_MAX_IMAGES = int(os.getenv('CAMERA_MAX_IMAGES', '1000'))
IMAGES_DIR = os.getenv('IMAGES_DIR', 'data/images')
CAMERA_STREAM_TOGGLE_DELAY = float(os.getenv('CAMERA_STREAM_TOGGLE_DELAY', '50')) / 1000  # Convert ms to seconds

class CameraDevice:
    def __init__(self, index: int, path: str, width: int = CAMERA_WIDTH, height: int = CAMERA_HEIGHT):
        self.index = index
        self.path = path
        self.width = width
        self.height = height
        self.lock = asyncio.Lock()
        self.name = f"Camera {index}"
        self.is_streaming = False
        self.is_capturing = False
        self.is_active = False
        self.cap = None
        self._initialize()
    
    def _initialize(self) -> None:
        try:
            self.cap = cv2.VideoCapture(self.path)
            if not self.cap.isOpened():
                log.error(f"Failed to initialize camera {self.index} at {self.path}")
                return
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.is_active = True
            log.debug(f"Camera {self.index} initialized successfully")
        except Exception as e:
            log.error(f"Camera {self.index} initialization error: {str(e)}")

    async def stop_stream(self):
        """Safely stop any active stream."""
        async with self.lock:
            if self.is_streaming:
                self.is_streaming = False
                await asyncio.sleep(CAMERA_STREAM_TOGGLE_DELAY)
                log.debug(f"Stream stopped for device {self.index}")

    async def start_stream(self):
        """Safely start stream if not capturing."""
        if not self.is_capturing:
            async with self.lock:
                if not self.is_streaming:
                    if not self.cap or not self.cap.isOpened():
                        self._initialize()
                    if not self.is_active:
                        log.error(f"Failed to start stream - camera {self.index} not active")
                        return
                    self.is_streaming = True
                    log.debug(f"Stream started for device {self.index}")

    async def get_frame(self):
        """Get a single frame from the camera."""
        if not self.cap or not self.cap.isOpened():
            self._initialize()
        if not self.is_active:
            return None
            
        ret, frame = self.cap.read()
        if not ret:
            log.error(f"Failed to read frame from camera {self.index}")
            return None
            
        return frame

class CameraManager:
    def __init__(self):
        self.devices: Dict[int, CameraDevice] = {}
        self._init_lock = asyncio.Lock()
        
    async def initialize(self) -> None:
        log.debug("Starting camera device initialization")
        async with self._init_lock:
            device_indices = os.getenv('CAMERA_DEVICES', '0').split(',')
            log.debug(f"Found {len(device_indices)} camera device indices in config")
            
            for idx in device_indices:
                try:
                    index = int(idx.strip())
                    path = f"/dev/video{index}"
                    log.debug(f"Checking camera device {index} at path {path}")
                    
                    if not os.path.exists(path):
                        log.error(f"Camera device path {path} does not exist")
                        continue
                        
                    log.debug(f"Attempting to open camera {index} for testing")
                    cap = cv2.VideoCapture(path)
                    if cap.isOpened():
                        device = CameraDevice(index=index, path=path)
                        device.is_active = True
                        self.devices[index] = device
                        log.info(f"Successfully initialized camera {index} at {path}")
                        cap.release()
                        log.debug(f"Released test capture for camera {index}")
                    else:
                        log.error(f"Camera {index} exists but failed to open - check permissions")
                        
                except ValueError as e:
                    log.error(f"Invalid camera index format {idx}: {str(e)}")
                except Exception as e:
                    log.error(f"Unexpected error initializing camera {idx}: {str(e)}", exc_info=True)
                    
            log.info(f"Camera initialization complete - {len(self.devices)} active devices")

    def get_device(self, index: int) -> Optional[CameraDevice]:
        return self.devices.get(index)

    async def capture_image(self, device: CameraDevice, filename: str) -> Optional[tuple[str, int, int, int]]:
        log.debug(f"Starting image capture from device {device.index}")
        if device.is_streaming:
            log.debug(f"Stopping stream on device {device.index} before capture")
            await device.stop_stream()
        
        async with device.lock:
            device.is_capturing = True
            try:
                log.debug(f"Opening capture device {device.path}")
                cap = cv2.VideoCapture(device.path)
                if not cap.isOpened():
                    log.error(f"Failed to open camera device {device.path}")
                    return None

                log.debug(f"Configuring camera {device.index} - width: {device.width}, height: {device.height}")
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, device.width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, device.height)
                
                frame = None
                for attempt in range(3):
                    log.debug(f"Capture attempt {attempt + 1} for device {device.index}")
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        break
                    log.warning(f"Capture attempt {attempt + 1} failed, retrying...")
                    await asyncio.sleep(0.2)

                if frame is None:
                    log.error(f"All capture attempts failed for device {device.index}")
                    return None

                filepath = os.path.join(IMAGES_DIR, filename)
                
                log.debug(f"Saving captured image to {filepath}")
                if cv2.imwrite(filepath, frame):
                    os.chmod(filepath, 0o644)
                    height, width = frame.shape[:2]
                    file_size = os.path.getsize(filepath)
                    log.debug(f"Image saved successfully - dimensions: {width}x{height}, size: {file_size} bytes")
                    await self._cleanup_old_images()
                    return filepath, width, height, file_size

                log.error(f"Failed to write image to {filepath}")
                return None
            except Exception as e:
                log.error(f"Capture error: {str(e)}", exc_info=True)
                return None
            finally:
                device.is_capturing = False
                if cap:
                    cap.release()

    async def generate_frames(self, device: CameraDevice) -> AsyncGenerator[bytes, None]:
        if not device:
            log.error("No camera device provided")
            return

        if device.is_capturing:
            log.info(f"Camera {device.index} is currently capturing, waiting...")
            await asyncio.sleep(1)

        try:
            async with device.lock:
                if not device.is_streaming:
                    device.is_streaming = True
                    log.debug(f"Stream started for device {device.index}")

                target_dim = min(CAMERA_MAX_DIM, device.width, device.height)
                scale = min(target_dim/device.width, target_dim/device.height)
                new_width = int(device.width * scale)
                new_height = int(device.height * scale)

            while device.is_streaming and not device.is_capturing:
                frame = await device.get_frame()
                if frame is None:
                    log.error(f"Failed to get frame from {device.path}")
                    continue

                try:
                    # Resize frame if needed
                    if new_width != device.width or new_height != device.height:
                        frame = cv2.resize(frame, (new_width, new_height))

                    _, buffer = cv2.imencode(f'.{CAMERA_IMG_TYPE}', frame)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                    await asyncio.sleep(1/CAMERA_FPS)  # Control frame rate
                except Exception as e:
                    log.error(f"Frame encoding error: {str(e)}")
                    continue

        except Exception as e:
            log.error(f"Stream error: {str(e)}", exc_info=True)
        finally:
            device.is_streaming = False

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
