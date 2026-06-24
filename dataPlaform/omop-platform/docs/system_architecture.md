# OMOP 医疗数据清洗与治理平台系统架构设计文档

## 1. 系统概述
本系统致力于处理从医院业务系统（EMR/HIS、PACS等）抽取的海量临床医疗数据，通过高性能的流式管线架构，实现数据的标准化（OMOP CDM v5.4）、去隐私化（PHI 脱敏）、以及目标数据的物理隔离存储。系统具备千万级数据处理能力与容错拦截机制，并提供实时前端监控大屏。

## 2. 核心架构设计

系统采用**两段式处理管线与多源异构存储**的架构：

### 2.1 存储层架构 (多数据库协作)
- **Staging 缓存层 (SQLite/CSV)**: 用于承载前端上传或业务库同步的原始脏数据，支持超大 CSV 文件（千万行级别）和本地缓存库，作为清洗管线的输入源。
- **Concept 标准术语库 (PostgreSQL)**: 存储 OMOP CDM 官方提供的标准医学术语表（Vocabulary），在清洗管线中提供实时的术语映射（Mapping）和字典校验。
- **标准化数据隔离区 (MongoDB)**: 用于最终存储经过 100% 校验合格的清洗数据，物理隔离保护隐私安全，同时其 NoSQL 特性天然支持海量病历的横向扩展。
- **非结构化对象存储 (MinIO)**: 用于接收并保存经过 PHI 脱敏后的 DICOM 影像文件。

### 2.2 数据管线架构 (Pipeline)
1. **阶段一：接入与解析管线 (Ingestion Pipeline)**
   - 文本流：接收 CSV，利用 `csv.DictReader` 进行块级读取（5000条/块），记录入 Staging 缓存库，生成 Batch ID，支持前端实时查询进度。
   - 影像流：接收 DICOM 文件，执行**双流拆分**：
     - 文件流：对 DICOM 头部的敏感信息（姓名、证件号）进行不可逆脱敏，保存至 MinIO 存储桶。
     - 元数据流：提取影像时间、检查部位等信息，映射入 Staging 表的观测记录。
2. **阶段二：清洗与归一化管线 (CDM Standardization Pipeline)**
   - 触发方式：后台常驻任务（FastAPI `BackgroundTasks`）。
   - 执行逻辑：流式迭代原始数据 -> 连接 PG 执行 Concept 对齐校验 -> 过滤脏数据/缺失字段 -> 生成质量异常报告（CSV 记录拦截详情） -> 合格数据以 `BATCH_SIZE = 100000` 批量写入 MongoDB。

## 3. 关键性能优化点
- **极低内存占用 (OOM 防范)**: 废弃了传统的 `bulk_save_objects` 全量加载模式，采用 Python Generator 与 Iterator 组合，使 300 万条（1.5GB+）级别数据的内存占用恒定在百兆以内。
- **智能轮询 (Smart Polling)**: 前端弃用复杂的 WebSocket，改用基于 React `useEffect` + `setInterval` 的无状态轮询机制，彻底解决状态不同步、"一直转圈" 的闭包陷阱。
- **动态状态计算**: 大屏监控彻底移除硬编码（如 "100%"），所有百分比指标（如 20% 的脏数据拦截率）均由实时拉取的 total 和 passed/failed 数据计算得出。

## 4. 前端视图架构
基于 React + Tailwind CSS 构建，主要包括：
1. **数据接入台 (Ingestion Form)**: 提供拖拽上传，进度分块回显。
2. **历史批次看板 (Batch History)**: 呈现各批次数据的解析结果与元信息。
3. **清洗监控大屏 (Pipeline Monitor)**: 核心组件，提供管线执行触发、各数据库节点连通性监控、千万级处理指标大盘，并提供“异常报告”的导出功能。

## 5. 部署与环境要求
- **后端服务**: FastAPI + Uvicorn
- **数据库节点**:
  - SQLite (Local: `data/omop_platform.db`)
  - PostgreSQL (Local: `localhost:5432`)
  - MongoDB (Remote/Isolated: `192.168.0.214:27017`)
  - MinIO (Remote/Local: 暴露 `9000` API 端口)
- **环境依赖**: Python 3.9+, Pydantic V2, PyMongo, SQLAlchemy, Minio, Pydicom。