FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm cache clean --force && \
    npm install && \
    npm cache clean --force
COPY . .
EXPOSE 3001
CMD ["npm", "start"]