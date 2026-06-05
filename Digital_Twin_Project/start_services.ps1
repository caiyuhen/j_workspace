# Start all microservices in separate background processes

Write-Host "Starting Patient Service on port 8003..."
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--port", "8003", "--reload" -WorkingDirectory "services/patient-service/src" -WindowStyle Minimized

Write-Host "Starting Simulation Service on port 8001..."
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--port", "8001", "--reload" -WorkingDirectory "services/simulation-service/src" -WindowStyle Minimized

Write-Host "Starting Visualization Service on port 8002..."
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--port", "8002", "--reload" -WorkingDirectory "services/visualization-service/src" -WindowStyle Minimized

Write-Host "Starting OCR Service on port 8004..."
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--port", "8004", "--reload" -WorkingDirectory "services/ocr-service/src" -WindowStyle Minimized

Write-Host "Starting Report Gateway on port 8000..."
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--port", "8000", "--reload" -WorkingDirectory "services/report-gateway/src" -WindowStyle Normal

Write-Host "All services started!"
Write-Host "Gateway URL: http://localhost:8000/docs"
Write-Host "Frontend URL: http://localhost:8000/"
