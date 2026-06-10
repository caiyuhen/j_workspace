# 脊柱数字孪生项目 (Spine Digital Twin Project)

## 概述 (Overview)

脊柱数字孪生项目是一个先进的医疗模拟系统，旨在为脊柱侧弯（Scoliosis）患者创建数字孪生模型。该系统利用患者的历史数据、影像资料（如 X 光片、MRI）和生物力学模型，模拟脊柱在不同治疗方案下的演变过程。

核心目标是为医生和患者提供可视化的、基于证据的预测工具，以优化治疗决策（如支具佩戴、手术干预或保守治疗）。

## 系统架构 (System Architecture)

该项目采用微服务架构，以确保模块化、可扩展性和易于维护。

### 核心微服务 (Core Microservices)

1.  **患者服务 (Patient Service)** (Port: 9003)
    *   **职责**: 管理患者数据，包括人口统计学信息、病史和当前脊柱状态（Cobb 角、椎骨旋转等）。
    *   **数据源**: 解析 OCR 提取的 JSON 数据，并提供结构化的患者对象。

2.  **OCR 服务 (OCR Service)** (Port: 9004)
    *   **职责**: 专门处理医疗文档（PDF 报告）。使用 OCR 技术（基于 RapidOCR/PaddleOCR）从扫描件或 PDF 中提取关键文本和数值数据。
    *   **集成**: 接收文件上传，提取文本，并将结果保存为标准 JSON 格式供其他服务使用。

3.  **X 光分析服务 (X-Ray Analysis Service)** (Port: 9005)
    *   **职责**: 读取并分析骨科 X 光影像，进行前景提取、中轴线拟合，估算影像质量分与角度。
    *   **支持格式**: PNG, JPG, JPEG, DCM, HEIC, HEIF。

4.  **模拟服务 (Simulation Service)** (Port: 9001)
    *   **职责**: 运行生物力学或经验生长模型来预测脊柱的演变。
    *   **功能**: 支持基于“周”或“月”的时间步长模拟，计算在不同治疗方案（如支具、物理治疗、强化康复、手术治疗）下的 Cobb 角变化。

5.  **可视化服务 (Visualization Service)** (Port: 9002)
    *   **职责**: 将模拟结果转换为直观的图表和 3D 模型。
    *   **功能**: 生成包含时间滑块的交互式 Plotly 图表，展示脊柱侧弯的 3D 演变轨迹及多方案对比。

6.  **报告网关 (Report Gateway)** (Port: 9000)
    *   **职责**: 作为系统的统一入口点和前端界面承载。
    *   **功能**: 提供多模态（PDF 文本、X 光图像）工作流编排，支持同患者多方案平行对比与融合决策。

## 快速开始 (Quick Start)

### 先决条件

*   Python 3.9+ (推荐 3.10)
*   PowerShell (Windows) 或 Bash (Linux/macOS)

### 本地开发运行 (Windows 备用端口)

目前系统已迁移至 `9000-9005` 端口段以避免与其他常见服务冲突。

1.  打开 PowerShell。
2.  运行启动脚本：
    ```powershell
    .\start_services_alt_ports.ps1
    ```
    该脚本将启动所有六个服务。
3.  打开浏览器访问前端控制台：`http://127.0.0.1:9000/`

### 本地开发运行 (Linux/macOS 备用端口)

1.  赋予脚本执行权限：
    ```bash
    chmod +x start_services_alt_ports.sh stop_services_alt_ports.sh
    ```
2.  运行启动脚本：
    ```bash
    ./start_services_alt_ports.sh
    ```
    服务将在后台启动，日志文件输出在 `./logs` 目录下。
3.  打开浏览器访问前端控制台：`http://127.0.0.1:9000/`
4.  停止服务：
    ```bash
    ./stop_services_alt_ports.sh
    ```

### 验证与联调测试

运行多模态工作流的自动化联调脚本，确认各链路（仅 PDF、仅 X光、多模态联合）运转正常：

```bash
python run_multimodal_smoke_checks.py
```

## 功能特性 (Features)

*   **多模态融合分析**: 能够单独基于文本病历（PDF）、单独基于医学影像（X光）或联合两者数据进行脊柱参数提取与融合。
*   **同患者多方案对比**: 针对导入患者或新上传数据，系统可一键并行模拟 4 种治疗方案（自然发展/支具/强化康复/手术），并给出直观的时间轴折线图。
*   **智能置信度预警**: 当图像质量得分过低或不同模态提取的角度参数冲突（误差 > 8°）时，系统会自动高亮提示需要人工复核。
*   **交互式 3D 可视化**: 提供带时间滑块的演变趋势图，同时展现冠状面、矢状面三维骨骼结构变化。

## 目录结构 (Directory Structure)

```
d:\workspace\Digital_Twin_Project/
  - services/                 # 微服务源代码
    - report-gateway/         # 网关与前端静态页面 (index.html)
    - patient-service/        # 患者数据与本地 SQLite 管理
    - simulation-service/     # 核心生物力学模拟演变
    - visualization-service/  # 3D 与 Plotly 图表渲染
    - ocr-service/            # PDF/图片 OCR 提取
    - xray-analysis-service/  # X 光图像处理增强
  - docs/                     # 详细设计与接口文档
  - extracted_data/           # OCR 提取的数据 (JSON 缓存)
  - tests/                    # TDD 单元测试与集成测试用例
  - start_services_alt_ports.ps1  # Windows 9000段启动脚本
  - start_services_alt_ports.sh   # Linux 9000段启动脚本
  - stop_services_alt_ports.sh    # Linux 停止脚本
  - run_multimodal_smoke_checks.py # 多模态联调验证脚本
```
