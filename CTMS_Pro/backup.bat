<<<<<<< HEAD
@echo off
chcp 65001 >nul 2>&1
setlocal
title CTMS Pro - 数据库备份

echo.
echo  CTMS Pro - 数据库备份工具
echo  ──────────────────────────
echo.

cd /d "%~dp0"

:: 创建备份目录
if not exist "backups" mkdir backups

:: 生成带时间戳的文件名
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%%dt:~10,2%%dt:~12,2%"
set "backupFile=backups\ctms_backup_%timestamp%.sql"

echo  备份文件: %backupFile%
echo.

docker exec ctms_postgres pg_dump -U ctms_user ctms_pro > "%backupFile%"

if %errorlevel% equ 0 (
    echo  [✓] 备份成功: %backupFile%
) else (
    echo  [错误] 备份失败
)

echo.
pause
endlocal
=======
@echo off
chcp 65001 >nul 2>&1
setlocal
title CTMS Pro - 数据库备份

echo.
echo  CTMS Pro - 数据库备份工具
echo  ──────────────────────────
echo.

cd /d "%~dp0"

:: 创建备份目录
if not exist "backups" mkdir backups

:: 生成带时间戳的文件名
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "timestamp=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%_%dt:~8,2%%dt:~10,2%%dt:~12,2%"
set "backupFile=backups\ctms_backup_%timestamp%.sql"

echo  备份文件: %backupFile%
echo.

docker exec ctms_postgres pg_dump -U ctms_user ctms_pro > "%backupFile%"

if %errorlevel% equ 0 (
    echo  [✓] 备份成功: %backupFile%
) else (
    echo  [错误] 备份失败
)

echo.
pause
endlocal
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
