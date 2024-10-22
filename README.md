
# Aquarius 🐟

Aquarium monitoring system with both a PC dashboard and a VR interface for visualizing fish positions, sensor data, and tank images.

## Components

- **Backend**: Python (FastAPI) that processes camera captures and integrates with multiple vision-language models (VLMs).
- **Frontend (PC)**: React-based dashboard for real-time monitoring of tank status.
- **Frontend (VR)**: A-Frame VR application for visualizing the aquarium in mixed reality.

## Prerequisites

- Docker and Docker Compose installed.
- Node.js and npm for local development of the frontends.
- A valid API key for each of the vision-language models (OpenAI, Gemini, Claude, Mistral).
  
### 1. Building and Running the Project

### Backend

The backend uses FastAPI to capture images from a connected camera, analyze them using vision-language models, and serve sensor data.

#### Setup

1. **Install Python dependencies (for local development)**:
    ```bash
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```

2. **Run the backend**:
    ```bash
    uvicorn pyaquarius.main:app --reload
    ```

3. **Using Docker** (recommended):
    ```bash
    cd backend
    docker build -t aquarius-backend .
    docker run -p 8000:8000 aquarius-backend
    ```

4. **Access the backend API**:
    - The API will be accessible at: `http://localhost:8000`
    - Endpoints:
      - `GET /status`: Current aquarium status (sensor readings, latest image, etc.)
      - `POST /capture`: Capture a new image.
      - `GET /images`: List recent images.
      - `GET /readings/history`: Get sensor readings history.

#### Running with Docker Compose

To run all components together (backend and frontends) using Docker Compose:

1. **Start the whole system**:
    ```bash
    ./scripts/start.sh
    ```

2. **Stop the system**:
    ```bash
    ./scripts/stop.sh
    ```

This will build and run all services (backend, frontend-pc, frontend-vr) in one command.

---

### Frontend (PC Dashboard)

The frontend for PC is a React app that displays a dashboard with real-time updates on the aquarium status, including the latest image, sensor data, and AI analysis.

#### Setup

1. **Install dependencies**:
    ```bash
    cd frontend-pc
    npm install
    ```

2. **Run the development server**:
    ```bash
    npm start
    ```

3. **Build for production**:
    ```bash
    npm run build
    ```

#### Running with Docker

1. **Build the Docker image**:
    ```bash
    cd frontend-pc
    docker build -t aquarius-frontend-pc .
    ```

2. **Run the container**:
    ```bash
    docker run -p 3000:3000 aquarius-frontend-pc
    ```

The PC dashboard will be accessible at `http://localhost:3000`.

---

### Frontend (VR)

The VR frontend is built using A-Frame, allowing you to visualize the aquarium in mixed reality with fish positions.

#### Setup

1. **Run the VR app**:

    ```bash
    cd frontend-vr
    npm start
    ```

2. **Run the VR frontend with Docker**:

    ```bash
    cd frontend-vr
    docker build -t aquarius-frontend-vr .
    docker run -p 3001:3001 aquarius-frontend-vr
    ```

Access the VR frontend at `http://localhost:3001`.

---

### 2. Testing

#### Backend

You can test the backend's API using curl or any API client like Postman:

- **Capture an image**:
    ```bash
    curl -X POST http://localhost:8000/capture -d '{"device_id": 0}'
    ```

- **Get aquarium status**:
    ```bash
    curl http://localhost:8000/status
    ```

#### Frontend (PC Dashboard)

You can test the React app by running the development server (`npm start`) and ensuring the dashboard updates based on real-time data from the backend.

#### Frontend (VR)

Test the VR frontend by opening the `index.html` in a browser and interacting with the A-Frame scene.

---

<!-- ## Video

[![YouTube Video](https://img.youtube.com/vi/TBD/0.jpg)](https://www.youtube.com/watch?v=TBD) -->

## Citation

```
@misc{hupo2024aquarius,
  title={Aquarius: PC + VR dashboard for aquarium monitoring using VLMs},
  author={Hugo Ponte},
  year={2024},
  url={https://github.com/hu-po/aquarius}
}
```