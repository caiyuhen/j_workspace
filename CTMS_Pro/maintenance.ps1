<<<<<<< HEAD
#Requires -Version 5.1
<#
.SYNOPSIS
    CTMS Pro 数据库迁移与维护工具
.DESCRIPTION
    提供数据库备份、恢复、日志清理、健康检查等维护功能
#>

param(
    [ValidateSet("backup", "restore", "clean-logs", "health", "update", "shell")]
    [string]$Action = "health"
)

$INSTALL_PATH = "d:\workspace\CTMS_Pro"
$BACKUP_DIR = "$INSTALL_PATH\backups"

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "  ─── $Title " + ("─" * (50 - $Title.Length)) -ForegroundColor Cyan
}

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "  ║      CTMS Pro 系统维护工具                   ║" -ForegroundColor Magenta
    Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  [1] 数据库备份" -ForegroundColor White
    Write-Host "  [2] 数据库恢复" -ForegroundColor White
    Write-Host "  [3] 清理旧日志（>30天）" -ForegroundColor White
    Write-Host "  [4] 系统健康检查" -ForegroundColor White
    Write-Host "  [5] 更新应用（重新构建）" -ForegroundColor White
    Write-Host "  [6] 进入后端容器 Shell" -ForegroundColor White
    Write-Host "  [7] 查看实时日志" -ForegroundColor White
    Write-Host "  [0] 退出" -ForegroundColor Gray
    Write-Host ""

    $choice = Read-Host "  请选择操作"
    switch ($choice) {
        "1" { Backup-Database }
        "2" { Restore-Database }
        "3" { Clean-Logs }
        "4" { Health-Check }
        "5" { Update-App }
        "6" { docker exec -it ctms_backend bash }
        "7" { docker compose -f "$INSTALL_PATH\docker-compose.yml" logs --follow }
        "0" { exit 0 }
        default { Show-Menu }
    }
}

function Backup-Database {
    Write-Header "数据库备份"
    New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "$BACKUP_DIR\ctms_backup_$timestamp.sql"
    $zipFile = "$BACKUP_DIR\ctms_backup_$timestamp.zip"

    Write-Host "  备份中..." -ForegroundColor Cyan
    docker exec ctms_postgres pg_dump -U ctms_user -Fc ctms_pro > $backupFile

    if ($LASTEXITCODE -eq 0) {
        # 压缩备份
        Compress-Archive -Path $backupFile -DestinationPath $zipFile -CompressionLevel Optimal
        Remove-Item $backupFile
        $size = [Math]::Round((Get-Item $zipFile).Length / 1KB, 1)
        Write-Host "  ✓ 备份成功: $zipFile ($size KB)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 备份失败，请确认数据库服务正在运行" -ForegroundColor Red
    }

    Read-Host "`n  按回车继续"
    Show-Menu
}

function Restore-Database {
    Write-Header "数据库恢复"
    $backups = Get-ChildItem -Path $BACKUP_DIR -Filter "*.zip" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending

    if ($backups.Count -eq 0) {
        Write-Host "  未找到备份文件（目录: $BACKUP_DIR）" -ForegroundColor Yellow
        Read-Host "`n  按回车继续"
        Show-Menu
        return
    }

    Write-Host "  可用备份文件：" -ForegroundColor White
    for ($i = 0; $i -lt [Math]::Min($backups.Count, 10); $i++) {
        $b = $backups[$i]
        $size = [Math]::Round($b.Length / 1KB, 1)
        Write-Host "  [$i] $($b.Name) ($size KB) - $($b.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
    }

    $idx = Read-Host "`n  选择备份文件序号"
    if ($idx -match "^\d+$" -and [int]$idx -lt $backups.Count) {
        $selected = $backups[[int]$idx]
        Write-Host "  ⚠ 警告: 恢复将覆盖当前数据库！" -ForegroundColor Red
        $confirm = Read-Host "  确认恢复 $($selected.Name)? [YES/NO]"
        if ($confirm -eq "YES") {
            # 解压
            $tmpDir = "$env:TEMP\ctms_restore"
            Expand-Archive -Path $selected.FullName -DestinationPath $tmpDir -Force
            $sqlFile = Get-ChildItem -Path $tmpDir -Filter "*.sql" | Select-Object -First 1

            if ($sqlFile) {
                docker exec -i ctms_postgres pg_restore -U ctms_user -d ctms_pro --clean < $sqlFile.FullName
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✓ 恢复成功" -ForegroundColor Green
                } else {
                    Write-Host "  ✗ 恢复失败" -ForegroundColor Red
                }
                Remove-Item -Recurse -Force $tmpDir
            }
        }
    }

    Read-Host "`n  按回车继续"
    Show-Menu
}

function Clean-Logs {
    Write-Header "清理旧日志"
    $logDirs = @("$INSTALL_PATH\backend\logs")
    $cutoff = (Get-Date).AddDays(-30)
    $total = 0

    foreach ($dir in $logDirs) {
        if (Test-Path $dir) {
            $old = Get-ChildItem -Path $dir -Filter "*.log" | Where-Object { $_.LastWriteTime -lt $cutoff }
            foreach ($f in $old) {
                Remove-Item $f.FullName -Force
                $total++
                Write-Host "  删除: $($f.Name)" -ForegroundColor Gray
            }
        }
    }

    Write-Host "  ✓ 清理完成，共删除 $total 个日志文件" -ForegroundColor Green
    Read-Host "`n  按回车继续"
    Show-Menu
}

function Health-Check {
    Write-Header "系统健康检查"

    $services = @(
        @{ Container = "ctms_postgres"; Name = "PostgreSQL 数据库" },
        @{ Container = "ctms_redis";    Name = "Redis 缓存" },
        @{ Container = "ctms_minio";    Name = "MinIO 文件存储" },
        @{ Container = "ctms_backend";  Name = "FastAPI 后端" },
        @{ Container = "ctms_nginx";    Name = "Nginx 前端" },
        @{ Container = "ctms_celery";   Name = "Celery 任务队列" }
    )

    foreach ($svc in $services) {
        $status = docker inspect --format='{{.State.Status}}' $svc.Container 2>$null
        $health = docker inspect --format='{{.State.Health.Status}}' $svc.Container 2>$null
        $icon = if ($status -eq "running") { "✓" } else { "✗" }
        $color = if ($status -eq "running") { "Green" } else { "Red" }
        $healthStr = if ($health) { " [Health: $health]" } else { "" }
        Write-Host "  $icon $($svc.Name): $status$healthStr" -ForegroundColor $color
    }

    Write-Host ""
    Write-Host "  容器资源使用情况：" -ForegroundColor Cyan
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>$null

    Read-Host "`n  按回车继续"
    Show-Menu
}

function Update-App {
    Write-Header "更新应用"
    Write-Host "  此操作将重新构建后端镜像并重启服务" -ForegroundColor Yellow
    $confirm = Read-Host "  确认更新? [Y/N]"
    if ($confirm -match "^[Yy]$") {
        Set-Location $INSTALL_PATH
        Write-Host "  拉取最新代码变更..." -ForegroundColor Cyan
        Write-Host "  重新构建镜像..." -ForegroundColor Cyan
        docker compose build --no-cache backend
        Write-Host "  滚动重启服务..." -ForegroundColor Cyan
        docker compose up -d --force-recreate backend celery_worker
        Write-Host "  ✓ 更新完成" -ForegroundColor Green
    }

    Read-Host "`n  按回车继续"
    Show-Menu
}

# 主入口
Show-Menu
=======
#Requires -Version 5.1
<#
.SYNOPSIS
    CTMS Pro 数据库迁移与维护工具
.DESCRIPTION
    提供数据库备份、恢复、日志清理、健康检查等维护功能
#>

param(
    [ValidateSet("backup", "restore", "clean-logs", "health", "update", "shell")]
    [string]$Action = "health"
)

$INSTALL_PATH = "d:\workspace\CTMS_Pro"
$BACKUP_DIR = "$INSTALL_PATH\backups"

function Write-Header {
    param([string]$Title)
    Write-Host ""
    Write-Host "  ─── $Title " + ("─" * (50 - $Title.Length)) -ForegroundColor Cyan
}

function Show-Menu {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "  ║      CTMS Pro 系统维护工具                   ║" -ForegroundColor Magenta
    Write-Host "  ╚══════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "  [1] 数据库备份" -ForegroundColor White
    Write-Host "  [2] 数据库恢复" -ForegroundColor White
    Write-Host "  [3] 清理旧日志（>30天）" -ForegroundColor White
    Write-Host "  [4] 系统健康检查" -ForegroundColor White
    Write-Host "  [5] 更新应用（重新构建）" -ForegroundColor White
    Write-Host "  [6] 进入后端容器 Shell" -ForegroundColor White
    Write-Host "  [7] 查看实时日志" -ForegroundColor White
    Write-Host "  [0] 退出" -ForegroundColor Gray
    Write-Host ""

    $choice = Read-Host "  请选择操作"
    switch ($choice) {
        "1" { Backup-Database }
        "2" { Restore-Database }
        "3" { Clean-Logs }
        "4" { Health-Check }
        "5" { Update-App }
        "6" { docker exec -it ctms_backend bash }
        "7" { docker compose -f "$INSTALL_PATH\docker-compose.yml" logs --follow }
        "0" { exit 0 }
        default { Show-Menu }
    }
}

function Backup-Database {
    Write-Header "数据库备份"
    New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupFile = "$BACKUP_DIR\ctms_backup_$timestamp.sql"
    $zipFile = "$BACKUP_DIR\ctms_backup_$timestamp.zip"

    Write-Host "  备份中..." -ForegroundColor Cyan
    docker exec ctms_postgres pg_dump -U ctms_user -Fc ctms_pro > $backupFile

    if ($LASTEXITCODE -eq 0) {
        # 压缩备份
        Compress-Archive -Path $backupFile -DestinationPath $zipFile -CompressionLevel Optimal
        Remove-Item $backupFile
        $size = [Math]::Round((Get-Item $zipFile).Length / 1KB, 1)
        Write-Host "  ✓ 备份成功: $zipFile ($size KB)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ 备份失败，请确认数据库服务正在运行" -ForegroundColor Red
    }

    Read-Host "`n  按回车继续"
    Show-Menu
}

function Restore-Database {
    Write-Header "数据库恢复"
    $backups = Get-ChildItem -Path $BACKUP_DIR -Filter "*.zip" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending

    if ($backups.Count -eq 0) {
        Write-Host "  未找到备份文件（目录: $BACKUP_DIR）" -ForegroundColor Yellow
        Read-Host "`n  按回车继续"
        Show-Menu
        return
    }

    Write-Host "  可用备份文件：" -ForegroundColor White
    for ($i = 0; $i -lt [Math]::Min($backups.Count, 10); $i++) {
        $b = $backups[$i]
        $size = [Math]::Round($b.Length / 1KB, 1)
        Write-Host "  [$i] $($b.Name) ($size KB) - $($b.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))" -ForegroundColor Gray
    }

    $idx = Read-Host "`n  选择备份文件序号"
    if ($idx -match "^\d+$" -and [int]$idx -lt $backups.Count) {
        $selected = $backups[[int]$idx]
        Write-Host "  ⚠ 警告: 恢复将覆盖当前数据库！" -ForegroundColor Red
        $confirm = Read-Host "  确认恢复 $($selected.Name)? [YES/NO]"
        if ($confirm -eq "YES") {
            # 解压
            $tmpDir = "$env:TEMP\ctms_restore"
            Expand-Archive -Path $selected.FullName -DestinationPath $tmpDir -Force
            $sqlFile = Get-ChildItem -Path $tmpDir -Filter "*.sql" | Select-Object -First 1

            if ($sqlFile) {
                docker exec -i ctms_postgres pg_restore -U ctms_user -d ctms_pro --clean < $sqlFile.FullName
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "  ✓ 恢复成功" -ForegroundColor Green
                } else {
                    Write-Host "  ✗ 恢复失败" -ForegroundColor Red
                }
                Remove-Item -Recurse -Force $tmpDir
            }
        }
    }

    Read-Host "`n  按回车继续"
    Show-Menu
}

function Clean-Logs {
    Write-Header "清理旧日志"
    $logDirs = @("$INSTALL_PATH\backend\logs")
    $cutoff = (Get-Date).AddDays(-30)
    $total = 0

    foreach ($dir in $logDirs) {
        if (Test-Path $dir) {
            $old = Get-ChildItem -Path $dir -Filter "*.log" | Where-Object { $_.LastWriteTime -lt $cutoff }
            foreach ($f in $old) {
                Remove-Item $f.FullName -Force
                $total++
                Write-Host "  删除: $($f.Name)" -ForegroundColor Gray
            }
        }
    }

    Write-Host "  ✓ 清理完成，共删除 $total 个日志文件" -ForegroundColor Green
    Read-Host "`n  按回车继续"
    Show-Menu
}

function Health-Check {
    Write-Header "系统健康检查"

    $services = @(
        @{ Container = "ctms_postgres"; Name = "PostgreSQL 数据库" },
        @{ Container = "ctms_redis";    Name = "Redis 缓存" },
        @{ Container = "ctms_minio";    Name = "MinIO 文件存储" },
        @{ Container = "ctms_backend";  Name = "FastAPI 后端" },
        @{ Container = "ctms_nginx";    Name = "Nginx 前端" },
        @{ Container = "ctms_celery";   Name = "Celery 任务队列" }
    )

    foreach ($svc in $services) {
        $status = docker inspect --format='{{.State.Status}}' $svc.Container 2>$null
        $health = docker inspect --format='{{.State.Health.Status}}' $svc.Container 2>$null
        $icon = if ($status -eq "running") { "✓" } else { "✗" }
        $color = if ($status -eq "running") { "Green" } else { "Red" }
        $healthStr = if ($health) { " [Health: $health]" } else { "" }
        Write-Host "  $icon $($svc.Name): $status$healthStr" -ForegroundColor $color
    }

    Write-Host ""
    Write-Host "  容器资源使用情况：" -ForegroundColor Cyan
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>$null

    Read-Host "`n  按回车继续"
    Show-Menu
}

function Update-App {
    Write-Header "更新应用"
    Write-Host "  此操作将重新构建后端镜像并重启服务" -ForegroundColor Yellow
    $confirm = Read-Host "  确认更新? [Y/N]"
    if ($confirm -match "^[Yy]$") {
        Set-Location $INSTALL_PATH
        Write-Host "  拉取最新代码变更..." -ForegroundColor Cyan
        Write-Host "  重新构建镜像..." -ForegroundColor Cyan
        docker compose build --no-cache backend
        Write-Host "  滚动重启服务..." -ForegroundColor Cyan
        docker compose up -d --force-recreate backend celery_worker
        Write-Host "  ✓ 更新完成" -ForegroundColor Green
    }

    Read-Host "`n  按回车继续"
    Show-Menu
}

# 主入口
Show-Menu
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
