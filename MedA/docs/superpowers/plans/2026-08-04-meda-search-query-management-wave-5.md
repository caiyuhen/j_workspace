# MedA Wave 5 检索式管理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first real deep work page under the MedA search stage so a project-scoped search query can open as a draft, be edited as grouped terms plus expression blocks, be validated, saved, and versioned in both Web and Desktop.

**Architecture:** Extend the current `workspace` slice with a dedicated search-query editor API instead of overloading the existing stage-entry response. Persist a minimal `SearchQuery -> SearchQueryDraft -> SearchQueryVersion` model on the backend, expose one shared SDK contract for read/write actions, and keep frontend routing lightweight by driving the deep page through internal app state while preserving project and stage context.

**Tech Stack:** Python 3.12, FastAPI, SQLModel, React 18, TypeScript, Electron, Vitest, pytest

---

## Scope Note

This wave covers only the first independently testable deep page under the search stage:

- project-scoped search query editor read API
- draft save, save-as-version, and derive-draft actions
- shared SDK types and client methods for the editor
- Web deep page for `检索式管理`
- Desktop deep page with the same information architecture
- heuristic preview and validation messaging

This wave explicitly does **not** include:

- real database search execution
- database source management page
- search log timeline page
- free-form drag and drop builder
- version diff center
- multi-user conflict handling

## File Structure

### Repository Layout

- Modify: `D:\workspace\MedA\apps\agent-core\app\models.py` - add `SearchQuery`, `SearchQueryDraft`, and `SearchQueryVersion`
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py` - add query editor request/response models
- Create: `D:\workspace\MedA\apps\agent-core\app\services\search_query.py` - build default drafts, validate blocks, generate heuristic preview, persist draft/version actions
- Modify: `D:\workspace\MedA\apps\agent-core\app\services\stage_entry.py` - point search-stage primary action and query-builder card to the deep page route
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\workspace.py` - add read/write query-builder endpoints
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py` - verify draft creation, save, save-as-version, snapshot open, and derive-draft
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\client.ts` - add editor types and client helpers
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts` - verify editor calls use the bearer token
- Create: `D:\workspace\MedA\apps\web\src\components\workspace\SearchQueryBuilderScreen.tsx` - render the three-column query builder screen in Web
- Modify: `D:\workspace\MedA\apps\web\src\components\workspace\StageEntryScreen.tsx` - allow opening individual stage-entry cards by key
- Modify: `D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx` - orchestrate stage-entry vs query-builder vs placeholder handoff
- Modify: `D:\workspace\MedA\apps\web\src\App.tsx` - load, save, version, and reopen search query editor state
- Modify: `D:\workspace\MedA\apps\web\src\App.test.tsx` - verify opening and versioning the search query builder
- Create: `D:\workspace\MedA\apps\desktop\src\components\SearchQueryBuilderScreen.tsx` - render the same deep page in Desktop
- Modify: `D:\workspace\MedA\apps\desktop\src\components\StageEntryScreen.tsx` - open stage-entry cards individually
- Modify: `D:\workspace\MedA\apps\desktop\src\App.tsx` - load and save query-builder state in Desktop
- Modify: `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx` - verify Desktop opens the query builder and creates a version

---

### Task 1: Add The Search Query Editor Read API

**Files:**
- Modify: `D:\workspace\MedA\apps\agent-core\app\models.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\services\search_query.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\services\stage_entry.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\workspace.py`
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py`

- [ ] **Step 1: Write the failing test**

`D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py`

```python
from fastapi.testclient import TestClient

from app.main import app


def test_query_builder_creates_default_draft_for_project() -> None:
    client = TestClient(app)

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
            "description": "Wave 5 query builder",
        },
    )
    project_id = project.json()["id"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["project"]["id"] == project_id
    assert body["query_name"] == "检索式 1"
    assert body["query_mode"] == "draft"
    assert body["query_dirty"] is False
    assert body["query_version"] == "draft"
    assert body["grouped_terms"][0]["group_key"] == "population"
    assert body["expression_blocks"][0]["block_type"] == "term"
    assert body["preview_summary"]["status"] == "available"
    assert body["preview_summary"]["database_scope_summary"] == "PubMed, Embase"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py::test_query_builder_creates_default_draft_for_project" -v`

Expected: FAIL with `404 Not Found` because the query-builder endpoint does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\apps\agent-core\app\models.py`

```python
class SearchQuery(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    name: str
    stage_key: str = "search"
    latest_version: str = "v0"


class SearchQueryDraft(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="searchquery.id")
    based_on_version: str = "v0"
    grouped_terms_json: str
    expression_blocks_json: str
    selected_sources_json: str
    query_dirty: bool = False


class SearchQueryVersion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="searchquery.id")
    version_label: str
    grouped_terms_json: str
    expression_blocks_json: str
    selected_sources_json: str
```

`D:\workspace\MedA\apps\agent-core\app\schemas.py`

```python
class SearchTermSummary(BaseModel):
    term_id: str
    label: str
    source_type: str
    selected: bool


class SearchTermGroupSummary(BaseModel):
    group_key: str
    group_label: str
    terms: list[SearchTermSummary]


class SearchExpressionBlock(BaseModel):
    block_id: str
    block_type: str
    operator: str | None = None
    term_ref: str | None = None
    children: list[str] = []
    position: int


class SearchValidationMessage(BaseModel):
    level: str
    code: str
    message: str


class SearchPreviewSummary(BaseModel):
    status: str
    coverage_hint: str
    database_scope_summary: str
    estimated_hit_band: str
    last_generated_from: str


class SearchQueryEditorResponse(BaseModel):
    project: WorkspaceProjectSummary
    stage_key: str
    query_id: int
    query_name: str
    query_version: str
    query_dirty: bool
    query_mode: str
    selected_sources: list[str]
    grouped_terms: list[SearchTermGroupSummary]
    expression_blocks: list[SearchExpressionBlock]
    validation_messages: list[SearchValidationMessage]
    preview_summary: SearchPreviewSummary
```

`D:\workspace\MedA\apps\agent-core\app\services\search_query.py`

```python
import json

from sqlmodel import Session, select

from app.models import ResearchProject, SearchQuery, SearchQueryDraft
from app.schemas import (
    SearchExpressionBlock,
    SearchPreviewSummary,
    SearchQueryEditorResponse,
    SearchTermGroupSummary,
    SearchTermSummary,
    SearchValidationMessage,
    WorkspaceProjectSummary,
)


def _default_grouped_terms() -> list[SearchTermGroupSummary]:
    return [
        SearchTermGroupSummary(
            group_key="population",
            group_label="人群 / 疾病",
            terms=[
                SearchTermSummary(
                    term_id="population-1",
                    label="diabetes mellitus",
                    source_type="controlled",
                    selected=True,
                )
            ],
        ),
        SearchTermGroupSummary(
            group_key="intervention",
            group_label="干预 / 暴露",
            terms=[
                SearchTermSummary(
                    term_id="intervention-1",
                    label="metformin",
                    source_type="free_text",
                    selected=True,
                )
            ],
        ),
    ]


def _default_expression_blocks() -> list[SearchExpressionBlock]:
    return [
        SearchExpressionBlock(
            block_id="block-1",
            block_type="term",
            term_ref="population-1",
            position=0,
        ),
        SearchExpressionBlock(
            block_id="block-2",
            block_type="operator",
            operator="AND",
            position=1,
        ),
        SearchExpressionBlock(
            block_id="block-3",
            block_type="term",
            term_ref="intervention-1",
            position=2,
        ),
    ]


def _build_validation_messages(
    grouped_terms: list[SearchTermGroupSummary],
    expression_blocks: list[SearchExpressionBlock],
) -> list[SearchValidationMessage]:
    if not expression_blocks:
        return [
            SearchValidationMessage(
                level="error",
                code="EMPTY_EXPRESSION",
                message="当前检索式为空，暂不可执行。",
            )
        ]

    if len(grouped_terms) < 2:
        return [
            SearchValidationMessage(
                level="warning",
                code="MISSING_CORE_GROUP",
                message="建议至少补充两个核心主题组。",
            )
        ]

    return [
        SearchValidationMessage(
            level="info",
            code="READY_TO_SAVE",
            message="当前检索式结构完整，可继续保存或生成版本。",
        )
    ]


def _build_preview_summary(selected_sources: list[str], source: str) -> SearchPreviewSummary:
    return SearchPreviewSummary(
        status="available" if selected_sources else "unavailable",
        coverage_hint="主题组覆盖 2 / 5",
        database_scope_summary=", ".join(selected_sources) if selected_sources else "未选择数据库",
        estimated_hit_band="80-150",
        last_generated_from=source,
    )


def get_or_create_search_query_editor(
    session: Session,
    project: ResearchProject,
) -> SearchQueryEditorResponse:
    project_id = project.id or 0
    query = session.exec(
        select(SearchQuery).where(SearchQuery.project_id == project_id)
    ).first()

    if query is None:
        grouped_terms = _default_grouped_terms()
        expression_blocks = _default_expression_blocks()
        query = SearchQuery(project_id=project_id, name="检索式 1")
        session.add(query)
        session.commit()
        session.refresh(query)

        draft = SearchQueryDraft(
            query_id=query.id or 0,
            grouped_terms_json=json.dumps([item.model_dump() for item in grouped_terms], ensure_ascii=False),
            expression_blocks_json=json.dumps([item.model_dump() for item in expression_blocks], ensure_ascii=False),
            selected_sources_json=json.dumps(["PubMed", "Embase"], ensure_ascii=False),
        )
        session.add(draft)
        session.commit()
        session.refresh(draft)
    else:
        draft = session.exec(
            select(SearchQueryDraft).where(SearchQueryDraft.query_id == (query.id or 0))
        ).one()
        grouped_terms = [SearchTermGroupSummary(**item) for item in json.loads(draft.grouped_terms_json)]
        expression_blocks = [SearchExpressionBlock(**item) for item in json.loads(draft.expression_blocks_json)]

    selected_sources = json.loads(draft.selected_sources_json)
    validation_messages = _build_validation_messages(grouped_terms, expression_blocks)

    return SearchQueryEditorResponse(
        project=WorkspaceProjectSummary(
            id=project_id,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="检索",
            updated_at_label="刚刚更新",
        ),
        stage_key="search",
        query_id=query.id or 0,
        query_name=query.name,
        query_version="draft",
        query_dirty=draft.query_dirty,
        query_mode="draft",
        selected_sources=selected_sources,
        grouped_terms=grouped_terms,
        expression_blocks=expression_blocks,
        validation_messages=validation_messages,
        preview_summary=_build_preview_summary(selected_sources, "draft"),
    )
```

`D:\workspace\MedA\apps\agent-core\app\services\stage_entry.py`

```python
    primary_action = config["primary_action"]
    entry_cards = config["entry_cards"]

    if stage_key == "search":
        primary_action = primary_action.model_copy(
            update={"target": f"/workspace/projects/{project_id}/stages/search/query-builder"}
        )
        entry_cards = [
            card.model_copy(
                update={
                    "target": (
                        f"/workspace/projects/{project_id}/stages/search/query-builder"
                        if card.key == "query-builder"
                        else card.target
                    )
                }
            )
            for card in config["entry_cards"]
        ]
```

`D:\workspace\MedA\apps\agent-core\app\routers\workspace.py`

```python
from app.schemas import SearchQueryEditorResponse, StageEntryResponse, WorkspaceHomeResponse
from app.services.search_query import get_or_create_search_query_editor


@router.get(
    "/projects/{project_id}/stages/search/query-builder",
    response_model=SearchQueryEditorResponse,
)
def get_search_query_editor(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = session.get(ResearchProject, project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    return get_or_create_search_query_editor(session, project)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py::test_query_builder_creates_default_draft_for_project" -v`

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/app/models.py" "MedA/apps/agent-core/app/schemas.py" "MedA/apps/agent-core/app/services/search_query.py" "MedA/apps/agent-core/app/services/stage_entry.py" "MedA/apps/agent-core/app/routers/workspace.py" "MedA/apps/agent-core/tests/test_search_query_api.py"
git -C "D:\workspace" commit -m "feat: add MedA search query editor read API"
```

### Task 2: Add Draft Save, Save-As-Version, And Snapshot Reopen APIs

**Files:**
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\services\search_query.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\workspace.py`
- Modify: `D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py`

- [ ] **Step 1: Write the failing tests**

Append these tests to `D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py`:

```python
def test_query_builder_saves_draft_and_creates_version_snapshot() -> None:
    client = TestClient(app)

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
            "description": "Wave 5 query save",
        },
    )
    project_id = project.json()["id"]

    initial = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    save_response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query_id": initial["query_id"],
            "query_name": "糖尿病检索式",
            "selected_sources": ["PubMed", "Embase"],
            "grouped_terms": initial["grouped_terms"],
            "expression_blocks": initial["expression_blocks"],
        },
    )

    save_body = save_response.json()

    assert save_response.status_code == 200
    assert save_body["query_name"] == "糖尿病检索式"
    assert save_body["query_dirty"] is False

    version_response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/save-as-version",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query_id": initial["query_id"],
            "query_name": "糖尿病检索式",
            "selected_sources": ["PubMed", "Embase"],
            "grouped_terms": initial["grouped_terms"],
            "expression_blocks": initial["expression_blocks"],
        },
    )

    assert version_response.status_code == 200
    assert version_response.json()["query_version"] == "v1"
    assert version_response.json()["query_mode"] == "draft"


def test_query_builder_opens_snapshot_and_derives_new_draft() -> None:
    client = TestClient(app)

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
            "description": "Wave 5 query snapshot",
        },
    )
    project_id = project.json()["id"]

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

    snapshot = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder?query_id={initial['query_id']}&version=v1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert snapshot.status_code == 200
    assert snapshot.json()["query_mode"] == "snapshot"
    assert snapshot.json()["query_version"] == "v1"

    derive = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/derive-draft",
        headers={"Authorization": f"Bearer {token}"},
        json={"query_id": initial["query_id"], "version_label": "v1"},
    )

    assert derive.status_code == 200
    assert derive.json()["query_mode"] == "draft"
    assert derive.json()["query_version"] == "v1"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py" -v`

Expected: FAIL with `404 Not Found` for the save, save-as-version, and derive-draft routes.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\apps\agent-core\app\schemas.py`

```python
class SaveSearchQueryDraftRequest(BaseModel):
    query_id: int
    query_name: str
    selected_sources: list[str]
    grouped_terms: list[SearchTermGroupSummary]
    expression_blocks: list[SearchExpressionBlock]


class DeriveSearchQueryDraftRequest(BaseModel):
    query_id: int
    version_label: str
```

`D:\workspace\MedA\apps\agent-core\app\services\search_query.py`

```python
from app.models import SearchQueryVersion


def save_search_query_draft(
    session: Session,
    project: ResearchProject,
    payload: SaveSearchQueryDraftRequest,
) -> SearchQueryEditorResponse:
    query = session.get(SearchQuery, payload.query_id)
    draft = session.exec(
        select(SearchQueryDraft).where(SearchQueryDraft.query_id == payload.query_id)
    ).one()

    query.name = payload.query_name
    draft.grouped_terms_json = json.dumps([item.model_dump() for item in payload.grouped_terms], ensure_ascii=False)
    draft.expression_blocks_json = json.dumps([item.model_dump() for item in payload.expression_blocks], ensure_ascii=False)
    draft.selected_sources_json = json.dumps(payload.selected_sources, ensure_ascii=False)
    draft.query_dirty = False
    session.add(query)
    session.add(draft)
    session.commit()

    return get_or_create_search_query_editor(session, project)


def save_search_query_version(
    session: Session,
    project: ResearchProject,
    payload: SaveSearchQueryDraftRequest,
) -> SearchQueryEditorResponse:
    response = save_search_query_draft(session, project, payload)
    query = session.get(SearchQuery, payload.query_id)
    current_index = int(query.latest_version.removeprefix("v"))
    next_version = f"v{current_index + 1}"

    version = SearchQueryVersion(
        query_id=payload.query_id,
        version_label=next_version,
        grouped_terms_json=json.dumps([item.model_dump() for item in payload.grouped_terms], ensure_ascii=False),
        expression_blocks_json=json.dumps([item.model_dump() for item in payload.expression_blocks], ensure_ascii=False),
        selected_sources_json=json.dumps(payload.selected_sources, ensure_ascii=False),
    )
    query.latest_version = next_version
    draft = session.exec(
        select(SearchQueryDraft).where(SearchQueryDraft.query_id == payload.query_id)
    ).one()
    draft.based_on_version = next_version
    session.add(version)
    session.add(query)
    session.add(draft)
    session.commit()

    updated = get_or_create_search_query_editor(session, project)
    return updated.model_copy(update={"query_version": next_version})


def get_search_query_snapshot(
    session: Session,
    project: ResearchProject,
    query_id: int,
    version_label: str,
) -> SearchQueryEditorResponse:
    query = session.get(SearchQuery, query_id)
    version = session.exec(
        select(SearchQueryVersion).where(
            SearchQueryVersion.query_id == query_id,
            SearchQueryVersion.version_label == version_label,
        )
    ).one()
    grouped_terms = [SearchTermGroupSummary(**item) for item in json.loads(version.grouped_terms_json)]
    expression_blocks = [SearchExpressionBlock(**item) for item in json.loads(version.expression_blocks_json)]
    selected_sources = json.loads(version.selected_sources_json)

    return SearchQueryEditorResponse(
        project=WorkspaceProjectSummary(
            id=project.id or 0,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="检索",
            updated_at_label="刚刚更新",
        ),
        stage_key="search",
        query_id=query_id,
        query_name=query.name,
        query_version=version_label,
        query_dirty=False,
        query_mode="snapshot",
        selected_sources=selected_sources,
        grouped_terms=grouped_terms,
        expression_blocks=expression_blocks,
        validation_messages=_build_validation_messages(grouped_terms, expression_blocks),
        preview_summary=_build_preview_summary(selected_sources, "snapshot"),
    )


def derive_search_query_draft(
    session: Session,
    project: ResearchProject,
    payload: DeriveSearchQueryDraftRequest,
) -> SearchQueryEditorResponse:
    version = session.exec(
        select(SearchQueryVersion).where(
            SearchQueryVersion.query_id == payload.query_id,
            SearchQueryVersion.version_label == payload.version_label,
        )
    ).one()
    draft = session.exec(
        select(SearchQueryDraft).where(SearchQueryDraft.query_id == payload.query_id)
    ).one()
    draft.grouped_terms_json = version.grouped_terms_json
    draft.expression_blocks_json = version.expression_blocks_json
    draft.selected_sources_json = version.selected_sources_json
    draft.based_on_version = payload.version_label
    draft.query_dirty = False
    session.add(draft)
    session.commit()

    updated = get_or_create_search_query_editor(session, project)
    return updated.model_copy(update={"query_version": payload.version_label})
```

`D:\workspace\MedA\apps\agent-core\app\routers\workspace.py`

```python
from fastapi import Query

from app.schemas import (
    DeriveSearchQueryDraftRequest,
    SaveSearchQueryDraftRequest,
    SearchQueryEditorResponse,
    StageEntryResponse,
    WorkspaceHomeResponse,
)
from app.services.search_query import (
    derive_search_query_draft,
    get_or_create_search_query_editor,
    get_search_query_snapshot,
    save_search_query_draft,
    save_search_query_version,
)


@router.get(
    "/projects/{project_id}/stages/search/query-builder",
    response_model=SearchQueryEditorResponse,
)
def get_search_query_editor(
    project_id: int,
    query_id: int | None = Query(default=None),
    version: str | None = Query(default=None),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = session.get(ResearchProject, project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    if query_id is not None and version is not None:
        return get_search_query_snapshot(session, project, query_id, version)

    return get_or_create_search_query_editor(session, project)


@router.post(
    "/projects/{project_id}/stages/search/query-builder/save",
    response_model=SearchQueryEditorResponse,
)
def post_search_query_save(
    project_id: int,
    payload: SaveSearchQueryDraftRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = session.get(ResearchProject, project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    return save_search_query_draft(session, project, payload)


@router.post(
    "/projects/{project_id}/stages/search/query-builder/save-as-version",
    response_model=SearchQueryEditorResponse,
)
def post_search_query_save_as_version(
    project_id: int,
    payload: SaveSearchQueryDraftRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = session.get(ResearchProject, project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    return save_search_query_version(session, project, payload)


@router.post(
    "/projects/{project_id}/stages/search/query-builder/derive-draft",
    response_model=SearchQueryEditorResponse,
)
def post_search_query_derive_draft(
    project_id: int,
    payload: DeriveSearchQueryDraftRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = session.get(ResearchProject, project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    return derive_search_query_draft(session, project, payload)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_search_query_api.py" "D:\workspace\MedA\apps\agent-core\tests\test_stage_entry_api.py" -v`

Expected: PASS with `5 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/app/schemas.py" "MedA/apps/agent-core/app/services/search_query.py" "MedA/apps/agent-core/app/routers/workspace.py" "MedA/apps/agent-core/tests/test_search_query_api.py"
git -C "D:\workspace" commit -m "feat: add MedA search query save and version APIs"
```

### Task 3: Add Search Query Editor Support To The Shared SDK

**Files:**
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\client.ts`
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts`

- [ ] **Step 1: Write the failing tests**

Append these tests to `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts`:

```ts
it("fetches the search query editor with the bearer token", async () => {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    json: async () => ({
      project: {
        id: 7,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      query_id: 12,
      query_name: "检索式 1",
      query_version: "draft",
      query_dirty: false,
      query_mode: "draft",
      selected_sources: ["PubMed", "Embase"],
      grouped_terms: [],
      expression_blocks: [],
      validation_messages: [],
      preview_summary: {
        status: "available",
        coverage_hint: "主题组覆盖 2 / 5",
        database_scope_summary: "PubMed, Embase",
        estimated_hit_band: "80-150",
        last_generated_from: "draft",
      },
    }),
  }));

  vi.stubGlobal("fetch", fetchMock);

  const client = createClient(
    "http://localhost:8000",
    createMemorySessionStore("meda_token"),
  );

  const data = await client.getSearchQueryEditor(7);

  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/api/workspace/projects/7/stages/search/query-builder",
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer meda_token",
      },
    },
  );
  expect(data.query_name).toBe("检索式 1");
  expect(data.preview_summary.status).toBe("available");
});


it("posts save-as-version with the bearer token", async () => {
  const fetchMock = vi.fn(async () => ({
    ok: true,
    json: async () => ({
      project: {
        id: 7,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      query_id: 12,
      query_name: "糖尿病检索式",
      query_version: "v1",
      query_dirty: false,
      query_mode: "draft",
      selected_sources: ["PubMed", "Embase"],
      grouped_terms: [],
      expression_blocks: [],
      validation_messages: [],
      preview_summary: {
        status: "available",
        coverage_hint: "主题组覆盖 2 / 5",
        database_scope_summary: "PubMed, Embase",
        estimated_hit_band: "80-150",
        last_generated_from: "draft",
      },
    }),
  }));

  vi.stubGlobal("fetch", fetchMock);

  const client = createClient(
    "http://localhost:8000",
    createMemorySessionStore("meda_token"),
  );

  const data = await client.saveSearchQueryVersion(7, {
    query_id: 12,
    query_name: "糖尿病检索式",
    selected_sources: ["PubMed", "Embase"],
    grouped_terms: [],
    expression_blocks: [],
  });

  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/api/workspace/projects/7/stages/search/query-builder/save-as-version",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer meda_token",
      },
      body: JSON.stringify({
        query_id: 12,
        query_name: "糖尿病检索式",
        selected_sources: ["PubMed", "Embase"],
        grouped_terms: [],
        expression_blocks: [],
      }),
    },
  );
  expect(data.query_version).toBe("v1");
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm --prefix "D:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run "src/session.test.ts"`

Expected: FAIL because `getSearchQueryEditor` and `saveSearchQueryVersion` do not exist yet.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\packages\shared-sdk\src\client.ts`

```ts
export type SearchTermSummary = {
  term_id: string;
  label: string;
  source_type: string;
  selected: boolean;
};

export type SearchTermGroupSummary = {
  group_key: string;
  group_label: string;
  terms: SearchTermSummary[];
};

export type SearchExpressionBlock = {
  block_id: string;
  block_type: string;
  operator?: string | null;
  term_ref?: string | null;
  children: string[];
  position: number;
};

export type SearchValidationMessage = {
  level: string;
  code: string;
  message: string;
};

export type SearchPreviewSummary = {
  status: string;
  coverage_hint: string;
  database_scope_summary: string;
  estimated_hit_band: string;
  last_generated_from: string;
};

export type SearchQueryEditorSummary = {
  project: WorkspaceProjectSummary;
  stage_key: string;
  query_id: number;
  query_name: string;
  query_version: string;
  query_dirty: boolean;
  query_mode: string;
  selected_sources: string[];
  grouped_terms: SearchTermGroupSummary[];
  expression_blocks: SearchExpressionBlock[];
  validation_messages: SearchValidationMessage[];
  preview_summary: SearchPreviewSummary;
};

export type SaveSearchQueryDraftPayload = {
  query_id: number;
  query_name: string;
  selected_sources: string[];
  grouped_terms: SearchTermGroupSummary[];
  expression_blocks: SearchExpressionBlock[];
};

async getSearchQueryEditor(
  projectId: number,
  options?: { queryId?: number; version?: string },
): Promise<SearchQueryEditorSummary> {
  const queryString = new URLSearchParams();
  if (options?.queryId !== undefined) queryString.set("query_id", String(options.queryId));
  if (options?.version !== undefined) queryString.set("version", options.version);
  const suffix = queryString.size > 0 ? `?${queryString.toString()}` : "";
  const response = await fetch(
    `${baseUrl}/api/workspace/projects/${projectId}/stages/search/query-builder${suffix}`,
    { headers: buildHeaders() },
  );
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "search query editor failed");
  }

  return data;
},

async saveSearchQueryDraft(
  projectId: number,
  payload: SaveSearchQueryDraftPayload,
): Promise<SearchQueryEditorSummary> {
  const response = await fetch(
    `${baseUrl}/api/workspace/projects/${projectId}/stages/search/query-builder/save`,
    {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    },
  );
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "search query save failed");
  }

  return data;
},

async saveSearchQueryVersion(
  projectId: number,
  payload: SaveSearchQueryDraftPayload,
): Promise<SearchQueryEditorSummary> {
  const response = await fetch(
    `${baseUrl}/api/workspace/projects/${projectId}/stages/search/query-builder/save-as-version`,
    {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify(payload),
    },
  );
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "search query version failed");
  }

  return data;
},

async deriveSearchQueryDraft(
  projectId: number,
  queryId: number,
  versionLabel: string,
): Promise<SearchQueryEditorSummary> {
  const response = await fetch(
    `${baseUrl}/api/workspace/projects/${projectId}/stages/search/query-builder/derive-draft`,
    {
      method: "POST",
      headers: buildHeaders(),
      body: JSON.stringify({ query_id: queryId, version_label: versionLabel }),
    },
  );
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "search query derive failed");
  }

  return data;
},
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm --prefix "D:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run "src/session.test.ts"`

Expected: PASS with `4 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/packages/shared-sdk/src/client.ts" "MedA/packages/shared-sdk/src/session.test.ts"
git -C "D:\workspace" commit -m "feat: add MedA search query SDK helpers"
```

### Task 4: Render The Search Query Builder In Web

**Files:**
- Create: `D:\workspace\MedA\apps\web\src\components\workspace\SearchQueryBuilderScreen.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\components\workspace\StageEntryScreen.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\App.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\App.test.tsx`

- [ ] **Step 1: Write the failing test**

Replace `D:\workspace\MedA\apps\web\src\App.test.tsx` with:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "./App";

const sessionStore = {
  getToken: vi.fn(() => null),
  setToken: vi.fn(),
  clearToken: vi.fn(),
};

const saveSearchQueryVersion = vi.fn(async () => ({
  project: {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
    current_stage: "检索",
    updated_at_label: "刚刚更新",
  },
  stage_key: "search",
  query_id: 11,
  query_name: "糖尿病检索式",
  query_version: "v1",
  query_dirty: false,
  query_mode: "draft",
  selected_sources: ["PubMed", "Embase"],
  grouped_terms: [],
  expression_blocks: [],
  validation_messages: [],
  preview_summary: {
    status: "available",
    coverage_hint: "主题组覆盖 2 / 5",
    database_scope_summary: "PubMed, Embase",
    estimated_hit_band: "80-150",
    last_generated_from: "draft",
  },
}));

vi.mock("@meda/shared-sdk", () => ({
  createBrowserSessionStore: () => sessionStore,
  createClient: () => ({
    devLogin: async () => ({
      token: "meda_token",
      user: { user_id: "u-001", display_name: "Dr. Chen" },
      organization: { slug: "demo-hospital", name: "Demo Hospital" },
      role: "org_admin",
      client_type: "web",
    }),
    listProjects: async () => [
      { id: 1, name: "糖尿病真实世界研究", workspace_key: "demo-hospital/糖尿病真实世界研究" },
    ],
    getWorkspaceHome: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "方案设计",
        updated_at_label: "刚刚更新",
      },
      hero_cta: { label: "继续上次研究", target: "/workspace/tasks/recent" },
      stages: [{ key: "search", label: "检索", status: "done", task_count: 1, artifact_count: 1, target: "/workspace/stages/search" }],
      recent_tasks: [],
      recent_artifacts: [],
      activity: [],
      assistant: {
        headline: "MedA 助手建议",
        primary_action_label: "生成下一步建议",
        primary_action_target: "/workspace/assistant",
      },
      todos: [],
    }),
    getStageEntry: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      stage_label: "检索",
      stage_status: "done",
      stage_goal: "完成检索式与来源配置",
      primary_action: {
        label: "进入检索式管理",
        target: "/workspace/projects/1/stages/search/query-builder",
      },
      entry_cards: [
        {
          key: "query-builder",
          title: "检索式管理",
          description: "维护主题词、自由词和组合策略",
          status: "ready",
          target: "/workspace/projects/1/stages/search/query-builder",
        },
      ],
      recent_tasks: [],
      recent_artifacts: [],
      assistant_suggestions: [],
      guidance_notes: [{ title: "输入要求", detail: "需要主题词、自由词与数据库范围。" }],
    }),
    getSearchQueryEditor: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      query_id: 11,
      query_name: "检索式 1",
      query_version: "draft",
      query_dirty: false,
      query_mode: "draft",
      selected_sources: ["PubMed", "Embase"],
      grouped_terms: [
        {
          group_key: "population",
          group_label: "人群 / 疾病",
          terms: [{ term_id: "population-1", label: "diabetes mellitus", source_type: "controlled", selected: true }],
        },
      ],
      expression_blocks: [
        { block_id: "block-1", block_type: "term", term_ref: "population-1", children: [], position: 0 },
      ],
      validation_messages: [{ level: "info", code: "READY_TO_SAVE", message: "当前检索式结构完整，可继续保存或生成版本。" }],
      preview_summary: {
        status: "available",
        coverage_hint: "主题组覆盖 2 / 5",
        database_scope_summary: "PubMed, Embase",
        estimated_hit_band: "80-150",
        last_generated_from: "draft",
      },
    }),
    saveSearchQueryDraft: vi.fn(),
    saveSearchQueryVersion,
    deriveSearchQueryDraft: vi.fn(),
  }),
}));

test("web workspace opens query builder and creates a version", async () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("机构标识"), {
    target: { value: "demo-hospital" },
  });
  fireEvent.change(screen.getByLabelText("用户编号"), {
    target: { value: "u-001" },
  });
  fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));
  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "进入检索式管理" }));

  expect(await screen.findByText("检索式管理")).toBeInTheDocument();
  expect(screen.getByText("人群 / 疾病")).toBeInTheDocument();
  expect(screen.getByText("主题组覆盖 2 / 5")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "另存为新版本" }));

  expect(saveSearchQueryVersion).toHaveBeenCalled();
  expect(await screen.findByText("当前版本：v1")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`

Expected: FAIL because the stage-entry screen still routes `query-builder` to the generic placeholder `阶段子入口承接页`.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\apps\web\src\components\workspace\SearchQueryBuilderScreen.tsx`

```tsx
import type { SearchQueryEditorSummary } from "@meda/shared-sdk";

type SearchQueryBuilderScreenProps = {
  editor: SearchQueryEditorSummary;
  onBackToStageEntry: () => void;
  onSaveDraft: () => void;
  onSaveVersion: () => void;
  onDeriveDraft: () => void;
};

export function SearchQueryBuilderScreen({
  editor,
  onBackToStageEntry,
  onSaveDraft,
  onSaveVersion,
  onDeriveDraft,
}: SearchQueryBuilderScreenProps) {
  return (
    <>
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
          <button onClick={onBackToStageEntry}>返回检索阶段入口页</button>
          <h2 style={{ margin: "12px 0 8px" }}>检索式管理</h2>
          <div>{editor.project.name}</div>
          <div>当前检索式：{editor.query_name}</div>
          <div>当前版本：{editor.query_version}</div>
          <div>模式：{editor.query_mode}</div>
          <div style={{ display: "flex", gap: "12px", marginTop: "16px" }}>
            <button onClick={onSaveDraft}>保存</button>
            <button onClick={onSaveVersion}>另存为新版本</button>
            {editor.query_mode === "snapshot" ? <button onClick={onDeriveDraft}>派生为草稿</button> : null}
          </div>
        </section>

        <section style={{ display: "grid", gridTemplateColumns: "280px minmax(0, 1fr)", gap: "20px" }}>
          <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
            <h3 style={{ marginTop: 0 }}>词组与字段区</h3>
            {editor.grouped_terms.map((group) => (
              <div key={group.group_key} style={{ marginBottom: "16px" }}>
                <div style={{ fontWeight: 600 }}>{group.group_label}</div>
                {group.terms.map((term) => (
                  <div key={term.term_id} style={{ marginTop: "8px", border: "1px solid #e5e7eb", borderRadius: "12px", padding: "10px 12px" }}>
                    {term.label} · {term.source_type}
                  </div>
                ))}
              </div>
            ))}
          </section>

          <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
            <h3 style={{ marginTop: 0 }}>块式编辑器</h3>
            {editor.expression_blocks.map((block) => (
              <div key={block.block_id} style={{ marginBottom: "10px", border: "1px solid #e5e7eb", borderRadius: "12px", padding: "10px 12px" }}>
                {block.block_type === "term" ? `TERM · ${block.term_ref}` : `${block.block_type} · ${block.operator ?? ""}`}
              </div>
            ))}
            <div style={{ marginTop: "16px", color: "#4b5563" }}>
              {editor.validation_messages.map((message) => message.message).join(" / ")}
            </div>
          </section>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
          <h3 style={{ marginTop: 0 }}>预览 + 助手</h3>
          <div>{editor.preview_summary.coverage_hint}</div>
          <div>{editor.preview_summary.database_scope_summary}</div>
          <div>{editor.preview_summary.estimated_hit_band}</div>
          <div>{editor.preview_summary.last_generated_from}</div>
        </section>
      </aside>
    </>
  );
}
```

`D:\workspace\MedA\apps\web\src\components\workspace\StageEntryScreen.tsx`

```tsx
type StageEntryScreenProps = {
  stageEntry: StageEntrySummary;
  onOpenPrimaryAction: () => void;
  onOpenTaskPage: () => void;
  onOpenArtifactPage: () => void;
  onOpenAssistantAction: () => void;
  onOpenEntryCard: (entryKey: string) => void;
};

{stageEntry.entry_cards.map((card) => (
  <SummaryButton
    key={card.key}
    item={card}
    onClick={() => onOpenEntryCard(card.key)}
  />
))}
```

`D:\workspace\MedA\apps\web\src\App.tsx`

```tsx
import {
  createBrowserSessionStore,
  createClient,
  type ProjectSummary,
  type SearchQueryEditorSummary,
  type SessionContext,
  type StageEntrySummary,
  type WorkspaceHomeSummary,
} from "@meda/shared-sdk";

const [searchQueryEditor, setSearchQueryEditor] = useState<SearchQueryEditorSummary | null>(null);

const handleOpenSearchQueryBuilder = async (projectId: number, options?: { queryId?: number; version?: string }) => {
  setSearchQueryEditor(await client.getSearchQueryEditor(projectId, options));
};

const handleSaveSearchQueryDraft = async (projectId: number) => {
  if (searchQueryEditor === null) return;
  setSearchQueryEditor(
    await client.saveSearchQueryDraft(projectId, {
      query_id: searchQueryEditor.query_id,
      query_name: searchQueryEditor.query_name,
      selected_sources: searchQueryEditor.selected_sources,
      grouped_terms: searchQueryEditor.grouped_terms,
      expression_blocks: searchQueryEditor.expression_blocks,
    }),
  );
};

const handleSaveSearchQueryVersion = async (projectId: number) => {
  if (searchQueryEditor === null) return;
  setSearchQueryEditor(
    await client.saveSearchQueryVersion(projectId, {
      query_id: searchQueryEditor.query_id,
      query_name: searchQueryEditor.query_name,
      selected_sources: searchQueryEditor.selected_sources,
      grouped_terms: searchQueryEditor.grouped_terms,
      expression_blocks: searchQueryEditor.expression_blocks,
    }),
  );
};
```

`D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx`

```tsx
import type {
  ProjectSummary,
  SearchQueryEditorSummary,
  SessionContext,
  StageEntrySummary,
  WorkspaceHomeSummary,
} from "@meda/shared-sdk";

import { SearchQueryBuilderScreen } from "./workspace/SearchQueryBuilderScreen";

type Screen =
  | "home"
  | "recent-tasks"
  | "recent-artifacts"
  | "assistant"
  | "stage-entry"
  | "query-builder"
  | "stage-subentry";

type WorkspaceShellProps = {
  session: SessionContext;
  projects: ProjectSummary[];
  workspaceHome: WorkspaceHomeSummary;
  stageEntry: StageEntrySummary | null;
  searchQueryEditor: SearchQueryEditorSummary | null;
  onOpenStage: (projectId: number, stageKey: string) => Promise<void>;
  onOpenSearchQueryBuilder: (
    projectId: number,
    options?: { queryId?: number; version?: string },
  ) => Promise<void>;
  onSaveSearchQueryDraft: (projectId: number) => Promise<void>;
  onSaveSearchQueryVersion: (projectId: number) => Promise<void>;
  onDeriveSearchQueryDraft: (projectId: number, queryId: number, version: string) => Promise<void>;
};

if (screen === "query-builder" && searchQueryEditor !== null) {
  return (
    <main style={shellStyle}>
      <LeftRail projects={projects} workspaceHome={workspaceHome} />
      <SearchQueryBuilderScreen
        editor={searchQueryEditor}
        onBackToStageEntry={() => setScreen("stage-entry")}
        onSaveDraft={() => onSaveSearchQueryDraft(workspaceHome.project.id)}
        onSaveVersion={() => onSaveSearchQueryVersion(workspaceHome.project.id)}
        onDeriveDraft={() =>
          onDeriveSearchQueryDraft(
            workspaceHome.project.id,
            searchQueryEditor.query_id,
            searchQueryEditor.query_version,
          )
        }
      />
    </main>
  );
}

<StageEntryScreen
  stageEntry={stageEntry}
  onOpenPrimaryAction={async () => {
    await onOpenSearchQueryBuilder(workspaceHome.project.id);
    setScreen("query-builder");
  }}
  onOpenTaskPage={() => setScreen("recent-tasks")}
  onOpenArtifactPage={() => setScreen("recent-artifacts")}
  onOpenAssistantAction={() => setScreen("assistant")}
  onOpenEntryCard={async (entryKey) => {
    if (entryKey === "query-builder") {
      await onOpenSearchQueryBuilder(workspaceHome.project.id);
      setScreen("query-builder");
      return;
    }

    setScreen("stage-subentry");
  }}
/>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/web/src/components/workspace/SearchQueryBuilderScreen.tsx" "MedA/apps/web/src/components/workspace/StageEntryScreen.tsx" "MedA/apps/web/src/components/WorkspaceShell.tsx" "MedA/apps/web/src/App.tsx" "MedA/apps/web/src/App.test.tsx"
git -C "D:\workspace" commit -m "feat: add MedA web search query builder"
```

### Task 5: Mirror The Search Query Builder In Desktop

**Files:**
- Create: `D:\workspace\MedA\apps\desktop\src\components\SearchQueryBuilderScreen.tsx`
- Modify: `D:\workspace\MedA\apps\desktop\src\components\StageEntryScreen.tsx`
- Modify: `D:\workspace\MedA\apps\desktop\src\App.tsx`
- Modify: `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx`

- [ ] **Step 1: Write the failing test**

Replace `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx` with:

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "../src/App";

const saveSearchQueryVersion = vi.fn(async () => ({
  project: {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
    current_stage: "检索",
    updated_at_label: "刚刚更新",
  },
  stage_key: "search",
  query_id: 11,
  query_name: "检索式 1",
  query_version: "v1",
  query_dirty: false,
  query_mode: "draft",
  selected_sources: ["PubMed", "Embase"],
  grouped_terms: [],
  expression_blocks: [],
  validation_messages: [],
  preview_summary: {
    status: "available",
    coverage_hint: "主题组覆盖 2 / 5",
    database_scope_summary: "PubMed, Embase",
    estimated_hit_band: "80-150",
    last_generated_from: "draft",
  },
}));

vi.mock("@meda/shared-sdk", () => ({
  createMemorySessionStore: () => ({ getToken: () => "meda_token" }),
  createClient: () => ({
    getMe: async () => ({
      token: "meda_token",
      user: { user_id: "u-001", display_name: "Dr. Chen" },
      organization: { slug: "demo-hospital", name: "Demo Hospital" },
      role: "researcher",
      client_type: "desktop",
    }),
    listProjects: async () => [
      { id: 1, name: "糖尿病真实世界研究", workspace_key: "demo-hospital/糖尿病真实世界研究" },
    ],
    getWorkspaceHome: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "方案设计",
        updated_at_label: "刚刚更新",
      },
      hero_cta: { label: "继续上次研究", target: "/workspace/tasks/recent" },
      stages: [{ key: "search", label: "检索", status: "done", task_count: 1, artifact_count: 1, target: "/workspace/stages/search" }],
      recent_tasks: [],
      recent_artifacts: [],
      activity: [],
      assistant: {
        headline: "MedA 助手建议",
        primary_action_label: "生成下一步建议",
        primary_action_target: "/workspace/assistant",
      },
      todos: [],
    }),
    getStageEntry: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      stage_label: "检索",
      stage_status: "done",
      stage_goal: "完成检索式与来源配置",
      primary_action: {
        label: "进入检索式管理",
        target: "/workspace/projects/1/stages/search/query-builder",
      },
      entry_cards: [
        {
          key: "query-builder",
          title: "检索式管理",
          description: "维护主题词、自由词和组合策略",
          status: "ready",
          target: "/workspace/projects/1/stages/search/query-builder",
        },
      ],
      recent_tasks: [],
      recent_artifacts: [],
      assistant_suggestions: [{ title: "补全数据库来源", subtitle: "优先确认核心医学数据库清单", target: "/workspace/stage/search/sources" }],
      guidance_notes: [{ title: "输入要求", detail: "需要主题词、自由词与数据库范围。" }],
    }),
    getSearchQueryEditor: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      query_id: 11,
      query_name: "检索式 1",
      query_version: "draft",
      query_dirty: false,
      query_mode: "draft",
      selected_sources: ["PubMed", "Embase"],
      grouped_terms: [],
      expression_blocks: [],
      validation_messages: [],
      preview_summary: {
        status: "available",
        coverage_hint: "主题组覆盖 2 / 5",
        database_scope_summary: "PubMed, Embase",
        estimated_hit_band: "80-150",
        last_generated_from: "draft",
      },
    }),
    saveSearchQueryDraft: vi.fn(),
    saveSearchQueryVersion,
    deriveSearchQueryDraft: vi.fn(),
  }),
}));

test("desktop workspace opens query builder and creates a version", async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "进入检索式管理" }));

  expect(await screen.findByText("检索式管理")).toBeInTheDocument();
  expect(screen.getByText("PubMed, Embase")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "另存为新版本" }));

  expect(saveSearchQueryVersion).toHaveBeenCalled();
  expect(await screen.findByText("当前版本：v1")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`

Expected: FAIL because Desktop still routes the stage-entry primary action to the generic `stage-subentry` placeholder.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\apps\desktop\src\components\SearchQueryBuilderScreen.tsx`

```tsx
import type { SearchQueryEditorSummary } from "@meda/shared-sdk";

export function SearchQueryBuilderScreen({
  editor,
  onBackToStageEntry,
  onSaveDraft,
  onSaveVersion,
}: {
  editor: SearchQueryEditorSummary;
  onBackToStageEntry: () => void;
  onSaveDraft: () => void;
  onSaveVersion: () => void;
}) {
  return (
    <>
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
          <button onClick={onBackToStageEntry}>返回检索阶段入口页</button>
          <h2 style={{ margin: "12px 0 8px" }}>检索式管理</h2>
          <div>当前检索式：{editor.query_name}</div>
          <div>当前版本：{editor.query_version}</div>
          <div style={{ display: "flex", gap: "12px", marginTop: "16px" }}>
            <button onClick={onSaveDraft}>保存</button>
            <button onClick={onSaveVersion}>另存为新版本</button>
          </div>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
          <h3 style={{ marginTop: 0 }}>预览 + 助手</h3>
          <div>{editor.preview_summary.database_scope_summary}</div>
          <div>{editor.preview_summary.coverage_hint}</div>
        </section>
      </aside>
    </>
  );
}
```

`D:\workspace\MedA\apps\desktop\src\components\StageEntryScreen.tsx`

```tsx
export function StageEntryScreen({
  stageEntry,
  onOpenPrimaryAction,
  onOpenAssistantAction,
  onOpenTaskPage,
  onOpenArtifactPage,
  onOpenEntryCard,
}: {
  stageEntry: StageEntrySummary;
  onOpenPrimaryAction: () => void;
  onOpenAssistantAction: () => void;
  onOpenTaskPage: () => void;
  onOpenArtifactPage: () => void;
  onOpenEntryCard: (entryKey: string) => void;
}) {
  return (
    <>
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>{stageEntry.project.name}</div>
          <h2 style={{ margin: "8px 0 12px", fontSize: "30px" }}>
            {stageEntry.stage_label}阶段
          </h2>
          <p style={{ margin: "0 0 8px" }}>当前状态：{stageEntry.stage_status}</p>
          <p style={{ margin: 0 }}>{stageEntry.stage_goal}</p>
          <button
            style={{
              marginTop: "16px",
              border: "none",
              borderRadius: "999px",
              background: "#111827",
              color: "#f9fafb",
              padding: "10px 16px",
              cursor: "pointer",
              fontWeight: 600,
            }}
            onClick={onOpenPrimaryAction}
          >
            {stageEntry.primary_action.label}
          </button>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>子入口导航</h3>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
            {stageEntry.entry_cards.map((card) => (
              <StageButton
                key={card.key}
                title={card.title}
                subtitle={`${card.description} · ${card.status}`}
                onClick={() => onOpenEntryCard(card.key)}
              />
            ))}
          </div>
        </section>

        <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "20px" }}>
          <div style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>最近任务</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {stageEntry.recent_tasks.map((task) => (
                <StageButton
                  key={task.title}
                  title={task.title}
                  subtitle={task.subtitle}
                  onClick={onOpenTaskPage}
                />
              ))}
            </div>
          </div>

          <div style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>最近产物</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {stageEntry.recent_artifacts.map((artifact) => (
                <StageButton
                  key={artifact.title}
                  title={artifact.title}
                  subtitle={artifact.subtitle}
                  onClick={onOpenArtifactPage}
                />
              ))}
            </div>
          </div>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>阶段助手 + 下一步建议</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {stageEntry.assistant_suggestions.map((item) => (
              <StageButton
                key={item.title}
                title={item.title}
                subtitle={item.subtitle}
                onClick={onOpenAssistantAction}
              />
            ))}
          </div>
        </section>

        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>阶段提示</h2>
          <ul style={{ margin: 0, paddingLeft: "20px", color: "#374151" }}>
            {stageEntry.guidance_notes.map((note) => (
              <li key={note.title} style={{ marginBottom: "10px" }}>
                <strong>{note.title}</strong>：{note.detail}
              </li>
            ))}
          </ul>
        </section>
      </aside>
    </>
  );
}
```

`D:\workspace\MedA\apps\desktop\src\App.tsx`

```tsx
import {
  createClient,
  createMemorySessionStore,
  type ProjectSummary,
  type SearchQueryEditorSummary,
  type SessionContext,
  type StageEntrySummary,
  type WorkspaceHomeSummary,
  type WorkspaceItemSummary,
  type WorkspaceStageSummary,
} from "@meda/shared-sdk";

import { SearchQueryBuilderScreen } from "./components/SearchQueryBuilderScreen";

function renderDesktopSidebar(projects: ProjectSummary[], workspaceHome: WorkspaceHomeSummary) {
  return (
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
  );
}

type Screen =
  | "home"
  | "recent-tasks"
  | "recent-artifacts"
  | "assistant"
  | "stage-entry"
  | "query-builder"
  | "stage-subentry";

const [searchQueryEditor, setSearchQueryEditor] = useState<SearchQueryEditorSummary | null>(null);

if (screen === "query-builder" && searchQueryEditor !== null) {
  return (
    <main style={shellStyle}>
      {renderDesktopSidebar(projects, workspaceHome)}
      <SearchQueryBuilderScreen
        editor={searchQueryEditor}
        onBackToStageEntry={() => setScreen("stage-entry")}
        onSaveDraft={async () => {
          setSearchQueryEditor(
            await client.saveSearchQueryDraft(workspaceHome.project.id, {
              query_id: searchQueryEditor.query_id,
              query_name: searchQueryEditor.query_name,
              selected_sources: searchQueryEditor.selected_sources,
              grouped_terms: searchQueryEditor.grouped_terms,
              expression_blocks: searchQueryEditor.expression_blocks,
            }),
          );
        }}
        onSaveVersion={async () => {
          setSearchQueryEditor(
            await client.saveSearchQueryVersion(workspaceHome.project.id, {
              query_id: searchQueryEditor.query_id,
              query_name: searchQueryEditor.query_name,
              selected_sources: searchQueryEditor.selected_sources,
              grouped_terms: searchQueryEditor.grouped_terms,
              expression_blocks: searchQueryEditor.expression_blocks,
            }),
          );
        }}
      />
    </main>
  );
}

<StageEntryScreen
  stageEntry={stageEntry}
  onOpenPrimaryAction={async () => {
    setSearchQueryEditor(await client.getSearchQueryEditor(workspaceHome.project.id));
    setScreen("query-builder");
  }}
  onOpenTaskPage={() => setScreen("recent-tasks")}
  onOpenArtifactPage={() => setScreen("recent-artifacts")}
  onOpenAssistantAction={() => setScreen("assistant")}
  onOpenEntryCard={async (entryKey) => {
    if (entryKey === "query-builder") {
      setSearchQueryEditor(await client.getSearchQueryEditor(workspaceHome.project.id));
      setScreen("query-builder");
      return;
    }

    setScreen("stage-subentry");
  }}
/>
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`

Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/desktop/src/components/SearchQueryBuilderScreen.tsx" "MedA/apps/desktop/src/components/StageEntryScreen.tsx" "MedA/apps/desktop/src/App.tsx" "MedA/apps/desktop/tests/app-auth.test.tsx"
git -C "D:\workspace" commit -m "feat: add MedA desktop search query builder"
```

## Self-Review

### Spec Coverage

- Covered in this wave:
  - query draft creation, read, save, save-as-version, and snapshot reopen
  - `draft` vs `snapshot` mode distinction
  - heuristic preview and validation messaging
  - query-builder deep page in both Web and Desktop
  - stage-entry to deep-page navigation
- Deferred to later:
  - database source management page
  - real search execution
  - version diff center
  - search log and query library pages

### Placeholder Scan

- No `TBD`, `TODO`, or vague “implement later” wording remains in the plan.
- Every task includes file paths, concrete code, commands, expected failures, expected passes, and commit messages.

### Type Consistency

- `SearchQueryEditorResponse` matches `SearchQueryEditorSummary`.
- `SaveSearchQueryDraftRequest` matches `SaveSearchQueryDraftPayload`.
- The frontend screen name is consistently `query-builder` in both Web and Desktop.
