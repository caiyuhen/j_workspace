# MedA Auth And Workspace Wave 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the second MedA platform slice so Web, Admin, and Desktop can share a real login session, resolve organization-scoped roles, and enter the same protected project workspace shell.

**Architecture:** Extend the existing FastAPI `agent-core` with explicit `User`, `AuthSession`, and role-aware session resolution. Keep auth intentionally simple for this wave: a dev-login endpoint issues a bearer token persisted by the shared SDK, and all three clients reuse the same session bootstrap flow before rendering their protected shells.

**Tech Stack:** Python 3.12, FastAPI, SQLModel, React 18, TypeScript, Electron, Vitest, pytest

---

## Scope Note

This wave is intentionally narrower than the full Hermes parity track. It only covers the next independently testable foundation layer:

- session-based login bootstrap
- current-user and current-organization resolution
- role-aware backend guards
- protected project workspace shell in Web
- protected operator shell in Admin
- protected project shell in Desktop
- shared SDK helpers for session storage and authenticated requests

This wave explicitly does **not** include:

- Hermes 1:1 visual parity
- SSO / OAuth / enterprise IdP integration
- full fine-grained RBAC matrix
- invitation flows
- password reset, MFA, or production security hardening
- research module pages

## File Structure

### Repository Layout

- Modify: `D:\workspace\MedA\apps\agent-core\app\models.py` - add `User` and `AuthSession` persistence models
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py` - add auth/session request and response schemas
- Modify: `D:\workspace\MedA\apps\agent-core\app\db.py` - add test reset helper for deterministic API tests
- Modify: `D:\workspace\MedA\apps\agent-core\app\main.py` - register auth router and keep startup initialization centralized
- Create: `D:\workspace\MedA\apps\agent-core\app\deps\auth.py` - resolve session token and enforce roles
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\auth.py` - dev login and current-session endpoints
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\projects.py` - require authenticated session for listing projects
- Create: `D:\workspace\MedA\apps\agent-core\app\services\auth.py` - create users, memberships, and bearer sessions
- Create: `D:\workspace\MedA\apps\agent-core\tests\conftest.py` - reset in-memory database between tests
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_auth_api.py` - login and session bootstrap tests
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_workspace_authz.py` - authenticated project listing tests
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\client.ts` - add token-aware client and auth helpers
- Create: `D:\workspace\MedA\packages\shared-sdk\src\session.ts` - token storage and bootstrap helpers
- Create: `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts` - session store test
- Modify: `D:\workspace\MedA\packages\shared-sdk\package.json` - export session helpers
- Modify: `D:\workspace\MedA\apps\web\package.json` - add React Router if needed by workspace shell
- Modify: `D:\workspace\MedA\apps\web\src\App.tsx` - switch from raw project list to guarded app shell
- Create: `D:\workspace\MedA\apps\web\src/components\LoginForm.tsx` - login form for Web
- Create: `D:\workspace\MedA\apps\web\src/components\WorkspaceShell.tsx` - authenticated workspace shell for Web
- Modify: `D:\workspace\MedA\apps\web\src\App.test.tsx` - test login-to-workspace render path
- Modify: `D:\workspace\MedA\apps\admin\package.json` - add jsdom-compatible admin test deps
- Modify: `D:\workspace\MedA\apps\admin\src\App.tsx` - add admin session gate and role check
- Create: `D:\workspace\MedA\apps\admin\src/App.test.tsx` - test admin role gate behavior
- Create: `D:\workspace\MedA\apps\admin\src\test-setup.ts` - admin test setup
- Create: `D:\workspace\MedA\apps\admin\tsconfig.json` - admin TypeScript config
- Create: `D:\workspace\MedA\apps\admin\vitest.config.ts` - admin jsdom test config
- Modify: `D:\workspace\MedA\apps\desktop\src\App.tsx` - add desktop session gate and shared workspace shell
- Create: `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx` - test desktop login gate behavior
- Modify: `D:\workspace\MedA\apps\desktop\package.json` - add jsdom test support for renderer auth tests
- Modify: `D:\workspace\MedA\apps\desktop\vitest.config.ts` - switch renderer tests to jsdom
- Create: `D:\workspace\MedA\apps\desktop\src\test-setup.ts` - desktop renderer test setup

---

### Task 1: Add Session Models And Dev Login API

**Files:**
- Modify: `D:\workspace\MedA\apps\agent-core\app\models.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\db.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\main.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\services\auth.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\auth.py`
- Create: `D:\workspace\MedA\apps\agent-core\tests\conftest.py`
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_auth_api.py`

- [ ] **Step 1: Write the failing test**

`D:\workspace\MedA\apps\agent-core\tests\conftest.py`

```python
from collections.abc import Generator

import pytest

from app.db import init_db, reset_db


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    reset_db()
    init_db()
    yield
```

`D:\workspace\MedA\apps\agent-core\tests\test_auth_api.py`

```python
from fastapi.testclient import TestClient

from app.main import app


def test_dev_login_creates_session_and_returns_context() -> None:
    client = TestClient(app)

    response = client.post(
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

    body = response.json()

    assert response.status_code == 200
    assert body["token"].startswith("meda_")
    assert body["user"]["user_id"] == "u-001"
    assert body["user"]["display_name"] == "Dr. Chen"
    assert body["organization"]["slug"] == "demo-hospital"
    assert body["role"] == "org_admin"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_auth_api.py::test_dev_login_creates_session_and_returns_context" -v`
Expected: FAIL with `404 Not Found` for `/api/auth/dev-login` or import errors for missing auth modules.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\apps\agent-core\app\models.py`

```python
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    display_name: str


class Organization(SQLModel, table=True):
    slug: str = Field(primary_key=True)
    name: str


class Membership(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
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


class AuthSession(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
    organization_slug: str = Field(foreign_key="organization.slug")
    role: str
    client_type: str
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


class DevLoginRequest(BaseModel):
    organization_slug: str
    organization_name: str
    user_id: str
    display_name: str
    role: str
    client_type: str


class SessionUserResponse(BaseModel):
    user_id: str
    display_name: str


class SessionOrganizationResponse(BaseModel):
    slug: str
    name: str


class SessionResponse(BaseModel):
    token: str
    user: SessionUserResponse
    organization: SessionOrganizationResponse
    role: str
    client_type: str
```

`D:\workspace\MedA\apps\agent-core\app\db.py`

```python
from collections.abc import Generator

from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
```

`D:\workspace\MedA\apps\agent-core\app\services\auth.py`

```python
from uuid import uuid4

from sqlmodel import Session, select

from app.models import AuthSession, Membership, Organization, User
from app.schemas import (
    DevLoginRequest,
    SessionOrganizationResponse,
    SessionResponse,
    SessionUserResponse,
)


def login_with_dev_session(session: Session, payload: DevLoginRequest) -> SessionResponse:
    user = session.get(User, payload.user_id)
    if user is None:
        user = User(user_id=payload.user_id, display_name=payload.display_name)
        session.add(user)
    else:
        user.display_name = payload.display_name

    organization = session.get(Organization, payload.organization_slug)
    if organization is None:
        organization = Organization(
            slug=payload.organization_slug,
            name=payload.organization_name,
        )
        session.add(organization)
    else:
        organization.name = payload.organization_name

    membership = session.exec(
        select(Membership).where(
            Membership.user_id == payload.user_id,
            Membership.organization_slug == payload.organization_slug,
        )
    ).first()
    if membership is None:
        membership = Membership(
            user_id=payload.user_id,
            organization_slug=payload.organization_slug,
            role=payload.role,
        )
        session.add(membership)
    else:
        membership.role = payload.role

    token = f"meda_{uuid4().hex}"
    auth_session = AuthSession(
        token=token,
        user_id=payload.user_id,
        organization_slug=payload.organization_slug,
        role=payload.role,
        client_type=payload.client_type,
    )
    session.add(auth_session)
    session.commit()

    return SessionResponse(
        token=token,
        user=SessionUserResponse(
            user_id=payload.user_id,
            display_name=payload.display_name,
        ),
        organization=SessionOrganizationResponse(
            slug=payload.organization_slug,
            name=payload.organization_name,
        ),
        role=payload.role,
        client_type=payload.client_type,
    )
```

`D:\workspace\MedA\apps\agent-core\app\routers\auth.py`

```python
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas import DevLoginRequest, SessionResponse
from app.services.auth import login_with_dev_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/dev-login", response_model=SessionResponse)
def dev_login(
    payload: DevLoginRequest, session: Session = Depends(get_session)
) -> SessionResponse:
    return login_with_dev_session(session, payload)
```

`D:\workspace\MedA\apps\agent-core\app\main.py`

```python
from fastapi import FastAPI

from app.db import init_db
from app.routers.auth import router as auth_router
from app.routers.events import router as events_router
from app.routers.files import router as files_router
from app.routers.projects import router as projects_router

app = FastAPI(title="MedA Agent Core")
init_db()
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(events_router)
app.include_router(files_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_auth_api.py::test_dev_login_creates_session_and_returns_context" -v`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/app/models.py" "MedA/apps/agent-core/app/schemas.py" "MedA/apps/agent-core/app/db.py" "MedA/apps/agent-core/app/main.py" "MedA/apps/agent-core/app/services/auth.py" "MedA/apps/agent-core/app/routers/auth.py" "MedA/apps/agent-core/tests/conftest.py" "MedA/apps/agent-core/tests/test_auth_api.py"
git -C "D:\workspace" commit -m "feat: add MedA dev login and session models"
```

### Task 2: Resolve Current Session And Guard Project Listing

**Files:**
- Create: `D:\workspace\MedA\apps\agent-core\app\deps\auth.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\auth.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\projects.py`
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_workspace_authz.py`

- [ ] **Step 1: Write the failing test**

`D:\workspace\MedA\apps\agent-core\tests\test_workspace_authz.py`

```python
from fastapi.testclient import TestClient

from app.main import app


def test_project_list_requires_session_and_returns_org_scoped_projects() -> None:
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

    client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "Wave 2 auth workspace test",
        },
    )

    unauthorized = client.get("/api/projects")
    authorized = client.get(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json()[0]["workspace_key"] == "demo-hospital/糖尿病真实世界研究"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_workspace_authz.py::test_project_list_requires_session_and_returns_org_scoped_projects" -v`
Expected: FAIL because `/api/projects` currently returns `200` without a session.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\apps\agent-core\app\deps\auth.py`

```python
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.models import AuthSession, Organization, User


@dataclass
class SessionContext:
    token: str
    user_id: str
    display_name: str
    organization_slug: str
    organization_name: str
    role: str
    client_type: str


def get_current_session(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> SessionContext:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")

    token = authorization.replace("Bearer ", "", 1)
    auth_session = session.get(AuthSession, token)
    if auth_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session")

    user = session.get(User, auth_session.user_id)
    organization = session.get(Organization, auth_session.organization_slug)
    if user is None or organization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session context missing")

    return SessionContext(
        token=auth_session.token,
        user_id=user.user_id,
        display_name=user.display_name,
        organization_slug=organization.slug,
        organization_name=organization.name,
        role=auth_session.role,
        client_type=auth_session.client_type,
    )


def require_admin(context: SessionContext = Depends(get_current_session)) -> SessionContext:
    if context.role not in {"org_admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin role required")

    return context
```

`D:\workspace\MedA\apps\agent-core\app\routers\auth.py`

```python
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.schemas import DevLoginRequest, SessionOrganizationResponse, SessionResponse, SessionUserResponse
from app.services.auth import login_with_dev_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/dev-login", response_model=SessionResponse)
def dev_login(
    payload: DevLoginRequest, session: Session = Depends(get_session)
) -> SessionResponse:
    return login_with_dev_session(session, payload)


@router.get("/me", response_model=SessionResponse)
def get_me(context: SessionContext = Depends(get_current_session)) -> SessionResponse:
    return SessionResponse(
        token=context.token,
        user=SessionUserResponse(
            user_id=context.user_id,
            display_name=context.display_name,
        ),
        organization=SessionOrganizationResponse(
            slug=context.organization_slug,
            name=context.organization_name,
        ),
        role=context.role,
        client_type=context.client_type,
    )
```

`D:\workspace\MedA\apps\agent-core\app\routers\projects.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.models import Membership, Organization, ResearchProject
from app.schemas import CreateProjectRequest, ProjectResponse
from app.services.audit import record_audit_event
from app.services.events import broker

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> list[ProjectResponse]:
    projects = session.exec(
        select(ResearchProject).where(
            ResearchProject.organization_slug == context.organization_slug
        )
    ).all()
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

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_workspace_authz.py::test_project_list_requires_session_and_returns_org_scoped_projects" -v`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/app/deps/auth.py" "MedA/apps/agent-core/app/routers/auth.py" "MedA/apps/agent-core/app/routers/projects.py" "MedA/apps/agent-core/tests/test_workspace_authz.py"
git -C "D:\workspace" commit -m "feat: guard MedA project workspace with sessions"
```

### Task 3: Add Shared Session SDK For Browser And Desktop Clients

**Files:**
- Modify: `D:\workspace\MedA\packages\shared-sdk\package.json`
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\client.ts`
- Create: `D:\workspace\MedA\packages\shared-sdk\src\session.ts`

- [ ] **Step 1: Write the failing test**

Create: `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts`

```ts
import { describe, expect, it } from "vitest";

import { createMemorySessionStore } from "./session";

describe("session store", () => {
  it("persists and clears bearer tokens", () => {
    const store = createMemorySessionStore();

    expect(store.getToken()).toBeNull();

    store.setToken("meda_token");
    expect(store.getToken()).toBe("meda_token");

    store.clearToken();
    expect(store.getToken()).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run "src/session.test.ts"`
Expected: FAIL because `src/session.ts` does not exist.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\packages\shared-sdk\package.json`

```json
{
  "name": "@meda/shared-sdk",
  "version": "0.1.0",
  "type": "module",
  "main": "src/client.ts",
  "exports": {
    ".": "./src/client.ts",
    "./session": "./src/session.ts"
  },
  "devDependencies": {
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
```

`D:\workspace\MedA\packages\shared-sdk\src\session.ts`

```ts
export type SessionStore = {
  getToken(): string | null;
  setToken(token: string): void;
  clearToken(): void;
};

export function createMemorySessionStore(initialToken: string | null = null): SessionStore {
  let token = initialToken;

  return {
    getToken() {
      return token;
    },
    setToken(nextToken: string) {
      token = nextToken;
    },
    clearToken() {
      token = null;
    },
  };
}

export function createBrowserSessionStore(key = "meda.session.token"): SessionStore {
  return {
    getToken() {
      return window.localStorage.getItem(key);
    },
    setToken(token: string) {
      window.localStorage.setItem(key, token);
    },
    clearToken() {
      window.localStorage.removeItem(key);
    },
  };
}
```

`D:\workspace\MedA\packages\shared-sdk\src\client.ts`

```ts
import type { SessionStore } from "./session";
export { createBrowserSessionStore, createMemorySessionStore } from "./session";

export type ProjectSummary = {
  id: number;
  name: string;
  workspace_key: string;
};

export type SessionContext = {
  token: string;
  user: { user_id: string; display_name: string };
  organization: { slug: string; name: string };
  role: string;
  client_type: string;
};

export type DevLoginPayload = {
  organization_slug: string;
  organization_name: string;
  user_id: string;
  display_name: string;
  role: string;
  client_type: string;
};

export function createClient(
  baseUrl = "http://localhost:8000",
  sessionStore?: SessionStore,
) {
  const buildHeaders = () => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const token = sessionStore?.getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  };

  return {
    async devLogin(payload: DevLoginPayload): Promise<SessionContext> {
      const response = await fetch(`${baseUrl}/api/auth/dev-login`, {
        method: "POST",
        headers: buildHeaders(),
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "login failed");
      }

      sessionStore?.setToken(data.token);
      return data;
    },

    async getMe(): Promise<SessionContext> {
      const response = await fetch(`${baseUrl}/api/auth/me`, {
        headers: buildHeaders(),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "session bootstrap failed");
      }

      return data;
    },

    async listProjects(): Promise<ProjectSummary[]> {
      const response = await fetch(`${baseUrl}/api/projects`, {
        headers: buildHeaders(),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "project list failed");
      }

      return data;
    },
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run "src/session.test.ts"`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/packages/shared-sdk/package.json" "MedA/packages/shared-sdk/src/client.ts" "MedA/packages/shared-sdk/src/session.ts" "MedA/packages/shared-sdk/src/session.test.ts"
git -C "D:\workspace" commit -m "feat: add shared session helpers for MedA clients"
```

### Task 4: Render Web Login And Protected Workspace Shell

**Files:**
- Modify: `D:\workspace\MedA\apps\web\package.json`
- Modify: `D:\workspace\MedA\apps\web\src\App.tsx`
- Create: `D:\workspace\MedA\apps\web\src/components\LoginForm.tsx`
- Create: `D:\workspace\MedA\apps\web\src/components\WorkspaceShell.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\App.test.tsx`

- [ ] **Step 1: Write the failing test**

`D:\workspace\MedA\apps\web\src\App.test.tsx`

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "./App";

const sessionStore = {
  getToken: vi.fn(() => null),
  setToken: vi.fn(),
  clearToken: vi.fn(),
};

const devLogin = vi.fn(async () => ({
  token: "meda_token",
  user: { user_id: "u-001", display_name: "Dr. Chen" },
  organization: { slug: "demo-hospital", name: "Demo Hospital" },
  role: "org_admin",
  client_type: "web",
}));

const listProjects = vi.fn(async () => [
  {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
  },
]);

vi.mock("@meda/shared-sdk", () => ({
  createBrowserSessionStore: () => sessionStore,
  createClient: () => ({
    devLogin,
    listProjects,
    getMe: vi.fn(),
  }),
}));

test("web shell logs in and renders the protected workspace", async () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("机构标识"), {
    target: { value: "demo-hospital" },
  });
  fireEvent.change(screen.getByLabelText("用户编号"), {
    target: { value: "u-001" },
  });
  fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));

  expect(await screen.findByText("欢迎，Dr. Chen")).toBeInTheDocument();
  expect(await screen.findByText("糖尿病真实世界研究")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`
Expected: FAIL because the current app has no login form or protected shell.

- [ ] **Step 3: Write minimal implementation**

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
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^24.1.1",
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
```

`D:\workspace\MedA\apps\web\src\components\LoginForm.tsx`

```tsx
import { FormEvent, useState } from "react";

type LoginFormProps = {
  onSubmit(payload: { organizationSlug: string; userId: string }): Promise<void>;
};

export function LoginForm({ onSubmit }: LoginFormProps) {
  const [organizationSlug, setOrganizationSlug] = useState("demo-hospital");
  const [userId, setUserId] = useState("u-001");

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    await onSubmit({ organizationSlug, userId });
  };

  return (
    <form onSubmit={handleSubmit}>
      <label>
        机构标识
        <input
          aria-label="机构标识"
          value={organizationSlug}
          onChange={(event) => setOrganizationSlug(event.target.value)}
        />
      </label>
      <label>
        用户编号
        <input
          aria-label="用户编号"
          value={userId}
          onChange={(event) => setUserId(event.target.value)}
        />
      </label>
      <button type="submit">进入工作台</button>
    </form>
  );
}
```

`D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx`

```tsx
import type { ProjectSummary, SessionContext } from "@meda/shared-sdk";

type WorkspaceShellProps = {
  session: SessionContext;
  projects: ProjectSummary[];
};

export function WorkspaceShell({ session, projects }: WorkspaceShellProps) {
  return (
    <main>
      <h1>欢迎，{session.user.display_name}</h1>
      <p>
        当前机构：{session.organization.name} ({session.organization.slug})
      </p>
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

`D:\workspace\MedA\apps\web\src\App.tsx`

```tsx
import { useMemo, useState } from "react";

import {
  createBrowserSessionStore,
  createClient,
  type ProjectSummary,
  type SessionContext,
} from "@meda/shared-sdk";

import { LoginForm } from "./components/LoginForm";
import { WorkspaceShell } from "./components/WorkspaceShell";

export default function App() {
  const sessionStore = useMemo(() => createBrowserSessionStore(), []);
  const client = useMemo(() => createClient("http://localhost:8000", sessionStore), [sessionStore]);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  const handleLogin = async (payload: { organizationSlug: string; userId: string }) => {
    const nextSession = await client.devLogin({
      organization_slug: payload.organizationSlug,
      organization_name: "Demo Hospital",
      user_id: payload.userId,
      display_name: "Dr. Chen",
      role: "org_admin",
      client_type: "web",
    });
    const nextProjects = await client.listProjects();

    setSession(nextSession);
    setProjects(nextProjects);
  };

  if (session === null) {
    return <LoginForm onSubmit={handleLogin} />;
  }

  return <WorkspaceShell session={session} projects={projects} />;
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/web/package.json" "MedA/apps/web/src/App.tsx" "MedA/apps/web/src/App.test.tsx" "MedA/apps/web/src/components/LoginForm.tsx" "MedA/apps/web/src/components/WorkspaceShell.tsx"
git -C "D:\workspace" commit -m "feat: add MedA web login and workspace shell"
```

### Task 5: Gate Admin And Desktop Shells With Shared Session Context

**Files:**
- Modify: `D:\workspace\MedA\apps\admin\package.json`
- Modify: `D:\workspace\MedA\apps\admin\src\App.tsx`
- Create: `D:\workspace\MedA\apps\admin\src\App.test.tsx`
- Create: `D:\workspace\MedA\apps\admin\src\test-setup.ts`
- Create: `D:\workspace\MedA\apps\admin\tsconfig.json`
- Create: `D:\workspace\MedA\apps\admin\vitest.config.ts`
- Modify: `D:\workspace\MedA\apps\desktop\package.json`
- Modify: `D:\workspace\MedA\apps\desktop\vitest.config.ts`
- Modify: `D:\workspace\MedA\apps\desktop\src\App.tsx`
- Create: `D:\workspace\MedA\apps\desktop\src\test-setup.ts`
- Create: `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx`

- [ ] **Step 1: Write the failing tests**

`D:\workspace\MedA\apps\admin\src\App.test.tsx`

```tsx
import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "./App";

vi.mock("@meda/shared-sdk", () => ({
  createBrowserSessionStore: () => ({ getToken: () => "meda_token" }),
  createClient: () => ({
    getMe: async () => ({
      token: "meda_token",
      user: { user_id: "u-001", display_name: "Ops Lead" },
      organization: { slug: "demo-hospital", name: "Demo Hospital" },
      role: "org_admin",
      client_type: "admin",
    }),
  }),
}));

test("admin app renders operator shell for admin role", async () => {
  render(<App />);

  expect(await screen.findByText("MedA Admin Shell")).toBeInTheDocument();
  expect(screen.getByText("Ops Lead")).toBeInTheDocument();
});
```

`D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx`

```tsx
import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "../src/App";

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
      {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
      },
    ],
  }),
}));

test("desktop app renders authenticated workspace shell", async () => {
  render(<App />);

  expect(await screen.findByText("MedA Desktop Shell")).toBeInTheDocument();
  expect(screen.getByText("糖尿病真实世界研究")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/admin run test -- --run`
Expected: FAIL because the admin app has no authenticated shell.

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`
Expected: FAIL because the desktop app has no session bootstrap or renderer test setup.

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
    "@meda/shared-sdk": "0.1.0",
    "electron": "^31.0.2",
    "react": "^18.3.1",
    "react-dom": "^18.3.1"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.0.0",
    "@types/node": "^22.0.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^24.1.1",
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
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
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.0.0",
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "jsdom": "^24.1.1",
    "typescript": "^5.5.4",
    "vitest": "^2.0.5"
  }
}
```

`D:\workspace\MedA\apps\admin\src\test-setup.ts`

```ts
import "@testing-library/jest-dom/vitest";
```

`D:\workspace\MedA\apps\admin\tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "jsx": "react-jsx",
    "strict": true,
    "esModuleInterop": true,
    "types": ["vitest/globals"]
  },
  "include": ["src", "vitest.config.ts"]
}
```

`D:\workspace\MedA\apps\admin\vitest.config.ts`

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
  },
});
```

`D:\workspace\MedA\apps\admin\src\App.tsx`

```tsx
import { useEffect, useMemo, useState } from "react";

import { createBrowserSessionStore, createClient, type SessionContext } from "@meda/shared-sdk";

export default function App() {
  const sessionStore = useMemo(() => createBrowserSessionStore(), []);
  const client = useMemo(() => createClient("http://localhost:8000", sessionStore), [sessionStore]);
  const [session, setSession] = useState<SessionContext | null>(null);

  useEffect(() => {
    client.getMe().then(setSession).catch(() => setSession(null));
  }, [client]);

  if (session === null) {
    return <main>Admin session unavailable.</main>;
  }

  if (!["org_admin", "super_admin"].includes(session.role)) {
    return <main>Admin role required.</main>;
  }

  return (
    <main>
      <h1>MedA Admin Shell</h1>
      <p>{session.user.display_name}</p>
      <p>{session.organization.name}</p>
    </main>
  );
}
```

`D:\workspace\MedA\apps\desktop\src\App.tsx`

```tsx
import { useEffect, useMemo, useState } from "react";

import {
  createClient,
  createMemorySessionStore,
  type ProjectSummary,
  type SessionContext,
} from "@meda/shared-sdk";

export default function App() {
  const sessionStore = useMemo(() => createMemorySessionStore("meda_token"), []);
  const client = useMemo(() => createClient("http://localhost:8000", sessionStore), [sessionStore]);
  const [session, setSession] = useState<SessionContext | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);

  useEffect(() => {
    client
      .getMe()
      .then(async (nextSession) => {
        setSession(nextSession);
        setProjects(await client.listProjects());
      })
      .catch(() => {
        setSession(null);
        setProjects([]);
      });
  }, [client]);

  if (session === null) {
    return <main>Desktop session unavailable.</main>;
  }

  return (
    <main>
      <h1>MedA Desktop Shell</h1>
      <p>{session.user.display_name}</p>
      <ul>
        {projects.map((project) => (
          <li key={project.id}>{project.name}</li>
        ))}
      </ul>
    </main>
  );
}
```

`D:\workspace\MedA\apps\desktop\src\test-setup.ts`

```ts
import "@testing-library/jest-dom/vitest";
```

`D:\workspace\MedA\apps\desktop\vitest.config.ts`

```ts
import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
  },
});
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/admin run test -- --run`
Expected: PASS with `1 passed`.

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`
Expected: PASS with `2 passed` across the smoke and auth renderer tests.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/admin/package.json" "MedA/apps/admin/src/App.tsx" "MedA/apps/admin/src/App.test.tsx" "MedA/apps/admin/src/test-setup.ts" "MedA/apps/admin/tsconfig.json" "MedA/apps/admin/vitest.config.ts" "MedA/apps/desktop/package.json" "MedA/apps/desktop/src/App.tsx" "MedA/apps/desktop/src/test-setup.ts" "MedA/apps/desktop/tests/app-auth.test.tsx" "MedA/apps/desktop/vitest.config.ts"
git -C "D:\workspace" commit -m "feat: gate MedA admin and desktop shells with session context"
```

## Self-Review

### Spec Coverage

- Covered in this wave:
  - shared login bootstrap
  - session token persistence helpers
  - current user / organization context
  - authenticated project listing
  - protected Web workspace shell
  - admin role gate
  - desktop session bootstrap
- Deferred to later:
  - full Hermes visual parity
  - enterprise auth
  - production security hardening
  - fine-grained permissions beyond the starter role gate

### Placeholder Scan

- No placeholder markers remain in the task steps.
- Every task contains concrete test code, exact commands, implementation code, and commit commands.

### Type Consistency

- Session payloads consistently use `token`, `user`, `organization`, `role`, and `client_type`.
- Shared SDK uses the same `SessionContext` shape across Web, Admin, and Desktop.
- Project shells consistently consume `ProjectSummary.workspace_key`.
