# 脊柱数字孪生项目 (Spine Digital Twin Project)

## 概述 (Overview)

脊柱数字孪生项目是一个先进的医疗模拟系统，旨在为脊柱侧弯（Scoliosis）患者创建数字孪生模型。该系统利用患者的历史数据、影像资料（如 X 光片、MRI）和生物力学模型，模拟脊柱在不同治疗方案下的演变过程。

核心目标是为医生和患者提供可视化的、基于证据的预测工具，以优化治疗决策（如支具佩戴、手术干预或保守治疗）。

## 系统架构 (System Architecture)

该项目采用微服务架构，以确保模块化、可扩展性和易于维护。

### 核心微服务 (Core Microservices)

1.  **患者服务 (Patient Service)** (Port: 8003)
    *   **职责**: 管理患者数据，包括人口统计学信息、病史和当前脊柱状态（Cobb 角、椎骨旋转等）。
    *   **数据源**: 解析 OCR 提取的 JSON 数据，并提供结构化的患者对象。

2.  **OCR 服务 (OCR Service)** (Port: 8004)
    *   **职责**: 专门处理医疗文档（PDF 报告）。使用 OCR 技术（基于 RapidOCR/PaddleOCR）从扫描件或 PDF 中提取关键文本和数值数据。
    *   **集成**: 接收文件上传，提取文本，并将结果保存为标准 JSON 格式供其他服务使用。

3.  **模拟服务 (Simulation Service)** (Port: 8001)
    *   **职责**: 运行生物力学或经验生长模型来预测脊柱的演变。
    *   **功能**: 支持基于“周”的时间步长模拟，计算在不同治疗方案（如支具、手术、自然生长）下的 Cobb 角变化。

4.  **可视化服务 (Visualization Service)** (Port: 8002)
    *   **职责**: 将模拟结果转换为直观的图表和 3D 模型。
    *   **功能**: 生成包含时间滑块（按周）的交互式 Plotly 图表，展示脊柱侧弯的演变轨迹。

5.  **报告网关 (Report Gateway)** (Port: 8000)
    *   **职责**: 作为系统的统一入口点 (API Gateway)。
    *   **功能**: 编排上述所有服务，处理文件上传，协调数据流，并生成最终的综合报告。

### 数据流 (Data Flow)

1.  **上传**: 用户通过网关上传 PDF 医疗报告。
2.  **提取**: 网关调用 OCR 服务提取数据，并保存为 JSON。
3.  **查询**: 网关请求患者服务，患者服务读取并解析 JSON 数据。
4.  **模拟**: 网关将患者数据和治疗方案发送给模拟服务。
5.  **可视化**: 模拟结果被发送到可视化服务以生成图表。
6.  **报告**: 网关聚合所有结果并返回给用户。

## 快速开始 (Quick Start)

### 先决条件

*   Python 3.9+
*   Docker (可选，用于容器化部署)
*   PowerShell (Windows) 或 Bash (Linux/macOS)

### 本地开发运行 (Windows)

我们提供了一个一键启动脚本，可在后台启动所有微服务。

1.  打开 PowerShell。
2.  运行启动脚本：
    ```powershell
    ./start_services.ps1
    ```
    该脚本将启动所有五个服务，分别监听端口 8000-8004。

### 本地开发运行 (Linux/macOS)

1.  赋予脚本执行权限：
    ```bash
    chmod +x start_services.sh stop_services.sh
    ```
2.  运行启动脚本：
    ```bash
    ./start_services.sh
    ```
3.  停止服务：
    ```bash
    ./stop_services.sh
    ```

### Docker 容器化部署 (推荐)

如果您希望在隔离环境中运行服务，或在生产环境中部署，请使用Docker。

详细指南请参阅 [Docker 部署文档](README_DOCKER.md)。

简要步骤：
```bash
docker-compose up --build -d
```

### 验证安装

运行端到端测试脚本以验证所有服务是否正常协同工作：

```bash
python test_e2e.py
```

或者单独测试 OCR 服务：

```bash
python test_ocr.py
```

## 功能特性 (Features)

*   **PDF 自动解析**: 自动从医疗报告中提取患者姓名、诊断结果和测量数据。
*   **多维度模拟**: 支持支具治疗、手术干预和自然病程的模拟。
*   **高精度预测**: 按“周”进行时间步进，提供细粒度的演变预测。
*   **交互式可视化**: 提供带时间滑块的演变趋势图，直观展示治疗效果。
*   **模块化设计**: 微服务架构允许独立更新和扩展各个功能模块。

## 目录结构 (Directory Structure)

```
d:\workspace\Digital_Twin_Project/
  - services/            # 微服务源代码
  - docs/                # 详细设计文档
  - extracted_data/      # OCR 提取的数据 (JSON)
  - start_services.ps1   # Windows 启动脚本
  - start_services.sh    # Linux 启动脚本
  - test_e2e.py          # 端到端测试脚本
  - docker-compose.yml   # Docker 编排文件
```

## 详细文档 (Detailed Documentation)

请参阅 `docs/` 目录下的详细设计文档：

*   [架构设计 (Architecture Design)](docs/ARCHITECTURE_DESIGN.md)
*   [API 规范 (API Specification)](docs/API_SPECIFICATION.md)
*   [数据模型 (Data Models)](docs/DATA_MODELS.md)
*   [数据字典 (Data Dictionary)](docs/data_dictionary.md)
*   [干预方法 (Intervention Methods)](docs/intervention_methods.md)
*   [Docker 部署指南 (Docker Deployment)](README_DOCKER.md)

*   `/services`: 包含所有微服务的源代码。
    *   `/patient-service`: 患者数据管理。
    *   `/simulation-service`: 演变预测算法。
    *   `/visualization-service`: 图表和模型渲染。
    *   `/report-gateway`: API 网关和编排。
    *   `/ocr-service`: 光学字符识别引擎。
*   `/docs`: 项目文档（架构设计、API 规范等）。
*   `start_services.ps1`: Windows 启动脚本。
*   `start_services.sh`: Linux 启动脚本。
*   `test_e2e.py`: 端到端测试套件。
*   `test_ocr.py`: OCR 服务测试脚本。

## 贡献 (Contributing)

请阅读 `CONTRIBUTING.md` (如有) 了解代码规范和提交流程。
