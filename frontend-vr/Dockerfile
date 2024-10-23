FROM node:20-slim
WORKDIR /app
COPY package*.json ./
RUN npm cache clean --force && \
    npm install && \
    npm cache clean --force
COPY . .
EXPOSE 3001
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3001/ || exit 1
CMD ["npm", "start"]