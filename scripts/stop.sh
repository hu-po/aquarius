#!/bin/bash
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [component...]

Components:
  backend      - Stop the Python FastAPI backend
  frontend-pc  - Stop the React dashboard
  frontend-vr  - Stop the VR interface

If no component is specified, all components will be stopped.
Multiple components can be specified, separated by spaces.

Examples:
  $0                   # Stop all components
  $0 backend          # Stop only the backend
  $0 frontend-pc      # Stop only the PC frontend
  $0 backend frontend-pc  # Stop backend and PC frontend"
    exit 0
fi

source "$(dirname "$0")/load_env.sh"

stop_components() {
    local components=("$@")
    [ ${#components[@]} -eq 0 ] && echo "⏹️  Stopping all..." || echo "⏹️  Stopping: ${components[*]}"
    [ ${#components[@]} -eq 0 ] && docker compose down || docker compose stop "${components[@]}"
}

stop_components "$@"