import socket
import logging
import os
import time
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Client settings
HOST = os.getenv('ROBOT_SERVER_HOST', '192.168.10.10')
PORT = int(os.getenv('ROBOT_SERVER_PORT', '9000'))
BUFFER_SIZE = 1024
RECONNECT_DELAY = 5

class RobotClient:
    def __init__(self):
        self.socket: Optional[socket.socket] = None
        self.connected = False

    def connect(self) -> bool:
        """Connect to robot server"""
        try:
            if self.socket:
                self.socket.close()
                
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((HOST, PORT))
            self.connected = True
            log.info(f"Connected to robot server at {HOST}:{PORT}")
            return True
            
        except Exception as e:
            log.error(f"Failed to connect to robot server: {e}")
            self.connected = False
            return False

    def send_command(self, command: str) -> str:
        """Send command to robot server"""
        if not self.connected:
            if not self.connect():
                return "Not connected to robot server"

        try:
            self.socket.sendall(command.encode('utf-8'))
            response = self.socket.recv(BUFFER_SIZE).decode('utf-8')
            log.debug(f"Sent command '{command}', received: {response}")
            return response
            
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
                    log.error(f"Connection failed, retrying in {RECONNECT_DELAY} seconds...")
                    time.sleep(RECONNECT_DELAY)
                    continue

            try:
                command = input("Enter command (q/r/c/p/P/s/l/f): ").strip()
                if not command:
                    continue
                    
                response = client.send_command(command)
                print(f"Server response: {response}")
                
                if command == 'q' or response == 'quit':
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