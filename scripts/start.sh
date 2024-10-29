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
  $0 backend frontend-pc  # Start backend and PC frontend"
    exit 0
fi

# Setup environment if needed
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Running setup..."
    "$(dirname "$0")/setup.sh" || { echo "❌ Setup failed"; exit 1; }
    echo "✅ Setup complete"
fi

# Source environment variables
set -a
source .env
set +a

# Start components function
start_components() {
    local components=("$@")
    [ ${#components[@]} -eq 0 ] && echo "▶️  Starting all..." || echo "▶️  Starting: ${components[*]}"
    HOST_IP=${HOST_IP:-"127.0.0.1"} docker compose up --build "${components[@]}"
}

echo "🌐 Access URLs:
Backend:     http://${HOST_IP}:8000
Frontend PC: http://${HOST_IP}:3000
Frontend VR: http://${HOST_IP}:3001"

start_components "$@"