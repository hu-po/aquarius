#!/bin/bash
check_and_set_vars() {
    local required_vars=("ANTHROPIC_API_KEY" "OPENAI_API_KEY" "GOOGLE_API_KEY")
    local missing_vars=0

    # Check for required API keys
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "⚠️  $var not set"
            missing_vars=$((missing_vars + 1))
        else
            echo "✅ Found $var"
            # Use double quotes to ensure proper variable expansion
            # Use different delimiter (|) to avoid conflicts with potential / in API keys
            val="${!var}"
            sed -i "s|^${var}=.*|${var}=${val}|" .env
        fi
    done

    # Set HOST_IP if not already set
    HOST_IP=$(hostname -I | awk '{print $1}')
    sed -i "s|^HOST_IP=.*|HOST_IP=${HOST_IP}|" .env

    # Set USER_ID/GROUP_ID if not already set
    USER_ID=${USER_ID:-$(id -u)}
    GROUP_ID=${GROUP_ID:-$(id -g)}
    sed -i "s|^USER_ID=.*|USER_ID=${USER_ID}|" .env
    sed -i "s|^GROUP_ID=.*|GROUP_ID=${GROUP_ID}|" .env

    return $missing_vars
}

# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    if [ ! -f .env.example ]; then
        echo "❌ .env.example not found"
        exit 1
    fi
    cp .env.example .env
    echo "✅ Created .env from example"
fi

# Always source the .env file
set -a
source .env
set +a

# Check and set variables, create directories
check_and_set_vars
echo "📁 Creating data directories..."
mkdir -p data/images data/db
chmod -R 777 data
echo "✅ Setup complete"
