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
    
    async def get_stream(self, device_index: int) -> Optional['CameraStream']:
        """Get or create a camera stream."""
        if device_index not in self.streams:
            try:
                # Test camera access before creating stream
                with self.get_lock(device_index):
                    cap = cv2.VideoCapture(device_index, cv2.CAP_V4L2)
                    if not cap.isOpened():
                        log.error(f"Failed to open camera {device_index}")
                        return None
                    cap.release()
                
                stream = CameraStream(device_index, self)
                success = await stream.start()
                if success:
                    self.streams[device_index] = stream
                else:
                    log.error(f"Failed to start stream for camera {device_index}")
                    return None
            except Exception as e:
                log.error(f"Error creating stream for camera {device_index}: {e}")
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
    """Handles continuous camera streaming with WebSocket support."""
    
    def __init__(self, device_index: int, manager: CameraManager, fps: int = 30):
        self.device_index = device_index
        self.manager = manager
        self.fps = fps
        self.active = False
        self.frame_interval = 1 / fps
        self.connections: Set[WebSocket] = set()
        self.frame_queue: Queue = Queue(maxsize=2)
        self.capture_thread = None
        self.cap = None
        self.paused = False
        self._pause_lock = threading.Lock()
    
    async def start(self) -> bool:
        """Start the camera stream."""
        if not self.active:
            try:
                # Test camera access first
                with self.manager.get_lock(self.device_index):
                    self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_V4L2)
                    if not self.cap.isOpened():
                        raise RuntimeError(f"Failed to open camera {self.device_index}")
                    
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                    
                    # Test frame capture
                    ret, _ = self.cap.read()
                    if not ret:
                        raise RuntimeError("Failed to capture test frame")
                    
                self.active = True
                self.capture_thread = threading.Thread(target=self._capture_frames)
                self.capture_thread.daemon = True
                self.capture_thread.start()
                return True
            except Exception as e:
                log.error(f"Failed to start camera {self.device_index}: {e}")
                if self.cap:
                    self.cap.release()
                    self.cap = None
                return False
        return False
    
    async def stop(self):
        """Stop the camera stream."""
        self.active = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
        if self.cap:
            self.cap.release()
            self.cap = None
    
    async def pause(self):
        """Pause the stream temporarily."""
        with self._pause_lock:
            self.paused = True
            await asyncio.sleep(0.1)  # Allow current frame to complete
    
    async def resume(self):
        """Resume the paused stream."""
        with self._pause_lock:
            self.paused = False
    
    async def capture_frame(self, filename: str) -> bool:
        """Capture a frame from the active stream."""
        await self.pause()
        try:
            with self.manager.get_lock(self.device_index):
                ret, frame = self.cap.read()
                if not ret:
                    return False
                return await self.manager._process_and_save_frame(frame, filename)
        finally:
            await self.resume()
    
    def _capture_frames(self):
        """Continuous frame capture thread."""
        with self.manager.get_lock(self.device_index):
            try:
                self.cap = cv2.VideoCapture(self.device_index, cv2.CAP_V4L2)
                if not self.cap.isOpened():
                    log.error(f"Failed to open camera {self.device_index}")
                    return

                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, self.fps)
                
                last_frame_time = 0
                
                while self.active:
                    if self.paused:
                        time.sleep(0.01)
                        continue
                        
                    current_time = time.time()
                    if current_time - last_frame_time < self.frame_interval:
                        time.sleep(0.001)
                        continue
                    
                    ret, frame = self.cap.read()
                    if not ret:
                        continue
                    
                    ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    if not ret:
                        continue
                    
                    encoded_frame = base64.b64encode(buffer.tobytes())
                    
                    while not self.frame_queue.empty():
                        try:
                            self.frame_queue.get_nowait()
                        except:
                            break
                    
                    try:
                        self.frame_queue.put_nowait(encoded_frame)
                    except:
                        pass
                    
                    last_frame_time = current_time
                    
            except Exception as e:
                log.error(f"Camera {self.device_index} streaming error: {e}")
            finally:
                if self.cap:
                    self.cap.release()
    
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