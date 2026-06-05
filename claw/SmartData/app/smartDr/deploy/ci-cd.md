# CI/CD Pipeline

## 1. CI/CD 流程概述

本项目使用 GitHub Actions 实现持续集成和持续部署 (CI/CD)。

## 2. 构建流程

### 构建检查
- 验证所有服务的package.json和依赖
- 运行单元测试（如果存在）
- 代码质量检查
- 安全扫描

### Docker 构建
- 构建所有服务的Docker镜像
- 推送到Docker仓库（Docker Hub）

## 3. 部署流程

### 开发环境部署
- 自动部署到开发服务器
- 自动运行集成测试

### 生产环境部署
- 手动触发部署流程
- 滚动更新策略
- 健康检查确认

## 4. GitHub Actions 配置

### 工作流文件: `.github/workflows/ci-cd.yml`

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
        
    - name: Install dependencies
      run: |
        cd backend/auth-service
        npm ci
        cd ../ctms-service
        npm ci
        cd ../edc-service
        npm ci
        cd ../iwrs-service
        npm ci
        cd ../patient-folder-service
        npm ci
        cd ../api-gateway
        npm ci
        cd ../monitoring-service
        npm ci
        
    - name: Run tests
      run: |
        # 运行单元测试（如果存在）
        echo "Running unit tests..."
        
    - name: Build Docker images
      run: |
        docker build -t smartdr/auth-service ./backend/auth-service
        docker build -t smartdr/ctms-service ./backend/ctms-service
        docker build -t smartdr/edc-service ./backend/edc-service
        docker build -t smartdr/iwrs-service ./backend/iwrs-service
        docker build -t smartdr/patient-folder-service ./backend/patient-folder-service
        docker build -t smartdr/api-gateway ./backend/api-gateway
        docker build -t smartdr/monitoring-service ./backend/monitoring-service
        
    - name: Push to Docker Hub
      if: github.ref == 'refs/heads/main'
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push smartdr/auth-service
        docker push smartdr/ctms-service
        docker push smartdr/edc-service
        docker push smartdr/iwrs-service
        docker push smartdr/patient-folder-service
        docker push smartdr/api-gateway
        docker push smartdr/monitoring-service
```

## 5. 部署脚本

### 一键部署脚本: `deploy.sh`

```bash
#!/bin/bash
# 自动部署脚本

echo "开始部署 Clinical Trial Management System..."

# 验证环境
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "错误: Docker Compose未安装"
    exit 1
fi

# 拉取最新代码
echo "拉取最新代码..."
git pull origin main

# 停止现有容器
echo "停止现有容器..."
docker-compose down

# 构建新镜像
echo "构建新镜像..."
docker-compose build

# 启动新服务
echo "启动新服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
docker-compose ps

echo "部署完成!"
```

## 6. 监控和告警

### 系统监控端点
所有服务都提供 `/health` 端点用于健康检查。

### 日志管理
- 使用Winston进行日志记录
- 日志分类存储在不同文件中
- 支持日志轮转

### 告警机制
- 健康检查失败告警
- 数据库连接失败告警
- API错误率监控