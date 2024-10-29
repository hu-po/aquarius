#!/bin/bash
echo "🧹 cleaning aquarius ..."
docker stop aquarius-frontend-pc aquarius-backend aquarius-frontend-vr
docker rmi aquarius-frontend-pc aquarius-backend aquarius-frontend-vr
docker image prune -f
docker volume prune -f
docker network prune -f
rm -f .env
rm -rf data
git pull
