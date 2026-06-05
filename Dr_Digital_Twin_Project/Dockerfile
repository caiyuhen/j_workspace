FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_ENDPOINT="https://hf-mirror.com" \
    PYTHONPATH=/app

# 安装系统依赖 (如果有需要，可根据模型或库的需求添加，例如 ffmpeg, libsm6, libxext6 等)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖列表并安装
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制项目代码
COPY . /app/

# 暴露 FastAPI 运行端口
EXPOSE 8123

# 启动后端服务
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8123", "--workers", "1"]
