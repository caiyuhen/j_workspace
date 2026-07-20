<<<<<<< HEAD
# 脊柱数字孪生微服务 (Spine Digital Twin Microservices)

本目录包含了脊柱数字孪生项目的微服务源代码。

## 服务列表 (Services)

*   **[patient-service](./patient-service)**: 患者数据服务。负责解析和检索患者数据。
*   **[simulation-service](./simulation-service)**: 模拟计算服务。根据治疗方案运行脊柱演变模拟。
*   **[visualization-service](./visualization-service)**: 可视化渲染服务。渲染 3D 脊柱模型和演变趋势图表。
*   **[report-gateway](./report-gateway)**: 报告网关。作为 API 网关，编排其他服务以生成最终报告。
*   **[ocr-service](./ocr-service)**: OCR 识别服务。从 PDF 医疗记录中提取结构化数据。
*   **[xray-analysis-service](./xray-analysis-service)**: X 光分析服务。接收 JPG / PNG / DICOM 文件，提取基础影像特征并输出统一患者状态。

## 统一工作流接口

报告网关新增统一分析接口：

```http
POST /workflow/analyze
Content-Type: multipart/form-data
```

支持三种工作流：

*   `pdf_only`: 仅上传 PDF，通过 OCR 进入模拟与可视化
*   `xray_only`: 仅上传 X 光文件，通过 X 光分析进入模拟与可视化
*   `multimodal`: 同时上传 PDF 和 X 光，进行轻量融合后进入模拟与可视化

请求字段示例：

```text
workflow_type=pdf_only|xray_only|multimodal
pdf_file=<optional pdf>
xray_file=<optional image or dicom>
patient_name=<optional>
treatment_type=Brace
duration=24
compliance=0.9
```

## 联调脚本

启动服务后可执行：

```bash
python .\run_multimodal_smoke_checks.py
```

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

5.  **X 光分析服务 (X-Ray Analysis Service)** (端口 8005):
    ```bash
    cd services/xray-analysis-service
    pip install -r requirements.txt
    cd src
    uvicorn main:app --reload --port 8005
    ```

6.  **报告网关 (Report Gateway)** (端口 8000):
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
docker build -t spine-xray-analysis-service ./services/xray-analysis-service
# ... 以此类推
```
=======
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
>>>>>>> origin/main
