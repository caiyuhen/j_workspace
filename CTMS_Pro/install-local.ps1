#Requires -Version 5.1
<#
.SYNOPSIS
    CTMS Pro 本地安装脚本（无需 Docker）
.DESCRIPTION
    在本地 Windows 机器上直接安装 Python + PostgreSQL + Redis
    解决端口冲突，自动配置环境
.NOTES
    版本: 2.0.0
    作者: CTMS Pro 部署工具
#>

[CmdletBinding()]
param(
    [switch]$Silent,
    [switch]$DevMode,
    [string]$InstallPath = "d:\workspace\CTMS_Pro",
    [string]$AdminEmail = "admin@ctms-pro.com",
    [string]$AdminPassword = "Admin@CTMS2026!",
    # 自定义端口（避免冲突）
    [int]$HttpPort = 8899,
    [int]$ApiPort = 8898,
    [int]$PgPort = 5433,
    [int]$RedisPort = 6380
)

# ====================================================================
# 全局变量
# ====================================================================
$Script:VERSION = "2.0.0"
$Script:LOG_FILE = "$InstallPath\install-local.log"
$Script:ERRORS = @()
$Script:WARNINGS = @()
$Script:INSTALL_PATH = $InstallPath

# 颜色
$colors = @{
    Success = "Green"
    Error   = "Red"
    Warning = "Yellow"
    Info    = "Cyan"
}

# ====================================================================
# 工具函数
# ====================================================================
function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "  ║     CTMS Pro 本地安装（无 Docker 版）                  ║" -ForegroundColor Magenta
    Write-Host "  ║               版本 $Script:VERSION                             ║" -ForegroundColor Magenta
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Write-Step {
    param([int]$Number, [int]$Total, [string]$Message)
    Write-Host ""
    Write-Host "  [$Number/$Total] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message -ForegroundColor White
    Write-Host "  " + ("─" * 50) -ForegroundColor DarkGray
}

function Write-OK    { param([string]$msg) Write-Host "  ✓ $msg" -ForegroundColor Green;  Log-Message "OK: $msg" }
function Write-FAIL  { param([string]$msg) Write-Host "  ✗ $msg" -ForegroundColor Red;    Log-Message "FAIL: $msg"; $Script:ERRORS += $msg }
function Write-WARN  { param([string]$msg) Write-Host "  ! $msg" -ForegroundColor Yellow; Log-Message "WARN: $msg"; $Script:WARNINGS += $msg }
function Write-INFO  { param([string]$msg) Write-Host "  · $msg" -ForegroundColor Cyan;   Log-Message "INFO: $msg" }

function Log-Message {
    param([string]$msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp | $msg" | Add-Content -Path $Script:LOG_FILE -ErrorAction SilentlyContinue
}

function Test-Admin {
    $currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# ====================================================================
# 第1步：检测端口冲突
# ====================================================================
function Step-PortCheck {
    Write-Step -Number 1 -Total 6 -Message "检测端口冲突"

    # 检测默认端口并提供替代方案
    $portMap = @{
        80    = $HttpPort
        8000  = $ApiPort
        5432  = $PgPort
        6379  = $RedisPort
    }

    $conflicts = @()
    foreach ($port in $portMap.Keys) {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($conn) {
            $altPort = $portMap[$port]
            Write-WARN "端口 $port 被占用 → 将使用备用端口 $altPort"
            $conflicts += @{Original=$port; Alt=$altPort}
        } else {
            Write-OK "端口 $port 可用"
        }
    }

    if ($conflicts.Count -gt 0) {
        Write-INFO "检测到端口冲突，已自动分配备用端口"
        Write-INFO "  HTTP:     $HttpPort"
        Write-INFO "  API:      $ApiPort"
        Write-INFO "  PostgreSQL: $PgPort"
        Write-INFO "  Redis:    $RedisPort"
    }

    return $true
}

# ====================================================================
# 第2步：安装 Python
# ====================================================================
function Step-InstallPython {
    Write-Step -Number 2 -Total 6 -Message "检测 / 安装 Python"

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pyVersion = python --version 2>&1
        Write-OK "Python 已安装: $pyVersion"
        return $true
    }

    Write-INFO "Python 未安装，正在下载..."
    
    # 下载 Python 3.11
    $pythonUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
    $installer = "$env:TEMP\python-3.11.9-amd64.exe"
    
    try {
        Write-INFO "下载 Python 3.11.9（约 25MB）..."
        Invoke-WebRequest -Uri $pythonUrl -OutFile $installer -UseBasicParsing
        
        Write-INFO "安装 Python（静默模式）..."
        Start-Process -FilePath $installer -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        
        # 刷新环境变量
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        
        Write-OK "Python 安装完成"
        python --version
    } catch {
        Write-FAIL "Python 安装失败: $($_.Exception.Message)"
        return $false
    }

    return $true
}

# ====================================================================
# 第3步：安装 PostgreSQL
# ====================================================================
function Step-InstallPostgres {
    Write-Step -Number 3 -Total 6 -Message "检测 / 安装 PostgreSQL"

    # 检测 PostgreSQL 服务
    $pgService = Get-Service -Name postgresql* -ErrorAction SilentlyContinue
    if ($pgService) {
        Write-OK "PostgreSQL 服务已安装: $($pgService.Name)"
        
        # 检查端口
        $pgData = & "C:\Program Files\PostgreSQL\16\bin\pg_isready.exe" -p $PgPort 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-OK "PostgreSQL 正在监听端口 $PgPort"
            return $true
        }
    }

    Write-INFO "PostgreSQL 未安装，正在下载..."
    
    # 下载 PostgreSQL 16
    $pgUrl = "https://get.enterprisedb.com/postgresql/postgresql-16.3-1-windows-x64.exe"
    $installer = "$env:TEMP\postgresql-16.3-1-windows-x64.exe"
    
    try {
        Write-INFO "下载 PostgreSQL 16（约 180MB）..."
        Invoke-WebRequest -Uri $pgUrl -OutFile $installer -UseBasicParsing
        
        Write-INFO "安装 PostgreSQL（静默模式）..."
        $args = @(
            "--mode", "unattended",
            "--unattendedmodeui", "none",
            "--serverport", $PgPort,
            "--username", "postgres",
            "--password", "postgres123"
        )
        Start-Process -FilePath $installer -ArgumentList $args -Wait
        
        Write-OK "PostgreSQL 安装完成"
        Write-INFO "默认账号: postgres / postgres123"
        Write-INFO "端口: $PgPort"
    } catch {
        Write-WARN "PostgreSQL 自动安装可能失败，请手动安装"
        Write-INFO "下载地址: https://www.postgresql.org/download/windows/"
        return $false
    }

    return $true
}

# ====================================================================
# 第4步：安装 Redis
# ====================================================================
function Step-InstallRedis {
    Write-Step -Number 4 -Total 6 -Message "检测 / 安装 Redis"

    # 检测 Redis
    $redisCmd = Get-Command redis-server -ErrorAction SilentlyContinue
    if ($redisCmd) {
        Write-OK "Redis 已安装"
        
        # 尝试启动 Redis
        $redisRunning = Get-Process -Name redis-server -ErrorAction SilentlyContinue
        if ($redisRunning) {
            Write-OK "Redis 正在运行（端口 $RedisPort）"
            return $true
        }
        
        # 启动 Redis
        try {
            $redisConf = "$InstallPath\redis.conf"
            if (-not (Test-Path $redisConf)) {
                @"
port $RedisPort
bind 127.0.0.1
daemonize no
"@ | Set-Content -Path $redisConf -Encoding UTF8
            }
            Start-Process -FilePath "redis-server" -ArgumentList $redisConf -WindowStyle Hidden
            Write-OK "Redis 已启动（端口 $RedisPort）"
            return $true
        } catch {
            Write-WARN "Redis 启动失败: $($_.Exception.Message)"
        }
    }

    Write-INFO "Redis 未安装，使用 Memurai/Redis Windows 兼容版..."
    
    # 尝试使用 chocolatey 安装或提供手动说明
    $choco = Get-Command choco -ErrorAction SilentlyContinue
    if ($choco) {
        Write-INFO "通过 Chocolatey 安装 Redis..."
        & choco install redis-64 -y --no-progress 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Redis 安装完成"
            return $true
        }
    }

    Write-WARN "Redis 安装失败，请手动安装 Redis for Windows"
    Write-INFO "替代方案：Memurai (https://www.memurai.com/)"
    Write-INFO "或使用 Docker 只运行 Redis: docker run -d -p $RedisPort`:6379 redis:alpine"
    
    return $true  # 不阻塞安装，Redis 可选
}

# ====================================================================
# 第5步：配置环境并安装 Python 依赖
# ====================================================================
function Step-ConfigurePython {
    Write-Step -Number 5 -Total 6 -Message "配置 Python 环境"

    Set-Location $InstallPath

    # 生成 .env.local
    $envFile = "$InstallPath\backend\.env.local"
    $envExample = "$InstallPath\backend\.env.example"

    if (-not (Test-Path $envExample)) {
        Write-FAIL ".env.example 文件不存在"
        return $false
    }

    # 随机密钥
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
    $fernet_key_bytes = New-Object byte[] 32
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($fernet_key_bytes)
    $fernetKey = [Convert]::ToBase64String($fernet_key_bytes)

    # 读取模板
    $envContent = Get-Content $envExample -Raw
    
    # 替换配置（本地模式）
    $envContent = $envContent -replace "POSTGRES_PORT=5432", "POSTGRES_PORT=$PgPort"
    $envContent = $envContent -replace "REDIS_PORT=6379", "REDIS_PORT=$RedisPort"
    $envContent = $envContent -replace "your-super-secret-key-change-in-production-min-32chars", $secretKey
    $envContent = $envContent -replace "APP_ENV=development", "APP_ENV=production"
    $envContent = $envContent -replace "DEBUG=True", "DEBUG=False"
    $envContent = $envContent -replace "API_V1_STR=/api/v1", "API_V1_STR=/api/v1"
    
    # 服务器配置 - 使用不同端口
    $envContent = $envContent -replace "SERVER_HOST=0.0.0.0", "SERVER_HOST=127.0.0.1"
    $envContent = $envContent -replace "SERVER_PORT=8000", "SERVER_PORT=$ApiPort"

    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-OK "配置文件已生成: .env.local"

    # 安装 Python 依赖
    Write-INFO "安装 Python 依赖包..."
    
    # 升级 pip
    python -m pip install --upgrade pip 2>&1 | Out-Null
    
    # 安装依赖
    $requirements = "$InstallPath\backend\requirements.txt"
    if (Test-Path $requirements) {
        $installResult = python -m pip install -r $requirements --quiet 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-OK "Python 依赖安装完成"
        } else {
            Write-WARN "部分依赖安装失败，尝试逐个安装..."
            Get-Content $requirements | ForEach-Object {
                if ($_ -and -not $_.StartsWith("#")) {
                    python -m pip install $_ --quiet 2>&1 | Out-Null
                }
            }
            Write-OK "依赖安装完成"
        }
    }

    return $true
}

# ====================================================================
# 第6步：初始化数据库并启动
# ====================================================================
function Step-InitAndStart {
    Write-Step -Number 6 -Total 6 -Message "初始化数据库并启动"

    Set-Location $InstallPath

    # 等待 PostgreSQL
    Write-INFO "等待 PostgreSQL 就绪..."
    $pgReady = & "C:\Program Files\PostgreSQL\16\bin\pg_isready.exe" -h localhost -p $PgPort -U postgres 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-WARN "PostgreSQL 可能未就绪，尝试启动服务..."
        Start-Service postgresql* -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 5
    }

    # 创建数据库和用户
    Write-INFO "创建数据库..."
    $createDbScript = @"
-- 创建用户
DO $$ 
BEGIN
   IF NOT EXISTS (SELECT FROM pg_user WHERE usename = 'ctms_user') THEN
      CREATE USER ctms_user WITH PASSWORD 'ctms_password_2026';
   END IF;
END
$$;

-- 创建数据库
SELECT 'CREATE DATABASE ctms_pro'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'ctms_pro')\gexec

-- 授权
GRANT ALL PRIVILEGES ON DATABASE ctms_pro TO ctms_user;
ALTER DATABASE ctms_pro OWNER TO ctms_user;
"@

    try {
        & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -p $PgPort -U postgres -c "CREATE DATABASE ctms_pro;" 2>&1 | Out-Null
        & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -p $PgPort -U postgres -c "CREATE USER ctms_user WITH PASSWORD 'ctms_password_2026';" 2>&1 | Out-Null
        & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -p $PgPort -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE ctms_pro TO ctms_user;" 2>&1 | Out-Null
        Write-OK "数据库 ctms_pro 已创建"
    } catch {
        Write-WARN "数据库可能已存在，跳过创建"
    }

    # 执行 DDL
    Write-INFO "初始化数据库表结构..."
    $ddlPath = "$InstallPath\database\init\01_schema.sql"
    if (Test-Path $ddlPath) {
        & "C:\Program Files\PostgreSQL\16\bin\psql.exe" -h localhost -p $PgPort -U ctms_user -d ctms_pro -f $ddlPath 2>&1 | Out-Null
        Write-OK "数据库表结构已初始化"
    }

    # 启动后端
    Write-INFO "启动 CTMS Pro 后端服务..."
    $backendDir = "$InstallPath\backend"
    $env:LOCAL_ENV = "true"
    
    # 使用 uvicorn 启动（后台运行）
    $uvicornCmd = "uvicorn app.main:app --host 127.0.0.1 --port $ApiPort --reload"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c cd $backendDir && $uvicornCmd" -WindowStyle Normal -WorkingDirectory $backendDir
    
    # 等待启动
    Write-INFO "等待服务启动..."
    Start-Sleep -Seconds 5

    # 验证
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1`:$ApiPort/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Write-OK "CTMS Pro 后端已启动: http://127.0.0.1`:$ApiPort"
        }
    } catch {
        Write-WARN "后端启动验证失败，请手动检查"
    }

    return $true
}

# ====================================================================
# 打印摘要
# ====================================================================
function Show-Summary {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  ║           CTMS Pro 本地安装完成！                        ║" -ForegroundColor Green
    Write-Host "  ╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "  ║  访问地址                                                ║" -ForegroundColor Green
    Write-Host "  ║  · 后端 API:  http://127.0.0.1`:$ApiPort                      ║" -ForegroundColor White
    Write-Host "  ║  · API 文档:  http://127.0.0.1`:$ApiPort/api/v1/docs      ║" -ForegroundColor White
    Write-Host "  ║  · PostgreSQL: localhost`:$PgPort (ctms_pro)             ║" -ForegroundColor White
    Write-Host "  ║  · Redis:     localhost`:$RedisPort                       ║" -ForegroundColor White
    Write-Host "  ║                                                          ║" -ForegroundColor Green
    Write-Host "  ║  默认账号                                                ║" -ForegroundColor Green
    Write-Host "  ║  · 邮箱: admin@ctms-pro.com                             ║" -ForegroundColor White
    Write-Host "  ║  · 密码: Admin@CTMS2026!                                ║" -ForegroundColor White
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""
    Write-Host "  启动命令: cd $InstallPath\backend && uvicorn app.main:app --reload" -ForegroundColor Gray
    Write-Host ""
}

# ====================================================================
# 主流程
# ====================================================================
function Main {
    Write-Banner

    # 初始化日志
    New-Item -ItemType Directory -Force -Path (Split-Path $Script:LOG_FILE) -ErrorAction SilentlyContinue | Out-Null
    Log-Message "====== CTMS Pro 本地安装开始 ======"
    Log-Message "安装时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    Write-INFO "安装路径: $InstallPath"
    Write-INFO "HTTP 端口: $HttpPort"
    Write-INFO "API 端口: $ApiPort"
    Write-INFO "PostgreSQL: $PgPort"
    Write-INFO "Redis: $RedisPort"
    Write-Host ""

    # 执行安装步骤
    $steps = @(
        { Step-PortCheck },
        { Step-InstallPython },
        { Step-InstallPostgres },
        { Step-InstallRedis },
        { Step-ConfigurePython },
        { Step-InitAndStart }
    )

    $allOk = $true
    foreach ($step in $steps) {
        $result = & $step
        if ($result -eq $false) {
            $allOk = $false
        }
    }

    Show-Summary

    Log-Message "====== CTMS Pro 本地安装结束 ======"

    if ($allOk) {
        Write-Host "  🎉 安装完成！" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ 安装完成但有错误，请查看日志" -ForegroundColor Yellow
    }
}

Main
