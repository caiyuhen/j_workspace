# 脊柱数字孪生微服务 (Spine Digital Twin Microservices)

本目录包含了脊柱数字孪生项目的微服务源代码。

## 服务列表 (Services)

*   **[patient-service](./patient-service)**: 患者数据服务。负责解析和检索患者数据。
*   **[simulation-service](./simulation-service)**: 模拟计算服务。根据治疗方案运行脊柱演变模拟。
*   **[visualization-service](./visualization-service)**: 可视化渲染服务。渲染 3D 脊柱模型和演变趋势图表。
*   **[report-gateway](./report-gateway)**: 报告网关。作为 API 网关，编排其他服务以生成最终报告。
*   **[ocr-service](./ocr-service)**: OCR 识别服务。从 PDF 医疗记录中提取结构化数据。

## 本地运行 (开发环境)

### 一键启动 (推荐)

**Windows (PowerShell):**
```powershell
.\start_services.ps1
```

**Linux/macOS (Bash):**
```bash
chmod +x start_services.sh stop_services.sh
./start_services.sh
# 停止服务: ./stop_services.sh
```

### 手动启动 (Manual Start)
您可以使用 `uvicorn` 单独启动每个服务：

1.  **模拟服务 (Simulation Service)** (端口 8001):
    ```bash
    cd services/simulation-service
    pip install -r requirements.txt
    cd src
    uvicorn main:app --reload --port 8001
    ```

2.  **可视化服务 (Visualization Service)** (端口 8002):
    ```bash
    cd services/visualization-service
    pip install -r requirements.txt
    cd src
    uvicorn main:app --reload --port 8002
    ```

3.  **患者服务 (Patient Service)** (端口 8003):
    ```bash
    cd services/patient-service
    pip install -r requirements.txt
    cd src
    uvicorn main:app --reload --port 8003
    ```

4.  **OCR 服务 (OCR Service)** (端口 8004):
    ```bash
    cd services/ocr-service
    pip install -r requirements.txt
    cd src
    uvicorn main:app --reload --port 8004
    ```

5.  **报告网关 (Report Gateway)** (端口 8000):
    ```bash
    cd services/report-gateway
    pip install -r requirements.txt
    cd src
    uvicorn main:app --reload --port 8000
    ```

## Docker 支持

每个服务都包含一个 `Dockerfile`。您可以单独构建镜像：

```bash
docker build -t spine-simulation-service ./services/simulation-service
docker build -t spine-visualization-service ./services/visualization-service
# ... 以此类推
```
