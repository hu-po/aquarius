#!/bin/bash
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [component...]

Components:
  backend      - Start the Python FastAPI backend
  frontend-pc  - Start the React dashboard
  frontend-vr  - Start the VR interface

If no component is specified, all components will be started.
Multiple components can be specified, separated by spaces.

Examples:
  $0                   # Start all components
  $0 backend          # Start only the backend
  $0 frontend-pc      # Start only the PC frontend
  $0 backend frontend-pc  # Start backend and PC frontend
  $0 debug               # Start all components with debug logging"
    exit 0
fi

source "$(dirname "$0")/load_env.sh"

start_components() {
    local components=("$@")
    local env_vars=""
    if [[ " ${components[@]} " =~ " debug " ]]; then
        env_vars="LOG_LEVEL=DEBUG"
        components=("${components[@]/debug/}")
        echo "🐛 Debug logging enabled"
    fi
    
    [ ${#components[@]} -eq 0 ] && echo "▶️  Starting all..." || echo "▶️  Starting: ${components[*]}"
    if [ -n "$env_vars" ]; then
        LOG_LEVEL=DEBUG docker compose up -d --build "${components[@]}"
    else
        docker compose up -d --build "${components[@]}"
    fi
}

echo "🌐 Access URLs:
Backend:     http://${HOST_IP}:8000
Frontend PC: http://${HOST_IP}:3000
Frontend VR: http://${HOST_IP}:3001"

start_components "$@"
