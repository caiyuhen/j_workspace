@echo off
cd /d "%~dp0"
start "project-config-8001" cmd /k ".venv\Scripts\python.exe -m uvicorn project_config_service.app:app --host 0.0.0.0 --port 8001"
start "randomization-8002" cmd /k ".venv\Scripts\python.exe -m uvicorn randomization_service.app:app --host 0.0.0.0 --port 8002"
start "audit-8003" cmd /k ".venv\Scripts\python.exe -m uvicorn audit_logging_service.app:app --host 0.0.0.0 --port 8003"
start "patient-8004" cmd /k ".venv\Scripts\python.exe -m uvicorn patient_mgmt_service.app:app --host 0.0.0.0 --port 8004"
start "validation-8005" cmd /k ".venv\Scripts\python.exe -m uvicorn data_validation_service.app:app --host 0.0.0.0 --port 8005"
start "monitoring-8006" cmd /k ".venv\Scripts\python.exe -m uvicorn monitoring_service.app:app --host 0.0.0.0 --port 8006"
start "security-8007" cmd /k ".venv\Scripts\python.exe -m uvicorn security_service.app:app --host 0.0.0.0 --port 8007"
start "frontend-8080" cmd /k ".venv\Scripts\python.exe -m uvicorn frontend_service.app:app --host 0.0.0.0 --port 8080"
echo Frontend: http://127.0.0.1:8080
