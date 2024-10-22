#!/bin/bash

# Show usage if --help flag is used
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [component...]"
    echo ""
    echo "Components:"
    echo "  backend      - Start the Python FastAPI backend"
    echo "  frontend-pc  - Start the React dashboard"
    echo "  frontend-vr  - Start the VR interface"
    echo ""
    echo "If no component is specified, all components will be started."
    echo "Multiple components can be specified, separated by spaces."
    echo ""
    echo "Examples:"
    echo "  $0                   # Start all components with logs"
    echo "  $0 backend          # Start only the backend"
    echo "  $0 frontend-pc      # Start only the PC frontend"
    echo "  $0 backend frontend-pc  # Start backend and PC frontend"
    exit 0
fi

# Check/create .env file
if [ ! -f .env ]; then
    echo "No .env file found. Creating from .env.example..."
    cp .env.example .env
fi

# Create data directories
mkdir -p data/images data/db

# Function to start components and show logs
start_components() {
    local components=("$@")
    
    # If no specific components, start all
    if [ ${#components[@]} -eq 0 ]; then
        echo "Starting all components..."
        docker compose up --build
    else
        echo "Starting components: ${components[*]}"
        docker compose up --build "${components[@]}"
    fi
}

# Start components and show logs
start_components "$@"