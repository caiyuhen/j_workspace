# 脊柱数字孪生系统 - 模块化与微服务架构设计方案

## 1. 概述 (Executive Summary)

当前系统基于 Python 脚本进行批处理，功能涵盖了从数据解析、3D 建模、治疗模拟到可视化报告生成的全流程。为了提升系统的**可扩展性 (Scalability)**、**可维护性 (Maintainability)** 和 **复用性 (Reusability)**，建议将现有的单体脚本架构重构为**模块化微服务架构**。

本设计方案旨在将核心业务逻辑（数据、模拟、可视化）解耦，使其能够独立开发、部署和扩展，同时支持未来对接 Web 前端或移动端应用。

---

## 2. 现有架构 (As-Is Architecture)

目前系统属于**脚本驱动的单体架构 (Script-based Monolith)**。

*   **数据层**: 依赖本地 JSON 文件 (`extracted_data.json`, `timeseries_output/*.json`)。
*   **逻辑层**:
    *   `parse_spine_data.py`: 数据解析。
    *   `generate_spine_model.py`: 静态模型生成。
    *   `simulate_treatment.py`: 核心模拟算法。
    *   `visualize_spine_evolution.py`: 可视化生成。
*   **控制层**: `run_batch_analysis.py` 等脚本作为入口，串行调用上述模块。
*   **表现层**: 生成静态 HTML 文件，通过简易 HTTP Server 访问。

**痛点**:
*   **耦合度高**: 模拟与可视化紧密绑定，修改一个可能影响另一个。
*   **并发受限**: 依赖本地文件锁，难以进行大规模并发计算。
*   **集成困难**: 难以对外提供 API 供其他系统调用。

---

## 3. 目标架构 (To-Be Architecture)

建议采用 **微服务架构 (Microservices Architecture)** 或 **模块化单体 (Modular Monolith)** 作为过渡。

### 3.1 服务拆分视图

我们将系统拆分为以下四个核心服务：

#### 1. 患者数据服务 (Patient Digital Twin Service)
*   **职责**: 负责患者档案、影像数据、脊柱参数的 CRUD (增删改查) 管理。它是“数字孪生”的数据基座。
*   **核心功能**:
    *   患者基本信息管理。
    *   OCR/影像数据解析与入库（原 `parse_spine_data.py`）。
    *   提供标准化的脊柱参数 API。
*   **数据存储**: 关系型数据库 (PostgreSQL) 存储结构化数据，对象存储 (MinIO/S3) 存储原始影像。

#### 2. 治疗模拟服务 (Treatment Simulation Service)
*   **职责**: 纯计算引擎，负责根据输入参数模拟脊柱演变。
*   **核心功能**:
    *   接收患者当前状态和干预方案（支具、强化、手术等）。
    *   执行时间序列模拟算法（原 `simulate_treatment.py`）。
    *   返回按周/月变化的预测数据。
*   **特点**: 无状态 (Stateless)，计算密集型，可横向扩展。

#### 3. 可视化渲染服务 (Visualization & Rendering Service)
*   **职责**: 将数据转换为视觉表达。
*   **核心功能**:
    *   生成 3D 脊柱网格数据（原 `generate_spine_model.py`）。
    *   生成演变趋势图表和动画帧数据（原 `visualize_spine_evolution.py`）。
    *   既可以返回静态 HTML 片段，也可以返回 JSON 格式的 3D 坐标供前端渲染。

#### 4. 报告与编排服务 (Report & Orchestration Service) / BFF
*   **职责**: 面向用户的业务聚合层。
*   **核心功能**:
    *   协调上述服务：获取数据 -> 调用模拟 -> 调用可视化 -> 组装报告。
    *   管理“批处理”任务。
    *   生成最终的用户仪表盘（原 `generate_index.py`）。

---

## 4. 接口与数据流设计 (Interface & Data Flow)

各服务之间通过 **RESTful API** (HTTP/JSON) 进行通信。

### 场景：生成患者预测报告

1.  **用户/编排服务** 发起请求：`POST /api/reports/generate`
    *   参数: `{ "patient_id": "123", "plan": "Brace_24Months" }`
2.  **编排服务** 调用 **患者数据服务**:
    *   `GET /api/patients/123/metrics` -> 获取脊柱参数 (Cobb角, 旋转等)。
3.  **编排服务** 调用 **模拟服务**:
    *   `POST /api/simulation/predict`
    *   输入: `{ "metrics": {...}, "plan": {...} }`
    *   输出: `timeseries_data` (96周的演变数据)。
4.  **编排服务** 调用 **可视化服务**:
    *   `POST /api/visualization/render/evolution`
    *   输入: `timeseries_data`
    *   输出: HTML 代码或 Plotly JSON 配置。
5.  **编排服务** 组装最终页面并返回/保存。

---

## 5. 技术栈建议 (Technology Stack)

*   **编程语言**: Python 3.9+ (保持现有技术栈)。
*   **Web 框架**: FastAPI (高性能，原生支持异步，适合计算服务) 或 Flask。
*   **数据验证**: Pydantic (确保数据结构在服务间传递的准确性)。
*   **容器化**: Docker (每个服务一个容器)。
*   **任务队列** (可选): Celery + Redis (用于处理耗时的模拟计算任务)。

---

## 6. 目录结构重构建议

```text
Digital_Twin_Project/
├── services/
│   ├── patient-service/        # 患者数据服务
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── simulation-service/     # 模拟计算服务 (原 simulate_treatment.py)
│   │   ├── src/
│   │   │   └── engine.py       # 核心算法
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   ├── visualization-service/  # 可视化服务 (原 visualize_spine_evolution.py)
│   │   ├── src/
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   └── report-gateway/         # 网关与编排
│       ├── src/
│       └── ...
├── shared/                     # 共享库 (数据模型定义)
├── docker-compose.yml          # 本地编排
└── README.md
```

## 7. 下一步行动计划 (Migration Plan)

1.  **定义数据模型 (Data Contracts)**: 明确各服务间交换的 JSON 结构。
2.  **提取核心类**: 将脚本中的函数封装为独立的类 (Class)，剥离文件 I/O 操作。
3.  **API 包装**: 使用 FastAPI 为每个核心类包裹 HTTP 接口。
4.  **容器化**: 编写 Dockerfile。
5.  **集成测试**: 验证服务间调用流程。
