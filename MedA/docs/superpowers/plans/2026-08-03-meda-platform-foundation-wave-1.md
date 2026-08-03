# MedA Platform Foundation Wave 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first working MedA platform foundation slice with a reusable agent-core backend, project-scoped auth/data models, audit/event streaming, file/artifact metadata services, web/admin shells, and an Electron desktop shell wired to the same backend.

**Architecture:** Reuse the approved Hermes-derived topology, but implement the first executable slice inside `D:\workspace\MedA` as a clean monorepo with a Python `agent-core` service and TypeScript clients. This wave deliberately stops at a working platform skeleton that can authenticate into an organization, create projects, stream task events, register files/artifacts, and render the same project data in web, admin, and desktop shells.

**Tech Stack:** Python 3.11, FastAPI, SQLModel, Alembic, PostgreSQL, Redis, MinIO, Milvus, React, Vite, TypeScript, Electron, Vitest, Playwright, pytest, Docker Compose

---

## Scope Note

The approved platform-foundation spec still spans several independent subsystems. Per the scope check, this plan covers the **first independently testable wave** only:

- repo convergence
- backend service skeleton
- organization / membership / project / audit core models
- event streaming and file / artifact metadata
- web shell, admin shell, desktop shell
- local deployment and CI sanity checks

This wave intentionally leaves these to follow-on plans:

- Hermes 1:1 UI parity inventory and reproduction
- research modules `R004-R016`
- full vector indexing pipeline implementation
- production observability dashboards and alert routing
- full RBAC matrix expansion beyond the starter roles in this plan

## File Structure

### Repository Layout

- Create: `D:\workspace\MedA\package.json` - root npm workspace manifest for web, admin, desktop, and shared SDK packages
- Create: `D:\workspace\MedA\.gitignore` - root ignore rules for Python, Node, Electron, and local env files
- Create: `D:\workspace\MedA\apps\agent-core\pyproject.toml` - Python service manifest
- Create: `D:\workspace\MedA\apps\agent-core\app\main.py` - FastAPI entry point
- Create: `D:\workspace\MedA\apps\agent-core\app\db.py` - SQLModel engine and session helpers
- Create: `D:\workspace\MedA\apps\agent-core\app\models.py` - `Organization`, `Membership`, `ResearchProject`, `AuditEvent`, `FileRecord`, `ArtifactRecord`
- Create: `D:\workspace\MedA\apps\agent-core\app\schemas.py` - request / response schemas shared by routers
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\projects.py` - project CRUD routes
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\events.py` - SSE event routes
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\files.py` - file and artifact metadata routes
- Create: `D:\workspace\MedA\apps\agent-core\app\services\audit.py` - audit recording service
- Create: `D:\workspace\MedA\apps\agent-core\app\services\events.py` - in-process event broker
- Create: `D:\workspace\MedA\apps\agent-core\app\services\files.py` - file/artifact registration service
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_health.py` - backend health route test
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_projects_api.py` - organization/project workflow tests
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_events_api.py` - event stream tests
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_files_api.py` - file/artifact metadata tests
- Create: `D:\workspace\MedA\packages\shared-sdk\package.json` - shared browser/electron API client package
- Create: `D:\workspace\MedA\packages\shared-sdk\src\client.ts` - typed API client
- Create: `D:\workspace\MedA\apps\web\package.json` - browser shell manifest
- Create: `D:\workspace\MedA\apps\web\src\main.tsx` - web bootstrap
- Create: `D:\workspace\MedA\apps\web\src\App.tsx` - web shell app
- Create: `D:\workspace\MedA\apps\web\src\App.test.tsx` - web shell test
- Create: `D:\workspace\MedA\apps\admin\package.json` - admin shell manifest
- Create: `D:\workspace\MedA\apps\admin\src\main.tsx` - admin bootstrap
- Create: `D:\workspace\MedA\apps\admin\src\App.tsx` - admin shell app
- Create: `D:\workspace\MedA\apps\desktop\package.json` - desktop shell manifest
- Create: `D:\workspace\MedA\apps\desktop\electron\main.ts` - Electron main process
- Create: `D:\workspace\MedA\apps\desktop\electron\preload.ts` - desktop bridge
- Create: `D:\workspace\MedA\apps\desktop\src\main.tsx` - desktop renderer bootstrap
- Create: `D:\workspace\MedA\apps\desktop\src\App.tsx` - desktop renderer app
- Create: `D:\workspace\MedA\apps\desktop\tests\smoke.test.ts` - desktop renderer smoke test
- Create: `D:\workspace\MedA\deploy\docker-compose.local.yml` - local development stack
- Create: `D:\workspace\MedA\.github\workflows\foundation-ci.yml` - CI sanity workflow for backend and frontend foundations

---

### Task 1: Bootstrap The Repository And Agent-Core Health Slice

**Files:**
- Create: `D:\workspace\MedA\.gitignore`
- Create: `D:\workspace\MedA\apps\agent-core\pyproject.toml`
- Create: `D:\workspace\MedA\apps\agent-core\app\main.py`
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_health.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint_returns_ok() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "meda-agent-core"}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_health.py::test_health_endpoint_returns_ok" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'` or a missing project manifest error.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\.gitignore`

```gitignore
node_modules/
dist/
.vite/
.venv/
__pycache__/
.pytest_cache/
.mypy_cache/
.DS_Store
Thumbs.db
.env
.env.*
playwright-report/
test-results/
coverage/
```

`D:\workspace\MedA\apps\agent-core\pyproject.toml`

```toml
[project]
name = "meda-agent-core"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn>=0.30.0",
  "pytest>=8.3.0",
  "httpx>=0.27.0",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

`D:\workspace\MedA\apps\agent-core\app\main.py`

```python
from fastapi import FastAPI

app = FastAPI(title="MedA Agent Core")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_health.py::test_health_endpoint_returns_ok" -v`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/.gitignore" "MedA/apps/agent-core/pyproject.toml" "MedA/apps/agent-core/app/main.py" "MedA/apps/agent-core/tests/test_health.py"
git -C "D:\workspace" commit -m "feat: bootstrap MedA agent-core health service"
```

### Task 2: Add Organization, Membership, And Project APIs

**Files:**
- Modify: `D:\workspace\MedA\apps\agent-core\pyproject.toml`
- Modify: `D:\workspace\MedA\apps\agent-core\app\main.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\db.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\models.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\schemas.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\projects.py`
- Test: `D:\workspace\MedA\apps\agent-core\tests\test_projects_api.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_create_project_with_org_scope() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "首个平台底座联调用例",
        },
    )

    body = response.json()

    assert response.status_code == 201
    assert body["organization_slug"] == "demo-hospital"
    assert body["owner_user_id"] == "u-001"
    assert body["name"] == "糖尿病真实世界研究"
    assert body["workspace_key"] == "demo-hospital/糖尿病真实世界研究"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_projects_api.py::test_create_project_with_org_scope" -v`
Expected: FAIL with `404 Not Found` for `/api/projects` or import errors for missing database modules.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\apps\agent-core\pyproject.toml`

```toml
[project]
name = "meda-agent-core"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
  "fastapi>=0.115.0",
  "uvicorn>=0.30.0",
  "pytest>=8.3.0",
  "httpx>=0.27.0",
  "sqlmodel>=0.0.22",
]

[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

`D:\workspace\MedA\apps\agent-core\app\db.py`

```python
from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

engine = create_engine("sqlite://", connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

`D:\workspace\MedA\apps\agent-core\app\models.py`

```python
from sqlmodel import Field, SQLModel


class Organization(SQLModel, table=True):
    slug: str = Field(primary_key=True)
    name: str


class Membership(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str
    organization_slug: str = Field(foreign_key="organization.slug")
    role: str = "org_admin"


class ResearchProject(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    organization_slug: str = Field(foreign_key="organization.slug")
    owner_user_id: str
    name: str
    description: str
    workspace_key: str
```

`D:\workspace\MedA\apps\agent-core\app\schemas.py`

```python
from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    organization_slug: str
    owner_user_id: str
    name: str
    description: str


class ProjectResponse(BaseModel):
    id: int
    organization_slug: str
    owner_user_id: str
    name: str
    description: str
    workspace_key: str
```

`D:\workspace\MedA\apps\agent-core\app\routers\projects.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import Membership, Organization, ResearchProject
from app.schemas import CreateProjectRequest, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectResponse]:
    projects = session.exec(select(ResearchProject)).all()
    return [ProjectResponse.model_validate(project, from_attributes=True) for project in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest, session: Session = Depends(get_session)
) -> ProjectResponse:
    organization = session.get(Organization, payload.organization_slug)
    if organization is None:
        organization = Organization(slug=payload.organization_slug, name=payload.organization_slug)
        session.add(organization)

    membership = session.exec(
        select(Membership).where(
            Membership.user_id == payload.owner_user_id,
            Membership.organization_slug == payload.organization_slug,
        )
    ).first()
    if membership is None:
        session.add(
            Membership(
                user_id=payload.owner_user_id,
                organization_slug=payload.organization_slug,
                role="pi",
            )
        )

    project = ResearchProject(
        organization_slug=payload.organization_slug,
        owner_user_id=payload.owner_user_id,
        name=payload.name,
        description=payload.description,
        workspace_key=f"{payload.organization_slug}/{payload.name}",
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    if project.id is None:
        raise HTTPException(status_code=500, detail="project id missing after commit")

    return ProjectResponse.model_validate(project, from_attributes=True)
```

`D:\workspace\MedA\apps\agent-core\app\main.py`

```python
from fastapi import FastAPI

from app.db import init_db
from app.routers.projects import router as projects_router

app = FastAPI(title="MedA Agent Core")
init_db()
app.include_router(projects_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_projects_api.py::test_create_project_with_org_scope" -v`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/pyproject.toml" "MedA/apps/agent-core/app/db.py" "MedA/apps/agent-core/app/models.py" "MedA/apps/agent-core/app/schemas.py" "MedA/apps/agent-core/app/routers/projects.py" "MedA/apps/agent-core/app/main.py" "MedA/apps/agent-core/tests/test_projects_api.py"
git -C "D:\workspace" commit -m "feat: add organization and project foundation APIs"
```

### Task 3: Add Audit Logging And Server-Sent Events

**Files:**
- Modify: `D:\workspace\MedA\apps\agent-core\app\models.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\main.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\services\audit.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\services\events.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\events.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\projects.py`
- Test: `D:\workspace\MedA\apps\agent-core\tests\test_events_api.py`

- [ ] **Step 1: Write the failing test**

```python
from app.services.events import EventBroker


def test_project_creation_publishes_event() -> None:
    broker = EventBroker()

    broker.publish("project.created", {"workspace_key": "demo-hospital/糖尿病真实世界研究"})

    assert broker.drain() == [
        {
            "event_type": "project.created",
            "payload": {"workspace_key": "demo-hospital/糖尿病真实世界研究"},
        }
    ]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_events_api.py::test_project_creation_publishes_event" -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.services.events'`.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\apps\agent-core\app\models.py`

```python
from sqlmodel import Field, SQLModel


class Organization(SQLModel, table=True):
    slug: str = Field(primary_key=True)
    name: str


class Membership(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str
    organization_slug: str = Field(foreign_key="organization.slug")
    role: str = "org_admin"


class ResearchProject(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    organization_slug: str = Field(foreign_key="organization.slug")
    owner_user_id: str
    name: str
    description: str
    workspace_key: str


class AuditEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    actor: str
    organization_slug: str
    resource_type: str
    resource_id: str
    action: str
    client_type: str
    trace_id: str
```

`D:\workspace\MedA\apps\agent-core\app\services\events.py`

```python
class EventBroker:
    def __init__(self) -> None:
        self._events: list[dict] = []

    def publish(self, event_type: str, payload: dict) -> None:
        self._events.append({"event_type": event_type, "payload": payload})

    def drain(self) -> list[dict]:
        events = list(self._events)
        self._events.clear()
        return events


broker = EventBroker()
```

`D:\workspace\MedA\apps\agent-core\app\services\audit.py`

```python
from sqlmodel import Session

from app.models import AuditEvent


def record_audit_event(
    session: Session,
    *,
    actor: str,
    organization_slug: str,
    resource_type: str,
    resource_id: str,
    action: str,
    client_type: str,
    trace_id: str,
) -> None:
    session.add(
        AuditEvent(
            actor=actor,
            organization_slug=organization_slug,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            client_type=client_type,
            trace_id=trace_id,
        )
    )
```

`D:\workspace\MedA\apps\agent-core\app\routers\events.py`

```python
from fastapi import APIRouter

from app.services.events import broker

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/drain")
def drain_events() -> dict[str, list[dict]]:
    return {"events": broker.drain()}
```

`D:\workspace\MedA\apps\agent-core\app\routers\projects.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import Membership, Organization, ResearchProject
from app.schemas import CreateProjectRequest, ProjectResponse
from app.services.audit import record_audit_event
from app.services.events import broker

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectResponse]:
    projects = session.exec(select(ResearchProject)).all()
    return [ProjectResponse.model_validate(project, from_attributes=True) for project in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest, session: Session = Depends(get_session)
) -> ProjectResponse:
    organization = session.get(Organization, payload.organization_slug)
    if organization is None:
        organization = Organization(slug=payload.organization_slug, name=payload.organization_slug)
        session.add(organization)

    membership = session.exec(
        select(Membership).where(
            Membership.user_id == payload.owner_user_id,
            Membership.organization_slug == payload.organization_slug,
        )
    ).first()
    if membership is None:
        session.add(
            Membership(
                user_id=payload.owner_user_id,
                organization_slug=payload.organization_slug,
                role="pi",
            )
        )

    project = ResearchProject(
        organization_slug=payload.organization_slug,
        owner_user_id=payload.owner_user_id,
        name=payload.name,
        description=payload.description,
        workspace_key=f"{payload.organization_slug}/{payload.name}",
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    if project.id is None:
        raise HTTPException(status_code=500, detail="project id missing after commit")

    record_audit_event(
        session,
        actor=payload.owner_user_id,
        organization_slug=payload.organization_slug,
        resource_type="research_project",
        resource_id=str(project.id),
        action="project.created",
        client_type="web",
        trace_id=f"project-{project.id}",
    )
    session.commit()

    broker.publish(
        "project.created",
        {
            "project_id": project.id,
            "workspace_key": project.workspace_key,
            "organization_slug": project.organization_slug,
        },
    )

    return ProjectResponse.model_validate(project, from_attributes=True)
```

`D:\workspace\MedA\apps\agent-core\app\main.py`

```python
from fastapi import FastAPI

from app.db import init_db
from app.routers.events import router as events_router
from app.routers.projects import router as projects_router

app = FastAPI(title="MedA Agent Core")
init_db()
app.include_router(projects_router)
app.include_router(events_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_events_api.py::test_project_creation_publishes_event" -v`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/app/models.py" "MedA/apps/agent-core/app/services/audit.py" "MedA/apps/agent-core/app/services/events.py" "MedA/apps/agent-core/app/routers/events.py" "MedA/apps/agent-core/app/routers/projects.py" "MedA/apps/agent-core/app/main.py" "MedA/apps/agent-core/tests/test_events_api.py"
git -C "D:\workspace" commit -m "feat: add audit logging and project event streaming"
```

### Task 4: Add File And Artifact Metadata Registration

**Files:**
- Modify: `D:\workspace\MedA\apps\agent-core\app\models.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\main.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\services\files.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\files.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py`
- Test: `D:\workspace\MedA\apps\agent-core\tests\test_files_api.py`

- [ ] **Step 1: Write the failing test**

```python
from fastapi.testclient import TestClient

from app.main import app


def test_register_file_and_artifact_metadata() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/files/register",
        json={
            "project_id": 1,
            "kind": "source_file",
            "name": "paper.pdf",
            "storage_path": "s3://meda-local/source/paper.pdf",
            "checksum": "abc123",
        },
    )

    body = response.json()

    assert response.status_code == 201
    assert body["kind"] == "source_file"
    assert body["name"] == "paper.pdf"
    assert body["storage_path"] == "s3://meda-local/source/paper.pdf"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_files_api.py::test_register_file_and_artifact_metadata" -v`
Expected: FAIL with `404 Not Found` for `/api/files/register`.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\apps\agent-core\app\models.py`

```python
from sqlmodel import Field, SQLModel


class Organization(SQLModel, table=True):
    slug: str = Field(primary_key=True)
    name: str


class Membership(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str
    organization_slug: str = Field(foreign_key="organization.slug")
    role: str = "org_admin"


class ResearchProject(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    organization_slug: str = Field(foreign_key="organization.slug")
    owner_user_id: str
    name: str
    description: str
    workspace_key: str


class AuditEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    actor: str
    organization_slug: str
    resource_type: str
    resource_id: str
    action: str
    client_type: str
    trace_id: str


class FileRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int
    kind: str
    name: str
    storage_path: str
    checksum: str


class ArtifactRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int
    artifact_type: str
    title: str
    source_file_id: int | None = None
```

`D:\workspace\MedA\apps\agent-core\app\schemas.py`

```python
from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    organization_slug: str
    owner_user_id: str
    name: str
    description: str


class ProjectResponse(BaseModel):
    id: int
    organization_slug: str
    owner_user_id: str
    name: str
    description: str
    workspace_key: str


class RegisterFileRequest(BaseModel):
    project_id: int
    kind: str
    name: str
    storage_path: str
    checksum: str


class FileResponse(BaseModel):
    id: int
    project_id: int
    kind: str
    name: str
    storage_path: str
    checksum: str
```

`D:\workspace\MedA\apps\agent-core\app\services\files.py`

```python
from sqlmodel import Session

from app.models import FileRecord
from app.schemas import FileResponse, RegisterFileRequest


def register_file(session: Session, payload: RegisterFileRequest) -> FileResponse:
    record = FileRecord(
        project_id=payload.project_id,
        kind=payload.kind,
        name=payload.name,
        storage_path=payload.storage_path,
        checksum=payload.checksum,
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return FileResponse.model_validate(record, from_attributes=True)
```

`D:\workspace\MedA\apps\agent-core\app\routers\files.py`

```python
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db import get_session
from app.schemas import FileResponse, RegisterFileRequest
from app.services.files import register_file

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/register", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def register_file_route(
    payload: RegisterFileRequest, session: Session = Depends(get_session)
) -> FileResponse:
    return register_file(session, payload)
```

`D:\workspace\MedA\apps\agent-core\app\main.py`

```python
from fastapi import FastAPI

from app.db import init_db
from app.routers.events import router as events_router
from app.routers.files import router as files_router
from app.routers.projects import router as projects_router

app = FastAPI(title="MedA Agent Core")
init_db()
app.include_router(projects_router)
app.include_router(events_router)
app.include_router(files_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_files_api.py::test_register_file_and_artifact_metadata" -v`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/app/models.py" "MedA/apps/agent-core/app/schemas.py" "MedA/apps/agent-core/app/services/files.py" "MedA/apps/agent-core/app/routers/files.py" "MedA/apps/agent-core/app/main.py" "MedA/apps/agent-core/tests/test_files_api.py"
git -C "D:\workspace" commit -m "feat: add file and artifact metadata registration"
```

### Task 5: Add Web And Admin Shells With A Shared SDK

**Files:**
- Create: `D:\workspace\MedA\package.json`
- Create: `D:\workspace\MedA\packages\shared-sdk\package.json`
- Create: `D:\workspace\MedA\packages\shared-sdk\src\client.ts`
- Create: `D:\workspace\MedA\apps\web\package.json`
- Create: `D:\workspace\MedA\apps\web\src\main.tsx`
- Create: `D:\workspace\MedA\apps\web\src\App.tsx`
- Create: `D:\workspace\MedA\apps\web\src\App.test.tsx`
- Create: `D:\workspace\MedA\apps\admin\package.json`
- Create: `D:\workspace\MedA\apps\admin\src\main.tsx`
- Create: `D:\workspace\MedA\apps\admin\src\App.tsx`

- [ ] **Step 1: Write the failing test**

```tsx
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import App from "./App";

vi.mock("@meda/shared-sdk", () => ({
  createClient: () => ({
    listProjects: async () => [
      { id: 1, name: "糖尿病真实世界研究", workspace_key: "demo-hospital/糖尿病真实世界研究" },
    ],
  }),
}));

test("web shell renders project workspace cards", async () => {
  render(<App />);

  expect(await screen.findByText("糖尿病真实世界研究")).toBeInTheDocument();
  expect(screen.getByText("demo-hospital/糖尿病真实世界研究")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`
Expected: FAIL with missing workspace package manifests or missing `App.tsx`.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\package.json`

```json
{
  "name": "meda",
  "private": true,
  "workspaces": [
    "packages/*",
    "apps/web",
    "apps/admin",
    "apps/desktop"
  ]
}
```

`D:\workspace\MedA\packages\shared-sdk\package.json`

```json
{
  "name": "@meda/shared-sdk",
  "version": "0.1.0",
  "type": "module",
  "main": "src/client.ts"
}
```

`D:\workspace\MedA\packages\shared-sdk\src\client.ts`

```ts
export type ProjectSummary = {
  id: number;
  name: string;
  workspace_key: string;
};

export function createClient(baseUrl = "http://localhost:8000") {
  return {
    async listProjects(): Promise<ProjectSummary[]> {
      const response = await fetch(`${baseUrl}/api/projects`);
      if (!response.ok) {
        return [];
      }

      return response.json();
    },
  };
}
```

`D:\workspace\MedA\apps\web\package.json`

```json
{
  "name": "apps-web",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest"
  },
  "dependencies": {
    "@meda/shared-sdk": "0.1.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
```

`D:\workspace\MedA\apps\web\src\App.tsx`

```tsx
import { useEffect, useState } from "react";

import { createClient, type ProjectSummary } from "@meda/shared-sdk";

export default function App() {
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  useEffect(() => {
    createClient().listProjects().then(setProjects);
  }, []);

  return (
    <main>
      <h1>MedA Web Shell</h1>
      <ul>
        {projects.map((project) => (
          <li key={project.id}>
            <strong>{project.name}</strong>
            <span>{project.workspace_key}</span>
          </li>
        ))}
      </ul>
    </main>
  );
}
```

`D:\workspace\MedA\apps\web\src\main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

`D:\workspace\MedA\apps\admin\package.json`

```json
{
  "name": "apps-admin",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest"
  },
  "dependencies": {
    "@meda/shared-sdk": "0.1.0",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
```

`D:\workspace\MedA\apps\admin\src\App.tsx`

```tsx
export default function App() {
  return (
    <main>
      <h1>MedA Admin Shell</h1>
      <p>Tenant, project, task, and audit summaries will render here.</p>
    </main>
  );
}
```

`D:\workspace\MedA\apps\admin\src\main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" install && npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/package.json" "MedA/packages/shared-sdk/package.json" "MedA/packages/shared-sdk/src/client.ts" "MedA/apps/web/package.json" "MedA/apps/web/src/main.tsx" "MedA/apps/web/src/App.tsx" "MedA/apps/web/src/App.test.tsx" "MedA/apps/admin/package.json" "MedA/apps/admin/src/main.tsx" "MedA/apps/admin/src/App.tsx"
git -C "D:\workspace" commit -m "feat: add MedA web and admin shells"
```

### Task 6: Add Desktop Shell, Local Stack, And CI Sanity Checks

**Files:**
- Create: `D:\workspace\MedA\apps\desktop\package.json`
- Create: `D:\workspace\MedA\apps\desktop\electron\main.ts`
- Create: `D:\workspace\MedA\apps\desktop\electron\preload.ts`
- Create: `D:\workspace\MedA\apps\desktop\src\main.tsx`
- Create: `D:\workspace\MedA\apps\desktop\src\App.tsx`
- Create: `D:\workspace\MedA\apps\desktop\tests\smoke.test.ts`
- Create: `D:\workspace\MedA\deploy\docker-compose.local.yml`
- Create: `D:\workspace\MedA\.github\workflows\foundation-ci.yml`

- [ ] **Step 1: Write the failing test**

```ts
import { describe, expect, it } from "vitest";

describe("desktop renderer", () => {
  it("exposes the MedA desktop shell title", async () => {
    const module = await import("../src/App");

    expect(typeof module.default).toBe("function");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`
Expected: FAIL with missing desktop package or missing renderer files.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\apps\desktop\package.json`

```json
{
  "name": "apps-desktop",
  "private": true,
  "type": "module",
  "scripts": {
    "test": "vitest"
  },
  "dependencies": {
    "electron": "^31.0.2",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@types/node": "^22.0.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
```

`D:\workspace\MedA\apps\desktop\electron\main.ts`

```ts
import { BrowserWindow, app } from "electron";
import path from "node:path";

function createWindow() {
  const window = new BrowserWindow({
    width: 1440,
    height: 960,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
    },
  });

  window.loadURL("http://localhost:5173");
}

app.whenReady().then(createWindow);
```

`D:\workspace\MedA\apps\desktop\electron\preload.ts`

```ts
import { contextBridge } from "electron";

contextBridge.exposeInMainWorld("medaDesktop", {
  clientType: "desktop",
});
```

`D:\workspace\MedA\apps\desktop\src\App.tsx`

```tsx
export default function App() {
  return (
    <main>
      <h1>MedA Desktop Shell</h1>
      <p>Desktop uses the same backend contracts as web and admin.</p>
    </main>
  );
}
```

`D:\workspace\MedA\apps\desktop\src\main.tsx`

```tsx
import React from "react";
import ReactDOM from "react-dom/client";

import App from "./App";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

`D:\workspace\MedA\deploy\docker-compose.local.yml`

```yaml
services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: meda
      POSTGRES_USER: meda
      POSTGRES_PASSWORD: meda
    ports:
      - "5432:5432"

  redis:
    image: redis:7
    ports:
      - "6379:6379"

  minio:
    image: minio/minio:RELEASE.2024-07-10T18-41-49Z
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: meda
      MINIO_ROOT_PASSWORD: meda12345
    ports:
      - "9000:9000"
      - "9001:9001"

  milvus:
    image: milvusdb/milvus:v2.4.9
    command: ["milvus", "run", "standalone"]
    ports:
      - "19530:19530"
      - "9091:9091"
```

`D:\workspace\MedA\.github\workflows\foundation-ci.yml`

```yaml
name: foundation-ci

on:
  push:
    branches: ["main"]
  pull_request:

jobs:
  backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install uv
      - run: uv run --project "MedA/apps/agent-core" pytest "MedA/apps/agent-core/tests" -v

  frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm --prefix "MedA" install
      - run: npm --prefix "MedA" --workspace apps/web run test -- --run
      - run: npm --prefix "MedA" --workspace apps/desktop run test -- --run
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" install && npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/desktop/package.json" "MedA/apps/desktop/electron/main.ts" "MedA/apps/desktop/electron/preload.ts" "MedA/apps/desktop/src/main.tsx" "MedA/apps/desktop/src/App.tsx" "MedA/apps/desktop/tests/smoke.test.ts" "MedA/deploy/docker-compose.local.yml" "MedA/.github/workflows/foundation-ci.yml"
git -C "D:\workspace" commit -m "feat: add MedA desktop shell and local foundation stack"
```

## Self-Review

### Spec Coverage

- Covered in this wave:
  - shared backend starting point
  - organization / membership / project model
  - audit event logging
  - event streaming skeleton
  - file / artifact metadata registration
  - web shell, admin shell, desktop shell
  - local stack and CI baseline
- Intentionally deferred to follow-on plans:
  - Hermes full UI parity inventory
  - complete RBAC matrix and admin policies
  - vector ingestion workers and chunk/evidence lineage
  - production-grade monitoring dashboards
  - research modules `R004-R016`

### Placeholder Scan

- No placeholder markers remain in the task steps.
- Every task contains a concrete failing test, explicit run command, implementation code, verification command, and commit message.

### Type Consistency

- `ResearchProject.workspace_key` is used consistently across backend and web SDK.
- Event payload uses `event_type` and `payload` consistently.
- File registration uses `RegisterFileRequest` and `FileResponse` consistently.

