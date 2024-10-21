#!/bin/bash

# Check if a path was provided
if [ -z "$1" ]; then
    echo "Usage: ./create_aquarium_monitor.sh /path/to/your/project"
    exit 1
fi

# Set the base directory
BASE_DIR="$1/aquarium-monitor"

# Create base directory
mkdir -p "$BASE_DIR"

# Navigate to the base directory
cd "$BASE_DIR" || exit

echo "Creating project structure at $BASE_DIR..."

# Create backend structure
mkdir -p backend/app/{core,api/v1/endpoints,models,schemas,services,utils}
touch backend/app/__init__.py
touch backend/app/main.py
touch backend/app/core/__init__.py
touch backend/app/core/config.py
touch backend/app/api/__init__.py
touch backend/app/api/v1/__init__.py
touch backend/app/api/v1/endpoints/__init__.py
touch backend/app/api/v1/endpoints/{camera.py,fish.py,llm.py,system.py}
touch backend/app/models/__init__.py
touch backend/app/models/{fish.py,system.py}
touch backend/app/schemas/__init__.py
touch backend/app/schemas/{fish.py,system.py}
touch backend/app/services/__init__.py
touch backend/app/services/{camera_service.py,fish_service.py,llm_service.py}
touch backend/app/utils/__init__.py
touch backend/app/utils/{camera.py,fish_tracker.py,vlm_api.py}
touch backend/requirements.txt
touch backend/Dockerfile

# Populate backend/main.py
cat << EOF > backend/app/main.py
from fastapi import FastAPI
from app.api.v1.endpoints import camera, fish, llm, system

app = FastAPI()

app.include_router(camera.router, prefix="/api/v1/camera", tags=["camera"])
app.include_router(fish.router, prefix="/api/v1/fish", tags=["fish"])
app.include_router(llm.router, prefix="/api/v1/llm", tags=["llm"])
app.include_router(system.router, prefix="/api/v1/system", tags=["system"])
EOF

# Populate backend/requirements.txt
cat << EOF > backend/requirements.txt
fastapi
uvicorn[standard]
opencv-python
requests
pydantic
EOF

# Populate backend/Dockerfile
cat << EOF > backend/Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# Create frontend-dashboard structure
mkdir -p frontend-dashboard/{public,src/{components/{Dashboard,FishPositionPlot,LatestImage,LLMReply,Stats},services,styles,assets}}
touch frontend-dashboard/src/{App.js,index.js}
touch frontend-dashboard/src/services/api.js
touch frontend-dashboard/package.json
touch frontend-dashboard/Dockerfile

# Create component files for frontend-dashboard
for component in Dashboard FishPositionPlot LatestImage LLMReply Stats
do
  mkdir -p "frontend-dashboard/src/components/$component"
  touch "frontend-dashboard/src/components/$component/$component.js"
  touch "frontend-dashboard/src/components/$component/$component.css"
  touch "frontend-dashboard/src/components/$component/index.js"
done

# Populate frontend-dashboard/src/App.js
cat << EOF > frontend-dashboard/src/App.js
import React from 'react';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <div className="App">
      <Dashboard />
    </div>
  );
}

export default App;
EOF

# Populate frontend-dashboard/package.json
cat << EOF > frontend-dashboard/package.json
{
  "name": "frontend-dashboard",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "axios": "^0.24.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  }
}
EOF

# Populate frontend-dashboard/Dockerfile
cat << EOF > frontend-dashboard/Dockerfile
FROM node:14-alpine

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . ./

CMD ["npm", "start"]
EOF

# Create frontend-vr structure
mkdir -p frontend-vr/{public,src/{components/AquariumVR,assets,styles}}
touch frontend-vr/src/{App.js,index.js}
touch frontend-vr/package.json
touch frontend-vr/Dockerfile

# Create component files for frontend-vr
mkdir -p frontend-vr/src/components/AquariumVR
touch frontend-vr/src/components/AquariumVR/{AquariumVR.js,AquariumVR.css,index.js}

# Populate frontend-vr/src/App.js
cat << EOF > frontend-vr/src/App.js
import React from 'react';
import AquariumVR from './components/AquariumVR';

function App() {
  return (
    <div className="App">
      <AquariumVR />
    </div>
  );
}

export default App;
EOF

# Populate frontend-vr/package.json
cat << EOF > frontend-vr/package.json
{
  "name": "frontend-vr",
  "version": "1.0.0",
  "private": true,
  "dependencies": {
    "react": "^18.0.0",
    "aframe": "^1.3.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build"
  }
}
EOF

# Populate frontend-vr/Dockerfile
cat << EOF > frontend-vr/Dockerfile
FROM node:14-alpine

WORKDIR /app

COPY package.json ./

RUN npm install

COPY . ./

CMD ["npm", "start"]
EOF

# Create root-level files
touch docker-compose.yml README.md .env .gitignore

# Populate docker-compose.yml
cat << EOF > docker-compose.yml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app
    env_file:
      - ./.env

  frontend-dashboard:
    build: ./frontend-dashboard
    ports:
      - "3000:3000"
    volumes:
      - ./frontend-dashboard:/app
    env_file:
      - ./.env

  frontend-vr:
    build: ./frontend-vr
    ports:
      - "4000:3000"
    volumes:
      - ./frontend-vr:/app
    env_file:
      - ./.env
EOF

# Populate README.md
cat << EOF > README.md
# Aquarium Monitor Project

This project monitors an aquarium using cameras and displays data through a dashboard and VR experience.

## Project Structure

- **backend/**: FastAPI backend application.
- **frontend-dashboard/**: React frontend dashboard.
- **frontend-vr/**: A-Frame VR frontend application.
- **docker-compose.yml**: Orchestrates the services using Docker.

## Getting Started

To run the application:

1. Install Docker and Docker Compose.
2. Create a \`.env\` file with necessary environment variables.
3. Run \`docker-compose up --build\`.

EOF

# Populate .gitignore
cat << EOF > .gitignore
.env
node_modules/
__pycache__/
*.pyc
EOF

# Create scripts directory and scripts
mkdir -p scripts
touch scripts/start.sh scripts/stop.sh

# Populate scripts/start.sh
cat << 'EOF' > scripts/start.sh
#!/bin/bash

docker-compose up --build -d
EOF

# Populate scripts/stop.sh
cat << 'EOF' > scripts/stop.sh
#!/bin/bash

docker-compose down
EOF

# Make scripts executable
chmod +x scripts/start.sh scripts/stop.sh

echo "Project structure created successfully at $BASE_DIR"
