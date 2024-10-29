#!/bin/bash
echo "🧹 cleaning aquarius ..."
rm -f .env
"$(dirname "$0")/stop.sh"
git pull
docker rmi aquarius-frontend-pc aquarius-backend aquarius-frontend-vr
docker image prune -f
docker volume prune -f
docker network prune -f
