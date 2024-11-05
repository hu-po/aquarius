from fastapi import APIRouter, HTTPException
import socket
import logging
from typing import Dict
from pydantic import BaseModel

router = APIRouter()
log = logging.getLogger(__name__)

class RobotCommand(BaseModel):
    command: str

@router.post("/command")
async def send_robot_command(cmd: RobotCommand) -> Dict[str, str]:
    """Send command to robot client"""
    try:
        # Connect to robot client
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("robot-client", 9000))
        
        # Send command
        sock.sendall(cmd.command.encode('utf-8'))
        
        # Get response
        response = sock.recv(1024).decode('utf-8')
        
        return {"message": f"Command sent: {response}"}
        
    except Exception as e:
        log.error(f"Failed to send robot command: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        sock.close() 