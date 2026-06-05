#!/bin/bash
# OCR Microservice Deployment Script for Linux

# Ensure output directory exists
mkdir -p output

# Function to try deploying with Docker Compose (v2 plugin)
deploy_with_compose_v2() {
    if docker compose version &> /dev/null; then
        echo "Using 'docker compose' (v2 plugin)..."
        docker compose down
        if docker compose up -d --build; then
            echo "Service deployed successfully via 'docker compose'!"
            echo "Check logs with: docker compose logs -f"
            return 0
        else
            echo "'docker compose' failed."
            return 1
        fi
    else
        return 1
    fi
}

# Function to try deploying with docker-compose (v1/standalone)
deploy_with_compose_v1() {
    if command -v docker-compose &> /dev/null; then
        echo "Using 'docker-compose' (standalone)..."
        # Check if it actually works (handles Python env issues)
        if ! docker-compose version &> /dev/null; then
            echo "'docker-compose' command exists but is broken (likely Python env issue). Skipping..."
            return 1
        fi
        
        docker-compose down
        if docker-compose up -d --build; then
            echo "Service deployed successfully via 'docker-compose'!"
            echo "Check logs with: docker-compose logs -f"
            return 0
        else
            echo "'docker-compose' failed."
            return 1
        fi
    else
        return 1
    fi
}

# Function to deploy with raw docker commands
deploy_with_raw_docker() {
    echo "Falling back to raw 'docker' commands..."
    
    # Build image
    echo "Building image..."
    if ! docker build -t ocr-microservice:latest .; then
        echo "Docker build failed!"
        exit 1
    fi
    
    # Stop and remove existing container
    if [ "$(docker ps -aq -f name=ocr-service)" ]; then
        echo "Stopping existing container..."
        docker stop ocr-service
        docker rm ocr-service
    fi
    
    # Run container
    echo "Starting container..."
    if docker run -d \
        -p 9080:9080 \
        --name ocr-service \
        --restart always \
        -v "$(pwd)/output:/app/output" \
        ocr-microservice:latest; then
            
        echo "Service deployed successfully via 'docker run'!"
        echo "Check logs with: docker logs -f ocr-service"
        return 0
    else
        echo "Docker run failed!"
        return 1
    fi
}

# Main execution logic
# Try v2 first (modern standard)
if deploy_with_compose_v2; then
    exit 0
fi

# Try v1 next (legacy)
if deploy_with_compose_v1; then
    exit 0
fi

# Fallback to raw docker
deploy_with_raw_docker
