#!/bin/bash

# start_services_alt_ports.sh
# 脊柱数字孪生项目 - Linux/macOS 一键启动脚本 (9000-9005 端口段)

echo "Starting Spine Digital Twin Microservices on alt ports (9000-9005)..."

# 获取当前脚本所在目录的绝对路径
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"

# 创建 logs 目录用于存放各服务的输出日志
mkdir -p "$PROJECT_ROOT/logs"

# 函数：在后台启动服务并将日志重定向到文件
start_service() {
    local SERVICE_DIR=$1
    local COMMAND=$2
    local LOG_FILE=$3

    echo "Starting $SERVICE_DIR..."
    cd "$PROJECT_ROOT/services/$SERVICE_DIR/src" || exit 1
    
    # 使用 nohup 在后台运行，并将 PID 存入文件以便后续关闭
    nohup $COMMAND > "$PROJECT_ROOT/logs/$LOG_FILE.log" 2>&1 &
    echo $! > "$PROJECT_ROOT/logs/$LOG_FILE.pid"
}

# 1. 启动基础支撑服务
start_service "patient-service" "python -m uvicorn main:app --host 127.0.0.1 --port 9003 --reload" "patient"
start_service "simulation-service" "python -m uvicorn main:app --host 127.0.0.1 --port 9001 --reload" "simulation"
start_service "visualization-service" "python -m uvicorn main:app --host 127.0.0.1 --port 9002 --reload" "visualization"
start_service "ocr-service" "python -m uvicorn main:app --host 127.0.0.1 --port 9004 --reload" "ocr"
start_service "xray-analysis-service" "python -m uvicorn main:app --host 127.0.0.1 --port 9005 --reload" "xray"

# 2. 启动网关服务 (带环境变量注入)
echo "Starting report-gateway..."
cd "$PROJECT_ROOT/services/report-gateway/src" || exit 1
export PATIENT_SERVICE_URL="http://127.0.0.1:9003"
export SIMULATION_SERVICE_URL="http://127.0.0.1:9001"
export VISUALIZATION_SERVICE_URL="http://127.0.0.1:9002"
export OCR_SERVICE_URL="http://127.0.0.1:9004"
export XRAY_SERVICE_URL="http://127.0.0.1:9005"
nohup python -m uvicorn main:app --host 127.0.0.1 --port 9000 --reload > "$PROJECT_ROOT/logs/gateway.log" 2>&1 &
echo $! > "$PROJECT_ROOT/logs/gateway.pid"

echo ""
echo "========================================================"
echo "Alt-port services started in background."
echo "Frontend URL: http://127.0.0.1:9000/"
echo "Gateway health: http://127.0.0.1:9000/health"
echo "Smoke test: python ./run_multimodal_smoke_checks.py"
echo "Logs are available in $PROJECT_ROOT/logs/"
echo "========================================================"
echo "To stop all services, you can run: ./stop_services_alt_ports.sh"
