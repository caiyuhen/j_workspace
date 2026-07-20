<<<<<<< HEAD
@echo off
chcp 65001 >nul 2>&1
title CTMS Pro 本地启动脚本

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║           CTMS Pro 本地快速启动                          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

::: 检查 .env.local 是否存在
if not exist "%~dp0backend\.env.local" (
    echo  [错误] 配置文件不存在，请先运行 install-local.bat
    echo.
    pause
    exit /b 1
)

::: 读取配置端口
for /f "tokens=1,* delims==" %%a in ('findstr /i "SERVER_PORT POSTGRES_PORT" "%~dp0backend\.env.local" 2^>nul') do (
    if "%%a"=="SERVER_PORT" set API_PORT=%%b
    if "%%a"=="POSTGRES_PORT" set PG_PORT=%%b
)

if not defined API_PORT set API_PORT=8898
if not defined PG_PORT set PG_PORT=5433

echo  [1/3] 启动 PostgreSQL 服务...
net start postgresql* >nul 2>&1
echo  PostgreSQL 已启动

echo.
echo  [2/3] 启动 Redis 服务...
start /b redis-server --port 6380 >nul 2>&1
echo  Redis 已启动

echo.
echo  [3/3] 启动后端 API 服务...
start "CTMS Pro Backend" cmd /k "cd /d "%~dp0backend" && uvicorn app.main:app --host 127.0.0.1 --port %API_PORT% --reload"

echo.
echo  等待服务启动...
timeout /t 5 /nobreak >nul

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  ✓ CTMS Pro 已启动！                                   ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  · 后端 API:   http://127.0.0.1:%API_PORT%             ║
echo  ║  · API 文档:   http://127.0.0.1:%API_PORT%/api/v1/docs ║
echo  ║  · 前端预览:   http://127.0.0.1:8899                   ║
echo  ║                                                          ║
echo  ║  账号: admin@ctms-pro.com / Admin@CTMS2026!             ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

::: 启动前端预览
start http://127.0.0.1:8899

echo  启动完成！按任意键退出...
pause >nul
=======
@echo off
chcp 65001 >nul 2>&1
title CTMS Pro 本地启动脚本

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║           CTMS Pro 本地快速启动                          ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

::: 检查 .env.local 是否存在
if not exist "%~dp0backend\.env.local" (
    echo  [错误] 配置文件不存在，请先运行 install-local.bat
    echo.
    pause
    exit /b 1
)

::: 读取配置端口
for /f "tokens=1,* delims==" %%a in ('findstr /i "SERVER_PORT POSTGRES_PORT" "%~dp0backend\.env.local" 2^>nul') do (
    if "%%a"=="SERVER_PORT" set API_PORT=%%b
    if "%%a"=="POSTGRES_PORT" set PG_PORT=%%b
)

if not defined API_PORT set API_PORT=8898
if not defined PG_PORT set PG_PORT=5433

echo  [1/3] 启动 PostgreSQL 服务...
net start postgresql* >nul 2>&1
echo  PostgreSQL 已启动

echo.
echo  [2/3] 启动 Redis 服务...
start /b redis-server --port 6380 >nul 2>&1
echo  Redis 已启动

echo.
echo  [3/3] 启动后端 API 服务...
start "CTMS Pro Backend" cmd /k "cd /d "%~dp0backend" && uvicorn app.main:app --host 127.0.0.1 --port %API_PORT% --reload"

echo.
echo  等待服务启动...
timeout /t 5 /nobreak >nul

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║  ✓ CTMS Pro 已启动！                                   ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  · 后端 API:   http://127.0.0.1:%API_PORT%             ║
echo  ║  · API 文档:   http://127.0.0.1:%API_PORT%/api/v1/docs ║
echo  ║  · 前端预览:   http://127.0.0.1:8899                   ║
echo  ║                                                          ║
echo  ║  账号: admin@ctms-pro.com / Admin@CTMS2026!             ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

::: 启动前端预览
start http://127.0.0.1:8899

echo  启动完成！按任意键退出...
pause >nul
>>>>>>> origin/main
