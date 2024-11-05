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
    log.debug(f"Received robot command: {cmd.command}")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log.debug("Connecting to localhost:9000")
        sock.connect(("localhost", 9000))
        
        log.debug(f"Sending command: {cmd.command}")
        sock.sendall(cmd.command.encode('utf-8'))
        
        log.debug("Waiting for response")
        response = sock.recv(1024).decode('utf-8')
        log.debug(f"Received response: {response}")
        
        return {"message": f"Command sent: {response}"}
        
    except Exception as e:
        log.error(f"Failed to send robot command: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    finally:
        sock.close() 