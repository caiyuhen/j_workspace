# Wave 10 · End-to-End PubMed + Dashboard 设计文档

> **Date:** 2026-08-21 | **Author:** MedA Agent-Core Team | **Status:** Draft for User Review
> **Depends on:** Wave 9 Evidence-Artifact (AC1-8 ✅ green · tag `v0.9.0-evidence-artifact-OK`)
> **Target delivery:** 3 days · 260+ new GREEN tests (PY≥130, TS≥130) · 0 new deps · NOTOUCH W1-W9

---

## 0. Executive Summary + Decisions Log (4/4 locked)

### 目标
把 W1-W9 的六大模块（PubMed 检索 → 去重 → 9a 筛选 → 9c 分流 → 9b 质量评估 → W5 GRADE → W8.4 报告）**串成一条可一键运行的端到端 Pipeline**，提供真实 PubMed 数据 Hybrid 双模式，并交付 3 屏可视化 Dashboard。
让科研人员能在 3 分钟内从 6 preset 中选一个 → 看到 200 篇文献的完整漏斗、RoB2 矩阵、GRADE 评级、自动生成 PDF 报告。

### 4 关键锁定决策（Brainstorming 4 Questions 全确认 = AAAA）

| # | Decision | Chosen (A) | Alternatives rejected |
|---|---|---|---|
| Q1 | 单次 run 文献规模上限 | ≤ **200 篇**（simhash O(n²)=40k 对 ≈15s；BK-Tree 留 W11） | B=500, C=1000+ |
| Q2 | Dashboard 屏数量 | **3 屏完整**：① Runs List ② Run Detail ③ A/B Compare | B=2, C=1 |
| Q3 | PubMed 数据模式 | **Hybrid 双模式**：Snapshot 默认（CI 永远 GREEN） + Live Toggle（用户 demo 实时） | B=永远在线, C=永远离线 |
| Q4 | 失败恢复策略 | **断点续跑 + 单步重试**（每步最多 2 次自动重试 1s→4s，失败保留断点、UI 可 RESUME 单步） | B=整 run 重跑, C=忽略 |

### Hard-Gate 验收标准（6/6，交付时必须满足）
| AC | 指标 | 目标值 |
|---|---|---|
| **AC1** | agent-core pytest 新增 GREEN 数 | ≥ **130** |
| **AC2** | shared-ui vitest 新增 GREEN 数 | ≥ **130** |
| **AC3** | 合计新增 GREEN | ≥ **260** |
| **AC4** | NOTOUCH：W1-W9 核心业务逻辑（9a/9b/9c/GRADE/Report 非 helper 函数）diff 数 | **0**（只允许 append） |
| **AC5** | 新依赖引入数（requirements.txt / package.json） | **0** |
| **AC6** | 2 条 Happy Path e2e（sglt2i_ckd + glp1_weightloss）在 offline snapshot 模式下 100% 全 8 步 success | GREEN |

---

## 1. Architecture (三层 · Layer 2 编排隔离保证 NOTOUCH)

```
─────────────────────────────────────────────────────────────────
Layer 1 · Shared-UI Dashboard (NEW ONLY · 4 components + 2 hooks)
─────────────────────────────────────────────────────────────────
  ├─ PipelineRunsListPage.tsx        Screen 1 · Runs 列表
  ├─ PipelineRunDetailPage.tsx       Screen 2 · 单 Run 8 段布局
  ├─ PipelineComparePage.tsx         Screen 3 · A/B 对比
  ├─ NewRunModal.tsx                 启动新 run modal
  ├─ usePipelineRun.ts               1.5s 轮询 + 6 actions
  └─ usePipelineCompare.ts           /compare/{a}/{b} 数据拉取
          │ injectFetchClient
          ▼ HTTP /api/v1/ws/{wid}
─────────────────────────────────────────────────────────────────
Layer 2 · Pipeline Orchestrator (NEW · 0 new deps · asyncio)
─────────────────────────────────────────────────────────────────
  ├─ pipeline_engine.py              asyncio 状态机 8 步编排
  │    ├─ run_pipeline(run_id)       主循环 + cancel_flag 检查
  │    ├─ run_single_step(i)         1 步 + 自动重试(2次, 退避1s→4s)
  │    └─ resume_pipeline(run_id)    断点续跑入口
  ├─ models.py 追加 2 张表           PipelineRun + PipelineStepResult
  └─ workspace.py 追加 6 路由        /pipelines/* + /pipelines/compare/*
          │ 纯函数调用（NOTOUCH BOUNDARY）
          ▼
─────────────────────────────────────────────────────────────────
Layer 3 · W1-W9 底座 (EXISTING · 0 internal change allowed)
─────────────────────────────────────────────────────────────────
  ├─ W8 PubMed Adapter       search_records(preset, mode="snapshot|live")
  ├─ W82b SimHash Dedupe     dedupe_records(record_ids)
  ├─ 9a Screening Engine     validate_exclude_decision() + calc_funnel()
  ├─ 9c Abstractor           triage_study() → include/review/exclude + PICO
  ├─ 9b RoB2 Engine          rob2_assessment(study_id) → 5域 + Overall
  ├─ W5 GRADE Engine         grade_ro_downgrade_evidence_artifact(EA id)
  └─ W8.4 Report Engine      generate_preview(run_id) → PDF/MD bytes
```

### 1.2 8 步 Pipeline 顺序（每步结束 = 可断点位置）
| Step Index | Step Name | 调 W1-W9 模块 | IO 数 | Success Output |
|---|---|---|---|---|
| 0 | `pubmed_fetch` | W8 PubMed Hybrid | N in=max_records (≤200) | `record_ids[]` 存 step_result.payload |
| 1 | `simhash_dedupe` | W82b dedupe | N in=Step0.n_out | `dedup_ids[]` + dedup pairs |
| 2 | `screen_ta` | 9a validate TA E1-E4 | N in=Step1.n_out | `decisions: TA_pass[]` |
| 3 | `screen_ft + EA create` | 9a validate FT + EvidenceArtifact bulk | N in=Step2.n_out | `ea_ids[]` rows 入库 |
| 4 | `abstractor` | 9c triage_study 批量 | N in=Step3.n_out | `include_ids[] / review_ids[] / exclude_ids[]` + PICO JSON |
| 5 | `rob2_assessment` | 9b rob2_engine | N in=Step4.include_ids | `rob2_results[study_id] → 5域 + Overall` |
| 6 | `grade_downgrade` | W5 GRADE | N in=Step5 入 grade 队列数 | `grade_rows[outcome] → H/M/L` |
| 7 | `report_generate` | W8.4 Report | 汇总 Step0-6 | `PDF bytes → storage` + `report_blob_path` 入库 |

### 1.3 Q4 断点续跑 & 重试细则（pipeline_engine.py 的 3 个核心函数）
```python
async def run_pipeline(run_id: str):
    # 入口函数：asyncio.create_task 后立刻返回（HTTP 202 Accepted）
    for i in range(8):
        if run.cancel_flag: break
        if step_i.status == "success": continue   # ← resume 跳过逻辑
        ok = await run_single_step(run_id, i, attempt=1)
        if not ok:
            # 自动重试 2 次（指数退避 1s→4s）
            for attempt in (2, 3):
                await asyncio.sleep(1 if attempt == 2 else 4)
                ok = await run_single_step(run_id, i, attempt)
                if ok: break
        if not ok:
            mark_run_failed(run_id, step_index=i, retryable=...)
            return
    mark_run_success(run_id)

async def resume_pipeline(run_id: str, from_step: int | None = None):
    # 用户点击 [RESUME] 触发；自动从第一个非 success 步骤开始
    start = from_step if from_step is not None else first_non_success_index(run_id)
    set_run_status(run_id, "resumable" if start > 0 else "queued")
    # 复用 run_pipeline，skip 逻辑在内部完成
    await run_pipeline(run_id)
```

### 1.4 6 条 REST 路由（全部追加 workspace.py 末尾）
| Method | Path | 200 Response (核心字段) | Error Code Map |
|---|---|---|---|
| POST | `/pipelines/run` | `{run_id, status:"queued", expected_ms_estimate: 180000}` | 401/403/400 invalid preset |
| GET  | `/pipelines?status=&preset=&page=&per_page=20` | `{runs: PipelineRunSummary[], total}` | 401/403 |
| GET  | `/pipelines/{rid}` | `PipelineRunDetail (steps 长度=8 + report_url?)` | 404/401/403 |
| POST | `/pipelines/{rid}/retry/{step_idx}` | `{queued:True, resumed_from: step_idx}` | 400 step_idx>7 / 409 already running |
| POST | `/pipelines/{rid}/cancel` | `{cancelled:True, will_stop_at_next_step_entry:True}` | 409 已终态(success/failed/cancelled) |
| GET  | `/pipelines/compare/{ridA}/{ridB}?metrics=funnel,rob,grade,pico` | `PipelineCompareResult` | 404 either not exist |

---

## 2. Dashboard UI 三屏设计

### 2.1 Screen 1: Runs List（Dashboard Home）
**视觉 = 顶部控制条 · 8 列表格 · 分页**
```
[ 🧪 Pipeline Runs Dashboard ]
  左侧 preset chips (全部=默认):  [sglt2i_ckd] [empagliflozin_hf] [glp1_weightloss] [liraglutide_nafld] [pkd_tolvaptan] [ckd_blood_pressure_control]
  右侧:  Status ▼ [all] · 🔘 [+ 启动新 Run]   → 弹出 NewRunModal

  表格列:
  ┌──────┬──────────┬──────┬────────┬─────────────┬───────────────────────┬────────────┬──────────┬─────────────┐
  │ ID   │ Preset   │ Mode │ N Rec  │ Status      │ 8-step Progress Dots  │ Created    │ Duration │  Actions    │
  ├──────┼──────────┼──────┼────────┼─────────────┼───────────────────────┼────────────┼──────────┼─────────────┤
  │p-314 │sglt2i_ckd│ LIVE │  200   │●  running   │●●●○○○○○ Step4 FT     │ Aug21 10:12│    1m12s │ [详情] [重跑]│
  │p-313 │empag_hf  │SNAP  │  178   │🟩 success   │●●●●●●●● All 8 ✅     │ Aug21 09:40│    3m02s │ [详情][PDF][重跑]│
  │p-312 │glp1_ob   │SNAP  │  156   │🟥 failed    │●●●●●●❌ Step6 RoB2   │ Aug21 09:10│    2m18s │ [详情][RESUME #6]│
  │p-311 │sglt2i_ckd│ LIVE │  112   │🟨 partial   │●●●●●●●○ SKIP Step8   │ Aug20 17:40│    2m45s │ [详情][CSV]│
  │ ...  │ ...      │ ...  │ ...    │ ...         │ ...                   │ ...        │ ...      │ ...         │
  └──────┴──────────┴──────┴────────┴─────────────┴───────────────────────┴────────────┴──────────┴─────────────┘
  [◀ 1 / 17 ▶]  per_page [20 ▼]
```
**Status 色标:** queued=灰 ● running=蓝 🔄 loading success=绿 🟩 failed=红 🟥 cancelled=灰斜体 resumable=橙🟧 partial=黄 🟨

### 2.2 Screen 2: Run Detail（核心 8 段垂直布局）
```
[↩ Back to Runs]   📊 Run p-314 · sglt2i_ckd · LIVE · max 200 records
  status=🟩 success · 总耗时 3m12s · [Cancel ↓ (若 running)] [RESUME #N (若 failed)] [ ⬇ PDF] [ ⬇ PICO CSV ]

  ① STEP PROGRESS (8 columns, 可点击)
    [0 PubMed ✅][1 Dedupe ✅][2 TA ✅][3 FT ✅][4 Abst ✅][5 RoB2 ✅][6 GRADE ✅][7 Report ✅]
    每格 hover tooltip = attempt_no / duration_ms / n_in→n_out; 若 failed → 列右下 [RETRY] 按钮

  ② FUNNEL (复用 FunnelProgressBar 只读)
    Identify 200  →  Deduped 178  →  TA-pass 104  →  FT-include 58  →  Abst-include 44  →  RoB2-assessed 42
    (每步下方显示：数字 + % 保留率)

  ③ EVIDENCE ARTIFACT CARD GRID (复用 AbstractorCard, 分页 10 条/页)
    显示 Abst-include 44 条的前 10 条
    [AbstractorCard R13] [R14] [R15 = review 黄标] [R16] [R17] [R18] [R19] [R20] [R21] [R22]
    [◀ 1 / 5 ▶]

  ④ ROB2 MATRIX (复用 9b RoB2Matrix 只读，点击 Overall 可跳转 ROBINS-I)
    Study        D1 Bias   D2 Dev   D3 Miss   D4 Outc   D5 Sel  |  Overall (3px TL border)
    NCT01730535   Low       Low     Some      Low       Low      |  🟨 Some concerns
    NCT02474188   Low       Low      Low      Low       Low      |  🟩 Low risk
    ... (42 rows)
    【底部摘要】 Low 18 / Some 21 / High 3

  ⑤ GRADE 分布 + 原因解释 (新小组件 GradeDistributionCard)
    ╔════════════════════════════════════════════════════╗
    ║ ● High        7  (17%)  无 RoB2 high + 无间接     ║
    ║ ●● Moderate  28  (67%)  RoB2 1域 Some → -1       ║
    ║ ● Low         7  (16%)  Overall High → -2 + 间接性║
    ╚════════════════════════════════════════════════════╝

  ⑥ REPORT 预览 + 下载 (iframe h=480)
    ┌───────────────────────────────────────────────────────┐
    │  PRISMA 2020 Abstract / 背景 / 方法 / 结果 / 结论... │  (PDF 缩略)
    └───────────────────────────────────────────────────────┘
    [⬇ 下载 PDF · 4.2MB]   [⬇ Markdown]   [⬇ PICO CSV]
```

### 2.3 Screen 3: A/B Compare（杀手级 demo 功能）
**双栏布局，中间 Δ 差值列**。顶部选择器：
```
Run A: [ ▼ p-314 sglt2i_ckd LIVE 2026-08-21 ]   Run B: [ ▼ p-304 sglt2i_ckd SNAP 2026-08-18 ]
中间: [📋 SYNC preset] 一键选 preset 相同的两个历史 run  ·  [⬇ 导出对比报告 MD]
```

| Row | 左 (Run A) | 中 (Δ) | 右 (Run B) |
|---|---|---|---|
| **Funnel Diff** | 漏斗竖条 (200→178→104→58→44→42) | `Diff: +12 Identify +4 FT +6 Abst +2 RoB2` | 漏斗竖条 (188→165→100→54→38→40) |
| **RoB2 Histogram** | Low/Some/High = 18/21/3 柱图 | `Δ High: +1 (R15 新增 Overall High)` | Low/Some/High = 17/22/2 |
| **GRADE 对比表** (每行 outcome) | eGFR drop 40%: H | Δ 0 | eGFR drop 40%: H |
| | Hospitalization for HF: **M** (因间接性 -1) | **Δ -1** | Hospitalization for HF: H |
| | All-cause death: L (因 RoB2 -2) | Δ 0 | All-cause death: L |
| **PICO 差异** | 仅 A 有 3 篇: NCT05... NCT04... | 共有 15 篇 · 仅 B 有 7 篇 | 仅 B 有 7 篇: NCT03... |

### 2.4 UI NOTOUCH 保证
- 复用组件（0 修改）：`FunnelProgressBar` `AbstractorCard` `RoB2Matrix` `ConfidenceBar` `TrafficLightCell`
- 仅新增组件：`PipelineRunsListPage` / `PipelineRunDetailPage` / `PipelineComparePage` / `NewRunModal` / `GradeDistributionCard`
- Hook 规则：`usePipelineRun.ts` 和 `usePipelineCompare.ts` 全部走 `injectFetchClient`，window.fetch 0 调用
- 不接 React Router（避免污染既有导航），屏切换用顶层 `view = "list" | "detail" | "compare"` state

---

## 3. Data Model (2 新表 + 6 SDK Types)

### 3.1 表 1：`pipeline_runs` (models.py append-only 追加)
```python
class PipelineRun(db.Model):
    __tablename__ = "pipeline_runs"
    id = db.Column(db.CHAR(32), primary_key=True)           # ULID p-xxxxxxxx
    workspace_id = db.Column(db.CHAR(36), db.ForeignKey("workspaces.id"), nullable=False, index=True)
    preset = db.Column(db.String(64), nullable=False, index=True)
    mode = db.Column(db.String(8), nullable=False)          # "snapshot" | "live"
    max_records = db.Column(db.SmallInteger, default=200, nullable=False)
    status = db.Column(db.String(16), nullable=False, index=True)
    current_step_index = db.Column(db.SmallInteger, default=0, nullable=False)
    cancel_flag = db.Column(db.Boolean, default=False, nullable=False)
    steps_json = db.Column(db.JSON, default=list, nullable=False)  # len=8, each = PipelineStepInfo
    error_msg = db.Column(db.Text, nullable=True)
    report_blob_path = db.Column(db.String(256), nullable=True)   # ./storage/p-314/report.pdf
    pico_csv_blob_path = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    finished_at = db.Column(db.DateTime, nullable=True)
    # index(workspace_id, created_at DESC) 列表页用
    __table_args__ = (db.Index("ix_pipeline_runs_ws_created", workspace_id, created_at.desc()),)
```

### 3.2 表 2：`pipeline_step_results`（断点续跑底层支撑）
```python
class PipelineStepResult(db.Model):
    __tablename__ = "pipeline_step_results"
    id = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    run_id = db.Column(db.CHAR(32), db.ForeignKey("pipeline_runs.id"), nullable=False)
    step_index = db.Column(db.SmallInteger, nullable=False)
    step_name = db.Column(db.String(32), nullable=False)
    attempt_no = db.Column(db.SmallInteger, default=1, nullable=False)
    status = db.Column(db.String(8), nullable=False)         # success / failed
    duration_ms = db.Column(db.Integer, nullable=False)
    n_inputs = db.Column(db.Integer, default=0, nullable=False)
    n_outputs = db.Column(db.Integer, default=0, nullable=False)
    payload_ref = db.Column(db.String(128), nullable=True)   # storage 路径
    error_msg = db.Column(db.Text, nullable=True)
    retryable = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    __table_args__ = (
        db.UniqueConstraint("run_id", "step_index", "attempt_no", name="uq_pipeline_step_run_attempt"),
        db.Index("ix_pipeline_step_run_id", run_id),
    )
```

### 3.3 shared-sdk 新增 6 个 types（T14 barrel 追加）
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
  steps: PipelineStepInfo[];    // 长度必须 = 8
  cancel_flag: boolean;
  pico_csv_url?: string;
  grade_distribution?: { H: number; M: number; L: number };
  rob2_distribution?: { low: number; some: number; high: number };
  funnel_counts?: number[];     // 长度 6 = identify/dedup/TA/FT/include/rob2
}

export interface PipelineCompareResult {
  run_a_id: string;
  run_b_id: string;
  funnel_delta: { step: string; a_n: number; b_n: number; diff: number }[];
  rob2_delta: { overall: "low" | "some" | "high"; a: number; b: number }[];
  grade_delta: {
    outcome: string;
    a: "H" | "M" | "L";
    b: "H" | "M" | "L";
    reason: string;
  }[];
  pico: {
    only_in_a_nct_ids: string[];
    only_in_b_nct_ids: string[];
    both: string[];
  };
}
```

---

## 4. Testing Strategy (Wave10 目标：PY ≥130, TS ≥130, 合计 ≥260)

### 4.1 PY 侧 pytest 明细（≥130 GREEN）
| 文件 | 数量 | 用例 ID 范围 | 核心场景 |
|---|---|---|---|
| `test_pipeline_run_model.py` | 12 | M1-M12 | ULID 前缀、FK、step_json 默认 8 长度、cancel_flag 默认 f、index 存在、max_records 200 上限校验、8 status 枚举合法 |
| `test_pipeline_engine_states.py` | 32 | E1-E32 | 8 步 × 4 状态 = success/fail 各 8 + 自动重试 1s→4s 观察 8 + 第 3 次 attempt 仍失败 8 |
| `test_pipeline_engine_q4_resume.py` | 18 | R1-R18 | 人工断点从 step=2 起 R1-R6 / 从 step=5 起 R7-R12 / cancel_flag 在 step 4 中断 R13-R15 + 已成功步骤跳过验证 R16-R18 |
| `test_pipeline_hybrid_fetch.py` | 14 | H1-H14 | 6 preset snapshot 各命中 1 + live 真 fetch 404 H7 / rate_limit 触发退避 H8 / mode=snapshot 禁止外网 H9 / 超过 200 上限抛错 H10 / ULID 生成 p- 前缀 H11-H14 |
| `test_workspace_pipeline_routes.py` | 24 | A1-A24 | 6 路由 × 4 状态 = 200 success + 401 not logged + 403 非 workspace 成员 + 404 不存在 |
| `test_w10_e2e_2preset.py` | 10 | HP1-HP10 | 离线 sglt2i_ckd STEP1..8 全 success 3 断言 HP1-HP3；glp1_weightloss 全 success 3 HP4-HP6；cancel 在 step3 后触发 HP7-HP8；已取消 run 重跑恢复 HP9-HP10 |
| `test_pipeline_compare_route.py` | 20 | C1-C20 | compare 同一 run 0 diff C1-C4；run 差 funnel C5-C8；差 rob2 C9-C12；差 grade C13-C16；差 pico C17-C20 |
| **PY 小计** | **≥ 130** | (12+32+18+14+24+10+20) | |

### 4.2 TS 侧 vitest 明细（≥130 GREEN）
| 文件 | 数量 | 核心场景 |
|---|---|---|
| `T18_shared_sdk_pipeline_types.test.ts` | 6 | 6 types 存在性 + 字段类型校验 |
| `NewRunModal.test.tsx` | 18 | preset 必填 + 6 preset 按钮选中 + live toggle + max 输入边界(1-200) + submit payload 正确 + Cancel 不触发 + invalid preset 拦截 |
| `PipelineRunsListPage.test.tsx` | 22 | 空列表 + 20 条分页 + status filter 3 组 + preset chip activate/deactivate + detail 导航 emit + rerun 按钮 payload + status 色标 5 种正确渲染 |
| `PipelineRunDetailPage.test.tsx` | 30 | 8 step success 样式 + running active step 高亮 + failed step [RETRY] 按钮显示 + CANCEL 按钮二次确认 + Funnel render + AbstractorCard 网格 10 条 + RoB2 只读 + GRADE distribution bar + PDF iframe src + Report URL display + Resumable banner + cancel flag 非 running 不显示 |
| `PipelineComparePage.test.tsx` | 22 | A/B run select 正确 + funnel diff 颜色 (A>B 绿 A<B 红) + rob2 histogram + grade row H/M/L 正确样式 + pico only A / only B / both 3 tab + 导出对比报告 payload |
| `usePipelineRun.test.tsx` | 16 | 1.5s 轮询 start/stop（success 后停）+ retry_step action POST payload + cancel optimistic update + detail 拉取 injectFetchClient 正确 + window.fetch 0 次 + error 404 抛错 |
| `usePipelineCompare.test.tsx` | 10 | /compare 路由正确 + metrics query params 拼接 + 404 错误处理 |
| `W10_happy_path.test.tsx` | 4 | ① List → NewRun → Detail → 轮询 3 次 success → Download 按钮启用；② Compare A/B select → FunnelDiff render |
| `T14 barrel export 追加测试.ts` | 2 | 6 types 可从 `@meda/shared-sdk` import |
| **TS 小计** | **≥ 130** | 6+18+22+30+22+16+10+4+2 |

### 4.3 NOTOUCH 审计（交付时强制执行）
```bash
# W1-W9 禁止被修改的核心文件（只允许 import / append helper）
cd d:/workspace/MedA
PY_NOTOUCH = apps/agent-core/app/services/screening_engine.py   (T14 内部逻辑禁止修改)
            apps/agent-core/app/services/rob2_engine.py         (9b rating 规则禁止改)
            apps/agent-core/app/services/abstractor.py          (Gold480 FN=0 逻辑禁止改)
            apps/agent-core/app/services/grade_engine.py        (GRADE 降级规则禁止改)
            apps/agent-core/app/services/report_engine.py       (W8.4 模板禁止改)
            apps/agent-core/app/services/simhash.py             (THRESHOLDS 7bit/92% 禁止改)
TS_NOTOUCH = shared-ui/src/components/FunnelProgressBar.tsx     (locked 样式逻辑)
            shared-ui/src/grade/RoB2Matrix.tsx                  (Overall 3px border)
            shared-ui/src/components/AbstractorCard.tsx         (include/review/exclude 3态)
```
→ Run 1 条对比命令：`git diff HEAD~1 --stat <上述 files>` → 若有非空非 append diff → AC4 FAIL。

---

## 5. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 真 PubMed LIVE 模式 NCBI 限流 (3req/s) | 高 | 中 | Hybrid 默认走 snapshot，LIVE 模式在 fetch 层加 `min_interval=350ms` + 退避 5s×3 |
| W10 代码量大 → TS vitest 超 CI 时长 | 中 | 中 | vitest shard 4 并发；超时阈值从 5s→10s 只在 W10 单测组临时加 |
| asyncio 状态机内存泄漏（未清理 cancel 回调） | 中 | 高 | 每 8 个并发 run 满时 reject 新 run 排队；提供 `/pipelines/gc` 内部路由清理 zombie task |
| PDF blob 占磁盘（1 run ≈ 4MB） | 低 | 低 | storage 目录按 run_id 分目录；提供 30 天自动清理 cron |

---

## 6. Out of Scope (明确 W10 不做，留 W11+)
- ❌ BK-Tree simhash（解决 n>500 OOM）→ W11
- ❌ Celery/Redis 生产级 worker（n run 并发 > 8）→ W12
- ❌ 多用户双人独立筛选 + Kappa 系数协同 → W13
- ❌ 移动端小屏适配 Dashboard（最小支持宽度 = 1280px）→ 看用户反馈再定
- ❌ 报告图表的交互式编辑（只读预览 + 下载）→ W14
