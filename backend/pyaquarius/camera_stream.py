import asyncio
import cv2
import base64
import logging
from typing import Dict, Set
from fastapi import WebSocket
import threading
from queue import Queue
import time

log = logging.getLogger(__name__)

class CameraStream:
    def __init__(self, device_index: int, fps: int = 30):
        self.device_index = device_index
        self.fps = fps
        self.active = False
        self.frame_interval = 1 / fps
        self.connections: Set[WebSocket] = set()
        self.latest_frame: bytes = b''
        self.frame_queue: Queue = Queue(maxsize=2)
        self.capture_thread = None
        
    async def start(self):
        if not self.active:
            self.active = True
            self.capture_thread = threading.Thread(target=self._capture_frames)
            self.capture_thread.daemon = True
            self.capture_thread.start()
    
    def stop(self):
        self.active = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
            self.capture_thread = None
            
    def _capture_frames(self):
        cap = cv2.VideoCapture(self.device_index, cv2.CAP_V4L2)
        if not cap.isOpened():
            log.error(f"Failed to open camera {self.device_index}")
            return
            
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Reduced resolution for streaming
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        
        last_frame_time = 0
        
        while self.active:
            current_time = time.time()
            if current_time - last_frame_time < self.frame_interval:
                time.sleep(0.001)  # Small sleep to prevent CPU overuse
                continue
                
            ret, frame = cap.read()
            if not ret:
                continue
                
            # Compress frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if not ret:
                continue
                
            # Convert to base64 for WebSocket transmission
            encoded_frame = base64.b64encode(buffer.tobytes())
            
            # Update latest frame and clear old frames from queue
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
            
        cap.release()
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)
        try:
            while self.active:
                try:
                    frame = self.frame_queue.get(timeout=1.0)
                    await websocket.send_bytes(frame)
                except:
                    await asyncio.sleep(0.01)
        finally:
            self.connections.remove(websocket)
            
class CameraStreamManager:
    def __init__(self):
        self.streams: Dict[int, CameraStream] = {}
        
    async def get_stream(self, device_index: int) -> CameraStream:
        if device_index not in self.streams:
            self.streams[device_index] = CameraStream(device_index)
            await self.streams[device_index].start()
        return self.streams[device_index]
        
    async def stop_all(self):
        for stream in self.streams.values():
            stream.stop()
        self.streams.clear()