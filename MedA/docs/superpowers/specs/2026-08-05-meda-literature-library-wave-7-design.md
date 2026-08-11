# MedA Wave 7 文献条目库设计文档

> 设计日期：2026-08-05
> 设计范围：检索阶段子入口深页 `文献条目库`
> 适用阶段：Wave 7 设计确认

## 1. 设计目标

本设计文档定义 MedA 在 `Wave 7` 阶段落地的第三个真实子入口工作页：`文献条目库`。

在前面各波中，系统已经完成：

- `Wave 5`：检索式管理，含草稿与版本快照模型
- `Wave 6`：数据库来源配置，并解除了 `selected_sources` 硬编码

但截至 `Wave 6`，系统中所有已建立的深页都是**配置型页面**。没有任何页面处理**文献条目集合**。这构成一个结构性缺口：

- `search-log`（检索记录）需要记录"某次检索命中了哪些文献"
- 筛选阶段的 `title-abstract`、`full-text` 需要面对待筛文献集合
- `prisma` 流程图需要"去重前 N 条、去重后 M 条"这类统计

这些都依赖一个前置概念：**项目级文献条目全集**。不先建立它，后续任何一条路都只能造假数据。

`Wave 7` 的核心目标是：**把文献条目集合做成真实数据资产，并建立可追溯的去重机制。**

本波要打实的核心能力是：

- 项目级文献条目的录入与存储
- 批量粘贴导入
- 三级去重判定与状态标记
- 去重结果的人工确认与驳回
- 文献集合的统计视图

## 2. 已确认设计决策

- `Wave 7` 优先对象为 `文献条目库`
- 条目来源限定为 `粘贴导入 + 手工录入`，不接真实 API、不做文件上传
- 去重策略为 `自动标记 + 人工确认`，重复条目不删除
- 采用 `独立 LiteratureRecord 实体 + 项目级集合` 的落地路径
- 导入格式采用自定义极简行分隔格式，不实现 RIS / BibTeX 解析器
- 导入失败采用部分成功语义，不做全失败回滚
- 前端组件放入 `Wave 6` 已建立的 `packages/shared-ui`，双端共用

## 3. 核心定位

`文献条目库` 是检索阶段的第三个真实深页，与 `检索式管理`、`数据库来源` 是**兄弟页**，三者都挂在检索阶段入口页下面。

它优先回答三个问题：

- 本项目目前收集了哪些文献
- 这些文献里有多少是重复的
- 每条文献来自哪个数据库、哪次导入

它不是筛选页，不是全文管理器，也不是引文管理软件，而是检索阶段的**文献集合底座**。

## 4. 方案选型

针对文献条目如何归属，本轮评估过三种方向：

- `A. 独立 LiteratureRecord 实体 + 项目级集合`
- `B. 挂在 SearchQuery 下，按检索式组织条目`
- `C. 复用 FileRecord / ArtifactRecord 存文献`

最终选择 `A`，原因如下：

- 文献集合是独立的数据资产，后续 `search-log`、筛选、抽取都能挂上去而互不干扰
- 去重轨迹天然可追溯
- 项目级隔离与既有 `ResearchProject` 中心化约束一致

排除 `B` 的原因是结构性的：筛选阶段面对的是**跨检索式合并去重后的全集**，不是单条检索式的结果。把文献挂在 query 下会让"项目级文献全集"这一核心概念无处安放，去重也退化为跨表操作。

排除 `C` 的原因：语义不匹配。`FileRecord` 是文件存储登记，`ArtifactRecord` 是产物登记，文献条目是结构化书目数据。三者混用会让所有概念都变模糊。

## 5. 数据模型

### 5.1 实体关系

```
ResearchProject (1) ── (N) LiteratureRecord
LiteratureRecord (N) ── (0..1) LiteratureRecord    # duplicate_of 自引用
ResearchProject (1) ── (N) LiteratureImportBatch
LiteratureImportBatch (1) ── (N) LiteratureRecord
```

### 5.2 LiteratureRecord 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `int` | 主键 |
| `project_id` | `int` | 外键指向 `researchproject.id` |
| `title` | `str` | 标题，必填 |
| `authors` | `str` | 作者串，如 `"Chen L, Wang H"`，可为空串 |
| `journal` | `str` | 期刊名，可为空串 |
| `year` | `int \| None` | 发表年份，`None` 表示未知 |
| `doi` | `str` | DOI，可为空串 |
| `pmid` | `str` | PubMed ID，可为空串 |
| `abstract` | `str` | 摘要，可为空串 |
| `source_key` | `str` | 来源库 key，复用 `Wave 6` 的来源目录 |
| `dedupe_status` | `str` | `unique` / `duplicate` / `confirmed_unique` |
| `duplicate_of_id` | `int \| None` | 指向被判定为原件的记录 |
| `import_batch_id` | `int \| None` | 归属导入批次，手工录入为 `None` |

可缺省的文本字段统一用空串而非 `None`，避免前端反复做空值判断。`year` 与两个 id 字段用 `None`，因为它们参与判断逻辑，空串会引入类型歧义。

### 5.3 LiteratureImportBatch 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `int` | 主键 |
| `project_id` | `int` | 外键指向 `researchproject.id` |
| `source_key` | `str` | 本批次的来源库 |
| `parsed_count` | `int` | 成功解析并入库的条目数 |
| `duplicate_count` | `int` | 本批次中被判定为重复的条目数 |
| `skipped_count` | `int` | 因缺少 `title` 被跳过的块数 |
| `created_at_label` | `str` | 展示用的创建标记 |

保留批次是为了让导入可追溯：用户能看到"这 40 条是从哪次粘贴来的"。

本波不存储 `raw_text` 原文。理由是原文可能很长，而当前没有任何功能需要回读它；若后续要支持"重新解析某批次"，再补该字段。

### 5.4 去重判定规则

三级判定，命中即停：

1. `doi` 非空且与已有记录相同 → 判重
2. `pmid` 非空且与已有记录相同 → 判重
3. 标题归一化后相同 **且** `year` 相同 → 判重

空的 `doi` 或 `pmid` 不参与判重。否则所有缺 DOI 的条目会被互相判重。

标题归一化规则：转小写，去除所有非字母数字字符（含空格与标点）。

因此以下两者会被识别为同一篇：

```
"Metformin in T2DM."
"metformin in t2dm"
```

第三级要求 `year` 相同，是为了避免把同名的不同年份研究误判为重复。若两条标题相同但 `year` 分别为 `2020` 与 `2023`，不判重。若两条 `year` 均为 `None`，视为相同（都未知）。

一条与 `None` 的比较需要明确：若一条 `year` 为 `2023`、另一条为 `None`，**不判重**。已知年份与未知年份不能认定为同一篇，否则会把缺字段的条目误并到有完整信息的条目上。

判重的比较对象是**同一项目内的已有记录**，跨项目不判重。

同一批次内部也要判重。若粘贴的文本中两条 DOI 相同，后出现的那条应被标记为 `duplicate` 并指向前一条。实现上，每条解析结果在入库时都要与"该项目当前已有记录"比较，包含本批次中先入库的条目。

被标记为 `duplicate` 的条目不再作为后续判重的原件候选。若 A、B、C 三条 DOI 相同，B 与 C 都应指向 A，而不是形成 A ← B ← C 的链。

### 5.5 去重状态语义

| 状态 | 含义 |
|---|---|
| `unique` | 导入时未检出重复 |
| `duplicate` | 自动检出重复，`duplicate_of_id` 指向原件 |
| `confirmed_unique` | 用户驳回了自动判重，视为独立文献 |

`confirmed_unique` 的条目**继续参与后续判重**，且可作为原件候选。用户驳回判重表示"这确实是另一篇独立文献"，那么它就应该像 `unique` 条目一样接受后续比较。否则用户驳回一次之后，再导入真正与它重复的条目将检不出来。

**关键约束：被标记 `duplicate` 的条目不删除。**

PRISMA 流程图需要"去重前 N 条、去重后 M 条"这两个数字。删除重复条目会让这个统计永久无法计算。这也是本波选择"自动标记 + 人工确认"而非"导入时直接丢弃"的根本原因。

## 6. 导入格式

### 6.1 格式定义

采用自定义极简行分隔格式：

```
title: Metformin and cardiovascular outcomes in type 2 diabetes
authors: Chen L, Wang H, Liu M
journal: Lancet Diabetes Endocrinol
year: 2023
doi: 10.1016/S2213-8587(23)00123-4
pmid: 37123456
abstract: This study evaluates cardiovascular outcomes...
---
title: Sodium-glucose cotransporter 2 inhibitors in heart failure
authors: Zhang Y, Li Q
journal: NEJM
year: 2022
doi: 10.1056/NEJMoa2201234
```

解析规则：

- `key: value` 逐行解析
- `---` 单独成行时作为条目分隔符
- 只有 `title` 必填，其余字段可缺省
- 未识别的 key 直接忽略，不报错
- 空行忽略
- key 大小写不敏感，value 首尾空白去除
- `year` 无法解析为整数时置为 `None`，不报错

### 6.2 为何不实现 RIS / BibTeX

RIS 与 BibTeX 都有大量方言与转义规则：BibTeX 的花括号嵌套与特殊字符转义，RIS 的多值字段与续行约定。正确实现需要相当篇幅，且"解析失败如何报错"本身就是一个独立子课题。

本波的目标是把**文献集合**这个概念立起来。格式解析是可替换的实现细节，解析器以纯函数形式隔离，后续替换不影响其他层。

等到需要接真实文件导入时，应引入成熟解析库而非自研。

### 6.3 手工录入

单条表单，字段与 `LiteratureRecord` 的用户可见字段一致。`title` 必填，其余可留空。

手工录入的条目同样参与去重判定，`import_batch_id` 为 `None`。

## 7. 页面结构

### 7.1 路由语义

```
workspace / projects / {project_id} / stages / search / literature
```

只有一种打开模式。文献库是项目级集合，不存在草稿与快照之分。

### 7.2 阶段入口页改造

检索阶段当前有三张卡片：`query-builder`、`sources`、`search-log`。本波新增第四张 `literature` 卡片，并纳入项目级深页路由改写集合（该集合在 `Wave 6` 已包含 `query-builder` 与 `sources`）。

`search-log` 卡片本波不改，继续保留占位。

### 7.3 整页结构

三段式，但与 `Wave 5` 的编辑器形态不同，本页是**列表型**：

1. `左侧窄导航`
2. `左侧项目上下文面板`
3. `中间主区`
4. `右侧统计区`

### 7.4 左侧区域

与前面各波保持一致，不新增专属层级。项目上下文面板保留项目名称、项目标识、当前阶段与返回检索阶段入口页的入口。

### 7.5 中间主区

分两块：

1. `导入条`
   - 来源选择（复用 `Wave 6` 的来源目录）
   - 粘贴文本框
   - `导入` 按钮
   - 导入结果摘要（成功数 / 重复数 / 跳过数）

2. `条目列表`
   - 每条显示标题、作者、期刊与年份、DOI 或 PMID
   - 去重状态徽标
   - 被标记 `duplicate` 的条目显示 `标记为独立文献` 按钮

### 7.6 右侧统计区

- 总条目数 / 唯一数 / 重复数
- 按来源分布
- 最近导入批次摘要

这一区是为 PRISMA 铺路：这三个数字将来直接进流程图。把它放在本波，是为了让统计口径从一开始就确定，避免后续反算。

## 8. 交互规则

### 8.1 导入语义

导入采用**部分成功**语义：

- 整段内容解析不出任何条目 → `422`
- 某个条目块缺 `title` → 跳过该块，其余条目正常导入，响应中返回 `skipped_count`

用户粘贴 50 条其中 1 条格式损坏，不应让另外 49 条也进不来。

### 8.2 去重确认

对 `duplicate` 状态的条目调用确认接口后：

- `dedupe_status` 改为 `confirmed_unique`
- `duplicate_of_id` 置为 `None`

本波只支持"驳回自动判重"这一个方向。不支持把 `unique` 条目手工标记为重复 —— 那需要选择原件的交互，属于额外范围。

### 8.3 返回链路

用户必须能够清楚地：

- 从 `文献条目库` 返回 `检索阶段入口页`
- 从 `检索阶段入口页` 返回 `工作台首页`
- 从 `检索阶段入口页` 进入兄弟页 `检索式管理` 与 `数据库来源`
- 全程保持同一 `ResearchProject` 上下文

### 8.4 双端同构

组件放入 `packages/shared-ui`，Web 与 Desktop import 同一实现。这延续 `Wave 6` code review 后建立的做法，避免再产生逐字节重复的双份组件。

## 9. API 契约

### 9.1 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/workspace/projects/{project_id}/stages/search/literature` | 读条目列表与统计 |
| `POST` | `/api/workspace/projects/{project_id}/stages/search/literature/import` | 粘贴导入 |
| `POST` | `/api/workspace/projects/{project_id}/stages/search/literature/records` | 手工新增单条 |
| `POST` | `/api/workspace/projects/{project_id}/stages/search/literature/records/{record_id}/confirm-unique` | 驳回自动判重 |

四个端点均返回完整的 `LiteratureLibraryResponse`，让前端一次拿到最新全量状态，无需二次请求。这与 `Wave 5` / `Wave 6` 的做法一致。

### 9.2 LiteratureLibraryResponse

```
project                  # WorkspaceProjectSummary，复用既有类型
stage_key                # 固定为 "search"
records[]                # LiteratureRecordSummary
stats                    # LiteratureStats
recent_batches[]         # LiteratureBatchSummary
available_sources[]      # 供导入时选择来源，复用 Wave 6 目录
last_import_result       # ImportResultSummary | None
```

`last_import_result` 只在导入端点的响应中非空，其余端点返回 `None`。它承载 7.5 提到的导入结果摘要。

### 9.3 LiteratureRecordSummary

```
id
title
authors
journal
year
doi
pmid
source_key
source_label             # 由 source_key 映射，复用 Wave 6 的 key→label 约定
dedupe_status
duplicate_of_id
```

响应中不含 `abstract`。列表页不展示摘要，返回它会显著增加载荷。若后续需要详情视图，再补单条详情端点。

### 9.4 LiteratureStats

```
total_count
unique_count             # unique + confirmed_unique
duplicate_count
by_source[]              # 每项含 source_key / source_label / count
```

`unique_count` 把 `confirmed_unique` 计入，因为二者在业务语义上都是"独立文献"。PRISMA 的"去重后数量"取的就是这个值。

### 9.5 请求体

`ImportLiteratureRequest`：

```
source_key
raw_text
```

`CreateLiteratureRecordRequest`：

```
title
authors
journal
year
doi
pmid
abstract
source_key
```

## 10. 错误处理

沿用 `Wave 5` / `Wave 6` 已建立的模式。

| 场景 | 状态码 |
|---|---|
| 项目不存在或跨机构 | `404` |
| `record_id` 不存在或不属于该项目 | `404` |
| 粘贴内容解析不出任何条目 | `422` |
| 手工录入缺 `title` | `422` |
| 未知 `source_key` | `422` |
| 对非 `duplicate` 状态条目调 confirm-unique | `422` |

实现方式：

- 项目校验复用 `workspace.py` 中已有的 `_load_project_or_404`
- 服务层定义 `LiteratureError` 领域异常，携带具体原因
- router 统一 `try/except` 转换，不让裸异常冒泡成 `500`

`422` 的 `detail` 需说明具体原因，便于前端定位。

## 11. 模块划分

为保持边界清晰，后端拆为两个服务模块：

| 模块 | 职责 |
|---|---|
| `app/services/literature_parser.py` | 纯函数：格式解析、标题归一化。不依赖 session |
| `app/services/literature.py` | 数据操作：导入、去重判定、确认、统计、响应组装 |

解析器独立成模块的理由：它是纯函数，可独立单测，且是后续替换为 RIS / BibTeX 解析库时唯一需要改动的位置。

## 12. 测试策略

采用 TDD，分层推进。

### 12.1 解析器纯函数

独立于 HTTP：

- 解析多条目文本
- 解析单条目文本
- 缺省字段的条目
- 未识别 key 被忽略
- 空行被忽略
- key 大小写不敏感
- `year` 非整数时为 `None`
- 缺 `title` 的块被识别为需跳过
- 标题归一化：大小写、标点、空格

### 12.2 去重逻辑

- `doi` 相同 → 标记 `duplicate`，`duplicate_of_id` 指向原件
- `pmid` 相同 → 标记 `duplicate`
- 标题归一化后相同且 `year` 相同 → 标记 `duplicate`
- 标题相同但 `year` 不同 → **不**判重
- 标题相同但一条 `year` 已知、另一条为 `None` → **不**判重
- 空 `doi` 不参与判重
- 空 `pmid` 不参与判重
- 同一批次内 DOI 相同的两条，后者被标记 `duplicate` 并指向前者
- 三条同 DOI 时，第二、三条都指向第一条，不形成链
- `confirmed_unique` 条目仍可作为后续判重的原件
- 跨项目不判重

### 12.3 导入与确认 API

- 粘贴导入多条，条目正确入库
- 只有 `title` 的条目也能导入
- 缺 `title` 的块被跳过，`skipped_count` 正确，其余条目正常入库
- 完全无法解析 → `422`
- 未知 `source_key` → `422`
- 手工录入成功
- 手工录入缺 `title` → `422`
- `confirm-unique` 把状态改为 `confirmed_unique` 并清空 `duplicate_of_id`
- 对 `unique` 条目调 confirm-unique → `422`
- 不存在的 `record_id` → `404`
- 跨机构项目 → `404`

### 12.4 统计

- `total_count` / `unique_count` / `duplicate_count` 正确
- `confirmed_unique` 被计入 `unique_count`
- `by_source` 分布正确

### 12.5 SDK

`getLiteratureLibrary`、`importLiterature`、`createLiteratureRecord`、`confirmLiteratureUnique` 各一个测试。

### 12.6 Web 与 Desktop

- 从阶段入口页进入文献库
- 粘贴导入
- 断言条目出现且统计更新

### 12.7 补 Wave 6 遗留

`packages/shared-ui` 目前没有自己的测试。本波给其纯函数 `toggleKey` 与 `parseYear` 补单测。

## 13. Wave 7 实现边界

本波明确只把 `文献条目库` 做成真实数据页，并建立去重机制。

本波默认包含：

- 项目级文献条目的存储与列表
- 粘贴批量导入与极简格式解析
- 手工单条录入
- 三级去重判定与状态标记
- 去重人工确认（驳回自动判重）
- 文献集合统计与来源分布
- 导入批次记录
- 阶段入口页新增 `literature` 卡片
- 组件放入 `shared-ui`，Web / Desktop 同构
- 补 `shared-ui` 纯函数单测

本波明确不包含：

- RIS / BibTeX / CSV 文件上传与解析
- 真实数据库 API 拉取
- 条目编辑与删除
- 条目详情页与摘要展示
- 把 `unique` 条目手工标记为重复
- 全文 PDF 关联与管理
- 检索式与文献条目的关联（哪次检索命中哪些文献）
- 检索记录时间线页
- 筛选阶段的纳入排除判断
- PRISMA 流程图
- 分页与搜索过滤

## 14. 验收标准

`Wave 7` 完成后，至少应满足：

- 用户可从检索阶段入口页进入真实的 `文献条目库`
- 用户可选择来源并粘贴批量导入文献
- 只含 `title` 的条目也能成功导入
- 格式损坏的条目块被跳过，其余条目正常入库，并给出跳过数量
- 完全无法解析的内容返回 `422`
- 用户可手工录入单条文献
- DOI 相同、PMID 相同、标题归一化加年份相同三种情况均被标记为 `duplicate`
- 标题相同但年份不同不被判重
- 标题相同但一条年份已知、另一条未知时不被判重
- 同一批次内的重复条目也能被检出并正确指向原件
- 空 DOI 与空 PMID 不参与判重
- 被标记为重复的条目不被删除
- 用户可驳回自动判重，条目变为 `confirmed_unique`
- 统计区正确显示总数、唯一数、重复数与来源分布
- `confirmed_unique` 被计入唯一数
- 非法输入返回 `422`，跨机构项目与不存在的条目返回 `404`，不出现未处理的 `500`
- 解析器与归一化逻辑有独立的纯函数单测
- Web 与 Desktop 共用 `shared-ui` 中的同一组件
- 返回阶段入口页和工作台首页的链路清楚可达
- `shared-ui` 的 `toggleKey` 与 `parseYear` 有单测覆盖

## 15. 风险与控制点

- 如果本波实现 RIS / BibTeX 解析，方言与转义处理会迅速膨胀，重点从"文献集合"转移到"格式兼容"
- 如果本波接真实 API，会引入网络依赖、频率限制与重试，重点转移到外部集成
- 如果导入采用全失败语义，用户粘贴大批量数据时会因单条损坏而反复受阻
- 如果重复条目直接删除，PRISMA 统计将永久无法计算
- 如果去重判定不排除空 DOI 与空 PMID，所有缺标识的条目会被互相误判为重复
- 如果本波同时做条目编辑与删除，会牵出"编辑后是否重新判重"这一连锁问题
- 如果本波就做检索式与条目的关联，会同时触碰 `Wave 5` 的版本快照语义

控制策略：

- 解析器隔离为纯函数模块，格式升级不影响其他层
- 导入采用部分成功语义并显式返回跳过数量
- 重复条目标记而不删除
- 空标识字段明确不参与判重，并有对应测试
- 条目编辑、删除、详情页推迟到后续波次
- 检索式与条目的关联推迟到 `search-log` 波次

## 16. 设计结论

MedA `Wave 7` 应实现 `检索链路` 下的 `文献条目库`，采用独立的项目级 `LiteratureRecord` 实体与三级去重判定。本波的核心价值在于**把系统从配置型页面推进到数据型页面**，建立后续 `search-log`、筛选、PRISMA 都必须依赖的文献集合底座，并从一开始就保证去重轨迹可追溯。本波不接真实 API、不做文件导入、不做条目编辑，为后续检索执行与筛选链路保留清晰的扩展位。
