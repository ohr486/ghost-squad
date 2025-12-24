# Frontend Dockerfile for development
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies for better caching
COPY package*.json ./
RUN npm install

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Default command for development
CMD ["npm", "start"]