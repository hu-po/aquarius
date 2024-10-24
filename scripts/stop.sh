#!/bin/bash

# Show usage if --help flag is used
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [component...]"
    echo ""
    echo "Components:"
    echo "  backend      - Stop the Python FastAPI backend"
    echo "  frontend-pc  - Stop the React dashboard"
    echo "  frontend-vr  - Stop the VR interface"
    echo ""
    echo "If no component is specified, all components will be stopped."
    echo "Multiple components can be specified, separated by spaces."
    echo ""
    echo "Examples:"
    echo "  $0                   # Stop all components"
    echo "  $0 backend           # Stop only the backend"
    echo "  $0 frontend-pc       # Stop only the PC frontend"
    echo "  $0 backend frontend-pc  # Stop backend and PC frontend"
    exit 0
fi

# Set the HOST_IP environment variable
HOST_IP=$(hostname -I | awk '{print $1}')
export HOST_IP

# Function to stop components
stop_components() {
    local components=("$@")

    if [ ${#components[@]} -eq 0 ]; then
        echo "⏹️  Stopping all components..."
        docker compose down
    else
        echo "⏹️  Stopping components: ${components[*]}"
        docker compose stop "${components[@]}"
    fi
}

# Stop the specified components
stop_components "$@"
