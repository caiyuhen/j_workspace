@echo off
chcp 936 >nul
echo ============================================================
echo MedAIagents - Medical AI Agent Desktop
echo ============================================================
echo.

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.9+
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check dependencies
echo [INFO] Checking dependencies...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
)

echo.
echo [INFO] Starting desktop application...
echo.

REM Set PYTHONPATH and start
set PYTHONPATH=%~dp0src
python -m medai.desktop.app --port 8229

echo.
echo [INFO] MedAIagents stopped.
pause
