# MedA Stage Entry Wave 4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable stage-entry hub so all six MedA research stages can open from the workspace home into the same project-scoped entry shell with stage-specific cards, recent items, and assistant guidance in both Web and Desktop.

**Architecture:** Extend the current `agent-core` workspace service with a second read-only summary endpoint dedicated to stage-entry data instead of overloading the existing workspace-home response. Keep the UI implementation narrow: reuse the Wave 3 shell, load stage-entry payloads on demand, and render one shared information architecture across Web and Desktop with a stage summary header, sub-entry cards, recent tasks/artifacts, and a right-rail assistant block.

**Tech Stack:** Python 3.12, FastAPI, SQLModel, React 18, TypeScript, Electron, Vitest, pytest

---

## Scope Note

This wave only covers the next independently testable layer after the Wave 3 workspace home:

- project-scoped stage-entry summary API
- shared SDK helper for stage-entry data
- Web stage-entry hub inside the existing workspace shell
- Desktop stage-entry hub with the same information architecture
- stage-specific sub-entry cards, recent task summary, recent artifact summary, and stage assistant guidance

This wave explicitly does **not** include:

- deep implementation of each stage's downstream feature pages
- complete task management flows
- complete artifact/version center
- large editors, grids, or analysis workbenches
- admin console work

## File Structure

### Repository Layout

- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py` - add stage-entry response models
- Create: `D:\workspace\MedA\apps\agent-core\app\services\stage_entry.py` - build per-stage summary payloads from project context and static stage definitions
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\workspace.py` - add `GET /api/workspace/projects/{project_id}/stages/{stage_key}`
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_stage_entry_api.py` - verify stage-entry payload shape and invalid-stage handling
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\client.ts` - add stage-entry types and fetch helper
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts` - verify authenticated stage-entry fetch
- Create: `D:\workspace\MedA\apps\web\src\components\workspace\SummaryButton.tsx` - share button rendering between workspace home and stage-entry cards
- Create: `D:\workspace\MedA\apps\web\src\components\workspace\StageEntryScreen.tsx` - render the reusable stage-entry hub in Web
- Modify: `D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx` - orchestrate home vs stage-entry vs handoff screens
- Modify: `D:\workspace\MedA\apps\web\src\App.tsx` - load stage-entry data on demand
- Modify: `D:\workspace\MedA\apps\web\src\App.test.tsx` - verify opening a stage-entry page from the home screen
- Create: `D:\workspace\MedA\apps\desktop\src\components\StageEntryScreen.tsx` - render the reusable stage-entry hub in Desktop
- Modify: `D:\workspace\MedA\apps\desktop\src\App.tsx` - load stage-entry data and route to the hub inside Desktop
- Modify: `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx` - verify Desktop opens the stage-entry page from a stage card

---

### Task 1: Add The Stage-Entry Summary API

**Files:**
- Modify: `D:\workspace\MedA\apps\agent-core\app\schemas.py`
- Create: `D:\workspace\MedA\apps\agent-core\app\services\stage_entry.py`
- Modify: `D:\workspace\MedA\apps\agent-core\app\routers\workspace.py`
- Create: `D:\workspace\MedA\apps\agent-core\tests\test_stage_entry_api.py`

- [ ] **Step 1: Write the failing tests**

`D:\workspace\MedA\apps\agent-core\tests\test_stage_entry_api.py`

```python
from fastapi.testclient import TestClient

from app.main import app


def test_stage_entry_returns_stage_specific_summary() -> None:
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
            "description": "Wave 4 stage entry",
        },
    )
    project_id = project.json()["id"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search",
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["stage_key"] == "search"
    assert body["stage_label"] == "检索"
    assert body["stage_goal"] == "完成检索式与来源配置"
    assert body["primary_action"]["label"] == "进入检索式管理"
    assert body["entry_cards"][0]["title"] == "检索式管理"
    assert body["assistant_suggestions"][0]["title"] == "补全数据库来源"
    assert body["guidance_notes"][0]["title"] == "输入要求"


def test_stage_entry_rejects_unknown_stage() -> None:
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
            "description": "Wave 4 invalid stage",
        },
    )
    project_id = project.json()["id"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/unknown",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "stage not found"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_stage_entry_api.py" -v`
Expected: FAIL with `404 Not Found` because the stage-entry endpoint does not exist yet.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\apps\agent-core\app\schemas.py`

```python
class StageEntryAction(BaseModel):
    label: str
    target: str


class StageEntryCardSummary(BaseModel):
    key: str
    title: str
    description: str
    status: str
    target: str


class StageEntryGuidanceNote(BaseModel):
    title: str
    detail: str


class StageEntryResponse(BaseModel):
    project: WorkspaceProjectSummary
    stage_key: str
    stage_label: str
    stage_status: str
    stage_goal: str
    primary_action: StageEntryAction
    entry_cards: list[StageEntryCardSummary]
    recent_tasks: list[WorkspaceItemSummary]
    recent_artifacts: list[WorkspaceItemSummary]
    assistant_suggestions: list[WorkspaceItemSummary]
    guidance_notes: list[StageEntryGuidanceNote]
```

`D:\workspace\MedA\apps\agent-core\app\services\stage_entry.py`

```python
from sqlmodel import Session, select

from app.models import ArtifactRecord, ResearchProject, ResearchTaskRecord
from app.schemas import (
    StageEntryAction,
    StageEntryCardSummary,
    StageEntryGuidanceNote,
    StageEntryResponse,
    WorkspaceItemSummary,
    WorkspaceProjectSummary,
)

STAGE_ENTRY_CONFIG = {
    "topic": {
        "label": "选题",
        "status": "done",
        "goal": "明确研究问题与研究边界",
        "primary_action": StageEntryAction(
            label="进入研究问题定义",
            target="/workspace/stage/topic/problem-definition",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="problem-definition",
                title="研究问题定义",
                description="明确研究对象、暴露和结局边界",
                status="ready",
                target="/workspace/stage/topic/problem-definition",
            ),
            StageEntryCardSummary(
                key="pico",
                title="PICO 结构",
                description="梳理人群、干预、对照与结局",
                status="ready",
                target="/workspace/stage/topic/pico",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="完善研究问题边界",
                subtitle="先确认核心终点和比较对象",
                target="/workspace/stage/topic/problem-definition",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要明确研究场景、研究对象和核心结局。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成研究问题草案与 PICO 结构。",
            ),
        ],
    },
    "search": {
        "label": "检索",
        "status": "done",
        "goal": "完成检索式与来源配置",
        "primary_action": StageEntryAction(
            label="进入检索式管理",
            target="/workspace/stage/search/query-builder",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="query-builder",
                title="检索式管理",
                description="维护主题词、自由词和组合策略",
                status="ready",
                target="/workspace/stage/search/query-builder",
            ),
            StageEntryCardSummary(
                key="sources",
                title="数据库来源",
                description="配置 PubMed、Embase 等来源",
                status="ready",
                target="/workspace/stage/search/sources",
            ),
            StageEntryCardSummary(
                key="search-log",
                title="检索记录",
                description="查看已执行检索和时间线",
                status="ready",
                target="/workspace/stage/search/search-log",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="补全数据库来源",
                subtitle="优先确认核心医学数据库清单",
                target="/workspace/stage/search/sources",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要主题词、自由词与数据库范围。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成检索式与检索记录。",
            ),
        ],
    },
    "screening": {
        "label": "筛选",
        "status": "in_progress",
        "goal": "完成文献纳入排除判断",
        "primary_action": StageEntryAction(
            label="进入标题摘要筛选",
            target="/workspace/stage/screening/title-abstract",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="title-abstract",
                title="标题摘要筛选",
                description="先完成标题摘要轮筛选",
                status="ready",
                target="/workspace/stage/screening/title-abstract",
            ),
            StageEntryCardSummary(
                key="full-text",
                title="全文筛选",
                description="进入全文纳入排除判断",
                status="ready",
                target="/workspace/stage/screening/full-text",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先完成标题摘要筛选",
                subtitle="保证排除理由结构化记录",
                target="/workspace/stage/screening/title-abstract",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要纳入排除标准和待筛文献集合。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成筛选结果与排除原因记录。",
            ),
        ],
    },
    "extraction": {
        "label": "抽取",
        "status": "pending",
        "goal": "把非结构化内容转成结构化证据",
        "primary_action": StageEntryAction(
            label="进入抽取字段模板",
            target="/workspace/stage/extraction/template",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="template",
                title="抽取字段模板",
                description="定义抽取字段与结构",
                status="ready",
                target="/workspace/stage/extraction/template",
            ),
            StageEntryCardSummary(
                key="evidence-table",
                title="证据表",
                description="查看结构化抽取结果",
                status="ready",
                target="/workspace/stage/extraction/evidence-table",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先确认抽取字段模板",
                subtitle="减少后续双人抽取差异",
                target="/workspace/stage/extraction/template",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要抽取字段定义和文献全文。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成结构化证据表。",
            ),
        ],
    },
    "analysis": {
        "label": "分析",
        "status": "pending",
        "goal": "组织变量、方法和结果表达",
        "primary_action": StageEntryAction(
            label="进入分析变量",
            target="/workspace/stage/analysis/variables",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="variables",
                title="分析变量",
                description="整理分析所需变量与分组",
                status="ready",
                target="/workspace/stage/analysis/variables",
            ),
            StageEntryCardSummary(
                key="results",
                title="结果摘要",
                description="查看分析结果与核心结论",
                status="ready",
                target="/workspace/stage/analysis/results",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先整理分析变量",
                subtitle="确认变量口径后再进入结果表达",
                target="/workspace/stage/analysis/variables",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要变量定义、分析方法和证据数据。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成分析变量表和结果摘要。",
            ),
        ],
    },
    "output": {
        "label": "产出",
        "status": "pending",
        "goal": "形成最终交付产物",
        "primary_action": StageEntryAction(
            label="进入方案文档",
            target="/workspace/stage/output/protocol",
        ),
        "entry_cards": [
            StageEntryCardSummary(
                key="protocol",
                title="方案文档",
                description="进入方案与报告主文档入口",
                status="ready",
                target="/workspace/stage/output/protocol",
            ),
            StageEntryCardSummary(
                key="exports",
                title="导出与版本",
                description="查看导出记录和版本快照",
                status="ready",
                target="/workspace/stage/output/exports",
            ),
        ],
        "assistant_suggestions": [
            WorkspaceItemSummary(
                title="先整理最终输出结构",
                subtitle="确认主文档和附件列表",
                target="/workspace/stage/output/protocol",
            )
        ],
        "guidance_notes": [
            StageEntryGuidanceNote(
                title="输入要求",
                detail="需要上游阶段已确认的分析结果和草稿内容。",
            ),
            StageEntryGuidanceNote(
                title="产出要求",
                detail="至少形成主文档入口与版本导出承接。",
            ),
        ],
    },
}


def build_stage_entry(session: Session, project: ResearchProject, stage_key: str) -> StageEntryResponse | None:
    config = STAGE_ENTRY_CONFIG.get(stage_key)
    if config is None:
        return None

    project_id = project.id or 0
    tasks = session.exec(
        select(ResearchTaskRecord).where(
            ResearchTaskRecord.project_id == project_id,
            ResearchTaskRecord.stage_key == stage_key,
        )
    ).all()
    artifacts = session.exec(
        select(ArtifactRecord).where(ArtifactRecord.project_id == project_id)
    ).all()

    recent_tasks = [
        WorkspaceItemSummary(
            title=task.title,
            subtitle="进入该阶段任务承接页",
            target=f"/workspace/stage/{stage_key}/tasks",
        )
        for task in tasks[:2]
    ] or [
        WorkspaceItemSummary(
            title=f"{config['label']}阶段待开始任务",
            subtitle="进入该阶段任务承接页",
            target=f"/workspace/stage/{stage_key}/tasks",
        )
    ]

    recent_artifacts = [
        WorkspaceItemSummary(
            title=artifact.title,
            subtitle="进入该阶段产物承接页",
            target=f"/workspace/stage/{stage_key}/artifacts",
        )
        for artifact in artifacts[:2]
    ] or [
        WorkspaceItemSummary(
            title=f"{config['label']}阶段产物承接",
            subtitle="进入该阶段产物承接页",
            target=f"/workspace/stage/{stage_key}/artifacts",
        )
    ]

    return StageEntryResponse(
        project=WorkspaceProjectSummary(
            id=project_id,
            name=project.name,
            workspace_key=project.workspace_key,
            current_stage=config["label"],
            updated_at_label="刚刚更新",
        ),
        stage_key=stage_key,
        stage_label=config["label"],
        stage_status=config["status"],
        stage_goal=config["goal"],
        primary_action=config["primary_action"],
        entry_cards=config["entry_cards"],
        recent_tasks=recent_tasks,
        recent_artifacts=recent_artifacts,
        assistant_suggestions=config["assistant_suggestions"],
        guidance_notes=config["guidance_notes"],
    )
```

`D:\workspace\MedA\apps\agent-core\app\routers\workspace.py`

```python
from app.schemas import StageEntryResponse, WorkspaceHomeResponse
from app.services.stage_entry import build_stage_entry
from app.services.workspace import build_workspace_home


@router.get("/projects/{project_id}/stages/{stage_key}", response_model=StageEntryResponse)
def get_stage_entry(
    project_id: int,
    stage_key: str,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> StageEntryResponse:
    project = session.get(ResearchProject, project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    stage_entry = build_stage_entry(session, project, stage_key)
    if stage_entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stage not found")

    return stage_entry
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --project "D:\workspace\MedA\apps\agent-core" pytest "D:\workspace\MedA\apps\agent-core\tests\test_stage_entry_api.py" "D:\workspace\MedA\apps\agent-core\tests\test_workspace_home_api.py" -v`
Expected: PASS with `4 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/agent-core/app/schemas.py" "MedA/apps/agent-core/app/services/stage_entry.py" "MedA/apps/agent-core/app/routers/workspace.py" "MedA/apps/agent-core/tests/test_stage_entry_api.py"
git -C "D:\workspace" commit -m "feat: add MedA stage entry summary API"
```

### Task 2: Add Stage-Entry Support To The Shared SDK

**Files:**
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\client.ts`
- Modify: `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts`

- [ ] **Step 1: Write the failing test**

Append this test to `D:\workspace\MedA\packages\shared-sdk\src\session.test.ts`:

```ts
it("fetches stage-entry data with the bearer token", async () => {
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
      stage_label: "检索",
      stage_status: "done",
      stage_goal: "完成检索式与来源配置",
      primary_action: {
        label: "进入检索式管理",
        target: "/workspace/stage/search/query-builder",
      },
      entry_cards: [
        {
          key: "query-builder",
          title: "检索式管理",
          description: "维护主题词、自由词和组合策略",
          status: "ready",
          target: "/workspace/stage/search/query-builder",
        },
      ],
      recent_tasks: [],
      recent_artifacts: [],
      assistant_suggestions: [],
      guidance_notes: [
        { title: "输入要求", detail: "需要主题词、自由词与数据库范围。" },
      ],
    }),
  }));

  vi.stubGlobal("fetch", fetchMock);

  const client = createClient(
    "http://localhost:8000",
    createMemorySessionStore("meda_token"),
  );

  const data = await client.getStageEntry(7, "search");

  expect(fetchMock).toHaveBeenCalledWith(
    "http://localhost:8000/api/workspace/projects/7/stages/search",
    {
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer meda_token",
      },
    },
  );
  expect(data.stage_label).toBe("检索");
  expect(data.entry_cards[0].title).toBe("检索式管理");
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm --prefix "D:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run "src/session.test.ts"`
Expected: FAIL because `getStageEntry` does not exist on the shared client.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\packages\shared-sdk\src\client.ts`

```ts
export type StageEntryAction = {
  label: string;
  target: string;
};

export type StageEntryCardSummary = {
  key: string;
  title: string;
  description: string;
  status: string;
  target: string;
};

export type StageEntryGuidanceNote = {
  title: string;
  detail: string;
};

export type StageEntrySummary = {
  project: WorkspaceProjectSummary;
  stage_key: string;
  stage_label: string;
  stage_status: string;
  stage_goal: string;
  primary_action: StageEntryAction;
  entry_cards: StageEntryCardSummary[];
  recent_tasks: WorkspaceItemSummary[];
  recent_artifacts: WorkspaceItemSummary[];
  assistant_suggestions: WorkspaceItemSummary[];
  guidance_notes: StageEntryGuidanceNote[];
};

async getStageEntry(projectId: number, stageKey: string): Promise<StageEntrySummary> {
  const response = await fetch(
    `${baseUrl}/api/workspace/projects/${projectId}/stages/${stageKey}`,
    {
      headers: buildHeaders(),
    },
  );
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail ?? "stage entry failed");
  }

  return data;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm --prefix "D:\workspace\MedA" --workspace @meda/shared-sdk exec vitest run "src/session.test.ts"`
Expected: PASS with `3 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/packages/shared-sdk/src/client.ts" "MedA/packages/shared-sdk/src/session.test.ts"
git -C "D:\workspace" commit -m "feat: add MedA stage entry client helper"
```

### Task 3: Render The Stage-Entry Hub In Web

**Files:**
- Create: `D:\workspace\MedA\apps\web\src\components\workspace\SummaryButton.tsx`
- Create: `D:\workspace\MedA\apps\web\src\components\workspace\StageEntryScreen.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\App.tsx`
- Modify: `D:\workspace\MedA\apps\web\src\App.test.tsx`

- [ ] **Step 1: Write the failing test**

Replace the existing test in `D:\workspace\MedA\apps\web\src\App.test.tsx` with:

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
          key: "search",
          label: "检索",
          status: "done",
          task_count: 1,
          artifact_count: 1,
          target: "/workspace/stages/search",
        },
      ],
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
        target: "/workspace/stage/search/query-builder",
      },
      entry_cards: [
        {
          key: "query-builder",
          title: "检索式管理",
          description: "维护主题词、自由词和组合策略",
          status: "ready",
          target: "/workspace/stage/search/query-builder",
        },
      ],
      recent_tasks: [
        {
          title: "补充文献检索式",
          subtitle: "进入该阶段任务承接页",
          target: "/workspace/stage/search/tasks",
        },
      ],
      recent_artifacts: [
        {
          title: "文献检索式 v0.2",
          subtitle: "进入该阶段产物承接页",
          target: "/workspace/stage/search/artifacts",
        },
      ],
      assistant_suggestions: [
        {
          title: "补全数据库来源",
          subtitle: "优先确认核心医学数据库清单",
          target: "/workspace/stage/search/sources",
        },
      ],
      guidance_notes: [
        { title: "输入要求", detail: "需要主题词、自由词与数据库范围。" },
      ],
    }),
    getMe: vi.fn(),
  }),
}));

test("web workspace opens a stage-entry hub from the stage card", async () => {
  render(<App />);

  fireEvent.change(screen.getByLabelText("机构标识"), {
    target: { value: "demo-hospital" },
  });
  fireEvent.change(screen.getByLabelText("用户编号"), {
    target: { value: "u-001" },
  });
  fireEvent.click(screen.getByRole("button", { name: "进入工作台" }));

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));

  expect(await screen.findByText("检索阶段")).toBeInTheDocument();
  expect(screen.getByText("完成检索式与来源配置")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "进入检索式管理" })).toBeInTheDocument();
  expect(screen.getByText("补全数据库来源")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`
Expected: FAIL because clicking a stage card still lands on the placeholder `科研流程模块入口页`.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\apps\web\src\components\workspace\SummaryButton.tsx`

```tsx
import type {
  StageEntryCardSummary,
  WorkspaceItemSummary,
  WorkspaceStageSummary,
} from "@meda/shared-sdk";

type SummaryItem =
  | WorkspaceItemSummary
  | WorkspaceStageSummary
  | StageEntryCardSummary;

export function SummaryButton({
  item,
  onClick,
}: {
  item: SummaryItem;
  onClick: () => void;
}) {
  const title = "title" in item ? item.title : item.label;
  const subtitle =
    "subtitle" in item
      ? item.subtitle
      : "description" in item
        ? item.description
        : `${item.task_count} 个任务 · ${item.artifact_count} 个产物`;

  return (
    <button
      aria-label={title}
      style={{
        width: "100%",
        border: "1px solid #d0d7e2",
        background: "#ffffff",
        borderRadius: "14px",
        padding: "12px 14px",
        textAlign: "left",
        cursor: "pointer",
      }}
      onClick={onClick}
    >
      <div style={{ fontWeight: 600 }}>{title}</div>
      <div style={{ marginTop: "4px", color: "#4b5563", fontSize: "14px" }}>
        {subtitle}
      </div>
    </button>
  );
}
```

`D:\workspace\MedA\apps\web\src\components\workspace\StageEntryScreen.tsx`

```tsx
import type { StageEntrySummary } from "@meda/shared-sdk";

import { SummaryButton } from "./SummaryButton";

export function StageEntryScreen({
  stageEntry,
  onOpenPrimaryAction,
  onOpenTaskPage,
  onOpenArtifactPage,
  onOpenAssistantAction,
}: {
  stageEntry: StageEntrySummary;
  onOpenPrimaryAction: () => void;
  onOpenTaskPage: () => void;
  onOpenArtifactPage: () => void;
  onOpenAssistantAction: () => void;
}) {
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
        <div style={{ color: "#6b7280", fontSize: "13px" }}>{stageEntry.project.name}</div>
        <h2 style={{ margin: "8px 0 12px", fontSize: "30px" }}>{stageEntry.stage_label}阶段</h2>
        <p style={{ margin: "0 0 8px" }}>当前状态：{stageEntry.stage_status}</p>
        <p style={{ margin: 0 }}>{stageEntry.stage_goal}</p>
        <button
          style={{ marginTop: "16px", border: "none", borderRadius: "999px", background: "#111827", color: "#f9fafb", padding: "10px 16px", cursor: "pointer", fontWeight: 600 }}
          onClick={onOpenPrimaryAction}
        >
          {stageEntry.primary_action.label}
        </button>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
        <h3 style={{ marginTop: 0 }}>子入口导航</h3>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "12px" }}>
          {stageEntry.entry_cards.map((card) => (
            <SummaryButton key={card.key} item={card} onClick={onOpenPrimaryAction} />
          ))}
        </div>
      </section>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "20px" }}>
        <div style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
          <h3 style={{ marginTop: 0 }}>最近任务</h3>
          {stageEntry.recent_tasks.map((task) => (
            <SummaryButton key={task.title} item={task} onClick={onOpenTaskPage} />
          ))}
        </div>
        <div style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
          <h3 style={{ marginTop: 0 }}>最近产物</h3>
          {stageEntry.recent_artifacts.map((artifact) => (
            <SummaryButton key={artifact.title} item={artifact} onClick={onOpenArtifactPage} />
          ))}
        </div>
      </section>

      <aside style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
        <h3 style={{ marginTop: 0 }}>阶段助手 + 下一步建议</h3>
        {stageEntry.assistant_suggestions.map((item) => (
          <SummaryButton key={item.title} item={item} onClick={onOpenAssistantAction} />
        ))}
        <ul>
          {stageEntry.guidance_notes.map((note) => (
            <li key={note.title}>
              <strong>{note.title}</strong>：{note.detail}
            </li>
          ))}
        </ul>
      </aside>
    </section>
  );
}
```

`D:\workspace\MedA\apps\web\src\App.tsx`

```tsx
import {
  createBrowserSessionStore,
  createClient,
  type ProjectSummary,
  type SessionContext,
  type StageEntrySummary,
  type WorkspaceHomeSummary,
} from "@meda/shared-sdk";

export default function App() {
  // existing setup stays the same
  const [stageEntry, setStageEntry] = useState<StageEntrySummary | null>(null);

  const handleOpenStage = async (projectId: number, stageKey: string) => {
    setStageEntry(await client.getStageEntry(projectId, stageKey));
  };

  return (
    <WorkspaceShell
      session={session}
      projects={projects}
      workspaceHome={workspaceHome}
      stageEntry={stageEntry}
      onOpenStage={handleOpenStage}
    />
  );
}
```

`D:\workspace\MedA\apps\web\src\components\WorkspaceShell.tsx`

```tsx
import type { ProjectSummary, SessionContext, StageEntrySummary, WorkspaceHomeSummary } from "@meda/shared-sdk";

import { SummaryButton } from "./workspace/SummaryButton";
import { StageEntryScreen } from "./workspace/StageEntryScreen";

type Screen =
  | "home"
  | "recent-tasks"
  | "recent-artifacts"
  | "assistant"
  | "stage-entry"
  | "stage-subentry";

type WorkspaceShellProps = {
  session: SessionContext;
  projects: ProjectSummary[];
  workspaceHome: WorkspaceHomeSummary;
  stageEntry: StageEntrySummary | null;
  onOpenStage: (projectId: number, stageKey: string) => Promise<void>;
};

if (screen === "stage-entry" && stageEntry !== null) {
  return (
    <main style={shellStyle}>
      {/* left rail stays the same */}
      <StageEntryScreen
        stageEntry={stageEntry}
        onOpenPrimaryAction={() => setScreen("stage-subentry")}
        onOpenTaskPage={() => setScreen("recent-tasks")}
        onOpenArtifactPage={() => setScreen("recent-artifacts")}
        onOpenAssistantAction={() => setScreen("assistant")}
      />
      {/* right rail stays the same */}
    </main>
  );
}

{workspaceHome.stages.map((stage) => (
  <SummaryButton
    key={stage.key}
    item={stage}
    onClick={async () => {
      await onOpenStage(workspaceHome.project.id, stage.key);
      setScreen("stage-entry");
    }}
  />
))}

if (screen === "stage-subentry") {
  return <main style={{ padding: "24px" }}>阶段子入口承接页</main>;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/web run test -- --run`
Expected: PASS with `1 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/web/src/components/workspace/SummaryButton.tsx" "MedA/apps/web/src/components/workspace/StageEntryScreen.tsx" "MedA/apps/web/src/components/WorkspaceShell.tsx" "MedA/apps/web/src/App.tsx" "MedA/apps/web/src/App.test.tsx"
git -C "D:\workspace" commit -m "feat: add MedA web stage entry hub"
```

### Task 4: Mirror The Stage-Entry Hub In Desktop

**Files:**
- Create: `D:\workspace\MedA\apps\desktop\src\components\StageEntryScreen.tsx`
- Modify: `D:\workspace\MedA\apps\desktop\src\App.tsx`
- Modify: `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx`

- [ ] **Step 1: Write the failing test**

Replace the current test in `D:\workspace\MedA\apps\desktop\tests\app-auth.test.tsx` with:

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
          key: "search",
          label: "检索",
          status: "done",
          task_count: 1,
          artifact_count: 1,
          target: "/workspace/stages/search",
        },
      ],
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
        target: "/workspace/stage/search/query-builder",
      },
      entry_cards: [
        {
          key: "query-builder",
          title: "检索式管理",
          description: "维护主题词、自由词和组合策略",
          status: "ready",
          target: "/workspace/stage/search/query-builder",
        },
      ],
      recent_tasks: [],
      recent_artifacts: [],
      assistant_suggestions: [
        {
          title: "补全数据库来源",
          subtitle: "优先确认核心医学数据库清单",
          target: "/workspace/stage/search/sources",
        },
      ],
      guidance_notes: [
        { title: "输入要求", detail: "需要主题词、自由词与数据库范围。" },
      ],
    }),
  }),
}));

test("desktop workspace opens the stage-entry hub from a stage card", async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));

  expect(await screen.findByText("检索阶段")).toBeInTheDocument();
  expect(screen.getByText("完成检索式与来源配置")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "进入检索式管理" })).toBeInTheDocument();
  expect(screen.getByText("补全数据库来源")).toBeInTheDocument();
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`
Expected: FAIL because clicking a stage card still lands on the placeholder `科研流程模块入口页`.

- [ ] **Step 3: Write the minimal implementation**

`D:\workspace\MedA\apps\desktop\src\components\StageEntryScreen.tsx`

```tsx
import type { StageEntrySummary } from "@meda/shared-sdk";

export function StageEntryScreen({
  stageEntry,
  onOpenPrimaryAction,
  onOpenAssistantAction,
}: {
  stageEntry: StageEntrySummary;
  onOpenPrimaryAction: () => void;
  onOpenAssistantAction: () => void;
}) {
  return (
    <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
      <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
        <h2 style={{ margin: "0 0 12px" }}>{stageEntry.stage_label}阶段</h2>
        <p>{stageEntry.stage_goal}</p>
        <button onClick={onOpenPrimaryAction}>{stageEntry.primary_action.label}</button>
      </section>

      <section style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
        <h3 style={{ marginTop: 0 }}>子入口导航</h3>
        {stageEntry.entry_cards.map((card) => (
          <button key={card.key} aria-label={card.title} onClick={onOpenPrimaryAction}>
            {card.title}
          </button>
        ))}
      </section>

      <aside style={{ background: "#ffffff", border: "1px solid #d7dce5", borderRadius: "20px", padding: "20px" }}>
        <h3 style={{ marginTop: 0 }}>阶段助手 + 下一步建议</h3>
        {stageEntry.assistant_suggestions.map((item) => (
          <button key={item.title} onClick={onOpenAssistantAction}>
            {item.title}
          </button>
        ))}
        <ul>
          {stageEntry.guidance_notes.map((note) => (
            <li key={note.title}>
              <strong>{note.title}</strong>：{note.detail}
            </li>
          ))}
        </ul>
      </aside>
    </section>
  );
}
```

`D:\workspace\MedA\apps\desktop\src\App.tsx`

```tsx
import {
  createClient,
  createMemorySessionStore,
  type ProjectSummary,
  type SessionContext,
  type StageEntrySummary,
  type WorkspaceHomeSummary,
} from "@meda/shared-sdk";

import { StageEntryScreen } from "./components/StageEntryScreen";

type Screen =
  | "home"
  | "recent-tasks"
  | "recent-artifacts"
  | "assistant"
  | "stage-entry"
  | "stage-subentry";

const [stageEntry, setStageEntry] = useState<StageEntrySummary | null>(null);

const openStage = async (projectId: number, stageKey: string) => {
  setStageEntry(await client.getStageEntry(projectId, stageKey));
  setScreen("stage-entry");
};

if (screen === "stage-entry" && stageEntry !== null) {
  return (
    <main style={shellStyle}>
      {/* left rail stays the same */}
      <StageEntryScreen
        stageEntry={stageEntry}
        onOpenPrimaryAction={() => setScreen("stage-subentry")}
        onOpenAssistantAction={() => setScreen("assistant")}
      />
      {/* right rail stays the same */}
    </main>
  );
}

{workspaceHome.stages.map((stage) => (
  <SummaryButton
    key={stage.key}
    item={stage}
    onClick={() => openStage(workspaceHome.project.id, stage.key)}
  />
))}

if (screen === "stage-subentry") {
  return <main style={{ padding: "24px" }}>阶段子入口承接页</main>;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `npm --prefix "D:\workspace\MedA" --workspace apps/desktop run test -- --run`
Expected: PASS with `2 passed`.

- [ ] **Step 5: Commit**

```bash
git -C "D:\workspace" add -- "MedA/apps/desktop/src/components/StageEntryScreen.tsx" "MedA/apps/desktop/src/App.tsx" "MedA/apps/desktop/tests/app-auth.test.tsx"
git -C "D:\workspace" commit -m "feat: add MedA desktop stage entry hub"
```

## Self-Review

### Spec Coverage

- Covered in this wave:
  - unified stage-entry hub for all six stages
  - stage-specific goals, primary action, sub-entry cards, recent items, assistant suggestions, and guidance notes
  - same information architecture in Web and Desktop
  - home-to-stage-entry navigation path
- Deferred to later:
  - downstream deep feature pages for every sub-entry
  - full task system
  - full artifact/version center

### Placeholder Scan

- No `TBD`, `TODO`, or vague task wording remains in the plan.
- Every task includes concrete files, code, commands, expected failures, expected passes, and commit messages.

### Type Consistency

- `StageEntrySummary` matches backend `StageEntryResponse`.
- `getStageEntry(projectId, stageKey)` is added before Web and Desktop consume it.
- `stage-entry` and `stage-subentry` screen names stay consistent across Web and Desktop tasks.
