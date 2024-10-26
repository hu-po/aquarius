#!/bin/bash
YELLOW='\033[1;33m'
NC='\033[0m'
echo -e "${YELLOW}🧹 cleaning aquarius ...${NC}"
docker compose down
git pull
rm -f .env
rm -rf data
docker images | grep 'aquarius-backend\|aquarius-frontend-pc\|aquarius-frontend-vr' | awk '{print $3}' | xargs -r docker rmi -f
docker image prune -f
docker volume prune -f
docker network prune -f