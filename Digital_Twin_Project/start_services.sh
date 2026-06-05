#!/bin/bash

# 脊柱数字孪生服务 - Linux/macOS 一键启动脚本

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}正在启动脊柱数字孪生微服务...${NC}"

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到 Python3。请先安装 Python3。${NC}"
    exit 1
fi

# 获取脚本所在目录的绝对路径
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR"

# 创建日志目录
LOG_DIR="$PROJECT_ROOT/logs"
mkdir -p "$LOG_DIR"

# 启动函数
start_service() {
    SERVICE_NAME=$1
    SERVICE_DIR=$2
    PORT=$3
    
    echo -e "正在启动 ${GREEN}$SERVICE_NAME${NC} (端口 $PORT)..."
    
    cd "$PROJECT_ROOT/$SERVICE_DIR/src" || exit
    
    # 检查依赖 (可选，为了速度可以注释掉)
    # pip install -r ../requirements.txt > "$LOG_DIR/${SERVICE_NAME}_install.log" 2>&1
    
    # 后台启动
    nohup uvicorn main:app --host 0.0.0.0 --port $PORT --reload > "$LOG_DIR/${SERVICE_NAME}.log" 2>&1 &
    PID=$!
    echo $PID > "$LOG_DIR/${SERVICE_NAME}.pid"
    echo -e "${SERVICE_NAME} PID: $PID"
}

# 1. 启动 OCR 服务
start_service "ocr-service" "services/ocr-service" 8004

# 2. 启动患者服务
start_service "patient-service" "services/patient-service" 8003

# 3. 启动模拟服务
start_service "simulation-service" "services/simulation-service" 8001

# 4. 启动可视化服务
start_service "visualization-service" "services/visualization-service" 8002

# 5. 启动报告网关
start_service "report-gateway" "services/report-gateway" 8000

echo -e "${GREEN}所有服务已在后台启动!${NC}"
echo -e "日志文件位于: $LOG_DIR"
echo -e "要停止服务，请运行: ./stop_services.sh"
