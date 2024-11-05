import socket
import logging
import os
import time
from typing import Optional
import threading

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Client settings
HOST = os.getenv('ROBOT_SERVER_HOST', '192.168.10.10')
PORT = int(os.getenv('ROBOT_SERVER_PORT', '9000'))
BUFFER_SIZE = 1024
INITIAL_RETRY_DELAY = 1.0  # Start with 1 second delay
MAX_RETRY_DELAY = 30.0    # Maximum delay between retries
RETRY_BACKOFF = 2.0       # Multiply delay by this factor after each failure
COMMAND_TIMEOUT = 10.0    # Seconds to wait for command response

class RobotClient:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.last_connect_attempt = 0
        self.current_retry_delay = INITIAL_RETRY_DELAY
        self.keep_alive_thread: Optional[threading.Thread] = None

    def start_keep_alive(self):
        """Start keep-alive thread to maintain connection"""
        def keep_alive():
            while self.connected:
                try:
                    # Send keep-alive ping every 30 seconds
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
            time.sleep(self.current_retry_delay - time_since_last_attempt)
            
        self.last_connect_attempt = time.time()
        
        try:
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                
            log.info(f"Attempting to connect to robot server at {HOST}:{PORT}")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(COMMAND_TIMEOUT)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            # Add connection timeout
            self.socket.settimeout(5)  
            self.socket.connect((HOST, PORT))
            
            # Verify connection with retries
            max_ping_attempts = 3
            for attempt in range(max_ping_attempts):
                try:
                    response = self.send_command('ping')
                    if response == 'pong':
                        self.connected = True
                        self.current_retry_delay = INITIAL_RETRY_DELAY
                        self.start_keep_alive()
                        log.info(f"Connected to robot server at {HOST}:{PORT}")
                        return True
                    log.warning(f"Invalid ping response on attempt {attempt + 1}: {response}")
                except Exception as e:
                    log.warning(f"Ping attempt {attempt + 1} failed: {e}")
                if attempt < max_ping_attempts - 1:
                    time.sleep(1)
                    
            raise ConnectionError("Failed ping verification after multiple attempts")
            
        except Exception as e:
            log.error(f"Failed to connect to robot server: {e}")
            self.connected = False
            self.current_retry_delay = min(self.current_retry_delay * RETRY_BACKOFF, MAX_RETRY_DELAY)
            log.info(f"Will retry in {self.current_retry_delay:.1f} seconds")
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

def main():
    client = RobotClient()
    
    try:
        while True:
            if not client.connected:
                log.info(f"Attempting to connect to robot server...")
                if not client.connect():
                    continue

            try:
                command = input("Enter command (q/r/c/p/P/s/l/f): ").strip()
                if not command:
                    continue
                    
                response = client.send_command(command)
                print(f"Server response: {response}")
                
                if command == 'q' or response == 'quit':
                    break
                    
            except EOFError:
                log.info("EOF received, attempting reconnection...")
                client.connected = False
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Error in command loop: {e}")
                client.connected = False
                
    except KeyboardInterrupt:
        log.info("Client shutting down")
    finally:
        client.close()

if __name__ == "__main__":
    main()