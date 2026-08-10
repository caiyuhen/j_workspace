# MedA Wave 6 数据库来源配置页 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现项目级数据库来源配置页，解除 Wave 5 遗留的 `selected_sources` 硬编码，让 `preview_summary` 由真实配置驱动。

**Architecture:** 新增 `SearchSourceConfig` 项目级单例实体存储启用来源与检索参数；来源目录以后端常量定义；`search_query.py` 改为从配置读取来源，通过 key→label 映射对外暴露 `selected_sources`；Web/Desktop 共用 shared-sdk 新增的三个方法渲染两段式配置页。

**Tech Stack:** FastAPI + SQLModel (SQLite in tests), TypeScript shared-sdk, React 18 (Web + Desktop), pytest, vitest

**Spec:** `docs/superpowers/specs/2026-08-05-meda-search-sources-wave-6-design.md`

---

## File Structure

**新建文件：**

| 路径 | 职责 |
|---|---|
| `apps/agent-core/app/services/source_catalog.py` | 来源目录、检索字段、语种常量；key→label 映射 |
| `apps/agent-core/app/services/search_source.py` | 配置的读取、创建、保存、校验；领域异常 |
| `apps/agent-core/tests/test_search_source_api.py` | 配置 API 与联动测试 |
| `apps/web/src/components/workspace/SearchSourceConfigScreen.tsx` | Web 配置页 |
| `apps/desktop/src/components/SearchSourceConfigScreen.tsx` | Desktop 配置页 |

**修改文件：**

| 路径 | 改动 |
|---|---|
| `apps/agent-core/app/models.py` | 新增 `SearchSourceConfig` 表 |
| `apps/agent-core/app/schemas.py` | 新增目录与配置的请求/响应模型 |
| `apps/agent-core/app/routers/workspace.py` | 新增 3 个端点 |
| `apps/agent-core/app/services/search_query.py` | 改为从配置读来源；新增来源缺失校验 |
| `apps/agent-core/app/services/stage_entry.py` | `sources` 卡片 target 升级为项目级路由 |
| `apps/agent-core/tests/test_search_query_api.py` | 补联动断言 |
| `packages/shared-sdk/src/client.ts` | 新增类型与 3 个方法 |
| `packages/shared-sdk/src/session.test.ts` | 新增 3 个方法测试 |
| `apps/web/src/App.tsx` | 配置状态与回调 |
| `apps/web/src/components/WorkspaceShell.tsx` | 新增 `source-config` 屏幕 |
| `apps/web/src/App.test.tsx` | 配置页流程测试 |
| `apps/desktop/src/App.tsx` | 配置状态、回调、新增屏幕 |
| `apps/desktop/tests/app-auth.test.tsx` | 配置页流程测试 |

**任务依赖顺序：** Task 1 (目录常量) → Task 2 (配置 API) → Task 3 (联动改造) → Task 4 (SDK) → Task 5 (Web) → Task 6 (Desktop)

---

## Task 1: 来源目录常量

来源目录、检索字段、语种以常量定义（spec 5.4 / 5.5）。这一层不依赖数据库，先做掉它，后面所有任务都要用到它的 key→label 映射。

**Files:**
- Create: `apps/agent-core/app/services/source_catalog.py`
- Create: `apps/agent-core/tests/test_search_source_api.py`

- [ ] **Step 1: 写失败测试**

创建 `apps/agent-core/tests/test_search_source_api.py`：

```python
from app.services.source_catalog import (
    LANGUAGE_OPTIONS,
    SEARCH_FIELD_OPTIONS,
    SOURCE_CATALOG,
    source_labels_for_keys,
)


def test_source_catalog_contains_six_medical_databases() -> None:
    keys = [item.key for item in SOURCE_CATALOG]

    assert keys == ["pubmed", "embase", "cochrane", "wos", "cnki", "wanfang"]
    assert all(item.label for item in SOURCE_CATALOG)
    assert all(item.description for item in SOURCE_CATALOG)


def test_source_catalog_marks_full_text_support() -> None:
    support = {item.key: item.supports_full_text for item in SOURCE_CATALOG}

    assert support["pubmed"] is False
    assert support["cochrane"] is True
    assert support["cnki"] is True


def test_search_field_and_language_options_are_defined() -> None:
    assert [item.key for item in SEARCH_FIELD_OPTIONS] == [
        "title",
        "abstract",
        "keyword",
        "mesh",
        "full_text",
    ]
    assert [item.key for item in LANGUAGE_OPTIONS] == ["en", "zh"]


def test_source_labels_for_keys_maps_keys_to_display_labels() -> None:
    assert source_labels_for_keys(["pubmed", "embase"]) == ["PubMed", "Embase"]


def test_source_labels_for_keys_preserves_catalog_order() -> None:
    assert source_labels_for_keys(["cnki", "pubmed"]) == ["PubMed", "中国知网 CNKI"]


def test_source_labels_for_keys_ignores_unknown_keys() -> None:
    assert source_labels_for_keys(["pubmed", "nope"]) == ["PubMed"]
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/test_search_source_api.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.services.source_catalog'`

- [ ] **Step 3: 写最小实现**

创建 `apps/agent-core/app/services/source_catalog.py`：

```python
from pydantic import BaseModel


class SourceCatalogItem(BaseModel):
    key: str
    label: str
    description: str
    supports_full_text: bool


class CatalogOption(BaseModel):
    key: str
    label: str


SOURCE_CATALOG: list[SourceCatalogItem] = [
    SourceCatalogItem(
        key="pubmed",
        label="PubMed",
        description="美国国立医学图书馆生物医学文献库",
        supports_full_text=False,
    ),
    SourceCatalogItem(
        key="embase",
        label="Embase",
        description="爱思唯尔生物医学与药理学文献库",
        supports_full_text=False,
    ),
    SourceCatalogItem(
        key="cochrane",
        label="Cochrane Library",
        description="系统评价与随机对照试验证据库",
        supports_full_text=True,
    ),
    SourceCatalogItem(
        key="wos",
        label="Web of Science",
        description="跨学科引文索引数据库",
        supports_full_text=False,
    ),
    SourceCatalogItem(
        key="cnki",
        label="中国知网 CNKI",
        description="中文学术期刊与学位论文库",
        supports_full_text=True,
    ),
    SourceCatalogItem(
        key="wanfang",
        label="万方数据",
        description="中文医药卫生与科技文献库",
        supports_full_text=True,
    ),
]

SEARCH_FIELD_OPTIONS: list[CatalogOption] = [
    CatalogOption(key="title", label="标题"),
    CatalogOption(key="abstract", label="摘要"),
    CatalogOption(key="keyword", label="关键词"),
    CatalogOption(key="mesh", label="主题词"),
    CatalogOption(key="full_text", label="全文"),
]

LANGUAGE_OPTIONS: list[CatalogOption] = [
    CatalogOption(key="en", label="英文"),
    CatalogOption(key="zh", label="中文"),
]

SOURCE_KEYS = {item.key for item in SOURCE_CATALOG}
SEARCH_FIELD_KEYS = {item.key for item in SEARCH_FIELD_OPTIONS}
LANGUAGE_KEYS = {item.key for item in LANGUAGE_OPTIONS}


def source_labels_for_keys(keys: list[str]) -> list[str]:
    """按目录顺序把来源 key 转成展示 label，未知 key 直接忽略。"""
    selected = set(keys)
    return [item.label for item in SOURCE_CATALOG if item.key in selected]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/test_search_source_api.py -v`
Expected: PASS — 6 passed

- [ ] **Step 5: 提交**

```bash
git add apps/agent-core/app/services/source_catalog.py apps/agent-core/tests/test_search_source_api.py
git commit -m "feat: add search source catalog constants"
```

---

## Task 2: 配置模型与 API

新增 `SearchSourceConfig` 表、schemas、service 与 3 个端点（spec 5.2 / 9 / 10 / 11）。

**Files:**
- Modify: `apps/agent-core/app/models.py` (在 `SearchQueryVersion` 之后插入)
- Modify: `apps/agent-core/app/schemas.py` (文件末尾追加)
- Create: `apps/agent-core/app/services/search_source.py`
- Modify: `apps/agent-core/app/routers/workspace.py`
- Modify: `apps/agent-core/tests/test_search_source_api.py`

- [ ] **Step 1: 写失败测试**

在 `apps/agent-core/tests/test_search_source_api.py` 末尾追加。注意 `_login_and_create_project` 是本文件新增的辅助函数（与 `test_search_query_api.py` 里的同名函数各自独立，不要跨文件导入）：

```python
from fastapi.testclient import TestClient

from app.main import app


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
            "description": "Wave 6 source config",
        },
    )

    return token, project.json()["id"]


def test_source_catalog_endpoint_returns_options() -> None:
    client = TestClient(app)
    token, _ = _login_and_create_project(client)

    response = client.get(
        "/api/workspace/sources/catalog",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200
    assert [item["key"] for item in body["available_sources"]] == [
        "pubmed",
        "embase",
        "cochrane",
        "wos",
        "cnki",
        "wanfang",
    ]
    assert body["available_sources"][0]["label"] == "PubMed"
    assert body["available_sources"][0]["supports_full_text"] is False
    assert [item["key"] for item in body["search_field_options"]] == [
        "title",
        "abstract",
        "keyword",
        "mesh",
        "full_text",
    ]
    assert [item["key"] for item in body["language_options"]] == ["en", "zh"]


def test_source_config_creates_default_on_first_read() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["project"]["id"] == project_id
    assert body["stage_key"] == "search"
    assert body["enabled_source_keys"] == ["pubmed", "embase"]
    assert body["search_fields"] == ["title", "abstract"]
    assert body["year_from"] is None
    assert body["year_to"] is None
    assert body["languages"] == ["en"]
    assert body["config_dirty"] is False
    assert body["impact_summary"]["enabled_count"] == 2
    assert body["validation_messages"] == []

    enabled = {item["key"]: item["enabled"] for item in body["available_sources"]}
    assert enabled["pubmed"] is True
    assert enabled["cochrane"] is False


def test_source_config_saves_and_persists() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
    )

    saved = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed", "cochrane", "cnki"],
            "search_fields": ["title", "abstract", "mesh"],
            "year_from": 2015,
            "year_to": 2025,
            "languages": ["en", "zh"],
        },
    )
    body = saved.json()

    assert saved.status_code == 200
    assert body["enabled_source_keys"] == ["pubmed", "cochrane", "cnki"]
    assert body["year_from"] == 2015
    assert body["impact_summary"]["enabled_count"] == 3

    reread = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert reread["enabled_source_keys"] == ["pubmed", "cochrane", "cnki"]
    assert reread["search_fields"] == ["title", "abstract", "mesh"]
    assert reread["year_to"] == 2025
    assert reread["languages"] == ["en", "zh"]


def test_source_config_rejects_unknown_source_key() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed", "not-a-database"],
            "search_fields": ["title"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )

    assert response.status_code == 422
    assert "not-a-database" in response.json()["detail"]


def test_source_config_rejects_unknown_search_field() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed"],
            "search_fields": ["title", "nope"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )

    assert response.status_code == 422
    assert "nope" in response.json()["detail"]


def test_source_config_rejects_inverted_year_range() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed"],
            "search_fields": ["title"],
            "year_from": 2025,
            "year_to": 2015,
            "languages": ["en"],
        },
    )

    assert response.status_code == 422
    assert "year" in response.json()["detail"].lower()


def test_source_config_rejects_project_from_other_organization() -> None:
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
    other_token = other.json()["token"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_source_config_flags_missing_sources() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": [],
            "search_fields": ["title"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )
    body = response.json()
    codes = [item["code"] for item in body["validation_messages"]]

    assert response.status_code == 200
    assert body["impact_summary"]["enabled_count"] == 0
    assert "MISSING_SOURCE_CONFIG" in codes
    assert next(
        item["level"]
        for item in body["validation_messages"]
        if item["code"] == "MISSING_SOURCE_CONFIG"
    ) == "error"


def test_source_config_warns_on_empty_search_fields() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed"],
            "search_fields": [],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )
    codes = [item["code"] for item in response.json()["validation_messages"]]

    assert response.status_code == 200
    assert "EMPTY_SEARCH_FIELDS" in codes


def test_source_config_notes_narrow_year_range() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed"],
            "search_fields": ["title"],
            "year_from": 2024,
            "year_to": 2025,
            "languages": ["en"],
        },
    )
    codes = [item["code"] for item in response.json()["validation_messages"]]

    assert response.status_code == 200
    assert "NARROW_YEAR_RANGE" in codes
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/test_search_source_api.py -v`
Expected: FAIL — catalog 与 config 端点均返回 404

- [ ] **Step 3: 新增数据模型**

在 `apps/agent-core/app/models.py` 的 `SearchQueryVersion` 类之后、`AuditEvent` 之前插入：

```python
class SearchSourceConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    enabled_sources_json: str
    search_fields_json: str
    year_from: int | None = None
    year_to: int | None = None
    languages_json: str
    config_dirty: bool = False
```

- [ ] **Step 4: 新增 schemas**

在 `apps/agent-core/app/schemas.py` 末尾追加。`SearchValidationMessage` 与 `WorkspaceProjectSummary` 已在文件中定义，直接复用：

```python
class SourceCatalogItemResponse(BaseModel):
    key: str
    label: str
    description: str
    supports_full_text: bool


class CatalogOptionResponse(BaseModel):
    key: str
    label: str


class SearchSourceCatalogResponse(BaseModel):
    available_sources: list[SourceCatalogItemResponse]
    search_field_options: list[CatalogOptionResponse]
    language_options: list[CatalogOptionResponse]


class AvailableSourceResponse(BaseModel):
    key: str
    label: str
    description: str
    supports_full_text: bool
    enabled: bool


class SourceImpactSummary(BaseModel):
    enabled_count: int
    coverage_hint: str
    query_impact_hint: str


class SearchSourceConfigResponse(BaseModel):
    project: WorkspaceProjectSummary
    stage_key: str
    available_sources: list[AvailableSourceResponse]
    enabled_source_keys: list[str]
    search_fields: list[str]
    year_from: int | None
    year_to: int | None
    languages: list[str]
    config_dirty: bool
    impact_summary: SourceImpactSummary
    validation_messages: list[SearchValidationMessage]


class SaveSearchSourceConfigRequest(BaseModel):
    enabled_source_keys: list[str]
    search_fields: list[str]
    year_from: int | None = None
    year_to: int | None = None
    languages: list[str]
```

- [ ] **Step 5: 新增 service**

创建 `apps/agent-core/app/services/search_source.py`：

```python
import json

from sqlmodel import Session, select

from app.models import ResearchProject, SearchSourceConfig
from app.schemas import (
    AvailableSourceResponse,
    CatalogOptionResponse,
    SaveSearchSourceConfigRequest,
    SearchSourceCatalogResponse,
    SearchSourceConfigResponse,
    SearchValidationMessage,
    SourceCatalogItemResponse,
    SourceImpactSummary,
    WorkspaceProjectSummary,
)
from app.services.source_catalog import (
    LANGUAGE_KEYS,
    LANGUAGE_OPTIONS,
    SEARCH_FIELD_KEYS,
    SEARCH_FIELD_OPTIONS,
    SOURCE_CATALOG,
    SOURCE_KEYS,
    source_labels_for_keys,
)

DEFAULT_ENABLED_SOURCES = ["pubmed", "embase"]
DEFAULT_SEARCH_FIELDS = ["title", "abstract"]
DEFAULT_LANGUAGES = ["en"]
NARROW_YEAR_SPAN = 3


class SearchSourceConfigError(Exception):
    """请求中携带了非法的来源 key、字段 key 或年份区间。"""


def build_source_catalog() -> SearchSourceCatalogResponse:
    return SearchSourceCatalogResponse(
        available_sources=[
            SourceCatalogItemResponse(
                key=item.key,
                label=item.label,
                description=item.description,
                supports_full_text=item.supports_full_text,
            )
            for item in SOURCE_CATALOG
        ],
        search_field_options=[
            CatalogOptionResponse(key=item.key, label=item.label)
            for item in SEARCH_FIELD_OPTIONS
        ],
        language_options=[
            CatalogOptionResponse(key=item.key, label=item.label)
            for item in LANGUAGE_OPTIONS
        ],
    )


def _validate_payload(payload: SaveSearchSourceConfigRequest) -> None:
    unknown_sources = [key for key in payload.enabled_source_keys if key not in SOURCE_KEYS]
    if unknown_sources:
        raise SearchSourceConfigError(
            f"unknown source keys: {', '.join(unknown_sources)}"
        )

    unknown_fields = [key for key in payload.search_fields if key not in SEARCH_FIELD_KEYS]
    if unknown_fields:
        raise SearchSourceConfigError(
            f"unknown search fields: {', '.join(unknown_fields)}"
        )

    unknown_languages = [key for key in payload.languages if key not in LANGUAGE_KEYS]
    if unknown_languages:
        raise SearchSourceConfigError(
            f"unknown languages: {', '.join(unknown_languages)}"
        )

    if (
        payload.year_from is not None
        and payload.year_to is not None
        and payload.year_from > payload.year_to
    ):
        raise SearchSourceConfigError(
            f"year_from {payload.year_from} must not exceed year_to {payload.year_to}"
        )


def build_source_validation_messages(
    enabled_source_keys: list[str],
    search_fields: list[str],
    year_from: int | None,
    year_to: int | None,
) -> list[SearchValidationMessage]:
    messages: list[SearchValidationMessage] = []

    if not enabled_source_keys:
        messages.append(
            SearchValidationMessage(
                level="error",
                code="MISSING_SOURCE_CONFIG",
                message="请先在数据库来源页启用至少一个来源。",
            )
        )

    if not search_fields:
        messages.append(
            SearchValidationMessage(
                level="warning",
                code="EMPTY_SEARCH_FIELDS",
                message="未选择任何检索字段，检索范围可能过窄。",
            )
        )

    if (
        year_from is not None
        and year_to is not None
        and year_to - year_from < NARROW_YEAR_SPAN
    ):
        messages.append(
            SearchValidationMessage(
                level="info",
                code="NARROW_YEAR_RANGE",
                message="当前时间窗较窄，可能遗漏早期关键研究。",
            )
        )

    return messages


def get_or_create_source_config(
    session: Session,
    project: ResearchProject,
) -> SearchSourceConfig:
    project_id = project.id or 0
    config = session.exec(
        select(SearchSourceConfig).where(SearchSourceConfig.project_id == project_id)
    ).first()

    if config is None:
        config = SearchSourceConfig(
            project_id=project_id,
            enabled_sources_json=json.dumps(DEFAULT_ENABLED_SOURCES, ensure_ascii=False),
            search_fields_json=json.dumps(DEFAULT_SEARCH_FIELDS, ensure_ascii=False),
            languages_json=json.dumps(DEFAULT_LANGUAGES, ensure_ascii=False),
        )
        session.add(config)
        session.commit()
        session.refresh(config)

    return config


def enabled_source_keys_for_project(
    session: Session,
    project: ResearchProject,
) -> list[str]:
    """供 search_query 服务读取项目当前启用的来源 key。"""
    config = get_or_create_source_config(session, project)
    return json.loads(config.enabled_sources_json)


def _build_response(
    project: ResearchProject,
    config: SearchSourceConfig,
) -> SearchSourceConfigResponse:
    enabled_keys = json.loads(config.enabled_sources_json)
    search_fields = json.loads(config.search_fields_json)
    languages = json.loads(config.languages_json)
    labels = source_labels_for_keys(enabled_keys)

    coverage_hint = (
        f"已启用 {len(enabled_keys)} 个数据库：{', '.join(labels)}"
        if labels
        else "尚未启用任何数据库"
    )
    query_impact_hint = (
        f"当前检索式的预览将基于这 {len(enabled_keys)} 个库重新计算"
        if labels
        else "检索式预览当前不可用，请先启用来源"
    )

    return SearchSourceConfigResponse(
        project=WorkspaceProjectSummary(
            id=project.id or 0,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="检索",
            updated_at_label="刚刚更新",
        ),
        stage_key="search",
        available_sources=[
            AvailableSourceResponse(
                key=item.key,
                label=item.label,
                description=item.description,
                supports_full_text=item.supports_full_text,
                enabled=item.key in set(enabled_keys),
            )
            for item in SOURCE_CATALOG
        ],
        enabled_source_keys=enabled_keys,
        search_fields=search_fields,
        year_from=config.year_from,
        year_to=config.year_to,
        languages=languages,
        config_dirty=config.config_dirty,
        impact_summary=SourceImpactSummary(
            enabled_count=len(enabled_keys),
            coverage_hint=coverage_hint,
            query_impact_hint=query_impact_hint,
        ),
        validation_messages=build_source_validation_messages(
            enabled_keys, search_fields, config.year_from, config.year_to
        ),
    )


def get_source_config(
    session: Session,
    project: ResearchProject,
) -> SearchSourceConfigResponse:
    config = get_or_create_source_config(session, project)
    return _build_response(project, config)


def save_source_config(
    session: Session,
    project: ResearchProject,
    payload: SaveSearchSourceConfigRequest,
) -> SearchSourceConfigResponse:
    _validate_payload(payload)

    config = get_or_create_source_config(session, project)
    config.enabled_sources_json = json.dumps(
        payload.enabled_source_keys, ensure_ascii=False
    )
    config.search_fields_json = json.dumps(payload.search_fields, ensure_ascii=False)
    config.languages_json = json.dumps(payload.languages, ensure_ascii=False)
    config.year_from = payload.year_from
    config.year_to = payload.year_to
    config.config_dirty = False
    session.add(config)
    session.commit()
    session.refresh(config)

    return _build_response(project, config)
```

- [ ] **Step 6: 新增端点**

在 `apps/agent-core/app/routers/workspace.py` 的 imports 中追加：

```python
from app.schemas import (
    SaveSearchSourceConfigRequest,
    SearchSourceCatalogResponse,
    SearchSourceConfigResponse,
)
from app.services.search_source import (
    SearchSourceConfigError,
    build_source_catalog,
    get_source_config,
    save_source_config,
)
```

在文件末尾追加三个端点。注意 catalog 路由必须放在 `/projects/{project_id}/...` 之前不会冲突，因为路径前缀不同：

```python
@router.get("/sources/catalog", response_model=SearchSourceCatalogResponse)
def get_search_source_catalog(
    context: SessionContext = Depends(get_current_session),
) -> SearchSourceCatalogResponse:
    return build_source_catalog()


@router.get(
    "/projects/{project_id}/stages/search/sources",
    response_model=SearchSourceConfigResponse,
)
def get_search_source_config(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchSourceConfigResponse:
    project = _load_project_or_404(session, project_id, context)

    return get_source_config(session, project)


@router.put(
    "/projects/{project_id}/stages/search/sources",
    response_model=SearchSourceConfigResponse,
)
def put_search_source_config(
    project_id: int,
    payload: SaveSearchSourceConfigRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchSourceConfigResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        return save_source_config(session, project, payload)
    except SearchSourceConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
```

- [ ] **Step 7: 运行测试确认通过**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/test_search_source_api.py -v`
Expected: PASS — 16 passed

- [ ] **Step 8: 跑全量后端回归**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/ -q`
Expected: PASS — 36 passed（Wave 5 的 20 个 + 本任务 16 个）

- [ ] **Step 9: 提交**

```bash
git add apps/agent-core/app/models.py apps/agent-core/app/schemas.py apps/agent-core/app/services/search_source.py apps/agent-core/app/routers/workspace.py apps/agent-core/tests/test_search_source_api.py
git commit -m "feat: add project-level search source config API"
```

---

## Task 3: 联动改造 — 解除硬编码

**这是本波的核心价值点。** 让 `query-builder` 的 `selected_sources` 与 `preview_summary` 由真实配置驱动（spec 6.1 / 6.2 / 6.3 / 6.4 / 12.2）。

改造要点：
- `selected_sources` 从 `SearchSourceConfig` 读，不再从 `SearchQueryDraft` 读
- key→label 转换在此完成
- 无来源时 preview 降级为 `unavailable` + `MISSING_SOURCE_CONFIG`
- **版本快照不受影响** —— 继续从 `SearchQueryVersion` 读自己的来源

**Files:**
- Modify: `apps/agent-core/app/services/search_query.py`
- Modify: `apps/agent-core/app/services/stage_entry.py`
- Modify: `apps/agent-core/tests/test_search_query_api.py`

- [ ] **Step 1: 写失败测试**

在 `apps/agent-core/tests/test_search_query_api.py` 末尾追加：

```python
def test_query_builder_reads_sources_from_project_config() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed", "cochrane", "cnki"],
            "search_fields": ["title", "abstract"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert body["selected_sources"] == ["PubMed", "Cochrane Library", "中国知网 CNKI"]
    assert body["preview_summary"]["status"] == "available"
    assert body["preview_summary"]["database_scope_summary"] == (
        "PubMed, Cochrane Library, 中国知网 CNKI"
    )


def test_query_builder_preview_degrades_when_no_sources_enabled() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": [],
            "search_fields": ["title"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    codes = [item["code"] for item in body["validation_messages"]]

    assert body["selected_sources"] == []
    assert body["preview_summary"]["status"] == "unavailable"
    assert body["preview_summary"]["database_scope_summary"] == "未选择数据库"
    assert "MISSING_SOURCE_CONFIG" in codes
    assert next(
        item["level"]
        for item in body["validation_messages"]
        if item["code"] == "MISSING_SOURCE_CONFIG"
    ) == "error"


def test_version_snapshot_keeps_its_own_sources_after_config_change() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    initial = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/save-as-version",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query_id": initial["query_id"],
            "query_name": initial["query_name"],
            "selected_sources": initial["selected_sources"],
            "grouped_terms": initial["grouped_terms"],
            "expression_blocks": initial["expression_blocks"],
        },
    )

    client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["wanfang"],
            "search_fields": ["title"],
            "year_from": None,
            "year_to": None,
            "languages": ["zh"],
        },
    )

    snapshot = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder"
        f"?query_id={initial['query_id']}&version=v1",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    current = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert snapshot["query_mode"] == "snapshot"
    assert snapshot["selected_sources"] == ["PubMed", "Embase"]
    assert current["selected_sources"] == ["万方数据"]


def test_stage_entry_points_sources_card_to_project_deep_page() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    sources_card = next(
        card for card in body["entry_cards"] if card["key"] == "sources"
    )

    assert sources_card["target"] == (
        f"/workspace/projects/{project_id}/stages/search/sources"
    )
```

- [ ] **Step 2: 运行测试确认失败**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/test_search_query_api.py -v`
Expected: FAIL — `selected_sources` 仍是硬编码的 `["PubMed", "Embase"]`；`sources` 卡片 target 仍是旧格式

- [ ] **Step 3: 改造 search_query.py 的 imports**

在 `apps/agent-core/app/services/search_query.py` 顶部 imports 追加：

```python
from app.services.search_source import enabled_source_keys_for_project
from app.services.source_catalog import source_labels_for_keys
```

`SearchValidationMessage` 已在该文件的 `app.schemas` import 中，无需重复添加。

- [ ] **Step 4: 改造 _build_preview_summary**

把 `_build_preview_summary` 整个函数替换为：

```python
def _build_preview_summary(
    selected_source_labels: list[str],
    source: str,
) -> SearchPreviewSummary:
    return SearchPreviewSummary(
        status="available" if selected_source_labels else "unavailable",
        coverage_hint="主题组覆盖 2 / 5",
        database_scope_summary=(
            ", ".join(selected_source_labels) if selected_source_labels else "未选择数据库"
        ),
        estimated_hit_band="80-150" if selected_source_labels else "不可用",
        last_generated_from=source,
    )
```

- [ ] **Step 5: 改造 get_or_create_search_query_editor**

在 `get_or_create_search_query_editor` 函数内，把这一段：

```python
    selected_sources = json.loads(draft.selected_sources_json)
    validation_messages = _build_validation_messages(grouped_terms, expression_blocks)
```

替换为：

```python
    # Wave 6: 来源不再从 draft 读，改为项目级配置驱动
    enabled_keys = enabled_source_keys_for_project(session, project)
    selected_sources = source_labels_for_keys(enabled_keys)
    validation_messages = _build_validation_messages(grouped_terms, expression_blocks)
    if not enabled_keys:
        validation_messages.append(
            SearchValidationMessage(
                level="error",
                code="MISSING_SOURCE_CONFIG",
                message="请先在数据库来源页启用至少一个来源。",
            )
        )
```

这里直接构造消息而不复用 `build_source_validation_messages`：后者会同时检查字段与年份，而本函数只关心来源缺失这一条（字段与年份的校验属于配置页自身的职责）。因此 Step 3 的 imports 中只需 `enabled_source_keys_for_project`，不需要 `build_source_validation_messages`。

- [ ] **Step 6: 运行测试确认通过**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/test_search_query_api.py -v`
Expected: 前三个新测试 PASS，`test_stage_entry_points_sources_card_to_project_deep_page` 仍 FAIL

`get_search_query_snapshot` 无需改动——版本快照的 `selected_sources_json` 在 Wave 5 保存时已存 label，继续从版本记录读取即可，这正是 spec 6.3 要求的"不随配置变更回溯改写"。

- [ ] **Step 7: 升级 stage_entry 的 sources 卡片**

在 `apps/agent-core/app/services/stage_entry.py` 的 `build_stage_entry` 中，找到 `if stage_key == "search":` 分支内的 `entry_cards` 列表推导（约 380-391 行）。当前它只改写 `query-builder` 一个卡片，把整个列表推导替换为：

```python
        project_deep_page_keys = {"query-builder", "sources"}
        entry_cards = [
            card.model_copy(
                update={
                    "target": (
                        f"/workspace/projects/{project_id}/stages/search/{card.key}"
                        if card.key in project_deep_page_keys
                        else card.target
                    )
                }
            )
            for card in config["entry_cards"]
        ]
```

注意：`config["entry_cards"]` 里存的是 `StageEntryCardSummary` 实例（不是 dict），所以用 `card.key` / `card.target` 属性访问与 `model_copy`。`primary_action` 的改写逻辑保持不变，不要动它。

- [ ] **Step 8: 运行测试确认通过**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/test_search_query_api.py -v`
Expected: PASS — 13 passed

- [ ] **Step 9: 跑全量后端回归**

Run: `uv run --project "apps/agent-core" pytest apps/agent-core/tests/ -q`
Expected: PASS — 40 passed

- [ ] **Step 10: 提交**

```bash
git add apps/agent-core/app/services/search_query.py apps/agent-core/app/services/stage_entry.py apps/agent-core/tests/test_search_query_api.py
git commit -m "feat: drive query builder preview from real source config"
```

---

## Task 4: Shared SDK

新增 3 个方法与配套类型（spec 12.3）。

**Files:**
- Modify: `packages/shared-sdk/src/client.ts`
- Modify: `packages/shared-sdk/src/session.test.ts`

- [ ] **Step 1: 写失败测试**

在 `packages/shared-sdk/src/session.test.ts` 末尾追加：

```typescript
test("client fetches the source catalog", async () => {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    json: async () => ({
      available_sources: [
        {
          key: "pubmed",
          label: "PubMed",
          description: "美国国立医学图书馆生物医学文献库",
          supports_full_text: false,
        },
      ],
      search_field_options: [{ key: "title", label: "标题" }],
      language_options: [{ key: "en", label: "英文" }],
    }),
  }));
  vi.stubGlobal("fetch", fetchMock);

  const client = createClient("http://localhost:8000");
  const catalog = await client.getSourceCatalog();

  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/api/workspace/sources/catalog",
    expect.objectContaining({ headers: expect.any(Object) }),
  );
  expect(catalog.available_sources[0].key).toBe("pubmed");
  expect(catalog.search_field_options[0].label).toBe("标题");
});

test("client fetches the search source config", async () => {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    json: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      available_sources: [],
      enabled_source_keys: ["pubmed", "embase"],
      search_fields: ["title", "abstract"],
      year_from: null,
      year_to: null,
      languages: ["en"],
      config_dirty: false,
      impact_summary: {
        enabled_count: 2,
        coverage_hint: "已启用 2 个数据库：PubMed, Embase",
        query_impact_hint: "当前检索式的预览将基于这 2 个库重新计算",
      },
      validation_messages: [],
    }),
  }));
  vi.stubGlobal("fetch", fetchMock);

  const client = createClient("http://localhost:8000");
  const config = await client.getSearchSourceConfig(1);

  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/api/workspace/projects/1/stages/search/sources",
    expect.objectContaining({ headers: expect.any(Object) }),
  );
  expect(config.enabled_source_keys).toEqual(["pubmed", "embase"]);
  expect(config.impact_summary.enabled_count).toBe(2);
});

test("client saves the search source config", async () => {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    json: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      available_sources: [],
      enabled_source_keys: ["pubmed", "cochrane"],
      search_fields: ["title"],
      year_from: 2015,
      year_to: 2025,
      languages: ["en"],
      config_dirty: false,
      impact_summary: {
        enabled_count: 2,
        coverage_hint: "已启用 2 个数据库：PubMed, Cochrane Library",
        query_impact_hint: "当前检索式的预览将基于这 2 个库重新计算",
      },
      validation_messages: [],
    }),
  }));
  vi.stubGlobal("fetch", fetchMock);

  const client = createClient("http://localhost:8000");
  const config = await client.saveSearchSourceConfig(1, {
    enabled_source_keys: ["pubmed", "cochrane"],
    search_fields: ["title"],
    year_from: 2015,
    year_to: 2025,
    languages: ["en"],
  });

  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/api/workspace/projects/1/stages/search/sources",
    expect.objectContaining({ method: "PUT" }),
  );
  expect(config.enabled_source_keys).toEqual(["pubmed", "cochrane"]);
  expect(config.year_from).toBe(2015);
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix "." --workspace @meda/shared-sdk exec vitest run src/session.test.ts`
Expected: FAIL — `client.getSourceCatalog is not a function` 等三处

- [ ] **Step 3: 新增类型**

在 `packages/shared-sdk/src/client.ts` 的 `DeriveSearchQueryDraftPayload` 定义之后追加：

```typescript
export type SourceCatalogItem = {
  key: string;
  label: string;
  description: string;
  supports_full_text: boolean;
};

export type CatalogOption = {
  key: string;
  label: string;
};

export type SearchSourceCatalog = {
  available_sources: SourceCatalogItem[];
  search_field_options: CatalogOption[];
  language_options: CatalogOption[];
};

export type AvailableSource = SourceCatalogItem & {
  enabled: boolean;
};

export type SourceImpactSummary = {
  enabled_count: number;
  coverage_hint: string;
  query_impact_hint: string;
};

export type SearchSourceConfigSummary = {
  project: WorkspaceProjectSummary;
  stage_key: string;
  available_sources: AvailableSource[];
  enabled_source_keys: string[];
  search_fields: string[];
  year_from: number | null;
  year_to: number | null;
  languages: string[];
  config_dirty: boolean;
  impact_summary: SourceImpactSummary;
  validation_messages: SearchValidationMessage[];
};

export type SaveSearchSourceConfigPayload = {
  enabled_source_keys: string[];
  search_fields: string[];
  year_from: number | null;
  year_to: number | null;
  languages: string[];
};
```

- [ ] **Step 4: 新增方法**

在 `createClient` 返回对象内，`deriveSearchQueryDraft` 之后追加：

```typescript
    async getSourceCatalog(): Promise<SearchSourceCatalog> {
      const response = await fetch(
        `${baseUrl}/api/workspace/sources/catalog`,
        {
          headers: buildHeaders(),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "source catalog failed");
      }

      return data;
    },

    async getSearchSourceConfig(
      projectId: number,
    ): Promise<SearchSourceConfigSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/sources`,
        {
          headers: buildHeaders(),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "source config failed");
      }

      return data;
    },

    async saveSearchSourceConfig(
      projectId: number,
      payload: SaveSearchSourceConfigPayload,
    ): Promise<SearchSourceConfigSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/sources`,
        {
          method: "PUT",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "source config save failed");
      }

      return data;
    },
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm --prefix "." --workspace @meda/shared-sdk exec vitest run src/session.test.ts`
Expected: PASS — 10 passed

- [ ] **Step 6: 提交**

```bash
git add packages/shared-sdk/src/client.ts packages/shared-sdk/src/session.test.ts
git commit -m "feat: add source config methods to shared sdk"
```

---

## Task 5: Web 配置页

两段式配置页 + 右侧影响提示（spec 7 / 12.4）。

**Files:**
- Create: `apps/web/src/components/workspace/SearchSourceConfigScreen.tsx`
- Modify: `apps/web/src/App.tsx`
- Modify: `apps/web/src/components/WorkspaceShell.tsx`
- Modify: `apps/web/src/App.test.tsx`

- [ ] **Step 1: 写失败测试**

在 `apps/web/src/App.test.tsx` 中，先在现有 mock 的 `createClient` 返回对象里追加两个方法。找到 `deriveSearchQueryDraft,` 这一行，在其后插入：

```typescript
    getSearchSourceConfig,
    saveSearchSourceConfig,
```

然后在 `const deriveSearchQueryDraft = vi.fn();` 之后追加 mock 定义：

```typescript
const sourceConfigResponse = {
  project: {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
    current_stage: "检索",
    updated_at_label: "刚刚更新",
  },
  stage_key: "search",
  available_sources: [
    {
      key: "pubmed",
      label: "PubMed",
      description: "美国国立医学图书馆生物医学文献库",
      supports_full_text: false,
      enabled: true,
    },
    {
      key: "cochrane",
      label: "Cochrane Library",
      description: "系统评价与随机对照试验证据库",
      supports_full_text: true,
      enabled: false,
    },
  ],
  enabled_source_keys: ["pubmed"],
  search_fields: ["title", "abstract"],
  year_from: null,
  year_to: null,
  languages: ["en"],
  config_dirty: false,
  impact_summary: {
    enabled_count: 1,
    coverage_hint: "已启用 1 个数据库：PubMed",
    query_impact_hint: "当前检索式的预览将基于这 1 个库重新计算",
  },
  validation_messages: [],
};

const getSearchSourceConfig = vi.fn(async () => sourceConfigResponse);

const saveSearchSourceConfig = vi.fn(async () => ({
  ...sourceConfigResponse,
  available_sources: [
    { ...sourceConfigResponse.available_sources[0], enabled: true },
    { ...sourceConfigResponse.available_sources[1], enabled: true },
  ],
  enabled_source_keys: ["pubmed", "cochrane"],
  impact_summary: {
    enabled_count: 2,
    coverage_hint: "已启用 2 个数据库：PubMed, Cochrane Library",
    query_impact_hint: "当前检索式的预览将基于这 2 个库重新计算",
  },
}));
```

同时把 `getStageEntry` mock 的 `entry_cards` 补上 `sources` 卡片。找到 `entry_cards: [` 数组，在 `query-builder` 卡片之后追加：

```typescript
    {
      key: "sources",
      title: "数据库来源",
      description: "配置检索覆盖的数据库范围",
      status: "ready",
      target: "/workspace/projects/1/stages/search/sources",
    },
```

最后在文件末尾追加测试：

```typescript
test("web workspace opens source config and saves an extra database", async () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("机构标识"), {
    target: { value: "demo-hospital" },
  });
  fireEvent.change(screen.getByLabelText("用户编号"), {
    target: { value: "u-001" },
  });
  fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "数据库来源" }));

  expect(getSearchSourceConfig).toHaveBeenCalledWith(1);
  expect(
    await screen.findByRole("heading", { name: "数据库来源" }),
  ).toBeInTheDocument();
  expect(screen.getByText("已启用 1 个数据库：PubMed")).toBeInTheDocument();
  expect(screen.getByLabelText("启用 Cochrane Library")).not.toBeChecked();

  fireEvent.click(screen.getByLabelText("启用 Cochrane Library"));
  fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

  expect(saveSearchSourceConfig).toHaveBeenCalledWith(1, {
    enabled_source_keys: ["pubmed", "cochrane"],
    search_fields: ["title", "abstract"],
    year_from: null,
    year_to: null,
    languages: ["en"],
  });
  expect(
    await screen.findByText("已启用 2 个数据库：PubMed, Cochrane Library"),
  ).toBeInTheDocument();
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix "." --workspace apps-web exec vitest run`
Expected: FAIL — 找不到 `数据库来源` 按钮（阶段入口页尚未把该卡片接到配置页）

- [ ] **Step 3: 创建配置页组件**

创建 `apps/web/src/components/workspace/SearchSourceConfigScreen.tsx`：

```typescript
import { useEffect, useState } from "react";

import type { SearchSourceConfigSummary } from "@meda/shared-sdk";

type SearchSourceConfigScreenProps = {
  config: SearchSourceConfigSummary;
  onBackToStageEntry: () => void;
  onSave: (payload: {
    enabled_source_keys: string[];
    search_fields: string[];
    year_from: number | null;
    year_to: number | null;
    languages: string[];
  }) => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

export function SearchSourceConfigScreen({
  config,
  onBackToStageEntry,
  onSave,
}: SearchSourceConfigScreenProps) {
  const [enabledKeys, setEnabledKeys] = useState<string[]>(
    config.enabled_source_keys,
  );

  useEffect(() => {
    setEnabledKeys(config.enabled_source_keys);
  }, [config.enabled_source_keys]);

  const toggleSource = (key: string) => {
    setEnabledKeys((current) =>
      current.includes(key)
        ? current.filter((item) => item !== key)
        : config.available_sources
            .map((item) => item.key)
            .filter((item) => current.includes(item) || item === key),
    );
  };

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
          <h2 style={{ margin: "16px 0 8px", fontSize: "30px" }}>数据库来源</h2>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>
            {config.project.name}
          </div>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>来源清单</h3>
          {config.available_sources.map((source) => (
            <label
              key={source.key}
              style={{
                display: "flex",
                gap: "12px",
                alignItems: "flex-start",
                marginBottom: "12px",
                border: "1px solid #e5e7eb",
                borderRadius: "12px",
                padding: "12px 14px",
              }}
            >
              <input
                type="checkbox"
                aria-label={`启用 ${source.label}`}
                checked={enabledKeys.includes(source.key)}
                onChange={() => toggleSource(source.key)}
              />
              <span>
                <span style={{ fontWeight: 600 }}>{source.label}</span>
                <span
                  style={{
                    display: "block",
                    marginTop: "4px",
                    color: "#6b7280",
                    fontSize: "13px",
                  }}
                >
                  {source.description}
                  {source.supports_full_text ? " · 支持全文" : ""}
                </span>
              </span>
            </label>
          ))}
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>检索参数</h3>
          <div>检索字段：{config.search_fields.join(", ")}</div>
          <div style={{ marginTop: "8px" }}>
            年份区间：{config.year_from ?? "不限"} — {config.year_to ?? "不限"}
          </div>
          <div style={{ marginTop: "8px" }}>
            语种：{config.languages.join(", ")}
          </div>
        </section>

        <section style={panelStyle}>
          <button
            style={{
              border: "none",
              background: "#111827",
              color: "#f9fafb",
              borderRadius: "999px",
              padding: "10px 16px",
              cursor: "pointer",
            }}
            onClick={() =>
              onSave({
                enabled_source_keys: enabledKeys,
                search_fields: config.search_fields,
                year_from: config.year_from,
                year_to: config.year_to,
                languages: config.languages,
              })
            }
          >
            保存配置
          </button>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>配置影响</h3>
          <div>{config.impact_summary.coverage_hint}</div>
          <div style={{ marginTop: "8px", color: "#4b5563" }}>
            {config.impact_summary.query_impact_hint}
          </div>
          {config.validation_messages.map((message) => (
            <div
              key={message.code}
              style={{
                marginTop: "12px",
                color: message.level === "error" ? "#b91c1c" : "#6b7280",
              }}
            >
              {message.message}
            </div>
          ))}
        </section>
      </aside>
    </>
  );
}
```

- [ ] **Step 4: 接入 App.tsx**

在 `apps/web/src/App.tsx` 的类型 import 中追加 `type SearchSourceConfigSummary,`。

在 `const [searchQueryEditor, setSearchQueryEditor] = ...` 之后追加状态：

```typescript
  const [sourceConfig, setSourceConfig] =
    useState<SearchSourceConfigSummary | null>(null);
```

在 `handleLogin` 内 `setSearchQueryEditor(null);` 之后追加 `setSourceConfig(null);`。

在 `handleDeriveSearchQueryDraft` 之后追加两个回调：

```typescript
  const handleOpenSourceConfig = async (projectId: number) => {
    const nextConfig = await client.getSearchSourceConfig(projectId);
    setSourceConfig(nextConfig);
  };

  const handleSaveSourceConfig = async (
    projectId: number,
    payload: {
      enabled_source_keys: string[];
      search_fields: string[];
      year_from: number | null;
      year_to: number | null;
      languages: string[];
    },
  ) => {
    const nextConfig = await client.saveSearchSourceConfig(projectId, payload);
    setSourceConfig(nextConfig);
  };
```

在 `<WorkspaceShell ... />` 的 props 中追加：

```typescript
      sourceConfig={sourceConfig}
      onOpenSourceConfig={handleOpenSourceConfig}
      onSaveSourceConfig={handleSaveSourceConfig}
```

- [ ] **Step 5: 接入 WorkspaceShell.tsx**

在 `apps/web/src/components/WorkspaceShell.tsx` 的 import 中追加：

```typescript
import { SearchSourceConfigScreen } from "./workspace/SearchSourceConfigScreen";
```

在类型 import 中追加 `SearchSourceConfigSummary,`。

在 `WorkspaceShellProps` 中追加三个 prop：

```typescript
  sourceConfig: SearchSourceConfigSummary | null;
  onOpenSourceConfig: (projectId: number) => Promise<void>;
  onSaveSourceConfig: (
    projectId: number,
    payload: {
      enabled_source_keys: string[];
      search_fields: string[];
      year_from: number | null;
      year_to: number | null;
      languages: string[];
    },
  ) => Promise<void>;
```

在 `Screen` 联合类型中追加 `| "source-config"`。

在函数签名的解构参数中追加 `sourceConfig, onOpenSourceConfig, onSaveSourceConfig,`。

在 `query-builder` 屏幕分支之后、`stage-entry` 分支之前插入新分支：

```typescript
  if (screen === "source-config" && sourceConfig !== null) {
    return (
      <main style={shellStyle}>
        <LeftRail projects={projects} workspaceHome={workspaceHome} />
        <SearchSourceConfigScreen
          config={sourceConfig}
          onBackToStageEntry={() => setScreen("stage-entry")}
          onSave={(payload) =>
            onSaveSourceConfig(workspaceHome.project.id, payload)
          }
        />
      </main>
    );
  }
```

在 `stage-entry` 分支的 `onOpenEntryCard` 回调中，把 `query-builder` 判断扩展为同时处理 `sources`：

```typescript
          onOpenEntryCard={async (entryKey) => {
            if (entryKey === "query-builder") {
              await onOpenSearchQueryBuilder(workspaceHome.project.id);
              setScreen("query-builder");
              return;
            }

            if (entryKey === "sources") {
              await onOpenSourceConfig(workspaceHome.project.id);
              setScreen("source-config");
              return;
            }

            setScreen("stage-subentry");
          }}
```

- [ ] **Step 6: 运行测试确认通过**

Run: `npm --prefix "." --workspace apps-web exec vitest run`
Expected: PASS — 3 passed

- [ ] **Step 7: 提交**

```bash
git add apps/web/src/components/workspace/SearchSourceConfigScreen.tsx apps/web/src/App.tsx apps/web/src/components/WorkspaceShell.tsx apps/web/src/App.test.tsx
git commit -m "feat: add web source config screen"
```

---

## Task 6: Desktop 配置页

与 Web 同构（spec 8.4 / 12.4）。Desktop 没有独立 shell 组件，屏幕分支直接写在 `App.tsx` 内，沿用 Wave 5 的既有做法。

**Files:**
- Create: `apps/desktop/src/components/SearchSourceConfigScreen.tsx`
- Modify: `apps/desktop/src/App.tsx`
- Modify: `apps/desktop/tests/app-auth.test.tsx`

- [ ] **Step 1: 写失败测试**

在 `apps/desktop/tests/app-auth.test.tsx` 的 mock `createClient` 返回对象中追加：

```typescript
    getSearchSourceConfig,
    saveSearchSourceConfig,
```

在 mock 定义区追加（与 Web 相同的响应结构，Desktop mock 是独立的，不跨文件复用）：

```typescript
const sourceConfigResponse = {
  project: {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
    current_stage: "检索",
    updated_at_label: "刚刚更新",
  },
  stage_key: "search",
  available_sources: [
    {
      key: "pubmed",
      label: "PubMed",
      description: "美国国立医学图书馆生物医学文献库",
      supports_full_text: false,
      enabled: true,
    },
    {
      key: "cochrane",
      label: "Cochrane Library",
      description: "系统评价与随机对照试验证据库",
      supports_full_text: true,
      enabled: false,
    },
  ],
  enabled_source_keys: ["pubmed"],
  search_fields: ["title", "abstract"],
  year_from: null,
  year_to: null,
  languages: ["en"],
  config_dirty: false,
  impact_summary: {
    enabled_count: 1,
    coverage_hint: "已启用 1 个数据库：PubMed",
    query_impact_hint: "当前检索式的预览将基于这 1 个库重新计算",
  },
  validation_messages: [],
};

const getSearchSourceConfig = vi.fn(async () => sourceConfigResponse);

const saveSearchSourceConfig = vi.fn(async () => ({
  ...sourceConfigResponse,
  enabled_source_keys: ["pubmed", "cochrane"],
  impact_summary: {
    enabled_count: 2,
    coverage_hint: "已启用 2 个数据库：PubMed, Cochrane Library",
    query_impact_hint: "当前检索式的预览将基于这 2 个库重新计算",
  },
}));
```

在 `getStageEntry` mock 的 `entry_cards` 中追加 `sources` 卡片：

```typescript
        {
          key: "sources",
          title: "数据库来源",
          description: "配置检索覆盖的数据库范围",
          status: "ready",
          target: "/workspace/projects/1/stages/search/sources",
        },
```

在文件末尾追加测试：

```typescript
test("desktop workspace opens source config and saves an extra database", async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "数据库来源" }));

  expect(getSearchSourceConfig).toHaveBeenCalledWith(1);
  expect(
    await screen.findByRole("heading", { name: "数据库来源" }),
  ).toBeInTheDocument();
  expect(screen.getByText("已启用 1 个数据库：PubMed")).toBeInTheDocument();

  fireEvent.click(screen.getByLabelText("启用 Cochrane Library"));
  fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

  expect(saveSearchSourceConfig).toHaveBeenCalledWith(1, {
    enabled_source_keys: ["pubmed", "cochrane"],
    search_fields: ["title", "abstract"],
    year_from: null,
    year_to: null,
    languages: ["en"],
  });
  expect(
    await screen.findByText("已启用 2 个数据库：PubMed, Cochrane Library"),
  ).toBeInTheDocument();
});
```

- [ ] **Step 2: 运行测试确认失败**

Run: `npm --prefix "." --workspace apps-desktop exec vitest run`
Expected: FAIL — 找不到 `数据库来源` 按钮

- [ ] **Step 3: 创建配置页组件**

创建 `apps/desktop/src/components/SearchSourceConfigScreen.tsx`。内容与 Web 版完全一致，仅 import 路径的相对层级不同（Desktop 组件目录是 `src/components/`，不是 `src/components/workspace/`）：

```typescript
import { useEffect, useState } from "react";

import type { SearchSourceConfigSummary } from "@meda/shared-sdk";

type SearchSourceConfigScreenProps = {
  config: SearchSourceConfigSummary;
  onBackToStageEntry: () => void;
  onSave: (payload: {
    enabled_source_keys: string[];
    search_fields: string[];
    year_from: number | null;
    year_to: number | null;
    languages: string[];
  }) => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

export function SearchSourceConfigScreen({
  config,
  onBackToStageEntry,
  onSave,
}: SearchSourceConfigScreenProps) {
  const [enabledKeys, setEnabledKeys] = useState<string[]>(
    config.enabled_source_keys,
  );

  useEffect(() => {
    setEnabledKeys(config.enabled_source_keys);
  }, [config.enabled_source_keys]);

  const toggleSource = (key: string) => {
    setEnabledKeys((current) =>
      current.includes(key)
        ? current.filter((item) => item !== key)
        : config.available_sources
            .map((item) => item.key)
            .filter((item) => current.includes(item) || item === key),
    );
  };

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
          <h2 style={{ margin: "16px 0 8px", fontSize: "30px" }}>数据库来源</h2>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>
            {config.project.name}
          </div>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>来源清单</h3>
          {config.available_sources.map((source) => (
            <label
              key={source.key}
              style={{
                display: "flex",
                gap: "12px",
                alignItems: "flex-start",
                marginBottom: "12px",
                border: "1px solid #e5e7eb",
                borderRadius: "12px",
                padding: "12px 14px",
              }}
            >
              <input
                type="checkbox"
                aria-label={`启用 ${source.label}`}
                checked={enabledKeys.includes(source.key)}
                onChange={() => toggleSource(source.key)}
              />
              <span>
                <span style={{ fontWeight: 600 }}>{source.label}</span>
                <span
                  style={{
                    display: "block",
                    marginTop: "4px",
                    color: "#6b7280",
                    fontSize: "13px",
                  }}
                >
                  {source.description}
                  {source.supports_full_text ? " · 支持全文" : ""}
                </span>
              </span>
            </label>
          ))}
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>检索参数</h3>
          <div>检索字段：{config.search_fields.join(", ")}</div>
          <div style={{ marginTop: "8px" }}>
            年份区间：{config.year_from ?? "不限"} — {config.year_to ?? "不限"}
          </div>
          <div style={{ marginTop: "8px" }}>
            语种：{config.languages.join(", ")}
          </div>
        </section>

        <section style={panelStyle}>
          <button
            style={{
              border: "none",
              background: "#111827",
              color: "#f9fafb",
              borderRadius: "999px",
              padding: "10px 16px",
              cursor: "pointer",
            }}
            onClick={() =>
              onSave({
                enabled_source_keys: enabledKeys,
                search_fields: config.search_fields,
                year_from: config.year_from,
                year_to: config.year_to,
                languages: config.languages,
              })
            }
          >
            保存配置
          </button>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>配置影响</h3>
          <div>{config.impact_summary.coverage_hint}</div>
          <div style={{ marginTop: "8px", color: "#4b5563" }}>
            {config.impact_summary.query_impact_hint}
          </div>
          {config.validation_messages.map((message) => (
            <div
              key={message.code}
              style={{
                marginTop: "12px",
                color: message.level === "error" ? "#b91c1c" : "#6b7280",
              }}
            >
              {message.message}
            </div>
          ))}
        </section>
      </aside>
    </>
  );
}
```

- [ ] **Step 4: 接入 Desktop App.tsx**

在 import 区追加：

```typescript
import { SearchSourceConfigScreen } from "./components/SearchSourceConfigScreen";
```

在类型 import 中追加 `type SearchSourceConfigSummary,`。

在 `Screen` 联合类型中追加 `| "source-config"`。

在 `const [searchQueryEditor, setSearchQueryEditor] = ...` 之后追加状态：

```typescript
  const [sourceConfig, setSourceConfig] =
    useState<SearchSourceConfigSummary | null>(null);
```

在 `stage-entry` 分支的 `StageEntryScreen` 的 `onOpenEntryCard` 回调中追加 `sources` 处理：

```typescript
          onOpenEntryCard={async (entryKey) => {
            if (entryKey === "query-builder") {
              setSearchQueryEditor(
                await client.getSearchQueryEditor(workspaceHome.project.id),
              );
              setScreen("query-builder");
              return;
            }

            if (entryKey === "sources") {
              setSourceConfig(
                await client.getSearchSourceConfig(workspaceHome.project.id),
              );
              setScreen("source-config");
              return;
            }

            setScreen("stage-subentry");
          }}
```

在 `query-builder` 屏幕分支之后、`stage-subentry` 分支之前插入新分支。左侧栏结构与 `query-builder` 分支完全相同，直接复用同样的 JSX：

```typescript
  if (screen === "source-config" && sourceConfig !== null) {
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

        <SearchSourceConfigScreen
          config={sourceConfig}
          onBackToStageEntry={() => setScreen("stage-entry")}
          onSave={async (payload) => {
            setSourceConfig(
              await client.saveSearchSourceConfig(
                workspaceHome.project.id,
                payload,
              ),
            );
          }}
        />
      </main>
    );
  }
```

- [ ] **Step 5: 运行测试确认通过**

Run: `npm --prefix "." --workspace apps-desktop exec vitest run`
Expected: PASS — 4 passed

- [ ] **Step 6: 全链路回归**

依次运行四条命令，全部应为 exit code 0：

```bash
uv run --project "apps/agent-core" pytest apps/agent-core/tests/ -q
npm --prefix "." --workspace @meda/shared-sdk exec vitest run
npm --prefix "." --workspace apps-web exec vitest run
npm --prefix "." --workspace apps-desktop exec vitest run
```

Expected: 后端 40 passed，SDK 10 passed，Web 3 passed，Desktop 4 passed

- [ ] **Step 7: 提交**

```bash
git add apps/desktop/src/components/SearchSourceConfigScreen.tsx apps/desktop/src/App.tsx apps/desktop/tests/app-auth.test.tsx
git commit -m "feat: add desktop source config screen"
```

---

## 验收清单

对照 spec 14 逐项核对：

- [ ] 可从检索阶段入口页进入 `数据库来源` 配置页（Task 5 / 6）
- [ ] 页面含来源清单、检索参数、影响提示三块（Task 5 / 6）
- [ ] 可启用停用来源并保存（Task 2 / 5 / 6）
- [ ] 检索字段、年份区间、语种可配置并持久化（Task 2）
- [ ] `query-builder` 的 `selected_sources` 来自真实配置（Task 3）
- [ ] `preview_summary` 由真实配置驱动（Task 3）
- [ ] 无来源时 preview 进入 `unavailable` 并给出 `MISSING_SOURCE_CONFIG`（Task 3）
- [ ] 版本快照来源不被配置变更改写（Task 3）
- [ ] 非法输入 `422`、跨机构 `404`、无未处理 `500`（Task 2）
- [ ] Web 与 Desktop 同构（Task 5 / 6）
- [ ] 返回链路可达（Task 5 / 6）



