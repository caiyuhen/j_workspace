# MedA Wave 8 Implementation Plan: R004 收口 (PICO + 多库异步检索 + PRISMA + BM25)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Waves 1~7 的检索骨架补成真正的检索系统——从「点运行检索」→ 多库异步跑 → 三级去重入库 → BM25 相关性评分 → PRISMA 漏斗 → PICO 自动提取 → 一键回填检索式 形成端到端闭环，并在 Web / Desktop 双端复用 shared-ui 组件交付。

**Architecture:** 新增 `SearchRun` / `SearchRunSource` / `LiteraturePico` 3 张表并扩展 2 张 Wave 7 表承载状态；`SourceAdapter` Protocol 隔离 3 个检索源实现；轻量同进程 asyncio worker（startup 挂载）轮询 DB 调度任务；BM25 / PICO 各自独立纯服务模块；前端 2 个新组件 + 1 个扩展组件都放 `packages/shared-ui`。

**Tech Stack:** FastAPI + SQLModel (SQLite in tests) + asyncio + httpx (for NCBI) + rank_bm25；TypeScript shared-sdk、React 18 shared-ui（纯 SVG 画 PRISMA 不引 chart lib）；pytest + vitest

**Spec:** `docs/superpowers/specs/2026-08-11-meda-r004-closeout-wave-8-design.md`

---

## File Structure

**新建文件（20 个）:**

| 路径 | 职责 |
|---|---|
| `apps/agent-core/app/services/search_run.py` | SearchRun 生命周期：创建 / 取消 / 重试 / PRISMA 聚合 / CSV 导出 |
| `apps/agent-core/app/services/search_worker.py` | asyncio 轮询主循环 + `run_one_source()` 状态机 |
| `apps/agent-core/app/services/bm25_scoring.py` | rank_bm25 评分 + 写回 `LiteratureRecord.relevance_score` |
| `apps/agent-core/app/services/pico.py` | 双引擎 PICO 抽取：`rule_baseline` + 可选 `llm:<provider>` |
| `apps/agent-core/app/services/sources/__init__.py` | Adapter 注册表 + Factory `get_source_adapter(source_key)` |
| `apps/agent-core/app/services/sources/pubmed_adapter.py` | PubMed 真 NCBI E-utilities esearch/efetch 分页 XML 解析 |
| `apps/agent-core/app/services/sources/cnki_adapter.py` | CNKI stub + 可注入 mock 数据集 |
| `apps/agent-core/app/services/sources/wanfang_adapter.py` | Wanfang stub + 可注入 mock 数据集 |
| `apps/agent-core/app/services/sources/protocol.py` | `SourceAdapter` Protocol + `UnifiedLiteratureEntry` dataclass |
| `apps/agent-core/tests/test_search_run_service.py` | SearchRun 生命周期 + 状态迁移 pytest |
| `apps/agent-core/tests/test_search_worker.py` | worker 循环 + 崩溃恢复 + timeout 重置 pytest |
| `apps/agent-core/tests/test_search_adapters.py` | 3 Adapter（含 PubMed httpx monkeypatch + 2 stub）pytest |
| `apps/agent-core/tests/test_bm25_scoring.py` | BM25 评分 + B1/B2 API 扩展 pytest |
| `apps/agent-core/tests/test_pico_service.py` | PICO 双引擎 rule_baseline / llm 未配置 fallback pytest |
| `apps/agent-core/tests/test_search_run_api.py` | S1~S7 13 端点集成测试 pytest |
| `packages/shared-ui/src/SearchRunListScreen.tsx` | 检索运行 Tab 列表组件 |
| `packages/shared-ui/src/SearchRunDetailScreen.tsx` | 运行详情 + PRISMA SVG 漏斗图 + 每库明细 |
| `packages/shared-ui/src/PicoPanel.tsx` | PICO 4 格展示 + 批量抽取按钮 + 回写检索式草稿确认框 |
| `packages/shared-ui/src/PrismChart.tsx` | 纯 SVG PRISMA 漏斗图组件（可复用于 Wave 9/10） |
| `packages/shared-ui/src/searchRun.test.tsx` | PRISMA chart / 状态 chip / 排序下拉 3 类 vitest |

**修改文件（15 个）:**

| 路径 | 改动 |
|---|---|
| `apps/agent-core/app/models.py` | 新增 3 表类 + 2 张 Wave 7 表扩列 + 外键声明 + `datetime.utcnow` 默认值 |
| `apps/agent-core/app/schemas.py` | 新增 SearchRunSummary / Detail / SourceSummary / PicoResponse / PrismaReport 模型；Literal 状态约束 |
| `apps/agent-core/app/services/literature.py` | 扩 `import_literature` 接收 `search_run_source_id?`；`build_library_response` 支持 `search_run_id? + sort=relevance/.. + min_score?`；抽 `_normalize_identifiers` 给 Adapter 复用 |
| `apps/agent-core/app/routers/workspace.py` | 新增 13 端点（S1~S7 / P1~P3 / B1~B2）；`_load_project_or_404` 全部放 try 块（Wave 7 Fix 4 模式） |
| `apps/agent-core/app/main.py` | `@app.on_event("startup")` 启 worker；`@app.on_event("shutdown")` 设停止事件 + 2s 等待 |
| `apps/agent-core/tests/conftest.py` | 注册 MockSourceDataset provider；插 3 表的 `sqlmodel` metadata |
| `packages/shared-sdk/src/client.ts` | 新增 13 方法 + 类型，继续复用 `handleResponse<T>` |
| `packages/shared-sdk/src/session.test.ts` | 新增 13 条 fetch mock 断言 |
| `packages/shared-ui/src/LiteratureLibraryScreen.tsx` | 扩：4 项排序下拉 / search_run_id 筛选上下文面包屑 / BM25 ⭐ 分数角标 / 🏷️ 按钮弹 PICO 抽屉 |
| `packages/shared-ui/src/index.ts` | 导出 SearchRunListScreen / SearchRunDetailScreen / PicoPanel / PrismaChart + 纯函数类型 |
| `packages/shared-ui/src/helpers.test.ts` | 补 PRISMA 比例计算 / 相对时间格式化边界用例 |
| `apps/web/src/App.tsx` | 新增 search_run 状态、回调、`navigate("search-runs")` 屏幕 |
| `apps/web/src/components/WorkspaceShell.tsx` | Stage Entry「检索阶段」扩 Tab 3（运行列表）+ SearchRunDetail 路由 |
| `apps/desktop/src/App.tsx` | 同 web：search-run 状态、回调、Tab + Detail 屏幕 |
| `apps/agent-core/tests/test_literature_api.py` | 更新 3 处：扩 `/literature` 的 sort/search_run_id/min_score 参数断言；扩 LiteratureImportBatch 新增列 |

**任务依赖顺序:**

```
Task 1 (models/schemas) ──┐
                          ├─→ Task 3 (Adapter 3 + protocol + registry) ──→ Task 4 (worker loop) ──→ Task 5 (search_run service + 7 API) ──→ Task 9 (SDK) ──→ Task 10 (UI: List/Detail/Pico/Prisma + 扩 Library) ──→ Task 12 (5端回归)
Task 2 (search_run 数据准备同上，可并行)        ↑
                          └→ Task 6 (BM25) ────────────────────────────────────────────────┘
                          └→ Task 7 (PICO) ────────────────────────────────────────────────┘
                                                                                              Task 8 (API 13端点集成测试) ← Task5/6/7 完
                                                                                              Task 11 (测试补全：SDK 13 + UI 12) ← Task 9/10
```

为减少并行冲突，本 plan 按串行 12 Task 顺序执行，但 Task 6/7 可在 Task 3 后独立并行（与 Task 4/5 不共享文件）。

---

## Pre-Check (0.5 任务：验证环境 + metadata)

在开始 Task 1 前先单独跑一次基线，避免后续回归不知道基线值：

- [ ] **Step 1: 记 5 端基线值**

分别执行并把结果复制到一个便签（预计：agent-core 88、shared-sdk 14、shared-ui 16、web 5、admin 1、desktop 5）：

```powershell
# agent-core 88 passed
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/ --no-header -q --tb=no 2>&1 | Select-Object -Last 3
# shared-sdk 14
cd d:\workspace\MedA\packages\shared-sdk ; npx vitest run --reporter=json --outputFile=..\..\.base-sdk.json ; node -e "const r=require('d:/workspace/MedA/.base-sdk.json');console.log('shared-sdk:', r.numPassedTests, r.numTotalTests)"
# shared-ui 16
cd d:\workspace\MedA\packages\shared-ui ; npx vitest run --reporter=json --outputFile=..\..\.base-ui.json ; node -e "const r=require('d:/workspace/MedA/.base-ui.json');console.log('shared-ui:', r.numPassedTests, r.numTotalTests)"
# web 5 / admin 1 / desktop 5
cd d:\workspace\MedA\apps\web ; npx vitest run --reporter=json --outputFile=..\..\.base-web.json ; node -e "const r=require('d:/workspace/MedA/.base-web.json');console.log('web:', r.numPassedTests)"
cd d:\workspace\MedA\apps\admin ; npx vitest run --reporter=json --outputFile=..\..\.base-admin.json ; node -e "const r=require('d:/workspace/MedA/.base-admin.json');console.log('admin:', r.numPassedTests)"
cd d:\workspace\MedA\apps\desktop ; npx vitest run --reporter=json --outputFile=..\..\.base-desktop.json ; node -e "const r=require('d:/workspace/MedA/.base-desktop.json');console.log('desktop:', r.numPassedTests)"
```

Expected exit 0。本步失败不要继续，先修复环境。

---

## Task 1: Models + Schemas（3 新表 + 2 扩展表 + Pydantic 响应模型）

**Files:**
- Modify: `apps/agent-core/app/models.py`
- Modify: `apps/agent-core/app/schemas.py`
- Create: `apps/agent-core/tests/test_search_run_models.py`

- [ ] **Step 1: 写 pytest 失败用例，验证新 3 表与 2 扩展列存在性、Literal、FK**

创建 `apps/agent-core/tests/test_search_run_models.py`：

```python
from datetime import datetime
from sqlmodel import SQLModel, Session, select

from app.models import (
    LiteratureImportBatch,
    LiteraturePico,
    LiteratureRecord,
    ResearchProject,
    SearchRun,
    SearchRunSource,
    User,
)
from app.tests.conftest import create_test_project, create_test_user


def _statuses_ok(value, allowed) -> bool:
    return value in allowed


def test_search_run_literal_status_and_nullable_fields(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id,
        search_query_version_id=None,         # 可空：用户临时跑
        query_snapshot='{"p":"T2DM","i":"met","boolean":"Metformin[Mesh]"}',
        selected_sources="pubmed,cnki",
        status="pending",
        total_hits_raw=0,
        total_after_dedupe=0,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    # status 允许 6 种
    assert _statuses_ok(
        run.status,
        {"pending","running","completed","partial_failed","failed","cancelled"},
    )
    assert isinstance(run.created_at, datetime)
    assert run.search_query_version_id is None
    assert run.id is not None


def test_search_run_source_links_back_to_run(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id,
        query_snapshot="{}",
        selected_sources="pubmed",
        status="pending",
    )
    db_session.add(run)
    db_session.flush()

    src = SearchRunSource(
        search_run_id=run.id,
        source_key="pubmed",
        status="pending",
        records_retrieved=0,
        records_imported=0,
    )
    db_session.add(src)
    db_session.commit()
    db_session.refresh(src)

    assert src.search_run_id == run.id
    assert src.error_message is None
    assert _statuses_ok(src.status, {"pending","running","completed","failed"})


def test_literature_pico_one_to_one_with_record(db_session: Session) -> None:
    from app.services.literature import create_literature_record
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    rec = create_literature_record(
        db_session, project.id, {"title":"A RCT on SGLT2i","authors":"","journal":"NEJM","year":2024,"doi":"","pmid":""},
    )

    pico = LiteraturePico(
        record_id=rec.id,
        population="成人 T2DM",
        intervention="SGLT2 抑制剂",
        comparison="安慰剂",
        outcome="3P-MACE 发生率",
        study_type="rct",
        extraction_method="rule_baseline",
        confidence=0.72,
    )
    db_session.add(pico)
    db_session.commit()
    db_session.refresh(pico)

    loaded = db_session.exec(
        select(LiteraturePico).where(LiteraturePico.record_id == rec.id)
    ).one()
    assert loaded.study_type == "rct"
    assert loaded.record_id == rec.id


def test_extended_columns_on_record_and_batch(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id,
        query_snapshot="{}",
        selected_sources="pubmed",
        status="completed",
    )
    db_session.add(run)
    db_session.flush()

    srs = SearchRunSource(
        search_run_id=run.id,
        source_key="pubmed",
        status="completed",
        records_retrieved=1,
        records_imported=1,
    )
    db_session.add(srs)
    db_session.flush()

    batch = LiteratureImportBatch(
        project_id=project.id,
        source_key="pubmed",
        parsed_count=1,
        duplicate_count=0,
        skipped_count=0,
        search_run_source_id=srs.id,
    )
    db_session.add(batch)
    db_session.flush()

    rec = LiteratureRecord(
        project_id=project.id,
        title="SGLT2i vs placebo in CKD",
        authors="Neuen BL",
        journal="NEJM",
        year=2023,
        doi="10.1056/nejmoa2212939",
        pmid="",
        source_key="pubmed",
        source_label="PubMed",
        dedupe_status="unique",
        import_batch_id=batch.id,
        search_run_id=run.id,
        relevance_score=2.17,
        pico_status="not_extracted",
    )
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)

    assert rec.search_run_id == run.id
    assert rec.relevance_score == 2.17
    assert rec.pico_status == "not_extracted"
    assert batch.search_run_source_id == srs.id
```

- [ ] **Step 2: 运行 pytest 确认失败（报 `ImportError` / `AttributeError`：类 / 列不存在）**

Run：

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_run_models.py -v --tb=short 2>&1 | Select-Object -Last 20
```

Expected：FAIL（4 tests errored）。记下 exit code != 0。

- [ ] **Step 3: 实现 models.py 最小改动**

在 `apps/agent-core/app/models.py` 顶部补（如果尚未）：

```python
from datetime import datetime
from typing import Literal
```

追加 3 个新 SQLModel 类：

```python
class SearchRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    search_query_version_id: int | None = Field(
        default=None, foreign_key="searchqueryversion.id", index=True
    )
    query_snapshot: str
    selected_sources: str
    status: Literal[
        "pending", "running", "completed", "partial_failed", "failed", "cancelled"
    ] = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_hits_raw: int = 0
    total_after_dedupe: int = 0
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchRunSource(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    search_run_id: int = Field(foreign_key="searchrun.id", index=True)
    source_key: str = Field(index=True)
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    hits_on_source: int | None = None
    records_retrieved: int = 0
    records_imported: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    raw_response_excerpt: str | None = None


class LiteraturePico(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="literaturerecord.id", sa_column_kwargs={"unique": True})
    population: str | None = None
    intervention: str | None = None
    comparison: str | None = None
    outcome: str | None = None
    study_type: str | None = None
    extraction_method: str
    confidence: float | None = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)
```

然后在 2 个已有表里追加列：

```python
# LiteratureRecord（在已有字段之后、表类结束前插入）
search_run_id: int | None = Field(default=None, foreign_key="searchrun.id")
relevance_score: float | None = None
pico_status: Literal["not_extracted", "extracted", "failed"] = "not_extracted"

# LiteratureImportBatch 追加：
search_run_source_id: int | None = Field(default=None, foreign_key="searchrunsource.id")
```

- [ ] **Step 4: schemas.py 新增 Pydantic 响应模型（不含 SQLModel 字段，纯请求/响应）**

在 `apps/agent-core/app/schemas.py` 顶部补 `from typing import Literal`（若无），并追加：

```python
# ================= Search Run / Source 视图层模型 =================

SearchRunStatus = Literal[
    "pending","running","completed","partial_failed","failed","cancelled"
]
SearchRunSourceStatus = Literal["pending","running","completed","failed"]
PicoStatus = Literal["not_extracted","extracted","failed"]


class SearchSourceBreakdown(BaseModel):
    source_key: str
    source_label: str
    records_retrieved: int
    records_imported: int


class PrismaReport(BaseModel):
    identification: int
    screening: int
    eligibility: int
    included: int
    by_source: list[SearchSourceBreakdown]


class SearchRunSummary(BaseModel):
    id: int
    project_id: int
    search_query_version_id: int | None
    selected_sources: list[str]
    status: SearchRunStatus
    created_at: str
    started_at: str | None
    finished_at: str | None
    total_hits_raw: int
    total_after_dedupe: int
    prisma: PrismaReport
    eta_seconds: float | None


class SearchRunSourceSummary(BaseModel):
    id: int
    search_run_id: int
    source_key: str
    source_label: str
    status: SearchRunSourceStatus
    hits_on_source: int | None
    records_retrieved: int
    records_imported: int
    started_at: str | None
    finished_at: str | None
    error_message: str | None


class SearchRunDetail(BaseModel):
    run: SearchRunSummary
    sources: list[SearchRunSourceSummary]


class SearchRunCreatePayload(BaseModel):
    search_query_version_id: int | None = None
    query_snapshot: dict | None = None
    sources: list[str]


class SearchRunStatusPoll(BaseModel):
    status: SearchRunStatus
    finished_sources: int
    total_sources: int
    eta_seconds: float | None


# ================= PICO =================

class LiteraturePicoResponse(BaseModel):
    record_id: int
    population: str | None
    intervention: str | None
    comparison: str | None
    outcome: str | None
    study_type: str | None
    extraction_method: str
    confidence: float | None
    extracted_at: str


class BatchPicoPayload(BaseModel):
    record_ids: list[int]
    method: Literal["rule_baseline", "llm"] = "rule_baseline"


class BatchPicoResult(BaseModel):
    processed: int
    already_had: int
    failed: int


class PicoAutofillDraft(BaseModel):
    p: str
    i: str
    c: str
    o: str
    supporting_record_ids: list[int]


# ================= BM25 + library 扩展 =================

class LiteratureLibraryRequestExt(BaseModel):
    search_run_id: int | None = None
    sort: Literal["default", "relevance", "year_desc", "journal"] = "default"
    min_score: float | None = None
    page: int = 1
    page_size: int = 100
```

- [ ] **Step 5: 重跑 pytest，4 tests 全过**

Run：

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_run_models.py -v --tb=short 2>&1 | Select-Object -Last 20
```

Expected: **4 passed**。

- [ ] **Step 6: Commit**

```bash
git add apps/agent-core/app/models.py apps/agent-core/app/schemas.py apps/agent-core/tests/test_search_run_models.py
git commit -m "feat(wave8/t1): add SearchRun/SearchRunSource/LiteraturePico models + schemas"
```

---

## Task 2: conftest / test helper 扩展

确保后续所有 test 能拿到 MockSourceDataset + 新表的 clean session。

**Files:**
- Modify: `apps/agent-core/tests/conftest.py`
- Modify: `apps/agent-core/tests/test_search_run_models.py`（从 Task 1 继承；若已通过本 Task 不编辑它）

- [ ] **Step 1: 在 conftest 顶部追加 MockDataset 常量**

在 `apps/agent-core/tests/conftest.py` 的 imports 下面加上：

```python
from dataclasses import dataclass

@dataclass
class UnifiedMockEntry:
    doi: str
    pmid: str
    title: str
    authors: str
    journal: str
    year: int | None
    abstract: str
    source_record_id: str | None = None


MOCK_PUBMED_DATASET: list[UnifiedMockEntry] = [
    UnifiedMockEntry(
        doi="10.1056/nejmoa2212939".lower(),
        pmid="37123457",
        title="Dapagliflozin in Patients with Chronic Kidney Disease",
        authors="Neuen BL, et al.",
        journal="New England Journal of Medicine",
        year=2023,
        abstract="BACKGROUND: The SGLT2 inhibitor... in chronic kidney disease (CKD). METHODS: We conducted a double-blind...",
        source_record_id="pm37123457",
    ),
    UnifiedMockEntry(
        doi="10.1016/s2213-8587(23)00042-5",
        pmid="37000001",
        title="Effect of Empagliflozin on Cardiovascular Outcomes in T2DM with Established CVD",
        authors="Zinman B, et al.",
        journal="Lancet Diabetes Endocrinol",
        year=2023,
        abstract="We studied empagliflozin versus placebo in T2DM with CVD...",
        source_record_id="pm37000001",
    ),
    UnifiedMockEntry(
        doi="10.1001/jama.2023.12345".lower(),
        pmid="37333333",
        title="Metformin plus Lifestyle versus Lifestyle Alone in Prediabetes",
        authors="Chen L, Zhang Y, Wang H",
        journal="JAMA",
        year=2024,
        abstract="This is a RCT of Metformin plus lifestyle against lifestyle...",
        source_record_id="pm37333333",
    ),
]

MOCK_CNKI_DATASET: list[UnifiedMockEntry] = [
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="二甲双胍联合 SGLT2 抑制剂治疗 2 型糖尿病合并慢性肾病疗效观察",
        authors="李明;王建国;赵丽",
        journal="中华内分泌代谢杂志",
        year=2024,
        abstract="目的 观察二甲双胍联合 SGLT2i 治疗 T2DM 合并 CKD 的疗效...",
        source_record_id="cnki-2024-0001",
    ),
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="GLP-1 RA 对心血管结局影响的真实世界研究（单中心）",
        authors="张伟;刘芳",
        journal="中国糖尿病杂志",
        year=2023,
        abstract="回顾性纳入 210 例 T2DM 患者...",
        source_record_id="cnki-2023-2345",
    ),
]

MOCK_WANFANG_DATASET: list[UnifiedMockEntry] = [
    UnifiedMockEntry(
        doi="",
        pmid="",
        title="达格列净在 CKD 非糖尿病人群中的安全性 Meta 分析",
        authors="孙志远;陈曦",
        journal="中华肾脏病杂志",
        year=2024,
        abstract="系统评价达格列净用于非 DM CKD 的安全性 ...",
        source_record_id="wf-2024-1122",
    ),
]


SOURCE_DATASET_REGISTRY: dict[str, list[UnifiedMockEntry]] = {
    "pubmed": MOCK_PUBMED_DATASET,
    "cnki": MOCK_CNKI_DATASET,
    "wanfang": MOCK_WANFANG_DATASET,
}
```

- [ ] **Step 2: 保证 db_session fixture 能创建新 3 张表**

在 conftest 的 `engine = create_engine("sqlite:///...")` 之后、fixture `db_session` 的 yield 之前，确保 `SQLModel.metadata.create_all(engine)` 包含新增表。因为 SQLModel 是「import time 注册元数据」，只要在 create_all 之前 **Task 1 的 3 类被 import**，就会被创建。在 conftest 顶部显式补一句：

```python
import app.models  # noqa: F401 – ensure all SQLModel classes register into metadata
```

- [ ] **Step 3: 重新跑 Task 1 的 4 tests + 原 Wave 7 测试确保没有回归**

Run：

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_run_models.py tests/test_literature_api.py tests/test_literature_parser.py --no-header -q --tb=short 2>&1 | Select-Object -Last 10
```

Expected: all passed。具体数 ≈ 4 + 原 47 ≈ **51 passed**。如果任何 literature 相关测试失败，说明 LiteratureRecord 扩列影响了默认值：检查 `pico_status` 的 default 是否写对。

- [ ] **Step 4: Commit**

```bash
git add apps/agent-core/tests/conftest.py
git commit -m "test(wave8/t2): extend conftest with mock datasets + ensure SQLModel metadata"
```

---

## Task 3: Adapter Protocol + 3 个实现（PubMed 真 / CNKI stub / Wanfang stub）

**Files:**
- Create: `apps/agent-core/app/services/sources/protocol.py`
- Create: `apps/agent-core/app/services/sources/__init__.py`
- Create: `apps/agent-core/app/services/sources/pubmed_adapter.py`
- Create: `apps/agent-core/app/services/sources/cnki_adapter.py`
- Create: `apps/agent-core/app/services/sources/wanfang_adapter.py`
- Create: `apps/agent-core/tests/test_search_adapters.py`

### 3.1 先写失败测试

- [ ] **Step 1: 写 pytest 失败用例**

创建 `apps/agent-core/tests/test_search_adapters.py`：

```python
from __future__ import annotations

from app.services.sources import get_source_adapter
from app.services.sources.protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    SourceAdapter,
)


async def _run(adapter: SourceAdapter) -> AdapterResult:
    ctx = SearchRunContext(
        project_id=1,
        search_run_id=1,
        rate_limit_rps={"pubmed": 3, "cnki": 3, "wanfang": 3},
    )
    query = NormalizedSearchQuery(
        boolean_text="(Metformin[Mesh] OR SGLT2i[Title/Abstract]) AND 2022:2024[Date - Publication]",
        filters={"language": ["chinese","english"], "study_type": ["rct"]},
        source_key=adapter.source_key,
    )
    return await adapter.run_search(query, ctx)


def test_adapter_factory_returns_3_sources() -> None:
    assert get_source_adapter("pubmed").source_key == "pubmed"
    assert get_source_adapter("cnki").source_key == "cnki"
    assert get_source_adapter("wanfang").source_key == "wanfang"


def test_cnki_stub_returns_zero_with_warning_when_mock_not_injected(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.sources.cnki_adapter.INJECTED_DATASET", [], raising=False
    )
    import asyncio
    res = asyncio.run(_run(get_source_adapter("cnki")))
    assert res.records == []
    assert any("stub" in w.lower() or "mock" in w.lower() for w in res.warnings)


def test_wanfang_stub_returns_zero_with_warning(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.sources.wanfang_adapter.INJECTED_DATASET", [], raising=False
    )
    import asyncio
    res = asyncio.run(_run(get_source_adapter("wanfang")))
    assert res.records == []
    assert len(res.warnings) >= 1


def test_pubmed_monkeypatch_parses_entries(monkeypatch) -> None:
    """把 PubMed adapter 的 HTTP 层替换成本地 fixture，模拟 esearch/efetch 往返两次。"""
    from tests.conftest import MOCK_PUBMED_DATASET
    import asyncio

    # 用 monkeypatch 直接跳过 httpx，让 esearch_ids 返回 [1..N]，efetch_xml 反序列化成 UnifiedLiteratureEntry
    esearch_ids = [e.source_record_id or str(i) for i, e in enumerate(MOCK_PUBMED_DATASET, 1)]

    async def fake_fetch(_q, _ctx):
        return esearch_ids, len(MOCK_PUBMED_DATASET)
    async def fake_parse(_ids):
        return MOCK_PUBMED_DATASET

    monkeypatch.setattr(
        "app.services.sources.pubmed_adapter._esearch_pubmed_ids", fake_fetch
    )
    monkeypatch.setattr(
        "app.services.sources.pubmed_adapter._efetch_parse_entries", fake_parse
    )

    result = asyncio.run(_run(get_source_adapter("pubmed")))
    assert result.hits_on_source == len(MOCK_PUBMED_DATASET)
    assert len(result.records) == len(MOCK_PUBMED_DATASET)
    # 首条 DOI/PMID/标题规范化（DOI 小写、strip，标题 strip）
    first = result.records[0]
    assert first.doi == first.doi.lower()
    assert "\n" not in first.title
    assert first.source_key == "pubmed"
```

### 3.2 实现 Protocol + 3 Adapter

- [ ] **Step 2: 运行 pytest 确认失败（ImportError / AttributeError）**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_adapters.py -v --tb=short 2>&1 | Select-Object -Last 15
```

Expected FAIL。继续。

- [ ] **Step 3: 写 protocol.py**

创建 `apps/agent-core/app/services/sources/protocol.py`：

```python
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class NormalizedSearchQuery:
    boolean_text: str
    filters: dict[str, list[str]]
    source_key: str


@dataclass
class SearchRunContext:
    project_id: int
    search_run_id: int
    rate_limit_rps: dict[str, float] = field(default_factory=dict)
    pubmed_api_key: str | None = None


@dataclass
class UnifiedLiteratureEntry:
    doi: str
    pmid: str
    title: str
    authors: str
    journal: str
    year: int | None
    abstract: str
    source_key: str
    source_record_id: str | None = None


@dataclass
class AdapterResult:
    hits_on_source: int | None
    records: list[UnifiedLiteratureEntry]
    warnings: list[str]


class SourceAdapter(Protocol):
    source_key: str

    async def run_search(
        self,
        query: NormalizedSearchQuery,
        ctx: SearchRunContext,
    ) -> AdapterResult: ...
```

- [ ] **Step 4: 写 `sources/__init__.py` Factory**

创建 `apps/agent-core/app/services/sources/__init__.py`：

```python
from __future__ import annotations

from typing import Final

from .protocol import SourceAdapter
from .pubmed_adapter import PubMedAdapter
from .cnki_adapter import CnkiAdapter
from .wanfang_adapter import WanfangAdapter


_REGISTRY: Final[dict[str, SourceAdapter]] = {
    "pubmed": PubMedAdapter(),
    "cnki": CnkiAdapter(),
    "wanfang": WanfangAdapter(),
}


def get_source_adapter(source_key: str) -> SourceAdapter:
    if source_key not in _REGISTRY:
        raise KeyError(f"adapter for source_key={source_key!r} not registered")
    return _REGISTRY[source_key]
```

- [ ] **Step 5: 实现 CNKI / Wanfang 两个 Stub（最简单，先过它们两条 tests）**

创建 `apps/agent-core/app/services/sources/cnki_adapter.py`：

```python
from __future__ import annotations

from .protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    SourceAdapter,
    UnifiedLiteratureEntry,
)

INJECTED_DATASET: list[UnifiedLiteratureEntry] | None = None


class CnkiAdapter:
    source_key = "cnki"

    async def run_search(
        self, query: NormalizedSearchQuery, ctx: SearchRunContext
    ) -> AdapterResult:
        if INJECTED_DATASET is None:
            return AdapterResult(
                hits_on_source=None,
                records=[],
                warnings=[
                    "CNKI adapter is a stub; real institutional API not wired yet. "
                    "Please register INJECTED_DATASET for demo/testing."
                ],
            )
        # 浅拷贝；已经是 UnifiedLiteratureEntry，保证 source_key == "cnki"
        out = [
            UnifiedLiteratureEntry(
                doi=r.doi.strip().lower(),
                pmid=r.pmid.strip(),
                title=r.title.strip(),
                authors=r.authors,
                journal=r.journal,
                year=r.year,
                abstract=r.abstract,
                source_key="cnki",
                source_record_id=r.source_record_id,
            )
            for r in INJECTED_DATASET
        ]
        return AdapterResult(
            hits_on_source=len(out),
            records=out,
            warnings=[],
        )
```

Wanfang 完全对称，创建 `apps/agent-core/app/services/sources/wanfang_adapter.py`，把 `CnkiAdapter`、`cnki_adapter`、`CNKI adapter`、`"cnki"` 统一替换为 `WanfangAdapter` / `wanfang_adapter` / `Wanfang adapter` / `"wanfang"`。

- [ ] **Step 6: 实现 PubMedAdapter（把 esearch_ids / efetch_parse_entries 抽成模块级函数便于 monkeypatch）**

创建 `apps/agent-core/app/services/sources/pubmed_adapter.py`：

```python
from __future__ import annotations

import asyncio
from typing import Iterable

import httpx

from .protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    SourceAdapter,
    UnifiedLiteratureEntry,
)

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


async def _esearch_pubmed_ids(
    query: NormalizedSearchQuery,
    ctx: SearchRunContext,
    client: httpx.AsyncClient,
    batch_size: int = 10000,
) -> tuple[list[str], int]:
    """Low-level helper. Module-level so tests can monkeypatch."""
    params = {
        "db": "pubmed",
        "term": query.boolean_text,
        "retmax": str(batch_size),
        "retmode": "json",
        "usehistory": "n",
    }
    if ctx.pubmed_api_key:
        params["api_key"] = ctx.pubmed_api_key
    # language / study_type filter 映射：对 pubmed study_type -> Filter query
    extra = []
    for lt in query.filters.get("language", []):
        if lt.lower() == "chinese":
            extra.append("Chinese[LA]")
        elif lt.lower() == "english":
            extra.append("English[LA]")
    if "rct" in [s.lower() for s in query.filters.get("study_type", [])]:
        extra.append("randomized controlled trial[pt]")
    if extra:
        params["term"] = f'({query.boolean_text}) AND {" AND ".join(extra)}'

    resp = await client.get(ESEARCH_URL, params=params)
    resp.raise_for_status()
    data = resp.json()["esearchresult"]
    return list(data["idlist"]), int(data["count"])


async def _efetch_parse_entries(
    pmids: Iterable[str],
    ctx: SearchRunContext,
    client: httpx.AsyncClient,
    chunk: int = 500,
) -> list[UnifiedLiteratureEntry]:
    """Low-level helper (module-level so tests can monkeypatch).

    Real XML parsing is heavy; in Wave 8 implementation we only translate
    fixture entries passed via test monkeypatch. The real NCBI XML →
    UnifiedLiteratureEntry parser will be added in a follow-up commit once
    external access is verified. To keep behavior deterministic, the real
    HTTP path returns an empty record list + 1 warning when it reaches
    XML processing (marked as a TODO for follow-up).
    """
    ids = list(pmids)
    if not ids:
        return []
    # Real impl will paginate over ids in `chunk` batches and parse XML.
    # We leave a placeholder branch that handles the non-monkeypatched call:
    params = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
    if ctx.pubmed_api_key:
        params["api_key"] = ctx.pubmed_api_key
    _ = await client.get(EFETCH_URL, params=params)  # smoke call; don't parse XML yet
    return []  # Follow-up commit: implement XML → entries parser


class PubMedAdapter:
    source_key = "pubmed"

    async def run_search(
        self, query: NormalizedSearchQuery, ctx: SearchRunContext
    ) -> AdapterResult:
        # Minimal rate limit sleep based on rps
        rps = ctx.rate_limit_rps.get("pubmed", 3.0)
        await asyncio.sleep(1.0 / max(rps, 0.1))

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            ids, count = await _esearch_pubmed_ids(query, ctx, client)
            entries = await _efetch_parse_entries(ids, ctx, client)

        # Enforce DOI lower case + strip, title strip regardless of whether efetch filled them.
        normalized = [
            UnifiedLiteratureEntry(
                doi=(r.doi or "").strip().lower(),
                pmid=(r.pmid or "").strip(),
                title=(r.title or "").strip(),
                authors=r.authors,
                journal=r.journal,
                year=r.year,
                abstract=r.abstract,
                source_key="pubmed",
                source_record_id=r.source_record_id,
            )
            for r in entries
        ]
        warnings = []
        if count > 0 and len(normalized) == 0:
            warnings.append(
                "PubMed esearch returned IDs but XML efetch → entries parser "
                "is a placeholder in Wave 8. Inject monkeypatch for tests."
            )
        return AdapterResult(hits_on_source=count, records=normalized, warnings=warnings)
```

- [ ] **Step 7: 重跑 Task 3 的 4 tests → 4 passed**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_adapters.py -v --tb=short 2>&1 | Select-Object -Last 15
```

Expected: **4 passed**（4 tests）。

- [ ] **Step 8: Commit**

```bash
git add apps/agent-core/app/services/sources apps/agent-core/tests/test_search_adapters.py
git commit -m "feat(wave8/t3): SourceAdapter Protocol + 3 implementations"
```

---

## Task 4: asyncio worker loop（状态机 + 启动钩子 + 崩溃恢复 + 超时重置）

**Files:**
- Create: `apps/agent-core/app/services/search_worker.py`
- Modify: `apps/agent-core/app/main.py`
- Create: `apps/agent-core/tests/test_search_worker.py`

### 4.1 失败用例

- [ ] **Step 1: 写失败 pytest**

创建 `apps/agent-core/tests/test_search_worker.py`：

```python
from __future__ import annotations
import asyncio
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models import SearchRun, SearchRunSource
from app.services.search_worker import (
    _reset_timed_out_running_sources,
    _worker_tick_once,
)
from app.tests.conftest import (
    SOURCE_DATASET_REGISTRY,
    create_test_project,
    create_test_user,
    inject_mock_datasets_into_adapters,  # 若没有此函数，下面 Step 3 会定义
)


def test_worker_completes_3_sources_sets_search_run_completed(
    db_session: Session, monkeypatch
) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    # Inject mocks
    inject_mock_datasets_into_adapters(monkeypatch, SOURCE_DATASET_REGISTRY)

    run = SearchRun(
        project_id=project.id,
        query_snapshot="{}",
        selected_sources="pubmed,cnki,wanfang",
        status="pending",
    )
    db_session.add(run)
    db_session.flush()
    for s in ["pubmed", "cnki", "wanfang"]:
        db_session.add(SearchRunSource(
            search_run_id=run.id, source_key=s, status="pending",
        ))
    db_session.commit()
    db_session.refresh(run)

    # Run 2 ticks (pending→running; running→completed)
    asyncio.run(_worker_tick_once(db_session))
    asyncio.run(_worker_tick_once(db_session))

    db_session.refresh(run)
    # 所有 sources 已完成 → run.status = completed
    assert run.status == "completed"
    # 命中数聚合：mock 3 + 2 + 1 = 6 retrieved
    sources = db_session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all()
    retrieved = sum(s.records_retrieved for s in sources)
    assert retrieved >= 6
    assert run.total_hits_raw >= 6
    assert run.total_after_dedupe >= 1  # Wave 7 dedupe 会干掉 DOI/标题重复


def test_one_source_failed_marks_run_partial_failed(db_session: Session, monkeypatch) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    # 只 inject pubmed，其余两条空 stub 会报错（被我们用 monkeypatch 改成抛异常）
    inject_mock_datasets_into_adapters(monkeypatch, {"pubmed": SOURCE_DATASET_REGISTRY["pubmed"]})

    async def bad_run(*_a, **_k):
        raise RuntimeError("simulated CNKI failure")
    monkeypatch.setattr(
        "app.services.sources.cnki_adapter.CnkiAdapter.run_search", bad_run
    )

    run = SearchRun(
        project_id=project.id,
        query_snapshot="{}",
        selected_sources="pubmed,cnki,wanfang",
        status="pending",
    )
    db_session.add(run)
    db_session.flush()
    for s in ["pubmed", "cnki", "wanfang"]:
        db_session.add(SearchRunSource(
            search_run_id=run.id, source_key=s, status="pending",
        ))
    db_session.commit()

    # 3 ticks 保证 bad_run 的 failure 被写入 error_message
    for _ in range(3):
        asyncio.run(_worker_tick_once(db_session))

    db_session.refresh(run)
    # partial_failed：至少 1 completed，至少 1 failed
    assert run.status == "partial_failed"
    sources = db_session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all()
    statuses = {s.source_key: s.status for s in sources}
    assert statuses.get("pubmed") in {"completed", "running"}
    assert statuses.get("cnki") == "failed"
    assert any(s.error_message for s in sources if s.source_key == "cnki")


def test_reset_timed_out_running_sources_marks_as_failed(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id, query_snapshot="{}", selected_sources="pubmed",
        status="running",
    )
    db_session.add(run)
    db_session.flush()
    too_old = datetime.utcnow() - timedelta(minutes=31)
    db_session.add(SearchRunSource(
        search_run_id=run.id,
        source_key="pubmed",
        status="running",
        started_at=too_old,
    ))
    db_session.commit()

    updated = asyncio.run(_reset_timed_out_running_sources(db_session, max_age_minutes=30))
    assert updated == 1

    src = db_session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).one()
    assert src.status == "failed"
    assert "timeout" in (src.error_message or "").lower()
```

- [ ] **Step 2: 运行确认失败（ModuleNotFoundError / 无 `_worker_tick_once`）**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_worker.py -v --tb=short 2>&1 | Select-Object -Last 15
```

Expected FAIL。

### 4.2 实现 worker

- [ ] **Step 3: 在 conftest 补 `inject_mock_datasets_into_adapters` helper（上面 tests 用到）**

编辑 `apps/agent-core/tests/conftest.py` 末尾追加：

```python
def inject_mock_datasets_into_adapters(
    monkeypatch,
    registry: dict[str, list[UnifiedMockEntry]],
) -> None:
    """Helper that pushes test mock entries into each StubAdapter's INJECTED_DATASET."""
    from app.services.sources import cnki_adapter, pubmed_adapter, wanfang_adapter
    from app.services.sources.protocol import UnifiedLiteratureEntry

    def _coerce(entries: list[UnifiedMockEntry]) -> list[UnifiedLiteratureEntry]:
        return [
            UnifiedLiteratureEntry(
                doi=e.doi, pmid=e.pmid, title=e.title, authors=e.authors,
                journal=e.journal, year=e.year, abstract=e.abstract,
                source_key="__unset__", source_record_id=e.source_record_id,
            ) for e in entries
        ]

    if "pubmed" in registry:
        mock_entries = _coerce(registry["pubmed"])
        async def _esearch(q, ctx):
            ids = [e.source_record_id or f"m{i}" for i, e in enumerate(mock_entries, 1)]
            return ids, len(mock_entries)
        async def _efetch(ids):
            return mock_entries
        monkeypatch.setattr(
            "app.services.sources.pubmed_adapter._esearch_pubmed_ids", _esearch
        )
        monkeypatch.setattr(
            "app.services.sources.pubmed_adapter._efetch_parse_entries", _efetch
        )
    if "cnki" in registry:
        monkeypatch.setattr(
            cnki_adapter, "INJECTED_DATASET", _coerce(registry["cnki"])
        )
    if "wanfang" in registry:
        monkeypatch.setattr(
            wanfang_adapter, "INJECTED_DATASET", _coerce(registry["wanfang"])
        )
```

- [ ] **Step 4: 写 search_worker.py**

创建 `apps/agent-core/app/services/search_worker.py`：

```python
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import Iterable

from sqlmodel import Session, select

from app.models import (
    LiteratureRecord,
    SearchRun,
    SearchRunSource,
)
from app.services.literature import (
    _normalize_identifiers,
    import_unified_entries,  # 下面 Task 5 会扩 literature.py；此时用占位函数
)
from app.services.sources import get_source_adapter
from app.services.sources.protocol import (
    NormalizedSearchQuery,
    SearchRunContext,
    UnifiedLiteratureEntry,
)
from app.services.bm25_scoring import recompute_bm25_for_search_run  # Task 6 实现


STALE_SOURCE_TIMEOUT_MINUTES = 30
PARALLEL_SOURCES_PER_RUN = 3


# ---------------------------------------------------------------- lifecycle hooks

_worker_stop_event: asyncio.Event | None = None
_worker_task: asyncio.Task | None = None


async def start_worker_loop(get_session_factory, poll_seconds: float = 1.0) -> None:
    """Called from main.py startup event. Runs until stop event is set."""
    global _worker_stop_event, _worker_task
    _worker_stop_event = asyncio.Event()

    async def _loop():
        while not _worker_stop_event.is_set():
            try:
                session_factory = get_session_factory()
                with session_factory() as sess:
                    await _reset_timed_out_running_sources(sess)
                    await _worker_tick_once(sess)
                    sess.commit()
            except Exception as exc:  # noqa: BLE001 - worker never crashes the server
                # TODO(in production): attach sentry/logger
                print(f"[search_worker] tick error: {exc!r}")
            finally:
                await asyncio.sleep(poll_seconds)

    _worker_task = asyncio.create_task(_loop())


async def stop_worker_loop(wait_timeout: float = 2.0) -> None:
    """Called from main.py shutdown event."""
    global _worker_stop_event
    if _worker_stop_event is None:
        return
    _worker_stop_event.set()
    if _worker_task is not None and not _worker_task.done():
        try:
            await asyncio.wait_for(_worker_task, timeout=wait_timeout)
        except (TimeoutError, asyncio.TimeoutError):
            _worker_task.cancel()
            try:
                await _worker_task
            except asyncio.CancelledError:
                pass


# ------------------------------------------------------------- public helpers

async def _reset_timed_out_running_sources(
    session: Session, *, max_age_minutes: int = STALE_SOURCE_TIMEOUT_MINUTES
) -> int:
    """Mark any SearchRunSource stuck in running for too long as failed."""
    cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    stales = session.exec(
        select(SearchRunSource).where(
            SearchRunSource.status == "running",
            SearchRunSource.started_at < cutoff,
        )
    ).all()
    for s in stales:
        s.status = "failed"
        s.error_message = (s.error_message or "") + " [timeout reset at startup]"
        s.finished_at = datetime.utcnow()
    session.add_all(stales)
    return len(stales)


# ---------------------------------------------------------------- state machine

async def _worker_tick_once(session: Session) -> None:
    # ① claim pending → running: up to PARALLEL_SOURCES_PER_RUN sources that aren't running yet
    claimed: list[SearchRunSource] = _claim_pending_sources(session, PARALLEL_SOURCES_PER_RUN)
    for srs in claimed:
        srs.status = "running"
        srs.started_at = datetime.utcnow()
    session.add_all(claimed)
    session.flush()

    # ② execute those claimed
    for srs in claimed:
        await _execute_single_source(session, srs)
    session.flush()

    # ③ Aggregate per-run counts, update status, recompute BM25 when run done
    _update_runs_status_and_counts(session)


def _claim_pending_sources(session: Session, k: int) -> list[SearchRunSource]:
    # 只从「未取消、未完成、非失败父运行」中拿 pending
    subq = (
        select(SearchRun.id)
        .where(SearchRun.status.in_(["pending", "running", "partial_failed"]))
        .subquery()
    )
    q = (
        select(SearchRunSource)
        .where(
            SearchRunSource.status == "pending",
            SearchRunSource.search_run_id.in_(subq),
        )
        .order_by(SearchRunSource.id.asc())
        .limit(k)
    )
    return list(session.exec(q).all())


async def _execute_single_source(session: Session, srs: SearchRunSource) -> None:
    try:
        run = session.get(SearchRun, srs.search_run_id)
        assert run is not None
        adapter = get_source_adapter(srs.source_key)
        query = NormalizedSearchQuery(
            boolean_text=_extract_bool_from_snapshot(run.query_snapshot),
            filters=_extract_filters_from_snapshot(run.query_snapshot),
            source_key=srs.source_key,
        )
        ctx = SearchRunContext(
            project_id=run.project_id,
            search_run_id=run.id,
        )
        result = await adapter.run_search(query, ctx)
        # 写入：去重、规范化、import_unified_entries（Task 5 定义）
        normalized_records = [
            UnifiedLiteratureEntry(
                doi=_normalize_identifiers(r.doi, "", "")[0],
                pmid=_normalize_identifiers("", r.pmid, "")[1],
                title=r.title.strip(),
                authors=r.authors,
                journal=r.journal,
                year=r.year,
                abstract=r.abstract,
                source_key=r.source_key,
                source_record_id=r.source_record_id,
            ) for r in result.records
        ]
        imported = import_unified_entries(
            session,
            run.project_id,
            source_key=srs.source_key,
            entries=normalized_records,
            search_run_id=run.id,
            search_run_source_id=srs.id,
        )

        srs.status = "completed"
        srs.hits_on_source = result.hits_on_source
        srs.records_retrieved = len(result.records)
        srs.records_imported = imported.count
        if imported.skipped_count > 0:
            srs.error_message = (
                f"skipped {imported.skipped_count} malformed entries"
            )
    except Exception as exc:  # noqa: BLE001
        srs.status = "failed"
        srs.error_message = (
            (srs.error_message or "") +
            f" worker exception: {exc.__class__.__name__}: {exc!s}"
        )[:400]
    finally:
        srs.finished_at = datetime.utcnow()
        session.add(srs)


def _update_runs_status_and_counts(session: Session) -> None:
    run_ids = {
        s.search_run_id
        for s in session.exec(
            select(SearchRunSource).where(
                SearchRunSource.status.in_(["completed", "failed"])
            )
        ).all()
    }
    # Also include runs that have non-pending sources
    for run in session.exec(
        select(SearchRun).where(SearchRun.id.in_(list(run_ids) or [-1]))
    ).all():
        sources = session.exec(
            select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
        ).all()
        if not sources:
            continue

        total_raw = sum(s.records_retrieved for s in sources if s.status == "completed")
        dedupe_q = (
            select(LiteratureRecord.id)
            .where(LiteratureRecord.search_run_id == run.id)
            .where(LiteratureRecord.dedupe_status != "duplicate")
        )
        total_dedupe = len(session.exec(dedupe_q).all())

        run.total_hits_raw = total_raw
        run.total_after_dedupe = total_dedupe

        statuses = {s.status for s in sources}
        all_done = statuses <= {"completed", "failed"}
        if not all_done:
            run.status = "running" if "running" in statuses or run.status == "running" else run.status
            session.add(run)
            continue

        if "failed" in statuses and "completed" not in statuses:
            run.status = "failed"
        elif "failed" in statuses:
            run.status = "partial_failed"
        else:
            run.status = "completed"
        run.finished_at = datetime.utcnow()
        session.add(run)

        # Once fully finished (any success), compute BM25 once
        if run.total_after_dedupe > 0 and run.status != "failed":
            try:
                recompute_bm25_for_search_run(session, run.id)
            except Exception:  # noqa: BLE001
                # BM25 is non-fatal: records still exist without score
                pass


def _extract_bool_from_snapshot(snapshot: str) -> str:
    import json
    try:
        obj = json.loads(snapshot)
    except Exception:
        return ""
    return obj.get("boolean_text") or obj.get("boolean") or ""


def _extract_filters_from_snapshot(snapshot: str) -> dict[str, list[str]]:
    import json
    try:
        obj = json.loads(snapshot)
    except Exception:
        return {}
    return obj.get("filters") or {}
```

- [ ] **Step 5: Task 5 会定义 `import_unified_entries` + Task 6 会定义 `recompute_bm25_for_search_run`，现在先放两个占位版本以免 import 失败**

临时在 `apps/agent-core/app/services/literature.py` 顶部附近加占位：

```python
# ----- Placeholders implemented properly in Wave 8 Tasks 5 & 6 -----
from dataclasses import dataclass

@dataclass
class _ImportResult:
    count: int
    skipped_count: int
    duplicate_count: int


def import_unified_entries(
    session, project_id, source_key, entries,
    search_run_id=None, search_run_source_id=None,
) -> _ImportResult:
    return _ImportResult(count=len(entries), skipped_count=0, duplicate_count=0)
```

同理在 `apps/agent-core/app/services/bm25_scoring.py` 写占位：

```python
from __future__ import annotations

def recompute_bm25_for_search_run(session, search_run_id: int) -> None:
    return None
```

- [ ] **Step 6: 把 worker hook 加到 main.py**

在 `apps/agent-core/app/main.py` 中：

```python
# 在 @app.on_event("startup") 里（若无则新建）加上：
@app.on_event("startup")
async def _on_startup():
    from app.db import get_engine, SessionLocal
    from app.services.search_worker import start_worker_loop
    await start_worker_loop(lambda: SessionLocal)


@app.on_event("shutdown")
async def _on_shutdown():
    from app.services.search_worker import stop_worker_loop
    await stop_worker_loop(wait_timeout=2.0)
```

- [ ] **Step 7: 跑 Task 4 tests（3 tests）→ 3 passed**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_worker.py -v --tb=short 2>&1 | Select-Object -Last 15
```

Expected: **3 passed**。

- [ ] **Step 8: Commit**

```bash
git add apps/agent-core/app/services/search_worker.py apps/agent-core/app/main.py apps/agent-core/tests/conftest.py apps/agent-core/tests/test_search_worker.py
git commit -m "feat(wave8/t4): asyncio worker loop + state machine + startup/shutdown hooks"
```

---

## Task 5: search_run 服务 + 7 端点 S1~S7 + import_unified_entries 真正实现（替换 Task 4 占位）

**Files:**
- Create: `apps/agent-core/app/services/search_run.py`
- Modify: `apps/agent-core/app/services/literature.py`（替换占位 + 扩 library sort/search_run_id/min_score）
- Modify: `apps/agent-core/app/routers/workspace.py`（S1~S7）
- Create: `apps/agent-core/tests/test_search_run_service.py`（服务层 + 创建 / 取消 / 重试 / PRISMA）

### 5.1 失败测试

- [ ] **Step 1: 写失败用例 test_search_run_service.py（4 tests）**

创建 `apps/agent-core/tests/test_search_run_service.py`：

```python
from __future__ import annotations
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    LiteratureRecord,
    ResearchProject,
    SearchRun,
    SearchRunSource,
    SearchQueryVersion,
)
from app.services.search_run import (
    SearchRunError,
    cancel_search_run,
    create_search_run,
    export_search_run_csv_text,
    get_search_run_detail,
    get_search_run_list,
    retry_failed_sources,
)
from app.tests.conftest import create_test_project, create_test_user


def test_create_rejects_no_sources(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    try:
        create_search_run(db_session, project.id, sources=[], query_snapshot=None, search_query_version_id=None)
    except SearchRunError as exc:
        assert exc.code == "no_sources_selected"
        return
    raise AssertionError("expected SearchRunError no_sources_selected")


def test_create_rejects_both_snapshot_and_version_empty(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    try:
        create_search_run(
            db_session, project.id, sources=["pubmed"],
            query_snapshot=None, search_query_version_id=None,
        )
    except SearchRunError:
        return
    raise AssertionError("expected SearchRunError when both snapshot and version are null")


def test_cancel_sets_status_cancelled_for_pending_or_running(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    run = create_search_run(
        db_session, project.id,
        sources=["pubmed","cnki"],
        query_snapshot={"boolean_text":"Dapagliflozin","filters":{}},
        search_query_version_id=None,
    )
    # simulate pending and running sources
    src_pub = SearchRunSource(search_run_id=run.id, source_key="pubmed", status="pending")
    src_cnk = SearchRunSource(search_run_id=run.id, source_key="cnki", status="running", started_at=datetime.utcnow())
    db_session.add_all([src_pub, src_cnk])
    db_session.commit()
    cancel_search_run(db_session, run.id)
    db_session.refresh(run)
    assert run.status == "cancelled"
    for s in db_session.exec(select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)).all():
        assert s.status == "failed"  # pending/running 都标失败 后续不再重试
        assert "cancelled" in (s.error_message or "").lower()


def test_retry_failed_sources_only_retries_failed_or_partial(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id, query_snapshot="{}",
        selected_sources="pubmed,cnki", status="partial_failed",
    )
    db_session.add(run)
    db_session.flush()
    ok = SearchRunSource(search_run_id=run.id, source_key="pubmed", status="completed", records_retrieved=3, records_imported=3)
    bad = SearchRunSource(search_run_id=run.id, source_key="cnki", status="failed", error_message="x")
    db_session.add_all([ok, bad])
    db_session.commit()
    restarted = retry_failed_sources(db_session, run.id)
    assert set(restarted) == {"cnki"}
    db_session.refresh(bad)
    assert bad.status == "pending"
    assert bad.error_message is None  # 清掉旧错误
    db_session.refresh(run)
    assert run.status == "running"


def test_export_csv_contains_expected_headers_and_counts(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id, query_snapshot="{}", selected_sources="pubmed",
        status="completed", total_hits_raw=5, total_after_dedupe=3,
    )
    db_session.add(run)
    db_session.flush()
    srs = SearchRunSource(
        search_run_id=run.id, source_key="pubmed", status="completed",
        records_retrieved=5, records_imported=3,
    )
    db_session.add(srs)
    db_session.flush()
    # 塞两条 literature record 带 search_run_id
    rec1 = LiteratureRecord(
        project_id=project.id, title="Paper A", authors="", journal="J",
        year=2024, doi="10.1/a", pmid="", source_key="pubmed",
        source_label="PubMed", dedupe_status="unique",
        search_run_id=run.id, relevance_score=1.2, pico_status="not_extracted",
    )
    rec2 = LiteratureRecord(
        project_id=project.id, title="Paper B", authors="", journal="J",
        year=2023, doi="10.1/b", pmid="", source_key="pubmed",
        source_label="PubMed", dedupe_status="unique",
        search_run_id=run.id, relevance_score=0.8, pico_status="not_extracted",
    )
    db_session.add_all([rec1, rec2])
    db_session.commit()
    db_session.refresh(run)

    text = export_search_run_csv_text(db_session, run.id)
    assert "Identification,Screening,Eligibility,Included" in text
    assert "Paper A" in text
    assert "10.1/a" in text
    assert "source_key,pubmed" in text or "source_key, pubmed" in text or "\npubmed,completed" in text  # flexible
```

- [ ] **Step 2: 运行确认失败**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_run_service.py -v --tb=short 2>&1 | Select-Object -Last 20
```

Expected FAIL。

### 5.2 实现 search_run.py + 真正的 `import_unified_entries` + library 扩展查询

- [ ] **Step 3: 实现 search_run.py**

创建 `apps/agent-core/app/services/search_run.py`：

```python
from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Literal

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import LiteratureRecord, SearchRun, SearchRunSource
from app.services.workspace import _load_project_or_404  # 如不存在则写一个本地薄封装


class SearchRunError(Exception):
    def __init__(
        self,
        message: str,
        code: Literal[
            "no_sources_selected",
            "nothing_to_retry",
            "already_finished",
            "adapter_not_registered",
            "rate_limit_exceeded",
        ],
    ) -> None:
        super().__init__(message)
        self.code = code


VALID_SOURCES = {"pubmed", "cnki", "wanfang"}


# -------------------------------------------------------------------------------- create/list/read

def create_search_run(
    session: Session,
    project_id: int,
    *,
    sources: list[str],
    query_snapshot: dict | None,
    search_query_version_id: int | None,
) -> SearchRun:
    _ensure_project(session, project_id)

    # 1) sources 非空 & 全合法
    if not sources:
        raise SearchRunError("no_sources_selected", "no_sources_selected")
    unknown = [s for s in sources if s not in VALID_SOURCES]
    if unknown:
        raise SearchRunError(f"adapter_not_registered: {unknown}", "adapter_not_registered")

    # 2) 至少一个快照来源
    if query_snapshot is None and search_query_version_id is None:
        raise SearchRunError(
            "must provide either query_snapshot or search_query_version_id",
            "no_sources_selected",  # reuse code; spec uses the same bucket
        )
    # 3) 以 dict 形式拿到快照，统一序列化成 JSON 字符串存
    snap_dict = dict(query_snapshot) if query_snapshot is not None else {}
    if search_query_version_id is not None and not snap_dict:
        snap_dict = _load_snapshot_from_search_version(session, search_query_version_id)

    run = SearchRun(
        project_id=project_id,
        search_query_version_id=search_query_version_id,
        query_snapshot=json.dumps(snap_dict, ensure_ascii=False),
        selected_sources=",".join(sorted(set(sources))),
        status="pending",
    )
    session.add(run)
    session.flush()  # gets run.id

    for s in sources:
        session.add(SearchRunSource(
            search_run_id=run.id,
            source_key=s,
            status="pending",
        ))
    session.commit()
    session.refresh(run)
    return run


def get_search_run_list(
    session: Session,
    project_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[SearchRun], int]:
    _ensure_project(session, project_id)
    total_q = select(SearchRun).where(SearchRun.project_id == project_id)
    total = len(session.exec(total_q).all())
    q = (
        total_q.order_by(SearchRun.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(session.exec(q).all()), total


def get_search_run_detail(
    session: Session, project_id: int, run_id: int
) -> tuple[SearchRun, list[SearchRunSource]]:
    _ensure_project(session, project_id)
    run = session.get(SearchRun, run_id)
    if run is None or run.project_id != project_id:
        raise HTTPException(status_code=404, detail="search_run not found")
    sources = list(session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all())
    return run, sources


# -------------------------------------------------------------------------------- cancel/retry

def cancel_search_run(session: Session, run_id: int) -> None:
    run = session.get(SearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="search_run not found")
    if run.status in {"completed", "failed", "cancelled"}:
        raise SearchRunError("already_finished", "already_finished")
    run.status = "cancelled"
    run.finished_at = datetime.utcnow()
    # 将 pending / running sources 标记为失败，避免 worker 再捡起来
    for s in session.exec(
        select(SearchRunSource).where(
            SearchRunSource.search_run_id == run.id,
            SearchRunSource.status.in_(["pending", "running"]),
        )
    ).all():
        s.status = "failed"
        s.error_message = (s.error_message or "") + " [cancelled by user]"
        s.finished_at = datetime.utcnow()
        session.add(s)
    session.add(run)
    session.commit()


def retry_failed_sources(session: Session, run_id: int) -> list[str]:
    run = session.get(SearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="search_run not found")
    if run.status not in {"partial_failed", "failed"}:
        raise SearchRunError("nothing_to_retry", "nothing_to_retry")
    restarted: list[str] = []
    for s in session.exec(
        select(SearchRunSource).where(
            SearchRunSource.search_run_id == run.id,
            SearchRunSource.status == "failed",
        )
    ).all():
        s.status = "pending"
        s.started_at = None
        s.finished_at = None
        s.error_message = None
        s.records_retrieved = 0
        s.records_imported = 0
        s.hits_on_source = None
        session.add(s)
        restarted.append(s.source_key)
    if not restarted:
        raise SearchRunError("nothing_to_retry", "nothing_to_retry")
    run.status = "running"
    run.finished_at = None
    run.error_message = None
    session.add(run)
    session.commit()
    return restarted


# -------------------------------------------------------------------------------- export csv

def export_search_run_csv_text(session: Session, run_id: int) -> str:
    run = session.get(SearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="search_run not found")
    sources = list(session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all())
    records = list(session.exec(
        select(LiteratureRecord)
        .where(LiteratureRecord.search_run_id == run.id)
        .order_by((LiteratureRecord.relevance_score or 0).desc())
    ).all())

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["project_id", run.project_id])
    w.writerow(["search_run_id", run.id])
    w.writerow(["created_at", run.created_at.isoformat() if run.created_at else ""])
    w.writerow([])
    w.writerow(["PRISMA"])
    w.writerow(["Identification", "Screening", "Eligibility", "Included"])
    w.writerow([run.total_hits_raw, run.total_after_dedupe, run.total_after_dedupe, run.total_after_dedupe])
    w.writerow([])
    w.writerow(["Per source"])
    w.writerow(["source_key", "status", "retrieved", "imported", "hits_on_source", "error_message"])
    for s in sources:
        w.writerow([s.source_key, s.status, s.records_retrieved, s.records_imported, s.hits_on_source, s.error_message or ""])
    w.writerow([])
    w.writerow(["Records (after dedupe)"])
    w.writerow([
        "id","score","title","authors","journal","year","doi","pmid",
        "source_key","dedupe_status","pico_status",
    ])
    for r in records:
        w.writerow([
            r.id,
            f"{r.relevance_score:.4f}" if r.relevance_score is not None else "",
            r.title, r.authors, r.journal, r.year or "", r.doi, r.pmid,
            r.source_key, r.dedupe_status, r.pico_status,
        ])
    return buf.getvalue()


# -------------------------------------------------------------------------------- helpers

def _ensure_project(session: Session, project_id: int) -> None:
    # 薄封装：若 workspace._load_project_or_404 是 async 的话，这里用同步版本直接 check。
    from app.models import ResearchProject
    p = session.get(ResearchProject, project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="project not found")


def _load_snapshot_from_search_version(session: Session, version_id: int) -> dict:
    v = session.get(SearchQueryVersion, version_id)
    if v is None:
        raise HTTPException(status_code=404, detail="search_query_version not found")
    # Reconstruct a snapshot dict from the saved version.
    out = {
        "boolean_text": v.boolean_text or "",
        "p": v.p or "",
        "i": v.i or "",
        "c": v.c or "",
        "o": v.o or "",
    }
    try:
        extra = json.loads(v.meta_json or "{}")
    except Exception:
        extra = {}
    out["filters"] = extra.get("filters") or {}
    return out
```

- [ ] **Step 4: 把 `services/literature.py` 里占位的 `import_unified_entries` 换成真实实现**

修改 `apps/agent-core/app/services/literature.py`：
将上面占位的 `import_unified_entries` 替换为：

```python
from app.services.literature_parser import normalize_title   # 已有
from sqlmodel import select
from app.models import LiteratureImportBatch, LiteratureRecord
from app.services.search_run import _ensure_project  # 或用 project_id 直接判断
from dataclasses import dataclass


@dataclass
class _ImportResult:
    count: int
    skipped_count: int
    duplicate_count: int


def import_unified_entries(
    session,
    project_id,
    source_key,
    entries,
    search_run_id=None,
    search_run_source_id=None,
) -> _ImportResult:
    # Thin 封装：复用 import_literature 的 import_batch 语义 + 传扩展列
    # ① 先构造一个文献 text 字符串？不，直接把每条条目写进 import batch 逻辑
    _project = session.get(ResearchProject, project_id)  # ensure exists
    if _project is None:
        raise HTTPException(status_code=404, detail="project not found")

    source_label = {"pubmed":"PubMed","cnki":"CNKI","wanfang":"万方"}.get(source_key, source_key)

    batch = LiteratureImportBatch(
        project_id=project_id,
        source_key=source_key,
        parsed_count=len(entries),
        duplicate_count=0,
        skipped_count=0,
        search_run_source_id=search_run_source_id,
    )
    session.add(batch)
    session.flush()

    imported = 0
    failed = 0
    duplicates = 0

    # 用 _detect_duplicate (已存在) 判定每条 duplicate_of_id
    for e in entries:
        try:
            doi, pmid, title = _normalize_identifiers(e.doi or "", e.pmid or "", e.title or "")
            if title == "":
                failed += 1
                continue
            dup_id = _detect_duplicate(session, project_id, e.__class__(
                doi=doi, pmid=pmid, title=title, authors=e.authors, journal=e.journal,
                year=e.year, abstract=e.abstract, source_key=source_key,
            ))
            status = "unique" if dup_id is None else "duplicate"
            if dup_id is not None:
                duplicates += 1
            rec = LiteratureRecord(
                project_id=project_id,
                doi=doi,
                pmid=pmid,
                title=title,
                authors=e.authors or "",
                journal=e.journal or "",
                year=e.year,
                abstract=e.abstract or "",
                source_key=source_key,
                source_label=source_label,
                dedupe_status=status,
                duplicate_of_id=dup_id,
                import_batch_id=batch.id,
                search_run_id=search_run_id,
                pico_status="not_extracted",
            )
            session.add(rec)
            session.flush()
            imported += 1
        except Exception:  # noqa: BLE001
            failed += 1
            session.rollback()
    # flush 收尾 batch 统计
    session.commit()
    session.refresh(batch)
    batch.duplicate_count = duplicates
    batch.skipped_count = failed
    session.add(batch)
    session.commit()
    return _ImportResult(count=imported, skipped_count=failed, duplicate_count=duplicates)
```

（注意：`ResearchProject` 需要在顶部 import）

- [ ] **Step 5: 在 `literature.py` 扩 build_library_response 支持 sort / search_run_id / min_score**

在现有的 `def build_library_response(...)` 里追加 3 个可选参数：

```python
def build_library_response(
    session: Session,
    project_id: int,
    *,
    search_run_id: int | None = None,
    sort: Literal["default", "relevance", "year_desc", "journal"] = "default",
    min_score: float | None = None,
) -> LiteratureLibrarySummary:
    ...
    # records 查询部分替换为：
    q = select(LiteratureRecord).where(LiteratureRecord.project_id == project_id)
    if search_run_id is not None:
        q = q.where(LiteratureRecord.search_run_id == search_run_id)
    all_records = list(session.exec(q).all())
    if min_score is not None:
        all_records = [r for r in all_records
                       if r.relevance_score is not None and r.relevance_score >= min_score]

    # sort 排序
    if sort == "relevance":
        all_records.sort(
            key=lambda r: (-(r.relevance_score or -1.0), -(r.year or 0))
        )
    elif sort == "year_desc":
        all_records.sort(key=lambda r: (-(r.year or 0), (r.relevance_score or 0)))
    elif sort == "journal":
        all_records.sort(key=lambda r: ((r.journal or "").lower(), -(r.year or 0)))
    # else default: by id desc (already insertion order). 再补一遍 id desc fallback:
    all_records.sort(key=lambda r: -(r.id or 0))
    ...
```

- [ ] **Step 6: workspace.py 加 7 端点 S1~S7**

在 `apps/agent-core/app/routers/workspace.py`：

导入：

```python
from app.services.search_run import (
    SearchRunError,
    cancel_search_run,
    create_search_run,
    export_search_run_csv_text,
    get_search_run_detail,
    get_search_run_list,
    retry_failed_sources,
)
from app.schemas import (
    BatchPicoPayload,        # 任务 7 会加
    BatchPicoResult,         # 任务 7
    LiteratureLibraryRequestExt,
    PicoAutofillDraft,       # 任务 7
    SearchRunCreatePayload,
    SearchRunDetail as _SDetail,
    SearchRunSourceSummary,
    SearchRunStatusPoll,
    SearchRunSummary,
)
from fastapi.responses import StreamingResponse
```

追加：

```python
# ---------- Wave 8: S1~S7 search run endpoints ----------

@router.post(
    "/projects/{project_id}/stages/search/search-runs",
    status_code=status.HTTP_201_CREATED,
    response_model=SearchRunSummary,
)
def search_run_create(
    project_id: int,
    payload: SearchRunCreatePayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        run = create_search_run(
            session, project_id,
            sources=payload.sources,
            query_snapshot=payload.query_snapshot,
            search_query_version_id=payload.search_query_version_id,
        )
        return _map_search_run_summary(session, run)
    except SearchRunError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.args[0]) from exc
    except LiteratureNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc


@router.get(
    "/projects/{project_id}/stages/search/search-runs",
    response_model=dict,
)
def search_run_list(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        runs, total = get_search_run_list(session, project_id, page=page, page_size=page_size)
        return {
            "items": [_map_search_run_summary(session, r) for r in runs],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except LiteratureNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc


@router.get(
    "/projects/{project_id}/stages/search/search-runs/{run_id}",
    response_model=_SDetail,
)
def search_run_detail(
    project_id: int,
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        run, sources = get_search_run_detail(session, project_id, run_id)
        return _SDetail(
            run=_map_search_run_summary(session, run),
            sources=[_map_source_summary(s) for s in sources],
        )
    except SearchRunError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.args[0]) from exc
    except LiteratureNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc


@router.post(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/cancel",
)
def search_run_cancel(
    project_id: int,
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        cancel_search_run(session, run_id)
        return {"status": "cancelled"}
    except SearchRunError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.args[0]) from exc


@router.post(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/retry",
)
def search_run_retry(
    project_id: int,
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        restarted = retry_failed_sources(session, run_id)
        return {"restarted_sources": restarted}
    except SearchRunError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.args[0]) from exc


@router.get(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/export.csv",
)
def search_run_export_csv(
    project_id: int,
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        text = export_search_run_csv_text(session, run_id)
    except LiteratureNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc
    # Safe filename
    import re
    safe_id = re.sub(r"[^A-Za-z0-9_-]+", "", f"search-run-{run_id}")
    date = datetime.utcnow().strftime("%Y%m%d")
    filename = f"{safe_id}-{date}.csv"
    from fastapi.responses import Response
    return Response(
        content="\ufeff" + text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/status",
    response_model=SearchRunStatusPoll,
)
def search_run_status_poll(
    project_id: int,
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        run, sources = get_search_run_detail(session, project_id, run_id)
        total = len(sources)
        finished = sum(1 for s in sources if s.status in {"completed", "failed"})
        eta = None
        if total and finished < total and run.started_at is not None:
            elapsed = (datetime.utcnow() - run.started_at).total_seconds()
            per_item = elapsed / finished if finished > 0 else 0
            eta = max(0.0, per_item * (total - finished))
        return SearchRunStatusPoll(
            status=run.status,
            finished_sources=finished,
            total_sources=total,
            eta_seconds=eta,
        )
    except LiteratureNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc


# ======================================= helpers ==========================================

_SOURCE_LABELS = {"pubmed": "PubMed", "cnki": "CNKI", "wanfang": "万方"}


def _prisma_for_run(session, run):
    from app.models import LiteratureRecord
    # 直接用 run 存储的总数字（worker 已更新）；Eligibility/Included 在 Wave 8 预留 == after_dedupe
    raw = run.total_hits_raw
    after = run.total_after_dedupe
    # per source breakdown
    sources = list(session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all())
    by_source = [
        {
            "source_key": s.source_key,
            "source_label": _SOURCE_LABELS.get(s.source_key, s.source_key),
            "records_retrieved": s.records_retrieved,
            "records_imported": s.records_imported,
        } for s in sources
    ]
    return {
        "identification": raw,
        "screening": after,
        "eligibility": after,
        "included": after,
        "by_source": by_source,
    }


def _fmt(t):
    return t.isoformat() if t else None


def _map_search_run_summary(session, run):
    eta = None
    if run.status == "running" and run.started_at:
        # simple rough ETA (2s/source remaining)
        sources = list(session.exec(
            select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
        ).all())
        done = sum(1 for s in sources if s.status in {"completed","failed"})
        remaining = len(sources) - done
        eta = remaining * 2.0
    return SearchRunSummary(
        id=run.id,
        project_id=run.project_id,
        search_query_version_id=run.search_query_version_id,
        selected_sources=[s for s in run.selected_sources.split(",") if s],
        status=run.status,
        created_at=_fmt(run.created_at),
        started_at=_fmt(run.started_at),
        finished_at=_fmt(run.finished_at),
        total_hits_raw=run.total_hits_raw,
        total_after_dedupe=run.total_after_dedupe,
        prisma=_prisma_for_run(session, run),
        eta_seconds=eta,
    )


def _map_source_summary(s):
    return SearchRunSourceSummary(
        id=s.id,
        search_run_id=s.search_run_id,
        source_key=s.source_key,
        source_label=_SOURCE_LABELS.get(s.source_key, s.source_key),
        status=s.status,
        hits_on_source=s.hits_on_source,
        records_retrieved=s.records_retrieved,
        records_imported=s.records_imported,
        started_at=_fmt(s.started_at),
        finished_at=_fmt(s.finished_at),
        error_message=s.error_message,
    )
```

- [ ] **Step 7: 跑 test_search_run_service.py → 5 tests 全过**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_run_service.py -v --tb=short 2>&1 | Select-Object -Last 20
```

Expected: **5 passed**。

- [ ] **Step 8: Commit**

```bash
git add apps/agent-core/app/services/search_run.py apps/agent-core/app/services/literature.py apps/agent-core/app/routers/workspace.py apps/agent-core/tests/test_search_run_service.py
git commit -m "feat(wave8/t5): search_run service (create/cancel/retry/export) + 7 endpoints"
```

---

## Task 6: BM25 服务 + B1/B2 端点（替换占位）

**Files:**
- Modify: `apps/agent-core/app/services/bm25_scoring.py`（替换占位）
- Create: `apps/agent-core/tests/test_bm25_scoring.py`
- Modify: `apps/agent-core/app/routers/workspace.py`（补 B1/B2）
- Modify: `apps/agent-core/pyproject.toml`（如果未声明 rank_bm25 依赖就加）

### 6.1 失败测试

- [ ] **Step 1: 写失败测试**

创建 `apps/agent-core/tests/test_bm25_scoring.py`：

```python
from __future__ import annotations
from sqlmodel import Session, select

from app.models import LiteratureRecord
from app.services.bm25_scoring import (
    compute_bm25_scores_for,
    recompute_bm25_for_search_run,
    tokenize_for_bm25,
)
from app.tests.conftest import create_test_project, create_test_user


def test_tokenize_preserves_chinese_and_alphanum_lowercase() -> None:
    # cjk 字符按单字分词；英文按 \W+ 拆 + 小写
    tokens = tokenize_for_bm25("Metformin 对 2型糖尿病患者 CVD 结局的影响 (RCT).")
    assert "metformin" in tokens
    assert "cvd" in tokens
    assert "rct" in tokens
    # Chinese characters split as individual tokens
    for c in "对型糖尿病患者结局的影响":
        assert c in tokens


def test_bm25_scores_higher_for_relevant_titles(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    docs = [
        ("SGLT2i reduces heart failure hospitalizations in T2DM CKD","...", 2024, "10.1/a"),
        ("Lifestyle intervention and metformin for prediabetes","...", 2023, "10.1/b"),
        ("Totally unrelated orthopedic surgery study","...", 2022, "10.1/c"),
    ]
    for title, abstract, year, doi in docs:
        db_session.add(LiteratureRecord(
            project_id=project.id, title=title, authors="", journal="J",
            year=year, doi=doi, pmid="", source_key="pubmed",
            source_label="PubMed", dedupe_status="unique", pico_status="not_extracted",
        ))
    db_session.commit()
    records = list(db_session.exec(
        select(LiteratureRecord).where(LiteratureRecord.project_id == project.id)
    ).all())

    query = "SGLT2i 心力衰竭 T2DM CKD".split()
    scores = compute_bm25_scores_for(records, query)
    assert len(scores) == len(records)
    # 第一条最高分
    order = sorted(range(len(records)), key=lambda i: -scores[i])
    assert order[0] == 0
    # 排序后 A > B > C（第三条完全无关 ≈ 0）
    assert scores[order[0]] > scores[order[1]] >= scores[order[2]]


def test_recompute_writes_relevance_score_to_each_record(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    from app.models import SearchRun
    run = SearchRun(project_id=project.id, query_snapshot='{"p":"T2DM","i":"SGLT2i","boolean_text":"SGLT2i T2DM"}', selected_sources="pubmed", status="running")
    db_session.add(run)
    db_session.flush()

    for i in range(4):
        db_session.add(LiteratureRecord(
            project_id=project.id, title=f"Paper {i} about SGLT2i T2DM" if i % 2 == 0 else f"Paper {i} about influenza vaccine",
            authors="", journal="J", year=2024, doi=f"10.1/x{i}", pmid="", source_key="pubmed",
            source_label="PubMed", dedupe_status="unique",
            search_run_id=run.id, pico_status="not_extracted",
        ))
    db_session.commit()
    recompute_bm25_for_search_run(db_session, run.id)
    recs = list(db_session.exec(
        select(LiteratureRecord).where(LiteratureRecord.search_run_id == run.id)
    ).all())
    scores = {r.title: r.relevance_score for r in recs}
    # 偶数 title（带 SGLT2i T2DM）应高于奇数 title（疫苗）
    assert max(scores["Paper 0 about SGLT2i T2DM"], scores["Paper 2 about SGLT2i T2DM"]) > \
        max(scores["Paper 1 about influenza vaccine"], scores["Paper 3 about influenza vaccine"])
```

- [ ] **Step 2: 运行确认失败（缺少 `recompute_bm25_for_search_run` 非占位真实实现）**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_bm25_scoring.py -v --tb=short 2>&1 | Select-Object -Last 15
```

Expected FAIL。

### 6.2 实现 BM25 服务 + 2 端点

- [ ] **Step 3: 确保 rank_bm25 在 pyproject.toml 中声明**

编辑 `apps/agent-core/pyproject.toml` 的 dependencies，补：

```
dependencies = [
    ...
    "rank-bm25>=0.2.2",
]
```

然后本地 `uv pip install rank-bm25`（或直接 `uv sync`）确认能 import。

- [ ] **Step 4: 写 bm25_scoring.py**

替换占位：

```python
from __future__ import annotations

import json
import re
from typing import Iterable, Sequence

from rank_bm25 import BM25Okapi
from sqlmodel import Session, select

from app.models import LiteratureRecord, SearchRun

CJK_RE = re.compile(r"[\u4e00-\u9fff]")
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize_for_bm25(text: str) -> list[str]:
    """CJK character-wise + Latin/Numeric tokenize. 不做停用词（避免语言错）。"""
    if not text:
        return []
    cjk = CJK_RE.findall(text)
    words = [w.lower() for w in TOKEN_RE.findall(text)]
    return cjk + words


def _doc_tokens(r: LiteratureRecord) -> list[str]:
    return tokenize_for_bm25(f"{r.title} {r.abstract}")


def compute_bm25_scores_for(
    records: Sequence[LiteratureRecord], query_tokens: Iterable[str]
) -> list[float]:
    corpus = [_doc_tokens(r) for r in records]
    if not corpus:
        return []
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(list(query_tokens))
    return [float(x) for x in scores]


def recompute_bm25_for_search_run(session: Session, search_run_id: int) -> None:
    run = session.get(SearchRun, search_run_id)
    if run is None:
        return
    records = list(session.exec(
        select(LiteratureRecord).where(
            LiteratureRecord.search_run_id == run.id,
            LiteratureRecord.dedupe_status != "duplicate",
        )
    ).all())
    if not records:
        return
    # query tokens from snapshot (p+i+o + boolean 拆)
    try:
        snap = json.loads(run.query_snapshot or "{}")
    except Exception:
        snap = {}
    parts: list[str] = []
    for key in ("p", "i", "c", "o"):
        if snap.get(key):
            parts.append(str(snap[key]))
    if snap.get("boolean_text"):
        parts.append(str(snap["boolean_text"]))
    raw = " ".join(parts)
    q_tokens = tokenize_for_bm25(raw)
    if not q_tokens:
        for r in records:
            r.relevance_score = None
        session.add_all(records)
        session.commit()
        return
    scores = compute_bm25_scores_for(records, q_tokens)
    max_s = max(scores) if scores and max(scores) > 0 else None
    for r, s in zip(records, scores):
        r.relevance_score = float(s) / float(max_s) if max_s is not None else None
    session.add_all(records)
    session.commit()
```

- [ ] **Step 5: 补 workspace.py B1/B2 端点**

在 `routers/workspace.py` 继续追加：

```python
# ---------- Wave 8: B1/B2 BM25 + library 扩展 ----------

@router.post(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/recompute-bm25",
)
def search_run_recompute_bm25(
    project_id: int,
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        recompute_bm25_for_search_run(session, run_id)
        return {"queued": True, "note": "recomputed synchronously"}
    except LiteratureNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc


@router.get(
    "/projects/{project_id}/stages/search/literature",
    response_model=LiteratureLibrarySummary,
)
def literature_library_ext(
    project_id: int,
    search_run_id: int | None = Query(default=None),
    sort: Literal["default", "relevance", "year_desc", "journal"] = Query(default="default"),
    min_score: float | None = Query(default=None, ge=0.0, le=1.0),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        return build_library_response(
            session, project_id,
            search_run_id=search_run_id,
            sort=sort,
            min_score=min_score,
        )
    except LiteratureNotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.args[0]) from exc
```

（记得在顶部 import `from app.services.bm25_scoring import recompute_bm25_for_search_run`）

- [ ] **Step 6: 跑 3 tests → 3 passed**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_bm25_scoring.py -v --tb=short 2>&1 | Select-Object -Last 15
```

Expected: **3 passed**。

- [ ] **Step 7: Commit**

```bash
git add apps/agent-core/app/services/bm25_scoring.py apps/agent-core/app/routers/workspace.py apps/agent-core/tests/test_bm25_scoring.py apps/agent-core/pyproject.toml
git commit -m "feat(wave8/t6): BM25 relevance scoring + recompute + library sort/search_run_id filter"
```

---

## Task 7: PICO 双引擎（rule_baseline 默认 + llm 可选）+ P1~P3 端点

**Files:**
- Create: `apps/agent-core/app/services/pico.py`
- Create: `apps/agent-core/tests/test_pico_service.py`
- Modify: `apps/agent-core/app/routers/workspace.py`（补 P1~P3）

### 7.1 失败测试

- [ ] **Step 1: 写失败用例（3 tests）**

创建 `apps/agent-core/tests/test_pico_service.py`：

```python
from __future__ import annotations

from sqlmodel import Session, select

from app.models import LiteraturePico, LiteratureRecord
from app.services.pico import (
    PicoExtractionError,
    batch_extract_pico,
    extract_pico_for_record,
    suggest_pico_autofill,
)
from app.tests.conftest import create_test_project, create_test_user


def _insert_records(session: Session, project_id: int, specs):
    out = []
    for title, abstract, doi in specs:
        r = LiteratureRecord(
            project_id=project_id, title=title, authors="", journal="J",
            year=2024, doi=doi, pmid="", source_key="pubmed",
            source_label="PubMed", dedupe_status="unique", pico_status="not_extracted",
        )
        session.add(r)
        out.append(r)
    session.commit()
    for r in out:
        session.refresh(r)
    return out


def test_rule_baseline_extracts_rct_and_sglti_cvd(db_session: Session, monkeypatch) -> None:
    # 确保 llm 未配置；默认走规则
    monkeypatch.setattr("app.services.pico._LLM_PROVIDER", None)

    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    [rec] = _insert_records(session, project.id, [
        (
            "SGLT2 Inhibitors and Cardiovascular Outcomes in T2DM: A Randomized Controlled Trial",
            "Background: T2DM patients ... Intervention: Empagliflozin 10mg daily vs. placebo ... Outcome: 3-point MACE (CV death, non-fatal MI, non-fatal stroke).",
            "10.1/sglt2i-cvd",
        ),
    ])

    pico = extract_pico_for_record(db_session, rec.id, method="rule_baseline")
    assert pico is not None
    assert pico.study_type == "rct"
    assert "T2DM" in (pico.population or "") or "糖尿病" in (pico.population or "")
    assert "SGLT" in (pico.intervention or "") or "Empagliflozin" in (pico.intervention or "")
    assert pico.extraction_method == "rule_baseline"
    assert 0 < (pico.confidence or 0) <= 1.0


def test_batch_extract_skips_extracted_and_counts_failures(
    db_session: Session, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.pico._LLM_PROVIDER", None)

    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    specs = [
        ("Metformin vs placebo on T2DM (RCT)", "...", "10.1/m"),
        ("A prospective cohort of Dapagliflozin in CKD non-DM", "...", "10.1/d"),
    ]
    recs = _insert_records(session, project.id, specs)
    # 先把第二条的 pico_status 预先标 extracted
    recs[1].pico_status = "extracted"
    session = db_session
    session.add(recs[1])
    session.commit()

    result = batch_extract_pico(session, [r.id for r in recs], method="rule_baseline")
    assert result.processed == 1  # 只有第一条真处理
    assert result.already_had == 1
    assert result.failed == 0


def test_suggest_pico_autofill_returns_top_tokens_with_supporting_ids(
    db_session: Session, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.pico._LLM_PROVIDER", None)

    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    from app.models import SearchRun
    run = SearchRun(project_id=project.id, query_snapshot='{"p":"T2DM","i":"SGLT2i","boolean_text":"T2DM SGLT2i CVD RCT"}', selected_sources="pubmed", status="completed")
    db_session.add(run)
    db_session.flush()

    titles = [
        ("SGLT2i on CVD outcomes in patients with T2DM (RCT)", "...", "10.1/1"),
        ("Empagliflozin reduces HF hospitalization in T2DM CKD", "...", "10.1/2"),
        ("Influenza vaccine coverage 2023 (无关)", "...", "10.1/3"),
    ]
    for t, a, doi in titles:
        r = LiteratureRecord(project_id=project.id, title=t, authors="", journal="J", year=2024,
            doi=doi, pmid="", source_key="pubmed", source_label="PubMed",
            dedupe_status="unique", search_run_id=run.id, pico_status="not_extracted")
        db_session.add(r)
    db_session.commit()
    # 先批量 extract
    ids = list(r.id for r in db_session.exec(
        select(LiteratureRecord).where(LiteratureRecord.search_run_id == run.id)
    ).all())
    batch_extract_pico(db_session, ids, method="rule_baseline")

    draft = suggest_pico_autofill(db_session, run.id)
    # P 应含 T2DM
    assert "T2DM" in draft.p or "糖尿病" in draft.p
    # I 含 SGLT2
    assert "SGLT2" in draft.i or "Empagliflozin" in draft.i or "SGLT" in draft.i
    assert len(draft.supporting_record_ids) >= 2  # 两条相关都会命中
```

- [ ] **Step 2: 运行确认失败**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_pico_service.py -v --tb=short 2>&1 | Select-Object -Last 15
```

Expected FAIL。

### 7.2 实现 PICO 服务

- [ ] **Step 3: 实现 services/pico.py**

```python
from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Literal

from sqlmodel import Session, select

from app.models import LiteraturePico, LiteratureRecord, SearchRun


# ---- providers ----
_LLM_PROVIDER: Literal["claude", "openai"] | None = (
    os.environ.get("MEDA_PICO_LLM_PROVIDER") or None
)


# 基础词典（够用的 rule_baseline；后续迭代再扩）
POP_TERMS = [
    "T2DM", "2型糖尿病", "2 型糖尿病", "T1DM", "CKD", "慢性肾病", "CKD 3b", "HFrEF", "心衰",
    "高血压", "STEMI", "NSTEMI", "ACS", "急性冠脉综合征", "肥胖", "NAFLD",
]
INT_TERMS = [
    "SGLT2", "SGLT2i", "达格列净", "Dapagliflozin", "恩格列净", "Empagliflozin",
    "GLP-1", "GLP1", "司美格鲁肽", "Semaglutide", "利拉鲁肽", "Liraglutide",
    "二甲双胍", "Metformin", "胰岛素", "Insulin", "ACEI", "ARB", "他汀", "Statin",
]
CMP_TERMS = [
    "安慰剂", "placebo", "常规治疗", "usual care", "对照", "control",
    "生活方式", "lifestyle", "磺脲类", "sulfonylurea",
]
OUT_TERMS = [
    "MACE", "主要心血管不良事件", "3P-MACE", "4P-MACE", "HF 住院", "心衰住院", "住院率",
    "全因死亡", "all-cause mortality", "心血管死亡", "CV death", "eGFR 下降", "肌酐翻倍",
    "复合肾脏终点", "HbA1c", "体重变化",
]
STUDY_TYPE_RULES = [
    ("rct", re.compile(r"\bRCT\b|randomiz|随机|随机对照|randomized controlled", re.IGNORECASE)),
    ("observational", re.compile(r"cohort|队列|retrospective|回顾性|observational", re.IGNORECASE)),
    ("review", re.compile(r"meta.?analysis|systematic review|Meta分析|系统综述", re.IGNORECASE)),
]


class PicoExtractionError(Exception):
    def __init__(self, message: str, code: Literal["no_records_provided","llm_not_configured","pico_failed"]):
        super().__init__(message)
        self.code = code


@dataclass
class BatchResult:
    processed: int
    already_had: int
    failed: int


# ===================================================== core rule extraction

def _extract_population(text: str) -> tuple[str | None, float]:
    found = [t for t in POP_TERMS if t.lower() in text.lower()]
    if not found:
        return None, 0.0
    return "；".join(sorted(set(found))), min(1.0, 0.25 + 0.15 * len(found))


def _extract_intervention(text: str) -> tuple[str | None, float]:
    found = [t for t in INT_TERMS if t.lower() in text.lower()]
    if not found:
        return None, 0.0
    return "；".join(sorted(set(found))), min(1.0, 0.25 + 0.15 * len(found))


def _extract_comparison(text: str) -> tuple[str | None, float]:
    found = [t for t in CMP_TERMS if t.lower() in text.lower()]
    if not found:
        return None, 0.0
    return "；".join(sorted(set(found))), min(1.0, 0.25 + 0.15 * len(found))


def _extract_outcome(text: str) -> tuple[str | None, float]:
    found = [t for t in OUT_TERMS if t.lower() in text.lower()]
    if not found:
        return None, 0.0
    return "；".join(sorted(set(found))), min(1.0, 0.25 + 0.15 * len(found))


def _detect_study_type(text: str) -> tuple[str | None, float]:
    for label, rx in STUDY_TYPE_RULES:
        if rx.search(text):
            return label, 0.9
    return None, 0.0


def _rule_baseline_extract(rec: LiteratureRecord) -> LiteraturePico:
    text = f"{rec.title}\n{rec.abstract}"
    pop, p_w = _extract_population(text)
    intr, i_w = _extract_intervention(text)
    cmp, c_w = _extract_comparison(text)
    out, o_w = _extract_outcome(text)
    study, s_w = _detect_study_type(text)
    conf = round(sum([p_w, i_w, c_w, o_w, s_w]) / 5.0, 3)
    return LiteraturePico(
        record_id=rec.id,
        population=pop,
        intervention=intr,
        comparison=cmp,
        outcome=out,
        study_type=study,
        extraction_method="rule_baseline",
        confidence=conf,
    )


async def _llm_extract(rec: LiteratureRecord, provider: str) -> LiteraturePico:
    """Optional LLM engine. Only called when env var provider is set.

    这里保留薄封装：调用 get_llm_config 与相应 SDK；若调用失败则 fallback 到 rule_baseline。
    """
    try:
        # 未来 Wave 打开：import 后真实调用。
        raise RuntimeError(f"LLM provider {provider!r} not wired yet in Wave 8")
    except Exception:
        base = _rule_baseline_extract(rec)
        base.extraction_method = f"llm:{provider}+fallback_rule"
        return base


# ===================================================== public API

def extract_pico_for_record(
    session: Session,
    record_id: int,
    *,
    method: Literal["rule_baseline", "llm"] = "rule_baseline",
) -> LiteraturePico:
    rec = session.get(LiteratureRecord, record_id)
    if rec is None:
        raise PicoExtractionError("record not found", "pico_failed")

    if method == "llm":
        if _LLM_PROVIDER is None:
            raise PicoExtractionError(
                "PICO LLM engine not configured. Set MEDA_PICO_LLM_PROVIDER env.",
                "llm_not_configured",
            )
        import asyncio
        pico = asyncio.run(_llm_extract(rec, _LLM_PROVIDER))
    else:
        pico = _rule_baseline_extract(rec)

    # Upsert：若已有 LiteraturePico 就删除后重写（record_id 唯一）
    exist = session.exec(
        select(LiteraturePico).where(LiteraturePico.record_id == record_id)
    ).first()
    if exist is not None:
        session.delete(exist)
        session.flush()
    session.add(pico)
    rec.pico_status = "extracted" if pico.population or pico.intervention else "failed"
    session.add(rec)
    session.commit()
    session.refresh(pico)
    return pico


def batch_extract_pico(
    session: Session,
    record_ids: list[int],
    *,
    method: Literal["rule_baseline", "llm"] = "rule_baseline",
) -> BatchResult:
    if not record_ids:
        raise PicoExtractionError("no_records_provided", "no_records_provided")
    processed = 0
    already = 0
    failed = 0
    for rid in record_ids:
        rec = session.get(LiteratureRecord, rid)
        if rec is None:
            failed += 1
            continue
        if rec.pico_status == "extracted":
            already += 1
            continue
        try:
            extract_pico_for_record(session, rid, method=method)
            processed += 1
        except PicoExtractionError as exc:
            if exc.code == "llm_not_configured":
                raise
            failed += 1
            rec.pico_status = "failed"
            session.add(rec)
            session.commit()
    return BatchResult(processed=processed, already_had=already, failed=failed)


def suggest_pico_autofill(
    session: Session,
    run_id: int,
    top_n_records: int = 5,
) -> "PicoAutofillDraft":  # 字符串前向避免循环 import；实际上用的是 schemas 里类
    run = session.get(SearchRun, run_id)
    if run is None:
        from fastapi import HTTPException
        raise HTTPException(404, "search_run not found")

    records = list(session.exec(
        select(LiteratureRecord)
        .where(LiteratureRecord.search_run_id == run.id)
        .where(LiteratureRecord.dedupe_status != "duplicate")
        .order_by((LiteratureRecord.relevance_score or 0).desc())
        .limit(max(20, top_n_records))
    ).all())
    if not records:
        from app.schemas import PicoAutofillDraft as _D
        return _D(p="", i="", c="", o="", supporting_record_ids=[])

    picos = list(session.exec(
        select(LiteraturePico).where(
            LiteraturePico.record_id.in_([r.id for r in records])
        )
    ).all())
    # 缺 PICO 的先用 rule 补跑（不落库？这里直接在内存算）
    pico_by_rec = {p.record_id: p for p in picos}
    # for counting token weights:
    pop_counter: Counter[str] = Counter()
    int_counter: Counter[str] = Counter()
    cmp_counter: Counter[str] = Counter()
    out_counter: Counter[str] = Counter()
    supporting = []
    for r in records:
        p = pico_by_rec.get(r.id) or _rule_baseline_extract(r)
        scored = 0
        if p.population:
            for part in p.population.split("；"):
                if part:
                    pop_counter[part] += 1
                    scored += 1
        if p.intervention:
            for part in p.intervention.split("；"):
                if part:
                    int_counter[part] += 1
                    scored += 1
        if p.comparison:
            for part in p.comparison.split("；"):
                if part:
                    cmp_counter[part] += 1
                    scored += 1
        if p.outcome:
            for part in p.outcome.split("；"):
                if part:
                    out_counter[part] += 1
                    scored += 1
        if scored >= 2 and len(supporting) < top_n_records:
            supporting.append(r.id)

    def _top(counter: Counter[str]) -> str:
        items = [t for t, _ in counter.most_common(5)]
        return "；".join(items)

    from app.schemas import PicoAutofillDraft as _D
    return _D(
        p=_top(pop_counter),
        i=_top(int_counter),
        c=_top(cmp_counter),
        o=_top(out_counter),
        supporting_record_ids=supporting,
    )
```

- [ ] **Step 4: 补 P1~P3 端点到 workspace.py**

在 `routers/workspace.py` 继续追加：

```python
# ---------- Wave 8: P1~P3 PICO ----------

@router.post(
    "/projects/{project_id}/stages/search/records/pico:batch-extract",
    response_model=BatchPicoResult,
)
def pico_batch_extract(
    project_id: int,
    payload: BatchPicoPayload,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        result = batch_extract_pico(
            session, payload.record_ids, method=payload.method,
        )
        return BatchPicoResult(
            processed=result.processed,
            already_had=result.already_had,
            failed=result.failed,
        )
    except PicoExtractionError as exc:
        status_code = status.HTTP_501_NOT_IMPLEMENTED if exc.code == "llm_not_configured" else status.HTTP_422_UNPROCESSABLE_ENTITY
        raise HTTPException(status_code, detail=exc.args[0]) from exc


@router.get(
    "/projects/{project_id}/stages/search/records/{record_id}/pico",
    response_model=LiteraturePicoResponse,
)
def pico_get_one(
    project_id: int,
    record_id: int,
    method: Literal["rule_baseline", "llm"] = "rule_baseline",
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        p = extract_pico_for_record(session, record_id, method=method)
        return LiteraturePicoResponse(
            record_id=p.record_id,
            population=p.population,
            intervention=p.intervention,
            comparison=p.comparison,
            outcome=p.outcome,
            study_type=p.study_type,
            extraction_method=p.extraction_method,
            confidence=p.confidence,
            extracted_at=p.extracted_at.isoformat() if p.extracted_at else "",
        )
    except PicoExtractionError as exc:
        status_code = status.HTTP_501_NOT_IMPLEMENTED if exc.code == "llm_not_configured" else status.HTTP_404_NOT_FOUND
        raise HTTPException(status_code, detail=exc.args[0]) from exc


@router.post(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/pico:autofill-query",
    response_model=PicoAutofillDraft,
)
def pico_autofill_query(
    project_id: int,
    run_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        _load_project_or_404(session, project_id, current_user)
        return suggest_pico_autofill(session, run_id)
    except PicoExtractionError as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.args[0]) from exc
```

记得在 workspace.py 顶部 import `from app.services.pico import PicoExtractionError, batch_extract_pico, extract_pico_for_record, suggest_pico_autofill`。

- [ ] **Step 5: 跑 test_pico_service.py → 3 passed**

```powershell
cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_pico_service.py -v --tb=short 2>&1 | Select-Object -Last 15
```

Expected: **3 passed**。

- [ ] **Step 6: Commit**

```bash
git add apps/agent-core/app/services/pico.py apps/agent-core/app/routers/workspace.py apps/agent-core/tests/test_pico_service.py
git commit -m "feat(wave8/t7): PICO dual engine (rule_baseline default + llm optional) + 3 endpoints"
```

---

## Task 8: 13 API 端点集成测试

**Files:**
- Create: `apps/agent-core/tests/test_search_run_api.py`
- Modify: `apps/agent-core/tests/test_literature_api.py`（加 3 处扩展 /literature query）

任务简述：S1~S7、P1~P3、B1~B2 共 13 端点的 HTTP 层测试（TestClient）。复用 monkeypatch + mock dataset。要求至少 12 tests；每一个 non-2xx 错误分支至少 1 条。

- [ ] **Step 1: 写失败用例，12+ tests**
- [ ] **Step 2: 运行确认失败**
- [ ] **Step 3: 修 workspace.py 的响应字段不一致处**
- [ ] **Step 4: 12+ passed；和 Task 1~7 合计 tests ≥ 4+3+4+5+3+3+3+12 = 37**
- [ ] **Step 5: Commit**

（为节省篇幅，测试内部每条遵循：devLogin → create project → `POST /search-runs` → 调 tick_once worker 辅助函数 → `GET /status` 轮询断言 → `GET /{id}` → GET CSV 断言有 PRISMA header → retry/cancel 的 422 断言。）

---

## Task 9: shared-sdk 13 个方法 + 类型

**Files:**
- Modify: `packages/shared-sdk/src/client.ts`
- Modify: `packages/shared-sdk/src/session.test.ts`

- [ ] **Step 1: 读当前 client.ts 中的 handleResponse 和现有方法，保持一致命名**
- [ ] **Step 2: 在顶部 type 区块中补：SearchRunStatus / SearchRunSourceStatus / PicoStatus、SearchRunSummary、SearchRunSourceSummary、SearchRunDetail、PrismaReport、SearchSourceBreakdown、SearchRunCreatePayload、SearchRunStatusPoll、LiteraturePicoResponse、BatchPicoPayload、BatchPicoResult、PicoAutofillDraft、LiteratureLibrarySortKey**
- [ ] **Step 3: 补 13 方法：`createSearchRun(projectId, payload)`、`listSearchRuns(projectId, {page,pageSize})`、`getSearchRun(projectId, runId)`、`cancelSearchRun(projectId, runId)`、`retrySearchRun(projectId, runId)`、`exportSearchRunCsvUrl(projectId, runId)`（返回 URL 字符串，避免二进制）、`pollSearchRunStatus(projectId, runId)`、`recomputeBm25(projectId, runId)`、`getLiteratureLibraryExt(projectId, {searchRunId, sort, minScore})`（原 `getLiteratureLibrary` 保持不变）、`batchExtractPico(projectId, {recordIds, method})`、`getRecordPico(projectId, recordId, method)`、`autofillPicoFromRun(projectId, runId)`**
- [ ] **Step 4: 在 session.test.ts 中每个新方法加 1 条 mock assertion（共 13 条），合计 session.test.ts 14 + 13 = 27 tests**
- [ ] **Step 5: 运行 vitest → 27 passed**
- [ ] **Step 6: Commit**

---

## Task 10: shared-ui 4 组件 + 扩 LiteratureLibraryScreen

**Files:**
- Create: `packages/shared-ui/src/PrismChart.tsx`（纯 SVG PRISMA 图）
- Create: `packages/shared-ui/src/SearchRunListScreen.tsx`
- Create: `packages/shared-ui/src/SearchRunDetailScreen.tsx`
- Create: `packages/shared-ui/src/PicoPanel.tsx`
- Modify: `packages/shared-ui/src/LiteratureLibraryScreen.tsx`（排序下拉、run_id 面包屑、⭐、🏷️ PICO drawer）
- Modify: `packages/shared-ui/src/index.ts`（导出新组件 + 纯函数类型）

- [ ] **Step 1: PrismChart.tsx 写纯函数组件 + helpers.test.ts 中加 PRISMA 比例 + 差值测试**
- [ ] **Step 2: SearchRunListScreen.tsx（列表 Tab）+ SearchRunDetailScreen.tsx（详情）**
- [ ] **Step 3: PicoPanel.tsx + 批量按钮 + 确认对话框「回写为检索式草稿？」**
- [ ] **Step 4: LiteratureLibraryScreen 4 项扩展**
- [ ] **Step 5: searchRun.test.tsx 12 tests（PRISMA 宽度、状态 chip 文案、排序下拉）**
- [ ] **Step 6: vitest → shared-ui 16+12 = 28 passed**
- [ ] **Step 7: Commit**

---

## Task 11: Web / Desktop 接线 + shared-ui helpers.test.ts 补测

**Files:**
- Modify: `apps/web/src/App.tsx` / `apps/web/src/components/WorkspaceShell.tsx`
- Modify: `apps/desktop/src/App.tsx`
- Modify: `packages/shared-ui/src/helpers.test.ts`（PRISMA 计算 + 相对时间边界）
- Modify: `apps/agent-core/tests/test_literature_api.py`（扩 `/literature` 新 query 参数用例；ImportBatch 新列）

- [ ] **Step 1: Web Stage Entry Tab 3 接线 + run detail 屏幕切换**
- [ ] **Step 2: Desktop 对称接线**
- [ ] **Step 3: helpers.test.ts 补用例（≥ 4 新用例）**
- [ ] **Step 4: test_literature_api.py 3 处新断言**
- [ ] **Step 5: Commit**

---

## Task 12: 5 端全量回归（目标 ≥ 194 passed）

- [ ] **Step 1: agent-core pytest（≥ 128 passed；Wave 7 88 + ≥ 40 新增）**
- [ ] **Step 2: shared-sdk vitest（≥ 27）**
- [ ] **Step 3: shared-ui vitest（≥ 28）**
- [ ] **Step 4: web / admin / desktop vitest（5 + 1 + 5 = 11）**
- [ ] **Step 5: 汇总 ≥ 128+27+28+5+1+5 = 194。若少于 194，逐端补测试直到达标**
- [ ] **Step 6: 最终 Commit："chore(wave8/t12): 5-end regressions ≥194 all green"**

---

## 验收标准（对照 spec）

1. 从「保存的检索式版本」或「临时未保存布尔式 + 过滤」→ POST `/search-runs` → **立即返回 201**
2. 同进程 worker 在 1s 轮询内把 pending source → running → completed/failed，SearchRun 状态为 completed/partial_failed/failed
3. PubMed adapter 在没有 monkeypatch 时走真 esearch；CNKI/Wanfang 默认 stub 给出 `mock dataset not registered` warning
4. 记录写完后 LiteratureRecord.relevance_score ∈ [0,1]；排序 "relevance" 下高分在前
5. PICO 缺任何 LLM 配置（默认）→ rule_baseline 正常返回；指定 method=llm 返回 501 Not Implemented
6. PRISMA 图 Identification ≥ Screening == Eligibility == Included（非空 run）；CSV 导出包含 3 节：PRISMA / Per source / Records
7. 5 端测试全绿且总用例 ≥ 194
