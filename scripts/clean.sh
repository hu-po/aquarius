#!/bin/bash
echo "🧹 cleaning aquarius ..."

if [ "$(docker ps -a -q)" ]; then
  docker stop $(docker ps -a -q)
else
  echo "No running containers to stop."
fi

docker rmi -f aquarius-frontend-pc aquarius-backend aquarius-frontend-vr
docker image prune -f
docker volume prune -f
docker network prune -f
# docker system prune -f

rm -f .env
rm -rf data

git pull
