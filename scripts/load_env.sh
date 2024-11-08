#!/bin/bash
# Create .env from example if it doesn't exist
if [ ! -f .env ]; then
    if [ ! -f .env.example ]; then
        echo "❌ .env.example not found"
        exit 1
    fi
    cp .env.example .env
    echo "✅ Created .env from example"
    
    # replace foo variables in .env.example with values from environment
    required_vars=("ANTHROPIC_API_KEY" "OPENAI_API_KEY" "GOOGLE_API_KEY")

    # Check for required API keys
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            echo "⚠️  $var not set"
        else
            echo "✅ Found $var"
            # Escape special characters in the value
            val=$(printf '%s\n' "${!var}" | sed -e 's/[\/&]/\\&/g')
            # Use @ as delimiter since it's unlikely to appear in API keys
            sed -i "s@${var}=.*@${var}=${val}@" .env
        fi
    done

    # Set HOST_IP, USER_ID, GROUP_ID
    HOST_IP=$(hostname -I | awk '{print $1}')
    sed -i "s@HOST_IP=.*@HOST_IP=${HOST_IP}@" .env
    USER_ID=${USER_ID:-$(id -u)}
    sed -i "s@USER_ID=.*@USER_ID=${USER_ID}@" .env
    GROUP_ID=${GROUP_ID:-$(id -g)}
    sed -i "s@GROUP_ID=.*@GROUP_ID=${GROUP_ID}@" .env

    # Copy .env to backend, frontends
    cp .env backend/.env
    cp .env frontend-pc/.env
    cp .env frontend-vr/.env
fi

# Source the .env file
set -a
source .env
set +a

# Create directories
echo "📁 Creating data directories..."
mkdir -p data/images data/db
chmod -R 777 data

echo "✅ Setup complete"
