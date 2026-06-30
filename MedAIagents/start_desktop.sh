#!/bin/bash
# ============================================================
# 🏥 MedAIagents - 医学 AI 助手 桌面版 (Linux/Mac)
# ============================================================

echo "============================================================"
echo "🏥 MedAIagents - 医学 AI 助手 桌面版"
echo "============================================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "❌ 未检测到 Python 3，请先安装 Python 3.9+"
    exit 1
fi

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查是否已安装依赖
echo "🔍 检查依赖..."
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 正在安装依赖..."
    pip3 install -r requirements.txt
fi

echo ""
echo "🚀 启动桌面应用..."
echo ""

# 启动桌面应用
python3 -m medai.desktop.app

echo ""
echo "👋 感谢使用 MedAIagents"
