# Aquarius 🐟

Aquarium monitoring system with both a PC dashboard and a VR interface for visualizing fish positions, sensor data, and tank images.

## Prerequisites

- Docker and Docker Compose
- Node.js and npm (for local development)
- API keys: OpenAI, Gemini, Claude, Mistral

## Components

- `backend`: Python (FastAPI) that processes camera captures and integrates with multiple vision-language models (VLMs).
- `frontend-pc`: React-based dashboard for real-time monitoring of tank status.
- `frontend-vr`: A-Frame VR application for visualizing the aquarium in mixed reality.

## Setup & Running

1. Set up environment variables:
```bash
cp .env.example .env  # Edit with your API keys
```

2. Start components individually:
```bash
./scripts/start.sh backend        # Start only backend
./scripts/start.sh frontend-pc    # Start only PC dashboard
./scripts/start.sh frontend-vr    # Start only VR interface
```

Or start everything:
```bash
./scripts/start.sh  # Starts all components
```

3. Access interfaces:
- Backend API: http://localhost:8000
- PC Dashboard: http://localhost:3000 
- VR Interface: http://localhost:3001

4. Stop components:
```bash
./scripts/stop.sh backend         # Stop backend
./scripts/stop.sh frontend-pc     # Stop PC dashboard
./scripts/stop.sh frontend-vr     # Stop VR interface
./scripts/stop.sh                 # Stop everything
```

## API Endpoints

```
GET /status             - Get current aquarium status
POST /capture           - Capture new image
GET /images             - List captured images
GET /readings/history   - Get sensor reading history
GET /devices            - List available camera devices
```

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