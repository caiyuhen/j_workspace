<<<<<<< HEAD
@echo off
chcp 65001 >nul 2>&1
setlocal
title CTMS Pro - 停止系统

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║      CTMS Pro - 停止所有服务                 ║
echo  ╚══════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo  正在停止 CTMS Pro 所有服务...
docker compose down

if %errorlevel% equ 0 (
    echo.
    echo  [✓] 所有服务已停止。数据已保留在 Docker 数据卷中。
) else (
    echo  [警告] 停止服务时遇到问题
)

echo.
pause
endlocal
=======
@echo off
chcp 65001 >nul 2>&1
setlocal
title CTMS Pro - 停止系统

echo.
echo  ╔══════════════════════════════════════════════╗
echo  ║      CTMS Pro - 停止所有服务                 ║
echo  ╚══════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo  正在停止 CTMS Pro 所有服务...
docker compose down

if %errorlevel% equ 0 (
    echo.
    echo  [✓] 所有服务已停止。数据已保留在 Docker 数据卷中。
) else (
    echo  [警告] 停止服务时遇到问题
)

echo.
pause
endlocal
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
