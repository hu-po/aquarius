# Aquarius 🐟

Aquarium monitoring system with both a PC dashboard and a VR interface for visualizing fish positions, sensor data, and tank images.

## Components

- `backend`: Python (FastAPI) that processes camera captures and integrates with multiple AI apis.
- `robot`: Python (MyCobot280PI) that controls the robotic arm.
- `frontend-pc`: React-based dashboard for real-time monitoring of tank status.
- `frontend-vr`: A-Frame VR application for visualizing the aquarium in mixed reality.

## Usage

Uses docker compose, all config stored in `.env` file. Make sure to add API keys for OpenAI, Gemini, Claude.

Use the scripts in `scripts` to start the services on the master robot node, then access dashboards on pc/mobile/vr.

```bash
# start services on agx orin (docker compose)
./scripts/start.sh
./scripts/stop.sh
./scripts/clean.sh # CAUTION: removes all local data
# start robot on mycobot 280 pi
./scripts/start-robot.sh
```

<!-- ## Video

[![YouTube Video](https://img.youtube.com/vi/TBD/0.jpg)](https://www.youtube.com/watch?v=TBD) -->

## Architecture

```mermaid
flowchart TB
    subgraph Physical Setup["{Physical Setup}"]
        direction LR
        camera1["📷 Camera 1"] --- aquarium1["🐟 Aquarium 1"]
        aquarium1 --- aquarium2["🐠 Aquarium 2"]
        aquarium2 --- camera2["📷 Camera 2"]
        robot_arm["🦾 Robot Arm"] --- aquarium1
        robot_arm --- aquarium2
    end
    
    subgraph AGX Orin["AGX Orin (192.168.x.x)"]
        backend["backend\nFastAPI"]
        fe_pc["frontend-pc\nReact"]
        fe_vr["frontend-vr\nA-Frame"]
        robot_client["robot-client\nMyCobotSocket"]
        backend -- "HTTP:8000" --> fe_pc
        backend -- "HTTP:8000" --> fe_vr
        backend -- "HTTP:3002" --> robot_client
    end
    
    subgraph Robot["MyCobot280PI (192.168.x.y)"]
        robot_server["robot-server"]
    end
    
    subgraph Remote Devices
        pc["💻 PC Browser"]
        vr["🥽 VR Browser"]
        phone["📱 Mobile Browser"]
    end
    
    camera1 -- "USB" --> backend
    camera2 -- "USB" --> backend
    fe_pc -- "HTTP:3000" --> pc
    fe_pc -- "HTTP:3000" --> phone
    fe_vr -- "HTTP:3001" --> vr
    robot_client -- "TCP/IP" --> robot_server
    robot_server -- "Serial" --> robot_arm

    style Physical Setup fill:#e8f4ff,stroke:#0088cc
    style aquarium1 fill:#e2f5ff,stroke:#0088cc
    style aquarium2 fill:#e2f5ff,stroke:#0088cc
    style AGX Orin fill:#f5f5f5,stroke:#666666
    style camera1 fill:#f9f9f9,stroke:#999999
    style camera2 fill:#f9f9f9,stroke:#999999
    style backend fill:#ddfbe7,stroke:#28a745
    style fe_pc fill:#fff3cd,stroke:#ffc107
    style fe_vr fill:#f8d7da,stroke:#dc3545
    style pc fill:#cce5ff,stroke:#0056b3
    style vr fill:#d7d8f8,stroke:#6610f2
    style phone fill:#cce5ff,stroke:#0056b3
    style Robot Pi fill:#ffe6cc,stroke:#ff9900
    style robot_client fill:#f5e6ff,stroke:#9933cc
    style robot_control fill:#ffe6cc,stroke:#ff9900
    style robot_arm fill:#ffe6cc,stroke:#ff9900
```

## Citation

```
@misc{hupo2024aquarius,
  title={Aquarius: AI Aquarium Monitoring},
  author={Hugo Ponte},
  year={2024},
  url={https://github.com/hu-po/aquarius}
}
```