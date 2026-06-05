@echo off
echo Building Docker image...
docker build -t ocr-microservice:latest .
echo Build complete.
pause
