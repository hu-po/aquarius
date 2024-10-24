#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Function to check if a variable is set
check_variable() {
    local var_name=$1
    local var_value=${!var_name}
    if [ -z "$var_value" ]; then
        echo -e "${RED}Warning: $var_name is not set in your shell environment${NC}"
        return 1
    else
        echo -e "${GREEN}Found $var_name${NC}"
        return 0
    fi
}

# Function to create backup of existing .env
backup_env() {
    if [ -f .env ]; then
        backup_file=".env.backup.$(date +%Y%m%d_%H%M%S)"
        echo -e "${YELLOW}Creating backup of existing .env as $backup_file${NC}"
        cp .env "$backup_file"
    fi
}

# Main script
echo "Setting up environment variables..."

# Check if .env.example exists
if [ ! -f .env.example ]; then
    echo -e "${RED}Error: .env.example not found${NC}"
    exit 1
fi

# Required API keys
required_vars=(
    "ANTHROPIC_API_KEY"
    "OPENAI_API_KEY"
    "GOOGLE_API_KEY"
)

# Check all required variables
missing_vars=0
for var in "${required_vars[@]}"; do
    if ! check_variable "$var"; then
        missing_vars=$((missing_vars + 1))
    fi
done

if [ $missing_vars -gt 0 ]; then
    echo -e "\n${RED}Error: Some required environment variables are missing${NC}"
    echo "Please ensure these variables are set in your shell environment (e.g., .bashrc or .zshrc):"
    for var in "${required_vars[@]}"; do
        echo "  export $var=your_${var,,}_here"
    done
    exit 1
fi

# Create backup of existing .env
backup_env

# Create new .env from template and replace variables
echo -e "${GREEN}Creating new .env file...${NC}"
cp .env.example .env

# Replace each variable in .env
for var in "${required_vars[@]}"; do
    value=${!var}
    # Use different delimiters for sed since API keys might contain special characters
    sed -i "s|${var}=.*|${var}=${value}|" .env
done

# Set additional environment variables
# Get host IP
HOST_IP=$(hostname -I | awk '{print $1}')
sed -i "s|HOST_IP=.*|HOST_IP=${HOST_IP}|" .env

# Set current user's UID/GID for Docker
sed -i "s|UID=.*|UID=$(id -u)|" .env
sed -i "s|GID=.*|GID=$(id -g)|" .env

echo -e "${GREEN}Environment setup complete!${NC}"
echo -e "Created .env file with the following API keys:"
for var in "${required_vars[@]}"; do
    echo -e "${YELLOW}$var${NC} is set"
done
echo -e "${YELLOW}HOST_IP${NC} set to: $HOST_IP"
echo -e "${YELLOW}UID/GID${NC} set to: $(id -u)/$(id -g)"