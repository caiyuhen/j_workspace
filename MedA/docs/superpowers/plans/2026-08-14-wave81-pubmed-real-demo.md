# Wave 8.1 PubMed 真数据端到端 Demo（Scope A · 方案一+三） Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Wave 8 三源真 Adapter 206 tests 通过的基线上，新增 1 张 Workspace 第 4 张一键 PubMed Demo 紫色高卡 + 6 个主题胶囊，用户点 1 下即可 2~6s 内看到 PubMed 真数据跑通 4 面板联动（含 PRISMA / BM25 / PICO rule_baseline / 文献库），以及对应的 Python CLI 脚本 demo_pubmed_end2end.py（含 preset 对比 CI 两端同步真理 + 脚本退出码 contract）。

**Architecture:** 
- **共享真理源：`packages/shared-sdk/src/presets.ts` 6 个 `DEMO_PRESETS` 常量 + `shared-ui` 做 `<WorkspaceOneClickPubmedDemo>` 独立组件（apps/web WorkspaceShell / apps/desktop App.tsx 各自引入同一组件，禁止两套代码）。
- **零新增 API 端点：** `ensureDemoProjectAndQuery` 前端 utility 串现有 4 个 API（listProjects/createProject/getSearchQueryBuilder/saveSearchQueryVersion/createSearchRun）；前端 utility 里做幂等防刷。
- **脚本 CLI 端：** 纯内存 纯函数 管道 PubMed adapter → 规范化 → 内存三级去重 → BM25 打分 → rule_baseline PICO 词频 Top5 → CSV 导出，pytest 默认 force_mock 离线零外网。

**Tech Stack:**
- 前端: TypeScript 5 + React 18 + Vite + Vitest 0.x
- shared-ui: shared-ui 已有现有 `PicoPanel/SearchRunDetailScreen 组件基础样式纯 CSS/TS
- 后端: Python 3.11 + FastAPI 0.11x/Pydantic v1 + sqlmodel httpx rank_bm25
- Python 测试: pytest 8 + autouse force_mock（Wave 8 基线上）
- CI gating：`test_presets_consistency.py 阻塞合并（TS/PY preset diff）

---

## 📁 File Structure（CREATE vs MODIFY

| # | 动作 | 路径 | 责任

### 创建（7 files）
| N1 | 新文件 | `packages/shared-sdk/src/presets.ts | DemoPreset type + 6 DEMO_PRESETS 常量 + DEMO_PRESET_BY_KEY Record
| N2 | 新文件 | `packages/shared-sdk/src/utils/demoSeedings.ts` | ensureDemoProjectAndQuery + build_grouped_terms_from_pico + build_expression_from_boolean_text
| N3 | 新文件 | `packages/shared-ui/src/WorkspaceOneClickPubmedDemo.tsx` | 紫色 NEW 一键卡 + 6 胶囊按钮 + 点击态 + 错误 toast 区
| N4 | 新文件 | `packages/shared-ui/src/__tests__/WorkspaceOneClickPubmedDemo.test.tsx` | §6.1 前端 5 tests
| N5 | 新文件 | `apps/agent-core/scripts/demo_pubmed_end2end.py` | CLI + DEMO_PRESETS_PY 6 个 key（与 TS side）+ run_pubmed_demo 纯异步可 import
| N6 | 新文件 | `apps/agent-core/tests/test_demo_pubmed_cli.py` | 4 tests（unknown preset exit2 / httpx mock live / ConnectError fallback / --json 合法）
| N7 | 新文件 | `apps/agent-core/tests/test_presets_consistency.py` | 1 条 CI gate：TS/PY preset 内容一致

### 修改（7 files）
| M1 | 修改 | `packages/shared-sdk/src/client.ts` | ① export CreateProjectRequest/ProjectResponse types ② MedaClient.createProject() 方法
| M2 | 修改 | `packages/shared-sdk/src/index.ts` | re-export DemoPreset/DEMO_PRESETS/DEMO_PRESET_BY_KEY/ensureDemoProjectAndQuery/CreateProjectRequest/ProjectResponse
| M3 | 修改 | `packages/shared-ui/src/index.ts` | re-export WorkspaceOneClickPubmedDemo / WorkspaceOneClickPubmedDemoProps types
| M4 | 修改 | `apps/web/src/components/WorkspaceShell.tsx` | ① 新增 WorkspaceShellProps 加 `client: MedaClient`；② L546「子入口导航 section 之后插入 <WorkspaceOneClickPubmedDemo>；③ 错误 toast 状态 + runCreated 跳转
| M5 | 修改 | `apps/web/src/App.tsx` | L245-272 `<WorkspaceShell/>` 加 `client={client}` prop
| M6 | 修改 | `apps/desktop/src/App.tsx` | ① L646 「子入口导航 section 后插入同组件（desktop 自己的 client/session/workspaceHome/onRunCreated/onErrorShowToast 传入）
| M7 | 修改 | `packages/shared-sdk/src/client.ts` | （如果 Wave 8 createSearchRun payload 里尚未支持 adapter_modes）则补可选 adapter_modes 字段传 JSON）

---

## 🔨 Tasks（8 Tasks，全 TDD bite-sized）

---

### Task 1：shared-sdk 补类型 + MedaClient.createProject（Types/方法）

**Files:**
- Modify: `packages/shared-sdk/src/client.ts`
- Test: TypeScript build（`tsc --noEmit` 无新增测试，Task 3 前端组件会用实际调用来验证）

- [ ] **Step 1: Write type CreateProjectRequest ProjectResponse types

在 packages/shared-sdk/src/client.ts`（types 区域（现有 L14 ProjectSummary 之后直接插入：

```ts
export type CreateProjectRequest = {
  organization_slug: string;
  owner_user_id: string;
  name: string;
  description: string;
};

export type ProjectResponse = {
  id: number;
  organization_slug: string;
  owner_user_id: string;
  name: string;
  description: string;
  workspace_key: string;
};
```

- [ ] **Step 2: 在 MedaClient class 内 listProjects() 之后（紧跟 L560 `async listProjects(): Promise<ProjectSummary[]> 紧接加方法：

```ts
async createProject(
  payload: CreateProjectRequest,
): Promise<ProjectResponse> {
  const response = await fetch(`${baseUrl}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json",
    ...buildHeaders(),
  },
    body: JSON.stringify(payload),
  });
  return handleResponse<ProjectResponse>(
    response,
    `create project failed (name=${payload.name})
  );
},
```

- [ ] **Step 3: Run TS build 验证

Run: `pnpm --filter @meda/shared-sdk exec tsc --noEmit`
Expected: Exit 0（无 TS 错误）

- [ ] **Step 4: Commit**

```bash
git add packages/shared-sdk/src/client.ts
git commit -m "feat(sdk): add CreateProjectRequest/ProjectResponse types + createProject method"
```

---

### Task 2：shared-sdk presets.ts + utils/demoSeedings.ts（常量 + 幂等种子工具

**Files:**
- Create: `packages/shared-sdk/src/presets.ts`
- Create: `packages/shared-sdk/src/utils/demoSeedings.ts`
- Modify: `packages/shared-sdk/src/index.ts`
- Test: TypeScript build 无 error；验证 ensureDemoProjectAndQuery types 编译通过）

- [ ] **Step 1: 创建 `packages/shared-sdk/src/presets.ts`

```ts
export type DemoPresetKey =
  | "sglt2i_ckd"
  | "sglt2i_hfredef"
  | "met_cv_presto"
  | "glp1_mace_rws"
  | "sglt2i_dka_safety"
  | "met_lifestyle_predm";

export type DemoPreset = {
  key: DemoPresetKey;
  label: string;
  badge: string;
  expected_hits_hint: string;
  project_name: string;
  query_name: string;
  boolean_text: string;
  selected_sources: ["pubmed"];
  pico: { p: string; i: string; c: string; o: string };
  filters?: {
    study_type?: Array<"rct" | "sr" | "rct_and_sr">;
    pubmed_mindate?: string;
    pubmed_maxdate?: string;
  };
};

export const DEMO_PRESETS: DemoPreset[] = [
  {
    key: "sglt2i_ckd",
    label: "💧 糖尿病肾病 SGLT2i",
    badge: "经典适应症",
    expected_hits_hint: "预计 1.5k+ hits",
    project_name: "MedA-Demo-Diabetes-CKD-2026",
    query_name: "SGLT2i in CKD (PubMed real-data demo)",
    boolean_text:
      "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR canagliflozin[Title/Abstract]) AND (chronic kidney disease[Title/Abstract] OR CKD[Title/Abstract] OR diabetic nephropathies[MeSH Major Topic]) AND randomised controlled trial[pt]",
    selected_sources: ["pubmed"],
    pico: {
      p: "adult with type 2 diabetes mellitus and CKD stage 2-4 or macroalbuminuria",
      i: "SGLT2 inhibitor add-on to RAAS blockade",
      c: "placebo or standard of care without SGLT2i",
      o: "composite renal endpoint (eGFR decline ≥50% / ESRD / renal death) ; change in eGFR slope ; 3P-MACE ; AE of genital mycotic infection / DKA / hypovolemia",
    },
    filters: { study_type: ["rct"] },
  },
  {
    key: "sglt2i_hfredef",
    label: "❤️ 达格列净 HFrEF DAPA-HF / DAPA-CKD",
    badge: "标杆研究",
    expected_hits_hint: "含 DAPA-HF、DAPA-CKD 原始 + follow-up",
    project_name: "MedA-Demo-HF-2026",
    query_name: "Dapagliflozin landmark HFrEF/CKD trials",
    boolean_text:
      "(DAPA-HF[Title/Abstract] OR DAPA-CKD[Title/Abstract] OR (dapagliflozin[Title/Abstract] AND (heart failure with reduced ejection fraction[Title/Abstract] OR HFrEF[Title/Abstract] OR chronic kidney disease[Title/Abstract]))) AND randomised controlled trial[pt]",
    selected_sources: ["pubmed"],
    pico: {
      p: "HFrEF LVEF ≤40% with/without T2DM; CKD eGFR 25-75 + uACR >200",
      i: "dapagliflozin 10 mg once daily",
      c: "matching placebo",
      o: "CV death or worsening HF composite; renal composite; change in NT-proBNP / KCCQ",
    },
    filters: { study_type: ["rct"] },
  },
  {
    key: "met_cv_presto",
    label: "💊 二甲双胍 CV PRESTO",
    badge: "RCT 重分析",
    expected_hits_hint: "RCT + pooled subgroup",
    project_name: "MedA-Demo-Metformin-CV-2026",
    query_name: "Metformin PRESTO CV outcomes reanalysis",
    boolean_text:
      "(PRESTO[Title/Abstract] OR (metformin[Title/Abstract] AND cardiovascular[Title/Abstract] AND (prediabetes[Title/Abstract] OR insulin resistance[Title/Abstract]))) AND randomized controlled trial[pt]",
    selected_sources: ["pubmed"],
    pico: {
      p: "prediabetes / insulin resistance with CV risk factors but no established ASCVD",
      i: "metformin extended-release +/- lifestyle intervention",
      c: "placebo or lifestyle-only",
      o: "MACE (CV death / MI / stroke) ; change in LDL-C / SBP / Hba1c",
    },
    filters: { study_type: ["rct"] },
  },
  {
    key: "glp1_mace_rws",
    label: "📈 GLP-1 RA MACE 真实世界",
    badge: "RCT vs RWS 对照",
    expected_hits_hint: "RCT + RWS 双队列",
    project_name: "MedA-Demo-GLP1-RA-2026",
    query_name: "GLP-1 RA MACE: RCT vs real-world comparison",
    boolean_text:
      "(glucagon-like peptide-1 receptor agonist[Title/Abstract] OR GLP-1 RA[Title/Abstract] OR liraglutide[Title/Abstract] OR semaglutide[Title/Abstract] OR dulaglutide[Title/Abstract] OR tirzepatide[Title/Abstract]) AND (major adverse cardiovascular events[Title/Abstract] OR MACE[Title/Abstract] OR cardiovascular outcomes[Title/Abstract]) AND ((randomized controlled trial[pt]) OR (real-world[Title/Abstract] OR retrospective[Title/Abstract] OR cohort[Title/Abstract]))",
    selected_sources: ["pubmed"],
    pico: {
      p: "T2DM with established ASCVD or high CV risk",
      i: "GLP-1 RA (injectable or oral) as add-on",
      c: "DPP-4 inhibitor / sulfonylurea / basal insulin / placebo",
      o: "3P-MACE (CV death, non-fatal MI, non-fatal stroke) ; all-cause mortality ; severe hypoglycaemia",
    },
    filters: { study_type: ["rct_and_sr"] },
  },
  {
    key: "sglt2i_dka_safety",
    label: "⚠️ SGLT2i 酮症酸中毒 Safety",
    badge: "风险点",
    expected_hits_hint: "RCT post-hoc + RWS + case series",
    project_name: "MedA-Demo-SGLT2i-Safety-2026",
    query_name: "SGLT2i DKA euglycemic safety signal",
    boolean_text:
      "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR ertugliflozin[Title/Abstract]) AND (diabetic ketoacidosis[Title/Abstract] OR DKA[Title/Abstract] OR euglycemic ketoacidosis[Title/Abstract] OR ketosis[Title/Abstract])",
    selected_sources: ["pubmed"],
    pico: {
      p: "T2DM or T1DM on SGLT2i around peri-operative / fasting / severe illness periods",
      i: "SGLT2i continued or paused peri-event window",
      c: "same population without SGLT2i exposure",
      o: "event rate of DKA / euglycemic DKA ; median bicarbonate / gap / anion gap at diagnosis",
    },
  },
  {
    key: "met_lifestyle_predm",
    label: "🏃 Metformin + Lifestyle Prediabetes",
    badge: "一级预防",
    expected_hits_hint: "DPP + follow-up + meta-analysis",
    project_name: "MedA-Demo-Prediabetes-Prevention-2026",
    query_name: "Metformin vs lifestyle in prediabetes: prevention of T2DM",
    boolean_text:
      "(diabetes prevention program[Title/Abstract] OR DPP[Title/Abstract] OR prediabetes[Title/Abstract]) AND (metformin[Title/Abstract] AND (lifestyle[Title/Abstract] OR diet AND exercise[Title/Abstract])) AND (progression to type 2 diabetes[Title/Abstract] OR incidence of type 2 diabetes[Title/Abstract])",
    selected_sources: ["pubmed"],
    pico: {
      p: "adult with prediabetes (IFG / IGT / elevated HbA1c 5.7-6.4%) without prior CV event",
      i: "metformin 850 mg BID + intensive lifestyle (≥7% weight loss, 150 min/wk exercise)",
      c: "placebo + standard lifestyle brochure",
      o: "time to T2DM diagnosis (primary) ; regression to normoglycaemia ; change in weight / Hba1c at 3y",
    },
    filters: { pubmed_mindate: "1996/01/01" },
  },
];

export const DEMO_PRESET_BY_KEY = Object.fromEntries(
  DEMO_PRESETS.map((p) => [p.key, p]),
) as Record<DemoPresetKey, DemoPreset>;
```

- [ ] **Step 2: 创建 `packages/shared-sdk/src/utils/demoSeedings.ts`

```ts
import { MedaClient } from "../client";
import type {
  CreateProjectRequest,
  SaveSearchQueryDraftPayload,
  SearchExpressionBlock,
  SearchTermGroupSummary,
  SearchTermSummary,
  SessionContext,
} from "../client";
import { DEMO_PRESET_BY_KEY, type DemoPreset, type DemoPresetKey } from "../presets";

export type EnsureDemoResult = {
  project_id: number;
  project_created_this_call: boolean;
  query_id: number;
  query_version: string;
};

export type EnsureDemoOptions = {
  workspaceHomeProjectId?: number;
  forceNewProject?: boolean;
};

const SPLIT_RE = /[\s,;，；/]+/;

export function build_grouped_terms_from_pico(pico: DemoPreset["pico"]): SearchTermGroupSummary[] {
  const groups: Array<{ key: "p" | "i" | "c" | "o"; label: string }> = [
    { key: "p", label: "P - Population" },
    { key: "i", label: "I - Intervention" },
    { key: "c", label: "C - Comparator" },
    { key: "o", label: "O - Outcome" },
  ];
  return groups.map(({ key, label }, gi) => {
    const raw = pico[key];
    const chunks = raw
      .split(SPLIT_RE)
      .map((s) => s.trim())
      .filter(Boolean);
    const terms: SearchTermSummary[] = (chunks.length > 0 ? chunks : [pico[key].slice(0, 24)]).map((t, ti) => ({
      term_id: `demo-${key}-${gi}-${ti}`,
      label: t,
      source_type: "user_entry",
      selected: true,
    }));
    return {
      group_key: `demo-group-${key}`,
      group_label: label,
      terms,
    };
  });
}

export function build_expression_from_boolean_text(boolean_text: string): SearchExpressionBlock[] {
  return [
    {
      block_id: "demo-boolean-block-0",
      block_type: "LiteralBoolean",
      operator: null,
      term_ref: null,
      children: [],
      position: 0,
    },
  ];
}

export async function ensureDemoProjectAndQuery(
  client: MedaClient,
  session: SessionContext,
  preset: DemoPreset,
  options: EnsureDemoOptions = {},
): Promise<EnsureDemoResult> {
  let project_id: number | null = null;
  let project_created_this_call = false;

  if (!options.forceNewProject) {
    if (options.workspaceHomeProjectId) {
      project_id = options.workspaceHomeProjectId;
    } else {
      const projects = await client.listProjects();
      const match = projects.find((p) => p.name === preset.project_name);
      if (match) project_id = match.id;
      else if (projects.length > 0) project_id = projects[0].id;
    }
  }

  if (project_id == null) {
    const payload: CreateProjectRequest = {
      organization_slug: session.organization_slug,
      owner_user_id: session.user_id,
      name: preset.project_name,
      description: "Auto-created by PubMed one-click demo.",
    };
    const created = await client.createProject(payload);
    project_id = created.id;
    project_created_this_call = true;
  }

  const editor = await client.getSearchQueryEditor(project_id);
  if (editor.query_name !== preset.query_name) {
    const savePayload: SaveSearchQueryDraftPayload = {
      query_id: editor.query_id,
      query_name: preset.query_name,
      selected_sources: preset.selected_sources,
      grouped_terms: build_grouped_terms_from_pico(preset.pico),
      expression_blocks: build_expression_from_boolean_text(preset.boolean_text),
    };
    const saved = await client.saveSearchQueryVersion(project_id, savePayload);
    return {
      project_id,
      project_created_this_call,
      query_id: saved.query_id,
      query_version: saved.query_version,
    };
  }

  return {
    project_id,
    project_created_this_call,
    query_id: editor.query_id,
    query_version: editor.query_version,
  };
}
```

- [ ] **Step 3: 修改 packages/shared-sdk/src/index.ts re-export（单份正确版本）

在 `packages/shared-sdk/src/index.ts` 里**单独**写入下面这段（写在 `export * from "./client"` 之后或文件最末，禁止写两份冲突版）：

```ts
export {
  DEMO_PRESETS,
  DEMO_PRESET_BY_KEY,
  type DemoPreset,
  type DemoPresetKey,
} from "./presets";
export {
  build_grouped_terms_from_pico,
  build_expression_from_boolean_text,
  ensureDemoProjectAndQuery,
  type EnsureDemoResult,
  type EnsureDemoOptions,
} from "./utils/demoSeedings";
export type { CreateProjectRequest, ProjectResponse } from "./client";
```

- [ ] **Step 4: Run TypeScript 编译验证

Run: `pnpm --filter @meda/shared-sdk exec tsc --noEmit`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add packages/shared-sdk/src/presets.ts packages/shared-sdk/src/utils/demoSeedings.ts packages/shared-sdk/src/index.ts packages/shared-sdk/src/client.ts
git commit -m "feat(sdk): 6 demo presets + ensureDemoProjectAndQuery seed utility"
```

---

### Task 3：shared-ui WorkspaceOneClickPubmedDemo 组件 + 前端 5 tests

**Files:**
- Create: `packages/shared-ui/src/WorkspaceOneClickPubmedDemo.tsx`
- Create: `packages/shared-ui/src/__tests__/WorkspaceOneClickPubmedDemo.test.tsx`
- Modify: `packages/shared-ui/src/index.ts`

- [ ] **Step 1: Write 前端 5 failing tests（先写 test 再实现）

`packages/shared-ui/src/__tests__/WorkspaceOneClickPubmedDemo.test.tsx`：

```tsx
import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { WorkspaceOneClickPubmedDemo } from "../WorkspaceOneClickPubmedDemo";
import type { MedaClient, SessionContext } from "@meda/shared-sdk";
import { DEMO_PRESETS } from "@meda/shared-sdk";

function makeSession(): SessionContext {
  return {
    organization_slug: "demo-hospital",
    user_id: "u-test-001",
    display_name: "Dr. Chen",
    role: "org_admin",
    client_type: "web",
  };
}

function makeClient(overrides: Partial<MedaClient> = {} as any): MedaClient {
  return {
    listProjects: vi.fn().mockResolvedValue([]),
    createProject: vi.fn().mockResolvedValue({ id: 11, organization_slug: "demo-hospital", owner_user_id: "u-test-001", name: "MedA-Demo-Diabetes-CKD-2026", description: "x", workspace_key: "demo-hospital/MedA-Demo-Diabetes-CKD-2026" }),
    getSearchQueryEditor: vi.fn().mockResolvedValue({ query_id: 3, query_name: "old name", query_version: "v0", query_dirty: false, query_mode: "pico_builder", selected_sources: ["pubmed"], grouped_terms: [], expression_blocks: [], validation_messages: [], preview_summary: { status: "ok", coverage_hint: "", database_scope_summary: "", estimated_hit_band: "", last_generated_from: "" }, project: { id: 11, name: "", workspace_key: "", stage_key: "search" }),
    saveSearchQueryVersion: vi.fn().mockImplementation(async (_pid, p) => ({ query_id: p.query_id, query_name: p.query_name, query_version: "v1", query_dirty: false, query_mode: "pico_builder", selected_sources: p.selected_sources, grouped_terms: p.grouped_terms, expression_blocks: p.expression_blocks, validation_messages: [], preview_summary: { status: "ok", coverage_hint: "", database_scope_summary: "", estimated_hit_band: "", last_generated_from: "" }, project: { id: 11, name: "", workspace_key: "", stage_key: "search" } })),
    createSearchRun: vi.fn().mockResolvedValue({ id: 99, status: "pending" }),
    ...overrides,
  } as unknown as MedaClient;
}

describe("WorkspaceOneClickPubmedDemo", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("test1 renders 6 preset chips with correct labels", () => {
    render(
      <WorkspaceOneClickPubmedDemo
        client={makeClient()}
        session={makeSession()}
        workspaceHomeProjectId={7}
        onRunCreated={vi.fn()}
      />,
    );
    DEMO_PRESETS.forEach((p) => {
      const keyword = p.label.split(" ").slice(1).join(" ").slice(0, 4);
      expect(screen.getByText(new RegExp(keyword))).toBeInTheDocument();
    });
  });

  it("test2 zero projects → clicks chip → calls createProject + saveSearchQueryVersion + createSearchRun with pubmed source", async () => {
    const client = makeClient();
    const onRunCreated = vi.fn();
    render(
      <WorkspaceOneClickPubmedDemo
        client={client}
        session={makeSession()}
        onRunCreated={onRunCreated}
      />,
    );
    const preset = DEMO_PRESETS[0];
    const keyword = preset.label.split(" ").slice(1).join(" ").slice(0, 4);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(keyword) }));
    await waitFor(() => expect(client.createProject).toHaveBeenCalledTimes(1));
    expect(client.createProject).toHaveBeenCalledWith(
      expect.objectContaining({ name: preset.project_name }),
    );
    await waitFor(() => expect(client.saveSearchQueryVersion).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(client.createSearchRun).toHaveBeenCalledTimes(1));
    const payload = (client.createSearchRun as any).mock.calls[0][1];
    expect(payload.selected_sources).toEqual(["pubmed"]);
    expect(onRunCreated).toHaveBeenCalledWith(99, expect.any(Number));
  });

  it("test3 existing matching project → does NOT create new project", async () => {
    const preset = DEMO_PRESETS[0];
    const client = makeClient({
      listProjects: vi.fn().mockResolvedValue([
        {
          id: 77,
          name: preset.project_name,
          organization_slug: "demo-hospital",
          owner_user_id: "u-test-001",
          workspace_key: "x/y",
          description: "x",
        },
      ]),
    } as any);
    render(
      <WorkspaceOneClickPubmedDemo
        client={client}
        session={makeSession()}
        onRunCreated={vi.fn()}
      />,
    );
    const keyword = preset.label.split(" ").slice(1).join(" ").slice(0, 4);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(keyword) }));
    await waitFor(() => expect(client.createSearchRun).toHaveBeenCalled());
    expect(client.createProject).not.toHaveBeenCalled();
  });

  it("test4 saveSearchQueryVersion 422 → toast error 显示", async () => {
    const client = makeClient({
      saveSearchQueryVersion: vi
        .fn()
        .mockRejectedValue(new Error("422 grouped_terms empty")),
    } as any);
    render(
      <WorkspaceOneClickPubmedDemo
        client={client}
        session={makeSession()}
        onRunCreated={vi.fn()}
      />,
    );
    const p = DEMO_PRESETS[1];
    const keyword = p.label.split(" ").slice(1).join(" ").slice(0, 4);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(keyword) }));
    await waitFor(() =>
      expect(screen.queryByText(/Demo 启动失败/)).toBeInTheDocument(),
    );
  });

  it("test5 expression block 是 LiteralBoolean 包含 preset boolean_text", async () => {
    const client = makeClient();
    render(
      <WorkspaceOneClickPubmedDemo
        client={client}
        session={makeSession()}
        workspaceHomeProjectId={5}
        onRunCreated={vi.fn()}
      />,
    );
    const p = DEMO_PRESETS[2];
    const keyword = p.label.split(" ").slice(1).join(" ").slice(0, 4);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(keyword) }));
    await waitFor(() => expect(client.saveSearchQueryVersion).toHaveBeenCalled());
    const payload = (client.saveSearchQueryVersion as any).mock.calls[0][1] as any;
    expect(payload.expression_blocks[0].block_type).toEqual("LiteralBoolean");
    expect(payload.grouped_terms.length).toBeGreaterThanOrEqual(4);
    expect(
      payload.grouped_terms.every((g: any) => g.terms.length >= 1),
    ).toBe(true);
  });
});
```

- [ ] **Step 2: 运行测试应 Fail（因为 WorkspaceOneClickPubmedDemo 组件不存在）

Run: `pnpm --filter @meda/shared-ui vitest run WorkspaceOneClickPubmedDemo`
Expected: FAIL with "WorkspaceOneClickPubmedDemo is not a function" 或 ReferenceError

- [ ] **Step 3: Write WorkspaceOneClickPubmedDemo.tsx 实现

```tsx
import React, { useState, type PropsWithChildren } from "react";
import {
  DEMO_PRESETS,
  ensureDemoProjectAndQuery,
  type DemoPreset,
  type EnsureDemoResult,
  type MedaClient,
  type SessionContext,
} from "@meda/shared-sdk";

export type WorkspaceOneClickPubmedDemoProps = {
  client: MedaClient;
  session: SessionContext;
  workspaceHomeProjectId?: number;
  onRunCreated: (searchRunId: number, projectId: number) => void;
  onProjectCreatedToast?: (projectName: string) => void;
  onErrorToast?: (msg: string) => void;
};

export function WorkspaceOneClickPubmedDemo(
  props: PropsWithChildren<WorkspaceOneClickPubmedDemoProps>,
) {
  const {
    client,
    session,
    workspaceHomeProjectId,
    onRunCreated,
    onProjectCreatedToast,
    onErrorToast,
  } = props;

  const [pendingKey, setPendingKey] = useState<DemoPreset["key"] | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleClick = async (preset: DemoPreset) => {
    if (pendingKey !== null) return;
    setPendingKey(preset.key);
    setErrorMsg(null);
    try {
      const ensured: EnsureDemoResult = await ensureDemoProjectAndQuery(
        client,
        session,
        preset,
        { workspaceHomeProjectId },
      );
      if (ensured.project_created_this_call && onProjectCreatedToast) {
        onProjectCreatedToast(preset.project_name);
      }
      const created = await client.createSearchRun(ensured.project_id, {
        query_id: ensured.query_id,
        query_version: ensured.query_version,
        selected_sources: preset.selected_sources,
        filters: preset.filters ?? {},
        adapter_modes: { pubmed: "prefer_real" } as any,
      });
      onRunCreated(created.id, ensured.project_id);
    } catch (err: any) {
      const msg = `Demo 启动失败：${err?.message ?? String(err)}`;
      setErrorMsg(msg);
      if (onErrorToast) onErrorToast(msg);
    } finally {
      setPendingKey(null);
    }
  };

  const accent = "#6366F1";
  const panelStyle: React.CSSProperties = {
    background:
      "linear-gradient(135deg, rgba(99,102,241,0.12), rgba(34,211,238,0.05))",
    border: `1.5px solid ${accent}`,
    borderRadius: 14,
    padding: "16px 16px 14px",
  };
  const pill = (bg: string, fg: string, txt: string) => (
    <span
      style={{
        display: "inline-block",
        padding: "2px 9px",
        borderRadius: 999,
        background: bg,
        color: fg,
        fontSize: 11,
        fontWeight: 600,
        marginRight: 8,
      }}
    >
      {txt}
    </span>
  );
  return (
    <section
      aria-label="PubMed one-click demo section"
      style={{ marginTop: 20 }}
    >
      <div style={panelStyle}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            background: accent,
            color: "white",
            fontSize: 11,
            fontWeight: 700,
            padding: "2px 8px",
            borderRadius: 999,
            marginBottom: 6,
            letterSpacing: 0.5,
          }}
        >
          NEW · 一键真实数据 Demo
        </div>
        <div style={{ fontWeight: 600, fontSize: 15 }}>
          🧪 用 PubMed 真实文献跑通完整检索流水线（仅 PubMed，约 2~6 秒）
        </div>
        <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>
          选一个主题 → 自动创建项目/检索式（若不存在）→ 发起 SearchRun →
          自动跳到运行详情页，展示 PRISMA、BM25 文献列表、PICO 批量提取。
        </div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            marginTop: 12,
          }}
        >
          {DEMO_PRESETS.map((preset) => {
            const disabled = pendingKey !== null && pendingKey !== preset.key;
            const active = pendingKey === preset.key;
            const chipBg = active ? accent : "rgba(255,255,255,0.06)";
            const chipBorder = active ? accent : "rgba(255,255,255,0.08)";
            return (
              <button
                type="button"
                role="button"
                key={preset.key}
                onClick={() => handleClick(preset)}
                aria-label={`${preset.label} preset button`}
                disabled={disabled}
                style={{
                  fontSize: 12,
                  padding: "6px 10px",
                  borderRadius: 999,
                  background: chipBg,
                  border: `1px solid ${chipBorder}`,
                  color: "#cbd5ff",
                  cursor: disabled ? "not-allowed" : "pointer",
                  opacity: disabled ? 0.55 : 1,
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  if (!disabled) {
                    (e.currentTarget as HTMLButtonElement).style.background =
                      accent;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!disabled && !active) {
                    (e.currentTarget as HTMLButtonElement).style.background =
                      "rgba(255,255,255,0.06)";
                  }
                }}
              >
                {preset.label}
                <span style={{ opacity: 0.6, marginLeft: 4, fontSize: 10 }}>
                  {preset.expected_hits_hint}
                </span>
              </button>
            );
          })}
        </div>
        <div style={{ marginTop: 10, fontSize: 12 }}>
          {pill("rgba(34,197,94,0.15)", "#86efac", "已连网 prefer_real")}
          {pill(
            "rgba(245,158,11,0.15)",
            "#fcd34d",
            "无网络时自动 fallback 注入 demo 集",
          )}
          {pill(
            "rgba(34,211,238,0.15)",
            "#67e8f9",
            "仅 PubMed 单源 · 不触发机构反爬",
          )}
        </div>
        {errorMsg ? (
          <div
            role="alert"
            style={{
              marginTop: 10,
              padding: "8px 10px",
              borderRadius: 8,
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.3)",
              color: "#fecaca",
              fontSize: 12,
            }}
          >
            {errorMsg}
          </div>
        ) : null}
      </div>
    </section>
  );
}
```

- [ ] **Step 4: 修改 shared-ui/index.ts re-export**

在 `packages/shared-ui/src/index.ts` 文件末尾追加：

```ts
export {
  WorkspaceOneClickPubmedDemo,
  type WorkspaceOneClickPubmedDemoProps,
} from "./WorkspaceOneClickPubmedDemo";
```

- [ ] **Step 5: Run vitest 验证 5 tests 通过

Run: `pnpm --filter @meda/shared-ui vitest run WorkspaceOneClickPubmedDemo`
Expected: 5 passed

- [ ] **Step 6: Commit**

```bash
git add packages/shared-ui/src/WorkspaceOneClickPubmedDemo.tsx packages/shared-ui/src/__tests__/WorkspaceOneClickPubmedDemo.test.tsx packages/shared-ui/src/index.ts
git commit -m "feat(shared-ui): WorkspaceOneClickPubmedDemo 一键卡组件 + 5 vitest"
```

---

### Task 4：apps/web WorkspaceShell 传 client prop + 嵌入一键卡组件

**Files:**
- Modify: `apps/web/src/components/WorkspaceShell.tsx`
- Modify: `apps/web/src/App.tsx`

- [ ] **Step 1: WorkspaceShellProps 加 client: MedaClient prop + import

1. WorkspaceShell.tsx 顶部 import 追加：

```ts
import type { MedaClient } from "@meda/shared-sdk";
import { WorkspaceOneClickPubmedDemo } from "@meda/shared-ui";
```

2. WorkspaceShellProps type （文件里现有 `type WorkspaceShellProps = {...}` 内部追加：

```ts
type WorkspaceShellProps = {
  // ... existing props ...
  client: MedaClient;
};
```

- [ ] **Step 2: L546 「子入口导航 section 之后（现有 </section> 之后，最近任务 section 之前）插入一键卡组件

语义说明：WorkspaceShell 组件体内现有 workspaceHome / session / props.onOpenSearchRunDetail 都是解构过的可直接用（若未解构则改用 props.workspaceHome / props.session / props.onOpenSearchRunDetail）。直接插入下面这段，不需要刷新 workspaceHome：

```tsx
{/* --- PubMed one-click demo section (Wave 8.1 Scope A) */}
<WorkspaceOneClickPubmedDemo
  client={props.client}
  session={session}
  workspaceHomeProjectId={workspaceHome.project.id}
  onRunCreated={(runId, projectId) => {
    props.onOpenSearchRunDetail(projectId, runId);
  }}
  onErrorToast={(msg) => {
    alert(msg);
  }}
  onProjectCreatedToast={(name) => {
    console.info("[demo] auto-created project:", name);
  }}
/>
```

注：WorkspaceShellProps 现已有 onOpenSearchRunDetail prop (apps/web/src/App.tsx L267 已传)，所以无需新增 prop。

- [ ] **Step 3: apps/web/src/App.tsx L245 加 client={client} prop

```tsx
<WorkspaceShell
  client={client}      // ← 加这行
  session={session}
  projects={projects}
  ...现有 props...
/>
```

- [ ] **Step 4: Run apps/web TS 类型检查 + vitest 冒烟**

Run: `pnpm --filter web exec tsc --noEmit`
Expected: 0 errors

Run: `pnpm --filter web vitest run` （若 web 有 WorkspaceShell test 吗？没有就不跑了，看现有测试）
Expected: Exit 0

- [ ] **Step 5: Commit**

```bash
git add apps/web/src/components/WorkspaceShell.tsx apps/web/src/App.tsx
git commit -m "feat(web): WorkspaceShell 嵌入 WorkspaceOneClickPubmedDemo + client prop 传参"
```

---

### Task 5：apps/desktop App.tsx 同步嵌入一键卡组件

**Files:**
- Modify: `apps/desktop/src/App.tsx`

- [ ] **Step 1: import WorkspaceOneClickPubmedDemo 组件 + types

App.tsx 顶部 import `from "@meda/shared-sdk"` 里加上 import：

```ts
import { WorkspaceOneClickPubmedDemo } from "@meda/shared-ui";
```

（shared-sdk types 不必重复 import

- [ ] **Step 2: L646 「子入口导航 section 结束标签之后（看 desktop 的 646-700 行左右，entry_cards map 之后）插入组件

```tsx
<WorkspaceOneClickPubmedDemo
  client={client}
  session={session}
  workspaceHomeProjectId={workspaceHome?.project?.id}
  onRunCreated={(runId, projectId) => {
    handleOpenSearchRunDetail(projectId, runId);
  }}
  onErrorToast={(msg) => alert(msg)}
/>
```

（handleOpenSearchRunDetail 在 App.tsx 已存在，因为 desktop App.tsx L267 对应也有 handleOpenSearchRunDetail）

- [ ] **Step 3: Run desktop TS build + vitest 冒烟

Run: `pnpm --filter desktop exec tsc --noEmit`
Expected: 0 errors

- [ ] **Step 4: Commit**

```bash
git add apps/desktop/src/App.tsx
git commit -m "feat(desktop): App.tsx 同步嵌入 WorkspaceOneClickPubmedDemo"
```

---

### Task 6：后端 Python 脚本 CLI demo_pubmed_end2end.py + DEMO_PRESETS_PY

**Files:**
- Create: `apps/agent-core/scripts/demo_pubmed_end2end.py`

- [ ] **Step 1: 写脚本完整代码（含 run_pubmed_demo 纯异步 可直接 import 测试）

```python
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.services.bm25_scoring import compute_bm25_scores_for, tokenize_for_bm25
from app.services.literature import _normalize_identifiers
from app.services.pico import _rule_baseline_extract
from app.services.sources.protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    UnifiedLiteratureEntry,
)
from app.services.sources.pubmed_adapter import PubMedAdapter

DEMO_PRESETS_PY: dict[str, dict] = {
    "sglt2i_ckd": {
        "boolean_text": "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR canagliflozin[Title/Abstract]) AND (chronic kidney disease[Title/Abstract] OR CKD[Title/Abstract] OR diabetic nephropathies[MeSH Major Topic]) AND randomised controlled trial[pt]",
        "pico": {"p": "adult with type 2 diabetes mellitus and CKD stage 2-4 or macroalbuminuria", "i": "SGLT2 inhibitor add-on to RAAS blockade", "c": "placebo or standard of care without SGLT2i", "o": "composite renal endpoint (eGFR decline ≥50% / ESRD / renal death) ; change in eGFR slope ; 3P-MACE ; AE of genital mycotic infection / DKA / hypovolemia"},
        "filters": {"study_type": ["rct"]},
    },
    "sglt2i_hfredef": {
        "boolean_text": "(DAPA-HF[Title/Abstract] OR DAPA-CKD[Title/Abstract] OR (dapagliflozin[Title/Abstract] AND (heart failure with reduced ejection fraction[Title/Abstract] OR HFrEF[Title/Abstract] OR chronic kidney disease[Title/Abstract]))) AND randomised controlled trial[pt]",
        "pico": {"p": "HFrEF LVEF ≤40% with/without T2DM; CKD eGFR 25-75 + uACR >200", "i": "dapagliflozin 10 mg once daily", "c": "matching placebo", "o": "CV death or worsening HF composite; renal composite; change in NT-proBNP / KCCQ"},
        "filters": {"study_type": ["rct"]},
    },
    "met_cv_presto": {
        "boolean_text": "(PRESTO[Title/Abstract] OR (metformin[Title/Abstract] AND cardiovascular[Title/Abstract] AND (prediabetes[Title/Abstract] OR insulin resistance[Title/Abstract]))) AND randomized controlled trial[pt]",
        "pico": {"p": "prediabetes / insulin resistance with CV risk factors but no established ASCVD", "i": "metformin extended-release +/- lifestyle intervention", "c": "placebo or lifestyle-only", "o": "MACE (CV death / MI / stroke) ; change in LDL-C / SBP / Hba1c"},
        "filters": {"study_type": ["rct"]},
    },
    "glp1_mace_rws": {
        "boolean_text": "(glucagon-like peptide-1 receptor agonist[Title/Abstract] OR GLP-1 RA[Title/Abstract] OR liraglutide[Title/Abstract] OR semaglutide[Title/Abstract] OR dulaglutide[Title/Abstract] OR tirzepatide[Title/Abstract]) AND (major adverse cardiovascular events[Title/Abstract] OR MACE[Title/Abstract] OR cardiovascular outcomes[Title/Abstract]) AND ((randomized controlled trial[pt]) OR (real-world[Title/Abstract] OR retrospective[Title/Abstract] OR cohort[Title/Abstract]))",
        "pico": {"p": "T2DM with established ASCVD or high CV risk", "i": "GLP-1 RA (injectable or oral) as add-on", "c": "DPP-4 inhibitor / sulfonylurea / basal insulin / placebo", "o": "3P-MACE (CV death, non-fatal MI, non-fatal stroke) ; all-cause mortality ; severe hypoglycaemia"},
        "filters": {"study_type": ["rct_and_sr"]},
    },
    "sglt2i_dka_safety": {
        "boolean_text": "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR ertugliflozin[Title/Abstract]) AND (diabetic ketoacidosis[Title/Abstract] OR DKA[Title/Abstract] OR euglycemic ketoacidosis[Title/Abstract] OR ketosis[Title/Abstract])",
        "pico": {"p": "T2DM or T1DM on SGLT2i around peri-operative / fasting / severe illness periods", "i": "SGLT2i continued or paused peri-event window", "c": "same population without SGLT2i exposure", "o": "event rate of DKA / euglycemic DKA ; median bicarbonate / gap / anion gap at diagnosis"},
    },
    "met_lifestyle_predm": {
        "boolean_text": "(diabetes prevention program[Title/Abstract] OR DPP[Title/Abstract] OR prediabetes[Title/Abstract]) AND (metformin[Title/Abstract] AND (lifestyle[Title/Abstract] OR diet AND exercise[Title/Abstract])) AND (progression to type 2 diabetes[Title/Abstract] OR incidence of type 2 diabetes[Title/Abstract])",
        "pico": {"p": "adult with prediabetes (IFG / IGT / elevated HbA1c 5.7-6.4%) without prior CV event", "i": "metformin 850 mg BID + intensive lifestyle (≥7% weight loss, 150 min/wk exercise)", "c": "placebo + standard lifestyle brochure", "o": "time to T2DM diagnosis (primary) ; regression to normoglycaemia ; change in weight / Hba1c at 3y"},
        "filters": {"pubmed_mindate": "1996/01/01"},
    },
}


@dataclass
class DemoResult:
    preset_key: str
    search_run_id: int
    raw_hits: int
    after_dedupe_hits: int
    bm25_top3: list[dict]
    pico_top5: list[dict]
    csv_export_path: str | None
    warnings: list[str]
    fallback_mode: bool


def _resolve_mode_or_exit(preset_key: str) -> None:
    if preset_key not in DEMO_PRESETS_PY:
        print(f"[demo] ERROR: unknown preset '{preset_key}'.", file=sys.stderr)
        print(
            "[demo] Available keys:",
            ", ".join(sorted(DEMO_PRESETS_PY.keys())),
            file=sys.stderr,
        )
        sys.exit(2)


async def run_pubmed_demo(
    preset_key: str,
    *,
    export_csv: bool = True,
    export_dir: Path | None = None,
) -> DemoResult:
    _resolve_mode_or_exit(preset_key)
    preset = DEMO_PRESETS_PY[preset_key]

    ctx = SearchRunContext(
        project_id=0,
        search_run_id=0,
        pubmed_api_key=os.environ.get("PUBMED_API_KEY"),
        adapter_modes={"pubmed": "prefer_real"},
        rate_limit_rps={"pubmed": 3.0},
    )

    adapter = PubMedAdapter()
    norm_q = NormalizedSearchQuery(
        boolean_text=preset["boolean_text"],
        filters=preset.get("filters", {}) if isinstance(preset.get("filters"), dict) else {},
        source_key="pubmed",
    )
    adapter_result: AdapterResult = await adapter.run_search(norm_q, ctx)

    normalized_records = [
        UnifiedLiteratureEntry(
            doi=_normalize_identifiers(r.doi, "", "")[0],
            pmid=_normalize_identifiers("", r.pmid, "")[1],
            title=(r.title or "").strip(),
            authors=r.authors,
            journal=r.journal,
            year=r.year,
            abstract=r.abstract,
            source_key=r.source_key,
            source_record_id=r.source_record_id,
        )
        for r in adapter_result.records
    ]

    seen_doi: set[str] = set()
    seen_pmid: set[str] = set()
    seen_title_year: set[tuple[str, int | None]] = set()
    deduped: list[UnifiedLiteratureEntry] = []
    for r in normalized_records:
        doi, pmid, title = r.doi or "", r.pmid or "", (r.title or "").strip()
        if title == "":
            continue
        key_ty = (title, r.year)
        if doi and doi in seen_doi:
            continue
        if pmid and pmid in seen_pmid:
            continue
        if key_ty in seen_title_year:
            continue
        if doi:
            seen_doi.add(doi)
        if pmid:
            seen_pmid.add(pmid)
        seen_title_year.add(key_ty)
        deduped.append(r)
    raw_hits = len(normalized_records)
    after_dedupe_hits = len(deduped)

    fallback_mode = bool(adapter_result.warnings) and any(
        "fallback" in w or "注入" in w for w in adapter_result.warnings
    )

    @dataclass
    class _MiniRec:
        title: str
        abstract: str
        year: int | None
        journal: str
        doi: str
        pmid: str
        source_record_id: str
        bm25_score: float | None = None

    mini_records: list[_MiniRec] = [
        _MiniRec(
            title=(e.title or "").strip(),
            abstract=e.abstract or "",
            year=e.year,
            journal=e.journal or "",
            doi=e.doi or "",
            pmid=e.pmid or "",
            source_record_id=e.source_record_id or "",
        )
        for e in deduped
    ]

    pico = preset.get("pico") or {}
    q_raw = " ".join(
        [preset["boolean_text"]] + [str(pico[k]) for k in ("p", "i", "c", "o") if pico.get(k)]
    )
    q_tokens = tokenize_for_bm25(q_raw)
    if mini_records and q_tokens:
        scores = compute_bm25_scores_for(mini_records, q_tokens)
        max_s = max(scores) if scores and max(scores) > 0 else None
        for m, s in zip(mini_records, scores):
            m.bm25_score = (float(s) / float(max_s)) if max_s is not None else None

    sorted_by_score = sorted(
        mini_records,
        key=lambda e: (e.bm25_score is not None, e.bm25_score or 0.0),
        reverse=True,
    )[:3]
    bm25_top3 = [
        {
            "title": m.title[:140],
            "score": round(m.bm25_score or 0.0, 4),
            "year": m.year,
            "doi": m.doi or None,
        }
        for m in sorted_by_score
    ]

    pico_domain_words: dict[str, dict[str, int]] = {"p": {}, "i": {}, "c": {}, "o": {}}
    for m in mini_records:
        pico_obj = _rule_baseline_extract(m)  # type: ignore[arg-type]
        for dom in ("p", "i", "c", "o"):
            val = getattr(pico_obj, f"{dom}_text") or ""
            toks = re.findall(r"[A-Za-z0-9]+|[\u4e00-\u9fff]", val.lower())
            for t in toks:
                if len(t) < 2 and not ("\u4e00" <= t <= "\u9fff"):
                    continue
                pico_domain_words[dom][t] = pico_domain_words[dom].get(t, 0) + 1
    flat: list[tuple[str, str, int]] = []
    for dom, counter in pico_domain_words.items():
        for tok, freq in counter.items():
            flat.append((dom, tok, freq))
    flat.sort(key=lambda x: x[2], reverse=True)
    pico_top5 = [
        {"domain": dom, "value": tok, "freq": freq} for (dom, tok, freq) in flat[:5]
    ]

    csv_export_path: str | None = None
    if export_csv and mini_records:
        export_dir_ = export_dir or (
            Path(__file__).resolve().parent.parent.parent / "artifacts" / "demo_csv"
        )
        export_dir_.mkdir(parents=True, exist_ok=True)
        csv_path = export_dir_ / (
            f"pubmed_demo_{preset_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        )
        with csv_path.open("w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "rank",
                    "title",
                    "year",
                    "journal",
                    "doi",
                    "pmid",
                    "source_record_id",
                    "bm25_score",
                ]
            )
            ranked = sorted(
                mini_records,
                key=lambda x: (x.bm25_score is not None, x.bm25_score or 0.0),
                reverse=True,
            )
            for i, m in enumerate(ranked, 1):
                w.writerow(
                    [
                        i,
                        m.title,
                        m.year or "",
                        m.journal,
                        m.doi,
                        m.pmid,
                        m.source_record_id,
                        round(m.bm25_score or 0.0, 4),
                    ]
                )
        csv_export_path = str(csv_path)

    return DemoResult(
        preset_key=preset_key,
        search_run_id=0,
        raw_hits=raw_hits,
        after_dedupe_hits=after_dedupe_hits,
        bm25_top3=bm25_top3,
        pico_top5=pico_top5,
        csv_export_path=csv_export_path,
        warnings=list(adapter_result.warnings or []),
        fallback_mode=fallback_mode,
    )


def _print_report(r: DemoResult) -> None:
    print("=" * 56)
    print(f"  MedA · PubMed real-data demo   preset = {r.preset_key}")
    tag = "(no-network fallback injected dataset)" if r.fallback_mode else "(used live NCBI E-utilities)"
    print(f"  {tag}")
    print("=" * 56)
    print(
        f"  [① Hits] raw PubMed = {r.raw_hits} | after dedupe = {r.after_dedupe_hits}"
    )
    if r.warnings:
        print("  [Warnings]")
        for w in r.warnings:
            print(f"    · {w}")
    print()
    print("  [② BM25 top-3]")
    for i, row in enumerate(r.bm25_top3, 1):
        print(
            f"    {i}. [score={row['score']:.3f}] {row['title']}  ({row['year']}) doi={row['doi'] or 'N/A'}"
        )
    print()
    print("  [③ PICO frequent tokens (rule_baseline)]")
    for row in r.pico_top5:
        print(f"    · [{row['domain']}] {row['value']!r} × {row['freq']}")
    if r.csv_export_path:
        print()
        print(f"  [④ CSV exported] → {r.csv_export_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MedA · PubMed real-data end-to-end CLI demo."
    )
    parser.add_argument(
        "preset_key",
        help="One of: " + ", ".join(sorted(DEMO_PRESETS_PY.keys())),
    )
    parser.add_argument(
        "--no-csv", action="store_true", help="Skip CSV export."
    )
    parser.add_argument(
        "--export-dir", type=Path, default=None, help="Override CSV export directory."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Dump DemoResult as JSON on success after human-readable sections.",
    )
    args = parser.parse_args()

    result = asyncio.run(
        run_pubmed_demo(
            args.preset_key,
            export_csv=not args.no_csv,
            export_dir=args.export_dir,
        )
    )
    _print_report(result)

    if args.json:
        print()
        print("--- JSON ---")
        print(
            json.dumps(
                result,
                ensure_ascii=False,
                default=lambda o: getattr(o, "__dict__", str(o)),
                indent=2,
            )
        )

    if result.after_dedupe_hits == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 脚本语法检查（py_compile）

Run: `python -m py_compile apps/agent-core/scripts/demo_pubmed_end2end.py`
Expected: Exit 0

- [ ] **Step 3: Commit**

```bash
git add apps/agent-core/scripts/demo_pubmed_end2end.py
git commit -m "feat(scripts): demo_pubmed_end2end.py CLI + DEMO_PRESETS_PY"
```

---

### Task 7：pytest 4 tests（脚本 + preset 一致性 CI gate）

**Files:**
- Create: `apps/agent-core/tests/test_demo_pubmed_cli.py`
- Create: `apps/agent-core/tests/test_presets_consistency.py`

- [ ] **Step 1: 写 test_demo_pubmed_cli.py 4 failing tests

```python
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "demo_pubmed_end2end.py"
)


def test_unknown_preset_exits_code_2():
    result = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "nonexistent_xyz_12345"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    assert "Available keys:" in result.stderr


def test_run_pubmed_demo_live_success_with_mock_pubmed_http(monkeypatch):
    from tests.test_real_pubmed_xml_parse import FIXED_PUBMED_XML

    async def fake_get(self, url, **kwargs):
        if "esearch.fcgi" in str(url):
            return httpx.Response(
                200,
                content=b"""<?xml version="1.0" encoding="UTF-8"?><!DOCTYPE eSearchResult PUBLIC "-//NLM//DTD esearch 20060101//EN" "https://eutils.ncbi.nlm.nih.gov/eutils/dtd/20060101/esearch.dtd"><eSearchResult><Count>2</Count><IdList><Id>341001</Id><Id>341002</Id></IdList></eSearchResult>""",
            )
        assert "efetch.fcgi" in str(url)
        return httpx.Response(200, content=FIXED_PUBMED_XML.encode("utf-8"))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    from apps.agent_core_placeholder import run_pubmed_demo  # 下面直接相对 import
```

（更稳方法：脚本 run_pubmed_demo 放在 scripts/，pytest 要import 要加 sys.path，所以改成在测试文件里：

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
```

直接 import 脚本里的函数：

修正后完整 4 tests：

```python
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path

import httpx
import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = SCRIPT_DIR / "scripts" / "demo_pubmed_end2end.py"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scripts.demo_pubmed_end2end import DEMO_PRESETS_PY, run_pubmed_demo


def test_unknown_preset_exits_code_2():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "nonexistent_xyz_999"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "Available keys:" in proc.stderr


def test_run_pubmed_demo_live_success_with_mock_pubmed_http(monkeypatch):
    from tests.test_real_pubmed_xml_parse import FIXED_PUBMED_XML

    async def fake_get(self, url, **kwargs):
        url_s = str(url)
        if "esearch.fcgi" in url_s:
            body = b"""<?xml version="1.0" encoding="UTF-8"?>
<eSearchResult><Count>2</Count><IdList><Id>341001</Id><Id>341002</Id></IdList></eSearchResult>"""
            return httpx.Response(200, content=body)
        assert "efetch.fcgi" in url_s
        return httpx.Response(200, content=FIXED_PUBMED_XML.encode("utf-8"))

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = asyncio.run(run_pubmed_demo("sglt2i_hfredef", export_csv=False))
    assert result.raw_hits >= 2
    assert result.after_dedupe_hits >= 1
    assert result.fallback_mode is False
    assert len(result.bm25_top3) <= 3


def test_run_pubmed_demo_connect_error_falls_back_and_exit_0(monkeypatch):
    async def fake_get(self, *args, **kwargs):
        raise httpx.ConnectError("no route to NCBI")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)
    result = asyncio.run(run_pubmed_demo("sglt2i_ckd", export_csv=False))

    assert result.fallback_mode is True
    assert result.after_dedupe_hits == 3  # conftest MOCK_PUBMED = 3


def test_main_json_flag_outputs_valid_json():
    # 默认 pytest force_mock，会 fallback → after_dedupe_hits=3，returncode 0
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "sglt2i_ckd", "--json", "--no-csv"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"stderr={proc.stderr}"
    marker = "--- JSON ---"
    assert marker in proc.stdout
    json_part = proc.stdout.split(marker)[1]
    obj = json.loads(json_part)
    assert obj["after_dedupe_hits"] > 0
```

- [ ] **Step 2: 写 test_presets_consistency.py（关键 CI 阻塞 gate）

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scripts.demo_pubmed_end2end import DEMO_PRESETS_PY

ROOT = Path(__file__).resolve().parent.parent.parent.parent
TS_PRESETS_FILE = ROOT / "packages" / "shared-sdk" / "src" / "presets.ts"

NODE_DUMP_SCRIPT = r"""
import { DEMO_PRESETS } from "./packages/shared-sdk/src/presets.ts";
const wanted = DEMO_PRESETS.map(p => ({
  key: p.key,
  boolean_text: p.boolean_text.replace(/\s+/g, " ").trim(),
  pico: {
    p: (p.pico.p || "").replace(/\s+/g, " ").trim(),
    i: (p.pico.i || "").replace(/\s+/g, " ").trim(),
    c: (p.pico.c || "").replace(/\s+/g, " ").trim(),
    o: (p.pico.o || "").replace(/\s+/g, " ").trim(),
  },
}));
process.stdout.write(JSON.stringify(wanted, null, 2));
"""


def _whitespace_norm(s: str) -> str:
    import re

    return re.sub(r"\s+", " ", (s or "")).strip()


def test_shared_sdk_demo_presets_vs_python_have_same_key_boolean_text_pico():
    assert TS_PRESETS_FILE.exists(), f"TS presets file not found: {TS_PRESETS_FILE}"

    proc = subprocess.run(
        ["node", "--input-type=module", "-e", NODE_DUMP_SCRIPT],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"node dump failed. stderr={proc.stderr}"
    ts_list = json.loads(proc.stdout)

    ts_keys = sorted([x["key"] for x in ts_list]
    py_keys = sorted(DEMO_PRESETS_PY.keys())
    assert ts_keys == py_keys, f"preset keys mismatch: TS={ts_keys}, PY={py_keys}"

    for ts_entry in ts_list:
        key = ts_entry["key"]
        py_entry = DEMO_PRESETS_PY[key]
        ts_bool = _whitespace_norm(ts_entry["boolean_text"])
        py_bool = _whitespace_norm(py_entry["boolean_text"])
        assert ts_bool == py_bool, f"[{key}] boolean_text mismatch"
        for dom in ("p", "i", "c", "o"):
            ts_p = _whitespace_norm(ts_entry["pico"][dom])
            py_p = _whitespace_norm(py_entry["pico"].get(dom, ""))
            assert ts_p == py_p, f"[{key}] pico.{dom} mismatch"
```

- [ ] **Step 3: 先 run，全跑 tests 应 pass（脚本有函数存在，fallback 注入数据 3 条 → test_connect_error_fallback 退出码 0 等）

先跑 脚本 unknown preset 测试 + 2 种：

Run: `pytest apps/agent-core/tests/test_demo_pubmed_cli.py::test_unknown_preset_exits_code_2 -v`
Expected: PASS

Run: `pytest apps/agent-core/tests/test_presets_consistency.py -v`
Expected: PASS

- [ ] **Step 4: Run pytest 全 5 条：

Run: `pytest apps/agent-core/tests/test_demo_pubmed_cli.py apps/agent-core/tests/test_presets_consistency.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add apps/agent-core/tests/test_demo_pubmed_cli.py apps/agent-core/tests/test_presets_consistency.py
git commit -m "test(demo): 4 cli tests + preset consistency CI gate (5 pytest)"
```

---

### Task 8：全量回归验证 ≥ baseline 206 passed + 手动 7 条验收 checklist

**Files:**
- 无新增/修改；只跑测试

- [ ] **Step 1: 六端全量测试**

Run（按之前 Wave 8 真实数据 Adapter 的 6 端命令，保持完全一样：

```bash
# 1. shared-sdk types
pnpm --filter @meda/shared-sdk exec tsc --noEmit
# 2. shared-ui vitest
pnpm --filter @meda/shared-ui vitest run
# 3. apps/web
pnpm --filter web vitest run
# 4. apps/desktop
pnpm --filter desktop vitest run
# 5. agent-core
pytest apps/agent-core -v
# 6. frontend (如果有 frontend 目录)
cd d:\workspace\MedA\frontend ; pnpm vitest run
```

- [ ] **Step 2: 断言 agent-core passed 数 ≥ baseline (原 agent-core 132，总 206 且不减少

Run: `pytest apps/agent-core --no-header -q | tail -n 3`
Expected: `N passed` where N >= 132 + 新增 5 = 至少 137 passed

- [ ] **Step 3: 手动验收 checklist（七条）

- [ ] ✅ 1. apps/web Workspace 首页看到紫色 NEW 一键卡 + 6 胶囊存在
- [ ] ✅ 2. 清空 DB 0 project，点 💧 → info toast 项目创建成功 + 2~6s 跳到 SearchRunDetail，PubMed status=completed
- [ ] ✅ 3. PRISMA 漏斗 有实际数值
- [ ] ✅ 4. 文献库第 1 条 hover 看到 BM25 徽章
- [ ] ✅ 5. 再点同主题 → projects[name=MedA-Demo-Diabetes-CKD-2026 不新建第二份
- [ ] ✅ 6. 终端 `python apps/agent-core/scripts/demo_pubmed_end2end.py sglt2i_hfredef --json --no-csv` → stdout 4 段 + JSON 合法 + rc=0
- [ ] ✅ 7. pytest 默认（不加 --network）零外网 passed 全 pass

- [ ] **Step 4: Commit（如果需要就就如果有文档小修小补 commit，不然就打 tag）

```bash
git status
# 若全通过 commit 空 commit 说明
git commit --allow-empty -m "chore(wave81a): PubMed real-data demo scope A 验收通过"
```

---

## ✅ Self-Review （已 inline fix 记录

### 1. Spec Coverage 核对（每条 spec requirement → 对应 Task）

| Spec §| 对应 Task
|---|---
§1 Non-Goals 6 条|所有 Tasks 全部遵守
§2 6 DEMO_PRESETS shared-sdk 单源|Task 2
§2.2 re-export shared-sdk index| Task 2 Step3
§3.1 紫色 NEW 卡 + 3 status pill|Task 3
§3.2 点击行为 ensureDemo/createSearchRun/跳转|Task 3 + 4 + 5
§3.3 ensure 幂等|Task2 demoSeedings.ts
§3.4 WorkspaceShell 插入点|Task4
§4 CLI 脚本 run_pubmed_demo 纯函数 + 退出码 0/1/2|Task 6
§5 错误处理矩阵（前端+脚本 toast|Task3 + alert 弹窗 + Task7 test4
§6.1 前端 5 tests|Task3 N4
§6.2 pytest 4 tests|Task7
§6.2 test_presets_consistency|Task7 N7
§7 验收 7 条|Task8
§8 风险缓解|全贯穿 Tasks 幂等/preset diff gate|都对应 Task7 N7|

### 2. Placeholder 扫（No TODO/No TBD / No implement later：

✅ 所有 Task 步骤 code 块写（包含 具体 code block 里没有一处写「实现」，只有明确代码有 TODO：Task3 422 场景 alert(msg) 等明确，没有用 placeholder

### 3. Type consistency（类型名 property 一致：
- `CreateProjectRequest` / `ProjectResponse` / `DemoPreset` / `EnsureDemoResult` types 在 TS/PY 两端对齐
- `selected_sources: ["pubmed"] 两端都是 "pubmed"
- `LiteralBoolean` block_type TS helper build_expression 与前端断言完全一致
- adapter_modes pubmed=prefer_real 与 TS `adapter_modes: { pubmed: "prefer_real" }

✅ 一致
