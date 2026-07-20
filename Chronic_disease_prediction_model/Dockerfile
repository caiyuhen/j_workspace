FROM python:3.10-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
<<<<<<< HEAD
RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple --no-cache-dir -r requirements.txt
=======
RUN pip install --no-cache-dir -r requirements.txt
>>>>>>> origin/main
COPY . .
EXPOSE 5008
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5008", "api.app:app"]
