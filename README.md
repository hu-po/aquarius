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
./scripts/start.sh debug # start with debug logging
./scripts/stop.sh # stops services
./scripts/clean.sh # CAUTION: removes all local data
./scripts/stop.sh && ./scripts/clean.sh # wipe
# start robot on mycobot 280 pi
./scripts/start-robot.sh
# start robot server (on robot)
sudo python3 robot/server.py --debug # start with debug logging
git pull && sudo pkill python* && sudo rm -rf robot/trajectories/ # wipe
```

<!-- ## Video

[![YouTube Video](https://img.youtube.com/vi/TBD/0.jpg)](https://www.youtube.com/watch?v=TBD) -->

## Architecture

```mermaid
flowchart TB
    aquarium1["🐟 Aquarium 1"]--- camera1["📷 Camera 1"]
    aquarium2["🐠 Aquarium 2"]--- camera2["📷 Camera 2"]
    robot_arm["🦾 Robot Arm"] --- aquarium1
    robot_arm --- aquarium2
    
    subgraph Compute["AGX Orin (192.168.x.x)"]
        backend["backend"]
        fe_pc["frontend-pc"]
        fe_vr["frontend-vr"]
        robot_client["client"]
        backend -- "HTTP:8000" --> fe_pc
        backend -- "HTTP:8000" --> fe_vr
        backend -- "HTTP:3002" --> robot_client
    end
    
    subgraph Robot["MyCobot280PI (192.168.x.y)"]
        robot_server["server"]
    end
    
    subgraph Remote_Devices["Remote Devices"]
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

    %% Hardware components
    style aquarium1 fill:#b3e0ff,stroke:#0066cc
    style aquarium2 fill:#b3e0ff,stroke:#0066cc
    style camera1 fill:#e6e6e6,stroke:#666666
    style camera2 fill:#e6e6e6,stroke:#666666
    style robot_arm fill:#ffcc80,stroke:#ff8c00

    %% Compute node
    style Compute fill:#f8f9fa,stroke:#495057
    style backend fill:#28a745,stroke:#1e7e34,color:#ffffff
    style fe_pc fill:#007bff,stroke:#0056b3,color:#ffffff
    style fe_vr fill:#6610f2,stroke:#520dc2,color:#ffffff
    style robot_client fill:#dc3545,stroke:#bd2130,color:#ffffff

    %% Robot node
    style Robot fill:#fff3cd,stroke:#ffc107
    style robot_server fill:#fd7e14,stroke:#d63384,color:#ffffff

    %% Client devices
    style Remote_Devices fill:#f8f9fa,stroke:#495057
    style pc fill:#20c997,stroke:#0ca678
    style vr fill:#6f42c1,stroke:#59359a
    style phone fill:#20c997,stroke:#0ca678
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

## TODO

- [ ] unified config management through frontend menus, store in backend db
- [ ] page to see associated images for each life
- [ ] voting system for ai analysis to collect fine tuning data
- [ ] human verification of associated images and each model response
- [ ] sort life.csv based on last seen
- [ ] temperature measurements during scan, maybe a separate function?
- [ ] links and back of the envelope calculation of cost per day, api?
- [ ] play trajectory backwards for collision avoidance
- [ ] use megalithic corner overlap style to reduce thermometers
- [ ] spray paint robot arm green
- [ ] trajectories should be managed on compute node, robot just plays
    - home position is a trajectory