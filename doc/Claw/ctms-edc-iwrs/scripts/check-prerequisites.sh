#!/bin/bash

# CTMS+EDC+IWRS 平台 - 环境检查脚本
# 用于检查所有前置软件是否已正确安装

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=================================="
echo "CTMS+EDC+IWRS 环境检查"
echo "=================================="
echo ""

# 检查 Git
echo "📦 检查 Git..."
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    echo -e "${GREEN}✓ Git 已安装：${GIT_VERSION}${NC}"
    
    # 检查版本（要求≥2.30）
    if [ "$(echo "$GIT_VERSION" | awk -F. '{print $1.$2}')" -ge 230 ]; then
        echo -e "${GREEN}  ✓ 版本满足要求 (≥2.30)${NC}"
    else
        echo -e "${YELLOW}  ⚠ 版本较低，建议升级到 2.30 或以上${NC}"
    fi
else
    echo -e "${RED}✗ Git 未安装${NC}"
    echo "  请访问 https://git-scm.com/downloads 下载安装"
    GIT_INSTALLED=false
fi
echo ""

# 检查 Node.js
echo "📦 检查 Node.js..."
if command -v node &> /dev/null; then
    NODE_VERSION=$(node -v | sed 's/v//')
    NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d. -f1)
    echo -e "${GREEN}✓ Node.js 已安装：v${NODE_VERSION}${NC}"
    
    if [ "$NODE_MAJOR" -ge 20 ]; then
        echo -e "${GREEN}  ✓ 版本满足要求 (≥20.x)${NC}"
    else
        echo -e "${YELLOW}  ⚠ 版本较低，建议升级到 Node.js 20 或以上${NC}"
    fi
else
    echo -e "${RED}✗ Node.js 未安装${NC}"
    echo "  请访问 https://nodejs.org/ 下载安装"
    NODE_INSTALLED=false
fi
echo ""

# 检查 npm
echo "📦 检查 npm..."
if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm -v)
    echo -e "${GREEN}✓ npm 已安装：v${NPM_VERSION}${NC}"
else
    echo -e "${RED}✗ npm 未安装${NC}"
    NPM_INSTALLED=false
fi
echo ""

# 检查 Docker
echo "📦 检查 Docker..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    echo -e "${GREEN}✓ Docker 已安装：${DOCKER_VERSION}${NC}"
    
    # 检查 Docker 是否运行
    if docker ps &> /dev/null; then
        echo -e "${GREEN}  ✓ Docker 服务正在运行${NC}"
    else
        echo -e "${YELLOW}  ⚠ Docker 服务未运行，请启动 Docker Desktop${NC}"
    fi
else
    echo -e "${RED}✗ Docker 未安装${NC}"
    echo "  请访问 https://www.docker.com/products/docker-desktop 下载安装"
    DOCKER_INSTALLED=false
fi
echo ""

# 检查 Docker Compose
echo "📦 检查 Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version | awk '{print $3}' | sed 's/,//')
    echo -e "${GREEN}✓ Docker Compose 已安装：v${COMPOSE_VERSION}${NC}"
elif docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short | cut -d' ' -f2)
    echo -e "${GREEN}✓ Docker Compose 已安装 (v2): ${COMPOSE_VERSION}${NC}"
    COMPOSE_V2=true
else
    echo -e "${RED}✗ Docker Compose 未安装${NC}"
    echo "  Docker Compose 通常随 Docker Desktop 一起安装"
    COMPOSE_INSTALLED=false
fi
echo ""

# 检查 psql（PostgreSQL 客户端，可选）
echo "📦 检查 PostgreSQL 客户端（可选）..."
if command -v psql &> /dev/null; then
    PSQL_VERSION=$(psql --version | awk '{print $2}')
    echo -e "${GREEN}✓ psql 已安装：${PSQL_VERSION}${NC}"
else
    echo -e "${YELLOW}⚠ psql 未安装（可选，用于直接操作数据库）${NC}"
fi
echo ""

# 总结
echo "=================================="
echo "检查总结"
echo "=================================="

ALL_INSTALLED=true

if [ "${GIT_INSTALLED:-true}" = false ]; then
    ALL_INSTALLED=false
    echo -e "${RED}✗ Git 未安装${NC}"
else
    echo -e "${GREEN}✓ Git 就绪${NC}"
fi

if [ "${NODE_INSTALLED:-true}" = false ]; then
    ALL_INSTALLED=false
    echo -e "${RED}✗ Node.js 未安装${NC}"
else
    echo -e "${GREEN}✓ Node.js 就绪${NC}"
fi

if [ "${NPM_INSTALLED:-true}" = false ]; then
    ALL_INSTALLED=false
    echo -e "${RED}✗ npm 未安装${NC}"
else
    echo -e "${GREEN}✓ npm 就绪${NC}"
fi

if [ "${DOCKER_INSTALLED:-true}" = false ]; then
    ALL_INSTALLED=false
    echo -e "${RED}✗ Docker 未安装${NC}"
else
    echo -e "${GREEN}✓ Docker 就绪${NC}"
fi

if [ "${COMPOSE_INSTALLED:-true}" = false ]; then
    ALL_INSTALLED=false
    echo -e "${RED}✗ Docker Compose 未安装${NC}"
else
    echo -e "${GREEN}✓ Docker Compose 就绪${NC}"
fi

echo ""

if [ "$ALL_INSTALLED" = true ]; then
    echo -e "${GREEN}🎉 所有前置软件已安装！${NC}"
    echo ""
    echo "下一步:"
    echo "  1. 复制 .env.example 为 .env 并配置"
    echo "  2. 运行 'docker-compose up -d' 启动所有服务"
    echo "  3. 访问 http://localhost:5173 查看前端"
    exit 0
else
    echo -e "${RED}❌ 缺少必要软件，请先安装上述标记为✗的组件${NC}"
    echo ""
    echo "安装指南:"
    echo "  - Git: https://git-scm.com/downloads"
    echo "  - Node.js: https://nodejs.org/"
    echo "  - Docker Desktop: https://www.docker.com/products/docker-desktop"
    exit 1
fi
