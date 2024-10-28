import asyncio
import cv2
import os
import base64
import logging
import threading
import time
import subprocess
import re
from datetime import datetime
from typing import Dict, Set, List, Optional
from dataclasses import dataclass
from fastapi import WebSocket
from queue import Queue

from .config import config

log = logging.getLogger(__name__)

@dataclass
class CameraDevice:
    index: int
    name: str
    path: str
    width: int = 640
    height: int = 480

class CameraManager:
    def __init__(self):
        self.streams: Dict[str, 'CameraStream'] = {}
        self._locks: Dict[str, threading.Lock] = {}
        self.devices = self.list_devices()

    @staticmethod
    def list_devices() -> List[CameraDevice]:
        """List all available camera devices using v4l2-ctl."""
        devices = []
        try:
            # Get device list from v4l2-ctl
            cmd = ["v4l2-ctl", "--list-devices"]
            output = subprocess.check_output(cmd, universal_newlines=True)
            
            current_camera = None
            device_index = 0
            
            for line in output.split('\n'):
                if ':' in line and not line.startswith('\t'):
                    # This is a camera name line
                    current_camera = line.split('(')[0].strip()
                elif line.startswith('\t/dev/video'):
                    # This is a device path line
                    if current_camera:
                        path = line.strip()
                        # Only add video capture devices (even numbers typically)
                        if int(re.search(r'\d+', path).group()) % 2 == 0:
                            devices.append(CameraDevice(
                                index=device_index,
                                name=current_camera,
                                path=path
                            ))
                            device_index += 1
                            
            # Get capabilities for each device
            for device in devices:
                try:
                    cap = cv2.VideoCapture(device.path, cv2.CAP_V4L2)
                    if cap.isOpened():
                        device.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        device.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()
                except Exception as e:
                    log.error(f"Error getting capabilities for {device.path}: {e}")
                    
        except Exception as e:
            log.error(f"Error listing camera devices: {e}")
            
        return devices

    def get_lock(self, device_path: str) -> threading.Lock:
        """Get or create a lock for a specific camera device."""
        if device_path not in self._locks:
            self._locks[device_path] = threading.Lock()
        return self._locks[device_path]

    def test_camera(self, device: CameraDevice) -> bool:
        """Test if a camera is accessible."""
        try:
            with self.get_lock(device.path):
                cap = cv2.VideoCapture(device.path, cv2.CAP_V4L2)
                if not cap.isOpened():
                    return False
                ret, frame = cap.read()
                cap.release()
                return ret and frame is not None
        except Exception as e:
            log.error(f"Camera test error for device {device.path}: {e}")
            return False

    async def get_stream(self, device_index: int) -> Optional['CameraStream']:
        """Get or create a camera stream."""
        device = next((d for d in self.devices if d.index == device_index), None)
        if not device:
            log.error(f"No camera found with index {device_index}")
            return None

        if not self.test_camera(device):
            log.error(f"Camera {device.path} is not accessible")
            return None
            
        if device.path not in self.streams:
            stream = CameraStream(device, self)
            success = await stream.start()
            if success:
                self.streams[device.path] = stream
            else:
                return None
        return self.streams[device.path]
    
    async def stop_all(self):
        """Stop all active camera streams."""
        for stream in self.streams.values():
            await stream.stop()
        self.streams.clear()

    async def save_frame(self, filename: str, device_index: int = 0) -> bool:
        """Save a frame from a camera, pausing any active stream if necessary."""
        device = next((d for d in self.devices if d.index == device_index), None)
        if not device:
            log.error(f"No camera found with index {device_index}")
            return False

        stream = self.streams.get(device.path)
        if stream:
            # If there's an active stream, use it to capture the frame
            return await stream.capture_frame(filename)
        else:
            # If no stream, do a one-off capture
            return await self._capture_single_frame(filename, device)
    
    async def _capture_single_frame(self, filename: str, device: CameraDevice) -> bool:
        """Capture a single frame from a camera without streaming."""
        with self.get_lock(device.path):
            try:
                cap = cv2.VideoCapture(device.path, cv2.CAP_V4L2)
                if not cap.isOpened():
                    raise RuntimeError(f"Failed to open device {device.path}")
                
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
    
    def __init__(self, device: CameraDevice, manager: CameraManager):
        self.device = device
        self.manager = manager
        self.active = False
        self.connections: Set[WebSocket] = set()
        self.frame_queue: Queue = Queue(maxsize=config.CAMERA_FRAME_BUFFER)
        self.capture_thread = None
        self._stop_event = threading.Event()
    
    async def start(self) -> bool:
        """Start the camera stream."""
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
            log.error(f"Failed to start camera {self.device.path}: {e}")
            self.active = False
            return False
    
    async def stop(self):
        """Stop the camera stream."""
        self.active = False
        self._stop_event.set()
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
    
    async def connect(self, websocket: WebSocket):
        """Handle a new WebSocket connection."""
        try:
            self.connections.add(websocket)
            log.info(f"New connection to camera {self.device.path}")
            
            while self.active and websocket in self.connections:
                try:
                    frame = self.frame_queue.get(timeout=1.0)
                    await websocket.send_bytes(frame)
                except asyncio.CancelledError:
                    break
                except Exception:
                    await asyncio.sleep(0.01)
                    
        except Exception as e:
            log.error(f"WebSocket error for camera {self.device.path}: {e}")
        finally:
            self.connections.remove(websocket)
            if not self.connections:
                await self.stop()
            log.info(f"Connection closed for camera {self.device.path}")

    async def capture_frame(self, filename: str) -> bool:
        """Capture a frame while streaming."""
        try:
            # Temporarily pause frame queue updates
            old_frame = None
            while not self.frame_queue.empty():
                try:
                    old_frame = self.frame_queue.get_nowait()
                except:
                    break

            with self.manager.get_lock(self.device.path):
                cap = cv2.VideoCapture(self.device.path, cv2.CAP_V4L2)
                if not cap.isOpened():
                    return False
                    
                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    return False

                success = await self.manager._process_and_save_frame(frame, filename)

                # Restore frame queue
                if old_frame is not None:
                    try:
                        self.frame_queue.put_nowait(old_frame)
                    except:
                        pass

                return success

        except Exception as e:
            log.error(f"Frame capture error: {e}")
            return False
    
    def _capture_frames(self):
        """Continuous frame capture thread."""
        while not self._stop_event.is_set():
            try:
                with self.manager.get_lock(self.device.path):
                    cap = cv2.VideoCapture(self.device.path, cv2.CAP_V4L2)
                    if not cap.isOpened():
                        raise RuntimeError(f"Failed to open camera {self.device.path}")

                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAMERA_CAM_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAMERA_CAM_HEIGHT)
                    cap.set(cv2.CAP_PROP_FPS, config.CAMERA_FPS)
                    
                    last_frame_time = 0
                    frame_interval = 1.0 / config.CAMERA_FPS
                    
                    while not self._stop_event.is_set():
                        current_time = time.time()
                        if current_time - last_frame_time < frame_interval:
                            time.sleep(0.001)
                            continue
                            
                        ret, frame = cap.read()
                        if not ret:
                            break

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
                            
                        last_frame_time = current_time

            except Exception as e:
                log.error(f"Camera {self.device.path} capture error: {e}")
                if not self._stop_event.is_set():
                    time.sleep(1)  # Wait before retrying
            finally:
                if cap:
                    cap.release()