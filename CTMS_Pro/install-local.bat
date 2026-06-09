@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title CTMS Pro 本地安装程序

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║       CTMS Pro 临床试验管理系统 - 本地安装               ║
echo  ║              版本 2.0.0（无需 Docker）                  ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

::: 检查 PowerShell
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo  [错误] 未找到 PowerShell
    pause
    exit /b 1
)

::: 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [提示] 建议以管理员身份运行
    echo  正在尝试提升权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b 0
)

echo  正在启动本地安装程序...
echo.
echo  此版本特点：
echo   · 无需 Docker Desktop
echo   · 自动检测并解决端口冲突
echo   · 自动安装 Python + PostgreSQL + Redis
echo.

powershell -ExecutionPolicy Bypass -NoLogo -File "%~dp0install-local.ps1" %*

echo.
pause
endlocal
