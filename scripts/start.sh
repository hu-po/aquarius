#!/bin/bash
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [debug]

Components:
  backend      - Python FastAPI backend
  frontend-pc  - React dashboard
  frontend-vr  - VR interface

Options:
  debug    Enable debug logging

Examples:
  $0         # Start all components
  $0 debug   # Start all components with debug logging"
    exit 0
fi

source "$(dirname "$0")/load_env.sh"

if [ "$1" = "debug" ]; then
    echo "🐛 Debug logging enabled"
    LOG_LEVEL=DEBUG docker compose up --build
else
    docker compose up -d --build
fi

echo "🌐 Access URLs:

Backend:     http://${HOST_IP}:8000

Frontend PC: http://${HOST_IP}:3000

Frontend VR: http://${HOST_IP}:3001

"
