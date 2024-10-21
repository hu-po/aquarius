# Aquarium Monitor App

This project is an aquarium monitor application with the following components:
- **Backend**: FastAPI for handling API requests, using OpenCV to capture images from a camera, and sending these images to an LLM/VLM for processing.
- **Frontend Dashboard**: React-based dashboard for displaying real-time fish positions, system status, and recent images.
- **VR Frontend**: Aframe-based VR frontend showing a 3D cube aquarium with dynamic fish positions.

## Setup

### Backend
1. Navigate to `backend` directory.
2. Install dependencies: `pip install -r requirements.txt`
3. Run the backend: `uvicorn app.main:app --reload`

### Frontend PC
1. Navigate to `frontend-dashboard` directory.
2. Install dependencies: `npm install`
3. Start the frontend: `npm start`

### Frontend VR
