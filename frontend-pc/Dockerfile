FROM node:16-alpine
WORKDIR /app
ARG BACKEND_URL
ENV VITE_BACKEND_URL=${BACKEND_URL}
COPY package*.json ./
RUN npm install
COPY . .
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1
CMD ["npm", "start"]