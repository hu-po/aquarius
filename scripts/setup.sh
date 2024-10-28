#!/bin/bash
check_variable() {
    local var_name=$1
    local var_value=${!var_name}
    [ -z "$var_value" ] && echo "⚠️  $var_name not set" && return 1
    echo "✅ Found $var_name"
    return 0
}

[ -f .env ] && cp .env ".env.backup.$(date +%Y%m%d_%H%M%S)"
[ ! -f .env.example ] && echo "❌ .env.example not found" && exit 1

required_vars=("ANTHROPIC_API_KEY" "OPENAI_API_KEY" "GOOGLE_API_KEY")
missing_vars=0

for var in "${required_vars[@]}"; do
    check_variable "$var" || missing_vars=$((missing_vars + 1))
done

if [ $missing_vars -gt 0 ]; then
    echo "❌ Missing environment variables. Add to .bashrc or .zshrc:"
    for var in "${required_vars[@]}"; do
        echo "export $var=your_${var,,}_here"
    done
    exit 1
fi

cp .env.example .env

for var in "${required_vars[@]}"; do
    value=${!var}
    sed -i "s|${var}=.*|${var}=${value}|" .env
done

HOST_IP=$(hostname -I | awk '{print $1}')
sed -i "s|HOST_IP=.*|HOST_IP=${HOST_IP}|" .env
sed -i "s|UID=.*|UID=$(id -u)|" .env
sed -i "s|GID=.*|GID=$(id -g)|" .env

echo "🎉 Setup complete with API keys:"
for var in "${required_vars[@]}"; do
    echo "🔑 $var is set"
done
echo "🌐 HOST_IP: $HOST_IP"
echo "👤 UID/GID: $(id -u)/$(id -g)"