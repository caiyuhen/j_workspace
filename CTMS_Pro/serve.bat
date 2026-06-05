@echo off
chcp 65001 >nul 2>&1
title CTMS Pro 前端服务器

echo.
echo  启动 CTMS Pro 前端服务器...
echo  访问地址: http://127.0.0.1:8899
echo  按 Ctrl+C 停止服务器
echo.

cd /d "%~dp0"
python -m http.server 8899
