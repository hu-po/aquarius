import socket
import logging
import os
import json
import threading
from typing import Optional
from pymycobot.mycobot import MyCobot

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
        
    def initialize(self):
        """Initialize MyCobot connection"""
        try:
            self.mc = MyCobot(SERIAL_PORT, BAUD_RATE, debug=DEBUG)
            self.mc.power_on()
            log.info("Robot initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize robot: {e}")
            raise

    def handle_command(self, command: str) -> str:
        """Handle incoming commands from client"""
        log.debug(f"Received command: {command}")
        
        if command == "q":
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

    def start(self):
        """Start the robot server"""
        self.initialize()
        
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((HOST, PORT))
        server.listen(1)
        log.info(f"Server listening on {HOST}:{PORT}")

        try:
            while True:
                conn, addr = server.accept()
                log.info(f"Connected by {addr}")
                
                try:
                    while True:
                        data = conn.recv(BUFFER_SIZE)
                        if not data:
                            break
                            
                        command = data.decode('utf-8').strip()
                        response = self.handle_command(command)
                        conn.sendall(response.encode('utf-8'))
                        
                        if response == "quit":
                            break
                            
                except Exception as e:
                    log.error(f"Error handling client: {e}")
                finally:
                    conn.close()
                    
        except KeyboardInterrupt:
            log.info("Server shutting down")
        finally:
            server.close()

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
            for record in self.record_list:
                angles, speeds, gripper, interval = record
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
            with open(self.path, 'w') as f:
                json.dump(self.record_list, f, indent=2)
            log.info(f"Recording saved to {self.path}")

    def load_recording(self):
        """Load recorded movements from file"""
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                self.record_list = json.load(f)
            log.info(f"Recording loaded from {self.path}")

if __name__ == "__main__":
    server = RobotServer()
    server.start()