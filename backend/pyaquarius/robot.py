import socket
import logging
import os
import time
import threading
from typing import Optional, List
from contextlib import contextmanager
import json

log = logging.getLogger(__name__)

HOST = os.getenv('ROBOT_SERVER_HOST', '192.168.1.33')
PORT = int(os.getenv('ROBOT_SERVER_PORT', '9000'))
BUFFER_SIZE = int(os.getenv('ROBOT_SERVER_BUFFER_SIZE', '1024'))
INITIAL_RETRY_DELAY = float(os.getenv('ROBOT_SERVER_INITIAL_RETRY_DELAY', '1.0'))
MAX_RETRY_DELAY = float(os.getenv('ROBOT_SERVER_MAX_RETRY_DELAY', '10.0'))
RETRY_BACKOFF = float(os.getenv('ROBOT_SERVER_RETRY_BACKOFF', '1.0'))
COMMAND_TIMEOUT = float(os.getenv('ROBOT_SERVER_COMMAND_TIMEOUT', '8.0'))
MAX_CONNECT_ATTEMPTS = int(os.getenv('ROBOT_SERVER_MAX_CONNECT_ATTEMPTS', '3'))
KEEP_ALIVE_INTERVAL = float(os.getenv('ROBOT_SERVER_KEEP_ALIVE_INTERVAL', '10.0'))
ROBOT_RAW_CMD_MAX_RETRY = int(os.getenv('ROBOT_RAW_CMD_MAX_RETRY', '3'))

class RobotClient:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.last_connect_attempt = 0
        self.current_retry_delay = INITIAL_RETRY_DELAY
        self.keep_alive_thread: Optional[threading.Thread] = None
        self.running = True
        self._initialize()

    def _initialize(self):
        log.info(f"Initializing robot client connection to {HOST}:{PORT}")
        if self.connect():
            log.info("Robot client initialized successfully")
        else:
            log.warning("Robot client failed to initialize, will retry on commands")

    def start_keep_alive(self):
        if self.keep_alive_thread and self.keep_alive_thread.is_alive():
            return
        self.keep_alive_thread = threading.Thread(target=self._keep_alive_loop, daemon=True)
        self.keep_alive_thread.start()

    def _keep_alive_loop(self):
        while self.running and self.connected:
            try:
                time.sleep(KEEP_ALIVE_INTERVAL)
                if not self.connected:
                    break
                response = self._send_raw('ping')
                if response != 'pong':
                    log.warning("Keep-alive ping failed, marking as disconnected")
                    self.connected = False
                    break
            except Exception as e:
                log.warning(f"Keep-alive error: {e}")
                self.connected = False
                break

    def connect(self) -> bool:
        current_time = time.time()
        if current_time - self.last_connect_attempt < self.current_retry_delay:
            return False

        self.last_connect_attempt = current_time
        
        try:
            if self.socket:
                try:
                    self.socket.close()
                except Exception:
                    pass
                    
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(COMMAND_TIMEOUT)
            
            for attempt in range(MAX_CONNECT_ATTEMPTS):
                try:
                    self.socket.connect((HOST, PORT))
                    response = self._send_raw('ping')
                    if response == 'pong':
                        self.connected = True
                        self.current_retry_delay = INITIAL_RETRY_DELAY
                        self.start_keep_alive()
                        log.info(f"Connected to robot server at {HOST}:{PORT}")
                        return True
                except Exception as e:
                    if attempt == MAX_CONNECT_ATTEMPTS - 1:
                        raise
                    log.debug(f"Connection attempt {attempt + 1} failed: {e}")
                    time.sleep(1)
                    
            raise ConnectionError("Failed ping verification")
            
        except Exception as e:
            log.error(f"Connection failed: {e}")
            self.connected = False
            self.current_retry_delay = min(self.current_retry_delay * RETRY_BACKOFF, MAX_RETRY_DELAY)
            return False

    def _send_raw(self, command: str) -> str:
        """Send raw command to robot server with retries"""
        last_error = None
        
        for attempt in range(ROBOT_RAW_CMD_MAX_RETRY):
            try:
                self.socket.sendall(command.encode('utf-8'))
                response = self.socket.recv(BUFFER_SIZE).decode('utf-8')
                if response:
                    return response
                log.warning(f"Empty response on attempt {attempt + 1}/{ROBOT_RAW_CMD_MAX_RETRY}")
            except Exception as e:
                last_error = e
                log.warning(f"Send attempt {attempt + 1}/{ROBOT_RAW_CMD_MAX_RETRY} failed: {e}")
                if attempt < ROBOT_RAW_CMD_MAX_RETRY - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                break
                
        self.connected = False
        raise ConnectionError(f"Send failed after {ROBOT_RAW_CMD_MAX_RETRY} attempts: {last_error}")

    def send_command(self, command: str, trajectory_name: Optional[str] = None) -> str:
        """Send command to robot server with optional trajectory name"""
        if not self.connected and not self.connect():
            return "Not connected to robot server"

        try:
            # Combine command with trajectory name if provided
            full_command = f"{command}{trajectory_name if trajectory_name else ''}"
            response = self._send_raw(full_command)
            return response
        except Exception as e:
            self.connected = False
            return f"Error: {str(e)}"

    def close(self):
        self.running = False
        if self.socket:
            try:
                self.send_command('q')
                self.socket.close()
            except Exception:
                pass
        self.connected = False

    def get_trajectories(self) -> list:
        """Get list of available trajectories from robot server"""
        if not self.connected and not self.connect():
            log.error("Failed to connect to robot server")
            return []
        
        try:
            response = self._send_raw('t')
            if not response or response.isspace():
                log.warning("Empty response from robot server")
                return []
            
            try:
                data = json.loads(response)
                if not isinstance(data, dict):
                    log.error("Invalid response format - expected dictionary")
                    return []
                
                if 'trajectories' in data:
                    return data['trajectories']
                elif 'error' in data:
                    log.error(f"Server error listing trajectories: {data['error']}")
                    return []
                else:
                    log.error("Response missing required fields")
                    return []
                
            except json.JSONDecodeError as e:
                log.error(f"Failed to parse trajectories response: {e}")
                return []
            
        except Exception as e:
            self.connected = False
            log.error(f"Failed to get trajectories: {e}")
            return []