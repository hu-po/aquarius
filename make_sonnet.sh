#!/bin/bash

# Check if a path argument is provided
if [ $# -eq 0 ]; then
    echo "Please provide a path for the project."
    exit 1
fi

# Set the project root directory
PROJECT_ROOT="$1/aquarium_monitor"

# Create the main project directory
mkdir -p "$PROJECT_ROOT"

# Create backend structure
mkdir -p "$PROJECT_ROOT/backend/app/routers" "$PROJECT_ROOT/backend/app/services" "$PROJECT_ROOT/backend/app/models"

# Create backend files
touch "$PROJECT_ROOT/backend/app/__init__.py"
touch "$PROJECT_ROOT/backend/app/main.py"
touch "$PROJECT_ROOT/backend/app/routers/__init__.py"
touch "$PROJECT_ROOT/backend/app/routers/camera.py"
touch "$PROJECT_ROOT/backend/app/routers/fish_tracking.py"
touch "$PROJECT_ROOT/backend/app/routers/llm.py"
touch "$PROJECT_ROOT/backend/app/services/__init__.py"
touch "$PROJECT_ROOT/backend/app/services/camera_service.py"
touch "$PROJECT_ROOT/backend/app/services/fish_tracking_service.py"
touch "$PROJECT_ROOT/backend/app/services/llm_service.py"
touch "$PROJECT_ROOT/backend/app/models/__init__.py"
touch "$PROJECT_ROOT/backend/app/models/fish.py"
touch "$PROJECT_ROOT/backend/requirements.txt"
touch "$PROJECT_ROOT/backend/Dockerfile"

# Create frontend-dashboard structure
mkdir -p "$PROJECT_ROOT/frontend-dashboard/public" "$PROJECT_ROOT/frontend-dashboard/src/components" "$PROJECT_ROOT/frontend-dashboard/src/services"

# Create frontend-dashboard files
touch "$PROJECT_ROOT/frontend-dashboard/src/components/Dashboard.js"
touch "$PROJECT_ROOT/frontend-dashboard/src/components/FishPositionPlot.js"
touch "$PROJECT_ROOT/frontend-dashboard/src/components/LatestImage.js"
touch "$PROJECT_ROOT/frontend-dashboard/src/services/api.js"
touch "$PROJECT_ROOT/frontend-dashboard/src/App.js"
touch "$PROJECT_ROOT/frontend-dashboard/src/index.js"
touch "$PROJECT_ROOT/frontend-dashboard/package.json"
touch "$PROJECT_ROOT/frontend-dashboard/Dockerfile"

# Create frontend-vr structure
mkdir -p "$PROJECT_ROOT/frontend-vr/js/components" "$PROJECT_ROOT/frontend-vr/assets/textures"

# Create frontend-vr files
touch "$PROJECT_ROOT/frontend-vr/index.html"
touch "$PROJECT_ROOT/frontend-vr/js/main.js"
touch "$PROJECT_ROOT/frontend-vr/js/components/aquarium.js"
touch "$PROJECT_ROOT/frontend-vr/js/components/fish.js"
touch "$PROJECT_ROOT/frontend-vr/Dockerfile"

# Create docker-compose file
touch "$PROJECT_ROOT/docker-compose.yml"

# Add some basic content to main files
echo "from fastapi import FastAPI

app = FastAPI()

@app.get('/')
async def root():
    return {'message': 'Welcome to the Aquarium Monitor API'}" > "$PROJECT_ROOT/backend/app/main.py"

echo "import React from 'react';
import ReactDOM from 'react-dom';
import App from './App';

ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById('root')
);" > "$PROJECT_ROOT/frontend-dashboard/src/index.js"

echo "<!DOCTYPE html>
<html>
  <head>
    <meta charset='utf-8'>
    <title>Aquarium VR</title>
    <script src='https://aframe.io/releases/1.2.0/aframe.min.js'></script>
    <script src='js/components/aquarium.js'></script>
    <script src='js/components/fish.js'></script>
    <script src='js/main.js'></script>
  </head>
  <body>
    <a-scene>
      <!-- Your A-Frame content will go here -->
    </a-scene>
  </body>
</html>" > "$PROJECT_ROOT/frontend-vr/index.html"

echo "version: '3'
services:
  backend:
    build: ./backend
    ports:
      - '8000:8000'
  frontend-dashboard:
    build: ./frontend-dashboard
    ports:
      - '3000:3000'
  frontend-vr:
    build: ./frontend-vr
    ports:
      - '8080:80'" > "$PROJECT_ROOT/docker-compose.yml"

echo "Project structure created successfully at $PROJECT_ROOT"