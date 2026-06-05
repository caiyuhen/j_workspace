## Docker Deployment / Docker 部署

### 1. Build Image / 构建镜像

```bash
docker build -t ocr-microservice:latest .
```
Or run `build_docker.bat` (Windows).
或者运行 `build_docker.bat` (Windows)。

### 2. Run Container / 运行容器

```bash
docker run -d -p 9080:9080 --name ocr-service -v %cd%/output:/app/output ocr-microservice:latest
```
Or run `run_docker.bat` (Windows).
或者运行 `run_docker.bat` (Windows)。

*Note: The `-v` flag mounts the local `output` directory to persist results.*
*注意：`-v` 参数用于挂载本地 `output` 目录以持久化保存结果。*

### 3. Linux Deployment / Linux 部署

For Linux servers, you can use the provided shell script `deploy.sh` or `docker-compose.yml`.
对于 Linux 服务器，您可以使用提供的 `deploy.sh` 脚本或 `docker-compose.yml`。

#### Option A: Using deploy.sh (Recommended) / 方案 A：使用 deploy.sh（推荐）

The `deploy.sh` script automatically detects your Docker environment (docker-compose, docker compose plugin, or raw docker) and handles the deployment process.
`deploy.sh` 脚本会自动检测您的 Docker 环境（docker-compose、docker compose 插件或原生 docker）并处理部署流程。

1.  Make the script executable / 赋予脚本执行权限:
    ```bash
    chmod +x deploy.sh
    ```

2.  Run the deployment script / 运行部署脚本:
    ```bash
    ./deploy.sh
    ```

#### Option B: Using Docker Compose / 方案 B：使用 Docker Compose

If you prefer standard tools, use the provided `docker-compose.yml`.
如果您更喜欢使用标准工具，可以使用提供的 `docker-compose.yml`。

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  ocr-service:
    build: .
    image: ocr-microservice:latest
    container_name: ocr-service
    ports:
      - "9080:9080"
    volumes:
      - ./output:/app/output
    restart: always
    environment:
      - PYTHONUNBUFFERED=1
```

1.  Start services / 启动服务:
    ```bash
    # Try the modern plugin first / 优先尝试新版插件
    docker compose up -d --build
    
    # Or legacy standalone command / 或者旧版独立命令
    docker-compose up -d --build
    ```
    
    *Troubleshooting*: If you encounter `ModuleNotFoundError: No module named 'attrs'`, your `docker-compose` installation is broken. Please use the `deploy.sh` script instead, or use raw `docker` commands.
    *故障排除*：如果遇到 `ModuleNotFoundError` 错误，说明您的 `docker-compose` 安装已损坏。请改用 `deploy.sh` 脚本，或直接使用 `docker` 命令。

2.  View logs / 查看日志:
    ```bash
    docker-compose logs -f
    ```

## Output Files / 输出文件
Recognition results are saved in the `output` folder with filename format: `original_filename_timestamp_randomID.json`.
识别结果将保存在 `output` 文件夹中，文件名格式为：`原始文件名_时间戳_随机ID.json`。
