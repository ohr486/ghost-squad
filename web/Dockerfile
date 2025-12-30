# Ghost Squad Web - Dockerfile
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Install dependencies for testing
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

# Copy package files first for better caching
COPY package*.json ./

# Install dependencies
# Use npm install if package-lock.json doesn't exist, otherwise use npm ci
RUN if [ -f package-lock.json ]; then npm ci --silent --legacy-peer-deps; else npm install --silent --legacy-peer-deps; fi

# Copy application code
COPY . .

# Expose port
EXPOSE 3000

# Default command (can be overridden)
CMD ["npm", "start"]
