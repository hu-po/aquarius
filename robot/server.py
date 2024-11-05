import socket
import logging
import os
import json
import threading
import time
from typing import Optional, Dict
from pymycobot.mycobot import MyCobot
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)

# Server settings
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 9000
BUFFER_SIZE = 1024

# Robot settings
SERIAL_PORT = "/dev/ttyAMA0"
BAUD_RATE = 1000000
DEBUG = False

class RobotServer:
    def __init__(self):
        self.mc: Optional[MyCobot] = None
        self.recording = False
        self.playing = False
        self.record_list = []
        self.record_thread: Optional[threading.Thread] = None
        self.play_thread: Optional[threading.Thread] = None
        self.path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "record.txt")
        self.active_clients: Dict[str, int] = {}  # IP -> connection count
        self.server_socket: Optional[socket.socket] = None
        self.running = True
        
    def initialize_robot(self) -> bool:
        """Initialize MyCobot connection with retry logic"""
        retry_count = 0
        while self.running:
            try:
                log.info(f"Attempting to connect to robot on {SERIAL_PORT}")
                self.mc = MyCobot(SERIAL_PORT, BAUD_RATE, debug=DEBUG)
                self.mc.power_on()
                log.info("Robot initialized successfully")
                return True
            except Exception as e:
                retry_count += 1
                log.error(f"Failed to initialize robot (attempt {retry_count}): {e}")
                if retry_count >= 3:
                    log.error("Max robot initialization retries exceeded")
                    return False
                time.sleep(5)  # Wait before retry
        return False

    def handle_command(self, command: str) -> str:
        """Handle incoming commands from client"""
        if not self.mc:
            return "Robot not initialized"
            
        log.debug(f"Received command: {command}")
        try:
            if command == "ping":
                return "pong"
            elif command == "q":
                return "quit"
            elif command == "r":
                self.start_record()
                return "Recording started"
            elif command == "c":
                self.stop_record()
                return "Recording stopped"
            elif command == "p":
                if not self.playing:
                    self.play_once()
                    return "Playing once"
                return "Already playing"
            elif command == "P":
                if not self.playing:
                    self.start_loop_play()
                    return "Loop play started"
                else:
                    self.stop_loop_play()
                    return "Loop play stopped"
            elif command == "s":
                self.save_recording()
                return "Recording saved"
            elif command == "l":
                self.load_recording()
                return "Recording loaded"
            elif command == "f":
                self.mc.release_all_servos()
                return "Robot released"
            else:
                return f"Unknown command: {command}"
        except Exception as e:
            log.error(f"Error handling command {command}: {e}")
            return f"Error: {str(e)}"

    def handle_client(self, conn: socket.socket, addr: tuple):
        """Handle individual client connection"""
        client_ip = addr[0]
        self.active_clients[client_ip] = self.active_clients.get(client_ip, 0) + 1
        
        try:
            while self.running:
                try:
                    data = conn.recv(BUFFER_SIZE)
                    if not data:
                        break
                        
                    command = data.decode('utf-8').strip()
                    response = self.handle_command(command)
                    conn.sendall(response.encode('utf-8'))
                    
                    if response == "quit":
                        break
                except socket.timeout:
                    continue
                except Exception as e:
                    log.error(f"Error handling client {client_ip}: {e}")
                    break
                    
        finally:
            conn.close()
            self.active_clients[client_ip] -= 1
            if self.active_clients[client_ip] <= 0:
                del self.active_clients[client_ip]
                log.info(f"Client {client_ip} disconnected")

    def start(self):
        """Start the robot server"""
        if not self.initialize_robot():
            log.error("Failed to initialize robot, exiting")
            return

        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((HOST, PORT))
            self.server_socket.listen(5)
            self.server_socket.settimeout(1.0)  # Allow checking self.running
            log.info(f"Server listening on {HOST}:{PORT}")

            while self.running:
                try:
                    conn, addr = self.server_socket.accept()
                    client_ip = addr[0]
                    
                    if client_ip not in self.active_clients:
                        log.info(f"New client connected from {client_ip}")
                    
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(conn, addr),
                        daemon=True
                    )
                    client_thread.start()
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.running:
                        log.error(f"Error accepting connection: {e}")
                        time.sleep(1)
                    
        except Exception as e:
            log.error(f"Server error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        if self.mc:
            try:
                self.mc.release_all_servos()
            except:
                pass
        log.info("Server shutdown complete")

    # Implement the teaching functionality methods
    def start_record(self):
        """Start recording robot movements"""
        if not self.recording:
            self.record_list = []
            self.recording = True
            self.record_thread = threading.Thread(target=self._record_loop, daemon=True)
            self.record_thread.start()
            log.info("Recording started")

    def _record_loop(self):
        """Record loop to capture robot state"""
        while self.recording:
            angles = self.mc.get_encoders()
            speeds = self.mc.get_servo_speeds()
            gripper = self.mc.get_encoder(7)
            log.debug(f"Recording state - Angles: {angles}, Speeds: {speeds}, Gripper: {gripper}")
            if angles and speeds:
                self.record_list.append([angles, speeds, gripper, 0.1])

    def stop_record(self):
        """Stop recording robot movements"""
        if self.recording:
            self.recording = False
            self.record_thread.join()
            log.info("Recording stopped")

    def play_once(self):
        """Play recorded movements once"""
        if self.record_list:
            self.playing = True
            log.debug(f"Starting playback of {len(self.record_list)} recorded movements")
            for i, record in enumerate(self.record_list):
                angles, speeds, gripper, interval = record
                log.debug(f"Playing movement {i+1}/{len(self.record_list)} - "
                         f"Angles: {angles}, Speeds: {speeds}, Gripper: {gripper}")
                self.mc.set_encoders_drag(angles, speeds)
                self.mc.set_encoder(7, gripper)
            self.playing = False
            log.info("Playback complete")

    def start_loop_play(self):
        """Start loop playback of recorded movements"""
        if not self.playing and self.record_list:
            self.playing = True
            self.play_thread = threading.Thread(target=self._loop_play, daemon=True)
            self.play_thread.start()
            log.info("Loop playback started")

    def _loop_play(self):
        """Loop playback thread"""
        while self.playing:
            self.play_once()

    def stop_loop_play(self):
        """Stop loop playback"""
        if self.playing:
            self.playing = False
            self.play_thread.join()
            log.info("Loop playback stopped")

    def save_recording(self):
        """Save recorded movements to file"""
        if self.record_list:
            log.debug(f"Saving {len(self.record_list)} movements to {self.path}")
            with open(self.path, 'w') as f:
                json.dump(self.record_list, f, indent=2)
            log.info(f"Recording saved to {self.path}")

    def load_recording(self):
        """Load recorded movements from file"""
        if os.path.exists(self.path):
            log.debug(f"Loading recording from {self.path}")
            with open(self.path, 'r') as f:
                self.record_list = json.load(f)
            log.debug(f"Loaded {len(self.record_list)} movements")
            log.info(f"Recording loaded from {self.path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Robot Server with optional debug mode')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    args = parser.parse_args()
    
    if args.debug:
        log.setLevel(logging.DEBUG)
        DEBUG = True
        
    server = RobotServer()
    try:
        server.start()
    except KeyboardInterrupt:
        log.info("Received shutdown signal")
    finally:
        server.cleanup()