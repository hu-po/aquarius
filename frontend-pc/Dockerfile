FROM node:16-alpine
WORKDIR /app

# Add build arguments for environment variables
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}

COPY package*.json ./
RUN npm install
COPY . .
CMD ["npm", "start"]