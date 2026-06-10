#!/bin/bash

# stop_services_alt_ports.sh
# 脊柱数字孪生项目 - Linux/macOS 一键停止脚本

echo "Stopping Spine Digital Twin Microservices..."

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
LOG_DIR="$PROJECT_ROOT/logs"

if [ -d "$LOG_DIR" ]; then
    for pid_file in "$LOG_DIR"/*.pid; do
        if [ -f "$pid_file" ]; then
            PID=$(cat "$pid_file")
            echo "Killing process $PID (from $(basename "$pid_file"))..."
            kill "$PID" 2>/dev/null
            rm "$pid_file"
        fi
    done
    echo "All known background services have been stopped."
else
    echo "No PID files found in $LOG_DIR. Services might not be running or were started differently."
fi
