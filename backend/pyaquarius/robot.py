import socket
import logging
import os
import time
import threading
from typing import Optional
from contextlib import contextmanager

log = logging.getLogger(__name__)

HOST = os.getenv('ROBOT_SERVER_HOST', '192.168.1.33')
PORT = int(os.getenv('ROBOT_SERVER_PORT', '9000'))
BUFFER_SIZE = 1024
INITIAL_RETRY_DELAY = 1.0
MAX_RETRY_DELAY = 30.0
RETRY_BACKOFF = 2.0
COMMAND_TIMEOUT = 10.0

class RobotClient:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.last_connect_attempt = 0
        self.current_retry_delay = INITIAL_RETRY_DELAY
        self.keep_alive_thread: Optional[threading.Thread] = None
        self._initialize()

    def _initialize(self):
        """Initialize connection on startup"""
        self.connect()
        if self.connected:
            log.info("Robot client initialized successfully")
        else:
            log.warning("Robot client failed to initialize, will retry on commands")

    def start_keep_alive(self):
        """Start keep-alive thread to maintain connection"""
        def keep_alive():
            while self.connected:
                try:
                    time.sleep(30)
                    if self.connected:
                        response = self.send_command('ping')
                        if response != 'pong':
                            self.connected = False
                except:
                    self.connected = False
                    break
                    
        self.keep_alive_thread = threading.Thread(target=keep_alive, daemon=True)
        self.keep_alive_thread.start()

    def connect(self) -> bool:
        """Connect to robot server with exponential backoff"""
        current_time = time.time()
        time_since_last_attempt = current_time - self.last_connect_attempt
        
        if time_since_last_attempt < self.current_retry_delay:
            log.debug(f"Waiting {self.current_retry_delay - time_since_last_attempt:.2f}s before retry")
            time.sleep(self.current_retry_delay - time_since_last_attempt)
            
        self.last_connect_attempt = time.time()
        
        try:
            if self.socket:
                try:
                    log.debug("Closing existing socket connection")
                    self.socket.close()
                except Exception as e:
                    log.debug(f"Error closing existing socket: {e}")
                    
            log.debug(f"Attempting to connect to robot server at {HOST}:{PORT}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(COMMAND_TIMEOUT)
            self.socket.connect((HOST, PORT))
            
            # Verify connection with retries
            max_ping_attempts = 3
            for attempt in range(max_ping_attempts):
                try:
                    log.debug(f"Ping attempt {attempt + 1}")
                    response = self.send_command('ping')
                    if response == 'pong':
                        self.connected = True
                        self.current_retry_delay = INITIAL_RETRY_DELAY
                        self.start_keep_alive()
                        log.info(f"Connected to robot server at {HOST}:{PORT}")
                        return True
                    log.debug(f"Unexpected ping response: {response}")
                except Exception as e:
                    log.debug(f"Ping attempt {attempt + 1} failed: {e}")
                if attempt < max_ping_attempts - 1:
                    time.sleep(1)
                    
            raise ConnectionError("Failed ping verification")
            
        except Exception as e:
            log.error(f"Connection failed: {e}", exc_info=True)
            self.connected = False
            self.current_retry_delay = min(self.current_retry_delay * RETRY_BACKOFF, MAX_RETRY_DELAY)
            log.debug(f"Next retry in {self.current_retry_delay:.2f}s")
            return False

    def send_command(self, command: str) -> str:
        """Send command to robot server with automatic reconnection"""
        if not self.connected and not self.connect():
            return "Not connected to robot server"

        try:
            self.socket.sendall(command.encode('utf-8'))
            response = self.socket.recv(BUFFER_SIZE).decode('utf-8')
            log.debug(f"Sent command '{command}', received: {response}")
            return response
            
        except socket.timeout:
            log.error("Command timed out")
            self.connected = False
            return "Command timed out"
        except Exception as e:
            log.error(f"Error sending command: {e}")
            self.connected = False
            return f"Error: {str(e)}"

    def close(self):
        """Close connection to robot server"""
        if self.socket:
            try:
                self.send_command('q')
                self.socket.close()
                log.info("Disconnected from robot server")
            except Exception as e:
                log.error(f"Error closing connection: {e}")
        self.connected = False