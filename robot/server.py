import socket
import logging
import os
import json
import threading
import time
from typing import Optional, Dict, List
from pymycobot.mycobot import MyCobot
import argparse
from datetime import datetime

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
HOME_POSITION = [0, 24, 108, 96, 0, 0]
HOME_SLEEP = 2

class RobotServer:
    def __init__(self):
        self.mc: Optional[MyCobot] = None
        self.recording = False
        self.playing = False
        self.trajectory = []
        self.record_thread: Optional[threading.Thread] = None
        self.play_thread: Optional[threading.Thread] = None
        self.trajectories_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "trajectories")
        os.makedirs(self.trajectories_dir, exist_ok=True)
        self.active_clients: Dict[str, int] = {}
        self.server_socket: Optional[socket.socket] = None
        self.running = True
        self.home_position = HOME_POSITION
        self.home_speed = 50  # speed percentage when returning to home
        
    def initialize_robot(self) -> bool:
        """Initialize MyCobot connection with retry logic"""
        retry_count = 0
        while self.running:
            try:
                log.debug(f"Attempting to connect to robot on {SERIAL_PORT} at {BAUD_RATE} baud")
                self.mc = MyCobot(SERIAL_PORT, BAUD_RATE, debug=DEBUG)
                self.mc.power_on()
                log.debug("Robot power on successful")
                # Test basic movement
                angles = self.mc.get_encoders()
                log.debug(f"Current robot angles: {angles}")
                if angles is None:
                    raise Exception("Failed to read robot angles")
                log.info("Robot initialized successfully")
                return True
            except Exception as e:
                retry_count += 1
                log.error(f"Failed to initialize robot (attempt {retry_count}): {e}", exc_info=True)
                if retry_count >= 3:
                    log.error("Max robot initialization retries exceeded")
                    return False
                log.debug(f"Waiting 5 seconds before retry {retry_count + 1}")
                time.sleep(5)
        return False

    def handle_command(self, command: str) -> str:
        """Handle incoming commands from client"""
        if not self.mc:
            return "Robot not initialized"
            
        log.debug(f"Received command: {command}")
        try:
            # Basic commands
            if command == "ping":
                return "pong"
            elif command == "q":
                return "quit"
            elif command == "h":
                self.mc.send_angles(self.home_position, self.home_speed)
                time.sleep(HOME_SLEEP)
                return "go to home"
            elif command == "H":
                try:
                    current_angles = self.mc.get_angles()
                    log.debug(f"Current angles: {current_angles}")
                    if not current_angles:
                        return "Failed to get current angles"
                    self.home_position = current_angles
                    log.info(f"Home position set to: {current_angles}")
                    return "set home position"
                except Exception as e:
                    log.error(f"Error setting home position: {str(e)}")
                    return f"Failed to set home position: {str(e)}"
                
            # Extract trajectory name if present
            cmd = command[0]
            traj_name = command[1:] if len(command) > 1 else None
            
            if cmd == "r":
                self.start_record()
                return "Recording started"
            elif cmd == "c":
                self.stop_record()
                return "Recording stopped"
            elif cmd == "p":
                if not self.playing:
                    if traj_name:
                        if self.load_trajectory(traj_name):
                            self.play_once()
                            return f"Playing trajectory: {traj_name}"
                        return f"Failed to load trajectory: {traj_name}"
                    self.play_once()
                    return "Playing current trajectory"
                return "Already playing"
            elif cmd == "P":
                if not self.playing:
                    if traj_name:
                        try:
                            trajectory_list = json.loads(traj_name)  # Expect JSON array of trajectory names
                            if not isinstance(trajectory_list, list):
                                return "Invalid trajectory list format"
                            log.debug(f"Starting playback of {len(trajectory_list)} trajectories")
                            for traj in trajectory_list:
                                log.debug(f"Playing trajectory: {traj}")
                                self.load_trajectory(traj)
                                self.play_once()
                            return f"Playing trajectories: {', '.join(trajectory_list)}"
                        except json.JSONDecodeError:
                            return "Invalid trajectory list format"
                        except Exception as e:
                            log.error(f"Error playing trajectories: {e}")
                            return f"Error: {str(e)}"
                    return "No trajectories provided"
                return "Already playing"
            elif cmd == "s":
                if not traj_name:
                    return "No trajectory name provided"
                return self.save_trajectory(traj_name)
            elif cmd == "l":
                if not traj_name:
                    return "No trajectory name provided"
                if self.load_trajectory(traj_name):
                    return f"Loaded trajectory: {traj_name}"
                return f"Failed to load trajectory: {traj_name}"
            elif cmd == "d":
                if not traj_name:
                    return "No trajectory name provided"
                return self.delete_trajectory(traj_name)
            elif cmd == "f":
                self.mc.release_all_servos()
                return "Robot released"
            elif cmd == "t":
                result = self.list_trajectories()
                return json.dumps(result)
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

    def start_record(self):
        """Start recording robot trajectory"""
        if not self.recording:
            self.trajectory = []
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
                self.trajectory.append([angles, speeds, gripper, 0.1])

    def stop_record(self):
        """Stop recording last recorded trajectory"""
        if self.recording:
            self.recording = False
            self.record_thread.join()
            log.info("Recording stopped")

    def play_once(self):
        """Play last recorded trajectory once"""
        if not self.trajectory:
            log.warning("No trajectory to play")
            return
        self.playing = True
        log.debug(f"Starting playback of {len(self.trajectory)} steps")
        try:
            for i, record in enumerate(self.trajectory):
                angles, speeds, _, interval = record
                log.debug(f"playing trajectory {i+1}/{len(self.trajectory)} - angles: {angles}, speeds: {speeds}")
                self.mc.set_encoders_drag(angles, speeds)
                time.sleep(interval)
        except Exception as e:
            log.error(f"Playback error: {str(e)}")
            self.playing = False
            raise
        self.playing = False
        log.info("Playback complete")

    def save_trajectory(self, name: str) -> str:
        """Save last recorded trajectory to file with specific name"""
        if not self.trajectory:
            log.warning("No trajectory to save")
            return "No trajectory to save"
        
        filepath = os.path.join(self.trajectories_dir, f"{name}.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(self.trajectory, f, indent=2)
            log.info(f"Trajectory saved to {filepath}")
            return f"Trajectory saved: {name}"
        except Exception as e:
            log.error(f"Failed to save trajectory: {e}")
            return f"Error saving trajectory: {str(e)}"

    def load_trajectory(self, name: str) -> bool:
        """Load last recorded trajectory from file with specific name"""
        filepath = os.path.join(self.trajectories_dir, f"{name}.json")
        if not os.path.exists(filepath):
            log.warning(f"Trajectory file not found: {filepath}")
            return False
        
        try:
            with open(filepath, 'r') as f:
                self.trajectory = json.load(f)
            log.info(f"Loaded trajectory {name} with {len(self.trajectory)} steps")
            return True
        except Exception as e:
            log.error(f"Failed to load trajectory: {e}")
            return False

    def delete_trajectory(self, name: str) -> str:
        """Delete last recorded trajectory file"""
        filepath = os.path.join(self.trajectories_dir, f"{name}.json")
        if not os.path.exists(filepath):
            return f"Trajectory not found: {name}"
        
        try:
            os.remove(filepath)
            return f"Deleted trajectory: {name}"
        except Exception as e:
            log.error(f"Failed to delete trajectory: {e}")
            return f"Error deleting trajectory: {str(e)}"

    def list_trajectories(self):
        """List available trajectory files"""
        try:
            files = []
            for filename in os.listdir(self.trajectories_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.trajectories_dir, filename)
                    stat = os.stat(filepath)
                    files.append({
                        'name': filename[:-5],  # Remove .json
                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            return {'trajectories': files}
        except Exception as e:
            log.error(f"Failed to list trajectories: {e}")
            return {'error': str(e)}


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