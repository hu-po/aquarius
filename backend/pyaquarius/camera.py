import asyncio
import cv2
import os
import base64
import logging
import threading
import time
from datetime import datetime
from typing import Dict, Set, List, Optional
from fastapi import WebSocket
from queue import Queue

from .config import config

log = logging.getLogger(__name__)

class CameraManager:
    """Unified camera management system with streaming and capture capabilities."""
    
    def __init__(self):
        self.streams: Dict[int, 'CameraStream'] = {}
        self._locks: Dict[int, threading.Lock] = {}
    
    def get_lock(self, device_index: int) -> threading.Lock:
        """Get or create a lock for a specific camera device."""
        if device_index not in self._locks:
            self._locks[device_index] = threading.Lock()
        return self._locks[device_index]
    
    def test_camera(self, device_index: int) -> bool:
        """Test if a camera is accessible."""
        try:
            with self.get_lock(device_index):
                cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
                if not cap.isOpened():
                    return False
                ret, frame = cap.read()
                if not ret or frame is None:
                    return False
                cap.release()
                return True
        except Exception as e:
            log.error(f"Camera test error for device {device_index}: {e}")
            return False

    async def get_stream(self, device_index: int) -> Optional['CameraStream']:
        """Get or create a camera stream."""
        if not self.test_camera(device_index):
            log.error(f"Camera {device_index} is not accessible")
            return None
            
        if device_index not in self.streams:
            stream = CameraStream(device_index, self)
            success = await stream.start()
            if success:
                self.streams[device_index] = stream
            else:
                return None
        return self.streams[device_index]
    
    async def stop_all(self):
        """Stop all active camera streams."""
        for stream in self.streams.values():
            await stream.stop()
        self.streams.clear()
    
    def list_devices() -> List[int]:
        """List all available camera devices."""
        devices = []
        for index in range(10):  # Check first 10 possible indices
            cap = cv2.VideoCapture(index, cv2.CAP_V4L2)
            if cap.isOpened():
                devices.append(index)
            cap.release()
        return devices

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
            log.error(f"Error getting device info for index {index}: {e}")
            return None

    def list_devices_info() -> List[Dict]:
        """List all available camera devices with their information."""
        return [info for index in range(10) if (info := CameraManager.get_device_info(index))]
    
    async def save_frame(self, filename: str, device_index: int = 0) -> bool:
        """Save a frame from a camera, pausing any active stream if necessary."""
        stream = self.streams.get(device_index)
        if stream:
            # If there's an active stream, use it to capture the frame
            return await stream.capture_frame(filename)
        else:
            # If no stream, do a one-off capture
            return await self._capture_single_frame(filename, device_index)
    
    async def _capture_single_frame(self, filename: str, device_index: int) -> bool:
        """Capture a single frame from a camera without streaming."""
        with self.get_lock(device_index):
            try:
                cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
                if not cap.isOpened():
                    raise RuntimeError(f"Failed to open device /dev/video{device_index}")
                
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_CAM_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_CAM_HEIGHT)
                
                ret, frame = cap.read()
                if not ret:
                    raise RuntimeError("Failed to capture frame")
                
                return await self._process_and_save_frame(frame, filename)
                
            except Exception as e:
                log.error(f"Camera capture error: {e}")
                return False
            finally:
                cap.release()
    
    async def _process_and_save_frame(self, frame, filename: str) -> bool:
        """Process and save a captured frame."""
        try:
            height, width = frame.shape[:2]
            if width > config.CAMERA_MAX_DIM or height > config.CAMERA_MAX_DIM:
                scale = config.CAMERA_MAX_DIM / max(width, height)
                new_width = int(width * scale)
                new_height = int(height * scale)
                frame = cv2.resize(frame, (new_width, new_height))
            
            filepath = os.path.join(config.IMAGES_DIR, filename)
            cv2.imwrite(filepath, frame)
            
            await self._cleanup_images()
            return True
        except Exception as e:
            log.error(f"Frame processing error: {e}")
            return False
    
    async def _cleanup_images(self):
        """Clean up old images to maintain storage limits."""
        try:
            all_images = []
            for filename in os.listdir(config.IMAGES_DIR):
                if filename.endswith(config.CAMERA_IMG_TYPE):
                    filepath = os.path.join(config.IMAGES_DIR, filename)
                    timestamp = datetime.fromtimestamp(os.path.getmtime(filepath))
                    all_images.append((filepath, timestamp))

            if len(all_images) <= config.CAMERA_MAX_IMAGES:
                return

            all_images.sort(key=lambda x: x[1], reverse=True)
            for filepath, _ in all_images[config.CAMERA_MAX_IMAGES:]:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
        except Exception as e:
            log.error(f"Image cleanup error: {e}")

class CameraStream:
    def __init__(self, device_index: int, manager: CameraManager):
        self.device_index = device_index
        self.manager = manager
        self.active = False
        self.connections: Set[WebSocket] = set()
        self.frame_queue: Queue = Queue(maxsize=2)
        self.capture_thread = None
        self._stop_event = threading.Event()

    async def start(self) -> bool:
        if self.active:
            return True
            
        try:
            self._stop_event.clear()
            self.active = True
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
            return True
        except Exception as e:
            log.error(f"Failed to start camera {self.device_index}: {e}")
            self.active = False
            return False

    def _capture_frames(self):
        while not self._stop_event.is_set():
            try:
                with self.manager.get_lock(self.device_index):
                    cap = cv2.VideoCapture(self.device_index, cv2.CAP_V4L2)
                    if not cap.isOpened():
                        raise RuntimeError(f"Failed to open camera {self.device_index}")

                    while not self._stop_event.is_set():
                        ret, frame = cap.read()
                        if not ret:
                            break

                        # Process frame...
                        ret, buffer = cv2.imencode('.jpg', frame)
                        if not ret:
                            continue

                        encoded_frame = base64.b64encode(buffer.tobytes())
                        
                        # Update queue
                        while not self.frame_queue.empty():
                            try:
                                self.frame_queue.get_nowait()
                            except:
                                break
                        
                        try:
                            self.frame_queue.put_nowait(encoded_frame)
                        except:
                            pass

            except Exception as e:
                log.error(f"Camera {self.device_index} capture error: {e}")
                if not self._stop_event.is_set():
                    time.sleep(1)  # Wait before retrying
            finally:
                if cap:
                    cap.release()
    
    async def connect(self, websocket: WebSocket):
        """Handle a new WebSocket connection."""
        await websocket.accept()
        self.connections.add(websocket)
        log.info(f"New connection to camera {self.device_index}")
        
        try:
            while self.active and websocket in self.connections:
                if self.paused:
                    await asyncio.sleep(0.1)
                    continue
                    
                try:
                    frame = self.frame_queue.get(timeout=1.0)
                    await websocket.send_bytes(frame)
                except:
                    await asyncio.sleep(0.01)
        except Exception as e:
            log.error(f"WebSocket error for camera {self.device_index}: {e}")
        finally:
            self.connections.remove(websocket)
            if not self.connections:
                await self.stop()
            log.info(f"Connection closed for camera {self.device_index}")