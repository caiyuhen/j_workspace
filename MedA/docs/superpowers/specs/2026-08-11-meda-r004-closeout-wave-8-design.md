# MedA Wave 8 设计文档：R004 收口（PICO + 多库异步检索 + PRISMA + BM25）

> 生成日期：2026-08-11
> 状态：Draft（待用户审阅）
> 下一层交付：Implementation Plan（writing-plans 产出）

## 1. 背景与目标

Waves 1~7 已交付的检索骨架：

- Wave 5 [Search Query Management]：检索式编辑器（PICO 槽位 + MeSH 词表输入框）+ 草稿/版本保存、版本衍生
- Wave 6 [Search Sources]：检索源配置面板（6 个数据源开关 + 语言 + 日期 + 文献类型过滤）
- Wave 7 [Literature Library]：文献条目库（`LiteratureRecord`、`LiteratureImportBatch`）+ 三级去重（DOI → PMID → 归一化标题+年份）+ 人工确认为独立条目（`confirmed_unique`）

**Wave 8 的目标**：把「检索式管理工具」补成「真正的检索系统」，形成 **检索式 → 多库跑 → 统一去重入库 → BM25 相关性排序 → PRISMA 筛选漏斗 → PICO 自动提取提示** 的端到端闭环，补完 PRD §6.1.1 R004 文献检索模块（除 Milvus 向量去重 FR-004-03 留后续 Wave）的剩余功能：

| PRD 需求 ID | 需求 | Wave 8 交付形式 |
|---|---|---|
| FR-004-01 | PICO 提取功能，准确率≥85% | **双引擎**：默认 `rule_baseline`（词典+正则，无 LLM 依赖）；可选 `llm:<provider>` 通过配置文件注入 |
| FR-004-02 | 多库并行检索 PubMed / CNKI / Wanfang | **异步任务引擎 + Adapter 模式**：PubMed 真 NCBI E-utilities；CNKI/Wanfang stub + 可注入 mock 数据集 |
| FR-004-04 | 标题/摘要去重 | 复用 Wave 7 三级去重，仅新增「跨库命中后同一 SearchRun 内先跑查重」 |
| FR-004-05 | 相关性排序（BM25） | Python `rank_bm25` 对 title+abstract 单语 tokenize；记录到 `LiteratureRecord.relevance_score`，排序阈值可调 |
| FR-004-06 | 结果展示与导出（PRISMA + CSV） | PRISMA 筛选漏斗（4 档，后两档先=去重后，下一 Wave 接人工筛选）+ SearchRun 维度 CSV 导出 |

**显式超出范围（Out of Scope）**：

- FR-004-03 Milvus 向量去重（留 Wave 9/10 接 RAG 模块时同步做）
- PRISMA 真实「人工筛选纳入/排除」阶段（只预留，不做交互）
- PDF 下载、引用格式导出（留 R005 论文阅读模块）
- CNKI / Wanfang 真实机构 API 对接（只留 stub，接口不硬拆）

## 2. 架构与数据流

（与用户在浏览器中确认的 4 段图一致，此处文字复现）：

```
① 用户点击「运行检索」 ──▶ POST /search-runs  (新建 SearchRun + N*SearchRunSource pending)
                                   │
                                   ▼
               ② asyncio worker 轮询（同进程，startup 启动）
                    ├── PubMed adapter    → NCBI E-utilities esearch/efetch
                    ├── CNKI adapter      → stub + 可注入 mock
                    └── Wanfang adapter   → stub + 可注入 mock
                                   │
                                   ▼
               ③ 统一管道（复用 Wave 6/7 + 新增 BM25）
                    ├── DOI/PMID/标题 规范化
                    ├── 三级去重（SearchRun 内先跨库，再查项目已存）
                    ├── 写入 LiteratureRecord + ImportBatch (关联 search_run_source_id)
                    └── BM25 评分 → relevance_score
                                   │
                                   ▼
               ④ 输出 4 个 UI 面板
                    ├── 🔍 检索运行面板（实时进度 / 每库命中 / 错误摘要）
                    ├── 📊 PRISMA 筛选漏斗（Identification / Screening / Eligibility / Included）
                    ├── 🏷️ PICO 面板（每条记录 P/I/C/O，可一键回填检索式）
                    └── 📚 文献条目库（Wave 7 + 新增 BM25 排序开关）
```

后台 worker 实现：**同进程 asyncio 轮询 + DB 持久化状态**（推荐方案 A 已确认）。关键参数：

- 轮询间隔：`SEARCH_WORKER_POLL_SECONDS=1`（配置可调）
- 每 SearchRun 并行 source 上限：`SEARCH_WORKER_MAX_PARALLEL_SOURCES=3`
- 单 adapter 超时：300 s（HTTP client 级）+ 每条 SearchRunSource 级别单条失败不影响其他库 → SearchRun 状态 = `partial_failed`
- 崩溃恢复：worker 启动时把所有「running 超过 30 分钟」的 SearchRunSource 重置为 `failed`，并把它记入 `error_message`

## 3. 数据模型

（与浏览器中确认一致）。命名统一 snake_case + SQLModel + 显式 FK。

### 3.1 新增表 `SearchRun`

```python
class SearchRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    search_query_version_id: int | None = Field(
        default=None, foreign_key="searchqueryversion.id", index=True
    )
    query_snapshot: str                       # JSON: { p, i, c, o, boolean_text, filters, sources }
    selected_sources: str                     # "pubmed,cnki" 逗号分隔
    status: Literal[
        "pending", "running", "completed",
        "partial_failed", "failed", "cancelled",
    ] = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_hits_raw: int = 0                   # PRISMA #1: Identification (cross-source, pre-dedupe)
    total_after_dedupe: int = 0               # PRISMA #2: Screening (after cross-source dedupe)
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

> 语义约束：
> - `search_query_version_id` **可空**（用户临时跑一个未保存的检索式时，query_snapshot 仍完整保留以便审计）
> - `query_snapshot` 为不可变 JSON 文本，即使后续 SearchQueryVersion 被删除，SearchRun 仍可完整重现

### 3.2 新增表 `SearchRunSource`

```python
class SearchRunSource(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    search_run_id: int = Field(foreign_key="searchrun.id", index=True)
    source_key: str = Field(index=True)       # "pubmed" | "cnki" | "wanfang"
    status: Literal["pending","running","completed","failed"] = "pending"
    hits_on_source: int | None = None         # API 返回的 total（如有）
    records_retrieved: int = 0                # 实际下载条数
    records_imported: int = 0                 # 经 dedupe 后写入 LiteratureRecord 的条数
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    raw_response_excerpt: str | None = None   # 截断 1024 字符，debug 用
```

### 3.3 新增表 `LiteraturePico`

1:1 on `LiteratureRecord`，不直接把 PICO 塞进 LiteratureRecord 的列，为后续方法迭代/重跑保留独立实体。

```python
class LiteraturePico(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="literaturerecord.id", sa_column_kwargs={"unique": True})
    population: str | None = None
    intervention: str | None = None
    comparison: str | None = None
    outcome: str | None = None
    study_type: str | None = None              # "rct" | "observational" | "review" | ...
    extraction_method: str                     # "rule_baseline" 或 "llm:<provider>"
    confidence: float | None = None            # 0..1
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
```

### 3.4 扩展 2 张 Wave 7 已有表

**LiteratureRecord**（3 列新增）：
```python
# 新增
search_run_id: int | None = Field(default=None, foreign_key="searchrun.id")
relevance_score: float | None = None
pico_status: Literal["not_extracted","extracted","failed"] = "not_extracted"
```

**LiteratureImportBatch**（1 列新增）：
```python
# 新增
search_run_source_id: int | None = Field(default=None, foreign_key="searchrunsource.id")
```

### 3.5 PRISMA 视图（不建表）

运行时在 `build_search_run_report(search_run_id)` 服务函数中聚合：

| PRISMA 阶段 | 计算规则 | Wave 8 是否有交互 |
|---|---|---|
| Identification | `SUM(searchrunsource.records_retrieved) WHERE search_run_id=X` | —— |
| Screening | `SearchRun.total_after_dedupe` | —— |
| Eligibility | **= Screening**（下一 Wave 接人工筛选） | 预留入口，显示「下一阶段支持」 |
| Included | **= Eligibility** | 预留入口 |

另加每库 breakdown 条形图（每库 records_retrieved vs records_imported）。

## 4. 多库 Adapter 与 Mock 注入机制

### 4.1 Adapter 接口（Protocol）

```python
class SourceAdapter(Protocol):
    source_key: Literal["pubmed", "cnki", "wanfang"]

    async def run_search(
        self,
        query: NormalizedSearchQuery,     # 已经按 source 语义翻译好的布尔式 / 过滤参数
        ctx: SearchRunContext,             # 带 rate-limit 桶 + logger + project_id
    ) -> AdapterResult: ...
```

统一返回：

```python
class AdapterResult:
    hits_on_source: int | None
    records: list[UnifiedLiteratureEntry]  # {doi, pmid, title, authors, journal, year, abstract, source_key, source_record_id}
    warnings: list[str]
```

### 4.2 三个 Adapter 实现

**PubMedAdapter**（真 NCBI E-utilities）：
- `esearch.fcgi?db=pubmed&term=<bool>&retmax=10000&usehistory=y` → `WebEnv+QueryKey`
- 再 `efetch.fcgi?db=pubmed&query_key=..&WebEnv=..&retmode=xml&retstart=&retbatch=500` 分页拉
- 解析 XML → UnifiedLiteratureEntry（authors 用 "Last, FM" 合并成一条分号分隔字符串；journal ISO abbreviation）
- 速率限制：无 API key → 3 req/s（`rate-limits.pubmed.rps=3`）；有 `NCBI_API_KEY` 环境变量 → 10 req/s
- **测试模式**：通过 `tests/` 内 `monkeypatch` 把 HTTP 层替换为本地 XML fixture（不依赖外网）

**CnkiAdapter / WanfangAdapter**（stub + 可注入 mock）：
- 默认行为：检查配置里是否注册了「Mock Dataset Provider」；未注册 → 返回 `records=[] + warnings=["CNKI adapter is a stub; mock dataset not registered."]`
- 注入机制：`app.dependency_overrides` + `MockSourceDataset` 注册表，测试 / 演示时注入（如内置一个「二甲双胍心血管」主题 200 条合成数据集）
- 保留 `future_hooks/` 空实现文件（`cnki_real_hints.py` / `wanfang_real_hints.py`）注释说明真实 API 对接的字段映射，后续 Wave 接入时只改 Adapter，不影响上游

### 4.3 PICO 抽取双引擎

默认引擎 `rule_baseline`（零 LLM 依赖）：
- `Population`：从 title/abstract 中匹配预设临床学科词表（「2 型糖尿病患者」「急性心梗」「老年高血压」…）+ 人口学正则（`\d+.*岁`、男/女比例）
- `Intervention / Comparison`：MeSH 词前缀匹配 + 常见药物/手术类白名单（「二甲双胍」「PCI」「SGLT2i」「安慰剂」…）
- `Study type`：正则（`随机` / `RCT` / `对照` / `回顾性` / `队列` / `meta.?analysis`）
- `confidence`：启发式（命中的词典条目数加权 / 最高可能权重）

可选引擎 `llm:<provider>`（通过 get_llm_config 注入，不开就完全不引 HTTP）：
- Prompt 固定结构：`「请从以下题录中抽取 PICO + study type，严格 JSON 返回」+ system 约束（无多余文字）`
- 失败 fallback 到 rule_baseline，`extraction_method` 记 `llm:claude+fallback_rule` 以便审计

> 与 PRD §6.1.4 R007 方案生成引擎的接口边界一致：PICO 统一由 `LiteraturePico` 实体承载，后续 R006/R007 直接复用而无需再抽。

### 4.4 BM25 相关性评分

在所有库记录进入 LiteratureRecord **之后**、同一 SearchRun 范围内统一执行一次：
- 语料：`title + " " + abstract`（中文保留；英文按 `\W+` 分词；无 stop word 词典以避免语言错误）
- 库：`rank_bm25.BM25Okapi`（单文件依赖）
- 查询词：SearchRun 的 `I+P+O` 非空槽（布尔词拆空格、MeSH 词条去修饰）
- 产出：`LiteratureRecord.relevance_score`，空/全停用/无查询则置 null
- UI：在「条目列表」顶部提供切换：`默认排序（按 ID 倒序）/ BM25 相关性（高→低）/ 年份倒序 / 期刊`

## 5. API 设计

**路由前缀**：`/api/workspace/projects/{project_id}/stages/search/`（与 Wave 5/7 同组，已确认）。所有端点统一鉴权：`_load_project_or_404(project_id, current_user, require_role="member")` → try 块内捕获 `LiteratureError / NotFound` → 422/404 映射（Wave 7 Fix 4 模式）。

### 5.1 SearchRun 执行与观测（6）

| # | 方法 | 路径 | 说明 | 关键响应 / 错误 |
|---|---|---|---|---|
| S1 | POST | `/search-runs` | 新建并启动一次检索运行 | 请求：`{search_query_version_id?:int, query_snapshot?:object, sources:[..]}`；响应 `201 SearchRunSummary`；错误：`422 未选任何源` / `422 snapshot 和 version_id 全空` |
| S2 | GET | `/search-runs` | 项目内检索运行列表（分页） | `{items:[SearchRunSummary], total, page}`；默认 `order_by=-created_at` |
| S3 | GET | `/search-runs/{run_id}` | 单条运行详情 | `SearchRunDetail { run, sources:[SearchRunSourceSummary], prisma, per_source_breakdown, records_count }` |
| S4 | POST | `/search-runs/{run_id}/cancel` | 取消（pending/running → cancelled） | `200 {status:"cancelled"}`；对已完成的返回 `422 already_finished` |
| S5 | POST | `/search-runs/{run_id}/retry` | 对 failed / partial_failed 的 source 重试 | `202 {restarted_sources:[..]}` |
| S6 | GET | `/search-runs/{run_id}/export.csv` | PRISMA + 每库明细 + 去重后文献 ID 清单导出 | `Content-Type: text/csv`，文件名 `search-run-{id}-{YYYYMMDD}.csv` |

### 5.2 运行时进度（1，轻量轮询优化）

| # | 方法 | 路径 | 说明 |
|---|---|---|---|
| S7 | GET | `/search-runs/{run_id}/status` | 只返回 `{status, finished_sources, total_sources, started_at, eta_seconds?}`，字段少，便于前端 2s 轮询拉 |

> 不引 SSE / WS（前端复杂度 + 移动端兼容成本高），用轻量轮询 + HTTP 缓存 ETag，后端对未变化的 SearchRun 直接 304。

### 5.3 PICO 抽取（3）

| # | 方法 | 路径 | 说明 | 关键响应 / 错误 |
|---|---|---|---|---|
| P1 | POST | `/records/pico:batch-extract` | 对 `{record_ids:[..], method?: "rule_baseline" | "llm"}` 批量抽 PICO | 响应 `{processed:N, already_had:M, failed:K}`，异步（用和检索同一个 worker loop 的另一个队列槽位，不新建 worker） |
| P2 | GET | `/records/{record_id}/pico` | 读单条 PICO（含置信度、方法） | `200 LiteraturePicoResponse` or `404` |
| P3 | POST | `/search-runs/{run_id}/pico:autofill-query` | 将该 SearchRun 下 **高频 P/I/C/O** 回写到检索式编辑器 | 返回回填草稿 `{p:string,i:string,c:string,o:string, supporting_records:[top5Ids]}`（不直接保存版本，前端弹确认保存） |

### 5.4 BM25 排序 + 条目库扩展（2）

| # | 方法 | 路径 | 说明 |
|---|---|---|---|
| B1 | POST | `/search-runs/{run_id}/recompute-bm25` | 重跑一次 BM25（例：改了检索式词集后重算） | `202 { queued: true }` |
| B2 | GET | `/literature`（Wave 7 已存在，扩展 query） | 新增查询参数：`sort=relevance|year_desc|id_desc|journal`、`search_run_id=X`（仅看某 SearchRun 命中的）、`min_score=0.3` | 复用 `LiteratureLibrarySummary` + 新字段 `applied_sort` |

### 5.5 错误码统一

除 Wave 7 已有 `LiteratureError / LiteratureNotFoundError` → 422/404，新增 2 个 Wave 8 专用错误：

```python
class SearchRunError(LiteratureError):  # 仍走 422
    code: Literal[
        "no_sources_selected",
        "nothing_to_retry",
        "already_finished",
        "adapter_not_registered",
        "rate_limit_exceeded",
    ]

class PicoExtractionError(LiteratureError):
    code: Literal["no_records_provided", "llm_not_configured", "pico_failed"]
```

## 6. UI / UX 设计（Web + Desktop 共用 shared-ui 组件）

新增 2 个 shared-ui 组件 + 扩展 1 个 Wave 7 组件：

### 6.1 新增 `SearchRunListScreen`（检索运行面板入口）

Wave 5 的 Stage Entry 的「检索阶段」增加第 3 个 Tab：
1. 检索式编辑器（Wave 5）
2. 检索源配置（Wave 6）
3. **🆕 检索运行记录**（本组件）+ 右上角「运行当前检索」主按钮

列表每行展示：
- 运行日期标签（相对时间，复用 Wave 7 `_format_created_at_label` 的语义，纯函数抽到 shared-ui）
- 状态 chip：`pending（灰）/ running（蓝·脉冲·进度%）/ completed（绿）/ partial_failed（橙）/ failed（红）/ cancelled（中性灰）`
- 每库小徽章：`PubMed 1242/1205`（records_retrieved/imported，颜色按 success / warning）
- 右对齐 PRISMA 计数小条（Identification → Screening 两个数）

### 6.2 新增 `SearchRunDetailScreen`（运行详情 + PRISMA 面板）

分 3 个 section：
1. **顶部概览卡**：开始/结束时间、耗时秒、所用检索式版本链接、所用过滤、运行 / 取消 / 重试按钮、CSV 导出按钮
2. **🆕 PRISMA 筛选漏斗图**（SVG，纯组件无 chart lib 依赖，4 个横条宽度递减 + 每段差值箭头显示被排除数，左列中文标签「识别 / 筛选 / 合格 / 纳入」，后两档显示「下一阶段支持」），下面接 per-source 双条分组条形图（retrieved vs imported，每组一个 source）
3. **每库执行明细**：SearchRunSource 卡片（绿/橙/红状态 + 错误 message（若有）+ 「重跑该库」按钮，点击展开 `raw_response_excerpt` 小框）
4. **关联文献条目短列表**：只列出本 SearchRun 的 records（top 200，可「打开完整库」跳转），复用 Wave 7 的 LiteratureRecord 条目子组件

### 6.3 扩展 Wave 7 `LiteratureLibraryScreen.tsx`

新增：
- 顶部排序下拉：`默认（入库顺序）/ BM25 相关性（高→低）/ 最新发表 / 期刊`
- 当在 `SearchRunDetail` 中点击「打开完整库」时，传入 `initialFilter.search_run_id`，组件右上角显示上下文面包屑「范围：检索运行 #123 · 清除筛选」
- 单条记录 hover 时右侧多出 🏷️ 小图标，点击弹出 PICO 抽屉（小型 drawer，不引额外库）展示 P/I/C/O + study_type + 置信度 + 「加入检索式草稿」

### 6.4 新增 `PicoPanel`（shared-ui 小组件）

在 LiteratureLibraryScreen / SearchRunDetail 中复用：
- 4 个标签式 Pill（P / I / C / O），空态占位灰
- 右下「抽取 PICO（批量）」按钮（空 > 20 条时建议批量抽取）
- 「高频 PICO 回写到检索式」按钮 → 弹确认对话框「将以下建议回填为检索式草稿，是否继续？」→ 确定后调 P3 API 跳回 Wave 5 编辑器草稿页

## 7. 服务内部职责划分

延续 Wave 7 模式：**路由层薄、服务层纯函数（依赖注入 session）**。新增 / 修改文件：

| 路径 | 内容 |
|---|---|
| `apps/agent-core/app/models.py` | 新增 `SearchRun / SearchRunSource / LiteraturePico` + 扩展 2 张 Wave 7 表 |
| `apps/agent-core/app/schemas.py` | 新增 SearchRunSummary / Detail / PicoResponse 等 Pydantic；`Literal[status]` 约束 |
| `apps/agent-core/app/services/search_run.py`（新） | SearchRun 生命周期：创建 / 取消 / 重试 / 报告 / CSV 导出 |
| `apps/agent-core/app/services/search_worker.py`（新） | asyncio 轮询主循环 + `run_one_source()` 调 adapter |
| `apps/agent-core/app/services/sources/__init__.py`（新） | adapter 注册表；`get_source_adapter(source_key)` Factory |
| `apps/agent-core/app/services/sources/pubmed_adapter.py`（新） | NCBI E-utilities 实现 |
| `apps/agent-core/app/services/sources/cnki_adapter.py`（新） | stub + 注入 mock 机制 |
| `apps/agent-core/app/services/sources/wanfang_adapter.py`（新） | stub + 注入 mock 机制 |
| `apps/agent-core/app/services/pico.py`（新） | 双引擎抽取 + 批量队列 |
| `apps/agent-core/app/services/bm25_scoring.py`（新） | rank_bm25 封装 + relevance_score 写回 |
| `apps/agent-core/app/routers/workspace.py` | 新增 §5 的 13 个端点（保持 try 包裹 + LiteratureError 捕获） |
| `apps/agent-core/app/main.py` | startup 事件：启动 worker loop；shutdown 事件：`graceful_stop.set()` 等 2 秒内完成中的单个 source |
| `packages/shared-sdk/src/client.ts` | 新增 13 端点方法，统一 `handleResponse<T>`（Wave 7 Fix 6） |
| `packages/shared-ui/src/SearchRunListScreen.tsx`（新） | 检索运行列表 |
| `packages/shared-ui/src/SearchRunDetailScreen.tsx`（新） | 运行详情 + PRISMA 图 + 每库明细 |
| `packages/shared-ui/src/PicoPanel.tsx`（新） | PICO 展示 + 批量抽取按钮 |
| `packages/shared-ui/src/LiteratureLibraryScreen.tsx` | 扩展：排序下拉、run_id 筛选上下文、BM25 星标、PICO 抽屉 |

## 8. 测试策略（TDD 顺序）

沿用 Wave 7 模式：**先写测试 → 再实现 → 全量回归**。

### 8.1 后端 pytest（预期 +40 用例，Wave 7 88 → 总 ≥ 128）

| 类别 | 要点 | 用例数估计 |
|---|---|---|
| models/schemas | Literal status、FK 约束（外键级联删除禁用 LiteratureRecord 不删 SearchRun）、snapshot JSON 往返 | ~6 |
| search_run 服务层 | 创建（空 sources 拒绝；snapshot 全空拒绝；version_id 可选）、取消 / 重试边界、PRISMA 聚合正确 | ~10 |
| adapter 层（含注入 mock） | PubMed 假 HTTP fixture（monkeypatch httpx.AsyncClient）→ esearch/efetch 分页、XML 解析、rate-limit 桶；CNKI/Wanfang 默认 stub 返回 0 条 + warning；注入后能出 20 条记录 | ~10 |
| worker 循环（关键） | 「创建 3 个 pending source → 推进到 running/completed → SearchRun 状态合并为 completed / partial_failed」；「重启后重置超时 running 为 failed」；「cancel 中断 pending 不影响已 running 单个」 | ~7 |
| PICO 双引擎 | rule_baseline 命中 2 型糖尿病 + RCT 合成题录；llm 未配置时使用 rule；batch P1 对已 extracted 跳过；失败写到 `pico_status=failed` | ~5 |
| BM25 + library API 扩展 | B1 重跑后评分有变化；B2 排序参数 + min_score 过滤生效 | ~3 |
| 端到端 API | S1→S7 轮询→S3 详情正确；S6 CSV 导出；异常映射（LiteratureError→422，NotFound→404） | ~5（与服务层重叠，部分集成） |

### 8.2 shared-sdk vitest（预期 +13，Wave 7 14 → 总 27）

每个 S1~S6 / S7 / P1~P3 / B1~B2 对应一条手写 fetch mock + 参数断言，保持 Wave 7 session.test.ts 模式。

### 8.3 shared-ui vitest（预期 +12，Wave 7 16 → 总 28）

- PRISMA 纯组件（不引 SVG 库）：传入 4 个数字后 4 段宽度比例正确、差值箭头数字匹配
- SearchRun 状态 chip：6 种状态颜色 / 脉冲 / 文案正确
- LiteratureLibraryScreen 扩展：排序下拉 4 项触发筛选回调；BM25 分>0 时显示 ⭐ 分数角标

### 8.4 web / admin / desktop 集成测试

web（Wave 7 5）+ admin（1）+ desktop（5）不变。Wave 8 增加的 shared-ui 组件在 shared-ui 单元测试覆盖，无需每端重测。

### 8.5 Wave 8 全量回归目标（对比 Wave 7 基线 129）

| 端 | Wave 7 基线 | Wave 8 目标 |
|---|---|---|
| agent-core pytest | 88 | ≥ 128 |
| shared-sdk vitest | 14 | ≥ 27 |
| shared-ui vitest | 16 | ≥ 28 |
| web vitest | 5 | 5 |
| admin vitest | 1 | 1 |
| desktop vitest | 5 | 5 |
| **合计** | **129** | **≥ 194** |

## 9. 非功能与运维点

- **配置热插拔**：`[search]` INI 节：`worker_poll_seconds`、`max_parallel_sources`、`pubmed_api_key`（可空）、`bm25_min_score`、`adapter_mock_dataset=metformin_cardio_200`
- **速率限制（PubMed 硬约束）**：在 `SearchRunContext` 内放一个 `asyncio.Semaphore(max_per_second)` + 时间窗口计数；超过则 sleep 而非抛错
- **可观测**：每个 SearchRunSource 写入完成后 `logger.info("source_finished", ..)` 结构化日志；SearchRun 状态跃迁记 `audit.AuditEvent`（Wave 6 已有 audit 服务）
- **停止优雅**：FastAPI shutdown 时发送停止事件，worker 等 2 s 内当前单个 source 任务完成，未完成的 SearchRunSource 下一轮启动时判定超时
- **安全**：S6 CSV 导出的文件名严格白名单 `[a-z0-9_-]{1,64}.csv`，内容只放 ASCII / 中文 UTF-8 BOM；不把 `raw_response_excerpt` 放 CSV（只放 S3 详情 API）

## 10. 分阶段实现里程碑（供 writing-plans 细化）

预估拆分为 10 个 Task（供 writing-plans 列 checklist）：

1. **Models + Schemas + 迁移（新增 SearchRun / SearchRunSource / LiteraturePico + 扩展列）**
2. **adapter 注册表 + 接口 Protocol + 3 个 Adapter（PubMed 真 / CNKI stub / Wanfang stub）**
3. **asyncio worker loop（SearchRun / SearchRunSource 状态机 + 启动/关闭钩子 + 超时重置）**
4. **search_run 服务 + S1/S2/S3/S4/S5/S6/S7 路由（7 个端点）**
5. **BM25 scoring 服务 + B1/B2 library 扩展（共享 Wave 7 literature.py）**
6. **PICO 双引擎 rule_baseline + llm 注入 + P1/P2/P3 路由**
7. **shared-sdk 13 个新端点方法（ApiError + handleResponse 复用）**
8. **shared-ui SearchRunListScreen + SearchRunDetailScreen（PRISMA SVG 组件 + per-source 条形图）**
9. **shared-ui LiteratureLibraryScreen 扩展（排序 / run 筛选上下文 / PicoPanel drawer）+ PicoPanel**
10. **后端 40 + SDK 13 + UI 12 新测试 + 5 端全量回归**
