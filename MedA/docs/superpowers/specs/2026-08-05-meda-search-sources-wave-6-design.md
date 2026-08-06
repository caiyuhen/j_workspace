# MedA Wave 6 数据库来源配置页设计文档

> 设计日期：2026-08-05
> 设计范围：检索阶段子入口深页 `数据库来源`
> 适用阶段：Wave 6 设计确认

## 1. 设计目标

本设计文档定义 MedA 在 `Wave 6` 阶段落地的第二个真实子入口工作页：`数据库来源`。

在 `Wave 5` 中，系统已经完成：

- 检索阶段第一个真实深页 `检索式管理`
- `可变草稿 + 不可变版本快照` 模型
- 块式检索式编辑与执行前校验
- 基于规则的 `heuristic preview`

但 `Wave 5` 遗留了一个明确的数据缺口：`selected_sources` 是后端硬编码的 `["PubMed", "Embase"]`，`preview_summary` 基于这份假数据计算。这导致 `Wave 5` spec 中定义的 `preview_summary.status = unavailable` 状态没有任何真实触发路径。

`Wave 6` 的核心目标是：**让来源配置成为真实数据，并驱动检索式管理页的预览反馈。**

本波要打实的核心能力是：

- 项目级数据库来源选择
- 项目级检索参数配置
- 解除 `Wave 5` 的 `selected_sources` 硬编码
- 让 `preview_summary` 由真实配置驱动

## 2. 已确认设计决策

- `Wave 6` 优先对象为 `数据库来源` 子入口
- 范围限定为 `配置 + 打通 preview`，不接真实数据库 API
- 配置作用域为 `项目级`，一个项目一套来源配置
- 采用 `独立来源实体 + query-builder 读取` 的落地路径
- 页面骨架采用 `两段式配置页`，不套用 `Wave 5` 的三段式编辑器
- 来源配置直接保存，不引入版本快照机制

## 3. 核心定位

`数据库来源` 与 `检索式管理` 是**兄弟页**，不是父子关系。两者都挂在检索阶段入口页下面，通过阶段入口页的子入口导航互相到达。

它优先回答三个问题：

- 本项目要在哪些数据库里检索
- 检索时使用什么字段范围、时间窗和语种限定
- 改动来源配置会对当前检索式产生什么影响

它不是凭证管理中心，不是连通性诊断页，也不是检索执行页，而是检索阶段的**范围设定页**。

## 4. 方案选型

针对如何落地来源配置，本轮评估过三种方向：

- `A. 独立来源实体 + query-builder 读取`
- `B. 扩展 ResearchProject 加字段`
- `C. 复用 Wave 5 的 draft/version 模型做来源版本化`

最终选择 `A`，原因如下：

- 边界干净，来源配置与检索式可各自独立演进
- 一次性解除 `Wave 5` 的硬编码问题
- 为后续凭证管理、连通性测试留出扩展位，而无需现在实现

排除 `B` 的原因：来源配置有自己的参数结构（字段范围、时间窗、语种），塞进 `ResearchProject` 会让项目实体迅速膨胀，且后续扩展无处安放。

排除 `C` 的原因：来源配置的变更频率与语义和检索式完全不同。来源配置是"设置"，检索式是"产物"。硬套版本模型属于过度设计。

## 5. 数据模型

### 5.1 实体关系

```
ResearchProject (1) ── (1) SearchSourceConfig
```

`SearchSourceConfig` 是**项目级单例**：一个项目最多一条配置记录。首次访问时自动创建默认配置，与 `Wave 5` 中 `SearchQueryDraft` 的创建策略保持一致。

### 5.2 SearchSourceConfig 字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `id` | `int` | 主键 |
| `project_id` | `int` | 外键指向 `researchproject.id`，逻辑上唯一 |
| `enabled_sources_json` | `str` | 启用的库 key 列表，如 `["pubmed", "embase"]` |
| `search_fields_json` | `str` | 检索字段范围，如 `["title", "abstract", "keyword"]` |
| `year_from` | `int \| None` | 起始年份，`None` 表示不限 |
| `year_to` | `int \| None` | 结束年份，`None` 表示不限 |
| `languages_json` | `str` | 语种限定，如 `["en", "zh"]` |
| `config_dirty` | `bool` | 是否有未保存改动 |

JSON 字段的存储方式沿用 `Wave 5` 中 `SearchQueryDraft` 的做法，保持后端内部一致。

### 5.3 默认配置

首次创建时的默认值：

- `enabled_sources_json`: `["pubmed", "embase"]`
- `search_fields_json`: `["title", "abstract"]`
- `year_from`: `None`
- `year_to`: `None`
- `languages_json`: `["en"]`
- `config_dirty`: `false`

默认启用 `pubmed` 和 `embase` 是为了与 `Wave 5` 的既有行为保持向后兼容，避免现有项目在升级后立刻进入 `unavailable` 状态。

### 5.4 来源目录

可选来源目录用**后端常量表**定义，不入库。第一波固定为医学检索常见的六个：

| key | label | supports_full_text |
|---|---|---|
| `pubmed` | PubMed | `false` |
| `embase` | Embase | `false` |
| `cochrane` | Cochrane Library | `true` |
| `wos` | Web of Science | `false` |
| `cnki` | 中国知网 CNKI | `true` |
| `wanfang` | 万方数据 | `true` |

每项包含 `key`、`label`、`description`、`supports_full_text`。

目录作为常量而非数据表的理由：本波不支持用户自定义添加数据库，目录内容由产品定义而非用户数据。若后续需要支持机构级自定义来源，再迁移为数据表。

### 5.5 检索字段与语种取值

检索字段范围限定为：

- `title`
- `abstract`
- `keyword`
- `mesh`
- `full_text`

语种限定为：

- `en`
- `zh`

这两组取值同样以后端常量定义，随目录端点一并返回，供前端渲染选项。

## 6. 与 Wave 5 的衔接

这是本波最实质的改动，也是本波的核心价值。

### 6.1 改造点

`apps/agent-core/app/services/search_query.py` 中：

- `get_or_create_search_query_editor` 的 `selected_sources` 不再从 `SearchQueryDraft.selected_sources_json` 硬编码读取默认值，改为从 `SearchSourceConfig.enabled_sources_json` 解析
- `_build_preview_summary` 接收真实启用来源，`database_scope_summary` 反映真实启用的库标签
- `_build_validation_messages` 增加来源缺失判断

### 6.2 降级路径

当项目未启用任何来源时：

- `preview_summary.status` 返回 `unavailable`
- `preview_summary.database_scope_summary` 返回 `未选择数据库`
- `validation_messages` 增加一条：
  - `level`: `error`
  - `code`: `MISSING_SOURCE_CONFIG`
  - `message`: 提示需先在数据库来源页启用至少一个来源

这样 `Wave 5` spec 中定义的 `unavailable` 状态第一次获得真实触发路径。

### 6.3 版本快照的处理

`SearchQueryVersion` 已经存储了创建时刻的 `selected_sources_json`。本波**不改变这一行为**：版本快照保留创建时的来源信息，不随后续来源配置变更而回溯改写。这符合"版本快照不可变"的既有语义。

因此 `get_search_query_snapshot` 继续从版本记录读取来源，不读取当前项目配置。

### 6.4 key 与 label 的转换约定

`Wave 5` 现有代码中 `selected_sources` 存储的是显示名（如 `"PubMed"`），而本波的来源目录以 `key` 标识（如 `"pubmed"`）。两者语义不同，需明确转换约定：

- `SearchSourceConfig.enabled_sources_json` 存储 **key**，如 `["pubmed", "embase"]`
- `SearchSourceConfigResponse.enabled_source_keys[]` 返回 **key**
- `SearchQueryEditorResponse.selected_sources[]` 返回 **label**，如 `["PubMed", "Embase"]`
- `preview_summary.database_scope_summary` 使用 **label** 拼接

即：配置侧以 key 为准，检索式侧对外暴露 label。转换在 `search_query.py` 读取配置时完成，通过来源目录常量做 key 到 label 的映射。

这样既保证配置存储稳定（label 可能因产品文案调整而变化，key 不变），又保持 `Wave 5` 已有的 `selected_sources` 对外契约不被破坏。

## 7. 页面结构

本页继续挂在现有工作台壳层内，保持项目上下文不丢失。

### 7.1 路由语义

```
workspace / projects / {project_id} / stages / search / sources
```

只有一种打开模式。项目级配置是单例，不存在 `draft` 与 `snapshot` 之分，因此不需要 `Wave 5` 那样的多模式路由参数。

### 7.2 整页结构

主区采用**两段式配置页**，而非 `Wave 5` 的三段式编辑器。三段式适合编辑器形态，配置页用表单结构更合适。

1. `左侧窄导航`
2. `左侧项目上下文面板`
3. `中间主配置区`
4. `右侧影响提示区`

### 7.3 左侧窄导航

与前面各波保持一致，不新增专属层级：

- 工作台
- 项目
- 数据 / 资料
- Agent
- 产物
- 管理

### 7.4 左侧项目上下文面板

继续负责说明当前项目上下文，保留：

- 当前项目名称
- 项目标识
- 当前阶段：检索
- 返回检索阶段入口页的快捷入口

### 7.5 中间主配置区

分三块：

1. `来源清单`
   - 可选库列表
   - 每项一个启用开关
   - 展示库名、说明、是否支持全文

2. `检索参数`
   - 检索字段范围（多选）
   - 年份区间（起始 / 结束）
   - 语种限定（多选）

3. `保存条`
   - `保存配置` 按钮
   - 未保存改动提示

### 7.6 右侧影响提示区

这一区回答"改了配置会影响什么"，包含：

- 当前启用库数量
- 覆盖范围摘要
- 对当前检索式的影响提示
- 未启用任何来源时的明确警告

影响提示的存在是为了让配置页不成为孤立表单，而是显式暴露它与检索式管理页的联动关系。

## 8. 交互规则

### 8.1 保存语义

来源配置**直接保存，不生成版本快照**。

这里刻意与 `Wave 5` 不同：来源配置是"设置"，不是"产物"，不需要可追溯的版本历史。保存后 `query-builder` 的 preview 自动反映新配置。

### 8.2 返回链路

用户必须能够清楚地：

- 从 `数据库来源` 返回 `检索阶段入口页`
- 从 `检索阶段入口页` 返回 `工作台首页`
- 从 `检索阶段入口页` 进入兄弟页 `检索式管理`
- 全程保持同一 `ResearchProject` 上下文

### 8.3 阶段入口页改造

`stage_entry.py` 中检索阶段的 `sources` 卡片 `target` 需要从旧格式升级为项目级深页路由：

- 旧：`/workspace/stage/search/sources`
- 新：`/workspace/projects/{project_id}/stages/search/sources`

这与 `Wave 5` 对 `query-builder` 卡片的处理方式一致。`search-log` 卡片本波不改，继续保留占位。

### 8.4 双端同构

Web 与 Desktop 共用同一套信息架构与 SDK 方法，与 `Wave 5` 做法一致。

## 9. API 契约

### 9.1 端点

| 方法 | 路径 | 说明 |
|---|---|---|
| `GET` | `/api/workspace/sources/catalog` | 读可选来源目录与取值选项，项目无关 |
| `GET` | `/api/workspace/projects/{project_id}/stages/search/sources` | 读项目配置，不存在则创建默认 |
| `PUT` | `/api/workspace/projects/{project_id}/stages/search/sources` | 保存项目配置 |

目录端点单独拆出的理由：它与项目无关且可缓存，混入配置响应会让契约含义不清。

### 9.2 SearchSourceCatalogResponse

```
available_sources[]      # 每项含 key / label / description / supports_full_text
search_field_options[]   # 每项含 key / label
language_options[]       # 每项含 key / label
```

### 9.3 SearchSourceConfigResponse

```
project                  # WorkspaceProjectSummary，复用既有类型
stage_key                # 固定为 "search"
available_sources[]      # 目录项 + enabled 布尔标记
enabled_source_keys[]
search_fields[]
year_from
year_to
languages[]
config_dirty
impact_summary
validation_messages[]    # 复用 Wave 5 的 SearchValidationMessage 类型
```

### 9.4 impact_summary

```
enabled_count            # 当前启用库数量
coverage_hint            # 覆盖范围摘要
query_impact_hint        # 对当前检索式的影响提示
```

### 9.5 SaveSearchSourceConfigRequest

```
enabled_source_keys[]
search_fields[]
year_from
year_to
languages[]
```

## 10. 错误处理

沿用 `Wave 5` 收尾时建立的模式，不重新发明。

### 10.1 状态码约定

| 场景 | 状态码 |
|---|---|
| 项目不存在或跨机构 | `404` |
| 未知 source key | `422` |
| 未知检索字段或语种 key | `422` |
| `year_from > year_to` | `422` |

### 10.2 实现方式

- 项目校验复用 `workspace.py` 中已有的 `_load_project_or_404`
- 服务层定义 `SearchSourceConfigError` 领域异常，携带具体原因
- router 统一 `try/except` 转换为 HTTP 状态码，不让裸异常冒泡成 `500`

`422` 响应的 `detail` 需说明具体哪个 key 无效或哪项区间非法，便于前端定位。

## 11. 校验规则

保存与读取时均计算 `validation_messages`：

| 条件 | level | code |
|---|---|---|
| 未启用任何来源 | `error` | `MISSING_SOURCE_CONFIG` |
| 未选任何检索字段 | `warning` | `EMPTY_SEARCH_FIELDS` |
| 年份跨度小于 3 年 | `info` | `NARROW_YEAR_RANGE` |

年份跨度判断仅在 `year_from` 与 `year_to` 均非空时执行。

## 12. 测试策略

采用 TDD，分层推进。

### 12.1 后端

- 首次访问创建默认配置
- 保存后重新读取，配置正确持久化
- 非法 source key 返回 `422`
- 年份区间倒置返回 `422`
- 跨机构项目返回 `404`
- 未启用来源时返回 `MISSING_SOURCE_CONFIG` 校验消息
- 目录端点返回完整来源列表与取值选项

### 12.2 联动测试

本波的核心验证点，证明配置真的驱动了 preview：

- 修改来源配置后，`query-builder` 的 `selected_sources` 随之变化
- 修改来源配置后，`query-builder` 的 `preview_summary.database_scope_summary` 反映新的库集合
- 清空所有来源后，`query-builder` 的 `preview_summary.status` 变为 `unavailable`
- 清空所有来源后，`query-builder` 的 `validation_messages` 包含 `MISSING_SOURCE_CONFIG`
- 已有版本快照的 `selected_sources` 不随当前配置变更而改写

### 12.3 SDK

- `getSourceCatalog`
- `getSearchSourceConfig`
- `saveSearchSourceConfig`

各一个测试，验证请求路径、payload 与返回类型。

### 12.4 Web 与 Desktop

- 从阶段入口页点击 `数据库来源` 卡片进入配置页
- 切换某个库的启用状态
- 点击保存
- 断言启用数量与影响提示更新

## 13. Wave 6 实现边界

本波明确只把 `数据库来源` 做成真实配置页，并打通与 `检索式管理` 的联动。

本波默认包含：

- 项目级来源配置的创建、读取、保存
- 来源目录常量与取值选项
- 检索字段范围、年份区间、语种限定
- 解除 `Wave 5` 的 `selected_sources` 硬编码
- `preview_summary` 由真实配置驱动
- `unavailable` 降级路径
- 阶段入口页 `sources` 卡片路由升级
- Web / Desktop 同构

本波明确不包含：

- 数据库凭证与密钥管理
- 连通性测试与健康检查
- 真实数据库 API 接入
- 真实命中量查询
- 按来源的差异化参数配置
- 用户自定义添加数据库
- 来源配置的版本快照与变更历史
- 检索记录时间线页
- 检索式库总览页

## 14. 验收标准

`Wave 6` 完成后，至少应满足：

- 用户可从检索阶段入口页进入真实的 `数据库来源` 配置页
- 页面采用两段式配置结构，含来源清单、检索参数、影响提示
- 用户可启用或停用来源，并保存配置
- 用户可配置检索字段范围、年份区间与语种限定
- 保存后配置正确持久化
- `检索式管理` 页的 `selected_sources` 来自真实配置，不再硬编码
- `检索式管理` 页的 `preview_summary` 由真实配置驱动
- 未启用任何来源时，`检索式管理` 页 preview 进入 `unavailable` 并给出 `MISSING_SOURCE_CONFIG`
- 已有版本快照的来源信息不被当前配置变更改写
- 非法输入返回 `422`，跨机构项目返回 `404`，不出现未处理的 `500`
- Web 与 Desktop 保持同构信息架构
- 返回阶段入口页和工作台首页的链路清楚可达

## 15. 风险与控制点

- 如果本波引入凭证管理，会立刻牵出加密存储、权限模型和审计要求，范围失控
- 如果本波接真实数据库 API，会引入外部网络依赖、频率限制和错误重试，重点从"配置"转移到"集成"
- 如果给来源配置也做版本快照，会把简单设置页做成第二个版本子系统
- 如果支持按来源差异化参数，配置矩阵会迅速膨胀，双端 UI 复杂度显著上升
- 如果不做联动测试，本波可能退化成一个孤立表单页，无法证明真实价值

控制策略：

- 凭证与连通性测试明确推迟到后续波次
- 来源目录用常量而非数据表，避免过早引入自定义来源
- 来源配置直接保存，不引入版本机制
- 所有启用来源共用同一套检索参数
- 把联动测试作为本波的核心验收项，而非可选项

## 16. 设计结论

MedA `Wave 6` 应实现 `检索链路` 下的 `数据库来源` 配置页，采用项目级单例配置与两段式页面结构。本波的核心价值不在于新增一个页面，而在于**解除 `Wave 5` 遗留的 `selected_sources` 硬编码，让 `preview_summary` 由真实配置驱动**，并使 `unavailable` 降级状态第一次获得真实触发路径。本波不接真实数据库 API，不做凭证管理与连通性测试，为后续检索执行链路保留清晰的扩展位。
