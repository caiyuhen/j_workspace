#!/bin/bash
# 部署脚本

echo "开始部署临床试验管理系统..."

# 设置环境变量
export NODE_ENV=production

# 进入项目根目录
cd /app/smartDr

# 安装依赖
echo "安装依赖..."
cd backend/auth-service && npm install --production && cd ../..
cd backend/ctms-service && npm install --production && cd ../..
cd backend/edc-service && npm install --production && cd ../..
cd backend/iwrs-service && npm install --production && cd ../..
cd backend/patient-folder-service && npm install --production && cd ../..
cd backend/api-gateway && npm install --production && cd ../..

# 初始化数据库
echo "初始化数据库..."
psql -U postgres -d clinical_trials_db -f database/init.sql

# 启动服务
echo "启动服务..."

# 启动认证服务
cd backend/auth-service
npm start &
AUTH_PID=$!

# 启动CTMS服务
cd ../ctms-service
npm start &
CTMS_PID=$!

# 启动EDC服务
cd ../edc-service
npm start &
EDC_PID=$!

# 启动IWRS服务
cd ../iwrs-service
npm start &
IWRS_PID=$!

# 启动病历夹服务
cd ../patient-folder-service
npm start &
PATIENT_FOLDER_PID=$!

# 启动API网关
cd ../api-gateway
npm start &
API_GATEWAY_PID=$!

echo "所有服务已启动"
echo "认证服务 PID: $AUTH_PID"
echo "CTMS服务 PID: $CTMS_PID"
echo "EDC服务 PID: $EDC_PID"
echo "IWRS服务 PID: $IWRS_PID"
echo "病历夹服务 PID: $PATIENT_FOLDER_PID"
echo "API网关 PID: $API_GATEWAY_PID"

# 等待服务启动
sleep 5

# 检查服务状态
echo "检查服务状态..."
for pid in $AUTH_PID $CTMS_PID $EDC_PID $IWRS_PID $PATIENT_FOLDER_PID $API_GATEWAY_PID; do
    if ps -p $pid > /dev/null; then
        echo "服务 PID $pid 运行正常"
    else
        echo "服务 PID $pid 启动失败"
    fi
done

echo "部署完成！"