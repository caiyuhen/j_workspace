# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Switch to Aliyun Mirror for APT (fix for China/Slow Network)
# Handles both old sources.list and new debian.sources formats
RUN if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list.d/debian.sources; \
    else \
        sed -i 's/deb.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list; \
        sed -i 's/security.debian.org/mirrors.ustc.edu.cn/g' /etc/apt/sources.list; \
    fi

# Install system dependencies required for OpenCV
<<<<<<< HEAD
# Changed libgl1-mesa-glx to libgl1 to fix missing package issue on newer Debian versions
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    libgl1 \
=======
# Added --fix-missing to handle potential transient network issues
RUN apt-get update --fix-missing && apt-get install -y --no-install-recommends \
    libgl1-mesa-glx \
>>>>>>> origin/main
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# Use Aliyun PyPI mirror
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# Copy the current directory contents into the container at /app
COPY . .

# Expose port 9080 to the outside world
EXPOSE 9080

# Define environment variable
ENV PYTHONUNBUFFERED=1

# Run main.py when the container launches
CMD ["python", "main.py"]
