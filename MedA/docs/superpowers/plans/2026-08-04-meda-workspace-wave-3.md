# MedA Workspace Wave 3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first Hermes-style MedA project workspace slice so authenticated Web and Desktop users can enter a three-column workspace home, see project-scoped summary data, and navigate to task, artifact, and research-stage entry pages from the same project context.

**Architecture:** Extend the existing FastAPI `agent-core` with a minimal project workspace summary API and dedicated response schemas instead of hard-coding dashboard data in the clients. Keep the frontend implementation narrow for this wave: evolve the current protected shells into a shared information architecture with a left navigation rail, project context sidebar, `C1` mixed home in the main column, and a right rail for assistant and todo blocks, plus skeletal route targets for recent tasks, recent artifacts, and research-stage entry pages.

**Tech Stack:** Python 3.12, FastAPI, SQLModel, React 18, TypeScript, Electron, Vitest, pytest

---

## Scope Note

This wave implements the first independently testable workspace experience that matches the approved design:

- Hermes-style three-column workspace shell
- project-scoped workspace home summary API
- `C1` mixed homepage in Web
- same information architecture in Desktop
- recent task / recent artifact / stage-entry navigation handoff pages
- right-rail assistant and todo panels

This wave explicitly does **not** include:

- deep implementation of every research module
- full Hermes pixel-perfect parity across all pages
- admin console expansion
- heavy dashboard analytics
- rich editors, data grids, or full report editing from the home page

## File Structure

### Repository Layout

- Modify: `D:\workspace\MedA\apps\agent-core\app\models.py` - add minimal workspace-facing records for project tasks and project artifacts metadata used by the homepage
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py` - add workspace summary request/response schemas and handoff page payload shapes
- Create: `D:\workspace\MedA\apps\agent-core\app\services\workspace.py` - build project-scoped workspace summary responses from stored records
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\workspace.py` - authenticated workspace summary endpoint
- Modify: `D:\workspace\MedA\apps\agent-core\app\main.py` - register the workspace router
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_workspace_home_api.py` - verify summary payload and project scoping
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\client.ts` - add typed workspace-summary fetch helper
- Modify: `D:\workspace\MedA\apps\web\src\App.tsx` - bootstrap selected project and fetch workspace summary after login
- Modify: `D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx` - render the three-column Hermes-style shell and simple handoff pages
- Modify: `D:\workspace\MedA\apps\web\src\App.test.tsx` - verify workspace home sections and navigation handoff
- Modify: `D:\workspace\MedA\apps\desktop\src\App.tsx` - render the same information architecture with project summary data
- Modify: `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx` - verify Desktop workspace sections and navigation handoff

---

### Task 1: Add Project Workspace Summary API

**Files:**
- Modify: `D:\workspace\MedA\apps\agent-core\app\models.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\services\workspace.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\routers\workspace.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\main.py`
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_workspace_home_api.py`

- [ ] **Step 1: Write the failing test**

`D:\workspace\MedA\apps\agent-core\tests\test_workspace_home_api.py`

```python
from fastapi.testclient import TestClient

from app.main import app


def test_workspace_home_returns_project_scoped_summary() -> None:
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
            "description": "Wave 3 workspace summary",
        },
    )
    project_id = project.json()["id"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/home",
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["project"]["id"] == project_id
    assert body["project"]["name"] == "糖尿病真实世界研究"
    assert body["project"]["current_stage"] == "方案设计"
    assert body["hero_cta"]["label"] == "继续上次研究"
    assert body["stages"][0]["key"] == "topic"
    assert body["recent_tasks"][0]["title"] == "完善纳排标准草案"
    assert body["recent_artifacts"][0]["title"] == "方案初稿 v0.3"
    assert body["assistant"]["headline"] == "MedA 助手建议"
    assert body["todos"][0]["title"] == "确认研究终点定义"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_workspace_home_api.py::test_workspace_home_returns_project_scoped_summary" -v`
Expected: FAIL with `404 Not Found` for `/api/workspace/projects/.../home`.

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


class ResearchTaskRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    title: str
    stage_key: str
    status: str


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


class WorkspaceHeroAction(BaseModel):
    label: str
    target: str


class WorkspaceStageSummary(BaseModel):
    key: str
    label: str
    status: str
    task_count: int
    artifact_count: int
    target: str


class WorkspaceItemSummary(BaseModel):
    title: str
    subtitle: str
    target: str


class WorkspaceAssistantSummary(BaseModel):
    headline: str
    primary_action_label: str
    primary_action_target: str


class WorkspaceProjectSummary(BaseModel):
    id: int
    name: str
    workspace_key: str
    current_stage: str
    updated_at_label: str


class WorkspaceHomeResponse(BaseModel):
    project: WorkspaceProjectSummary
    hero_cta: WorkspaceHeroAction
    stages: list[WorkspaceStageSummary]
    recent_tasks: list[WorkspaceItemSummary]
    recent_artifacts: list[WorkspaceItemSummary]
    activity: list[WorkspaceItemSummary]
    assistant: WorkspaceAssistantSummary
    todos: list[WorkspaceItemSummary]
```

`D:\workspace\MedA\apps\agent-core\app\services\workspace.py`

```python
from sqlmodel import Session, select

from app.models import ArtifactRecord, ResearchProject, ResearchTaskRecord
from app.schemas import (
    WorkspaceAssistantSummary,
    WorkspaceHeroAction,
    WorkspaceHomeResponse,
    WorkspaceItemSummary,
    WorkspaceProjectSummary,
    WorkspaceStageSummary,
)

STAGE_DEFINITIONS = [
    ("topic", "选题", "done"),
    ("search", "检索", "done"),
    ("screening", "筛选", "in_progress"),
    ("extraction", "抽取", "pending"),
    ("analysis", "分析", "pending"),
    ("output", "产出", "pending"),
]


def build_workspace_home(session: Session, project: ResearchProject) -> WorkspaceHomeResponse:
    tasks = session.exec(
        select(ResearchTaskRecord).where(ResearchTaskRecord.project_id == project.id)
    ).all()
    artifacts = session.exec(
        select(ArtifactRecord).where(ArtifactRecord.project_id == project.id)
    ).all()

    if not tasks:
        tasks = [
            ResearchTaskRecord(
                project_id=project.id or 0,
                title="完善纳排标准草案",
                stage_key="screening",
                status="in_progress",
            ),
            ResearchTaskRecord(
                project_id=project.id or 0,
                title="补充文献检索式",
                stage_key="search",
                status="todo",
            ),
        ]

    if not artifacts:
        artifacts = [
            ArtifactRecord(
                project_id=project.id or 0,
                artifact_type="protocol",
                title="方案初稿 v0.3",
            ),
            ArtifactRecord(
                project_id=project.id or 0,
                artifact_type="evidence-table",
                title="文献证据表 v0.2",
            ),
        ]

    stages = []
    for key, label, status in STAGE_DEFINITIONS:
        stage_tasks = [task for task in tasks if task.stage_key == key]
        stage_artifacts = [item for item in artifacts if item.artifact_type]
        stages.append(
            WorkspaceStageSummary(
                key=key,
                label=label,
                status=status,
                task_count=len(stage_tasks),
                artifact_count=len(stage_artifacts),
                target=f"/workspace/stages/{key}",
            )
        )

    return WorkspaceHomeResponse(
        project=WorkspaceProjectSummary(
            id=project.id or 0,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage="方案设计",
            updated_at_label="刚刚更新",
        ),
        hero_cta=WorkspaceHeroAction(
            label="继续上次研究",
            target="/workspace/tasks/recent",
        ),
        stages=stages,
        recent_tasks=[
            WorkspaceItemSummary(
                title=tasks[0].title,
                subtitle="继续完善当前任务",
                target="/workspace/tasks/recent",
            ),
            WorkspaceItemSummary(
                title=tasks[1].title,
                subtitle="检索策略待补充",
                target="/workspace/tasks/recent",
            ),
        ],
        recent_artifacts=[
            WorkspaceItemSummary(
                title=artifacts[0].title,
                subtitle="最近修改于 5 分钟前",
                target="/workspace/artifacts/recent",
            ),
            WorkspaceItemSummary(
                title=artifacts[1].title,
                subtitle="最近修改于 20 分钟前",
                target="/workspace/artifacts/recent",
            ),
        ],
        activity=[
            WorkspaceItemSummary(
                title="文献筛选阶段已进入进行中",
                subtitle="系统同步了最新阶段状态",
                target="/workspace/activity",
            ),
            WorkspaceItemSummary(
                title="新增方案初稿版本",
                subtitle="产物链路已更新",
                target="/workspace/artifacts/recent",
            ),
        ],
        assistant=WorkspaceAssistantSummary(
            headline="MedA 助手建议",
            primary_action_label="生成下一步建议",
            primary_action_target="/workspace/assistant",
        ),
        todos=[
            WorkspaceItemSummary(
                title="确认研究终点定义",
                subtitle="今日到期",
                target="/workspace/tasks/recent",
            ),
            WorkspaceItemSummary(
                title="审核入排标准变更",
                subtitle="等待 PI 确认",
                target="/workspace/tasks/recent",
            ),
        ],
    )
```

`D:\workspace\MedA\apps\agent-core\app\routers\workspace.py`

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.models import ResearchProject
from app.schemas import WorkspaceHomeResponse
from app.services.workspace import build_workspace_home

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


@router.get("/projects/{project_id}/home", response_model=WorkspaceHomeResponse)
def get_workspace_home(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> WorkspaceHomeResponse:
    project = session.get(ResearchProject, project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    return build_workspace_home(session, project)
```

`D:\workspace\MedA\apps\agent-core\app\main.py`

```python
from fastapi import FastAPI

from app.db import init_db
from app.routers.auth import router as auth_router
from app.routers.events import router as events_router
from app.routers.files import router as files_router
from app.routers.projects import router as projects_router
from app.routers.workspace import router as workspace_router

app = FastAPI(title="MedA Agent Core")
init_db()
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(events_router)
app.include_router(files_router)
app.include_router(workspace_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_workspace_home_api.py::test_workspace_home_returns_project_scoped_summary" -v`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/app/models.py" "MedA/apps/agent-core/app/schemas.py" "MedA/apps/agent-core/app/services/workspace.py" "MedA/apps/agent-core/app/routers/workspace.py" "MedA/apps/agent-core/app/main.py" "MedA/apps/agent-core/tests/test_workspace_home_api.py"
git -C "D:\workspace" commit -m "feat: add MedA workspace home summary API"
```

### Task 2: Add Workspace Summary Support To The Shared SDK

**Files:**
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\client.ts`

- [ ] **Step 1: Write the failing test**

Modify: `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts`

```ts
import { describe, expect, it, vi } from "vitest";

import { createClient } from "./client";
import { createMemorySessionStore } from "./session";

describe("workspace client", () => {
  it("sends the bearer token when fetching workspace home", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 7,
          name: "糖尿病真实世界研究",
          workspace_key: "demo-hospital/糖尿病真实世界研究",
          current_stage: "方案设计",
          updated_at_label: "刚刚更新",
        },
        hero_cta: { label: "继续上次研究", target: "/workspace/tasks/recent" },
        stages: [],
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
    }));

    vi.stubGlobal("fetch", fetchMock);

    const client = createClient(
      "http://localhost:8000",
      createMemorySessionStore("meda_token"),
    );

    const data = await client.getWorkspaceHome(7);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/home",
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer meda_token",
        },
      },
    );
    expect(data.project.name).toBe("糖尿病真实世界研究");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run "src/session.test.ts"`
Expected: FAIL because `getWorkspaceHome` is not defined on the shared client.

- [ ] **Step 3: Write minimal implementation**

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

export type WorkspaceHeroAction = {
  label: string;
  target: string;
};

export type WorkspaceStageSummary = {
  key: string;
  label: string;
  status: string;
  task_count: number;
  artifact_count: number;
  target: string;
};

export type WorkspaceItemSummary = {
  title: string;
  subtitle: string;
  target: string;
};

export type WorkspaceAssistantSummary = {
  headline: string;
  primary_action_label: string;
  primary_action_target: string;
};

export type WorkspaceProjectSummary = {
  id: number;
  name: string;
  workspace_key: string;
  current_stage: string;
  updated_at_label: string;
};

export type WorkspaceHomeSummary = {
  project: WorkspaceProjectSummary;
  hero_cta: WorkspaceHeroAction;
  stages: WorkspaceStageSummary[];
  recent_tasks: WorkspaceItemSummary[];
  recent_artifacts: WorkspaceItemSummary[];
  activity: WorkspaceItemSummary[];
  assistant: WorkspaceAssistantSummary;
  todos: WorkspaceItemSummary[];
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

    async getWorkspaceHome(projectId: number): Promise<WorkspaceHomeSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/home`,
        {
          headers: buildHeaders(),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "workspace home failed");
      }

      return data;
    },
  };
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run "src/session.test.ts"`
Expected: PASS with `2 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/packages/shared-sdk/src/client.ts" "MedA/packages/shared-sdk/src/session.test.ts"
git -C "D:\workspace" commit -m "feat: add MedA workspace summary client helper"
```

### Task 3: Render Hermes-Style Workspace Home In Web

**Files:**
- Modify: `D:\workspace\MedA\apps\web\src\App.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx`
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

vi.mock("@meda/shared-sdk", () => ({
  createBrowserSessionStore: () => sessionStore,
  createClient: () => ({
    devLogin,
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
      stages: [
        {
          key: "topic",
          label: "选题",
          status: "done",
          task_count: 1,
          artifact_count: 1,
          target: "/workspace/stages/topic",
        },
      ],
      recent_tasks: [
        {
          title: "完善纳排标准草案",
          subtitle: "继续完善当前任务",
          target: "/workspace/tasks/recent",
        },
      ],
      recent_artifacts: [
        {
          title: "方案初稿 v0.3",
          subtitle: "最近修改于 5 分钟前",
          target: "/workspace/artifacts/recent",
        },
      ],
      activity: [
        {
          title: "新增方案初稿版本",
          subtitle: "产物链路已更新",
          target: "/workspace/activity",
        },
      ],
      assistant: {
        headline: "MedA 助手建议",
        primary_action_label: "生成下一步建议",
        primary_action_target: "/workspace/assistant",
      },
      todos: [
        {
          title: "确认研究终点定义",
          subtitle: "今日到期",
          target: "/workspace/tasks/recent",
        },
      ],
    }),
    getMe: vi.fn(),
  }),
}));

test("web workspace renders mixed home sections and handoff pages", async () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("机构标识"), {
    target: { value: "demo-hospital" },
  });
  fireEvent.change(screen.getByLabelText("用户编号"), {
    target: { value: "u-001" },
  });
  fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));

  expect(await screen.findByText("糖尿病真实世界研究")).toBeInTheDocument();
  expect(screen.getByText("当前阶段：方案设计")).toBeInTheDocument();
  expect(screen.getByText("研究阶段")).toBeInTheDocument();
  expect(screen.getByText("MedA 助手建议")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "继续上次研究" }));
  expect(await screen.findByText("最近任务承接页")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`
Expected: FAIL because the current workspace shell only renders a greeting and raw project list.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\apps\web\src\App.tsx`

```tsx
import { useMemo, useState } from "react";

import {
  createBrowserSessionStore,
  createClient,
  type ProjectSummary,
  type SessionContext,
  type WorkspaceHomeSummary,
} from "@meda/shared-sdk";

import { LoginForm } from "./components/LoginForm";
import { WorkspaceShell } from "./components/WorkspaceShell";

export default function App() {
  const sessionStore = useMemo(() => createBrowserSessionStore(), []);
  const client = useMemo(
    () => createClient("http://localhost:8000", sessionStore),
    [sessionStore],
  );
  const [session, setSession] = useState<SessionContext | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [workspaceHome, setWorkspaceHome] = useState<WorkspaceHomeSummary | null>(null);

  const handleLogin = async (payload: {
    organizationSlug: string;
    userId: string;
  }) => {
    const nextSession = await client.devLogin({
      organization_slug: payload.organizationSlug,
      organization_name: "Demo Hospital",
      user_id: payload.userId,
      display_name: "Dr. Chen",
      role: "org_admin",
      client_type: "web",
    });
    const nextProjects = await client.listProjects();
    const firstProject = nextProjects[0];
    const nextWorkspaceHome = firstProject
      ? await client.getWorkspaceHome(firstProject.id)
      : null;

    setSession(nextSession);
    setProjects(nextProjects);
    setWorkspaceHome(nextWorkspaceHome);
  };

  if (session === null) {
    return <LoginForm onSubmit={handleLogin} />;
  }

  if (workspaceHome === null) {
    return <main>Workspace unavailable.</main>;
  }

  return (
    <WorkspaceShell
      session={session}
      projects={projects}
      workspaceHome={workspaceHome}
    />
  );
}
```

`D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx`

```tsx
import { useState } from "react";

import type {
  ProjectSummary,
  SessionContext,
  WorkspaceHomeSummary,
} from "@meda/shared-sdk";

type WorkspaceShellProps = {
  session: SessionContext;
  projects: ProjectSummary[];
  workspaceHome: WorkspaceHomeSummary;
};

type Screen =
  | "home"
  | "recent-tasks"
  | "recent-artifacts"
  | "assistant"
  | "stage";

export function WorkspaceShell({
  session,
  projects,
  workspaceHome,
}: WorkspaceShellProps) {
  const [screen, setScreen] = useState<Screen>("home");

  if (screen === "recent-tasks") {
    return <main>最近任务承接页</main>;
  }

  if (screen === "recent-artifacts") {
    return <main>最近产物承接页</main>;
  }

  if (screen === "assistant") {
    return <main>右侧助手触发面板</main>;
  }

  if (screen === "stage") {
    return <main>科研流程模块入口页</main>;
  }

  return (
    <main>
      <section>
        <p>工作台</p>
        <p>项目</p>
        <p>数据 / 资料</p>
        <p>Agent</p>
        <p>产物</p>
        <p>管理</p>
      </section>

      <section>
        <h1>{workspaceHome.project.name}</h1>
        <p>当前机构：{session.organization.name}</p>
        <p>当前阶段：{workspaceHome.project.current_stage}</p>
        <ul>
          {projects.map((project) => (
            <li key={project.id}>{project.name}</li>
          ))}
        </ul>
      </section>

      <section>
        <h2>项目工作台首页</h2>
        <p>欢迎，{session.user.display_name}</p>
        <button onClick={() => setScreen("recent-tasks")}>
          {workspaceHome.hero_cta.label}
        </button>

        <h3>研究阶段</h3>
        <ul>
          {workspaceHome.stages.map((stage) => (
            <li key={stage.key}>
              <button onClick={() => setScreen("stage")}>
                {stage.label}
              </button>
            </li>
          ))}
        </ul>

        <h3>最近任务</h3>
        <button onClick={() => setScreen("recent-tasks")}>
          {workspaceHome.recent_tasks[0]?.title}
        </button>

        <h3>最近产物</h3>
        <button onClick={() => setScreen("recent-artifacts")}>
          {workspaceHome.recent_artifacts[0]?.title}
        </button>

        <h3>协作动态</h3>
        <p>{workspaceHome.activity[0]?.title}</p>
      </section>

      <aside>
        <h3>{workspaceHome.assistant.headline}</h3>
        <button onClick={() => setScreen("assistant")}>
          {workspaceHome.assistant.primary_action_label}
        </button>
        <h3>待办与提醒</h3>
        <ul>
          {workspaceHome.todos.map((todo) => (
            <li key={todo.title}>{todo.title}</li>
          ))}
        </ul>
      </aside>
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/web/src/App.tsx" "MedA/apps/web/src/components/WorkspaceShell.tsx" "MedA/apps/web/src/App.test.tsx"
git -C "D:\workspace" commit -m "feat: add Hermes-style MedA workspace home"
```

### Task 4: Mirror The Workspace Information Architecture In Desktop

**Files:**
- Modify: `D:\workspace\MedA\apps\desktop\src\App.tsx`
- Modify: `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx`

- [ ] **Step 1: Write the failing test**

`D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx`

```tsx
import { fireEvent, render, screen } from "@testing-library/react";
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
    getWorkspaceHome: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "方案设计",
        updated_at_label: "刚刚更新",
      },
      hero_cta: { label: "继续上次研究", target: "/workspace/tasks/recent" },
      stages: [
        {
          key: "topic",
          label: "选题",
          status: "done",
          task_count: 1,
          artifact_count: 1,
          target: "/workspace/stages/topic",
        },
      ],
      recent_tasks: [
        {
          title: "完善纳排标准草案",
          subtitle: "继续完善当前任务",
          target: "/workspace/tasks/recent",
        },
      ],
      recent_artifacts: [
        {
          title: "方案初稿 v0.3",
          subtitle: "最近修改于 5 分钟前",
          target: "/workspace/artifacts/recent",
        },
      ],
      activity: [
        {
          title: "新增方案初稿版本",
          subtitle: "产物链路已更新",
          target: "/workspace/activity",
        },
      ],
      assistant: {
        headline: "MedA 助手建议",
        primary_action_label: "生成下一步建议",
        primary_action_target: "/workspace/assistant",
      },
      todos: [
        {
          title: "确认研究终点定义",
          subtitle: "今日到期",
          target: "/workspace/tasks/recent",
        },
      ],
    }),
  }),
}));

test("desktop workspace mirrors the workspace home structure", async () => {
  render(<App />);

  expect(await screen.findByText("MedA Desktop Workspace")).toBeInTheDocument();
  expect(screen.getByText("当前阶段：方案设计")).toBeInTheDocument();
  expect(screen.getByText("研究阶段")).toBeInTheDocument();
  expect(screen.getByText("MedA 助手建议")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "方案初稿 v0.3" }));
  expect(await screen.findByText("最近产物承接页")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`
Expected: FAIL because the current Desktop shell only renders a simple heading and project list.

- [ ] **Step 3: Write minimal implementation**

`D:\workspace\MedA\apps\desktop\src\App.tsx`

```tsx
import { useEffect, useMemo, useState } from "react";

import {
  createClient,
  createMemorySessionStore,
  type ProjectSummary,
  type SessionContext,
  type WorkspaceHomeSummary,
} from "@meda/shared-sdk";

type Screen =
  | "home"
  | "recent-tasks"
  | "recent-artifacts"
  | "assistant"
  | "stage";

export default function App() {
  const sessionStore = useMemo(() => createMemorySessionStore("meda_token"), []);
  const client = useMemo(
    () => createClient("http://localhost:8000", sessionStore),
    [sessionStore],
  );
  const [session, setSession] = useState<SessionContext | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [workspaceHome, setWorkspaceHome] = useState<WorkspaceHomeSummary | null>(null);
  const [screen, setScreen] = useState<Screen>("home");

  useEffect(() => {
    client
      .getMe()
      .then(async (nextSession) => {
        const nextProjects = await client.listProjects();
        const firstProject = nextProjects[0];
        const nextWorkspaceHome = firstProject
          ? await client.getWorkspaceHome(firstProject.id)
          : null;

        setSession(nextSession);
        setProjects(nextProjects);
        setWorkspaceHome(nextWorkspaceHome);
      })
      .catch(() => {
        setSession(null);
        setProjects([]);
        setWorkspaceHome(null);
      });
  }, [client]);

  if (session === null || workspaceHome === null) {
    return <main>Desktop session unavailable.</main>;
  }

  if (screen === "recent-tasks") {
    return <main>最近任务承接页</main>;
  }

  if (screen === "recent-artifacts") {
    return <main>最近产物承接页</main>;
  }

  if (screen === "assistant") {
    return <main>右侧助手触发面板</main>;
  }

  if (screen === "stage") {
    return <main>科研流程模块入口页</main>;
  }

  return (
    <main>
      <h1>MedA Desktop Workspace</h1>
      <p>{workspaceHome.project.name}</p>
      <p>当前阶段：{workspaceHome.project.current_stage}</p>

      <section>
        <h2>项目上下文</h2>
        <ul>
          {projects.map((project) => (
            <li key={project.id}>{project.name}</li>
          ))}
        </ul>
      </section>

      <section>
        <button onClick={() => setScreen("recent-tasks")}>
          {workspaceHome.hero_cta.label}
        </button>

        <h2>研究阶段</h2>
        <ul>
          {workspaceHome.stages.map((stage) => (
            <li key={stage.key}>
              <button onClick={() => setScreen("stage")}>
                {stage.label}
              </button>
            </li>
          ))}
        </ul>

        <h2>最近任务</h2>
        <button onClick={() => setScreen("recent-tasks")}>
          {workspaceHome.recent_tasks[0]?.title}
        </button>

        <h2>最近产物</h2>
        <button onClick={() => setScreen("recent-artifacts")}>
          {workspaceHome.recent_artifacts[0]?.title}
        </button>
      </section>

      <aside>
        <h2>{workspaceHome.assistant.headline}</h2>
        <button onClick={() => setScreen("assistant")}>
          {workspaceHome.assistant.primary_action_label}
        </button>
        <h2>待办与提醒</h2>
        <ul>
          {workspaceHome.todos.map((todo) => (
            <li key={todo.title}>{todo.title}</li>
          ))}
        </ul>
      </aside>
    </main>
  );
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/desktop/src/App.tsx" "MedA/apps/desktop/tests/app-auth.test.tsx"
git -C "D:\workspace" commit -m "feat: mirror MedA workspace home in desktop"
```

## Self-Review

### Spec Coverage

- Covered in this wave:
  - three-column workspace home shape
  - `C1` mixed home structure
  - project context sidebar content
  - right-rail assistant and todo blocks
  - stage, recent-task, and recent-artifact handoff pages
  - same information architecture in Web and Desktop
- Deferred to later:
  - deep research module pages
  - full Hermes visual parity polish
  - admin expansion
  - heavy analytics and editing surfaces

### Placeholder Scan

- No `TBD`, `TODO`, or vague implementation markers remain in the tasks.
- Each task includes concrete file paths, code snippets, commands, expected results, and commit messages.

### Type Consistency

- `WorkspaceHomeSummary` uses the same field names in backend schemas, shared SDK types, and client usage.
- `getWorkspaceHome(projectId)` is introduced in the shared SDK before any client task consumes it.
- The handoff screen names remain consistent across Web and Desktop tests and implementations.
