<<<<<<< HEAD
#Requires -Version 5.1
<#
.SYNOPSIS
    CTMS Pro 临床试验管理系统 - Windows 一键安装脚本
.DESCRIPTION
    自动检测并安装所有依赖组件，初始化数据库，配置系统环境。
    支持: Windows 10/11, Windows Server 2016+
.NOTES
    版本: 1.0.0
    作者: CTMS Pro 部署工具
    要求: PowerShell 5.1+, 管理员权限（推荐）
#>

[CmdletBinding()]
param(
    [switch]$Silent,          # 静默安装（不询问）
    [switch]$SkipDocker,      # 跳过Docker安装
    [switch]$DevMode,         # 开发模式（不启动生产服务）
    [string]$InstallPath = "d:\workspace\CTMS_Pro",
    [string]$AdminEmail = "admin@ctms-pro.com",
    [string]$AdminPassword = "Admin@CTMS2026!"
)

# ====================================================================
# 全局变量
# ====================================================================
$Script:VERSION = "1.0.0"
$Script:LOG_FILE = "$InstallPath\install.log"
$Script:ERRORS = @()
$Script:WARNINGS = @()
$Script:INSTALL_PATH = $InstallPath

# 颜色方案
$colors = @{
    Success = "Green"
    Error   = "Red"
    Warning = "Yellow"
    Info    = "Cyan"
    Header  = "Magenta"
    Step    = "White"
}

# ====================================================================
# 工具函数
# ====================================================================
function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "  ║         CTMS Pro 临床试验管理系统 安装程序               ║" -ForegroundColor Magenta
    Write-Host "  ║                   版本 $Script:VERSION                          ║" -ForegroundColor Magenta
    Write-Host "  ║         符合 GCP / FDA 21 CFR Part 11 / GDPR            ║" -ForegroundColor Magenta
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Write-Step {
    param([int]$Number, [int]$Total, [string]$Message)
    Write-Host ""
    Write-Host "  [$Number/$Total] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message -ForegroundColor White
    Write-Host "  " + ("─" * 58) -ForegroundColor DarkGray
}

function Write-OK    { param([string]$msg) Write-Host "  ✓ $msg" -ForegroundColor Green;  Log-Message "OK: $msg" }
function Write-FAIL  { param([string]$msg) Write-Host "  ✗ $msg" -ForegroundColor Red;    Log-Message "FAIL: $msg"; $Script:ERRORS += $msg }
function Write-WARN  { param([string]$msg) Write-Host "  ! $msg" -ForegroundColor Yellow; Log-Message "WARN: $msg"; $Script:WARNINGS += $msg }
function Write-INFO  { param([string]$msg) Write-Host "  · $msg" -ForegroundColor Cyan;   Log-Message "INFO: $msg" }
function Write-SUB   { param([string]$msg) Write-Host "    $msg" -ForegroundColor Gray }

function Log-Message {
    param([string]$msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp | $msg" | Add-Content -Path $Script:LOG_FILE -ErrorAction SilentlyContinue
}

function Test-Admin {
    $currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Show-Progress {
    param([int]$Percent, [string]$Activity)
    Write-Progress -Activity $Activity -PercentComplete $Percent -Status "$Percent% 完成"
}

function Confirm-Action {
    param([string]$Message, [string]$Default = "Y")
    if ($Silent) { return $true }
    $choice = Read-Host "  $Message [Y/N] (默认: $Default)"
    if ([string]::IsNullOrEmpty($choice)) { $choice = $Default }
    return $choice -match "^[Yy]"
}

# ====================================================================
# 第1步：环境预检
# ====================================================================
function Step-PreCheck {
    Write-Step -Number 1 -Total 7 -Message "系统环境预检"

    # OS版本
    $os = Get-WmiObject -Class Win32_OperatingSystem
    $osVersion = $os.Version
    Write-INFO "操作系统: $($os.Caption) (Build $osVersion)"

    # 架构
    $arch = $env:PROCESSOR_ARCHITECTURE
    Write-INFO "处理器架构: $arch"
    if ($arch -ne "AMD64") {
        Write-WARN "检测到非x64架构，部分组件可能不兼容"
    }

    # 内存
    $ramGB = [Math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
    Write-INFO "系统内存: ${ramGB} GB"
    if ($ramGB -lt 4) {
        Write-WARN "内存不足 4GB（推荐 8GB+），系统性能可能受限"
    } else {
        Write-OK "内存充足 (${ramGB} GB)"
    }

    # 磁盘空间
    $drive = Split-Path -Qualifier $InstallPath
    $disk = Get-PSDrive -Name ($drive.TrimEnd(':'))
    $freeGB = [Math]::Round($disk.Free / 1GB, 1)
    Write-INFO "安装目录可用空间: ${freeGB} GB"
    if ($freeGB -lt 10) {
        Write-WARN "磁盘可用空间不足 10GB，建议清理后再安装"
    } else {
        Write-OK "磁盘空间充足 (${freeGB} GB)"
    }

    # 管理员权限
    if (Test-Admin) {
        Write-OK "以管理员身份运行"
    } else {
        Write-WARN "未以管理员身份运行，部分功能（端口注册、服务安装）可能受限"
    }

    # PowerShell版本
    $psVersion = $PSVersionTable.PSVersion
    Write-INFO "PowerShell 版本: $psVersion"
    if ($psVersion.Major -lt 5) {
        Write-FAIL "需要 PowerShell 5.1 或更高版本"
        return $false
    }
    Write-OK "PowerShell 版本满足要求"

    # 网络连通性
    Write-INFO "检测网络连通性..."
    $netOk = Test-NetConnection -ComputerName "8.8.8.8" -Port 53 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($netOk.TcpTestSucceeded) {
        Write-OK "网络连接正常"
    } else {
        Write-WARN "网络连接异常，离线安装模式（需本地已有依赖）"
    }

    # 端口占用检测
    $portsToCheck = @(80, 443, 5432, 6379, 8000, 9000, 9001)
    $usedPorts = @()
    foreach ($port in $portsToCheck) {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($conn) { $usedPorts += $port }
    }
    if ($usedPorts.Count -gt 0) {
        Write-WARN "以下端口已被占用: $($usedPorts -join ', ')  ← 可能导致服务冲突"
    } else {
        Write-OK "所有必要端口（80/443/5432/6379/8000/9000）均可用"
    }

    return $true
}

# ====================================================================
# 第2步：安装 Docker Desktop
# ====================================================================
function Step-InstallDocker {
    Write-Step -Number 2 -Total 7 -Message "检测 / 安装 Docker"

    # 检查 Docker 是否已安装
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
        if ($dockerVersion) {
            Write-OK "Docker 已安装 (版本 $dockerVersion)"

            # 检查 Docker Compose
            $composeVersion = docker compose version --short 2>$null
            if ($composeVersion) {
                Write-OK "Docker Compose 已安装 (版本 $composeVersion)"
            } else {
                Write-WARN "Docker Compose 未检测到，将尝试安装"
                Install-DockerCompose
            }
            return $true
        }
    }

    # Docker 未安装
    Write-INFO "Docker Desktop 未安装"

    if ($SkipDocker) {
        Write-WARN "已跳过 Docker 安装（-SkipDocker 参数）"
        Write-WARN "请手动安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
        return $false
    }

    if (-not (Confirm-Action "是否自动下载并安装 Docker Desktop？（约 500MB）")) {
        Write-WARN "跳过 Docker 安装，请手动安装后重新运行此脚本"
        return $false
    }

    # 检查 WSL2（Docker Desktop 依赖）
    Write-INFO "检测 WSL2..."
    $wslStatus = wsl --status 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-INFO "安装 WSL2..."
        try {
            wsl --install --no-distribution 2>$null
            Write-OK "WSL2 安装成功（可能需要重启）"
        } catch {
            Write-WARN "WSL2 安装失败，Docker 将使用 Hyper-V 模式"
        }
    } else {
        Write-OK "WSL2 已就绪"
    }

    # 下载 Docker Desktop
    $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"

    Write-INFO "正在下载 Docker Desktop..."
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($dockerUrl, $dockerInstaller)
        Write-OK "Docker Desktop 下载完成"
    } catch {
        Write-FAIL "Docker Desktop 下载失败: $($_.Exception.Message)"
        Write-INFO "请手动下载: $dockerUrl"
        return $false
    }

    # 安装 Docker Desktop
    Write-INFO "正在安装 Docker Desktop（静默模式）..."
    try {
        Start-Process -FilePath $dockerInstaller -ArgumentList "install", "--quiet", "--accept-license", "--no-windows-containers" -Wait
        Write-OK "Docker Desktop 安装完成"
        Write-WARN "请重启计算机后重新运行安装程序"
        return $false
    } catch {
        Write-FAIL "Docker Desktop 安装失败: $($_.Exception.Message)"
        return $false
    }
}

function Install-DockerCompose {
    Write-INFO "安装 Docker Compose Plugin..."
    try {
        $composeUrl = "https://github.com/docker/compose/releases/latest/download/docker-compose-windows-x86_64.exe"
        $composePath = "$env:ProgramFiles\Docker\cli-plugins\docker-compose.exe"
        New-Item -ItemType Directory -Force -Path (Split-Path $composePath) | Out-Null
        Invoke-WebRequest -Uri $composeUrl -OutFile $composePath -UseBasicParsing
        Write-OK "Docker Compose 安装完成"
    } catch {
        Write-WARN "Docker Compose 自动安装失败，请手动安装"
    }
}

# ====================================================================
# 第3步：配置环境变量
# ====================================================================
function Step-ConfigureEnv {
    Write-Step -Number 3 -Total 7 -Message "配置环境变量"

    $envFile = "$InstallPath\backend\.env"
    $envExample = "$InstallPath\backend\.env.example"

    if (-not (Test-Path $envExample)) {
        Write-FAIL ".env.example 文件不存在，请确认项目文件完整"
        return $false
    }

    # 生成随机密钥
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
    $fernet_key_bytes = New-Object byte[] 32
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($fernet_key_bytes)
    $fernetKey = [Convert]::ToBase64String($fernet_key_bytes)

    if (Test-Path $envFile) {
        if (-not (Confirm-Action ".env 文件已存在，是否覆盖？")) {
            Write-OK "保留现有 .env 配置"
            return $true
        }
    }

    # 读取模板并替换
    $envContent = Get-Content $envExample -Raw
    $envContent = $envContent -replace "your-super-secret-key-change-in-production-min-32chars", $secretKey
    $envContent = $envContent -replace "APP_ENV=development", "APP_ENV=production"
    $envContent = $envContent -replace "DEBUG=True", "DEBUG=False"

    # 写入 .env
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-OK ".env 配置文件已生成"
    Write-SUB "位置: $envFile"

    # 生成 SECRET_KEY 到 docker-compose 环境
    [Environment]::SetEnvironmentVariable("CTMS_SECRET_KEY", $secretKey, "Process")
    Write-OK "SECRET_KEY 已随机生成 (64位)"

    # 显示重要配置
    Write-INFO "关键配置信息："
    Write-SUB "数据库密码: ctms_password_2026"
    Write-SUB "MinIO密码:  minioadmin123"
    Write-SUB "超管账号:   $AdminEmail"
    Write-SUB "超管密码:   $AdminPassword"
    Write-WARN "⚠ 生产环境请务必修改以上默认密码！"

    return $true
}

# ====================================================================
# 第4步：构建并启动 Docker 服务
# ====================================================================
function Step-StartServices {
    Write-Step -Number 4 -Total 7 -Message "构建并启动所有服务"

    Set-Location $InstallPath

    # 拉取基础镜像
    Write-INFO "拉取基础 Docker 镜像..."
    $images = @("postgres:15-alpine", "redis:7-alpine", "nginx:alpine")
    foreach ($img in $images) {
        Write-SUB "拉取 $img ..."
        docker pull $img --quiet 2>$null
    }

    # 构建后端镜像
    Write-INFO "构建 CTMS Pro 后端镜像（首次约需 3-5 分钟）..."
    $buildResult = docker compose build --no-cache 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "后端镜像构建成功"
    } else {
        Write-FAIL "镜像构建失败"
        Write-SUB $buildResult
        return $false
    }

    # 启动服务（按依赖顺序）
    Write-INFO "启动数据库服务..."
    docker compose up -d postgres redis 2>$null
    Start-Sleep -Seconds 10

    # 等待 PostgreSQL 就绪
    Write-INFO "等待 PostgreSQL 初始化..."
    $retries = 0
    $maxRetries = 30
    while ($retries -lt $maxRetries) {
        $pgReady = docker exec ctms_postgres pg_isready -U ctms_user -d ctms_pro 2>$null
        if ($pgReady -match "accepting connections") {
            Write-OK "PostgreSQL 已就绪"
            break
        }
        $retries++
        Start-Sleep -Seconds 2
        Write-Progress -Activity "等待 PostgreSQL..." -PercentComplete (($retries / $maxRetries) * 100)
    }
    Write-Progress -Completed -Activity "等待 PostgreSQL..."

    if ($retries -ge $maxRetries) {
        Write-FAIL "PostgreSQL 启动超时（60秒），请检查日志"
        return $false
    }

    # 启动所有服务
    Write-INFO "启动全部服务..."
    docker compose up -d 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-OK "所有服务已启动"
    } else {
        Write-FAIL "服务启动失败，请查看日志：docker compose logs"
        return $false
    }

    return $true
}

# ====================================================================
# 第5步：初始化数据库
# ====================================================================
function Step-InitDatabase {
    Write-Step -Number 5 -Total 7 -Message "初始化数据库"

    # 等待后端就绪
    Write-INFO "等待后端 API 就绪..."
    $retries = 0
    $maxRetries = 30
    while ($retries -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-OK "后端 API 已就绪"
                break
            }
        } catch { }
        $retries++
        Start-Sleep -Seconds 3
        Write-Progress -Activity "等待后端启动..." -PercentComplete (($retries / $maxRetries) * 100)
    }
    Write-Progress -Completed -Activity "等待后端启动..."

    if ($retries -ge $maxRetries) {
        Write-WARN "后端 API 未在预期时间内响应，数据库可能已通过 SQL 脚本初始化"
    }

    # 验证数据库表
    Write-INFO "验证数据库表结构..."
    $tableCheck = docker exec ctms_postgres psql -U ctms_user -d ctms_pro -c "\dt" 2>$null
    if ($tableCheck -match "users") {
        Write-OK "数据库表结构验证通过"
    } else {
        Write-INFO "手动执行数据库初始化脚本..."
        docker exec -i ctms_postgres psql -U ctms_user -d ctms_pro -f /docker-entrypoint-initdb.d/01_schema.sql 2>$null
        Write-OK "数据库初始化完成"
    }

    # 检查超管账号
    $userCheck = docker exec ctms_postgres psql -U ctms_user -d ctms_pro -t -c "SELECT COUNT(*) FROM users WHERE email='$AdminEmail';" 2>$null
    if ($userCheck -match "1") {
        Write-OK "超级管理员账号已存在: $AdminEmail"
    } else {
        Write-WARN "超管账号未找到，请登录后手动创建或通过 API 初始化"
    }

    return $true
}

# ====================================================================
# 第6步：配置 Windows 防火墙
# ====================================================================
function Step-ConfigureFirewall {
    Write-Step -Number 6 -Total 7 -Message "配置防火墙规则"

    if (-not (Test-Admin)) {
        Write-WARN "需要管理员权限配置防火墙，跳过此步骤"
        return $true
    }

    $rules = @(
        @{ Name = "CTMS Pro HTTP";       Port = 80;   Protocol = "TCP" },
        @{ Name = "CTMS Pro HTTPS";      Port = 443;  Protocol = "TCP" },
        @{ Name = "CTMS Pro API";        Port = 8000; Protocol = "TCP" },
        @{ Name = "CTMS Pro PostgreSQL"; Port = 5432; Protocol = "TCP" },
        @{ Name = "CTMS Pro MinIO";      Port = 9000; Protocol = "TCP" }
    )

    foreach ($rule in $rules) {
        $existing = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
        if (-not $existing) {
            try {
                New-NetFirewallRule `
                    -DisplayName $rule.Name `
                    -Direction Inbound `
                    -Protocol $rule.Protocol `
                    -LocalPort $rule.Port `
                    -Action Allow `
                    -Profile Any `
                    -ErrorAction Stop | Out-Null
                Write-OK "防火墙规则: $($rule.Name) (端口 $($rule.Port))"
            } catch {
                Write-WARN "无法创建防火墙规则: $($rule.Name)"
            }
        } else {
            Write-OK "防火墙规则已存在: $($rule.Name)"
        }
    }

    return $true
}

# ====================================================================
# 第7步：安装验证与摘要
# ====================================================================
function Step-Verify {
    Write-Step -Number 7 -Total 7 -Message "安装验证"

    $checks = @()

    # 检查各服务状态
    $services = @("ctms_postgres", "ctms_redis", "ctms_backend", "ctms_nginx", "ctms_minio")
    foreach ($svc in $services) {
        $status = docker inspect --format='{{.State.Status}}' $svc 2>$null
        if ($status -eq "running") {
            Write-OK "服务运行中: $svc"
            $checks += $true
        } else {
            Write-FAIL "服务异常: $svc (状态: $status)"
            $checks += $false
        }
    }

    # HTTP 连通性测试
    $endpoints = @(
        @{ Url = "http://localhost";         Name = "前端首页" },
        @{ Url = "http://localhost:8000/health"; Name = "后端健康检查" },
        @{ Url = "http://localhost/api/v1/docs"; Name = "API文档" }
    )

    foreach ($ep in $endpoints) {
        try {
            $resp = Invoke-WebRequest -Uri $ep.Url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            Write-OK "$($ep.Name): $($ep.Url) → HTTP $($resp.StatusCode)"
            $checks += $true
        } catch {
            Write-WARN "$($ep.Name) 暂时不可访问（服务可能仍在启动中）: $($ep.Url)"
            $checks += $false
        }
    }

    return $true
}

# ====================================================================
# 创建快捷方式
# ====================================================================
function Create-Shortcuts {
    Write-INFO "创建桌面快捷方式..."

    $desktopPath = [Environment]::GetFolderPath("Desktop")

    # CTMS Pro 系统入口
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut("$desktopPath\CTMS Pro.url")
    $shortcut.TargetPath = "http://localhost"
    $shortcut.Save()
    Write-OK "桌面快捷方式已创建: CTMS Pro"

    # API 文档
    $shortcut2 = $shell.CreateShortcut("$desktopPath\CTMS Pro API文档.url")
    $shortcut2.TargetPath = "http://localhost/api/v1/docs"
    $shortcut2.Save()
    Write-OK "桌面快捷方式已创建: CTMS Pro API文档"
}

# ====================================================================
# 打印安装摘要
# ====================================================================
function Show-Summary {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  ║              CTMS Pro 安装完成！                         ║" -ForegroundColor Green
    Write-Host "  ╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "  ║  访问地址                                                ║" -ForegroundColor Green
    Write-Host "  ║  · 系统入口:    http://localhost                         ║" -ForegroundColor White
    Write-Host "  ║  · API 文档:    http://localhost/api/v1/docs             ║" -ForegroundColor White
    Write-Host "  ║  · MinIO 控制台: http://localhost:9001                   ║" -ForegroundColor White
    Write-Host "  ║                                                          ║" -ForegroundColor Green
    Write-Host "  ║  默认账号                                                ║" -ForegroundColor Green
    Write-Host "  ║  · 邮箱: admin@ctms-pro.com                             ║" -ForegroundColor White
    Write-Host "  ║  · 密码: Admin@CTMS2026!                                ║" -ForegroundColor White
    Write-Host "  ║                                                          ║" -ForegroundColor Green
    Write-Host "  ║  管理命令                                                ║" -ForegroundColor Green
    Write-Host "  ║  · 启动: start.bat                                       ║" -ForegroundColor White
    Write-Host "  ║  · 停止: stop.bat                                        ║" -ForegroundColor White
    Write-Host "  ║  · 日志: docker compose logs -f                         ║" -ForegroundColor White
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""

    if ($Script:WARNINGS.Count -gt 0) {
        Write-Host "  ⚠ 安装警告（$($Script:WARNINGS.Count) 条）：" -ForegroundColor Yellow
        foreach ($w in $Script:WARNINGS) {
            Write-Host "    · $w" -ForegroundColor Yellow
        }
    }

    if ($Script:ERRORS.Count -gt 0) {
        Write-Host ""
        Write-Host "  ✗ 安装错误（$($Script:ERRORS.Count) 条）：" -ForegroundColor Red
        foreach ($e in $Script:ERRORS) {
            Write-Host "    · $e" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "  详细日志: $Script:LOG_FILE" -ForegroundColor Gray
    }
}

# ====================================================================
# 主流程
# ====================================================================
function Main {
    Write-Banner

    # 初始化日志
    New-Item -ItemType Directory -Force -Path (Split-Path $Script:LOG_FILE) | Out-Null
    Log-Message "====== CTMS Pro 安装开始 ======"
    Log-Message "安装路径: $InstallPath"
    Log-Message "安装时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    Write-Host "  安装路径: " -NoNewline -ForegroundColor Gray
    Write-Host $InstallPath -ForegroundColor White
    Write-Host "  日志文件: " -NoNewline -ForegroundColor Gray
    Write-Host $Script:LOG_FILE -ForegroundColor White
    Write-Host ""

    if (-not $Silent) {
        if (-not (Confirm-Action "开始安装 CTMS Pro 临床试验管理系统？")) {
            Write-Host "  安装已取消。" -ForegroundColor Yellow
            exit 0
        }
    }

    # 执行安装步骤
    $steps = @(
        { Step-PreCheck },
        { Step-InstallDocker },
        { Step-ConfigureEnv },
        { Step-StartServices },
        { Step-InitDatabase },
        { Step-ConfigureFirewall },
        { Step-Verify }
    )

    $allOk = $true
    foreach ($step in $steps) {
        $result = & $step
        if ($result -eq $false) {
            $allOk = $false
            if (-not $Silent) {
                $cont = Confirm-Action "某步骤执行失败，是否继续安装？"
                if (-not $cont) { break }
            }
        }
    }

    # 创建快捷方式
    if ($allOk) {
        Create-Shortcuts
    }

    # 显示摘要
    Show-Summary

    Log-Message "====== CTMS Pro 安装结束 (错误: $($Script:ERRORS.Count), 警告: $($Script:WARNINGS.Count)) ======"

    if ($allOk -and $Script:ERRORS.Count -eq 0) {
        Write-Host ""
        Write-Host "  🎉 安装成功！正在打开浏览器..." -ForegroundColor Green
        Start-Sleep -Seconds 2
        Start-Process "http://localhost"
    }
}

# 执行主流程
Main
=======
#Requires -Version 5.1
<#
.SYNOPSIS
    CTMS Pro 临床试验管理系统 - Windows 一键安装脚本
.DESCRIPTION
    自动检测并安装所有依赖组件，初始化数据库，配置系统环境。
    支持: Windows 10/11, Windows Server 2016+
.NOTES
    版本: 1.0.0
    作者: CTMS Pro 部署工具
    要求: PowerShell 5.1+, 管理员权限（推荐）
#>

[CmdletBinding()]
param(
    [switch]$Silent,          # 静默安装（不询问）
    [switch]$SkipDocker,      # 跳过Docker安装
    [switch]$DevMode,         # 开发模式（不启动生产服务）
    [string]$InstallPath = "d:\workspace\CTMS_Pro",
    [string]$AdminEmail = "admin@ctms-pro.com",
    [string]$AdminPassword = "Admin@CTMS2026!"
)

# ====================================================================
# 全局变量
# ====================================================================
$Script:VERSION = "1.0.0"
$Script:LOG_FILE = "$InstallPath\install.log"
$Script:ERRORS = @()
$Script:WARNINGS = @()
$Script:INSTALL_PATH = $InstallPath

# 颜色方案
$colors = @{
    Success = "Green"
    Error   = "Red"
    Warning = "Yellow"
    Info    = "Cyan"
    Header  = "Magenta"
    Step    = "White"
}

# ====================================================================
# 工具函数
# ====================================================================
function Write-Banner {
    Clear-Host
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Magenta
    Write-Host "  ║         CTMS Pro 临床试验管理系统 安装程序               ║" -ForegroundColor Magenta
    Write-Host "  ║                   版本 $Script:VERSION                          ║" -ForegroundColor Magenta
    Write-Host "  ║         符合 GCP / FDA 21 CFR Part 11 / GDPR            ║" -ForegroundColor Magenta
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Magenta
    Write-Host ""
}

function Write-Step {
    param([int]$Number, [int]$Total, [string]$Message)
    Write-Host ""
    Write-Host "  [$Number/$Total] " -ForegroundColor Cyan -NoNewline
    Write-Host $Message -ForegroundColor White
    Write-Host "  " + ("─" * 58) -ForegroundColor DarkGray
}

function Write-OK    { param([string]$msg) Write-Host "  ✓ $msg" -ForegroundColor Green;  Log-Message "OK: $msg" }
function Write-FAIL  { param([string]$msg) Write-Host "  ✗ $msg" -ForegroundColor Red;    Log-Message "FAIL: $msg"; $Script:ERRORS += $msg }
function Write-WARN  { param([string]$msg) Write-Host "  ! $msg" -ForegroundColor Yellow; Log-Message "WARN: $msg"; $Script:WARNINGS += $msg }
function Write-INFO  { param([string]$msg) Write-Host "  · $msg" -ForegroundColor Cyan;   Log-Message "INFO: $msg" }
function Write-SUB   { param([string]$msg) Write-Host "    $msg" -ForegroundColor Gray }

function Log-Message {
    param([string]$msg)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp | $msg" | Add-Content -Path $Script:LOG_FILE -ErrorAction SilentlyContinue
}

function Test-Admin {
    $currentPrincipal = [Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()
    return $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Show-Progress {
    param([int]$Percent, [string]$Activity)
    Write-Progress -Activity $Activity -PercentComplete $Percent -Status "$Percent% 完成"
}

function Confirm-Action {
    param([string]$Message, [string]$Default = "Y")
    if ($Silent) { return $true }
    $choice = Read-Host "  $Message [Y/N] (默认: $Default)"
    if ([string]::IsNullOrEmpty($choice)) { $choice = $Default }
    return $choice -match "^[Yy]"
}

# ====================================================================
# 第1步：环境预检
# ====================================================================
function Step-PreCheck {
    Write-Step -Number 1 -Total 7 -Message "系统环境预检"

    # OS版本
    $os = Get-WmiObject -Class Win32_OperatingSystem
    $osVersion = $os.Version
    Write-INFO "操作系统: $($os.Caption) (Build $osVersion)"

    # 架构
    $arch = $env:PROCESSOR_ARCHITECTURE
    Write-INFO "处理器架构: $arch"
    if ($arch -ne "AMD64") {
        Write-WARN "检测到非x64架构，部分组件可能不兼容"
    }

    # 内存
    $ramGB = [Math]::Round($os.TotalVisibleMemorySize / 1MB, 1)
    Write-INFO "系统内存: ${ramGB} GB"
    if ($ramGB -lt 4) {
        Write-WARN "内存不足 4GB（推荐 8GB+），系统性能可能受限"
    } else {
        Write-OK "内存充足 (${ramGB} GB)"
    }

    # 磁盘空间
    $drive = Split-Path -Qualifier $InstallPath
    $disk = Get-PSDrive -Name ($drive.TrimEnd(':'))
    $freeGB = [Math]::Round($disk.Free / 1GB, 1)
    Write-INFO "安装目录可用空间: ${freeGB} GB"
    if ($freeGB -lt 10) {
        Write-WARN "磁盘可用空间不足 10GB，建议清理后再安装"
    } else {
        Write-OK "磁盘空间充足 (${freeGB} GB)"
    }

    # 管理员权限
    if (Test-Admin) {
        Write-OK "以管理员身份运行"
    } else {
        Write-WARN "未以管理员身份运行，部分功能（端口注册、服务安装）可能受限"
    }

    # PowerShell版本
    $psVersion = $PSVersionTable.PSVersion
    Write-INFO "PowerShell 版本: $psVersion"
    if ($psVersion.Major -lt 5) {
        Write-FAIL "需要 PowerShell 5.1 或更高版本"
        return $false
    }
    Write-OK "PowerShell 版本满足要求"

    # 网络连通性
    Write-INFO "检测网络连通性..."
    $netOk = Test-NetConnection -ComputerName "8.8.8.8" -Port 53 -WarningAction SilentlyContinue -ErrorAction SilentlyContinue
    if ($netOk.TcpTestSucceeded) {
        Write-OK "网络连接正常"
    } else {
        Write-WARN "网络连接异常，离线安装模式（需本地已有依赖）"
    }

    # 端口占用检测
    $portsToCheck = @(80, 443, 5432, 6379, 8000, 9000, 9001)
    $usedPorts = @()
    foreach ($port in $portsToCheck) {
        $conn = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
        if ($conn) { $usedPorts += $port }
    }
    if ($usedPorts.Count -gt 0) {
        Write-WARN "以下端口已被占用: $($usedPorts -join ', ')  ← 可能导致服务冲突"
    } else {
        Write-OK "所有必要端口（80/443/5432/6379/8000/9000）均可用"
    }

    return $true
}

# ====================================================================
# 第2步：安装 Docker Desktop
# ====================================================================
function Step-InstallDocker {
    Write-Step -Number 2 -Total 7 -Message "检测 / 安装 Docker"

    # 检查 Docker 是否已安装
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($dockerCmd) {
        $dockerVersion = docker version --format "{{.Server.Version}}" 2>$null
        if ($dockerVersion) {
            Write-OK "Docker 已安装 (版本 $dockerVersion)"

            # 检查 Docker Compose
            $composeVersion = docker compose version --short 2>$null
            if ($composeVersion) {
                Write-OK "Docker Compose 已安装 (版本 $composeVersion)"
            } else {
                Write-WARN "Docker Compose 未检测到，将尝试安装"
                Install-DockerCompose
            }
            return $true
        }
    }

    # Docker 未安装
    Write-INFO "Docker Desktop 未安装"

    if ($SkipDocker) {
        Write-WARN "已跳过 Docker 安装（-SkipDocker 参数）"
        Write-WARN "请手动安装 Docker Desktop: https://www.docker.com/products/docker-desktop"
        return $false
    }

    if (-not (Confirm-Action "是否自动下载并安装 Docker Desktop？（约 500MB）")) {
        Write-WARN "跳过 Docker 安装，请手动安装后重新运行此脚本"
        return $false
    }

    # 检查 WSL2（Docker Desktop 依赖）
    Write-INFO "检测 WSL2..."
    $wslStatus = wsl --status 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-INFO "安装 WSL2..."
        try {
            wsl --install --no-distribution 2>$null
            Write-OK "WSL2 安装成功（可能需要重启）"
        } catch {
            Write-WARN "WSL2 安装失败，Docker 将使用 Hyper-V 模式"
        }
    } else {
        Write-OK "WSL2 已就绪"
    }

    # 下载 Docker Desktop
    $dockerInstaller = "$env:TEMP\DockerDesktopInstaller.exe"
    $dockerUrl = "https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe"

    Write-INFO "正在下载 Docker Desktop..."
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($dockerUrl, $dockerInstaller)
        Write-OK "Docker Desktop 下载完成"
    } catch {
        Write-FAIL "Docker Desktop 下载失败: $($_.Exception.Message)"
        Write-INFO "请手动下载: $dockerUrl"
        return $false
    }

    # 安装 Docker Desktop
    Write-INFO "正在安装 Docker Desktop（静默模式）..."
    try {
        Start-Process -FilePath $dockerInstaller -ArgumentList "install", "--quiet", "--accept-license", "--no-windows-containers" -Wait
        Write-OK "Docker Desktop 安装完成"
        Write-WARN "请重启计算机后重新运行安装程序"
        return $false
    } catch {
        Write-FAIL "Docker Desktop 安装失败: $($_.Exception.Message)"
        return $false
    }
}

function Install-DockerCompose {
    Write-INFO "安装 Docker Compose Plugin..."
    try {
        $composeUrl = "https://github.com/docker/compose/releases/latest/download/docker-compose-windows-x86_64.exe"
        $composePath = "$env:ProgramFiles\Docker\cli-plugins\docker-compose.exe"
        New-Item -ItemType Directory -Force -Path (Split-Path $composePath) | Out-Null
        Invoke-WebRequest -Uri $composeUrl -OutFile $composePath -UseBasicParsing
        Write-OK "Docker Compose 安装完成"
    } catch {
        Write-WARN "Docker Compose 自动安装失败，请手动安装"
    }
}

# ====================================================================
# 第3步：配置环境变量
# ====================================================================
function Step-ConfigureEnv {
    Write-Step -Number 3 -Total 7 -Message "配置环境变量"

    $envFile = "$InstallPath\backend\.env"
    $envExample = "$InstallPath\backend\.env.example"

    if (-not (Test-Path $envExample)) {
        Write-FAIL ".env.example 文件不存在，请确认项目文件完整"
        return $false
    }

    # 生成随机密钥
    $secretKey = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 64 | ForEach-Object { [char]$_ })
    $fernet_key_bytes = New-Object byte[] 32
    [System.Security.Cryptography.RNGCryptoServiceProvider]::Create().GetBytes($fernet_key_bytes)
    $fernetKey = [Convert]::ToBase64String($fernet_key_bytes)

    if (Test-Path $envFile) {
        if (-not (Confirm-Action ".env 文件已存在，是否覆盖？")) {
            Write-OK "保留现有 .env 配置"
            return $true
        }
    }

    # 读取模板并替换
    $envContent = Get-Content $envExample -Raw
    $envContent = $envContent -replace "your-super-secret-key-change-in-production-min-32chars", $secretKey
    $envContent = $envContent -replace "APP_ENV=development", "APP_ENV=production"
    $envContent = $envContent -replace "DEBUG=True", "DEBUG=False"

    # 写入 .env
    Set-Content -Path $envFile -Value $envContent -Encoding UTF8
    Write-OK ".env 配置文件已生成"
    Write-SUB "位置: $envFile"

    # 生成 SECRET_KEY 到 docker-compose 环境
    [Environment]::SetEnvironmentVariable("CTMS_SECRET_KEY", $secretKey, "Process")
    Write-OK "SECRET_KEY 已随机生成 (64位)"

    # 显示重要配置
    Write-INFO "关键配置信息："
    Write-SUB "数据库密码: ctms_password_2026"
    Write-SUB "MinIO密码:  minioadmin123"
    Write-SUB "超管账号:   $AdminEmail"
    Write-SUB "超管密码:   $AdminPassword"
    Write-WARN "⚠ 生产环境请务必修改以上默认密码！"

    return $true
}

# ====================================================================
# 第4步：构建并启动 Docker 服务
# ====================================================================
function Step-StartServices {
    Write-Step -Number 4 -Total 7 -Message "构建并启动所有服务"

    Set-Location $InstallPath

    # 拉取基础镜像
    Write-INFO "拉取基础 Docker 镜像..."
    $images = @("postgres:15-alpine", "redis:7-alpine", "nginx:alpine")
    foreach ($img in $images) {
        Write-SUB "拉取 $img ..."
        docker pull $img --quiet 2>$null
    }

    # 构建后端镜像
    Write-INFO "构建 CTMS Pro 后端镜像（首次约需 3-5 分钟）..."
    $buildResult = docker compose build --no-cache 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-OK "后端镜像构建成功"
    } else {
        Write-FAIL "镜像构建失败"
        Write-SUB $buildResult
        return $false
    }

    # 启动服务（按依赖顺序）
    Write-INFO "启动数据库服务..."
    docker compose up -d postgres redis 2>$null
    Start-Sleep -Seconds 10

    # 等待 PostgreSQL 就绪
    Write-INFO "等待 PostgreSQL 初始化..."
    $retries = 0
    $maxRetries = 30
    while ($retries -lt $maxRetries) {
        $pgReady = docker exec ctms_postgres pg_isready -U ctms_user -d ctms_pro 2>$null
        if ($pgReady -match "accepting connections") {
            Write-OK "PostgreSQL 已就绪"
            break
        }
        $retries++
        Start-Sleep -Seconds 2
        Write-Progress -Activity "等待 PostgreSQL..." -PercentComplete (($retries / $maxRetries) * 100)
    }
    Write-Progress -Completed -Activity "等待 PostgreSQL..."

    if ($retries -ge $maxRetries) {
        Write-FAIL "PostgreSQL 启动超时（60秒），请检查日志"
        return $false
    }

    # 启动所有服务
    Write-INFO "启动全部服务..."
    docker compose up -d 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-OK "所有服务已启动"
    } else {
        Write-FAIL "服务启动失败，请查看日志：docker compose logs"
        return $false
    }

    return $true
}

# ====================================================================
# 第5步：初始化数据库
# ====================================================================
function Step-InitDatabase {
    Write-Step -Number 5 -Total 7 -Message "初始化数据库"

    # 等待后端就绪
    Write-INFO "等待后端 API 就绪..."
    $retries = 0
    $maxRetries = 30
    while ($retries -lt $maxRetries) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-OK "后端 API 已就绪"
                break
            }
        } catch { }
        $retries++
        Start-Sleep -Seconds 3
        Write-Progress -Activity "等待后端启动..." -PercentComplete (($retries / $maxRetries) * 100)
    }
    Write-Progress -Completed -Activity "等待后端启动..."

    if ($retries -ge $maxRetries) {
        Write-WARN "后端 API 未在预期时间内响应，数据库可能已通过 SQL 脚本初始化"
    }

    # 验证数据库表
    Write-INFO "验证数据库表结构..."
    $tableCheck = docker exec ctms_postgres psql -U ctms_user -d ctms_pro -c "\dt" 2>$null
    if ($tableCheck -match "users") {
        Write-OK "数据库表结构验证通过"
    } else {
        Write-INFO "手动执行数据库初始化脚本..."
        docker exec -i ctms_postgres psql -U ctms_user -d ctms_pro -f /docker-entrypoint-initdb.d/01_schema.sql 2>$null
        Write-OK "数据库初始化完成"
    }

    # 检查超管账号
    $userCheck = docker exec ctms_postgres psql -U ctms_user -d ctms_pro -t -c "SELECT COUNT(*) FROM users WHERE email='$AdminEmail';" 2>$null
    if ($userCheck -match "1") {
        Write-OK "超级管理员账号已存在: $AdminEmail"
    } else {
        Write-WARN "超管账号未找到，请登录后手动创建或通过 API 初始化"
    }

    return $true
}

# ====================================================================
# 第6步：配置 Windows 防火墙
# ====================================================================
function Step-ConfigureFirewall {
    Write-Step -Number 6 -Total 7 -Message "配置防火墙规则"

    if (-not (Test-Admin)) {
        Write-WARN "需要管理员权限配置防火墙，跳过此步骤"
        return $true
    }

    $rules = @(
        @{ Name = "CTMS Pro HTTP";       Port = 80;   Protocol = "TCP" },
        @{ Name = "CTMS Pro HTTPS";      Port = 443;  Protocol = "TCP" },
        @{ Name = "CTMS Pro API";        Port = 8000; Protocol = "TCP" },
        @{ Name = "CTMS Pro PostgreSQL"; Port = 5432; Protocol = "TCP" },
        @{ Name = "CTMS Pro MinIO";      Port = 9000; Protocol = "TCP" }
    )

    foreach ($rule in $rules) {
        $existing = Get-NetFirewallRule -DisplayName $rule.Name -ErrorAction SilentlyContinue
        if (-not $existing) {
            try {
                New-NetFirewallRule `
                    -DisplayName $rule.Name `
                    -Direction Inbound `
                    -Protocol $rule.Protocol `
                    -LocalPort $rule.Port `
                    -Action Allow `
                    -Profile Any `
                    -ErrorAction Stop | Out-Null
                Write-OK "防火墙规则: $($rule.Name) (端口 $($rule.Port))"
            } catch {
                Write-WARN "无法创建防火墙规则: $($rule.Name)"
            }
        } else {
            Write-OK "防火墙规则已存在: $($rule.Name)"
        }
    }

    return $true
}

# ====================================================================
# 第7步：安装验证与摘要
# ====================================================================
function Step-Verify {
    Write-Step -Number 7 -Total 7 -Message "安装验证"

    $checks = @()

    # 检查各服务状态
    $services = @("ctms_postgres", "ctms_redis", "ctms_backend", "ctms_nginx", "ctms_minio")
    foreach ($svc in $services) {
        $status = docker inspect --format='{{.State.Status}}' $svc 2>$null
        if ($status -eq "running") {
            Write-OK "服务运行中: $svc"
            $checks += $true
        } else {
            Write-FAIL "服务异常: $svc (状态: $status)"
            $checks += $false
        }
    }

    # HTTP 连通性测试
    $endpoints = @(
        @{ Url = "http://localhost";         Name = "前端首页" },
        @{ Url = "http://localhost:8000/health"; Name = "后端健康检查" },
        @{ Url = "http://localhost/api/v1/docs"; Name = "API文档" }
    )

    foreach ($ep in $endpoints) {
        try {
            $resp = Invoke-WebRequest -Uri $ep.Url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            Write-OK "$($ep.Name): $($ep.Url) → HTTP $($resp.StatusCode)"
            $checks += $true
        } catch {
            Write-WARN "$($ep.Name) 暂时不可访问（服务可能仍在启动中）: $($ep.Url)"
            $checks += $false
        }
    }

    return $true
}

# ====================================================================
# 创建快捷方式
# ====================================================================
function Create-Shortcuts {
    Write-INFO "创建桌面快捷方式..."

    $desktopPath = [Environment]::GetFolderPath("Desktop")

    # CTMS Pro 系统入口
    $shell = New-Object -ComObject WScript.Shell
    $shortcut = $shell.CreateShortcut("$desktopPath\CTMS Pro.url")
    $shortcut.TargetPath = "http://localhost"
    $shortcut.Save()
    Write-OK "桌面快捷方式已创建: CTMS Pro"

    # API 文档
    $shortcut2 = $shell.CreateShortcut("$desktopPath\CTMS Pro API文档.url")
    $shortcut2.TargetPath = "http://localhost/api/v1/docs"
    $shortcut2.Save()
    Write-OK "桌面快捷方式已创建: CTMS Pro API文档"
}

# ====================================================================
# 打印安装摘要
# ====================================================================
function Show-Summary {
    Write-Host ""
    Write-Host "  ╔══════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "  ║              CTMS Pro 安装完成！                         ║" -ForegroundColor Green
    Write-Host "  ╠══════════════════════════════════════════════════════════╣" -ForegroundColor Green
    Write-Host "  ║  访问地址                                                ║" -ForegroundColor Green
    Write-Host "  ║  · 系统入口:    http://localhost                         ║" -ForegroundColor White
    Write-Host "  ║  · API 文档:    http://localhost/api/v1/docs             ║" -ForegroundColor White
    Write-Host "  ║  · MinIO 控制台: http://localhost:9001                   ║" -ForegroundColor White
    Write-Host "  ║                                                          ║" -ForegroundColor Green
    Write-Host "  ║  默认账号                                                ║" -ForegroundColor Green
    Write-Host "  ║  · 邮箱: admin@ctms-pro.com                             ║" -ForegroundColor White
    Write-Host "  ║  · 密码: Admin@CTMS2026!                                ║" -ForegroundColor White
    Write-Host "  ║                                                          ║" -ForegroundColor Green
    Write-Host "  ║  管理命令                                                ║" -ForegroundColor Green
    Write-Host "  ║  · 启动: start.bat                                       ║" -ForegroundColor White
    Write-Host "  ║  · 停止: stop.bat                                        ║" -ForegroundColor White
    Write-Host "  ║  · 日志: docker compose logs -f                         ║" -ForegroundColor White
    Write-Host "  ╚══════════════════════════════════════════════════════════╝" -ForegroundColor Green
    Write-Host ""

    if ($Script:WARNINGS.Count -gt 0) {
        Write-Host "  ⚠ 安装警告（$($Script:WARNINGS.Count) 条）：" -ForegroundColor Yellow
        foreach ($w in $Script:WARNINGS) {
            Write-Host "    · $w" -ForegroundColor Yellow
        }
    }

    if ($Script:ERRORS.Count -gt 0) {
        Write-Host ""
        Write-Host "  ✗ 安装错误（$($Script:ERRORS.Count) 条）：" -ForegroundColor Red
        foreach ($e in $Script:ERRORS) {
            Write-Host "    · $e" -ForegroundColor Red
        }
        Write-Host ""
        Write-Host "  详细日志: $Script:LOG_FILE" -ForegroundColor Gray
    }
}

# ====================================================================
# 主流程
# ====================================================================
function Main {
    Write-Banner

    # 初始化日志
    New-Item -ItemType Directory -Force -Path (Split-Path $Script:LOG_FILE) | Out-Null
    Log-Message "====== CTMS Pro 安装开始 ======"
    Log-Message "安装路径: $InstallPath"
    Log-Message "安装时间: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

    Write-Host "  安装路径: " -NoNewline -ForegroundColor Gray
    Write-Host $InstallPath -ForegroundColor White
    Write-Host "  日志文件: " -NoNewline -ForegroundColor Gray
    Write-Host $Script:LOG_FILE -ForegroundColor White
    Write-Host ""

    if (-not $Silent) {
        if (-not (Confirm-Action "开始安装 CTMS Pro 临床试验管理系统？")) {
            Write-Host "  安装已取消。" -ForegroundColor Yellow
            exit 0
        }
    }

    # 执行安装步骤
    $steps = @(
        { Step-PreCheck },
        { Step-InstallDocker },
        { Step-ConfigureEnv },
        { Step-StartServices },
        { Step-InitDatabase },
        { Step-ConfigureFirewall },
        { Step-Verify }
    )

    $allOk = $true
    foreach ($step in $steps) {
        $result = & $step
        if ($result -eq $false) {
            $allOk = $false
            if (-not $Silent) {
                $cont = Confirm-Action "某步骤执行失败，是否继续安装？"
                if (-not $cont) { break }
            }
        }
    }

    # 创建快捷方式
    if ($allOk) {
        Create-Shortcuts
    }

    # 显示摘要
    Show-Summary

    Log-Message "====== CTMS Pro 安装结束 (错误: $($Script:ERRORS.Count), 警告: $($Script:WARNINGS.Count)) ======"

    if ($allOk -and $Script:ERRORS.Count -eq 0) {
        Write-Host ""
        Write-Host "  🎉 安装成功！正在打开浏览器..." -ForegroundColor Green
        Start-Sleep -Seconds 2
        Start-Process "http://localhost"
    }
}

# 执行主流程
Main
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
