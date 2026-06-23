# OMOP 医疗数据清洗与治理平台 — 产品设计方案

> 版本：v1.0  
> 目标：构建符合 OMOP CDM 标准的医疗数据清洗、归一化、映射、质控、治理一体化平台

---

## 一、产品定位与核心理念

### 1.1 产品定位
面向医院/医疗机构的**数据中台型产品**，解决多源异构医疗数据（API、CSV导出）到 OMOP CDM 的端到端 ETL+L（抽取、清洗、映射、加载、治理）问题。

### 1.2 核心理念
| 理念 | 说明 |
|------|------|
| **可回溯** | 每条数据从源头到OMOP表的全链路可追溯，支持任意时间点数据回滚 |
| **自动化优先** | Source-to-OMOP 映射尽可能自动，人工干预做兜底 |
| **质量门槛** | ETL 过程中强制数据质量检查，质量不达标的批次不上线 |
| **可扩展** | 支持新增医院/数据源/映射规则时零代码或少代码配置 |

---

## 二、产品架构图

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          用户界面层 (Frontend)                               │
│  ┌───────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐   │
│  │Dashboard│数据源管理 │ 映射管理  │ 数据质量  │ 数据回溯  │ 系统管理│   │
│  └───┬───┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └──┬───┘   │
│      └──────────┴────────────┴────────────┴────────────┴───────────┘       │
│                                    │ REST API / WebSocket                   │
├────────────────────────────────────┼────────────────────────────────────────┤
│                           API 网关层                                        │
│                  ┌─────────────────┴─────────────────┐                      │
│                  │     Nginx / Kong API Gateway       │                      │
│                  │  (认证 / 限流 / 路由 / 日志)        │                     │
│                  └─────────────────┬─────────────────┘                      │
│                                    │                                        │
├────────────────────────────────────┼────────────────────────────────────────┤
│                         业务服务层 (Backend Microservices)                    │
│                                                                             │
│  ┌──────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐   │
│  │ 数据接入  │ │ 数据清洗   │ │ OMOP映射   │ │ 数据治理   │ │ 回溯服务  │   │
│  │ Service  │ │ Service    │ │ Engine     │ │ Service    │ │ Service  │   │
│  ├──────────┤ ├────────────┤ ├────────────┤ ├────────────┤ ├──────────┤   │
│  │ CSV解析  │ │ 结构归一化 │ │ WhiteRabbit│ │ 规则引擎   │ │ 版本追溯 │   │
│  │ API轮询  │ │ 编码转换   │ │ Usagi映射  │ │ 审批工作流 │ │ 审计日志 │   │
│  │ 增量识别 │ │ 脏数据清洗 │ │ 自动映射   │ │ 权限管控   │ │ 快照管理 │   │
│  └──────────┘ └────────────┘ └────────────┘ └────────────┘ └──────────┘   │
│                                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ 数据质量服务  │ │ 调度编排服务  │ │ 元数据服务    │ │ 通知与告警服务   │   │
│  │ ACHILLES+DQD │ │ Airflow      │ │ OpenMetadata │ │ Email/Webhook    │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘   │
│                                                                             │
├────────────────────────────────────┼────────────────────────────────────────┤
│                         数据存储层                                           │
│                                                                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐   │
│  │ 原始数据区    │ │ 清洗暂存区    │ │ OMOP CDM     │ │ 元数据仓库       │   │
│  │ (Raw Zone)   │ │ (Staging)    │ │ (PostgreSQL) │ │ (Metadata DB)   │   │
│  │ 带版本号存储  │ │ 标准化后数据  │ │ Person,Visit │ │ 映射规则         │   │
│  │ CSV/JSON原稿 │ │ 待映射状态   │ │ Condition... │ │ 质量基线         │   │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────────┘   │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                      数据湖 / 对象存储 (MinIO/S3)                      │  │
│  │             原始CSV、API响应快照、映射日志、质量报告归档                   │  │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.1 分层说明

| 层 | 职责 |
|----|------|
| **用户界面层** | 可视化操作与监控，面向数据管理员、数据治理人员、医院数据对接人 |
| **API 网关层** | 统一入口，认证鉴权（OAuth2/JWT），限流，请求日志 |
| **业务服务层** | 微服务架构（或模块化单体），每个服务独立部署/扩容 |
| **数据存储层** | 四区分离 + 对象存储归档，保证数据安全与可追溯 |

---

## 三、产品功能设计

### 3.1 前端功能

#### 3.1.1 Dashboard 总览面板
- **数据接入概览**：各医院数据源状态（正常/异常/待同步），实时接入流量
- **映射进度看板**：已映射概念数 / 待确认映射数 / 映射覆盖率百分比
- **数据质量仪表盘**：各 OMOP 表的质控通过率，常见异常分布（按来源、按字段）
- **ETL 流水线状态**：当前运行批次、排队批次、失败批次、历史趋势
- **公告与预警**：近期数据治理通知、质量阈值超标告警

#### 3.1.2 数据源管理
- **数据源注册**：配置医院数据源（名称、类型：API/CSV、连接参数、频率）
- **API 数据源配置**：接口地址、认证方式（Basic/OAuth2/Token）、轮询间隔、增量字段设置
- **CSV 数据源配置**：字段定义（文件头映射表）、分隔符、编码、上传方式（Web上传 / SFTP监控）
- **数据源测试连接**：一键连通性测试、返回样本数据预览
- **数据源启停**：单个暂停/恢复/删除，批量操作

#### 3.1.3 数据接入与预览
- **数据导入管理**：手动触发导入 / 查看导入历史 / 导入日志详情
- **原始数据预览**：查看最新批次原始数据（CSV表格渲染 / JSON 树形展示）
- **数据结构扫描**：自动识别字段名、数据类型、空值率、值分布直方图
- **数据版本对比**：同一数据源前后两个版本的差异对比（新增字段、值变化）

#### 3.1.4 OMOP 映射管理（核心功能）
- **Source-to-OMOP 映射工作台**（可视化映射配置）：
  - 左侧：源数据字段树（表→字段）
  - 右侧：目标 OMOP 表结构（Person / Visit / Condition / Drug / Measurement...）
  - 拖拽连线建立映射关系
- **概念映射编辑器**（基于 Usagi 二次开发）：
  - 自动推荐目标概念（基于 OHDSI 词汇表 + 语义相似度）
  - 模糊搜索 OMOP Concept（来源 / 目标 / 多语言）
  - 映射审批工作流：待审、一审通过、已生效、已废弃
- **映射规则集管理**：
  - 规则版本化（每次修改生成新版本，支持回滚）
  - 规则导出/导入（跨环境迁移）
  - 规则覆盖范围分析（哪些表哪些字段已覆盖）

#### 3.1.5 数据质量与验证
- **质量检查规则配置**：
  - 预置规则：完整性、唯一性、一致性、时效性、准确性
  - 自定义规则：编写 SQL 或 DSL 条件
  - OMOP 合规校验：ForeignKey 完整性、Concept ID 在词汇表内、日期逻辑校验
- **质量报告**：
  - 按批次/按表/按医院查看质量报告
  - 合格率趋势图
  - 异常详情下钻（哪个字段、哪条记录）
- **ACHILLES 数据特征报告**（嵌入式）：
  - OMOP CDM 各表的数据分布统计
  - 异常数据特征标记

#### 3.1.6 数据回溯与审计
- **数据谱系图（Data Lineage Graph）**：
  - 可视化展示：原始数据 → 清洗后数据 → 映射后 OMOP 数据
  - 点击任意节点查看该步骤的完整处理日志
- **版本快照管理**：
  - 任意时间点的 OMOP CDM 快照创建
  - 快照对比（diff）
  - 一键回滚到指定快照
- **变更审计日志**：
  - 操作人、操作类型、操作时间、变更前后值
  - 支持按时间/操作人/操作类型过滤检索

#### 3.1.7 数据治理管理
- **数据权限管理**：
  - 医院级数据隔离（A医院只能看A医院数据）
  - 角色权限：管理员、治理员、操作员、查看员
- **审批工作流**：
  - 映射规则生效审批
  - 数据发布到 OMOP 审批
  - 治理规则变更审批
- **数据字典与元数据浏览**：
  - OMOP CDM 表结构说明
  - 字段级业务定义
  - 词汇表搜索（SNOMED / RxNorm / LOINC / ICD 映射）

#### 3.1.8 系统管理
- 用户管理
- 角色与权限配置
- 日志检索
- 系统配置（邮件服务器、告警渠道）
- 任务调度配置（ETL 频率、时间窗口）

---

### 3.2 后端功能

#### 3.2.1 数据接入服务 (Ingestion Service)
- **CSV 解析引擎**：
  - 自动检测分隔符、编码（UTF-8/GBK）、换行符
  - 大文件分块读取（每10万行一批）
  - 字段类型推断（string/int/float/datetime）
  - 错误行隔离（格式错误行存入 error_log，不影响正常行处理）
- **API 轮询引擎**：
  - 可配置 HTTP 客户端（超时、重试、认证）
  - 增量拉取（基于时间戳 / 自增ID / 游标分页）
  - 数据校验（JSON Schema 校验）
  - 幂等性保证（基于 request_id 去重）
- **增量识别**：
  - full load（全量） vs incremental load（增量）
  - 使用 checksum 或 CDC（变更数据捕获） 识别变化行
- **文件归档**：
  - 原始文件存入对象存储（MinIO），路径含数据源ID+批次号+时间戳

#### 3.2.2 数据清洗服务 (Normalization Service)
- **字段级清洗管线**（可配置管道顺序）：
  - 空值处理：丢弃 / 默认值填充 / 均值中位数填充
  - 类型转换：字符串→日期、字符串→数字、编码格式统一
  - 格式归一化：手机号、身份证、性别代码、民族代码统一到国家/行业标准
  - 单位统一：kg↔lb、cm↔inch、mmHg↔kPa
  - 去重策略：基于业务主键（患者ID+就诊号）的去重与合并
  - 异常值过滤：年龄0-120、身高20-250cm、实验室数值3σ/箱线图剔除
- **医疗术语映射**：
  - 医院自定义编码 → 国家标准代码（如医院科室代码→国标科室分类）
  - 诊断名称 → ICD-10 编码映射（基于 NLP + 模糊匹配）
  - 药品名称 → 通用名 + ATC 编码映射
- **数据血缘标记**：
  - 每行数据打上 `source_id`、`batch_id`、`ingestion_timestamp`、`cleaning_rules_applied`

#### 3.2.3 OMOP 映射引擎 (Mapping Engine)
- **Schema Mapping (表结构映射)**：
  - 基于 WhiteRabbit 扫描源数据生成数据字典
  - RabbitInAHat 生成 ETL 骨架
  - 支持 1:1、1:N、N:1 字段映射
  - 支持字段转换函数（CONCAT、SUBSTRING、CASE WHEN、自定义 UDF）
- **Concept Mapping (概念映射)**：
  - 集成 Usagi：源词 → OMOP Concept ID 自动推荐
  - 集成 OHDSI Vocabulary：本地 SQLite/Synonym 表快速匹配
  - 自定义映射规则（正则、查表、条件映射）
  - 多级兜底策略：精确匹配 → 模糊匹配 → 父概念匹配 → 人工标记
- **ETL Template 生成**：
  - 从保存的映射规则自动生成可执行 ETL 脚本（Python/SQL）
  - 支持 ETL 脚本 Dry-Run 模式（预览映射结果，不写入 CDM）

#### 3.2.4 数据质量服务 (Data Quality Service)
- **规则引擎**：
  - 可扩展规则注册机制（插件式）
  - 内置规则库：
    - 完整性：NOT NULL 检查、必填字段检查
    - 唯一性：业务主键唯一性
    - 一致性：概念引用一致性（concept_id 在 concept 表中存在）
    - 合理性：PLAUSIBLE_GENDER、PLAUSIBLE_AGE、PLAUSIBLE_DATES
    - 规范性：日期格式、编码规范、值域范围
  - 规则执行引擎（并行检查，性能可调）
- **OHDSI DataQualityDashboard 集成**：
  - 调用 DQD 生成 OMOP CDM 合规性 JSON 报告
  - 报告解析入库、趋势追踪
- **质量阈值与告警**：
  - 配置质量指标通过阈值（如完整率 ≥ 99%）
  - 不达标时：自动阻止数据写入 CDM / 发送告警通知 / 暂停当前批次

#### 3.2.5 数据治理服务 (Data Governance Service)
- **权限模型**：RBAC（基于角色的访问控制）+ 数据行级权限（多租户隔离）
- **审批引擎**：可配置审批链（如：治理员发起 → 主管审批 → 管理员生效）
- **元数据管理**：
  - 自动采集数据源元数据（表结构、行数、更新时间）
  - 业务术语注册与映射（医院术语 ↔ 标准术语）
- **数据生命周期管理**：
  - 原始数据保留策略（如：保留90天）
  - 历史快照保留策略（如：每周快照，保留52周）

#### 3.2.6 回溯服务 (Traceability Service)
- **数据谱系存储**：
  - 使用 OpenLineage 标准或自定义 lineage 模型
  - 每条 lineage 记录：`input → transformation → output`，附带参数与上下文
  - 存储于 Neo4j（图数据库）+ PostgreSQL 双重持久化
- **版本快照引擎**：
  - 全量快照：基于 PostgreSQL pg_dump / COPY 导出
  - 增量快照：基于 WAL 日志或事件表记录变更
  - 快照元数据管理（创建时间、CDM版本、包含的数据源）
- **审计跟踪**：
  - 数据修改审计（触发器 + audit 表）
  - 操作审计（API 切面日志）
  - 非侵入式设计（不修改现有业务代码逻辑）

#### 3.2.7 调度编排服务 (Orchestration Service)
- **Apache Airflow / Prefect**：
  - DAG 定义：每个数据源/ETL流程为一个 DAG
  - 依赖管理：清洗 → 映射 → 质量检查 → 写入 CDM
  - 失败重试（指数退避）
  - 并行执行（多数据源同时处理）
- **任务监控**：
  - 任务状态追踪（running / success / failed / retrying）
  - 任务耗时统计与性能分析
  - 失败原因自动归类

---

## 四、技术实现方案

### 4.1 前端技术栈

| 技术 | 选型 | 说明 |
|------|------|------|
| 框架 | **React 18 + TypeScript** | 组件化开发，生态丰富 |
| UI 组件库 | **Ant Design Pro** | 企业级中后台组件，表格/表单/流程图开箱即用 |
| 状态管理 | **Zustand + React Query** | 轻量状态 + 服务端缓存/自动刷新 |
| 图表 | **ECharts + D3.js** | 质量仪表盘（ECharts）+ 数据谱系图（D3.js 力导向图） |
| 映射工作台 | **React Flow** | 拖拽式连线编辑器，用于 Source-to-OMOP 映射 |
| 构建工具 | **Vite** | 开发快速，HMR 秒级响应 |
| 国际化 | **react-i18next** | 支持中英文切换（医院方可能需求） |
| API 通信 | **Axios + React Query** | RESTful API 调用 |
| WebSocket | **Socket.IO 客户端** | 实时推送 ETL 状态、告警 |

### 4.2 后端技术栈

| 技术 | 选型 | 说明 |
|------|------|------|
| 语言/框架 | **Python FastAPI** | 高性能异步框架，Pydantic 校验，自动生成 OpenAPI 文档 |
| ORM | **SQLAlchemy 2.0 + Alembic** | 数据库操作与迁移管理 |
| 任务队列 | **Celery + Redis** | 异步任务执行（清洗、映射计算、质量检查） |
| 调度引擎 | **Apache Airflow** | ETL DAG 编排与调度 |
| 消息队列 | **RabbitMQ / Redis PubSub** | 服务间异步通信，事件驱动 |
| 图数据库 | **Neo4j** | 数据谱系存储与查询（Lineage 图遍历） |
| 对象存储 | **MinIO (S3-compatible)** | 原始文件、快照、报告归档 |
| 搜索 | **Elasticsearch** | 词汇表搜索、审计日志检索 |
| API 网关 | **Kong / Nginx + Lua** | 认证、路由、限流 |
| 监控 | **Prometheus + Grafana** | 系统指标监控（CPU/内存/QPS/ETL耗时） |
| 日志 | **ELK (Elasticsearch + Logstash + Kibana)** | 集中日志收集与分析 |

### 4.3 数据库选型

| 数据库 | 用途 | 说明 |
|--------|------|------|
| **PostgreSQL 15+** | OMOP CDM 主库 | 支持 JSONB、分区表、并行查询 |
| **PostgreSQL** | 原始数据暂存区 | 带 version/batch 标记的表结构 |
| **PostgreSQL** | 元数据/管理数据库 | 映射规则、质量基线、配置信息 |
| **SQLite** | OHDSI Vocabulary | 本地词汇表，只读，查询高效 |
| **Neo4j** | Lineage 图存储 | 数据谱系关系高效遍历 |
| **Redis** | 缓存 + 任务队列 | 高频配置缓存，Celery Broker |

### 4.4 OHDSI 工具集成

| OHDSI 工具 | 用途 | 集成方式 |
|-----------|------|----------|
| **WhiteRabbit** | 扫描源数据生成数据字典 | Python 调用白兔 JAR 或解析其输出报告 |
| **RabbitInAHat** | 生成 ETL 设计文档 | 解析其输出 JSON，导入平台映射工作台 |
| **Usagi** | 概念映射自动推荐 | 嵌入 Usagi 核心库（Java→Python 桥接或独立微服务） |
| **ACHILLES** | OMOP 数据特征分析 | 运行其 SQL 脚本，结果入库，前端展示 |
| **DataQualityDashboard** | OMOP 合规性质控 | Python SDK 调用，结果 JSON 解析入库 |
| **ATLAS / WebAPI** | OMOP 词汇浏览（可选） | 集成 WebAPI 的 Concept Search 接口 |
| **OMOP CDM 建表脚本** | 标准 CDM DDL | 直接执行官方 pg_ddl.sql |

### 4.5 数据流向设计（核心 ETL 管线）

```
┌────────────┐   Full/Incremental    ┌────────────┐
│  医院数据源  │ ──────────────────→  │ Raw Zone   │
│ (API/CSV)   │                      │ (版本化存储) │
└────────────┘                      └─────┬──────┘
                                         │
                                    ┌─────▼──────┐
                                    │ 清洗归一化  │
                                    │ ·空值处理   │
                                    │ ·类型转换   │
                                    │ ·编码统一   │
                                    │ ·脏数据清洗  │
                                    └─────┬──────┘
                                         │
                                    ┌─────▼──────┐
                                    │ Staging    │
                                    │ (标准化后)  │
                                    └─────┬──────┘
                                         │
                                    ┌─────▼──────┐
                                    │ OMOP 映射   │
                                    │ ·Schema映射 │
                                    │ ·Concept映射│
                                    │ ·Transforms │
                                    └─────┬──────┘
                                         │
                                    ┌─────▼──────┐
                                    │ 质量检查    │
                                    │ DQD + 自定义 │
                                    └─────┬──────┘
                                         │
                              ┌──────────┴──────────┐
                              │     Pass?            │
                          Yes └──────────┬──────────┘ No
                              ┌─────▼──────┐    ┌──────────────┐
                              │ Write CDM  │    │ 标记异常，    │
                              │ OMOP 主库  │    │ 阻塞写入，通知 │
                              └─────┬──────┘    └──────────────┘
                                    │
                              ┌─────▼──────┐
                              │ ACHILLES   │
                              │ 特征分析    │
                              └────────────┘
```

### 4.6 数据追溯实现

#### 4.6.1 行级追溯
每条原始记录经过 ETL 后在 OMOP 表中存储以下追溯字段：

```sql
-- OMOP 各表统一扩展字段（在CDM标准表外）
omop_source_row_id      VARCHAR(64)   -- 原始行ID（Raw Zone 主键）
source_batch_id         VARCHAR(32)   -- 批次号
ingestion_timestamp     TIMESTAMP     -- 接入时间
cleaning_rules_version  VARCHAR(16)   -- 清洗规则版本
mapping_rules_version   VARCHAR(16)   -- 映射规则版本
etl_job_id              VARCHAR(32)   -- ETL作业ID
```

#### 4.6.2 快照机制
```yaml
快照策略:
  计划快照: 每日凌晨全量快照（pg_dump + 压缩归档到 MinIO）
  按需快照: 用户触发任意时间点快照
  快照保留: 每日快照保留90天，每周快照保留52周
  回滚流程: 选择快照 → 新建临时库 → 恢复快照 → 验证 → 替换主库
```

#### 4.6.3 谱系可视化查询
```cypher
// Neo4j 谱系查询示例：追溯一条 OMOP 记录的全部上游
MATCH (omop:OmopRecord {id: 'OMOP-001'})
<-[:MAPPED_FROM]-(stg:StagingRecord)
<-[:CLEANED_FROM]-(raw:RawRecord)
<-[:EXTRACTED_FROM]-(src:SourceFile)
RETURN src, raw, stg, omop
```

---

## 五、OMOP CDM v5.4 版本策略

### 5.1 版本选择：CDM v5.4

采用 **OMOP CDM v5.4** 作为平台标准版本。v5.4 是目前 OHDSI 社区最广泛部署的生产版本，词汇表成熟，工具链完整。

### 5.2 v5.4 核心表结构

```
┌─────────────────┐    ┌──────────────────────┐
│    Person       │───→│   Observation_Period  │
│   (患者主表)     │    │   (观察期)            │
└────────┬────────┘    └──────────────────────┘
         │
    ┌────┼────────────────────────────────────┐
    │    │                                    │
    ▼    ▼            ▼            ▼           ▼
┌──────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐
│Visit     │ │Condition   │ │Drug_Exposure│ │Procedure │
│Occurrence│ │Occurrence  │ │(药品暴露)   │ │Occurrence│
│(就诊)    │ │(诊断)      │ │            │ │(手术)    │
└────┬─────┘ └─────┬──────┘ └─────┬──────┘ └────┬─────┘
     │              │              │             │
     ▼              ▼              ▼             ▼
┌──────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐
│Measurement│ │Observation │ │Device      │ │Note      │
│(检验检查) │ │(观察)      │ │Exposure    │ │(病历)    │
└──────────┘ └────────────┘ └────────────┘ └──────────┘

┌──────────────────┐     ┌──────────────────┐
│   Location       │     │   Care_Site      │
│   (机构地址)      │────→│   (科室/院区)     │
└──────────────────┘     └────────┬─────────┘
                                  │
                                  ▼
                          ┌─────────────────┐
                          │   Provider       │
                          │   (医护人员)     │
                          └─────────────────┘

┌──────────────────┐     ┌──────────────────┐
│   Cost           │     │   Payer_Plan     │
│   (费用明细)      │     │   Period         │
└──────────────────┘     │   (医保/商保)     │
                          └──────────────────┘
```

### 5.3 v5.4 各表关键字段速查

| 表名 | 核心字段 | 典型行数/患者 |
|------|---------|-------------|
| **person** | person_id, gender_concept_id, year_of_birth, race_concept_id, ethnicity_concept_id, location_id | 1 行/患者 |
| **observation_period** | observation_period_id, person_id, observation_period_start_date, observation_period_end_date, period_type_concept_id | 1-3 行/患者 |
| **visit_occurrence** | visit_occurrence_id, person_id, visit_concept_id, visit_start_date, visit_end_date, visit_type_concept_id, provider_id, care_site_id | 10-50 行/患者/年 |
| **condition_occurrence** | condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_end_date, visit_occurrence_id, condition_type_concept_id | 20-100 行/患者/年 |
| **drug_exposure** | drug_exposure_id, person_id, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date, drug_type_concept_id, quantity, visit_occurrence_id | 30-200 行/患者/年 |
| **procedure_occurrence** | procedure_occurrence_id, person_id, procedure_concept_id, procedure_date, procedure_type_concept_id, visit_occurrence_id | 10-50 行/患者/年 |
| **measurement** | measurement_id, person_id, measurement_concept_id, measurement_date, measurement_type_concept_id, value_as_number, value_as_concept_id, unit_concept_id, visit_occurrence_id | 50-500 行/患者/年 |
| **observation** | observation_id, person_id, observation_concept_id, observation_date, observation_type_concept_id, value_as_string, value_as_concept_id, visit_occurrence_id | 10-100 行/患者/年 |
| **note** | note_id, person_id, note_date, note_type_concept_id, note_text, visit_occurrence_id | 2-10 行/患者/年 |
| **device_exposure** | device_exposure_id, person_id, device_concept_id, device_exposure_start_date, device_exposure_end_date, device_type_concept_id | 0-5 行/患者/年 |
| **death** | person_id, death_date, death_type_concept_id, cause_concept_id | 0-1 行/患者 |
| **location** | location_id, address_1, city, state, zip, country_concept_id | 1 行/地址 |
| **care_site** | care_site_id, place_of_service_concept_id, location_id | 1 行/科室 |
| **provider** | provider_id, provider_name, specialty_concept_id, gender_concept_id | 1 行/医护人员 |

### 5.4 词汇表策略

| 词汇表 | 来源 | 用途 |
|--------|------|------|
| **SNOMED** 临床术语 | OHDSI Athena 导入 | 诊断、体征、手术概念映射终点 |
| **RxNorm / RxNorm Extension** | OHDSI Athena 导入 | 药品概念映射终点 |
| **LOINC** | OHDSI Athena 导入 | 检验检查项目概念映射终点 |
| **ICD-10-CM** (作为 Source) | 国家卫健委标准 | 医院诊断编码的中间映射源 |
| **ICD-9-CM** (作为 Source) | OHDSI Athena 导入 | 历史数据兼容 |
| **ATC** | WHO 药物分类 | 药品分类映射参考 |
| **国内映射扩展** | 自定义构建 | ICD-10 → SNOMED、医院自定义编码 → 标准概念的本地映射表 |

> **词汇表更新策略**：每季度同步 OHDSI Athena 最新版本，更新前备份当前词汇表，新旧版本对比生成影响分析报告（哪些映射需要重新校验）。

### 5.5 版本升级迁移方案

| 场景 | 策略 |
|------|------|
| **v5.3 → v5.4** | 增量变更（v5.4 新增了 visit_detail、note_nlp、metadata 等表），直接加表+加字段，无需重建已有数据 |
| **v5.4 → v6.0（未来）** | 等待 OHDSI 发布正式迁移脚本，平台预留 CDMSchemaVersion 元数据表记录当前版本 |
| **多版本兼容** | 不承诺多版本并行，平台运行单一 CDM 版本，数据导出时可做降级转换 |

---

## 六、医院数据对接协议标准

### 6.1 总体原则

- **标准化输入**：无论医院内部格式如何，对接前定义标准数据契约（Data Contract）
- **渐进式适配**：医院数据先按最低要求标准接入，后续逐步增补字段
- **编码预映射**：医院需提供编码字典（科室代码、诊断代码、药品代码），平台协助映射到国家标准/OMOP概念

### 6.2 必填字段标准（Minimum Data Set）

#### 6.2.1 患者主数据（Person）

| # | 字段名 | 类型 | 必填 | 说明 | 编码标准 |
|---|--------|------|------|------|----------|
| 1 | patient_id | VARCHAR(64) | ✅ | 患者唯一标识（院内ID） | 原始ID，平台加前缀做全局唯一 |
| 2 | gender | VARCHAR(2) | ✅ | 性别 | 0=未知, 1=男, 2=女, 9=未说明（国家卫生信息数据标准） |
| 3 | birth_date | DATE | ✅ | 出生日期 | YYYY-MM-DD |
| 4 | race | VARCHAR(16) |    | 种族（可选） | 参考国家标准 |
| 5 | ethnicity | VARCHAR(16) |    | 民族（可选） | 56个民族代码 GB 3304 |
| 6 | death_date | DATE |    | 死亡日期（如有） | YYYY-MM-DD |

#### 6.2.2 就诊记录（Visit Occurrence）

| # | 字段名 | 类型 | 必填 | 说明 |
|---|--------|------|------|------|
| 1 | visit_id | VARCHAR(64) | ✅ | 就诊唯一标识 |
| 2 | patient_id | VARCHAR(64) | ✅ | 患者ID（关联person） |
| 3 | visit_type | VARCHAR(16) | ✅ | 就诊类型：门诊/住院/急诊/体检 |
| 4 | visit_start_time | DATETIME | ✅ | 就诊开始时间 |
| 5 | visit_end_time | DATETIME |    | 就诊结束时间 |
| 6 | department_code | VARCHAR(32) | ✅ | 科室代码（医院原始编码） |
| 7 | discharge_code | VARCHAR(8) |    | 离院方式（出院转归） |
| 8 | admit_source | VARCHAR(8) |    | 入院来源（门诊/急诊/转院） |

#### 6.2.3 诊断记录（Condition Occurrence）

| # | 字段名 | 类型 | 必填 | 说明 |
|---|--------|------|------|------|
| 1 | condition_id | VARCHAR(64) | ✅ | 诊断唯一标识 |
| 2 | patient_id | VARCHAR(64) | ✅ | 患者ID |
| 3 | condition_code | VARCHAR(32) | ✅ | 诊断编码（医院原始编码） |
| 4 | condition_name | VARCHAR(256) | ✅ | 诊断名称（中文原文） |
| 5 | condition_type | VARCHAR(16) | ✅ | 诊断类型：入院诊断/出院诊断/门诊诊断 |
| 6 | coding_system | VARCHAR(16) | ✅ | 编码体系：ICD-10 / ICD-9 / 院内自定义 |
| 7 | condition_date | DATE | ✅ | 诊断日期 |
| 8 | visit_id | VARCHAR(64) |    | 关联就诊ID |

#### 6.2.4 药品记录（Drug Exposure）

| # | 字段名 | 类型 | 必填 | 说明 |
|---|--------|------|------|------|
| 1 | drug_id | VARCHAR(64) | ✅ | 用药记录唯一标识 |
| 2 | patient_id | VARCHAR(64) | ✅ | 患者ID |
| 3 | drug_code | VARCHAR(32) | ✅ | 药品编码（医院原始编码） |
| 4 | drug_name | VARCHAR(256) | ✅ | 药品名称（中文通用名优先） |
| 5 | drug_type | VARCHAR(16) | ✅ | 用药类型：医嘱/执行/出院带药 |
| 6 | start_date | DATE | ✅ | 用药开始日期 |
| 7 | end_date | DATE |    | 用药结束日期 |
| 8 | dosage | DECIMAL(12,2) |    | 单次剂量 |
| 9 | dosage_unit | VARCHAR(16) |    | 剂量单位：mg/g/ml/片 |
| 10 | frequency | VARCHAR(32) |    | 用药频率：qd/bid/tid |
| 11 | route | VARCHAR(32) |    | 给药途径：口服/静脉/肌肉 |
| 12 | quantity | DECIMAL(12,2) |    | 用药总量 |
| 13 | visit_id | VARCHAR(64) | ✅ | 关联就诊ID |

#### 6.2.5 检验检查记录（Measurement）

| # | 字段名 | 类型 | 必填 | 说明 |
|---|--------|------|------|------|
| 1 | measurement_id | VARCHAR(64) | ✅ | 检验检查唯一标识 |
| 2 | patient_id | VARCHAR(64) | ✅ | 患者ID |
| 3 | test_code | VARCHAR(32) | ✅ | 检验项目编码（医院原始编码） |
| 4 | test_name | VARCHAR(256) | ✅ | 检验项目名称 |
| 5 | measurement_date | DATETIME | ✅ | 检验日期 |
| 6 | result_value | VARCHAR(64) |    | 检验结果值（数值即填数值，文本即填文本） |
| 7 | result_unit | VARCHAR(16) |    | 检验结果单位 |
| 8 | result_flag | VARCHAR(8) |    | 异常标志：N/L/H/LL/HH |
| 9 | ref_range_low | VARCHAR(16) |    | 参考范围下限 |
| 10 | ref_range_high | VARCHAR(16) |    | 参考范围上限 |
| 11 | visit_id | VARCHAR(64) | ✅ | 关联就诊ID |

#### 6.2.6 手术记录（Procedure Occurrence）

| # | 字段名 | 类型 | 必填 | 说明 |
|---|--------|------|------|------|
| 1 | procedure_id | VARCHAR(64) | ✅ | 手术唯一标识 |
| 2 | patient_id | VARCHAR(64) | ✅ | 患者ID |
| 3 | procedure_code | VARCHAR(32) | ✅ | 手术编码（医院原始编码） |
| 4 | procedure_name | VARCHAR(256) | ✅ | 手术名称 |
| 5 | procedure_date | DATE | ✅ | 手术日期 |
| 6 | coding_system | VARCHAR(16) | ✅ | 编码体系：ICD-9-CM-3 / 院内自定义 |
| 7 | visit_id | VARCHAR(64) | ✅ | 关联就诊ID |

### 6.3 编码标准映射规范

```
┌─────────────────────────────────────────────────────────────────┐
│                    编码标准化管线                                │
│                                                                 │
│  医院原始编码  →  国家标准编码  →  OMOP Concept ID               │
│                                                                 │
│  性别: 0/1        →  GB/T 2261.1  →  gender_concept_id         │
│  诊断: ICD-10     →  SNOMED       →  condition_concept_id      │
│  药品: 院内药品码   →  ATC/通用名   →  drug_concept_id          │
│  检验: 院内项目码   →  LOINC        →  measurement_concept_id   │
│  手术: ICD-9-CM-3 →  SNOMED       →  procedure_concept_id      │
│  科室: 院内科室码   →  国标科室分类  →  care_site_id            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.4 数据格式要求

| 项目 | 要求 |
|------|------|
| **CSV 编码** | UTF-8（带 BOM） |
| **日期格式** | YYYY-MM-DD（ISO 8601） |
| **时间格式** | YYYY-MM-DD HH:mm:ss |
| **小数格式** | 小数点 `.`，禁止千分位逗号 |
| **空值表示** | 留空（空单元格），禁止填 "NULL" / "N/A" / "-" |
| **文件命名** | `{hospital_code}_{table_name}_{batch_date}.csv` |
| **API 响应格式** | JSON（标准 RESTful），分页参数 `page`/`page_size` |
| **API 增量字段** | 必须提供 `update_time` 或 `modified_at` 时间戳字段 |

---

## 七、隐私合规与脱敏方案

### 7.1 合规框架：双标准并行

本平台同时遵循《中华人民共和国个人信息保护法》（PIPL）和 HIPAA（美国健康保险可携性和责任法案），以 PIPL 为主（中国医院），以 HIPAA 为参考增强。

| 合规维度 | PIPL 要求 | HIPAA 要求 | 平台实现 |
|---------|-----------|------------|---------|
| **知情同意** | 处理个人信息需取得个人同意 | 患者授权同意 | 医院负责在数据导出前取得患者知情同意，平台记录授权证明引用 |
| **最小必要** | 仅收集实现目的的最少个人信息 | 最小必要原则（Minimum Necessary） | 平台提供字段级选择性接入，默认只接必需字段 |
| **去标识化** | 匿名化(不可逆) / 去标识化(可逆) | 去标识化(De-identification) / 有限数据集(Limited Dataset) | 支持两种模式（见下方） |
| **数据安全** | 加密存储、访问控制 | 管理、物理、技术三重保障 | 静态加密 + TLS + RBAC |
| **数据留存** | 处理目的达成后删除 | 6年保留期（HIPAA） | 可配置生命周期策略 |
| **跨境传输** | 安全评估 / 备案 | 合规合同（BAAs） | 数据不出医院内网（私有化部署） |
| **泄露通知** | 72小时内通知 | 60天内通知 | 自动告警 + 审计日志 |
| **数据主体权利** | 查阅/复制/更正/删除 | 查阅/更正/披露记录 | 提供数据主体请求处理模块 |

### 7.2 脱敏分级策略

#### 7.2.1 三级脱敏标准

| 级别 | 名称 | 适用场景 | 脱敏程度 |
|------|------|----------|----------|
| **L1** | 匿名化 | 科研/统计/对外发布 | 完全不可逆，所有标识符移除或扰动 |
| **L2** | 去标识化 | OMOP CDM 分析/内部研究 | 直接标识符移除/加密，准标识符泛化 |
| **L3** | 原始级 | ETL 内部中间处理 | 原始数据仅在内存中处理，落盘即脱敏 |

#### 7.2.2 字段级脱敏规则

| 字段类别 | 示例字段 | L1 匿名化 | L2 去标识化 | L3 原始级 |
|---------|---------|-----------|-------------|-----------|
| **直接标识符** | 姓名、身份证号、手机号、住址 | ❌ 移除(Remove) | ✅ 不可逆哈希+遮盖(HashMask) | ✅ 可逆加密(EncryptAES) |
| **准标识符** | 出生日期、性别、民族、邮编 | ✅ K-匿名泛化(仅保年份/区级) | ✅ 泛化(保年月) | ✅ 原始保留 |
| **医疗信息** | 诊断、用药、检验结果 | ✅ 保留(科研必须) | ✅ 保留 | ✅ 保留 |
| **元数据** | 科室、医生、设备号 | ✅ 泛化/编码覆盖 | ✅ 编码覆盖 | ✅ 保留 |
| **时间戳** | 就诊时间、住院时长 | ✅ 偏移扰动(±7天) | ✅ 保留日期，模糊时间 | ✅ 完全保留 |

### 7.3 脱敏技术实现

#### 7.3.1 脱敏管线位置

```
原始接入 → [脱敏引擎] → 清洗归一化 → 映射 → OMOP CDM（L2级别）
                ↑
   脱敏规则配置（前端配置，运行时可调整）
```

脱敏在**数据接入后、清洗前**执行，确保后续所有处理环节接触的已脱敏数据。

#### 7.3.2 脱敏算法库

| 算法 | 用途 | 实现方式 |
|------|------|----------|
| **AES-256-GCM** | 可逆字段加密（姓名、身份证） | Python `cryptography` 库，密钥由 KMS 管理 |
| **SHA-256 + 盐值** | 不可逆哈希（用于 Patient ID 做假名化） | 每医院不同盐值，防彩虹表 |
| **K-匿名 (Mondrian)** | 准标识符泛化（出生日期→年份、邮编→前3位） | 开源 ARX 工具库嵌入 |
| **日期偏移** | 就诊日期扰动（±N天，保持周内/月内分布） | 自定义算法，每患者固定偏移量 |
| **遮盖 (Masking)** | 手机号 `138****1234`、身份证 `110101********1234` | 正则匹配 + 替换 |
| **令牌化 (Tokenization)** | Patient ID 替换为不可逆 Token | 查找表（Token ↔ 原始ID 单独存储） |

### 7.4 数据分级与访问控制

```yaml
数据分级:
  C4-极敏感: 直接标识符（姓名、身份证、联系方式）
    → 仅系统管理员可访问，全部加密存储，接口默认不返回

  C3-敏感: 准标识符（出生日期、邮编、罕见病诊断）
    → 治理员+授权分析人员可访问，接口需二次授权

  C2-内部: 医疗数据（诊断、用药、检验）
    → 所有授权用户可访问，用于科研分析

  C1-公开: 元数据（科室列表、词汇表）
    → 全员可访问
```

### 7.5 隐私审计

- 每笔数据查询/导出记录日志（谁、什么时间、查了什么数据、多少条）
- 脱敏处理操作日志（脱敏级别、算法参数、处理时间）
- 数据导出审批流程（导出 L2 及以下自动审批，L1 需人工审批）
- 定期隐私合规自检报告（季度生成）

---

## 八、部署架构 — Docker 容器化

### 8.1 总体架构

```
┌─────────────────────────────────────────────────────────────┐
│                  Docker Host / Swarm 集群                      │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐   │
│  │                  docker-compose.yml                    │   │
│  │                                                       │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐          │   │
│  │  │ frontend  │ │  backend  │ │  celery   │          │   │
│  │  │ nginx:1.25│ │ fastapi   │ │ worker:N  │          │   │
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘          │   │
│  │        │             │              │                 │   │
│  │  ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐          │   │
│  │  │ frontend  │ │ backend   │ │ celery    │          │   │
│  │  │ (React)   │ │ (FastAPI) │ │ workers   │          │   │
│  │  └───────────┘ └───────────┘ └───────────┘          │   │
│  │                                                       │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐          │   │
│  │  │ airflow   │ │  redis    │ │  minio    │          │   │
│  │  │ scheduler │ │ 7.x       │ │ obj store │          │   │
│  │  └─────┬─────┘ └─────┬─────┘ └─────┬─────┘          │   │
│  │        │             │              │                 │   │
│  │  ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐          │   │
│  │  │ airflow   │ │  redis    │ │  minio    │          │   │
│  │  │ web+worker│ │ broker    │ │ (S3 API)  │          │   │
│  │  └───────────┘ └───────────┘ └───────────┘          │   │
│  │                                                       │   │
│  │  ┌───────────┐ ┌───────────┐ ┌───────────┐          │   │
│  │  │ postgres  │ │  neo4j    │ │  es       │          │   │
│  │  │ 15 (OMOP) │ │ 5.x       │ │ kibana    │          │   │
│  │  └───────────┘ └───────────┘ └───────────┘          │   │
│  │                                                       │   │
│  │  ┌─────────────────────────────────────────────────┐ │   │
│  │  │               docker network: omop-net           │ │   │
│  │  │         (bridge, internal communication)         │ │   │
│  │  └─────────────────────────────────────────────────┘ │   │
│  └───────────────────────────────────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 8.2 Docker Compose 服务清单

| 服务 | 镜像 | CPU | 内存 | 存储 | 副本数 |
|------|------|-----|------|------|--------|
| **frontend** | nginx:1.25-alpine (服务 React 静态文件) | 0.5 | 512MB | - | 1-2 |
| **backend-api** | python:3.11-slim (FastAPI + Gunicorn) | 2 | 4GB | - | 2-4 |
| **celery-worker** | python:3.11-slim (Celery workers) | 4 | 8GB | - | 2-4 |
| **airflow-scheduler** | apache/airflow:2.8 | 1 | 2GB | - | 1 |
| **airflow-worker** | apache/airflow:2.8 | 2 | 4GB | - | 2 |
| **airflow-webserver** | apache/airflow:2.8 | 0.5 | 1GB | - | 1 |
| **postgres-omop** | postgres:15 | 4 | 16GB | 200GB SSD | 1+同步备 |
| **postgres-meta** | postgres:15 | 1 | 4GB | 50GB SSD | 1 |
| **neo4j** | neo4j:5-enterprise | 2 | 4GB | 50GB SSD | 1 |
| **redis** | redis:7-alpine | 1 | 2GB | - | 1 |
| **minio** | minio/minio:latest | 2 | 4GB | 500GB | 2 (分布式) |
| **elasticsearch** | elasticsearch:8.11 | 2 | 8GB | 100GB SSD | 1 |
| **kibana** | kibana:8.11 | 0.5 | 1GB | - | 1 |

> **总计估算**：CPU ~20核，内存 ~60GB，存储 ~900GB（含数据冗余）

### 8.3 关键配置示例

```yaml
# docker-compose.yml 核心片段
version: '3.8'

services:
  postgres-omop:
    image: postgres:15
    environment:
      POSTGRES_DB: omop_cdm
      POSTGRES_USER: omop_user
      POSTGRES_PASSWORD: ${OMOP_DB_PASSWORD}
    volumes:
      - pg_omop_data:/var/lib/postgresql/data
      - ./sql/cdm_v54_ddl.sql:/docker-entrypoint-initdb.d/01_cdm.sql:ro
      - ./sql/vocab_ddl.sql:/docker-entrypoint-initdb.d/02_vocab.sql:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U omop_user -d omop_cdm"]
      interval: 10s
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 16G
    networks:
      - omop-net

  backend-api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://omop_user:${OMOP_DB_PASSWORD}@postgres-omop:5432/omop_cdm
      REDIS_URL: redis://redis:6379/0
      MINIO_ENDPOINT: minio:9000
      MINIO_ACCESS_KEY: ${MINIO_ACCESS_KEY}
      MINIO_SECRET_KEY: ${MINIO_SECRET_KEY}
      AIRFLOW_API_URL: http://airflow-webserver:8080/api/v1
    depends_on:
      postgres-omop:
        condition: service_healthy
      redis:
        condition: service_started
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '2'
          memory: 4G
    networks:
      - omop-net

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    volumes:
      - minio_data:/data
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD}
    ports:
      - "9000:9000"   # S3 API
      - "9001:9001"   # Console
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
    networks:
      - omop-net

volumes:
  pg_omop_data:
    driver: local
  minio_data:
    driver: local

networks:
  omop-net:
    driver: bridge
```

### 8.4 容器化最佳实践

| 实践 | 说明 |
|------|------|
| **健康检查** | 所有服务配置 healthcheck，依赖用 `condition: service_healthy` |
| **日志** | 各服务日志 → stdout → Docker 日志驱动，最终由 Filebeat 采集到 ELK |
| **密钥管理** | 密码/密钥通过环境变量注入，生产环境使用 Docker Secrets 或 Vault |
| **镜像构建** | 多阶段构建（builder pattern），最终镜像 < 200MB |
| **持久化** | 所有数据库/中间件数据通过 named volume 持久化 |
| **网络隔离** | 前端通过 Nginx 暴露 80/443，后端服务仅在内部 omop-net 互通 |
| **零停机部署** | backend-api 多副本 + rolling update，数据库通过 pg_rewind 做切换 |
| **资源限制** | 每个服务设置 `deploy.resources.limits`，防止单服务占满主机 |

---

## 九、性能与容量规划

### 9.1 容量假设

| 参数 | 值 | 说明 |
|------|-----|------|
| 数据总量 | **500 GB** | 单次传输/批次的总数据量（原始 CSV + JSON） |
| 并发接入 | **1000** | 同时处理的 API 请求或 CSV 批次数 |
| 医院规模 | 10-30 家三甲医院 | 每家日均产生 5-50 GB 医疗数据 |
| 患者数 | 约 500 万 ~ 2000 万 | 覆盖患者总量 |
| 日均增量 | 5-10 GB | 每日新增数据 |
| OMOP 数据膨胀比 | 1:1.2 ~ 1:1.5 | 原始数据 → OMOP CDM 后数据量增大（多表关联 + 标准化） |
| 查询并发 | 50-200 | 同时查询 OMOP CDM 的用户/API 请求 |

### 9.2 各环节吞吐量计算

| 环节 | 目标吞吐量 | 瓶颈分析 | 扩容方案 |
|------|-----------|----------|----------|
| **数据接入** | 500 GB / 4h = **35 MB/s** | 网络带宽、CSV 解析 CPU | 横向扩展 celery worker |
| **清洗归一化** | 35 MB/s 输入 | CPU（正则/NLP/单位转换） | 每 worker 处理 10MB/s，4 worker 即可 |
| **OMOP 映射** | 1M concepts/hour | 词汇表查询 I/O | SQLite 词汇表放内存（ramdisk） |
| **质量检查** | 500 GB / 6h | DQD 全表扫描 I/O | 分区表 + 并行扫描 |
| **CDM 写入** | 5000 rows/s | PostgreSQL 写入性能 | 批量 INSERT + 异步写入 + 关闭实时索引 |
| **CDM 查询** | 200 QPS @ <500ms | 查询复杂度、索引命中 | 物化视图 + 查询路由 + 只读副本 |

### 9.3 并行处理架构

```
                    ┌──────────────────┐
                    │   API Gateway    │
                    │  (负载均衡1000并发) │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
        │ Worker-01 │ │ Worker-02 │ │ Worker-N  │
        │ 处理医院A  │ │ 处理医院B  │ │ 处理医院X  │
        └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
              │              │              │
        ┌─────▼──────────────▼──────────────▼─────┐
        │           PostgreSQL 连接池             │
        │    max_connections=200 + PgBouncer      │
        │    + 连接复用(连接池1000请求复用200连接)  │
        └────────────────┬───────────────────────┘
                         │
              ┌──────────▼──────────┐
              │  OMOP CDM 主库      │
              │  (分区表 + 并行查询)  │
              └─────────────────────┘
```

### 9.4 数据库优化策略

| 策略 | 说明 |
|------|------|
| **表分区** | person 按 birth_year 分区；visit_occurrence、condition_occurrence 按日期范围分区（月/季分区） |
| **索引策略** | 主键索引 + 外键索引 + 常用查询条件索引（person_id、visit_date、concept_id）；避免冗余索引 |
| **批量写入** | 每 1000 行一个 batch INSERT，禁用 autocommit |
| **连接池** | PgBouncer 做事务级连接池，1000 并发复用 200 个 DB 连接 |
| **并行查询** | PostgreSQL 16 的并行查询（parallel query workers） |
| **物化视图** | 常用统计查询（ACHILLES 基础指标）创建物化视图，每小时刷新 |
| **异步写入** | OMOP ETL 写入时先写 WAL→内存→定期刷盘（synchronous_commit=off），降低写入延迟 |
| **只读副本** | 查询负载高时增加 1-2 个流复制只读副本，读写分离 |

### 9.5 水平扩容方案

```yaml
轻量负载（< 200GB/批次）:
  - 单机 Docker Compose（一台 32核/128GB/2TB SSD 主机）
  - Celery worker: 4 个
  - 无需读写分离

中等负载（200-500GB/批次）:
  - 3 节点 Docker Swarm 集群
  - Celery worker: 8-12 个（分布在 3 节点）
  - PostgreSQL 主备 + PgBouncer
  - MinIO 分布式（2 节点）

高负载（> 500GB/批次，1000 并发）:
  - 5+ 节点 Swarm/K8s 集群
  - Celery worker: 16-24 个
  - PostgreSQL: 主 + 2 只读副本 + PgBouncer + 分区表
  - ES 集群: 3 节点
  - MinIO 分布式: 4 节点
```

### 9.6 网络带宽要求

| 场景 | 带宽需求 |
|------|----------|
| 单批次 500GB / 4h | 500 GB × 8 / (4 × 3600) ≈ **278 Mbps** |
| 并发 1000 请求（平均 500KB/请求） | 1000 × 500KB × 8 / 1s ≈ **4 Gbps**（峰值） |
| 推荐内网配置 | **10 Gbps 内网**（万兆网），外网 1 Gbps |

---

## 十、开放平台 API 设计（补充）

### 10.1 外部 API 清单

| 接口 | 用途 | 认证 |
|------|------|------|
| `GET /api/v1/omop/person/{id}` | 查询患者 OMOP 数据 | API Key |
| `GET /api/v1/omop/visit?person_id=` | 查询就诊 OMOP 数据 | API Key |
| `GET /api/v1/quality/dashboard` | 获取质量看板数据 | JWT |
| `GET /api/v1/vocabulary/search?q=` | 搜索 OMOP 词汇表 | 公开 |
| `POST /api/v1/ingestion/push` | 医院主动推送数据 | 医院专属 HMAC |
| `GET /api/v1/dictionary/{table}` | 获取数据字典 | JWT |
| `GET /api/v1/lineage/record/{id}` | 追溯单条 OMOP 记录 | JWT |

---

## 十一、补充：需要进一步规划设计的事项

### 11.1 🟡 中优先级

| 补充项 | 理由 |
|--------|------|
| **NLP 辅助映射** | 诊断文本→ICD-10、药品名称→ATC 的 NLP 模型训练方案，可用 BioBERT / 医疗大模型辅助 |
| **映射冲突管理** | 同一源词在不同医院映射到不同概念时的冲突检测与解决策略 |
| **数据字典同步机制** | 医院端数据字典变更（新增字段、修改编码）时平台的感知与自动适配机制 |
| **灾备方案** | 主备切换、跨机房容灾、数据备份恢复演练 |
| **国际化支持** | 虽然目前面向国内医院，但 OMOP 本身是国际标准，词汇表包含多语言，前端是否需要英文版？ |

### 11.2 🟢 低优先级 — 未来扩展

| 补充项 | 理由 |
|--------|------|
| **实时数据接入** | 当前设计是批量 ETL，未来是否需要 Kafka / Flink 实现准实时 CDC 接入？ |
| **自然语言查询** | 治理人员用自然语言查询数据 → 自动生成 SQL |
| **AI 辅助映射** | 使用大语言模型辅助 Source-to-OMOP 映射推荐 |
| **多 OMOP 实例管理** | 一个平台管理多个 OMOP CDM 实例（跨院区、跨集团） |
| **行业报告自动生成** | 基于 ACHILLES 结果自动生成医疗机构的数据质量月度报告 |
| **知识图谱扩展** | 在 OMOP 之上构建疾病-药物-手术关联知识图谱 |

---

## 十二、推荐实施路线图

### 12.1 分阶段实施计划

| 阶段 | 时间 | 交付内容 | 关键里程碑 |
|------|------|----------|-----------|
| **P0 - 核心 MVP** ✅ | 1-2 月 | 单数据源 CSV 接入 + 基础清洗 + 固定映射 + 写入 CDM + 简单验证 | 第一个医院数据完整走通 ETL |
| **P1 - 平台化** 🔄 | 3-4 月 | 多数据源管理 + API 接入 + 可视化映射工作台 + Airflow 编排 + 质量检查 | 平台上线，3家医院接入 |
| **P2 - 质量与治理** 🛡️ | 5-6 月 | ACHILLES/DQD 集成 + 数据谱系 + 脱敏管线 + 权限管理 + 告警通知 + Docker 部署 | 质量达标阻断，谱系可视化 |
| **P3 - 智能化与扩展** 🚀 | 7-9 月 | NLP 辅助映射 + 快照管理 + 版本回滚 + 开放 API + 隐私合规 + 多医院治理 | 10家医院运行，合规达标 |

### 12.2 P0 MVP 详细里程碑

```
Week 1-2: 环境搭建
├── Docker Compose 基础编排（PostgreSQL + MinIO + Redis）
├── OHDSI Vocabulary 本地导入
├── OMOP CDM v5.4 DDL 执行
├── React 前端脚手架（Ant Design Pro）
└── FastAPI 后端脚手架

Week 3-4: CSV 接入管线
├── CSV 解析引擎（自动分隔符/编码检测）
├── 原始数据存入 MinIO + Raw Zone PostgreSQL
├── 数据预览前端（表格渲染）
└── 数据源管理前端（添加/测试连接）

Week 5-6: 清洗 + 固定映射
├── 字段级清洗管线（空值/类型/格式）
├── 一套固定映射规则（Person + Visit + Condition）
├── ETL 脚本生成 + Airflow DAG 运行
└── 写入 OMOP CDM 验证

Week 7-8: 基础验证 + 质量
├── 基础质量检查（完整性/唯一性）
├── 质量报告前端
├── 数据回溯：行级血缘标记
└── 端到端验收测试
```

---

## 十三、前端页面路由设计（参考）

```
/login                             登录页
/dashboard                         总览仪表盘
/datasources                       数据源列表
/datasources/:id                   数据源详情（预览、配置、日志）
/datasources/:id/schema            数据结构扫描结果
/ingestion/batches                 接入批次列表
/ingestion/batches/:id             批次详情
/mapping                           映射概览（覆盖率、待确认）
/mapping/source-to-omop/:tableId   表级映射编辑（Schema Mapping）
/mapping/concept/:sourceCode       概念映射编辑（Concept Mapping）
/quality/dashboard                 质量仪表盘
/quality/rules                     质量规则管理
/quality/reports/:batchId          批次质量报告
/quality/achilles                  ACHILLES 报告
/lineage/search                    数据谱系查询
/lineance/record/:id               单条记录谱系图
/governance/approvals              审批管理
/governance/users                  用户管理
/governance/roles                  角色管理
/system/config                     系统配置
/system/dictionary                 数据字典浏览
/system/logs                       操作审计日志
```

---

> **说明**：本文档为顶层产品设计，后续可基于此撰写技术设计文档（TDD）、数据库详细设计、API 设计文档（OpenAPI 3.0）、前端组件设计（Storybook）等。