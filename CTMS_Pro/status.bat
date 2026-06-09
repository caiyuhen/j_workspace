<<<<<<< HEAD
@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title CTMS Pro - 系统状态

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║      CTMS Pro - 系统状态监控                             ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo  ─── Docker 容器状态 ──────────────────────────────────────
docker compose ps
echo.

echo  ─── 资源使用情况 ────────────────────────────────────────
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo.

echo  ─── 服务访问地址 ────────────────────────────────────────
echo    系统入口:      http://localhost
echo    API 文档:      http://localhost/api/v1/docs
echo    MinIO 控制台:  http://localhost:9001
echo.

echo  ─── 快捷命令 ────────────────────────────────────────────
echo    查看日志:  docker compose logs -f [服务名]
echo    重启服务:  docker compose restart [服务名]
echo    进入容器:  docker exec -it ctms_backend bash
echo.

pause
endlocal
=======
@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion
title CTMS Pro - 系统状态

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║      CTMS Pro - 系统状态监控                             ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

cd /d "%~dp0"

echo  ─── Docker 容器状态 ──────────────────────────────────────
docker compose ps
echo.

echo  ─── 资源使用情况 ────────────────────────────────────────
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
echo.

echo  ─── 服务访问地址 ────────────────────────────────────────
echo    系统入口:      http://localhost
echo    API 文档:      http://localhost/api/v1/docs
echo    MinIO 控制台:  http://localhost:9001
echo.

echo  ─── 快捷命令 ────────────────────────────────────────────
echo    查看日志:  docker compose logs -f [服务名]
echo    重启服务:  docker compose restart [服务名]
echo    进入容器:  docker exec -it ctms_backend bash
echo.

pause
endlocal
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
