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
    echo "  $0 backend          # Stop only the backend"
    echo "  $0 frontend-pc      # Stop only the PC frontend"
    echo "  $0 backend frontend-pc  # Stop backend and PC frontend"
    exit 0
fi

# Stop specified components or all if none specified
if [ $# -eq 0 ]; then
    echo "Stopping all components..."
    docker compose down
else
    echo "Stopping components: $@"
    docker compose stop "$@"
fi