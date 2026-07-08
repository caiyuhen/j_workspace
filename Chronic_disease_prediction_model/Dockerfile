FROM python:3.10-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5008
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5008", "api.app:app"]
