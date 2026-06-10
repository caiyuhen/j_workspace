function Start-ServiceWindow {
    param(
        [string]$WorkingDir,
        [string]$Command,
        [string]$WindowStyle = "Minimized"
    )

    Start-Process -FilePath "powershell" -WindowStyle $WindowStyle -ArgumentList @(
        "-NoProfile",
        "-Command",
        "Set-Location '$WorkingDir'; $Command"
    )
}

Start-ServiceWindow -WorkingDir "D:\workspace\Digital_Twin_Project\services\patient-service\src" -Command "python -m uvicorn main:app --host 127.0.0.1 --port 9003 --reload"
Start-ServiceWindow -WorkingDir "D:\workspace\Digital_Twin_Project\services\simulation-service\src" -Command "python -m uvicorn main:app --host 127.0.0.1 --port 9001 --reload"
Start-ServiceWindow -WorkingDir "D:\workspace\Digital_Twin_Project\services\visualization-service\src" -Command "python -m uvicorn main:app --host 127.0.0.1 --port 9002 --reload"
Start-ServiceWindow -WorkingDir "D:\workspace\Digital_Twin_Project\services\ocr-service\src" -Command "python -m uvicorn main:app --host 127.0.0.1 --port 9004 --reload"
Start-ServiceWindow -WorkingDir "D:\workspace\Digital_Twin_Project\services\xray-analysis-service\src" -Command "python -m uvicorn main:app --host 127.0.0.1 --port 9005 --reload"
Start-ServiceWindow -WorkingDir "D:\workspace\Digital_Twin_Project\services\report-gateway\src" -WindowStyle "Normal" -Command '$env:PATIENT_SERVICE_URL=''http://127.0.0.1:9003''; $env:SIMULATION_SERVICE_URL=''http://127.0.0.1:9001''; $env:VISUALIZATION_SERVICE_URL=''http://127.0.0.1:9002''; $env:OCR_SERVICE_URL=''http://127.0.0.1:9004''; $env:XRAY_SERVICE_URL=''http://127.0.0.1:9005''; python -m uvicorn main:app --host 127.0.0.1 --port 9000 --reload'

Write-Host "Alt-port services started."
Write-Host "Frontend URL: http://127.0.0.1:9000/"
Write-Host "Gateway health: http://127.0.0.1:9000/health"
Write-Host "Smoke test: python .\run_multimodal_smoke_checks.py"
