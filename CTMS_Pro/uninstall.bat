<<<<<<< HEAD
@echo off
chcp 65001 >nul 2>&1
setlocal
title CTMS Pro - 卸载程序

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║      CTMS Pro - 卸载程序                                 ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  警告: 此操作将删除所有容器和服务                        ║
echo  ║  数据库数据请提前备份！                                   ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set /p CONFIRM=确认卸载 CTMS Pro? 请输入 YES 继续: 
if /i not "%CONFIRM%"=="YES" (
    echo 已取消卸载。
    pause
    exit /b 0
)

cd /d "%~dp0"

echo.
echo  [1/3] 停止并删除所有容器...
docker compose down --remove-orphans

set /p DEL_DATA=是否同时删除数据库数据（不可恢复）? [Y/N]:
if /i "%DEL_DATA%"=="Y" (
    echo  [2/3] 删除数据卷...
    docker compose down -v
    echo  [✓] 数据卷已删除
) else (
    echo  [2/3] 保留数据卷（数据未删除）
)

echo  [3/3] 删除 Docker 镜像...
docker rmi ctms_pro_backend 2>nul
docker rmi ctms_pro_celery_worker 2>nul

echo.
echo  [✓] CTMS Pro 已卸载完成
echo.
pause
endlocal
=======
@echo off
chcp 65001 >nul 2>&1
setlocal
title CTMS Pro - 卸载程序

echo.
echo  ╔══════════════════════════════════════════════════════════╗
echo  ║      CTMS Pro - 卸载程序                                 ║
echo  ╠══════════════════════════════════════════════════════════╣
echo  ║  警告: 此操作将删除所有容器和服务                        ║
echo  ║  数据库数据请提前备份！                                   ║
echo  ╚══════════════════════════════════════════════════════════╝
echo.

set /p CONFIRM=确认卸载 CTMS Pro? 请输入 YES 继续: 
if /i not "%CONFIRM%"=="YES" (
    echo 已取消卸载。
    pause
    exit /b 0
)

cd /d "%~dp0"

echo.
echo  [1/3] 停止并删除所有容器...
docker compose down --remove-orphans

set /p DEL_DATA=是否同时删除数据库数据（不可恢复）? [Y/N]:
if /i "%DEL_DATA%"=="Y" (
    echo  [2/3] 删除数据卷...
    docker compose down -v
    echo  [✓] 数据卷已删除
) else (
    echo  [2/3] 保留数据卷（数据未删除）
)

echo  [3/3] 删除 Docker 镜像...
docker rmi ctms_pro_backend 2>nul
docker rmi ctms_pro_celery_worker 2>nul

echo.
echo  [✓] CTMS Pro 已卸载完成
echo.
pause
endlocal
>>>>>>> origin/main
