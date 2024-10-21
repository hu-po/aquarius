#!/bin/bash

# Check if the path is provided
if [ -z "$1" ]; then
  echo "Please provide the project path."
  exit 1
fi

PROJECT_PATH=$1

# Create the project structure
mkdir -p "$PROJECT_PATH"/{backend/{app,static,routes},frontend-dashboard/{public,src/components,src/api},frontend-vr/{public,src/components}}

# Backend - FastAPI Structure
echo "Creating backend files..."

cat > "$PROJECT_PATH/backend/app/main.py" <<EOL
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Aquarium Monitor Backend is Running"}
EOL

cat > "$PROJECT_PATH/backend/app/camera.py" <<EOL
import cv2

def capture_image():
    # OpenCV logic to capture image from the camera
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    return frame
EOL

cat > "$PROJECT_PATH/backend/app/vlm_api.py" <<EOL
def send_image_to_vlm(image):
    # Logic to send image to VLM and receive a response
    return "Text response from VLM"
EOL

cat > "$PROJECT_PATH/backend/app/fish_tracker.py" <<EOL
def track_fish_positions(vlm_response):
    # Logic to extract fish positions from the VLM response
    return [{"fish": 1, "x": 100, "y": 200}]
EOL

cat > "$PROJECT_PATH/backend/app/routes/fish.py" <<EOL
from fastapi import APIRouter
from .camera import capture_image
from .vlm_api import send_image_to_vlm
from .fish_tracker import track_fish_positions

router = APIRouter()

@router.get("/fish")
async def get_fish_positions():
    # Capture image
    image = capture_image()
    # Send image to VLM and get response
    vlm_response = send_image_to_vlm(image)
    # Track fish positions
    positions = track_fish_positions(vlm_response)
    return {"positions": positions}
EOL

cat > "$PROJECT_PATH/backend/app/routes/system.py" <<EOL
from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
async def get_status():
    # Return system status, temperature data, etc.
    return {"status": "System running", "temperature": 78}
EOL

# __init__.py for routes
touch "$PROJECT_PATH/backend/app/routes/__init__.py"
touch "$PROJECT_PATH/backend/app/models.py"
touch "$PROJECT_PATH/backend/app/__init__.py"

cat > "$PROJECT_PATH/backend/requirements.txt" <<EOL
fastapi
opencv-python
uvicorn
EOL

cat > "$PROJECT_PATH/backend/Dockerfile" <<EOL
FROM python:3.9-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOL

# Frontend - React Dashboard Structure
echo "Creating React Dashboard files..."

cat > "$PROJECT_PATH/frontend-dashboard/src/components/FishPlot.js" <<EOL
import React from 'react';

const FishPlot = () => {
    return <div>Fish position plot will go here</div>;
};

export default FishPlot;
EOL

cat > "$PROJECT_PATH/frontend-dashboard/src/components/RecentImage.js" <<EOL
import React from 'react';

const RecentImage = () => {
    return <div>Recent image from the camera will go here</div>;
};

export default RecentImage;
EOL

cat > "$PROJECT_PATH/frontend-dashboard/src/components/LLMReply.js" <<EOL
import React from 'react';

const LLMReply = () => {
    return <div>LLM reply will go here</div>;
};

export default LLMReply;
EOL

cat > "$PROJECT_PATH/frontend-dashboard/src/components/Stats.js" <<EOL
import React from 'react';

const Stats = () => {
    return <div>System stats like temperature will go here</div>;
};

export default Stats;
EOL

cat > "$PROJECT_PATH/frontend-dashboard/src/api/api.js" <<EOL
export const fetchFishPositions = async () => {
    const response = await fetch('/api/fish');
    return await response.json();
};

export const fetchSystemStatus = async () => {
    const response = await fetch('/api/status');
    return await response.json();
};
EOL

cat > "$PROJECT_PATH/frontend-dashboard/src/App.js" <<EOL
import React from 'react';
import FishPlot from './components/FishPlot';
import RecentImage from './components/RecentImage';
import LLMReply from './components/LLMReply';
import Stats from './components/Stats';

const App = () => {
    return (
        <div>
            <h1>Aquarium Monitor Dashboard</h1>
            <FishPlot />
            <RecentImage />
            <LLMReply />
            <Stats />
        </div>
    );
};

export default App;
EOL

cat > "$PROJECT_PATH/frontend-dashboard/src/index.js" <<EOL
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(<App />, document.getElementById('root'));
EOL

cat > "$PROJECT_PATH/frontend-dashboard/package.json" <<EOL
{
  "name": "frontend-dashboard",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0"
  }
}
EOL

cat > "$PROJECT_PATH/frontend-dashboard/Dockerfile" <<EOL
FROM node:16-alpine
WORKDIR /app
COPY . /app
RUN npm install
CMD ["npm", "start"]
EOL

# Frontend - Aframe VR Structure
echo "Creating Aframe VR files..."

cat > "$PROJECT_PATH/frontend-vr/src/components/AquariumVR.js" <<EOL
import React, { useEffect } from 'react';

const AquariumVR = () => {
    useEffect(() => {
        // Initialize Aframe scene with fish positions
    }, []);

    return <a-scene></a-scene>;
};

export default AquariumVR;
EOL

cat > "$PROJECT_PATH/frontend-vr/src/App.js" <<EOL
import React from 'react';
import AquariumVR from './components/AquariumVR';

const App = () => {
    return (
        <div>
            <h1>Aquarium VR</h1>
            <AquariumVR />
        </div>
    );
};

export default App;
EOL

cat > "$PROJECT_PATH/frontend-vr/src/index.js" <<EOL
import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(<App />, document.getElementById('root'));
EOL

cat > "$PROJECT_PATH/frontend-vr/package.json" <<EOL
{
  "name": "frontend-vr",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "aframe": "^1.2.0"
  }
}
EOL

cat > "$PROJECT_PATH/frontend-vr/Dockerfile" <<EOL
FROM node:16-alpine
WORKDIR /app
COPY . /app
RUN npm install
CMD ["npm", "start"]
EOL

# Docker Compose
cat > "$PROJECT_PATH/docker-compose.yml" <<EOL
version: '3'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
  frontend-dashboard:
    build: ./frontend-dashboard
    ports:
      - "3000:3000"
  frontend-vr:
    build: ./frontend-vr
    ports:
      - "3001:3001"
EOL

# .env file
cat > "$PROJECT_PATH/.env" <<EOL
# Environment variables
LLM_API_KEY=your_llm_api_key_here
CAMERA_DEVICE_ID=0
EOL

# README.md
cat > "$PROJECT_PATH/README.md" <<EOL
# Aquarium Monitor App

This project is an aquarium monitor application with the following components:
- **Backend**: FastAPI for handling API requests, using OpenCV to capture images from a camera, and sending these images to an LLM/VLM for processing.
- **Frontend Dashboard**: React-based dashboard for displaying real-time fish positions, system status, and recent images.
- **VR Frontend**: Aframe-based VR frontend showing a 3D cube aquarium with dynamic fish positions.

## Setup

### Backend
1. Navigate to \`backend\` directory.
2. Install dependencies: \`pip install -r requirements.txt\`
3. Run the backend: \`uvicorn app.main:app --reload\`

### Frontend Dashboard
1. Navigate to \`frontend-dashboard\` directory.
2. Install dependencies: \`npm install\`
3. Start the frontend: \`npm start\`

### Frontend
