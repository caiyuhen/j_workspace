@echo off
echo Running Docker container...
docker run -d -p 9080:9080 --name ocr-service -v %cd%/output:/app/output ocr-microservice:latest
echo Container started on http://localhost:9080
pause
