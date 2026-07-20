<<<<<<< HEAD
@echo off
chcp 65001 >nul 2>&1
setlocal
title CTMS Pro - 系统维护工具
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -NoLogo -File "%~dp0maintenance.ps1"
endlocal
=======
@echo off
chcp 65001 >nul 2>&1
setlocal
title CTMS Pro - 系统维护工具
cd /d "%~dp0"
powershell -ExecutionPolicy Bypass -NoLogo -File "%~dp0maintenance.ps1"
endlocal
>>>>>>> origin/main
