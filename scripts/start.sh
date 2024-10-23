#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

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
    echo -e "${YELLOW}No .env file found. Running environment setup...${NC}"
    if ! "$(dirname "$0")/setup-env.sh"; then
        echo -e "${RED}Environment setup failed. Please check the error messages above.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Environment setup completed successfully.${NC}"
fi

# Create data directories
echo -e "${YELLOW}Setting up data directories...${NC}"
mkdir -p data/images data/db

# Allow read/write for all users
chmod -R 777 data

# Function to start components and show logs
start_components() {
    local components=("$@")
    
    # If no specific components, start all
    if [ ${#components[@]} -eq 0 ]; then
        echo -e "${GREEN}Starting all components...${NC}"
        docker compose up --build
    else
        echo -e "${GREEN}Starting components: ${components[*]}${NC}"
        docker compose up --build "${components[@]}"
    fi
}

# Export host IP for use in containers (this will be a fallback if not set in .env)
export HOST_IP=$(hostname -I | awk '{print $1}')

# Print access URLs
print_access_urls() {
    echo -e "\n${GREEN}Access URLs:${NC}"
    echo -e "Backend:     ${YELLOW}http://${HOST_IP}:8000${NC}"
    echo -e "Frontend PC: ${YELLOW}http://${HOST_IP}:3000${NC}"
    echo -e "Frontend VR: ${YELLOW}http://${HOST_IP}:3001${NC}"
    echo ""
}
print_access_urls

# Start components and show logs
start_components "$@"