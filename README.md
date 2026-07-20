<<<<<<< HEAD
# Workspace (工作区)

本仓库是一个综合性的代码库，包含多个医疗 AI、深度学习、大模型应用及软件工程项目。

## 📁 项目列表 (Project List)

### 🧠 医疗 AI 与大模型 (Medical AI & Large Models)

*   **[large _model](./large%20_model)**: 医疗大模型核心项目。
    *   **核心功能**: 包含 RAG（检索增强生成）与 RL（强化学习）微调全流程。
    *   **技术栈**: PyTorch, Transformers, PEFT, Milvus, Streamlit。
    *   **文档**: 详见 [README](./large%20_model/README.md) 和 [Summary](./large%20_model/summary.md)。

*   **[RAG_Project](./RAG_Project)**: 专注于 RAG 技术实现的独立模块。
    *   **核心功能**: 知识图谱构建、向量检索验证、Milvus 数据库管理。
    *   **关键脚本**: `reset_milvus_final.py`, `check_dim.py`。

*   **[project](./project)**: 医疗知识库数据处理工具集。
    *   **核心功能**: 支持 Excel/CSV/Markdown 等多格式数据的清洗、去重与索引构建。
    *   **应用**: 为 RAG 系统提供高质量的知识库数据源。

*   **[ne4j](./ne4j)**: 医疗知识图谱与临床路径资料管理项目。
    *   **核心功能**: 提供临床文档（PDF/Word）整理、图谱构建输入数据管理与知识检索数据准备能力。
    *   **应用**: 为 Neo4j 图数据库构建与医学知识关联分析提供基础数据支撑。

*   **[agent_ai](./agent_ai)**: AI 智能体与 AWS 集成。
    *   **核心功能**: 基于 Dify 与 AWS CDK 的智能体部署与编排。
    *   **组件**: Agent Core, Service Stack, Tools (PubMed/Google Search)。

*   **[OCR_Project](./OCR_Project)**: 医疗单据 OCR 识别。
    *   **核心功能**: 识别化验单、处方等医疗图像，提取关键字段。
    *   **特性**: 支持 Docker 容器化部署，提供 RESTful API。

### 🏥 临床与数字医疗 (Clinical & Digital Health)

*   **[CTMS](./CTMS)**: 临床试验管理系统 (Clinical Trial Management System)。
    *   **核心功能**: 包含前后端代码 (`CTMS_Code`) 及演示 (`CTMS_Demo`)，支持临床试验全流程管理、GCP 合规性检查。
    *   **技术栈**: Django, React, Vite。

*   **[CTMS_Pro](./CTMS_Pro)**: CTMS 专业版项目。
    *   **核心功能**: 包含 IWRS（随机化/药物分配）与后端测试脚本，面向临床试验执行场景。

*   **[CTMS_Project](./CTMS_Project)**: CTMS 拓展工程目录。
    *   **核心功能**: 作为 CTMS 相关子模块与实现补充。

*   **[Chronic_disease_prediction_model](./Chronic_disease_prediction_model)**: 慢病风险预测模型。
    *   **核心功能**: 基于 XGBoost/LSTM/Transformer 的多时间窗（7天/30天）风险预测。
    *   **特性**: 包含模型训练、评估报告生成及数据漂移监控 (`monitor.py`)。

*   **[Digital_Twin_Project](./Digital_Twin_Project)**: 数字孪生与脊柱模拟项目。
    *   **核心功能**: 脊柱演化模拟、治疗方案仿真、时间序列分析。
    *   **应用**: 个性化医疗与手术规划。

*   **[Dr_Digital_Twin_Project](./Dr_Digital_Twin_Project)**: 数字孪生医生端应用项目。
    *   **核心功能**: 面向医生工作流的前端交互与可视化能力，支持与数字孪生结果联动展示。

*   **[DEMO_Stroke](./DEMO_Stroke)**: 脑卒中风险预测与数据分析。
    *   **核心功能**: 基于 PPG 信号的心梗/脑卒中风险评估、血管弹性分析。
    *   **关键脚本**: `ppg_vascular_analysis.py`, `risk_results.md`。

### 🖼️ 医疗影像分析 (Medical Imaging)

*   **[Image_project](./Image_project)**: 脑卒中预测深度学习项目。
    *   **核心功能**: 基于 NCCT 和 CTA 图像预测 EVT 术后结果。
    *   **流程**: DICOM 转 NIfTI -> 图像配准 -> 临床数据处理 -> 模型训练 (DenseNet121)。

*   **[Image_project_coder1](./Image_project_coder1)**: 影像处理流程的变体版本。
    *   **核心功能**: 提供了独立的 DICOM 扫描、模板下载与配准验证工具。

### 🤖 自动化与平台 (Automation & Platforms)

*   **[n8n-master](./n8n-master)**: 工作流自动化平台源码。
    *   **核心功能**: 定制化 n8n 节点开发与流程编排。

*   **[openclaw-main](./openclaw-main)**: OpenClaw 主工程。
    *   **核心功能**: 智能体运行时、插件 SDK 与多通道消息集成能力。

*   **[coze](./coze)**: Coze Studio 相关工程代码。
    *   **核心功能**: 覆盖前端、IDL、脚本与 Helm 部署资源。

*   **[SadTalker-main](./SadTalker-main)**: 数字人驱动与口型动画项目。
    *   **核心功能**: 基于输入图像与语音生成数字人口播视频，支持头像驱动与表情动画。

*   **[chatterbox-master](./chatterbox-master)**: 语音交互与对话能力项目。
    *   **核心功能**: 面向语音场景的对话流程编排与交互能力验证。

*   **[clawlob](./clawlob)**: 智能机器人框架源码 (Legacy)。
    *   包含 `clawdbot` (Swabble) 和 `moltbot` 等模块。
*   **[OpenClawInstaller-main](./OpenClawInstaller-main)**: 系统部署与安装工具。
*   **[label-studio-develop](./label-studio-develop)**: Label Studio 数据标注平台的开发版本。

### 🌐 前端演示 (Demos)

*   **[demo](./demo)**: 通用功能演示页面。
*   **[med_demo](./med_demo)**: 医疗场景专用演示前端 (HTML/JS)。
*   **[10year](./10year)**: 心脑血管 10 年风险评估演示项目。
    *   **核心功能**: 基于 China-PAR 场景的表单评估、风险分层（低/中/高危）与个性化健康建议展示。

## 🚀 快速开始 (Getting Started)

每个子项目都包含独立的 `README.md` 文档，详细说明了环境配置、依赖安装及运行方式。请点击上述链接进入相应目录查看。

## 📦 数据目录 (Data)

*   **医院1**: 存储部分脱敏的医疗影像测试数据（DICOM 格式）。

---
*最后更新: 2026-04-27*
=======
# Workspace (工作区)

本仓库是一个综合性的代码库，包含多个医疗 AI、深度学习、大模型应用及软件工程项目。

## 📁 项目列表 (Project List)

### 🧠 医疗 AI 与大模型 (Medical AI & Large Models)

*   **[large _model](./large%20_model)**: 医疗大模型核心项目。
    *   **核心功能**: 包含 RAG（检索增强生成）与 RL（强化学习）微调全流程。
    *   **技术栈**: PyTorch, Transformers, PEFT, Milvus, Streamlit。
    *   **文档**: 详见 [README](./large%20_model/README.md) 和 [Summary](./large%20_model/summary.md)。

*   **[RAG_Project](./RAG_Project)**: 专注于 RAG 技术实现的独立模块。
    *   **核心功能**: 知识图谱构建、向量检索验证、Milvus 数据库管理。
    *   **关键脚本**: `reset_milvus_final.py`, `check_dim.py`。

*   **[project](./project)**: 医疗知识库数据处理工具集。
    *   **核心功能**: 支持 Excel/CSV/Markdown 等多格式数据的清洗、去重与索引构建。
    *   **应用**: 为 RAG 系统提供高质量的知识库数据源。

*   **[ne4j](./ne4j)**: 医疗知识图谱与临床路径资料管理项目。
    *   **核心功能**: 提供临床文档（PDF/Word）整理、图谱构建输入数据管理与知识检索数据准备能力。
    *   **应用**: 为 Neo4j 图数据库构建与医学知识关联分析提供基础数据支撑。

*   **[agent_ai](./agent_ai)**: AI 智能体与 AWS 集成。
    *   **核心功能**: 基于 Dify 与 AWS CDK 的智能体部署与编排。
    *   **组件**: Agent Core, Service Stack, Tools (PubMed/Google Search)。

*   **[OCR_Project](./OCR_Project)**: 医疗单据 OCR 识别。
    *   **核心功能**: 识别化验单、处方等医疗图像，提取关键字段。
    *   **特性**: 支持 Docker 容器化部署，提供 RESTful API。

### 🏥 临床与数字医疗 (Clinical & Digital Health)

*   **[CTMS](./CTMS)**: 临床试验管理系统 (Clinical Trial Management System)。
    *   **核心功能**: 包含前后端代码 (`CTMS_Code`) 及演示 (`CTMS_Demo`)，支持临床试验全流程管理、GCP 合规性检查。
    *   **技术栈**: Django, React, Vite。

*   **[CTMS_Pro](./CTMS_Pro)**: CTMS 专业版项目。
    *   **核心功能**: 包含 IWRS（随机化/药物分配）与后端测试脚本，面向临床试验执行场景。

*   **[CTMS_Project](./CTMS_Project)**: CTMS 拓展工程目录。
    *   **核心功能**: 作为 CTMS 相关子模块与实现补充。

*   **[Chronic_disease_prediction_model](./Chronic_disease_prediction_model)**: 慢病风险预测模型。
    *   **核心功能**: 基于 XGBoost/LSTM/Transformer 的多时间窗（7天/30天）风险预测。
    *   **特性**: 包含模型训练、评估报告生成及数据漂移监控 (`monitor.py`)。

*   **[Digital_Twin_Project](./Digital_Twin_Project)**: 数字孪生与脊柱模拟项目。
    *   **核心功能**: 脊柱演化模拟、治疗方案仿真、时间序列分析。
    *   **应用**: 个性化医疗与手术规划。

*   **[Dr_Digital_Twin_Project](./Dr_Digital_Twin_Project)**: 数字孪生医生端应用项目。
    *   **核心功能**: 面向医生工作流的前端交互与可视化能力，支持与数字孪生结果联动展示。

*   **[DEMO_Stroke](./DEMO_Stroke)**: 脑卒中风险预测与数据分析。
    *   **核心功能**: 基于 PPG 信号的心梗/脑卒中风险评估、血管弹性分析。
    *   **关键脚本**: `ppg_vascular_analysis.py`, `risk_results.md`。

### 🖼️ 医疗影像分析 (Medical Imaging)

*   **[Image_project](./Image_project)**: 脑卒中预测深度学习项目。
    *   **核心功能**: 基于 NCCT 和 CTA 图像预测 EVT 术后结果。
    *   **流程**: DICOM 转 NIfTI -> 图像配准 -> 临床数据处理 -> 模型训练 (DenseNet121)。

*   **[Image_project_coder1](./Image_project_coder1)**: 影像处理流程的变体版本。
    *   **核心功能**: 提供了独立的 DICOM 扫描、模板下载与配准验证工具。

### 🤖 自动化与平台 (Automation & Platforms)

*   **[n8n-master](./n8n-master)**: 工作流自动化平台源码。
    *   **核心功能**: 定制化 n8n 节点开发与流程编排。

*   **[openclaw-main](./openclaw-main)**: OpenClaw 主工程。
    *   **核心功能**: 智能体运行时、插件 SDK 与多通道消息集成能力。

*   **[coze](./coze)**: Coze Studio 相关工程代码。
    *   **核心功能**: 覆盖前端、IDL、脚本与 Helm 部署资源。

*   **[SadTalker-main](./SadTalker-main)**: 数字人驱动与口型动画项目。
    *   **核心功能**: 基于输入图像与语音生成数字人口播视频，支持头像驱动与表情动画。

*   **[chatterbox-master](./chatterbox-master)**: 语音交互与对话能力项目。
    *   **核心功能**: 面向语音场景的对话流程编排与交互能力验证。

*   **[clawlob](./clawlob)**: 智能机器人框架源码 (Legacy)。
    *   包含 `clawdbot` (Swabble) 和 `moltbot` 等模块。
*   **[OpenClawInstaller-main](./OpenClawInstaller-main)**: 系统部署与安装工具。
*   **[label-studio-develop](./label-studio-develop)**: Label Studio 数据标注平台的开发版本。

### 🌐 前端演示 (Demos)

*   **[demo](./demo)**: 通用功能演示页面。
*   **[med_demo](./med_demo)**: 医疗场景专用演示前端 (HTML/JS)。
*   **[10year](./10year)**: 心脑血管 10 年风险评估演示项目。
    *   **核心功能**: 基于 China-PAR 场景的表单评估、风险分层（低/中/高危）与个性化健康建议展示。

## 🚀 快速开始 (Getting Started)

每个子项目都包含独立的 `README.md` 文档，详细说明了环境配置、依赖安装及运行方式。请点击上述链接进入相应目录查看。

## 📦 数据目录 (Data)

*   **医院1**: 存储部分脱敏的医疗影像测试数据（DICOM 格式）。

---
*最后更新: 2026-04-27*
>>>>>>> origin/main
