# MedA Wave 7 文献条目库 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立项目级文献条目库，支持粘贴导入与手工录入，并实现三级去重判定与人工确认。

**Architecture:** 解析器以纯函数模块隔离（`literature_parser.py`），数据操作与去重判定在 `literature.py`；`LiteratureRecord` 为项目级实体，重复条目标记而不删除以保留 PRISMA 统计口径；前端组件放入 `packages/shared-ui`，Web 与 Desktop import 同一实现。

**Tech Stack:** FastAPI + SQLModel (SQLite in tests), TypeScript shared-sdk, React 18 (Web + Desktop), pytest, vitest

**Spec:** `docs/superpowers/specs/2026-08-05-meda-literature-library-wave-7-design.md`

---

## File Structure

**新建文件：**

| 路径 | 职责 |
|---|---|
| `apps/agent-core/app/services/literature_parser.py` | 纯函数：极简格式解析、标题归一化 |
| `apps/agent-core/app/services/literature.py` | 导入、去重判定、确认、统计、响应组装 |
| `apps/agent-core/tests/test_literature_parser.py` | 解析器纯函数单测 |
| `apps/agent-core/tests/test_literature_api.py` | 导入 / 去重 / 确认 / 统计 API 测试 |
| `packages/shared-ui/src/LiteratureLibraryScreen.tsx` | 双端共用的文献库页面 |
| `packages/shared-ui/src/helpers.test.ts` | shared-ui 纯函数单测（补 Wave 6 遗留） |
| `packages/shared-ui/vitest.config.ts` | shared-ui 测试配置 |

**修改文件：**

| 路径 | 改动 |
|---|---|
| `apps/agent-core/app/models.py` | 新增 `LiteratureRecord`、`LiteratureImportBatch` |
| `apps/agent-core/app/schemas.py` | 新增文献库请求/响应模型 |
| `apps/agent-core/app/routers/workspace.py` | 新增 4 个端点 |
| `apps/agent-core/app/services/stage_entry.py` | 新增 `literature` 卡片并纳入深页路由集合 |
| `packages/shared-ui/src/SearchSourceConfigScreen.tsx` | 导出 `toggleKey` / `parseYear` 供测试 |
| `packages/shared-ui/src/index.ts` | 导出新组件与两个纯函数 |
| `packages/shared-ui/package.json` | 加 vitest 依赖与 test script |
| `packages/shared-sdk/src/client.ts` | 新增类型与 4 个方法 |
| `packages/shared-sdk/src/session.test.ts` | 新增 4 个方法测试 |
| `apps/web/src/App.tsx` | 文献库状态与回调 |
| `apps/web/src/components/WorkspaceShell.tsx` | 新增 `literature` 屏幕 |
| `apps/web/src/App.test.tsx` | 文献库流程测试 |
| `apps/desktop/src/App.tsx` | 文献库状态、回调、新增屏幕 |
| `apps/desktop/tests/app-auth.test.tsx` | 文献库流程测试 |

**任务依赖顺序：** Task 1（解析器）→ Task 2（模型与导入 API）→ Task 3（去重与确认）→ Task 4（SDK）→ Task 5（共享组件 + 双端接线）→ Task 6（shared-ui 补测）

---

## Task 1: 解析器纯函数

极简格式解析与标题归一化（spec 6.1 / 5.4 / 12.1）。纯函数不依赖 session，先做掉它，后面去重逻辑要用它的归一化。

**Files:**
- Create: `apps/agent-core/app/services/literature_parser.py`
- Create: `apps/agent-core/tests/test_literature_parser.py`

- [ ] **Step 1: 写失败测试**

创建 `apps/agent-core/tests/test_literature_parser.py`：

```python
from app.services.literature_parser import (
    ParsedLiteratureEntry,
    normalize_title,
    parse_literature_text,
)


def test_parse_multiple_entries_separated_by_dashes() -> None:
    raw = """title: Metformin and cardiovascular outcomes
authors: Chen L, Wang H
journal: Lancet
year: 2023
doi: 10.1016/S2213-8587
pmid: 37123456
abstract: This study evaluates outcomes.
---
title: SGLT2 inhibitors in heart failure
authors: Zhang Y
journal: NEJM
year: 2022
"""

    result = parse_literature_text(raw)

    assert len(result.entries) == 2
    assert result.skipped_count == 0

    first = result.entries[0]
    assert first.title == "Metformin and cardiovascular outcomes"
    assert first.authors == "Chen L, Wang H"
    assert first.journal == "Lancet"
    assert first.year == 2023
    assert first.doi == "10.1016/S2213-8587"
    assert first.pmid == "37123456"
    assert first.abstract == "This study evaluates outcomes."

    second = result.entries[1]
    assert second.title == "SGLT2 inhibitors in heart failure"
    assert second.year == 2022
    assert second.doi == ""
    assert second.pmid == ""


def test_parse_single_entry_without_separator() -> None:
    result = parse_literature_text("title: Only one paper")

    assert len(result.entries) == 1
    assert result.entries[0] == ParsedLiteratureEntry(
        title="Only one paper",
        authors="",
        journal="",
        year=None,
        doi="",
        pmid="",
        abstract="",
    )


def test_parse_ignores_unknown_keys_and_blank_lines() -> None:
    raw = """title: A paper

publisher: Some Press
volume: 12
authors: Li Q
"""

    result = parse_literature_text(raw)

    assert len(result.entries) == 1
    assert result.entries[0].title == "A paper"
    assert result.entries[0].authors == "Li Q"


def test_parse_is_case_insensitive_for_keys() -> None:
    result = parse_literature_text("Title: Mixed case key\nYEAR: 2021")

    assert result.entries[0].title == "Mixed case key"
    assert result.entries[0].year == 2021


def test_parse_sets_year_to_none_when_not_an_integer() -> None:
    result = parse_literature_text("title: Bad year\nyear: in press")

    assert result.entries[0].year is None


def test_parse_skips_blocks_without_title() -> None:
    raw = """title: Good entry
year: 2020
---
authors: No Title Here
year: 2021
---
title: Another good entry
"""

    result = parse_literature_text(raw)

    assert [entry.title for entry in result.entries] == [
        "Good entry",
        "Another good entry",
    ]
    assert result.skipped_count == 1


def test_parse_returns_no_entries_for_unparseable_text() -> None:
    result = parse_literature_text("this text has no recognizable fields at all")

    assert result.entries == []
    assert result.skipped_count == 0


def test_parse_trims_whitespace_around_values() -> None:
    result = parse_literature_text("title:    Padded title   \nauthors:  Wang H  ")

    assert result.entries[0].title == "Padded title"
    assert result.entries[0].authors == "Wang H"


def test_normalize_title_strips_case_and_punctuation() -> None:
    assert normalize_title("Metformin in T2DM.") == normalize_title("metformin in t2dm")
    assert normalize_title("A  Study,  Revisited!") == "astudyrevisited"


def test_normalize_title_handles_empty_string() -> None:
    assert normalize_title("") == ""
    assert normalize_title("   ") == ""
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\test_literature_parser.py" -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.literature_parser'`

- [ ] **Step 3: 写最小实现**

创建 `apps/agent-core/app/services/literature_parser.py`：

```python
import re

from pydantic import BaseModel

ENTRY_SEPARATOR = "---"
KNOWN_KEYS = {"title", "authors", "journal", "year", "doi", "pmid", "abstract"}


class ParsedLiteratureEntry(BaseModel):
    title: str
    authors: str = ""
    journal: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    abstract: str = ""


class ParseResult(BaseModel):
    entries: list[ParsedLiteratureEntry]
    skipped_count: int


def normalize_title(title: str) -> str:
    """转小写并去除所有非字母数字字符，用于标题级去重比较。"""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def _parse_block(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}

    for line in lines:
        if ":" not in line:
            continue

        raw_key, raw_value = line.split(":", 1)
        key = raw_key.strip().lower()
        if key in KNOWN_KEYS:
            fields[key] = raw_value.strip()

    return fields


def _to_year(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None


def parse_literature_text(raw_text: str) -> ParseResult:
    blocks: list[list[str]] = [[]]

    for line in raw_text.splitlines():
        if line.strip() == ENTRY_SEPARATOR:
            blocks.append([])
            continue

        if line.strip() == "":
            continue

        blocks[-1].append(line)

    entries: list[ParsedLiteratureEntry] = []
    skipped_count = 0

    for block in blocks:
        fields = _parse_block(block)
        if not fields:
            continue

        title = fields.get("title", "")
        if title == "":
            skipped_count += 1
            continue

        entries.append(
            ParsedLiteratureEntry(
                title=title,
                authors=fields.get("authors", ""),
                journal=fields.get("journal", ""),
                year=_to_year(fields.get("year", "")),
                doi=fields.get("doi", ""),
                pmid=fields.get("pmid", ""),
                abstract=fields.get("abstract", ""),
            )
        )

    return ParseResult(entries=entries, skipped_count=skipped_count)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\test_literature_parser.py" -v`
Expected: PASS — 10 passed

- [ ] **Step 5: 跑全量后端确认没破坏既有测试**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\" -q`
Expected: PASS — 51 passed（Wave 6 的 41 个 + 本任务 10 个）

- [ ] **Step 6: 提交**

```bash
git add apps/agent-core/app/services/literature_parser.py apps/agent-core/tests/test_literature_parser.py
git commit -m "feat: add literature text parser and title normalization"
```

---

## Task 2: 条目模型与导入 API

新增两张表、schemas、service 与前两个端点（spec 5.2 / 5.3 / 9 / 10）。本任务先把导入与列表打通，去重逻辑留到 Task 3。

**Files:**
- Modify: `apps/agent-core/app/models.py`（在 `SearchSourceConfig` 之后、`AuditEvent` 之前插入）
- Modify: `apps/agent-core/app/schemas.py`（末尾追加）
- Create: `apps/agent-core/app/services/literature.py`
- Modify: `apps/agent-core/app/routers/workspace.py`
- Modify: `apps/agent-core/app/services/stage_entry.py`
- Create: `apps/agent-core/tests/test_literature_api.py`

- [ ] **Step 1: 写失败测试**

创建 `apps/agent-core/tests/test_literature_api.py`：

```python
from fastapi.testclient import TestClient

from app.main import app

TWO_ENTRIES = """title: Metformin and cardiovascular outcomes
authors: Chen L, Wang H
journal: Lancet
year: 2023
doi: 10.1016/S2213-8587
pmid: 37123456
---
title: SGLT2 inhibitors in heart failure
authors: Zhang Y
journal: NEJM
year: 2022
doi: 10.1056/NEJMoa2201234
"""


def _login_and_create_project(client: TestClient) -> tuple[str, int]:
    login = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "demo-hospital",
            "organization_name": "Demo Hospital",
            "user_id": "u-001",
            "display_name": "Dr. Chen",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    token = login.json()["token"]

    project = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "Wave 7 literature library",
        },
    )

    return token, project.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_literature_library_starts_empty() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/literature",
        headers=_auth(token),
    )
    body = response.json()

    assert response.status_code == 200
    assert body["project"]["id"] == project_id
    assert body["stage_key"] == "search"
    assert body["records"] == []
    assert body["stats"]["total_count"] == 0
    assert body["stats"]["unique_count"] == 0
    assert body["stats"]["duplicate_count"] == 0
    assert body["recent_batches"] == []
    assert body["last_import_result"] is None
    assert [item["key"] for item in body["available_sources"]][0] == "pubmed"


def test_import_creates_records_and_batch() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "pubmed", "raw_text": TWO_ENTRIES},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["last_import_result"]["imported_count"] == 2
    assert body["last_import_result"]["duplicate_count"] == 0
    assert body["last_import_result"]["skipped_count"] == 0

    titles = [record["title"] for record in body["records"]]
    assert "Metformin and cardiovascular outcomes" in titles
    assert "SGLT2 inhibitors in heart failure" in titles

    first = next(
        record
        for record in body["records"]
        if record["title"] == "Metformin and cardiovascular outcomes"
    )
    assert first["authors"] == "Chen L, Wang H"
    assert first["journal"] == "Lancet"
    assert first["year"] == 2023
    assert first["doi"] == "10.1016/S2213-8587"
    assert first["pmid"] == "37123456"
    assert first["source_key"] == "pubmed"
    assert first["source_label"] == "PubMed"
    assert first["dedupe_status"] == "unique"
    assert first["duplicate_of_id"] is None
    assert "abstract" not in first

    assert body["stats"]["total_count"] == 2
    assert body["stats"]["unique_count"] == 2
    assert len(body["recent_batches"]) == 1
    assert body["recent_batches"][0]["parsed_count"] == 2


def test_import_accepts_entry_with_title_only() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "embase", "raw_text": "title: Minimal entry"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["last_import_result"]["imported_count"] == 1
    assert body["records"][0]["title"] == "Minimal entry"
    assert body["records"][0]["year"] is None
    assert body["records"][0]["doi"] == ""


def test_import_skips_blocks_without_title_and_keeps_the_rest() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    raw = """title: Good one
year: 2020
---
authors: Missing Title
year: 2021
---
title: Good two
year: 2019
"""

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "pubmed", "raw_text": raw},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["last_import_result"]["imported_count"] == 2
    assert body["last_import_result"]["skipped_count"] == 1
    assert body["stats"]["total_count"] == 2


def test_import_rejects_unparseable_text_with_422() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "pubmed", "raw_text": "nothing useful here"},
    )

    assert response.status_code == 422
    assert "解析" in response.json()["detail"] or "parse" in response.json()["detail"].lower()


def test_import_rejects_unknown_source_key_with_422() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "not-a-database", "raw_text": "title: Some paper"},
    )

    assert response.status_code == 422
    assert "not-a-database" in response.json()["detail"]


def test_create_record_manually() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/records",
        headers=_auth(token),
        json={
            "title": "Hand entered paper",
            "authors": "Liu M",
            "journal": "BMJ",
            "year": 2021,
            "doi": "10.1136/bmj.n1234",
            "pmid": "",
            "abstract": "Manually typed abstract.",
            "source_key": "cochrane",
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["records"][0]["title"] == "Hand entered paper"
    assert body["records"][0]["source_label"] == "Cochrane Library"
    assert body["records"][0]["dedupe_status"] == "unique"
    assert body["stats"]["total_count"] == 1
    assert body["recent_batches"] == []
    assert body["last_import_result"] is None


def test_create_record_rejects_blank_title_with_422() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/records",
        headers=_auth(token),
        json={
            "title": "   ",
            "authors": "",
            "journal": "",
            "year": None,
            "doi": "",
            "pmid": "",
            "abstract": "",
            "source_key": "pubmed",
        },
    )

    assert response.status_code == 422


def test_literature_stats_group_by_source() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "pubmed", "raw_text": TWO_ENTRIES},
    )
    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "cnki", "raw_text": "title: A Chinese study\nyear: 2020"},
    )

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/literature",
        headers=_auth(token),
    ).json()
    by_source = {item["source_key"]: item["count"] for item in body["stats"]["by_source"]}

    assert body["stats"]["total_count"] == 3
    assert by_source["pubmed"] == 2
    assert by_source["cnki"] == 1
    assert len(body["recent_batches"]) == 2


def test_literature_rejects_project_from_other_organization() -> None:
    client = TestClient(app)
    _, project_id = _login_and_create_project(client)

    other = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "other-hospital",
            "organization_name": "Other Hospital",
            "user_id": "u-002",
            "display_name": "Dr. Li",
            "role": "org_admin",
            "client_type": "web",
        },
    )

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/literature",
        headers=_auth(other.json()["token"]),
    )

    assert response.status_code == 404


def test_stage_entry_points_literature_card_to_project_deep_page() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search",
        headers=_auth(token),
    ).json()
    card = next(item for item in body["entry_cards"] if item["key"] == "literature")

    assert card["title"] == "文献条目库"
    assert card["target"] == (
        f"/workspace/projects/{project_id}/stages/search/literature"
    )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\test_literature_api.py" -v`
Expected: FAIL — 所有端点返回 404，`literature` 卡片不存在

- [ ] **Step 3: 新增数据模型**

在 `apps/agent-core/app/models.py` 的 `SearchSourceConfig` 类之后、`AuditEvent` 之前插入：

```python
class LiteratureImportBatch(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    source_key: str
    parsed_count: int = 0
    duplicate_count: int = 0
    skipped_count: int = 0
    created_at_label: str = "刚刚导入"


class LiteratureRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    title: str
    authors: str = ""
    journal: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    abstract: str = ""
    source_key: str
    dedupe_status: str = "unique"
    duplicate_of_id: int | None = None
    import_batch_id: int | None = None
```

- [ ] **Step 4: 新增 schemas**

在 `apps/agent-core/app/schemas.py` 末尾追加。`WorkspaceProjectSummary` 与 `SourceCatalogItemResponse` 已在文件中定义，直接复用：

```python
class LiteratureRecordSummary(BaseModel):
    id: int
    title: str
    authors: str
    journal: str
    year: int | None
    doi: str
    pmid: str
    source_key: str
    source_label: str
    dedupe_status: str
    duplicate_of_id: int | None


class LiteratureSourceCount(BaseModel):
    source_key: str
    source_label: str
    count: int


class LiteratureStats(BaseModel):
    total_count: int
    unique_count: int
    duplicate_count: int
    by_source: list[LiteratureSourceCount]


class LiteratureBatchSummary(BaseModel):
    id: int
    source_key: str
    source_label: str
    parsed_count: int
    duplicate_count: int
    skipped_count: int
    created_at_label: str


class ImportResultSummary(BaseModel):
    imported_count: int
    duplicate_count: int
    skipped_count: int


class LiteratureLibraryResponse(BaseModel):
    project: WorkspaceProjectSummary
    stage_key: str
    records: list[LiteratureRecordSummary]
    stats: LiteratureStats
    recent_batches: list[LiteratureBatchSummary]
    available_sources: list[SourceCatalogItemResponse]
    last_import_result: ImportResultSummary | None = None


class ImportLiteratureRequest(BaseModel):
    source_key: str
    raw_text: str


class CreateLiteratureRecordRequest(BaseModel):
    title: str
    authors: str = ""
    journal: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    abstract: str = ""
    source_key: str
```

- [ ] **Step 5: 新增 service**

创建 `apps/agent-core/app/services/literature.py`。本任务先不实现去重，`_detect_duplicate` 返回 `None` 占位，Task 3 会替换它：

```python
from sqlmodel import Session, select

from app.models import LiteratureImportBatch, LiteratureRecord, ResearchProject
from app.schemas import (
    CreateLiteratureRecordRequest,
    ImportLiteratureRequest,
    ImportResultSummary,
    LiteratureBatchSummary,
    LiteratureLibraryResponse,
    LiteratureRecordSummary,
    LiteratureSourceCount,
    LiteratureStats,
    SourceCatalogItemResponse,
    WorkspaceProjectSummary,
)
from app.services.literature_parser import parse_literature_text
from app.services.source_catalog import SOURCE_CATALOG, SOURCE_KEYS

UNIQUE_STATUSES = {"unique", "confirmed_unique"}


class LiteratureError(Exception):
    """请求中携带了非法的来源 key、无法解析的文本，或非法的条目状态。"""


def _source_label(source_key: str) -> str:
    for item in SOURCE_CATALOG:
        if item.key == source_key:
            return item.label

    return source_key


def _require_known_source(source_key: str) -> None:
    if source_key not in SOURCE_KEYS:
        raise LiteratureError(f"unknown source key: {source_key}")


def _detect_duplicate(
    session: Session,
    project_id: int,
    candidate: LiteratureRecord,
) -> int | None:
    """Task 3 会实现三级去重判定，本任务先不判重。"""
    return None


def _to_record_summary(record: LiteratureRecord) -> LiteratureRecordSummary:
    return LiteratureRecordSummary(
        id=record.id or 0,
        title=record.title,
        authors=record.authors,
        journal=record.journal,
        year=record.year,
        doi=record.doi,
        pmid=record.pmid,
        source_key=record.source_key,
        source_label=_source_label(record.source_key),
        dedupe_status=record.dedupe_status,
        duplicate_of_id=record.duplicate_of_id,
    )


def _build_stats(records: list[LiteratureRecord]) -> LiteratureStats:
    counts: dict[str, int] = {}
    for record in records:
        counts[record.source_key] = counts.get(record.source_key, 0) + 1

    return LiteratureStats(
        total_count=len(records),
        unique_count=sum(
            1 for record in records if record.dedupe_status in UNIQUE_STATUSES
        ),
        duplicate_count=sum(
            1 for record in records if record.dedupe_status == "duplicate"
        ),
        by_source=[
            LiteratureSourceCount(
                source_key=item.key,
                source_label=item.label,
                count=counts[item.key],
            )
            for item in SOURCE_CATALOG
            if item.key in counts
        ],
    )


def build_library_response(
    session: Session,
    project: ResearchProject,
    last_import_result: ImportResultSummary | None = None,
) -> LiteratureLibraryResponse:
    project_id = project.id or 0
    records = list(
        session.exec(
            select(LiteratureRecord)
            .where(LiteratureRecord.project_id == project_id)
            .order_by(LiteratureRecord.id)
        )
    )
    batches = list(
        session.exec(
            select(LiteratureImportBatch)
            .where(LiteratureImportBatch.project_id == project_id)
            .order_by(LiteratureImportBatch.id)
        )
    )

    return LiteratureLibraryResponse(
        project=WorkspaceProjectSummary(
            id=project_id,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="检索",
            updated_at_label="刚刚更新",
        ),
        stage_key="search",
        records=[_to_record_summary(record) for record in records],
        stats=_build_stats(records),
        recent_batches=[
            LiteratureBatchSummary(
                id=batch.id or 0,
                source_key=batch.source_key,
                source_label=_source_label(batch.source_key),
                parsed_count=batch.parsed_count,
                duplicate_count=batch.duplicate_count,
                skipped_count=batch.skipped_count,
                created_at_label=batch.created_at_label,
            )
            for batch in batches
        ],
        available_sources=[
            SourceCatalogItemResponse(
                key=item.key,
                label=item.label,
                description=item.description,
                supports_full_text=item.supports_full_text,
            )
            for item in SOURCE_CATALOG
        ],
        last_import_result=last_import_result,
    )


def import_literature(
    session: Session,
    project: ResearchProject,
    payload: ImportLiteratureRequest,
) -> LiteratureLibraryResponse:
    _require_known_source(payload.source_key)

    parsed = parse_literature_text(payload.raw_text)
    if not parsed.entries:
        raise LiteratureError("无法从粘贴内容中解析出任何条目")

    project_id = project.id or 0
    batch = LiteratureImportBatch(
        project_id=project_id,
        source_key=payload.source_key,
        parsed_count=len(parsed.entries),
        skipped_count=parsed.skipped_count,
    )
    session.add(batch)
    session.commit()
    session.refresh(batch)

    duplicate_count = 0
    for entry in parsed.entries:
        record = LiteratureRecord(
            project_id=project_id,
            title=entry.title,
            authors=entry.authors,
            journal=entry.journal,
            year=entry.year,
            doi=entry.doi,
            pmid=entry.pmid,
            abstract=entry.abstract,
            source_key=payload.source_key,
            import_batch_id=batch.id,
        )
        original_id = _detect_duplicate(session, project_id, record)
        if original_id is not None:
            record.dedupe_status = "duplicate"
            record.duplicate_of_id = original_id
            duplicate_count += 1

        session.add(record)
        session.commit()

    batch.duplicate_count = duplicate_count
    session.add(batch)
    session.commit()

    return build_library_response(
        session,
        project,
        ImportResultSummary(
            imported_count=len(parsed.entries),
            duplicate_count=duplicate_count,
            skipped_count=parsed.skipped_count,
        ),
    )


def create_literature_record(
    session: Session,
    project: ResearchProject,
    payload: CreateLiteratureRecordRequest,
) -> LiteratureLibraryResponse:
    _require_known_source(payload.source_key)

    title = payload.title.strip()
    if title == "":
        raise LiteratureError("title 不能为空")

    project_id = project.id or 0
    record = LiteratureRecord(
        project_id=project_id,
        title=title,
        authors=payload.authors,
        journal=payload.journal,
        year=payload.year,
        doi=payload.doi,
        pmid=payload.pmid,
        abstract=payload.abstract,
        source_key=payload.source_key,
    )
    original_id = _detect_duplicate(session, project_id, record)
    if original_id is not None:
        record.dedupe_status = "duplicate"
        record.duplicate_of_id = original_id

    session.add(record)
    session.commit()

    return build_library_response(session, project)
```

- [ ] **Step 6: 新增端点**

在 `apps/agent-core/app/routers/workspace.py` 的 `from app.schemas import (...)` 中按字母序合并新增项：

```python
    CreateLiteratureRecordRequest,
    ImportLiteratureRequest,
    LiteratureLibraryResponse,
```

在 `from app.services.search_source import (...)` 之前插入新的 import 块（保持模块名字母序，`literature` 在 `search_query` 之前）：

```python
from app.services.literature import (
    LiteratureError,
    build_library_response,
    create_literature_record,
    import_literature,
)
```

在文件末尾追加两个端点：

```python
@router.get(
    "/projects/{project_id}/stages/search/literature",
    response_model=LiteratureLibraryResponse,
)
def get_literature_library(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    project = _load_project_or_404(session, project_id, context)

    return build_library_response(session, project)


@router.post(
    "/projects/{project_id}/stages/search/literature/import",
    response_model=LiteratureLibraryResponse,
)
def post_literature_import(
    project_id: int,
    payload: ImportLiteratureRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        return import_literature(session, project, payload)
    except LiteratureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.post(
    "/projects/{project_id}/stages/search/literature/records",
    response_model=LiteratureLibraryResponse,
)
def post_literature_record(
    project_id: int,
    payload: CreateLiteratureRecordRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        return create_literature_record(session, project, payload)
    except LiteratureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
```

- [ ] **Step 7: 新增阶段入口卡片**

在 `apps/agent-core/app/services/stage_entry.py` 的 `STAGE_ENTRY_CONFIG["search"]["entry_cards"]` 列表中，`sources` 卡片之后、`search-log` 卡片之前插入：

```python
            StageEntryCardSummary(
                key="literature",
                title="文献条目库",
                description="导入与去重项目文献集合",
                status="ready",
                target="/workspace/stage/search/literature",
            ),
```

然后在 `build_stage_entry` 中把 `literature` 纳入深页路由集合（该集合当前为 `{"query-builder", "sources"}`，位于约 380 行）：

```python
        project_deep_page_keys = {"query-builder", "sources", "literature"}
```

- [ ] **Step 8: 运行测试确认通过**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\test_literature_api.py" -v`
Expected: PASS — 11 passed

- [ ] **Step 9: 跑全量后端回归**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\" -q`
Expected: PASS — 62 passed（51 + 本任务 11 个）

- [ ] **Step 10: 提交**

```bash
git add apps/agent-core/app/models.py apps/agent-core/app/schemas.py apps/agent-core/app/services/literature.py apps/agent-core/app/routers/workspace.py apps/agent-core/app/services/stage_entry.py apps/agent-core/tests/test_literature_api.py
git commit -m "feat: add literature record model, import and manual entry API"
```

---

## Task 3: 三级去重与人工确认

**本波核心逻辑。** 实现 `_detect_duplicate` 的三级判定，并新增 confirm-unique 端点（spec 5.4 / 5.5 / 8.2 / 12.2）。

去重规则（命中即停）：
1. `doi` 非空且相同
2. `pmid` 非空且相同
3. 标题归一化后相同 **且** `year` 相同（含都为 `None`；一方已知一方 `None` 不判重）

**Files:**
- Modify: `apps/agent-core/app/services/literature.py`
- Modify: `apps/agent-core/app/routers/workspace.py`
- Modify: `apps/agent-core/tests/test_literature_api.py`

- [ ] **Step 1: 写失败测试**

在 `apps/agent-core/tests/test_literature_api.py` 末尾追加：

```python
def _import(client: TestClient, token: str, project_id: int, raw: str, source: str = "pubmed"):
    return client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": source, "raw_text": raw},
    ).json()


def test_same_doi_is_marked_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Original paper\ndoi: 10.1/abc")
    body = _import(
        client, token, project_id, "title: Different title\ndoi: 10.1/abc", "embase"
    )

    original = next(r for r in body["records"] if r["title"] == "Original paper")
    dup = next(r for r in body["records"] if r["title"] == "Different title")

    assert original["dedupe_status"] == "unique"
    assert dup["dedupe_status"] == "duplicate"
    assert dup["duplicate_of_id"] == original["id"]
    assert body["last_import_result"]["duplicate_count"] == 1
    assert body["stats"]["total_count"] == 2
    assert body["stats"]["unique_count"] == 1
    assert body["stats"]["duplicate_count"] == 1


def test_same_pmid_is_marked_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: First\npmid: 12345")
    body = _import(client, token, project_id, "title: Second\npmid: 12345", "embase")

    dup = next(r for r in body["records"] if r["title"] == "Second")
    original = next(r for r in body["records"] if r["title"] == "First")

    assert dup["dedupe_status"] == "duplicate"
    assert dup["duplicate_of_id"] == original["id"]


def test_normalized_title_with_same_year_is_marked_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Metformin in T2DM.\nyear: 2023")
    body = _import(
        client, token, project_id, "title: metformin in t2dm\nyear: 2023", "embase"
    )

    dup = next(r for r in body["records"] if r["title"] == "metformin in t2dm")

    assert dup["dedupe_status"] == "duplicate"
    assert body["stats"]["duplicate_count"] == 1


def test_same_title_with_different_year_is_not_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Shared title\nyear: 2020")
    body = _import(
        client, token, project_id, "title: Shared title\nyear: 2023", "embase"
    )

    assert body["stats"]["duplicate_count"] == 0
    assert body["stats"]["unique_count"] == 2


def test_same_title_with_one_unknown_year_is_not_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Shared title\nyear: 2020")
    body = _import(client, token, project_id, "title: Shared title", "embase")

    assert body["stats"]["duplicate_count"] == 0
    assert body["stats"]["unique_count"] == 2


def test_same_title_with_both_years_unknown_is_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: No year paper")
    body = _import(client, token, project_id, "title: No year paper", "embase")

    assert body["stats"]["duplicate_count"] == 1


def test_blank_doi_does_not_trigger_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Paper A\nyear: 2020")
    body = _import(client, token, project_id, "title: Paper B\nyear: 2021", "embase")

    assert body["stats"]["duplicate_count"] == 0


def test_blank_pmid_does_not_trigger_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Paper C\nyear: 2020\npmid:")
    body = _import(
        client, token, project_id, "title: Paper D\nyear: 2021\npmid:", "embase"
    )

    assert body["stats"]["duplicate_count"] == 0


def test_duplicate_within_the_same_batch_is_detected() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    raw = """title: In batch original
doi: 10.9/xyz
---
title: In batch copy
doi: 10.9/xyz
"""
    body = _import(client, token, project_id, raw)

    original = next(r for r in body["records"] if r["title"] == "In batch original")
    dup = next(r for r in body["records"] if r["title"] == "In batch copy")

    assert original["dedupe_status"] == "unique"
    assert dup["dedupe_status"] == "duplicate"
    assert dup["duplicate_of_id"] == original["id"]
    assert body["last_import_result"]["duplicate_count"] == 1


def test_three_same_doi_records_all_point_to_the_first() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    raw = """title: First of three
doi: 10.7/dup
---
title: Second of three
doi: 10.7/dup
---
title: Third of three
doi: 10.7/dup
"""
    body = _import(client, token, project_id, raw)

    first = next(r for r in body["records"] if r["title"] == "First of three")
    second = next(r for r in body["records"] if r["title"] == "Second of three")
    third = next(r for r in body["records"] if r["title"] == "Third of three")

    assert first["dedupe_status"] == "unique"
    assert second["duplicate_of_id"] == first["id"]
    assert third["duplicate_of_id"] == first["id"]
    assert body["stats"]["duplicate_count"] == 2


def test_duplicates_are_not_deleted() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Kept original\ndoi: 10.5/keep")
    _import(client, token, project_id, "title: Kept copy\ndoi: 10.5/keep", "embase")

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/literature",
        headers=_auth(token),
    ).json()

    assert len(body["records"]) == 2
    assert body["stats"]["total_count"] == 2


def test_dedupe_does_not_cross_projects() -> None:
    client = TestClient(app)
    token, first_project_id = _login_and_create_project(client)

    second = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "第二个项目",
            "description": "cross project dedupe check",
        },
    )
    second_project_id = second.json()["id"]

    _import(client, token, first_project_id, "title: Shared across\ndoi: 10.3/cross")
    body = _import(client, token, second_project_id, "title: Shared across\ndoi: 10.3/cross")

    assert body["stats"]["duplicate_count"] == 0
    assert body["stats"]["unique_count"] == 1


def test_confirm_unique_clears_duplicate_marking() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Base paper\ndoi: 10.2/base")
    imported = _import(
        client, token, project_id, "title: Flagged paper\ndoi: 10.2/base", "embase"
    )
    dup_id = next(r for r in imported["records"] if r["title"] == "Flagged paper")["id"]

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature"
        f"/records/{dup_id}/confirm-unique",
        headers=_auth(token),
    )
    body = response.json()
    confirmed = next(r for r in body["records"] if r["id"] == dup_id)

    assert response.status_code == 200
    assert confirmed["dedupe_status"] == "confirmed_unique"
    assert confirmed["duplicate_of_id"] is None
    assert body["stats"]["unique_count"] == 2
    assert body["stats"]["duplicate_count"] == 0


def test_confirmed_unique_still_serves_as_dedupe_original() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Anchor\ndoi: 10.4/anchor")
    imported = _import(
        client, token, project_id, "title: Rejected flag\ndoi: 10.4/anchor", "embase"
    )
    dup_id = next(r for r in imported["records"] if r["title"] == "Rejected flag")["id"]

    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature"
        f"/records/{dup_id}/confirm-unique",
        headers=_auth(token),
    )

    body = _import(client, token, project_id, "title: Third copy\ndoi: 10.4/anchor", "cnki")
    third = next(r for r in body["records"] if r["title"] == "Third copy")

    assert third["dedupe_status"] == "duplicate"
    assert third["duplicate_of_id"] is not None


def test_confirm_unique_rejects_non_duplicate_record_with_422() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    imported = _import(client, token, project_id, "title: Plain unique paper")
    record_id = imported["records"][0]["id"]

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature"
        f"/records/{record_id}/confirm-unique",
        headers=_auth(token),
    )

    assert response.status_code == 422


def test_confirm_unique_rejects_unknown_record_with_404() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature"
        "/records/99999/confirm-unique",
        headers=_auth(token),
    )

    assert response.status_code == 404
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\test_literature_api.py" -v`
Expected: FAIL — 去重相关测试因 `_detect_duplicate` 恒返回 `None` 而失败；confirm-unique 端点返回 404

- [ ] **Step 3: 实现三级去重判定**

在 `apps/agent-core/app/services/literature.py` 中，把 imports 里的解析器引用改为同时引入归一化函数：

```python
from app.services.literature_parser import normalize_title, parse_literature_text
```

然后把占位的 `_detect_duplicate` 整个函数替换为：

```python
def _detect_duplicate(
    session: Session,
    project_id: int,
    candidate: LiteratureRecord,
) -> int | None:
    """三级判定，命中即停。只在同项目内比较，且不以 duplicate 记录作为原件。"""
    existing = list(
        session.exec(
            select(LiteratureRecord)
            .where(
                LiteratureRecord.project_id == project_id,
                LiteratureRecord.dedupe_status != "duplicate",
            )
            .order_by(LiteratureRecord.id)
        )
    )

    if candidate.doi != "":
        for record in existing:
            if record.doi == candidate.doi:
                return record.id

    if candidate.pmid != "":
        for record in existing:
            if record.pmid == candidate.pmid:
                return record.id

    candidate_title = normalize_title(candidate.title)
    for record in existing:
        if (
            normalize_title(record.title) == candidate_title
            and record.year == candidate.year
        ):
            return record.id

    return None
```

三点说明：
- 过滤 `dedupe_status != "duplicate"` 保证不形成判重链，第三条同 DOI 的记录会指向第一条而非第二条
- `confirmed_unique` 不在过滤范围内，因此它仍可作为原件（spec 5.5）
- `record.year == candidate.year` 天然处理了"都为 `None` 判重、一方 `None` 不判重"

- [ ] **Step 4: 新增确认函数**

先在 `apps/agent-core/app/services/literature.py` 中找到文件开头的 `LiteratureError` 类定义，在它**紧后面**插入第二个异常类：

```python
class LiteratureNotFoundError(Exception):
    """指定的文献条目不存在，或不属于当前项目。"""
```

两者都直接继承 `Exception` 而非互为父子。这样 router 可以分别映射到 `404` 与 `422`，不会因为继承关系导致 `except` 顺序影响结果。

然后在同一文件**末尾**追加确认函数：

```python
def confirm_record_unique(
    session: Session,
    project: ResearchProject,
    record_id: int,
) -> LiteratureLibraryResponse:
    record = session.get(LiteratureRecord, record_id)
    if record is None or record.project_id != (project.id or 0):
        raise LiteratureNotFoundError("record not found")

    if record.dedupe_status != "duplicate":
        raise LiteratureError(
            f"record {record_id} is not marked as duplicate"
        )

    record.dedupe_status = "confirmed_unique"
    record.duplicate_of_id = None
    session.add(record)
    session.commit()

    return build_library_response(session, project)
```

- [ ] **Step 5: 新增确认端点**

在 `apps/agent-core/app/routers/workspace.py` 的 `from app.services.literature import (...)` 中补充两个名字：

```python
from app.services.literature import (
    LiteratureError,
    LiteratureNotFoundError,
    build_library_response,
    confirm_record_unique,
    create_literature_record,
    import_literature,
)
```

在文件末尾追加端点：

```python
@router.post(
    "/projects/{project_id}/stages/search/literature/records/{record_id}/confirm-unique",
    response_model=LiteratureLibraryResponse,
)
def post_literature_confirm_unique(
    project_id: int,
    record_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        return confirm_record_unique(session, project, record_id)
    except LiteratureNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    except LiteratureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
```

注意 `except` 顺序：`LiteratureNotFoundError` 必须在 `LiteratureError` 之前。两者是独立的 `Exception` 子类，顺序不影响正确性，但保持"更具体的在前"这一习惯有利于后续若改为继承关系时不出错。

- [ ] **Step 6: 运行测试确认通过**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\test_literature_api.py" -v`
Expected: PASS — 27 passed

- [ ] **Step 7: 跑全量后端回归**

Run: `uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\" -q`
Expected: PASS — 78 passed

- [ ] **Step 8: 提交**

```bash
git add apps/agent-core/app/services/literature.py apps/agent-core/app/routers/workspace.py apps/agent-core/tests/test_literature_api.py
git commit -m "feat: add three-tier literature dedupe with manual confirmation"
```

---

## Task 4: Shared SDK

新增 4 个方法与配套类型（spec 12.5）。

**Files:**
- Modify: `packages/shared-sdk/src/client.ts`
- Modify: `packages/shared-sdk/src/session.test.ts`

- [ ] **Step 1: 写失败测试**

在 `packages/shared-sdk/src/session.test.ts` 的 `describe("workspace client")` 块内末尾追加。文件已有的写法是 `it(...)` + `vi.stubGlobal("fetch", ...)`，沿用该风格：

```typescript
  const libraryResponse = {
    project: {
      id: 1,
      name: "糖尿病真实世界研究",
      workspace_key: "demo-hospital/糖尿病真实世界研究",
      current_stage: "检索",
      updated_at_label: "刚刚更新",
    },
    stage_key: "search",
    records: [
      {
        id: 11,
        title: "Metformin and cardiovascular outcomes",
        authors: "Chen L",
        journal: "Lancet",
        year: 2023,
        doi: "10.1016/S2213-8587",
        pmid: "37123456",
        source_key: "pubmed",
        source_label: "PubMed",
        dedupe_status: "unique",
        duplicate_of_id: null,
      },
    ],
    stats: {
      total_count: 1,
      unique_count: 1,
      duplicate_count: 0,
      by_source: [{ source_key: "pubmed", source_label: "PubMed", count: 1 }],
    },
    recent_batches: [],
    available_sources: [
      {
        key: "pubmed",
        label: "PubMed",
        description: "美国国立医学图书馆生物医学文献库",
        supports_full_text: false,
      },
    ],
    last_import_result: null,
  };

  it("fetches the literature library", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => libraryResponse,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const library = await client.getLiteratureLibrary(1);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/literature",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(library.records[0].title).toBe(
      "Metformin and cardiovascular outcomes",
    );
    expect(library.stats.total_count).toBe(1);
  });

  it("imports literature from pasted text", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        ...libraryResponse,
        last_import_result: {
          imported_count: 2,
          duplicate_count: 1,
          skipped_count: 0,
        },
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const library = await client.importLiterature(1, {
      source_key: "pubmed",
      raw_text: "title: A paper",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/literature/import",
      expect.objectContaining({ method: "POST" }),
    );
    expect(library.last_import_result?.imported_count).toBe(2);
    expect(library.last_import_result?.duplicate_count).toBe(1);
  });

  it("creates a literature record manually", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => libraryResponse,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    await client.createLiteratureRecord(1, {
      title: "Hand entered",
      authors: "",
      journal: "",
      year: null,
      doi: "",
      pmid: "",
      abstract: "",
      source_key: "cochrane",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/literature/records",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("confirms a flagged record as unique", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => libraryResponse,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    await client.confirmLiteratureUnique(1, 11);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/literature/records/11/confirm-unique",
      expect.objectContaining({ method: "POST" }),
    );
  });
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix "d:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run`
Expected: FAIL — `client.getLiteratureLibrary is not a function` 等四处

- [ ] **Step 3: 新增类型**

在 `packages/shared-sdk/src/client.ts` 的 `SaveSearchSourceConfigPayload` 定义之后追加：

```typescript
export type LiteratureRecordSummary = {
  id: number;
  title: string;
  authors: string;
  journal: string;
  year: number | null;
  doi: string;
  pmid: string;
  source_key: string;
  source_label: string;
  dedupe_status: string;
  duplicate_of_id: number | null;
};

export type LiteratureSourceCount = {
  source_key: string;
  source_label: string;
  count: number;
};

export type LiteratureStats = {
  total_count: number;
  unique_count: number;
  duplicate_count: number;
  by_source: LiteratureSourceCount[];
};

export type LiteratureBatchSummary = {
  id: number;
  source_key: string;
  source_label: string;
  parsed_count: number;
  duplicate_count: number;
  skipped_count: number;
  created_at_label: string;
};

export type ImportResultSummary = {
  imported_count: number;
  duplicate_count: number;
  skipped_count: number;
};

export type LiteratureLibrarySummary = {
  project: WorkspaceProjectSummary;
  stage_key: string;
  records: LiteratureRecordSummary[];
  stats: LiteratureStats;
  recent_batches: LiteratureBatchSummary[];
  available_sources: SourceCatalogItem[];
  last_import_result: ImportResultSummary | null;
};

export type ImportLiteraturePayload = {
  source_key: string;
  raw_text: string;
};

export type CreateLiteratureRecordPayload = {
  title: string;
  authors: string;
  journal: string;
  year: number | null;
  doi: string;
  pmid: string;
  abstract: string;
  source_key: string;
};
```

- [ ] **Step 4: 新增方法**

在 `createClient` 返回对象内，`saveSearchSourceConfig` 之后追加：

```typescript
    async getLiteratureLibrary(
      projectId: number,
    ): Promise<LiteratureLibrarySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature`,
        {
          headers: buildHeaders(),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "literature library failed");
      }

      return data;
    },

    async importLiterature(
      projectId: number,
      payload: ImportLiteraturePayload,
    ): Promise<LiteratureLibrarySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature/import`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "literature import failed");
      }

      return data;
    },

    async createLiteratureRecord(
      projectId: number,
      payload: CreateLiteratureRecordPayload,
    ): Promise<LiteratureLibrarySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature/records`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "literature record create failed");
      }

      return data;
    },

    async confirmLiteratureUnique(
      projectId: number,
      recordId: number,
    ): Promise<LiteratureLibrarySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature/records/${recordId}/confirm-unique`,
        {
          method: "POST",
          headers: buildHeaders(),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "literature confirm unique failed");
      }

      return data;
    },
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm --prefix "d:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run`
Expected: PASS — 14 passed（原有 10 个 + 本任务 4 个）

- [ ] **Step 6: 提交**

```bash
git add packages/shared-sdk/src/client.ts packages/shared-sdk/src/session.test.ts
git commit -m "feat: add literature library methods to shared sdk"
```

---

## Task 5: 共享组件与双端接线

组件放入 `packages/shared-ui`，Web 与 Desktop import 同一实现（spec 7 / 8.4 / 12.6）。

**Files:**
- Create: `packages/shared-ui/src/LiteratureLibraryScreen.tsx`
- Modify: `packages/shared-ui/src/index.ts`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/components/WorkspaceShell.tsx`
- Modify: `apps/web/src/App.test.tsx`
- Modify: `apps/desktop/src/App.tsx`
- Modify: `apps/desktop/tests/app-auth.test.tsx`

- [ ] **Step 1: 写 Web 失败测试**

在 `apps/web/src/App.test.tsx` 中，先在 mock 定义区追加（放在 `saveSearchSourceConfig` 定义之后）：

```typescript
const literatureResponse = {
  project: {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
    current_stage: "检索",
    updated_at_label: "刚刚更新",
  },
  stage_key: "search",
  records: [
    {
      id: 11,
      title: "Metformin and cardiovascular outcomes",
      authors: "Chen L",
      journal: "Lancet",
      year: 2023,
      doi: "10.1016/S2213-8587",
      pmid: "37123456",
      source_key: "pubmed",
      source_label: "PubMed",
      dedupe_status: "unique",
      duplicate_of_id: null,
    },
    {
      id: 12,
      title: "Duplicated paper",
      authors: "Zhang Y",
      journal: "NEJM",
      year: 2023,
      doi: "10.1016/S2213-8587",
      pmid: "",
      source_key: "embase",
      source_label: "Embase",
      dedupe_status: "duplicate",
      duplicate_of_id: 11,
    },
  ],
  stats: {
    total_count: 2,
    unique_count: 1,
    duplicate_count: 1,
    by_source: [
      { source_key: "pubmed", source_label: "PubMed", count: 1 },
      { source_key: "embase", source_label: "Embase", count: 1 },
    ],
  },
  recent_batches: [],
  available_sources: [
    {
      key: "pubmed",
      label: "PubMed",
      description: "美国国立医学图书馆生物医学文献库",
      supports_full_text: false,
    },
    {
      key: "embase",
      label: "Embase",
      description: "爱思唯尔生物医学与药理学文献库",
      supports_full_text: false,
    },
  ],
  last_import_result: null,
};

const getLiteratureLibrary = vi.fn(async () => literatureResponse);

const importLiterature = vi.fn(async () => ({
  ...literatureResponse,
  last_import_result: {
    imported_count: 2,
    duplicate_count: 1,
    skipped_count: 0,
  },
}));

const confirmLiteratureUnique = vi.fn(async () => ({
  ...literatureResponse,
  records: [
    literatureResponse.records[0],
    {
      ...literatureResponse.records[1],
      dedupe_status: "confirmed_unique",
      duplicate_of_id: null,
    },
  ],
  stats: { ...literatureResponse.stats, unique_count: 2, duplicate_count: 0 },
}));
```

在 mock 的 `createClient` 返回对象中追加三个方法：

```typescript
    getLiteratureLibrary,
    importLiterature,
    confirmLiteratureUnique,
```

在 `getStageEntry` mock 的 `entry_cards` 数组中追加 `literature` 卡片：

```typescript
    {
      key: "literature",
      title: "文献条目库",
      description: "导入与去重项目文献集合",
      status: "ready",
      target: "/workspace/projects/1/stages/search/literature",
    },
```

在文件末尾追加测试：

```typescript
test("web workspace imports literature and confirms a duplicate", async () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("机构标识"), {
    target: { value: "demo-hospital" },
  });
  fireEvent.change(screen.getByLabelText("用户编号"), {
    target: { value: "u-001" },
  });
  fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "文献条目库" }));

  expect(getLiteratureLibrary).toHaveBeenCalledWith(1);
  expect(
    await screen.findByRole("heading", { name: "文献条目库" }),
  ).toBeInTheDocument();
  expect(screen.getByText("共 2 条 · 唯一 1 条 · 重复 1 条")).toBeInTheDocument();
  expect(
    screen.getByText("Metformin and cardiovascular outcomes"),
  ).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("粘贴文献条目"), {
    target: { value: "title: A pasted paper" },
  });
  fireEvent.click(screen.getByRole("button", { name: "导入" }));

  expect(importLiterature).toHaveBeenCalledWith(1, {
    source_key: "pubmed",
    raw_text: "title: A pasted paper",
  });
  expect(
    await screen.findByText("本次导入 2 条 · 重复 1 条 · 跳过 0 条"),
  ).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "标记为独立文献" }));

  expect(confirmLiteratureUnique).toHaveBeenCalledWith(1, 12);
  expect(
    await screen.findByText("共 2 条 · 唯一 2 条 · 重复 0 条"),
  ).toBeInTheDocument();
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix "d:\workspace\MedA" --workspace apps-web exec vitest run`
Expected: FAIL — 找不到 `文献条目库` 按钮

- [ ] **Step 3: 创建共享组件**

创建 `packages/shared-ui/src/LiteratureLibraryScreen.tsx`：

```typescript
import { useState } from "react";

import type {
  ImportLiteraturePayload,
  LiteratureLibrarySummary,
} from "@meda/shared-sdk";

export type LiteratureLibraryScreenProps = {
  library: LiteratureLibrarySummary;
  onBackToStageEntry: () => void;
  onImport: (payload: ImportLiteraturePayload) => void;
  onConfirmUnique: (recordId: number) => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

const badgeStyles: Record<string, { background: string; color: string; label: string }> = {
  unique: { background: "#ecfdf5", color: "#047857", label: "唯一" },
  duplicate: { background: "#fef2f2", color: "#b91c1c", label: "重复" },
  confirmed_unique: { background: "#eff6ff", color: "#1d4ed8", label: "已确认独立" },
};

export function LiteratureLibraryScreen({
  library,
  onBackToStageEntry,
  onImport,
  onConfirmUnique,
}: LiteratureLibraryScreenProps) {
  const [sourceKey, setSourceKey] = useState(
    library.available_sources[0]?.key ?? "pubmed",
  );
  const [rawText, setRawText] = useState("");

  const { stats, last_import_result: importResult } = library;

  return (
    <>
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <button
            style={{
              border: "1px solid #d0d7e2",
              background: "#ffffff",
              borderRadius: "999px",
              padding: "8px 14px",
              cursor: "pointer",
            }}
            onClick={onBackToStageEntry}
          >
            返回检索阶段入口页
          </button>
          <h2 style={{ margin: "16px 0 8px", fontSize: "30px" }}>文献条目库</h2>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>
            {library.project.name}
          </div>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>导入条目</h3>
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <label htmlFor="literature-source">来源</label>
            <select
              id="literature-source"
              value={sourceKey}
              onChange={(event) => setSourceKey(event.target.value)}
              style={{
                border: "1px solid #d0d7e2",
                borderRadius: "10px",
                padding: "8px 10px",
              }}
            >
              {library.available_sources.map((source) => (
                <option key={source.key} value={source.key}>
                  {source.label}
                </option>
              ))}
            </select>
          </div>

          <textarea
            aria-label="粘贴文献条目"
            value={rawText}
            onChange={(event) => setRawText(event.target.value)}
            rows={6}
            style={{
              width: "100%",
              marginTop: "12px",
              border: "1px solid #d0d7e2",
              borderRadius: "12px",
              padding: "10px 12px",
              fontFamily: "inherit",
              boxSizing: "border-box",
            }}
          />

          <button
            style={{
              marginTop: "12px",
              border: "none",
              background: "#111827",
              color: "#f9fafb",
              borderRadius: "999px",
              padding: "10px 16px",
              cursor: "pointer",
            }}
            onClick={() => onImport({ source_key: sourceKey, raw_text: rawText })}
          >
            导入
          </button>

          {importResult === null ? null : (
            <div style={{ marginTop: "12px", color: "#4b5563" }}>
              本次导入 {importResult.imported_count} 条 · 重复{" "}
              {importResult.duplicate_count} 条 · 跳过{" "}
              {importResult.skipped_count} 条
            </div>
          )}
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>条目列表</h3>
          {library.records.length === 0 ? (
            <div style={{ color: "#6b7280" }}>尚未导入任何文献条目</div>
          ) : (
            library.records.map((record) => {
              const badge = badgeStyles[record.dedupe_status] ?? badgeStyles.unique;

              return (
                <div
                  key={record.id}
                  style={{
                    marginBottom: "12px",
                    border: "1px solid #e5e7eb",
                    borderRadius: "12px",
                    padding: "12px 14px",
                  }}
                >
                  <div style={{ display: "flex", gap: "10px", alignItems: "baseline" }}>
                    <span style={{ fontWeight: 600 }}>{record.title}</span>
                    <span
                      style={{
                        background: badge.background,
                        color: badge.color,
                        borderRadius: "999px",
                        padding: "2px 10px",
                        fontSize: "12px",
                      }}
                    >
                      {badge.label}
                    </span>
                  </div>
                  <div
                    style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                  >
                    {record.authors} · {record.journal} · {record.year ?? "年份未知"} ·{" "}
                    {record.source_label}
                  </div>
                  <div
                    style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                  >
                    {record.doi === "" ? "" : `DOI ${record.doi}`}
                    {record.pmid === "" ? "" : ` · PMID ${record.pmid}`}
                  </div>
                  {record.dedupe_status === "duplicate" ? (
                    <button
                      style={{
                        marginTop: "10px",
                        border: "1px solid #d0d7e2",
                        background: "#ffffff",
                        borderRadius: "999px",
                        padding: "6px 12px",
                        cursor: "pointer",
                      }}
                      onClick={() => onConfirmUnique(record.id)}
                    >
                      标记为独立文献
                    </button>
                  ) : null}
                </div>
              );
            })
          )}
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>集合统计</h3>
          <div>
            共 {stats.total_count} 条 · 唯一 {stats.unique_count} 条 · 重复{" "}
            {stats.duplicate_count} 条
          </div>
          <div style={{ marginTop: "12px" }}>
            {stats.by_source.map((item) => (
              <div key={item.source_key} style={{ marginTop: "6px", color: "#4b5563" }}>
                {item.source_label}：{item.count} 条
              </div>
            ))}
          </div>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>最近导入</h3>
          {library.recent_batches.length === 0 ? (
            <div style={{ color: "#6b7280" }}>暂无导入记录</div>
          ) : (
            library.recent_batches.map((batch) => (
              <div key={batch.id} style={{ marginTop: "8px", color: "#4b5563" }}>
                {batch.source_label} · 解析 {batch.parsed_count} 条 · 重复{" "}
                {batch.duplicate_count} 条 · 跳过 {batch.skipped_count} 条
              </div>
            ))
          )}
        </section>
      </aside>
    </>
  );
}
```

- [ ] **Step 4: 导出组件**

把 `packages/shared-ui/src/index.ts` 整个替换为：

```typescript
export {
  LiteratureLibraryScreen,
  type LiteratureLibraryScreenProps,
} from "./LiteratureLibraryScreen";
export {
  SearchSourceConfigScreen,
  type SearchSourceConfigScreenProps,
} from "./SearchSourceConfigScreen";
```

- [ ] **Step 5: 接入 Web**

在 `apps/web/src/App.tsx` 的类型 import 中追加：

```typescript
  type ImportLiteraturePayload,
  type LiteratureLibrarySummary,
```

在 `sourceCatalog` 状态之后追加：

```typescript
  const [literatureLibrary, setLiteratureLibrary] =
    useState<LiteratureLibrarySummary | null>(null);
```

在 `handleLogin` 内 `setSourceConfig(null);` 之后追加 `setLiteratureLibrary(null);`。

在 `handleSaveSourceConfig` 之后追加三个回调：

```typescript
  const handleOpenLiteratureLibrary = async (projectId: number) => {
    const nextLibrary = await client.getLiteratureLibrary(projectId);
    setLiteratureLibrary(nextLibrary);
  };

  const handleImportLiterature = async (
    projectId: number,
    payload: ImportLiteraturePayload,
  ) => {
    const nextLibrary = await client.importLiterature(projectId, payload);
    setLiteratureLibrary(nextLibrary);
  };

  const handleConfirmLiteratureUnique = async (
    projectId: number,
    recordId: number,
  ) => {
    const nextLibrary = await client.confirmLiteratureUnique(projectId, recordId);
    setLiteratureLibrary(nextLibrary);
  };
```

在 `<WorkspaceShell ... />` 的 props 中追加：

```typescript
      literatureLibrary={literatureLibrary}
      onOpenLiteratureLibrary={handleOpenLiteratureLibrary}
      onImportLiterature={handleImportLiterature}
      onConfirmLiteratureUnique={handleConfirmLiteratureUnique}
```

- [ ] **Step 6: 接入 WorkspaceShell**

在 `apps/web/src/components/WorkspaceShell.tsx` 的 shared-ui import 中追加组件：

```typescript
import { LiteratureLibraryScreen, SearchSourceConfigScreen } from "@meda/shared-ui";
```

在类型 import 中追加：

```typescript
  ImportLiteraturePayload,
  LiteratureLibrarySummary,
```

在 `WorkspaceShellProps` 中追加四个 prop：

```typescript
  literatureLibrary: LiteratureLibrarySummary | null;
  onOpenLiteratureLibrary: (projectId: number) => Promise<void>;
  onImportLiterature: (
    projectId: number,
    payload: ImportLiteraturePayload,
  ) => Promise<void>;
  onConfirmLiteratureUnique: (
    projectId: number,
    recordId: number,
  ) => Promise<void>;
```

在 `Screen` 联合类型中追加 `| "literature"`。

在函数签名解构参数中追加 `literatureLibrary, onOpenLiteratureLibrary, onImportLiterature, onConfirmLiteratureUnique,`。

在 `source-config` 屏幕分支之后插入新分支：

```typescript
  if (screen === "literature" && literatureLibrary !== null) {
    return (
      <main style={shellStyle}>
        <LeftRail projects={projects} workspaceHome={workspaceHome} />
        <LiteratureLibraryScreen
          library={literatureLibrary}
          onBackToStageEntry={() => setScreen("stage-entry")}
          onImport={(payload) =>
            onImportLiterature(workspaceHome.project.id, payload)
          }
          onConfirmUnique={(recordId) =>
            onConfirmLiteratureUnique(workspaceHome.project.id, recordId)
          }
        />
      </main>
    );
  }
```

在 `stage-entry` 分支的 `onOpenEntryCard` 回调中，`sources` 分支之后追加：

```typescript
            if (entryKey === "literature") {
              await onOpenLiteratureLibrary(workspaceHome.project.id);
              setScreen("literature");
              return;
            }
```

- [ ] **Step 7: 运行 Web 测试确认通过**

Run: `npm --prefix "d:\workspace\MedA" --workspace apps-web exec vitest run`
Expected: PASS — 5 passed

- [ ] **Step 8: 写 Desktop 失败测试**

在 `apps/desktop/tests/app-auth.test.tsx` 中重复 Step 1 的三段改动。Desktop mock 是独立的，不跨文件复用，因此需要在本文件再写一份 `literatureResponse`：

```typescript
const literatureResponse = {
  project: {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
    current_stage: "检索",
    updated_at_label: "刚刚更新",
  },
  stage_key: "search",
  records: [
    {
      id: 11,
      title: "Metformin and cardiovascular outcomes",
      authors: "Chen L",
      journal: "Lancet",
      year: 2023,
      doi: "10.1016/S2213-8587",
      pmid: "37123456",
      source_key: "pubmed",
      source_label: "PubMed",
      dedupe_status: "unique",
      duplicate_of_id: null,
    },
    {
      id: 12,
      title: "Duplicated paper",
      authors: "Zhang Y",
      journal: "NEJM",
      year: 2023,
      doi: "10.1016/S2213-8587",
      pmid: "",
      source_key: "embase",
      source_label: "Embase",
      dedupe_status: "duplicate",
      duplicate_of_id: 11,
    },
  ],
  stats: {
    total_count: 2,
    unique_count: 1,
    duplicate_count: 1,
    by_source: [
      { source_key: "pubmed", source_label: "PubMed", count: 1 },
      { source_key: "embase", source_label: "Embase", count: 1 },
    ],
  },
  recent_batches: [],
  available_sources: [
    {
      key: "pubmed",
      label: "PubMed",
      description: "美国国立医学图书馆生物医学文献库",
      supports_full_text: false,
    },
    {
      key: "embase",
      label: "Embase",
      description: "爱思唯尔生物医学与药理学文献库",
      supports_full_text: false,
    },
  ],
  last_import_result: null,
};

const getLiteratureLibrary = vi.fn(async () => literatureResponse);

const importLiterature = vi.fn(async () => ({
  ...literatureResponse,
  last_import_result: {
    imported_count: 2,
    duplicate_count: 1,
    skipped_count: 0,
  },
}));

const confirmLiteratureUnique = vi.fn(async () => ({
  ...literatureResponse,
  records: [
    literatureResponse.records[0],
    {
      ...literatureResponse.records[1],
      dedupe_status: "confirmed_unique",
      duplicate_of_id: null,
    },
  ],
  stats: { ...literatureResponse.stats, unique_count: 2, duplicate_count: 0 },
}));
```

在 mock 的 `createClient` 返回对象中追加：

```typescript
    getLiteratureLibrary,
    importLiterature,
    confirmLiteratureUnique,
```

在 `getStageEntry` mock 的 `entry_cards` 中追加：

```typescript
        {
          key: "literature",
          title: "文献条目库",
          description: "导入与去重项目文献集合",
          status: "ready",
          target: "/workspace/projects/1/stages/search/literature",
        },
```

在文件末尾追加测试：

```typescript
test("desktop workspace imports literature and confirms a duplicate", async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "文献条目库" }));

  expect(getLiteratureLibrary).toHaveBeenCalledWith(1);
  expect(
    await screen.findByRole("heading", { name: "文献条目库" }),
  ).toBeInTheDocument();
  expect(screen.getByText("共 2 条 · 唯一 1 条 · 重复 1 条")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("粘贴文献条目"), {
    target: { value: "title: A pasted paper" },
  });
  fireEvent.click(screen.getByRole("button", { name: "导入" }));

  expect(importLiterature).toHaveBeenCalledWith(1, {
    source_key: "pubmed",
    raw_text: "title: A pasted paper",
  });

  fireEvent.click(await screen.findByRole("button", { name: "标记为独立文献" }));

  expect(confirmLiteratureUnique).toHaveBeenCalledWith(1, 12);
  expect(
    await screen.findByText("共 2 条 · 唯一 2 条 · 重复 0 条"),
  ).toBeInTheDocument();
});
```

- [ ] **Step 9: 接入 Desktop**

在 `apps/desktop/src/App.tsx` 的 shared-ui import 中追加组件：

```typescript
import { LiteratureLibraryScreen, SearchSourceConfigScreen } from "@meda/shared-ui";
```

在类型 import 中追加 `type ImportLiteraturePayload,` 与 `type LiteratureLibrarySummary,`。

在 `Screen` 联合类型中追加 `| "literature"`。

在 `sourceCatalog` 状态之后追加：

```typescript
  const [literatureLibrary, setLiteratureLibrary] =
    useState<LiteratureLibrarySummary | null>(null);
```

在 `StageEntryScreen` 的 `onOpenEntryCard` 回调中，`sources` 分支之后追加：

```typescript
            if (entryKey === "literature") {
              setLiteratureLibrary(
                await client.getLiteratureLibrary(workspaceHome.project.id),
              );
              setScreen("literature");
              return;
            }
```

在 `source-config` 屏幕分支之后插入新分支。左侧栏复用与 `source-config` 分支完全相同的 JSX：

```typescript
  if (screen === "literature" && literatureLibrary !== null) {
    return (
      <main style={shellStyle}>
        <section
          style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
            >
              MEDA DESKTOP
            </div>
            <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
              MedA Desktop Workspace
            </h1>
          </div>

          <nav aria-label="主导航">
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
                <li key={item}>
                  <div
                    style={{
                      borderRadius: "12px",
                      padding: "10px 12px",
                      background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                      color: item === "工作台" ? "#3730a3" : "#334155",
                      fontWeight: item === "工作台" ? 600 : 500,
                    }}
                  >
                    {item}
                  </div>
                </li>
              ))}
            </ul>
          </nav>

          <section>
            <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {projects.map((project) => (
                <li key={project.id}>
                  <div
                    style={{
                      border:
                        project.id === workspaceHome.project.id
                          ? "1px solid #c7d2fe"
                          : "1px solid #e5e7eb",
                      background:
                        project.id === workspaceHome.project.id
                          ? "#f8faff"
                          : "#ffffff",
                      borderRadius: "14px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{project.name}</div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {project.workspace_key}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </section>

        <LiteratureLibraryScreen
          library={literatureLibrary}
          onBackToStageEntry={() => setScreen("stage-entry")}
          onImport={async (payload) => {
            setLiteratureLibrary(
              await client.importLiterature(workspaceHome.project.id, payload),
            );
          }}
          onConfirmUnique={async (recordId) => {
            setLiteratureLibrary(
              await client.confirmLiteratureUnique(
                workspaceHome.project.id,
                recordId,
              ),
            );
          }}
        />
      </main>
    );
  }
```

- [ ] **Step 10: 运行 Desktop 测试确认通过**

Run: `npm --prefix "d:\workspace\MedA" --workspace apps-desktop exec vitest run`
Expected: PASS — 5 passed

- [ ] **Step 11: 提交**

```bash
git add packages/shared-ui/src/LiteratureLibraryScreen.tsx packages/shared-ui/src/index.ts apps/web/src/App.tsx apps/web/src/components/WorkspaceShell.tsx apps/web/src/App.test.tsx apps/desktop/src/App.tsx apps/desktop/tests/app-auth.test.tsx
git commit -m "feat: add shared literature library screen and wire both apps"
```

---

## Task 6: shared-ui 纯函数补测

补 `Wave 6` 遗留：`packages/shared-ui` 当前没有自己的测试，两个纯函数只被双端集成测试间接覆盖（spec 12.7）。

本任务需要先给该包加测试基建 —— 它目前既没有 vitest 依赖也没有 test script。

**Files:**
- Modify: `packages/shared-ui/package.json`
- Create: `packages/shared-ui/vitest.config.ts`
- Modify: `packages/shared-ui/src/SearchSourceConfigScreen.tsx`
- Create: `packages/shared-ui/src/helpers.test.ts`

- [ ] **Step 1: 加测试基建**

把 `packages/shared-ui/package.json` 整个替换为：

```json
{
  "name": "@meda/shared-ui",
  "version": "0.1.0",
  "type": "module",
  "main": "src/index.ts",
  "exports": {
    ".": "./src/index.ts"
  },
  "scripts": {
    "test": "vitest"
  },
  "peerDependencies": {
    "react": "^18.3.1"
  },
  "devDependencies": {
    "@meda/shared-sdk": "0.1.0",
    "@types/react": "^18.3.3",
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
```

创建 `packages/shared-ui/vitest.config.ts`。本任务只测纯函数，不需要 jsdom：

```typescript
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "node",
  },
});
```

- [ ] **Step 2: 导出待测纯函数**

`toggleKey` 与 `parseYear` 当前是 `SearchSourceConfigScreen.tsx` 内的模块私有函数，需要导出才能单测。在 `packages/shared-ui/src/SearchSourceConfigScreen.tsx` 中给两个函数加 `export`：

```typescript
export function toggleKey(current: string[], ordered: string[], key: string): string[] {
  if (current.includes(key)) {
    return current.filter((item) => item !== key);
  }

  return ordered.filter((item) => current.includes(item) || item === key);
}

export function parseYear(raw: string): number | null {
  if (raw.trim() === "") {
    return null;
  }

  const parsed = Number.parseInt(raw, 10);
  return Number.isNaN(parsed) ? null : parsed;
}
```

函数体不变，只加 `export` 关键字。

- [ ] **Step 3: 写失败测试**

创建 `packages/shared-ui/src/helpers.test.ts`：

```typescript
import { describe, expect, it } from "vitest";

import { parseYear, toggleKey } from "./SearchSourceConfigScreen";

const CATALOG_ORDER = ["pubmed", "embase", "cochrane", "wos", "cnki", "wanfang"];

describe("toggleKey", () => {
  it("adds a key following the catalog order", () => {
    expect(toggleKey(["pubmed"], CATALOG_ORDER, "cochrane")).toEqual([
      "pubmed",
      "cochrane",
    ]);
  });

  it("normalizes order when adding a key that sorts earlier", () => {
    expect(toggleKey(["cnki"], CATALOG_ORDER, "pubmed")).toEqual([
      "pubmed",
      "cnki",
    ]);
  });

  it("removes a key that is already selected", () => {
    expect(toggleKey(["pubmed", "embase"], CATALOG_ORDER, "embase")).toEqual([
      "pubmed",
    ]);
  });

  it("preserves relative order when removing", () => {
    expect(
      toggleKey(["pubmed", "cochrane", "cnki"], CATALOG_ORDER, "cochrane"),
    ).toEqual(["pubmed", "cnki"]);
  });

  it("returns a single key when toggling into an empty selection", () => {
    expect(toggleKey([], CATALOG_ORDER, "wos")).toEqual(["wos"]);
  });

  it("returns an empty array when removing the last key", () => {
    expect(toggleKey(["wos"], CATALOG_ORDER, "wos")).toEqual([]);
  });
});

describe("parseYear", () => {
  it("parses a numeric string", () => {
    expect(parseYear("2023")).toBe(2023);
  });

  it("returns null for an empty string", () => {
    expect(parseYear("")).toBeNull();
  });

  it("returns null for whitespace only", () => {
    expect(parseYear("   ")).toBeNull();
  });

  it("returns null for non-numeric text", () => {
    expect(parseYear("in press")).toBeNull();
  });

  it("ignores surrounding whitespace", () => {
    expect(parseYear("  2015  ")).toBe(2015);
  });
});
```

- [ ] **Step 4: 运行测试确认失败**

先装依赖让 workspace 识别新增的 vitest：

Run: `npm install --prefix "d:\workspace\MedA"`

然后：

Run: `npm --prefix "d:\workspace\MedA" --workspace @meda/shared-ui exec vitest run`
Expected: FAIL — 若 Step 2 未执行，报 `toggleKey is not exported`

若 `npm install` 后出现 `Cannot find module @rollup/rollup-win32-x64-msvc`，这是 npm optional dependencies 的已知问题，执行修复：

```bash
npm install --prefix "d:\workspace\MedA" --no-save @rollup/rollup-win32-x64-msvc
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm --prefix "d:\workspace\MedA" --workspace @meda/shared-ui exec vitest run`
Expected: PASS — 11 passed

- [ ] **Step 6: 全链路回归**

依次运行五条命令，全部应为 exit code 0：

```bash
uv run --project "d:\workspace\MedA\apps\agent-core" pytest "d:\workspace\MedA\apps\agent-core\tests\" -q
npm --prefix "d:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run
npm --prefix "d:\workspace\MedA" --workspace @meda/shared-ui exec vitest run
npm --prefix "d:\workspace\MedA" --workspace apps-web exec vitest run
npm --prefix "d:\workspace\MedA" --workspace apps-desktop exec vitest run
```

Expected: 后端 78 passed，shared-sdk 14 passed，shared-ui 11 passed，Web 5 passed，Desktop 5 passed

- [ ] **Step 7: 提交**

```bash
git add packages/shared-ui/package.json packages/shared-ui/vitest.config.ts packages/shared-ui/src/SearchSourceConfigScreen.tsx packages/shared-ui/src/helpers.test.ts package-lock.json
git commit -m "test: add shared-ui pure function unit tests"
```

---

## 验收清单

对照 spec 14 逐项核对：

- [ ] 可从检索阶段入口页进入 `文献条目库`（Task 2 卡片 + Task 5 接线）
- [ ] 可选择来源并粘贴批量导入（Task 2 / 5）
- [ ] 只含 `title` 的条目也能导入（Task 2）
- [ ] 格式损坏的块被跳过，其余正常入库并给出跳过数量（Task 1 / 2）
- [ ] 完全无法解析返回 `422`（Task 2）
- [ ] 可手工录入单条（Task 2）
- [ ] DOI / PMID / 标题加年份三种情况均标记 `duplicate`（Task 3）
- [ ] 标题相同但年份不同不判重（Task 3）
- [ ] 标题相同但一方年份未知不判重（Task 3）
- [ ] 同批次内重复条目能被检出（Task 3）
- [ ] 三条同 DOI 时不形成判重链（Task 3）
- [ ] 空 DOI 与空 PMID 不参与判重（Task 3）
- [ ] 重复条目不被删除（Task 3）
- [ ] 可驳回自动判重，条目变 `confirmed_unique`（Task 3 / 5）
- [ ] `confirmed_unique` 仍可作为后续判重原件（Task 3）
- [ ] 统计正确显示总数 / 唯一数 / 重复数 / 来源分布（Task 2 / 3 / 5）
- [ ] `confirmed_unique` 计入唯一数（Task 2 / 3）
- [ ] 非法输入 `422`、跨机构与未知条目 `404`、无未处理 `500`（Task 2 / 3）
- [ ] 解析器与归一化有独立纯函数单测（Task 1）
- [ ] Web 与 Desktop 共用 shared-ui 同一组件（Task 5）
- [ ] 返回链路可达（Task 5）
- [ ] `toggleKey` 与 `parseYear` 有单测覆盖（Task 6）




