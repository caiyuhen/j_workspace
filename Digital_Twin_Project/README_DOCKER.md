# Digital Twin Project - Docker 部署指南

本指南将帮助您使用 Docker 和 Docker Compose 部署脊柱数字孪生微服务系统。

## 前置条件

- 已安装 [Docker Desktop](https://www.docker.com/products/docker-desktop) (Windows/Mac) 或 Docker Engine (Linux)。
- 确保 Docker 服务正在运行。

## 快速启动

1. **构建并启动所有服务**

   在项目根目录下打开终端，运行：

   ```bash
   docker-compose up --build -d
   ```

   这将构建所有微服务的镜像并启动容器。

2. **验证服务状态**

   运行以下命令查看容器状态：

   ```bash
   docker-compose ps
   ```

   您应该看到以下服务正在运行：
   - `report-gateway` (端口 8000)
   - `simulation-service` (端口 8001)
   - `visualization-service` (端口 8002)
   - `patient-service` (端口 8003)
   - `ocr-service` (端口 8004)

3. **访问应用**

   - **Web 前端**: 打开浏览器访问 [http://localhost:8000](http://localhost:8000)
   - **API 文档**: [http://localhost:8000/docs](http://localhost:8000/docs)

## 服务详情

| 服务名称 | 端口 | 描述 |
| --- | --- | --- |
| Report Gateway | 8000 | API 网关，处理前端请求和文件上传 |
| Simulation Service | 8001 | 运行脊柱演变模拟算法 |
| Visualization Service | 8002 | 生成 Plotly 3D 可视化图表 |
| Patient Service | 8003 | 管理患者数据 (SQLite/JSON) |
| OCR Service | 8004 | 处理 PDF 医疗记录并提取数据 |

## 数据持久化

- **OCR 数据**: 提取的 JSON 文件存储在 `./extracted_data` 目录中，该目录挂载到 OCR 和 Patient 服务容器中。
- **源代码**: `src` 目录挂载到容器中，支持热重载（开发模式）。

## 常用命令

- **停止所有服务**:
  ```bash
  docker-compose down
  ```

- **查看日志**:
  ```bash
  docker-compose logs -f
  ```

- **重启特定服务** (例如 OCR 服务):
  ```bash
  docker-compose restart ocr-service
  ```

## 故障排除

- **端口冲突**: 如果启动失败，请确保本地端口 (8000-8004) 未被其他程序占用。
- **OCR 依赖**: OCR 服务镜像较大，首次构建可能需要几分钟下载依赖。
- **网络问题**: 如果服务间无法通信，请检查 Docker 网络设置 (默认使用 bridge 网络)。
