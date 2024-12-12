#!/bin/sh

# Make sure the environment file is set
if [ ! -f ".env" ]; then 
    echo "Error: .env file not found." 
    exit 1 
fi

# Set working directory to /app (current folder)
WORKDIR=/app

# Container name
CONTAINER_NAME=nate-container

# Build Docker image
docker build -t nate .

# Stop and remove existing container if it exists
docker rm -f $CONTAINER_NAME >/dev/null 2>&1 || true

# Run new container with auto-remove and pass through all arguments
docker run --name $CONTAINER_NAME --rm nate "$@"
