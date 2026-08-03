# MedA 平台底座设计文档

> 设计日期：2026-08-03
> 设计范围：Hermes 继承式底座
> 适用阶段：平台底座设计确认

## 1. 设计目标

本设计文档用于定义 MedA 科研全流程 AI-Agent 系统的第一阶段平台底座方案。底座采用 `Hermes` 继承式路线，在保留 `hermes-agent-main`、`hermes-web-ui-main`、`hermes-desktop-0.4.5` 既有分层思路的前提下，补齐科研项目制、双端一致性、管理员后台、审计追溯、部署与测试基线等核心能力。

本阶段不直接展开 11 个科研模块的详细实现，而是先把后续模块赖以运行的统一工程边界、统一业务骨架和统一运行时约束确定下来。

## 2. 已确认设计决策

- 第一份设计确认对象为平台底座
- C/S 客户端按 Electron 形态纳入底座设计
- 参考系统 `Hermes` 采用源码继承策略
- 双端以统一后端和统一协议为准，不允许各自派生业务真相源
- 科研能力以后端挂载模块方式接入，不直接散落在端侧页面逻辑中

## 3. 总体设计原则

- 共享后端优先：所有业务真相源统一沉到后端
- 双端一致优先：Web 和 Desktop 只区分宿主能力，不区分业务规则
- 项目制优先：科研业务围绕项目、任务、产物组织，不围绕聊天记录组织
- 可追溯优先：文件、知识、产物、审计必须可回链
- 模块化优先：科研模块以标准能力挂载到 Agent 编排内核
- 受控写入优先：关键科研数据和正式产物必须带权限、审计、版本控制

## 4. 工程拓扑与系统边界

### 4.1 工程分层

平台底座采用“共享内核 + 双端壳层 + 科研扩展”结构：

1. `agent core`
   基于 `D:\workspace\hermes\hermes-agent-main` 演进，负责 Agent runtime、任务编排、工具调用、会话状态、事件流转、插件机制。
2. `web shell`
   基于 `D:\workspace\hermes\hermes-web-ui-main` 演进，负责浏览器端工作台、项目视图、会话视图、知识库视图与管理入口。
3. `desktop shell`
   基于 `D:\workspace\hermes\hermes-desktop-0.4.5` 演进，作为 Electron 客户端外壳，尽量复用 Web 端 UI 与状态逻辑。
4. `admin console`
   新增独立管理员后台，共用统一身份、权限与审计能力。
5. `research domain modules`
   R004-R016 等科研模块作为后端领域模块挂载到核心引擎。

### 4.2 系统边界

`Hermes` 继承范围：

- Agent runtime
- Web UI 框架
- Electron 壳层
- 会话、工作区、插件模式
- 可复用部署脚本

`MedA` 新增范围：

- 科研项目模型
- 文献、方案、样本量、eCRF、数据管理、SAP、CSR 业务能力
- 管理员后台
- 审计、合规、版本追踪增强

硬性边界：

- 业务规则不得下沉到 Electron 或 Web 专属层
- 功能定义以后端 API 和事件协议为准
- 双端不得产生彼此独立的业务逻辑分叉

### 4.3 推荐目录形态

```text
apps/
  agent-core/
  web/
  desktop/
  admin/
packages/
  shared-ui/
  shared-types/
  shared-sdk/
services/
  research-modules/
deploy/
```

## 5. 统一身份、权限、租户与项目模型

### 5.1 身份模型

统一身份体系由以下对象组成：

- `User`：用户主体
- `Organization`：机构主体，通常对应医院、院区、科研中心或企业客户
- `Membership`：用户与机构之间的关系
- `Profile`：用户个人资料与偏好

一个用户可以加入多个机构，但任一时刻只激活一个机构上下文。

### 5.2 权限模型

采用 `RBAC + Scope`：

角色：

- `Super Admin`
- `Org Admin`
- `PI / Project Owner`
- `Researcher`
- `CRC / Data Manager`
- `Reviewer / Statistician`
- `Guest / Readonly`

作用域：

- 平台级
- 机构级
- 项目级
- 资源级

### 5.3 项目主模型

科研业务围绕项目制组织，核心实体为：

- `ResearchProject`
- `ProjectWorkspace`
- `ProjectMember`
- `ResearchTask`
- `ResearchArtifact`
- `ProjectTimeline`

会话与项目关系原则：

- `Conversation / Session` 是交互载体
- `ResearchProject` 是业务主实体
- 所有会话必须挂到 `ProjectWorkspace`

### 5.4 审计基础

关键动作必须落审计事件，至少包含：

- 登录 / 切换机构 / 邀请成员
- 创建 / 编辑 / 删除项目
- 上传 / 删除文件
- 运行 Agent 任务
- 导出研究产物
- 编辑 eCRF / 锁库 / 解锁
- 权限变更 / 配额调整

审计字段：

- `actor`
- `tenant`
- `project`
- `resource_type`
- `resource_id`
- `before`
- `after`
- `timestamp`
- `client_type`
- `trace_id`

## 6. 双端同步、状态管理与离线/在线协同

### 6.1 状态分层

- `Server State`：项目、任务、产物、权限、审计等统一由后端维护
- `Session State`：Agent 运行过程、流式输出、工具调用、任务进度
- `Client UI State`：页面、布局、筛选、主题、窗口状态
- `Local Cache`：最近项目、草稿快照、附件索引、下载缓存

### 6.2 同步机制

- 请求响应同步：创建、编辑、提交、导出等明确写操作
- 事件推送同步：流式输出、任务进度、成员协作、锁库变化、审计通知

同步原则：

- 读写走标准 API
- 增量变化走事件流
- 客户端根据事件刷新资源

### 6.3 Electron 与 Web 的边界

Web 端适合：

- 在线协作
- 轻量访问
- 管理后台
- 审阅与共享

Electron 端可额外提供：

- 本地文件桥接
- 大文件上传优化
- 本地缓存与断网恢复
- 桌面通知
- 自动更新
- 未来接入院内本地资源的扩展位

这些只属于宿主增强能力，不得演化为独立业务逻辑。

### 6.4 离线策略

底座阶段采用有限离线：

- 支持离线查看最近项目缓存
- 支持离线编辑本地草稿
- 支持恢复联网后再提交
- 对未同步内容做明确标记

底座阶段不支持：

- 多人离线并发合并
- 本地完整数据库副本
- 跨设备自动冲突解决

### 6.5 冲突处理

- 普通草稿类：版本快照 + 冲突提示
- 结构化配置类：乐观锁 + 版本号校验
- 关键受控类：串行写入 + 强校验

### 6.6 固定约束

- 双端业务真相源只能是后端
- 客户端只缓存，不私自定义业务状态
- 实时同步只推送事件，不绕过 API 直接写数据
- 关键科研数据强一致优先
- 离线能力只做可恢复，不做完全离线自治

## 7. Agent 编排、Hook+Loop 核心引擎与科研模块挂载机制

### 7.1 核心定位

`Hook+Loop` 是任务执行框架，而不是单纯聊天 Agent。其职责包括：

- 接收用户意图或系统事件
- 结合项目上下文理解任务
- 选择 Agent / Tool / Workflow
- 执行并持续反馈进度
- 将结果沉淀为结构化科研产物

### 7.2 运行时分层

- `Intent Layer`
- `Planning Layer`
- `Execution Layer`
- `Artifact Layer`

聊天只是入口，系统交付的是可复用科研对象。

### 7.3 Hook 与 Loop 的职责

`Hook` 负责：

- 用户发起任务
- 上传文件
- 定时任务
- 管理员操作
- 上游任务完成后的链式触发

`Loop` 负责：

- 感知上下文
- 推理与规划
- 选择工具
- 执行动作
- 结果校验
- 反馈与继续/结束判断

### 7.4 科研模块挂载协议

每个模块至少暴露：

- `capabilities`
- `inputs schema`
- `executor`
- `artifact mapper`

标准产物示例：

- `LiteratureSearchSet`
- `PaperSummary`
- `ComparisonReport`
- `ProtocolDraft`
- `SampleSizeReport`
- `ProposalDraft`

### 7.5 多 Agent 协作

底座首期采用“主编排 Agent + 专业子 Agent”模式：

- `Research Orchestrator`
- `Literature Agent`
- `Reading Agent`
- `Methodology Agent`
- `Data Management Agent`
- `Writing Agent`

### 7.6 工具安全分级

- `Read Tools`
- `Transform Tools`
- `Controlled Write Tools`

其中 `Controlled Write Tools` 必须带：

- 权限校验
- 审计落库
- 幂等控制
- 必要时人工确认

### 7.7 校验机制

每个科研模块预留 `validator`，用于校验结果完整性、来源可信度、结构合法性与模板符合度。

### 7.8 固定约束

- 聊天只是入口，不是最终业务载体
- 所有科研功能都要模块化挂载
- 所有模块输出都必须落成标准产物
- 高风险写操作必须受控
- 每个模块都要有结果校验位

## 8. 文件、知识库、向量检索、产物版本与审计追踪基础设施

### 8.1 文件体系

统一文件域分为：

- `source files`
- `derived files`
- `knowledge assets`
- `artifacts`
- `exports`

文件元数据最少包含：

- `file_id`
- `project_id`
- `storage_path`
- `mime_type`
- `checksum`
- `source_type`
- `derived_from`
- `version`
- `created_by`
- `created_at`

### 8.2 知识库模型

知识库按三层组织：

- `Document Layer`
- `Chunk Layer`
- `Evidence Layer`

`Evidence Layer` 必须支持追踪：

- 结论来自哪篇论文
- 来自哪一页或哪一章节
- 哪次任务引用
- 最终进入哪份研究产物

### 8.3 向量检索基础设施

推荐组合：

- `PostgreSQL`：主业务数据、元数据、权限、项目、任务、审计
- `Object Storage`：原始文件与导出文件
- `Milvus`：文档向量与相似度检索

底座边界：

- 向量库只存检索索引和必要引用信息
- 文献去重索引与 RAG 索引逻辑隔离
- 项目级数据必须索引隔离
- 每个 chunk 必须回链原始文件与页码/章节

### 8.4 产物模型与版本机制

所有结果统一抽象为 `ResearchArtifact`，常见类型包括：

- `LiteratureSearchSet`
- `PaperSummary`
- `ComparisonReport`
- `ProtocolDraft`
- `SampleSizeReport`
- `ProposalDraft`
- `ECRFSchema`
- `DataQualityReport`
- `SAPDraft`
- `CSRDraft`

通用字段：

- `artifact_id`
- `artifact_type`
- `project_id`
- `status`
- `version`
- `parent_version_id`
- `source_refs`
- `generator_run_id`
- `review_state`
- `published_at`

版本策略：

- 普通草稿支持自动快照
- 关键里程碑支持显式发布版本
- 正式导出版本不可篡改
- 所有版本保留来源依赖链

### 8.5 双层追踪体系

- `Operational Audit`：谁在什么时间对什么资源执行了什么动作
- `Lineage Trace`：某个结果由哪些输入、工具、运行链路生成

### 8.6 固定约束

- 所有知识切片都必须可回溯到原始文档
- 所有正式产物都必须有版本链
- 所有导出物都必须定位到对应产物版本
- 所有 Agent 生成结果都必须带运行追踪标识
- 审计和血缘追踪必须分层建模

## 9. 部署拓扑、环境分层、监控告警与测试基线

### 9.1 部署拓扑

整体采用“前端双入口 + 统一后端服务层 + 分层数据基础设施”：

- `Web Gateway`
- `Desktop Client`
- `API / Agent Gateway`
- `Research Services`
- `Worker / Queue`
- `Data Layer`
- `Observability Layer`

### 9.2 环境分层

建议环境：

- `local`
- `dev`
- `staging`
- `prod`

环境隔离要求：

- 模型配置隔离
- 第三方 API Key 隔离
- 机构数据源隔离
- 向量索引隔离
- 对象存储隔离
- 禁止开发或测试客户端误连生产数据

### 9.3 最小部署单元

- `meda-agent-core`
- `meda-web`
- `meda-admin`
- `meda-worker`
- `meda-scheduler`
- `postgres`
- `milvus`
- `redis`
- `object-storage`
- `message-bus`

### 9.4 监控与告警基线

监控范围：

- 平台指标
- Agent 指标
- 模型指标
- 数据指标
- 业务指标

告警等级：

- `P1`
- `P2`
- `P3`

### 9.5 测试基线

- 单元测试
- 集成测试
- 端到端测试
- 兼容性测试
- 性能测试
- 安全测试

### 9.6 底座验收门槛

- Web 和 Desktop 都能访问同一套项目数据
- 用户、机构、项目、权限、审计链路跑通
- Agent 任务可流式执行并落产物
- 文件上传、解析、索引、回溯链路跑通
- 管理后台能看到租户、用户、任务、告警基础信息
- 基础部署文档、启动脚本、环境配置模板齐备
- 基础监控面板与错误告警已接通

### 9.7 固定约束

- 双端共享一套生产后端
- 重任务异步化
- 环境、数据、密钥严格隔离
- 可观测性从底座阶段接入
- 测试需与开发同步建设

## 10. 推荐实施顺序

推荐将平台底座拆为以下实施波次：

1. 工程收敛与仓库拓扑调整
2. 身份、机构、项目、权限主模型接入
3. Web / Desktop 共用协议与状态同步打通
4. Agent Core 与 Hook+Loop 挂载协议落地
5. 文件、知识、向量、产物、审计基础设施接入
6. 管理后台基础能力建设
7. 部署、监控、测试基线补齐
8. 再分阶段挂接科研模块

## 11. 风险与约束清单

主要风险：

- `Hermes` 三套工程的目录与边界尚未统一，继承式改造可能出现接口收敛成本
- 医学与科研模块后续接入时，会对权限、可追溯性和版本控制提出更高约束
- 若一开始把离线能力做得过重，会明显拖慢首期底座交付
- 若不提前固定模块挂载协议，后续 11 个模块容易演化为分散实现

约束清单：

- 不以聊天会话作为业务主实体
- 不在桌面端或 Web 端写独立业务规则
- 不让向量库替代主业务数据库
- 不让正式导出物脱离版本链
- 不让关键写操作绕过权限和审计

## 12. 非目标

本阶段不包含以下内容的详细实现设计：

- R004-R016 每个科研模块的内部算法细节
- PDF 编辑能力
- 移动端 App
- 多语言界面
- 复杂离线协同和自动冲突合并
- 替代专业统计软件的执行能力

## 13. 设计结论

MedA 平台底座应采用 `Hermes` 继承式方案，以统一后端、双端一致、项目制模型、Hook+Loop 编排内核、统一文件与知识基础设施、统一审计与版本追踪为核心。平台底座完成后，才适合继续拆解 `Hermes` 双端复刻层、科研核心能力层、科研执行与数据层、管理运营与交付层的后续设计与实施计划。
