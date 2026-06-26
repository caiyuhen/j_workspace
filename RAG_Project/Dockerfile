FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip config set global.index-url https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/
RUN pip install --no-cache-dir --default-timeout=1000 -r requirements.txt

COPY . .

# Expose port
EXPOSE 8001

CMD ["python", "server.py"]
