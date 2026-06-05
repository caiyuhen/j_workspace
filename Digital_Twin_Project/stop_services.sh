#!/bin/bash

# 脊柱数字孪生服务 - 停止脚本

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}正在停止脊柱数字孪生微服务...${NC}"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_DIR="$SCRIPT_DIR/logs"

# 停止函数
stop_service() {
    SERVICE_NAME=$1
    PID_FILE="$LOG_DIR/${SERVICE_NAME}.pid"
    
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p $PID > /dev/null; then
            echo "正在停止 $SERVICE_NAME (PID: $PID)..."
            kill $PID
            rm "$PID_FILE"
        else
            echo "$SERVICE_NAME (PID: $PID) 未运行，清理 PID 文件。"
            rm "$PID_FILE"
        fi
    else
        echo "未找到 $SERVICE_NAME 的 PID 文件。"
    fi
}

stop_service "report-gateway"
stop_service "visualization-service"
stop_service "simulation-service"
stop_service "patient-service"
stop_service "ocr-service"

echo -e "${GREEN}所有服务已停止。${NC}"
