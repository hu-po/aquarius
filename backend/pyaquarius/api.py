from fastapi import APIRouter, HTTPException
from .robot import robot_client

router = APIRouter()

@router.post("/robot/command/{command}")
async def send_robot_command(command: str):
    """Send command to robot and return response"""
    response = robot_client.send_command(command)
    if response.startswith("Error") or response == "Not connected to robot server":
        raise HTTPException(status_code=500, detail=response)
    return {"message": response} 