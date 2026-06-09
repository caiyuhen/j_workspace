@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title CTMS Pro 临床试验管理系统 - 安装程序

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║         CTMS Pro 临床试验管理系统 安装程序               ║
echo  ║              版本 1.0.0                                  ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

:: 检查 PowerShell 是否可用
where powershell >nul 2>&1
if %errorlevel% neq 0 (
    echo  [错误] 未找到 PowerShell，请先安装 Windows Management Framework 5.1
    echo  下载地址: https://www.microsoft.com/en-us/download/details.aspx?id=54616
    pause
    exit /b 1
)

:: 检查是否需要管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo  [提示] 建议以管理员身份运行以获得完整安装权限
    echo  正在尝试提升权限...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b 0
)

echo  正在启动安装程序...
echo.

:: 设置执行策略并运行 PowerShell 安装脚本
powershell -ExecutionPolicy Bypass -NoLogo -File "%~dp0install.ps1" %*

if %errorlevel% equ 0 (
    echo.
    echo  安装成功完成！
) else (
    echo.
    echo  安装过程中遇到问题，请查看日志文件了解详情。
)

echo.
pause
endlocal
