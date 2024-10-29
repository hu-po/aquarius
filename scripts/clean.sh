#!/bin/bash
echo "🧹 cleaning aquarius ..."
"$(dirname "$0")/stop.sh"
rm -f .env
rm -rf data
git pull
docker rmi aquarius-frontend-pc aquarius-backend aquarius-frontend-vr
docker image prune -f
docker volume prune -f
docker network prune -f
