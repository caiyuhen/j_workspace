@echo off
chcp 65001 >nul
echo ============================================================
echo 🏥 MedAIagents - 医学 AI 助手 桌面版
echo ============================================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未检测到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 切换到脚本所在目录
cd /d "%~dp0"

REM 检查是否已安装依赖
echo 🔍 检查依赖...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 正在安装依赖...
    pip install -r requirements.txt
)

echo.
echo 🚀 启动桌面应用...
echo.

REM 启动桌面应用
python -m medai.desktop.app

echo.
echo 👋 感谢使用 MedAIagents
pause
