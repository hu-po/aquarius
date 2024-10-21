# Aquarius 🐟

This project is an aquarium monitor application with the following components:

- **Backend**: FastAPI for handling API requests, using OpenCV to capture images from a camera, and sending these images to an LLM/VLM for processing.
- **Frontend Dashboard**: React-based dashboard for displaying real-time fish positions, system status, and recent images.
- **VR Frontend**: Aframe-based VR frontend showing a 3D cube aquarium with dynamic fish positions.

## Setup

### Backend

```bash
uvicorn pyaquarius.main:app --reload
```

### Frontend PC

```bash
npm install
npm start
```

### Frontend VR

```bash
npm install
npm start
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