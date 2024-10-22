FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
# Only copy necessary files, ignoring those in `.dockerignore`
COPY . .
CMD ["npm", "start"]