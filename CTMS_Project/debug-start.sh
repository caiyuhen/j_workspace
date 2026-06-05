#!/bin/bash
# 调试启动脚本 - 用于启动CTMS/EDC系统

echo "正在启动CTMS/EDC系统调试环境..."

# 启动后端服务
echo "启动后端服务..."
cd server
npm run dev &

# 等待后端服务启动
sleep 5

# 启动前端服务
echo "启动前端服务..."
cd ../client
npm run dev &

echo "调试环境启动完成！"
echo "后端服务: http://localhost:3666"
echo "前端服务: http://localhost:5779"