# Aquarius 🐟

aquarium monitoring system

backend: fastapi + python
- uses openai, gemini, claude, and mistral vision language models via api. async sends an image to each api and gets back text descriptions of the image.
- stores images and descriptions in a local database
- serves images and descriptions to the frontend

frontend-pc: react
- dashboard intended for a browser on local aquarium pc screen
- displays text based summary of tank
- interactive widget to displays images and descriptions, selectable via a timeline

frontend-vr: aframe
- vr box representing aquarium with points representing fish location
- mixed reality view of aquarium and fish

## Setup

### Backend

```bash
uvicorn pyaquarius.main:app --reload
```

Access the API at http://localhost:8000 with the following endpoints:

```
GET /status - Current aquarium status
POST /capture - Capture new image
POST /readings - Add sensor readings
GET /images - List recent images
GET /readings/history - Get reading history
GET /devices - List camera devices
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