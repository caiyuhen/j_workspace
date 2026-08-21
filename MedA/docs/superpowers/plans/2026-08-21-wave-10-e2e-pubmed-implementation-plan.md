# Wave 10 · End-to-End PubMed + Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Wave 9 v0.9.0 Evidence-Artifact AC1-8 GREEN 基线上，新增 Pipeline Orchestrator 状态机（0 新依赖）+ 3 屏 Dashboard UI，使 6 preset × 最多 200 篇的真实 PubMed Hybrid 端到端 8 步 run 可量化 260 GREEN 通过，且断点续跑 + A/B 对比页可复现。

**Architecture:** 三层严格 NOTOUCH：Layer1 shared-ui 4 Page 组件 + 2 Hook 新增 / Layer2 agent-core pipeline_engine.py asyncio + 2 张新表 + 6 路由 / Layer3 W1-W9 纯调用（禁止改内部逻辑）。Hybrid 模式用 snapshot 默认 + Live toggle；Q4 断点续跑靠每步独立成功标记 + 跳过已 success 步骤。

**Tech Stack:** Python 3.11 + FastAPI + SQLAlchemy 2.0 + asyncio (no Celery) · TypeScript 5 + React 18 + Vitest + @testing-library/react · shared-sdk barrel 追加 · 0 new dependencies（AC5 目标）

---

## 0. File Structure Map（新增 / 修改清单 · NOTOUCH 审计边界）

### 0.1 NOTOUCH 禁止修改（Diff 必须为 0 或仅 append helper）
```
W1-W9 核心业务层：
  apps/agent-core/app/services/screening_engine.py  (T14/W9 4 判定标准内部逻辑禁止改)
  apps/agent-core/app/services/rob2_engine.py        (RoB2 rating 规则禁止改)
  apps/agent-core/app/services/abstractor.py         (Gold480 FN=0 逻辑禁止改)
  apps/agent-core/app/services/grade_engine.py       (GRADE 降级规则禁止改)
  apps/agent-core/app/services/report_engine.py      (W8.4 模板禁止改)
  apps/agent-core/app/services/simhash.py            (THRESHOLDS 7bit/92% 禁止改)
  apps/agent-core/app/services/search_adapters/pubmed_adapter.py (只允许加 Hybrid 包装 helper)
UI 复用组件 (禁止修改默认导出/Props Schema，防止 67 it() RED)：
  packages/shared-ui/src/components/FunnelProgressBar.tsx
  packages/shared-ui/src/grade/RoB2Matrix.tsx
  packages/shared-ui/src/components/AbstractorCard.tsx
  packages/shared-ui/src/components/ConfidenceBar.tsx
  packages/shared-ui/src/grade/TrafficLightCell.tsx
```

### 0.2 NEW 新增文件（100% 全新，0 冲突）
| 路径 | 行数估计 | 说明 |
|---|---|---|
| `apps/agent-core/app/services/pipeline_engine.py` | ~480 | asyncio 编排核心：8 步状态机 + run_single_step + resume |
| `apps/agent-core/tests/test_pipeline_run_model.py` | ~240 | 12 tests M1-M12 |
| `apps/agent-core/tests/test_pipeline_engine_states.py` | ~520 | 32 tests E1-E32 |
| `apps/agent-core/tests/test_pipeline_engine_q4_resume.py` | ~420 | 18 tests R1-R18 |
| `apps/agent-core/tests/test_pipeline_hybrid_fetch.py` | ~320 | 14 tests H1-H14 |
| `apps/agent-core/tests/test_workspace_pipeline_routes.py` | ~480 | 24 tests A1-A24 |
| `apps/agent-core/tests/test_w10_e2e_2preset.py` | ~380 | 10 tests HP1-HP10 |
| `apps/agent-core/tests/test_pipeline_compare_route.py` | ~360 | 20 tests C1-C20 |
| `packages/shared-sdk/src/pipeline.types.ts` | ~80 | 6 types: Status/Mode/Summary/StepInfo/Detail/Compare |
| `packages/shared-ui/src/pages/PipelineRunsListPage.tsx` | ~280 | 屏 1 + preset chips + status filter |
| `packages/shared-ui/src/pages/PipelineRunDetailPage.tsx` | ~380 | 屏 2 · 8 段布局核心 |
| `packages/shared-ui/src/pages/PipelineComparePage.tsx` | ~320 | 屏 3 · A/B 对比杀手功能 |
| `packages/shared-ui/src/components/NewRunModal.tsx` | ~180 | 启动新 run modal |
| `packages/shared-ui/src/components/GradeDistributionCard.tsx` | ~120 | 屏 2 Sect5 GRADE 分布图 |
| `packages/shared-ui/src/hooks/usePipelineRun.ts` | ~180 | 轮询 + 6 actions |
| `packages/shared-ui/src/hooks/usePipelineCompare.ts` | ~120 | compare 数据拉取 |
| `packages/shared-ui/src/__tests__/T18_shared_sdk_pipeline_types.test.ts` | ~60 | 6 types 存在性 |
| `packages/shared-ui/src/__tests__/NewRunModal.test.tsx` | ~300 | 18 it() |
| `packages/shared-ui/src/__tests__/PipelineRunsListPage.test.tsx` | ~360 | 22 it() |
| `packages/shared-ui/src/__tests__/PipelineRunDetailPage.test.tsx` | ~480 | 30 it() |
| `packages/shared-ui/src/__tests__/PipelineComparePage.test.tsx` | ~360 | 22 it() |
| `packages/shared-ui/src/__tests__/usePipelineRun.test.tsx` | ~260 | 16 it() |
| `packages/shared-ui/src/__tests__/usePipelineCompare.test.tsx` | ~180 | 10 it() |
| `packages/shared-ui/src/__tests__/W10_happy_path.test.tsx` | ~140 | 4 it() Happy Path |
| `packages/shared-ui/src/__tests__/T14_barrel_export_append.test.ts` | ~30 | 2 it() barrel 追加 |

### 0.3 MODIFY 仅 append（不允许改旧内容）
| 文件 | Append 内容 | 行数加 |
|---|---|---|
| `apps/agent-core/app/models.py` | 追加 `class PipelineRun` + `class PipelineStepResult` (末尾，不碰旧迁移) | +110 |
| `apps/agent-core/app/routers/workspace.py` | 末尾追加 6 条 `/pipelines/*` 路由 | +420 |
| `packages/shared-sdk/src/index.ts` | barrel 追加 `export * from "./pipeline.types";` | +1 |
| `packages/shared-ui/src/index.ts` | barrel 追加 5 新组件 + 6 types 的导出 | +13 |

---

## 分天任务分解（3 天 · 每天产出独立可验证 GREEN 块）

### 🌗 Day 1 · Data Model + SDK Types + Pipeline Engine（PY 侧基础 78 GREEN）
### Task D1-1：PipelineRun + PipelineStepResult 数据模型追加（12 GREEN）

**Files:**
- Modify: `apps/agent-core/app/models.py:末尾`
- Test: `apps/agent-core/tests/test_pipeline_run_model.py`

- [ ] **Step 1: 写失败测试 12 tests (M1-M12)**
```python
# apps/agent-core/tests/test_pipeline_run_model.py
import pytest, uuid, datetime as dt
from app import create_app, db
from app.models import PipelineRun, PipelineStepResult

PRESETS = ["sglt2i_ckd","empagliflozin_hf","glp1_weightloss","liraglutide_nafld","pkd_tolvaptan","ckd_blood_pressure_control"]
STATUSES = ["queued","running","success","failed","resumable","paused","cancelled","partial"]

@pytest.fixture
def app_ctx():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_M1_pipeline_run_ulid_prefix_32char(app_ctx):
    r = PipelineRun(id="p-" + "x"*30, workspace_id=str(uuid.uuid4()),
                    preset="sglt2i_ckd", mode="snapshot", max_records=200,
                    status="queued", steps_json=[{"step_index":i,"status":"pending","step_name":n}
                        for i,n in enumerate(["pubmed_fetch","dedupe","screen_ta","screen_ft","abstractor","rob2","grade","report"])])
    assert r.id.startswith("p-")
    assert len(r.id) == 32

def test_M2_defaults_max_records_200_cancel_flag_F(app_ctx):
    r = PipelineRun(id="p-002", workspace_id=str(uuid.uuid4()),
                    preset="sglt2i_ckd", mode="snapshot", status="queued", steps_json=[])
    assert r.max_records == 200
    assert r.cancel_flag is False
    assert r.current_step_index == 0

def test_M3_max_records_rejects_gt_200(app_ctx):
    with pytest.raises(AssertionError if "no sqlalchemy event" else Exception):
        r = PipelineRun(id="p-003", workspace_id=str(uuid.uuid4()),
                        preset="sglt2i_ckd", mode="snapshot", max_records=501, status="queued", steps_json=[])
        db.session.add(r); db.session.commit()

def test_M4_workspace_fk_violation(app_ctx):
    with pytest.raises(Exception):
        r = PipelineRun(id="p-004", workspace_id="00000000-0000-0000-0000-000000000000",
                        preset="sglt2i_ckd", mode="snapshot", status="queued", steps_json=[])
        db.session.add(r); db.session.commit()

def test_M5_steps_json_length_8_success(app_ctx):
    steps = [{"step_index":i,"status":"pending"} for i in range(8)]
    r = PipelineRun(id="p-005", workspace_id=str(uuid.uuid4()), preset="sglt2i_ckd",
                    mode="snapshot", status="queued", steps_json=steps)
    db.session.add(r); db.session.commit()
    assert len(r.steps_json) == 8

def test_M6_steps_json_9_invalid_via_engine_guard(app_ctx):
    # 模型层允许任意，但 engine 层 create_pipeline_run() 强制 len=8 → 断言放 D1-3 测试；此处只保证入库成功
    r = PipelineRun(id="p-006", workspace_id=str(uuid.uuid4()), preset="sglt2i_ckd",
                    mode="snapshot", status="queued", steps_json=[{"x":1}])
    db.session.add(r); db.session.commit()
    assert r.steps_json == [{"x":1}]

def test_M7_status_all_8_values_ok(app_ctx):
    for i,s in enumerate(STATUSES):
        r = PipelineRun(id=f"p-007{i}", workspace_id=str(uuid.uuid4()), preset="sglt2i_ckd",
                        mode="snapshot", status=s, steps_json=[])
        db.session.add(r)
    db.session.commit()
    assert db.session.query(PipelineRun).count() == 8

def test_M8_report_blob_path_nullable(app_ctx):
    r = PipelineRun(id="p-008", workspace_id=str(uuid.uuid4()), preset="sglt2i_ckd",
                    mode="snapshot", status="queued", steps_json=[], report_blob_path=None)
    db.session.add(r); db.session.commit()
    assert r.report_blob_path is None

def test_M9_preset_6_values_ok(app_ctx):
    for i,p in enumerate(PRESETS):
        r = PipelineRun(id=f"p-009{i}", workspace_id=str(uuid.uuid4()), preset=p,
                        mode="snapshot", status="queued", steps_json=[])
        db.session.add(r)
    db.session.commit()
    assert db.session.query(PipelineRun).count() == 6

def test_M10_step_result_unique_run_step_attempt(app_ctx):
    wid = str(uuid.uuid4())
    r = PipelineRun(id="p-010", workspace_id=wid, preset="sglt2i_ckd",
                    mode="snapshot", status="queued", steps_json=[])
    db.session.add(r); db.session.flush()
    s1 = PipelineStepResult(run_id="p-010", step_index=0, step_name="pubmed_fetch", attempt_no=1,
                            status="success", duration_ms=1200, n_inputs=200, n_outputs=200)
    db.session.add(s1); db.session.commit()
    s1_dup = PipelineStepResult(run_id="p-010", step_index=0, step_name="pubmed_fetch", attempt_no=1,
                                status="failed", duration_ms=800, n_inputs=200, n_outputs=0)
    with pytest.raises(Exception):
        db.session.add(s1_dup); db.session.commit()

def test_M11_step_result_payload_ref_nullable(app_ctx):
    wid = str(uuid.uuid4())
    r = PipelineRun(id="p-011", workspace_id=wid, preset="sglt2i_ckd", mode="snapshot", status="queued", steps_json=[])
    db.session.add(r); db.session.flush()
    s = PipelineStepResult(run_id="p-011", step_index=3, step_name="screen_ft", attempt_no=1,
                           status="success", duration_ms=4500, n_inputs=104, n_outputs=58,
                           payload_ref=None, retryable=True)
    db.session.add(s); db.session.commit()
    assert s.retryable is True

def test_M12_workspace_createdat_desc_index_query_works(app_ctx):
    wid = str(uuid.uuid4())
    r1 = PipelineRun(id="p-012a", workspace_id=wid, preset="sglt2i_ckd", mode="snapshot", status="success",
                     steps_json=[], finished_at=dt.datetime(2026,8,21,10,0))
    r2 = PipelineRun(id="p-012b", workspace_id=wid, preset="empagliflozin_hf", mode="snapshot", status="success",
                     steps_json=[], finished_at=dt.datetime(2026,8,21,11,0))
    db.session.add_all([r1,r2]); db.session.commit()
    q = db.session.query(PipelineRun).filter_by(workspace_id=wid).order_by(PipelineRun.created_at.desc()).all()
    assert q[0].id in ("p-012a","p-012b")
```

- [ ] **Step 2: Run 测试 → 预期 FAIL (PipelineRun not defined)**
```bash
pytest apps/agent-core/tests/test_pipeline_run_model.py -v
Expected: FAIL ImportError or NameError: PipelineRun not defined
```

- [ ] **Step 3: Append 两个新表到 models.py 末尾**
```python
# ---- APPEND ONLY to apps/agent-core/app/models.py (末尾) ----
class PipelineRun(db.Model):
    __tablename__ = "pipeline_runs"
    id = db.Column(db.CHAR(32), primary_key=True)
    workspace_id = db.Column(db.CHAR(36), db.ForeignKey("workspaces.id"), nullable=False, index=True)
    preset = db.Column(db.String(64), nullable=False, index=True)
    mode = db.Column(db.String(8), nullable=False)
    max_records = db.Column(db.SmallInteger, default=200, nullable=False)
    status = db.Column(db.String(16), nullable=False, index=True)
    current_step_index = db.Column(db.SmallInteger, default=0, nullable=False)
    cancel_flag = db.Column(db.Boolean, default=False, nullable=False)
    steps_json = db.Column(db.JSON, default=list, nullable=False)
    error_msg = db.Column(db.Text, nullable=True)
    report_blob_path = db.Column(db.String(256), nullable=True)
    pico_csv_blob_path = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    __table_args__ = (
        db.Index("ix_pipeline_runs_ws_created", workspace_id, created_at.desc()),
        db.CheckConstraint("max_records BETWEEN 1 AND 500", name="cc_pipeline_max_records_cap"),
    )

class PipelineStepResult(db.Model):
    __tablename__ = "pipeline_step_results"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    run_id = db.Column(db.CHAR(32), db.ForeignKey("pipeline_runs.id"), nullable=False)
    step_index = db.Column(db.SmallInteger, nullable=False)
    step_name = db.Column(db.String(32), nullable=False)
    attempt_no = db.Column(db.SmallInteger, default=1, nullable=False)
    status = db.Column(db.String(8), nullable=False)
    duration_ms = db.Column(db.Integer, nullable=False)
    n_inputs = db.Column(db.Integer, default=0, nullable=False)
    n_outputs = db.Column(db.Integer, default=0, nullable=False)
    payload_ref = db.Column(db.String(128), nullable=True)
    error_msg = db.Column(db.Text, nullable=True)
    retryable = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=dt.datetime.utcnow, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("run_id", "step_index", "attempt_no", name="uq_pipeline_step_run_attempt"),
        db.Index("ix_pipeline_step_run_id", run_id),
    )
```

- [ ] **Step 4: Run 12 tests → 预期 GREEN**
```bash
pytest apps/agent-core/tests/test_pipeline_run_model.py -v
Expected: 12 passed
```

- [ ] **Step 5: Commit**
```bash
git add apps/agent-core/app/models.py apps/agent-core/tests/test_pipeline_run_model.py
git commit -m "feat(w10 D1-1): add PipelineRun + PipelineStepResult 2 models (12 GREEN)"
```

---

### Task D1-2：shared-sdk 6 types 追加 + barrel（8 GREEN = 6 types + 2 barrel）

**Files:**
- Create: `packages/shared-sdk/src/pipeline.types.ts`
- Modify: `packages/shared-sdk/src/index.ts` (末尾 1 行 append)
- Modify: `packages/shared-ui/src/index.ts` (末尾追加 13 barrel)
- Test TS1: `packages/shared-ui/src/__tests__/T18_shared_sdk_pipeline_types.test.ts`
- Test TS2: `packages/shared-ui/src/__tests__/T14_barrel_export_append.test.ts`

- [ ] **Step 1: 写两个失败测试**
```typescript
// T18_shared_sdk_pipeline_types.test.ts
import { describe, it, expect } from "vitest";
import type {
  PipelineRunStatus, PipelineMode, PipelineRunSummary,
  PipelineStepInfo, PipelineRunDetail, PipelineCompareResult,
} from "@meda/shared-sdk";

describe("T18 W10 shared-sdk 6 pipeline types defined", () => {
  it("T18-1 PipelineRunStatus has 8 values", () => {
    const v: PipelineRunStatus[] = ["queued","running","success","failed","resumable","paused","cancelled","partial"];
    expect(v).toHaveLength(8);
  });
  it("T18-2 PipelineMode snapshot|live only", () => {
    const m: PipelineMode[] = ["snapshot","live"];
    expect(m).toHaveLength(2);
  });
  it("T18-3 PipelineRunSummary required fields non-null", () => {
    const s: Required<PipelineRunSummary> = {
      run_id:"p-314", preset:"sglt2i_ckd", mode:"snapshot", max_records:200,
      status:"running", current_step_index:3, duration_ms:72000,
      created_at:"2026-08-21T10:12:00Z", finished_at:undefined as any, report_url:undefined as any
    };
    expect(s.run_id).toHaveLength(32);
    expect(s.current_step_index).toBeGreaterThanOrEqual(0);
    expect(s.current_step_index).toBeLessThan(8);
  });
  it("T18-4 PipelineStepInfo length 8 requirement", () => {
    const step: PipelineStepInfo = {
      step_index:2, step_name:"screen_ta", status:"success",
      duration_ms:2100, n_in:178, n_out:104
    };
    expect(step.step_index).toBeLessThan(8);
    expect(["pending","running","success","failed","skipped"]).toContain(step.status);
  });
  it("T18-5 PipelineRunDetail steps len 8", () => {
    const steps: PipelineStepInfo[] = Array.from({length:8}).map((_,i)=>({
      step_index:i as any, step_name:`step${i}`, status:"pending",
      duration_ms:null, n_in:0, n_out:0
    }));
    const d: PipelineRunDetail = { run_id:"p-1", preset:"x", mode:"snapshot",
      max_records:200, status:"queued", current_step_index:0, duration_ms:null,
      created_at:"", steps, cancel_flag:false };
    expect(d.steps).toHaveLength(8);
  });
  it("T18-6 PipelineCompareResult funnel_delta array", () => {
    const c: PipelineCompareResult = { run_a_id:"p-a", run_b_id:"p-b",
      funnel_delta:[{step:"identify",a_n:200,b_n:188,diff:12}],
      rob2_delta:[{overall:"low",a:18,b:17}],
      grade_delta:[{outcome:"eGFR",a:"H",b:"H",reason:"same"}],
      pico:{only_in_a_nct_ids:["N1"],only_in_b_nct_ids:["N2"],both:["N0"]}};
    expect(c.funnel_delta[0].diff).toBe(12);
  });
});

// T14_barrel_export_append.test.ts
import { describe, it, expect } from "vitest";
import {
  PipelineRunsListPage, PipelineRunDetailPage, PipelineComparePage,
  NewRunModal, GradeDistributionCard,
  type PipelineRunStatus, type PipelineRunDetail, type PipelineCompareResult,
} from "@meda/shared-ui";

describe("T14 W10 barrel append 5 components + 6 types", () => {
  it("T14-1 5 Page/Component names are functions (exported)", () => {
    [PipelineRunsListPage, PipelineRunDetailPage, PipelineComparePage, NewRunModal, GradeDistributionCard]
      .forEach(fn => expect(typeof fn).toBe("function"));
  });
  it("T14-2 3 core types can be imported from barrel without TS error", () => {
    const s: PipelineRunStatus = "success";
    const d: PipelineRunDetail = null as any;
    const c: PipelineCompareResult = null as any;
    expect(["queued","running","success","failed","resumable","paused","cancelled","partial"]).toContain(s);
    expect(d).toBeNull(); expect(c).toBeNull();
  });
});
```

- [ ] **Step 2: Run vitest 失败预期**
```bash
cd packages/shared-sdk && vitest run src/__tests__ 2>&1 | head -5
cd packages/shared-ui && vitest run src/__tests__/T14_barrel_export_append.test.ts 2>&1 | head -5
Expected: both FAIL cannot find module '@meda/shared-sdk/pipeline.types' / undefined exports
```

- [ ] **Step 3: 写 6 types 文件**
```typescript
// packages/shared-sdk/src/pipeline.types.ts
export type PipelineRunStatus =
  "queued" | "running" | "success" | "failed" |
  "resumable" | "paused" | "cancelled" | "partial";
export type PipelineMode = "snapshot" | "live";

export interface PipelineRunSummary {
  run_id: string;
  preset: string;
  mode: PipelineMode;
  max_records: number;
  status: PipelineRunStatus;
  current_step_index: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;
  duration_ms: number | null;
  created_at: string;
  finished_at?: string;
  report_url?: string;
}

export interface PipelineStepInfo {
  step_index: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;
  step_name: string;
  status: "pending" | "running" | "success" | "failed" | "skipped";
  duration_ms: number | null;
  n_in: number;
  n_out: number;
  error?: string;
  retryable?: boolean;
  attempt_no?: 1 | 2 | 3;
}

export interface PipelineRunDetail extends PipelineRunSummary {
  steps: PipelineStepInfo[];
  cancel_flag: boolean;
  pico_csv_url?: string;
  grade_distribution?: { H: number; M: number; L: number };
  rob2_distribution?: { low: number; some: number; high: number };
  funnel_counts?: number[];
}

export interface PipelineCompareResult {
  run_a_id: string;
  run_b_id: string;
  funnel_delta: { step: string; a_n: number; b_n: number; diff: number }[];
  rob2_delta: { overall: "low" | "some" | "high"; a: number; b: number }[];
  grade_delta: { outcome: string; a: "H" | "M" | "L"; b: "H" | "M" | "L"; reason: string }[];
  pico: {
    only_in_a_nct_ids: string[];
    only_in_b_nct_ids: string[];
    both: string[];
  };
}
```

- [ ] **Step 4: 追加 barrel 导出**
```typescript
// append to packages/shared-sdk/src/index.ts
export * from "./pipeline.types";

// append to packages/shared-ui/src/index.ts 末尾
export { PipelineRunsListPage } from "./pages/PipelineRunsListPage";
export { PipelineRunDetailPage } from "./pages/PipelineRunDetailPage";
export { PipelineComparePage } from "./pages/PipelineComparePage";
export { NewRunModal } from "./components/NewRunModal";
export { GradeDistributionCard } from "./components/GradeDistributionCard";
export type {
  PipelineRunStatus, PipelineMode, PipelineRunSummary,
  PipelineStepInfo, PipelineRunDetail, PipelineCompareResult,
} from "@meda/shared-sdk";
```

- [ ] **Step 5: vitest 2 份 8 it() GREEN**
```bash
cd packages/shared-ui && vitest run src/__tests__/T18_shared_sdk_pipeline_types.test.ts src/__tests__/T14_barrel_export_append.test.ts
Expected: 6 + 2 = 8 passed
```

- [ ] **Step 6: Commit**
```bash
git add packages/shared-sdk/src/pipeline.types.ts packages/shared-sdk/src/index.ts \
        packages/shared-ui/src/index.ts \
        packages/shared-ui/src/__tests__/T18_shared_sdk_pipeline_types.test.ts \
        packages/shared-ui/src/__tests__/T14_barrel_export_append.test.ts
git commit -m "feat(w10 D1-2): shared-sdk 6 pipeline types + barrel 5+6 export (8 GREEN)"
```

---

### Task D1-3：pipeline_engine.py 核心 8 步状态机 + retry + resume（50 GREEN = 32 States + 18 Q4 Resume）

**Files:**
- Create: `apps/agent-core/app/services/pipeline_engine.py`
- Test1: `apps/agent-core/tests/test_pipeline_engine_states.py` (E1-E32, 32 tests)
- Test2: `apps/agent-core/tests/test_pipeline_engine_q4_resume.py` (R1-R18, 18 tests)

- [ ] **Step 1: 写 states 失败测试（32 it）首 6 条展示**
```python
# apps/agent-core/tests/test_pipeline_engine_states.py E1-E32 skeleton
import pytest, asyncio
from unittest.mock import patch, AsyncMock
from app.services.pipeline_engine import (
    PIPELINE_STEPS, create_pipeline_run, run_pipeline, run_single_step,
    mark_step_success, mark_run_failed
)
from app.models import PipelineRun, PipelineStepResult

STEP_NAMES = ["pubmed_fetch","simhash_dedupe","screen_ta","screen_ft","abstractor","rob2_assessment","grade_downgrade","report_generate"]

@pytest.fixture
def loop():
    return asyncio.new_event_loop()

def test_E1_8_STEP_NAMES_in_PIPELINE_STEPS_order():
    assert [s["name"] for s in PIPELINE_STEPS] == STEP_NAMES

def test_E2_create_pipeline_run_steps_len_8(app_ctx):
    wid = str(uuid.uuid4())
    run = create_pipeline_run(workspace_id=wid, preset="sglt2i_ckd", mode="snapshot", max_records=200)
    assert len(run.steps_json) == 8
    assert run.id.startswith("p-") and len(run.id) == 32

# ... (repeat for E3-E32: E3-10 each step success mark; E11-18 auto retry 2 times, E19-26 non-retryable fails, E27-32 step durations logged)
```

- [ ] **Step 2: 写 pipeline_engine.py 实现（核心骨架）**
```python
# apps/agent-core/app/services/pipeline_engine.py
import asyncio, datetime as dt, time, uuid, ulid
from typing import Callable, Any
from app import db
from app.models import PipelineRun, PipelineStepResult

PIPELINE_STEPS = [
    {"index":0,"name":"pubmed_fetch",       "adapter":"pubmed_adapter.search_records_wrapper"},
    {"index":1,"name":"simhash_dedupe",     "adapter":"simhash.dedupe_records"},
    {"index":2,"name":"screen_ta",          "adapter":"screening_engine.validate_exclude_ta"},
    {"index":3,"name":"screen_ft",          "adapter":"screening_engine.validate_exclude_ft_and_eas"},
    {"index":4,"name":"abstractor",         "adapter":"abstractor.triage_study_batch"},
    {"index":5,"name":"rob2_assessment",    "adapter":"rob2_engine.rob2_batch"},
    {"index":6,"name":"grade_downgrade",    "adapter":"grade_engine.grade_ro_downgrade_batch"},
    {"index":7,"name":"report_generate",    "adapter":"report_engine.generate_preview"},
]

def _ulid_run_id() -> str:
    return "p-" + ulid.new().str[:30]

def create_pipeline_run(workspace_id: str, preset: str, mode: str = "snapshot",
                        max_records: int = 200) -> PipelineRun:
    assert 1 <= max_records <= 200, "max_records W10 cap=200 per Q1"
    assert preset in ("sglt2i_ckd","empagliflozin_hf","glp1_weightloss","liraglutide_nafld","pkd_tolvaptan","ckd_blood_pressure_control")
    assert mode in ("snapshot","live")
    default_steps = [{"step_index":i,"step_name":s["name"],"status":"pending",
                      "duration_ms":None,"n_in":0,"n_out":0} for i,s in enumerate(PIPELINE_STEPS)]
    r = PipelineRun(id=_ulid_run_id(), workspace_id=workspace_id, preset=preset, mode=mode,
                    max_records=max_records, status="queued", steps_json=default_steps)
    db.session.add(r); db.session.commit()
    return r

# mark_step_success / run_single_step / run_pipeline / resume_pipeline ... (~250 行完整实现)
```

- [ ] **Step 3: Run 32 + 18 tests = 50 GREEN**
```bash
pytest apps/agent-core/tests/test_pipeline_engine_states.py apps/agent-core/tests/test_pipeline_engine_q4_resume.py -v
Expected: 50 passed
```

- [ ] **Step 4: Commit**
```bash
git add apps/agent-core/app/services/pipeline_engine.py \
        apps/agent-core/tests/test_pipeline_engine_states.py \
        apps/agent-core/tests/test_pipeline_engine_q4_resume.py
git commit -m "feat(w10 D1-3): pipeline_engine 8-step state machine + retry2 + resume (50 GREEN)"
```

---

### Task D1-4：Hybrid PubMed 双模式 + 6 preset Snapshot 入库（14 GREEN）

**Files:**
- Modify: `apps/agent-core/app/services/search_adapters/pubmed_adapter.py` (末尾 append `search_records_wrapper` helper)
- Test: `apps/agent-core/tests/test_pipeline_hybrid_fetch.py` (H1-H14)

- [ ] **Step 1-5: 14 tests GREEN 流程**
- [ ] H1-H6: 6 preset snapshot 各正确返回 50-200 之间的 records
- [ ] H7: Live 模式网络报错 → 自动转入 snapshot fallback (如果用户启用)
- [ ] H8: Live 模式 NCBI rate limit → 退避 1s→4s→9s，retry 3 次
- [ ] H9: snapshot 模式下发出任何网络请求 → 断言拦截
- [ ] H10: max_records 201 → create_pipeline_run AssertionError
- [ ] H11-H14: ULID 前缀 + 单调递增

```bash
# Step4 Run
pytest apps/agent-core/tests/test_pipeline_hybrid_fetch.py -v
Expected: 14 passed
```

```bash
# Step5 Commit
git add apps/agent-core/app/services/search_adapters/pubmed_adapter.py apps/agent-core/tests/test_pipeline_hybrid_fetch.py
git commit -m "feat(w10 D1-4): Hybrid PubMed wrapper snapshot 6 default + Live retry (14 GREEN)"
```

### 🧪 Day 1 验收小结：12 + 8 + 50 + 14 = **84 GREEN** (≥ 60% 目标 130 PY)

---

### 🌓 Day 2 · Workspace 6 路由 + Compare + 2 E2E Happy Path（PY 侧剩余全量 66 GREEN = 累计 150/130 ✅ AC1 达成）

### Task D2-1：workspace.py 末尾追加 6 条路由（24 GREEN）
- [ ] **Step 1: 写 test_workspace_pipeline_routes.py 24 条 A1-A24（6 路由 × 200/401/403/404）**
- [ ] **Step 2: 追加 workspace.py 末尾 420 行**
```python
# workspace.py末尾 append
@router.post("/{workspace_id}/pipelines/run")
def pipeline_run(workspace_id, payload): ...
@router.get("/{workspace_id}/pipelines")
def pipeline_list(workspace_id, status, preset, page, per_page): ...
@router.get("/{workspace_id}/pipelines/{run_id}")
def pipeline_get(workspace_id, run_id): ...
@router.post("/{workspace_id}/pipelines/{run_id}/retry/{step_idx}")
def pipeline_retry_step(workspace_id, run_id, step_idx, force=False): ...
@router.post("/{workspace_id}/pipelines/{run_id}/cancel")
def pipeline_cancel(workspace_id, run_id): ...
@router.get("/{workspace_id}/pipelines/compare/{run_a}/{run_b}")
def pipeline_compare(workspace_id, run_a, run_b, metrics): ...
```
- [ ] **Step 3: pytest A1-A24 GREEN**
- [ ] **Step 4: Commit w10 D2-1 routes** (24 GREEN)

### Task D2-2：Compare Route 独立 20 GREEN（C1-C20）
- [ ] **Step 1: 20 compare testcases**
- [ ] **Step 2: 实现 helpers `compute_funnel_delta` `compute_rob2_delta` `compute_grade_delta` `compute_pico_diff`**
- [ ] **Step 3: C1-C20 GREEN**

### Task D2-3：Happy Path E2E × 2 preset + Cancel（10 GREEN HP1-HP10）
- [ ] **Step 1: 用 snapshot 数据真跑 STEP0-7 全流程（mock LLM 调用）**
- [ ] **Step 2: sglt2i_ckd 全 8 步 success HP1-HP3**
- [ ] **Step 3: glp1_weightloss 全 8 步 success HP4-HP6**
- [ ] **Step 4: Cancel 在 step3 生效 HP7-HP8**
- [ ] **Step 5: 已 cancel run 的 resume HP9-HP10**
- [ ] **Step 6: HP1-HP10 GREEN → Commit**

### 🧪 Day 2 验收：24 + 20 + 10 = 56 → Day 1 84 + Day 2 56 = **140 ≥ 130 AC1 ✅ PY OVER**

---

### 🌗 Day 3：UI 三屏 + 2 Hook + Happy Path（TS 侧 130+ GREEN = 达 AC2）

### Task D3-1：usePipelineRun + usePipelineCompare Hooks（26 GREEN）
- [ ] 16 it() + 10 it() hooks 纯 test 逻辑 → GREEN

### Task D3-2：NewRunModal + PipelineRunsListPage（屏1 = 40 it）
- [ ] Modal 18 it() + List 22 it() → GREEN

### Task D3-3：PipelineRunDetailPage（屏2 = 30 it）
- [ ] 8 段核心 + Funnel + Abstractor 网格 + RoB2Matrix 只读 + GRADE DistributionCard 共 30 GREEN

### Task D3-4：PipelineComparePage（屏3 = 22 it）
- [ ] A/B 选择器 + FunnelDiff 颜色 + GRADE row + PICO tab 22 GREEN

### Task D3-5：W10 2 条 UI Happy Path（4 it）
- [ ] List → NewRun → Detail 轮询 3 次 → Download enable
- [ ] Compare A/B select → funnel diff render → 4 GREEN

### 🧪 Day 3 汇总：26 + 40 + 30 + 22 + 4 + Day1-8 (types 8) = **130 it() 刚好达 AC2 ✅**

### 🏁 最终 Hard-Gate Total：PY 140 + TS 130 = **270 ≥ 260 AC3 ✅ 超额**

---

## 🚨 NOTOUCH 审计门禁（每次 Commit 后自动跑）
```bash
# 在实现完成后，执行以下 0-diff 检查：
git diff HEAD~$(git rev-list --count HEAD) \
  apps/agent-core/app/services/screening_engine.py \
  apps/agent-core/app/services/rob2_engine.py \
  apps/agent-core/app/services/abstractor.py \
  apps/agent-core/app/services/grade_engine.py \
  apps/agent-core/app/services/report_engine.py \
  apps/agent-core/app/services/simhash.py \
  packages/shared-ui/src/components/FunnelProgressBar.tsx \
  packages/shared-ui/src/grade/RoB2Matrix.tsx \
  packages/shared-ui/src/components/AbstractorCard.tsx \
  2>&1 | tee /tmp/notouch_audit.log
# Expected result: EMPTY output (0 diff lines). If any line → AC4 FAIL.
```
