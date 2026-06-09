<<<<<<< HEAD
@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title CTMS Pro - 启动系统

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║      CTMS Pro - 启动所有服务                 ║
echo  ╚══════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: 检查 Docker 是否运行
echo  检查 Docker 状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo  [错误] Docker 未运行，请先启动 Docker Desktop
    echo.
    echo  正在尝试启动 Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    echo  请等待 Docker 启动后再次运行此脚本（约 30-60 秒）
    pause
    exit /b 1
)

echo  [✓] Docker 运行正常
echo.
echo  正在启动 CTMS Pro 服务...
docker compose up -d

if %errorlevel% equ 0 (
    echo.
    echo  [✓] 所有服务已启动！
    echo.
    echo  ─────────────────────────────────────────
    echo    系统入口:    http://localhost
    echo    API 文档:    http://localhost/api/v1/docs
    echo    MinIO 控制台: http://localhost:9001
    echo  ─────────────────────────────────────────
    echo.

    :: 等待 3 秒后打开浏览器
    timeout /t 3 /nobreak >nul
    start "" "http://localhost"
) else (
    echo.
    echo  [错误] 服务启动失败，请查看日志：
    echo    docker compose logs
    echo.
)

pause
endlocal
=======
@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title CTMS Pro - 启动系统

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║      CTMS Pro - 启动所有服务                 ║
echo  ╚══════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

:: 检查 Docker 是否运行
echo  检查 Docker 状态...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo  [错误] Docker 未运行，请先启动 Docker Desktop
    echo.
    echo  正在尝试启动 Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    echo  请等待 Docker 启动后再次运行此脚本（约 30-60 秒）
    pause
    exit /b 1
)

echo  [✓] Docker 运行正常
echo.
echo  正在启动 CTMS Pro 服务...
docker compose up -d

if %errorlevel% equ 0 (
    echo.
    echo  [✓] 所有服务已启动！
    echo.
    echo  ─────────────────────────────────────────
    echo    系统入口:    http://localhost
    echo    API 文档:    http://localhost/api/v1/docs
    echo    MinIO 控制台: http://localhost:9001
    echo  ─────────────────────────────────────────
    echo.

    :: 等待 3 秒后打开浏览器
    timeout /t 3 /nobreak >nul
    start "" "http://localhost"
) else (
    echo.
    echo  [错误] 服务启动失败，请查看日志：
    echo    docker compose logs
    echo.
)

pause
endlocal
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
