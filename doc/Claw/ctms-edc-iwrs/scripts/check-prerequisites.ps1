# CTMS+EDC+IWRS 环境检查脚本（PowerShell 版）
# 用于 Windows 系统检查所有前置软件是否已正确安装

$ErrorActionPreference = "Stop"

# 颜色辅助函数
function Write-Green {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Green
}

function Write-Red {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Red
}

function Write-Yellow {
    param([string]$Message)
    Write-Host $Message -ForegroundColor Yellow
}

Write-Host "=================================="
Write-Host "CTMS+EDC+IWRS 环境检查"
Write-Host "=================================="
Write-Host ""

# 检查 Git
Write-Host "📦 检查 Git..."
try {
    $gitVersion = git --version
    if ($LASTEXITCODE -eq 0) {
        $versionNumber = $gitVersion -match '(\d+\.\d+\.\d+)') ? $Matches[1] : "unknown"
        Write-Green "✓ Git 已安装：$versionNumber"
        
        # 检查版本（要求≥2.30）
        $majorVersion = [int]($versionNumber.Split('.')[0])
        $minorVersion = [int]($versionNumber.Split('.')[1])
        if ($majorVersion -gt 2 -or ($majorVersion -eq 2 -and $minorVersion -ge 30)) {
            Write-Green "  ✓ 版本满足要求 (≥2.30)"
        } else {
            Write-Yellow "  ⚠ 版本较低，建议升级到 2.30 或以上"
        }
        $gitInstalled = $true
    }
} catch {
    Write-Red "✗ Git 未安装"
    Write-Host "  请访问 https://git-scm.com/downloads 下载安装"
    $gitInstalled = $false
}
Write-Host ""

# 检查 Node.js
Write-Host "📦 检查 Node.js..."
try {
    $nodeVersion = node -v
    if ($LASTEXITCODE -eq 0) {
        $versionNumber = $nodeVersion.TrimStart('v')
        Write-Green "✓ Node.js 已安装：v$versionNumber"
        
        $majorVersion = [int]($versionNumber.Split('.')[0])
        if ($majorVersion -ge 20) {
            Write-Green "  ✓ 版本满足要求 (≥20.x)"
        } else {
            Write-Yellow "  ⚠ 版本较低，建议升级到 Node.js 20 或以上"
        }
        $nodeInstalled = $true
    }
} catch {
    Write-Red "✗ Node.js 未安装"
    Write-Host "  请访问 https://nodejs.org/ 下载安装"
    $nodeInstalled = $false
}
Write-Host ""

# 检查 npm
Write-Host "📦 检查 npm..."
try {
    $npmVersion = npm -v
    if ($LASTEXITCODE -eq 0) {
        Write-Green "✓ npm 已安装：v$npmVersion"
        $npmInstalled = $true
    }
} catch {
    Write-Red "✗ npm 未安装"
    $npmInstalled = $false
}
Write-Host ""

# 检查 Docker
Write-Host "📦 检查 Docker..."
try {
    $dockerVersion = docker --version
    if ($LASTEXITCODE -eq 0) {
        $versionNumber = $dockerVersion -replace '.*\s([\d\.]+).*', '$1'
        Write-Green "✓ Docker 已安装：$versionNumber"
        
        # 检查 Docker 是否运行
        try {
            docker ps > $null
            Write-Green "  ✓ Docker 服务正在运行"
            $dockerInstalled = $true
        } catch {
            Write-Yellow "  ⚠ Docker 服务未运行，请启动 Docker Desktop"
            $dockerInstalled = $false
        }
    }
} catch {
    Write-Red "✗ Docker 未安装"
    Write-Host "  请访问 https://www.docker.com/products/docker-desktop 下载安装"
    $dockerInstalled = $false
}
Write-Host ""

# 检查 Docker Compose
Write-Host "📦 检查 Docker Compose..."
$composeInstalled = $false
try {
    $composeVersion = docker-compose --version
    if ($LASTEXITCODE -eq 0) {
        $versionNumber = $composeVersion -replace '.*\s+v?([\d\.]+).*', '$1'
        Write-Green "✓ Docker Compose 已安装 (v1): v$versionNumber"
        $composeInstalled = $true
    }
} catch {
    try {
        $composeVersion = docker compose version --short
        if ($LASTEXITCODE -eq 0) {
            $versionNumber = $composeVersion.Trim()
            Write-Green "✓ Docker Compose 已安装 (v2): $versionNumber"
            $composeInstalled = $true
        }
    } catch {
        Write-Red "✗ Docker Compose 未安装"
        Write-Host "  Docker Compose 通常随 Docker Desktop 一起安装"
        $composeInstalled = $false
    }
}
Write-Host ""

# 总结
Write-Host "=================================="
Write-Host "检查总结"
Write-Host "=================================="

$allInstalled = $true

if ($gitInstalled) {
    Write-Green "✓ Git 就绪"
} else {
    Write-Red "✗ Git 未安装"
    $allInstalled = $false
}

if ($nodeInstalled) {
    Write-Green "✓ Node.js 就绪"
} else {
    Write-Red "✗ Node.js 未安装"
    $allInstalled = $false
}

if ($npmInstalled) {
    Write-Green "✓ npm 就绪"
} else {
    Write-Red "✗ npm 未安装"
    $allInstalled = $false
}

if ($dockerInstalled) {
    Write-Green "✓ Docker 就绪"
} else {
    Write-Red "✗ Docker 未安装或未运行"
    $allInstalled = $false
}

if ($composeInstalled) {
    Write-Green "✓ Docker Compose 就绪"
} else {
    Write-Red "✗ Docker Compose 未安装"
    $allInstalled = $false
}

Write-Host ""

if ($allInstalled) {
    Write-Green "🎉 所有前置软件已安装！"
    Write-Host ""
    Write-Host "下一步:"
    Write-Host "  1. 复制 .env.example 为 .env 并配置"
    Write-Host "  2. 运行 'docker-compose up -d' 启动所有服务"
    Write-Host "  3. 访问 http://localhost:5173 查看前端"
} else {
    Write-Red "❌ 缺少必要软件，请先安装上述标记为✗的组件"
    Write-Host ""
    Write-Host "安装指南:"
    Write-Host "  - Git: https://git-scm.com/downloads"
    Write-Host "  - Node.js: https://nodejs.org/"
    Write-Host "  - Docker Desktop: https://www.docker.com/products/docker-desktop"
}
