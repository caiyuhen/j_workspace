# Wave 8.1 Design Spec — PubMed 真数据全链路 Demo（Scope A · 方案一+三）

- **文档 ID**: 2026-08-14-wave81-pubmed-real-demo-design
- **所属阶段**: R004 §6.1.2 Wave 8.1 首波，对应 R004 PRD §1「Demo 演示闭环」§7 验收条 7.4
- **前置基线**:
  - Wave 8 三源 Adapter 真 HTTP + 三级 mode（prefer_real / force_mock / force_real）206 tests passed，`conftest.py` autouse force_mock，pytest 默认零外网
  - Workspace 三 Tab 内联（检索式 / 来源 / 运行记录）已落地，apps/web 的 WorkspaceShell 内 `stageEntry.entry_cards` 现 4 张基础入口卡：query-builder / sources / literature / search-runs，见 [WorkspaceShell.tsx#L517-L544](file:///d:/workspace/MedA/apps/web/src/components/WorkspaceShell.tsx#L517-L544)
  - shared-sdk MedaClient 已支持 `createProject`、`listProjects`、`saveSearchQueryVersion`、`createSearchRun`、`getSearchRunDetail`，见 [client.ts#L555-L639](file:///d:/workspace/MedA/packages/shared-sdk/src/client.ts#L555-L639)
- **本 spec 目标**: **不重写任何 Wave 8 核心逻辑（BM25/去重/PICO/worker 全复用），仅在最薄的入口层做增量** — 新增 1 组「预设主题常量」+ 1 张 Workspace 第 4 行「一键 PubMed Demo」紫色高卡 + 6 个胶囊按钮 + 1 个自动种子工具 ensureDemoProjectAndQuery + 1 个 CLI 脚本 demo_pubmed_end2end.py，使首次打开 Workspace 的用户点 1 下胶囊即可 2~6 s 内看到真实 PubMed 文献在四面板完整联动。

---

## 1. Non-Goals & Scope Guard

1. **不做 CNKI / 万方 demo 入口**：机构反爬不友好，演示成功率低；留 Wave 8.2 后续再考虑。本 spec 6 个 preset 的 `selected_sources` 固定只含 `["pubmed"]`。
2. **不重写四面板渲染**：SearchRun 完成后跳现有 SearchRunDetailScreen，100% 复用现有 PRISMA / BM25 / 文献库 / PICO 渲染，零改逻辑。
3. **不改 adapter 内部 mode 机制**：继续用 Wave 8 ctx.adapter_modes + env `MEDA_PUBMED_MODE` 三级解析；本 spec 只在「用户点击一键 Demo 时」显式传 `adapter_modes = { pubmed: "prefer_real" }` 给 `createSearchRun` 的上下文（若有该字段；没有就不传，依赖 env 默认）。
4. **不新增后端 API 端点**：`createSearchRun` / `getSearchRunDetail` / `createProject` / `saveSearchQueryVersion` 13 端点全复用；种子工具 `ensureDemoProjectAndQuery` **放前端 utility（shared-sdk `demoSeedings.ts`）** 里串现有 API 调，零改 workspace router。
5. **不引新依赖**：前端不用新增 npm 包，后端不用新增 python 依赖；CLI 脚本只用现有 httpx/pydantic/sqlmodel。
6. **不接 LLM PICO 提取**：demo 默认只用 rule_baseline 引擎（不需要 LLM key，演示成功率 100%）。

---

## 2. 数据常量层：6 个 DEMO_PRESETS（shared-sdk 单源真理）

### 2.1 新增文件/导出

在 `packages/shared-sdk/src/presets.ts`（新文件）导出：

```ts
export type DemoPreset = {
  key:
    | "sglt2i_ckd"
    | "sglt2i_hfredef"
    | "met_cv_presto"
    | "glp1_mace_rws"
    | "sglt2i_dka_safety"
    | "met_lifestyle_predm";
  label: string;
  badge: string; // 胶囊右侧小文案，例如 "标杆研究"
  expected_hits_hint: string; // 胶囊 count 小标签，例如 "预计 2k~ hits"
  project_name: string; // ensureDemoProjectAndQuery 自动创建时的默认项目名
  query_name: string; // ensureDemoProjectAndQuery 创建 query version 时的 query_name
  boolean_text: string; // PubMed 原生布尔，已做 field tag/MeSH 简化
  selected_sources: ["pubmed"];
  pico: {
    p: string;
    i: string;
    c: string;
    o: string;
  };
  filters?: {
    study_type?: Array<"rct" | "sr" | "rct_and_sr">; // 传到 createSearchRun.filters
    pubmed_mindate?: string; // YYYY/MM/DD
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
) as Record<DemoPreset["key"], DemoPreset>;
```

### 2.2 共享位置要求

- `packages/shared-sdk/src/presets.ts` **必须从 `packages/shared-sdk/src/index.ts` re-export** `DEMO_PRESETS` / `DEMO_PRESET_BY_KEY` / `DemoPreset`；**apps/desktop 复用同一个 preset 源**，禁止在 apps/web 和 apps/desktop 各写一份硬编码（避免分叉）。
- 旧代码若 apps/web 内部写过临时 preset，**删除**，改为 `import { DEMO_PRESETS } from "@meda/shared-sdk"`。

---

## 3. Workspace 一键 PubMed Demo 卡（方案一：Workspace 内入口）

### 3.1 放置位置与样式

**位置**：沿用现有 WorkspaceShell 两栏布局（左主区 + 右阶段助手），放在「子入口导航」4 张基础入口卡（query-builder / sources / literature / search-runs）下方，**独立 section，纵向独占整行**，grid-column 1/-1。

**视觉约束（必须满足）**：
1. **紫色渐层高亮卡**：`background: linear-gradient(135deg, rgba(99,102,241,0.12), rgba(34,211,238,0.05))`；边框 1.5px solid var(--accent，#6366F1)，不与其他 entry 卡同色。
2. **NEW 角标 pill**：左上 `NEW · 一键真实数据 Demo` 白色实心紫色字。
3. **标题 + 描述**：标题 emoji "🧪" + "用 PubMed 真实文献跑通完整检索流水线（仅 PubMed，约 2~6 秒）"；描述解释：点胶囊自动创建/跳到项目 + SearchRun 自动发起 + 自动跳到运行详情页。
4. **6 胶囊按钮行**：flex-wrap gap-8；胶囊用现有 `<Pill>/<button className="chip">` 风格；每颗胶囊右侧小浅灰 `expected_hits_hint` 文字。
5. **底部 3 status pill**：
   - `<Pill tone="ok">已连网 prefer_real</Pill>`
   - `<Pill tone="warn">无网络时自动 fallback 注入 demo 集</Pill>`
   - `<Pill tone="info">仅 PubMed 单源 · 不触发机构反爬</Pill>`

### 3.2 点击行为

用户点某 preset 胶囊时走下面的异步序列，**所有步骤都包裹单条 `try/catch`，失败时 Workspace 顶部 toast 显示「Demo 启动失败：xxx」并回到可重点击状态**：

```
ensureDemoProjectAndQuery(user_ctx, preset)
  => { project_id, query_id, query_version }
  => createSearchRun(project_id, payload = {
       query_id,
       query_version,
       selected_sources: ["pubmed"],
       filters: preset.filters ?? {},
       // 若 Wave 8 createSearchRun 已支持上下文传 mode 就传；否则只依赖 env 默认
       adapter_modes: { pubmed: "prefer_real" }  [若 schema 已支持]
     })
  => search_run_id
  => 切换 screen = "search-run-detail" 并 poll 每 1.5 s getSearchRunDetail(search_run_id)
       直到 detail.status 属于 {completed, failed, cancelled}
```

- 初始 screen state：**不要求项目必须已存在**；零项目时 ensureDemoProjectAndQuery 自动创建项目 + query + version；零 query 时自动创建 query。
- **自动跳转后保留"返回 Workspace"按钮**：沿用 SearchRunDetailScreen 现有 `onBackToRunList` prop，不新增 UI。

### 3.3 缺省项目/检索式的自动种子工具 ensureDemoProjectAndQuery（shared-sdk utility，零新 API）

新文件：`packages/shared-sdk/src/utils/demoSeedings.ts`（必须从 index.ts re-export `ensureDemoProjectAndQuery`）

函数签名 & 语义：

```ts
export type EnsureDemoResult = {
  project_id: number;
  project_created_this_call: boolean;
  query_id: number;
  query_version: string;
};

/**
 * 前端串现有 4 个 API，保证 createSearchRun 所需的 project/query 都存在。
 * 1. 若 workspaceHome prop 已有 project → 复用；若无项目（listProjects().length==0）
 *    → 调 createProject({ org: session.org_slug, owner: session.user_id, name=preset.project_name, description='Auto-created by PubMed one-click demo.' })
 * 2. 对选中的项目调 getWorkspaceHome → query-builder stage；若无已保存 query
 *    → 先调 onOpenSearchQueryBuilder(projectId)（会返回 query_id）
 *    → 再 saveSearchQueryVersion(project_id, payload= {
 *          query_id,
 *          query_name: preset.query_name,
 *          selected_sources: preset.selected_sources,
 *          grouped_terms: build_grouped_terms_from_pico(preset.pico),
 *          expression_blocks: build_expression_from_boolean_text(preset.boolean_text)
 *        })
 * 3. 返回 {project_id, query_id, query_version}
 */
export async function ensureDemoProjectAndQuery(
  client: MedaClient,   // 或者直接把需要的方法拆成参数
  session: SessionContext,
  preset: DemoPreset,
  options?: {
    fallbackProjectId?: number;
    forceNewProject?: boolean;
  },
): Promise<EnsureDemoResult>;
```

**两个 helper（不 export 默认实现只给该 utility 内部用）**：
- `build_grouped_terms_from_pico(pico)`：P/I/C/O 每组各 1 个 SearchTermGroup，terms 按简单 "空格+逗号+/+分号" 拆分，保证 saveSearchQueryVersion 不因为 empty grouped_terms/empty expression_blocks 校验 422。
- `build_expression_from_boolean_text(boolean_text)`：直接生成 **单块 LiteralBoolean 型 expression_block**，expression 字符串就是 preset.boolean_text 原值；不需要 parse/拆分，因为 rule_baseline 和 PubMed adapter 最终都是拿已解析的 boolean_text 跑。

**幂等要求（非常重要，防刷）**：
1. 同一个 preset.key + 同一个 org 下若 **已存在同名 project.name == preset.project_name**，**不新建 project**，直接拿第一个 match 的 id 复用（防止用户连续点 5 次建 5 个项目）。
2. 同一个 project_id 下若 **已存在 query.name == preset.query_name 的已保存 version**，**不新建 query_version**，直接复用最近的一个 version。
3. 「同名已存在」判断只走「前缀精确匹配」，不做模糊匹配；避免误把用户自己的项目匹配上。

### 3.4 WorkspaceShell 代码级插入点

现有代码块在 [WorkspaceShell.tsx#L508-L579](file:///d:/workspace/MedA/apps/web/src/components/WorkspaceShell.tsx#L508-L579)：
- `<section>子入口导航</section>`（4 张 SummaryButton）结束后；
- `<section>最近任务+最近产物</section>` 之前；
- **插入新的 `<section style={{ marginTop: 20 }}>一键 PubMed Demo 卡</section>`**。

同时：
1. `import { DEMO_PRESETS, ensureDemoProjectAndQuery, type DemoPreset } from "@meda/shared-sdk";`
2. `WorkspaceShellProps` 增加（如果没有）：`client: MedaClient;` — 或者如果现已有 client 实例就复用；**禁止内部用 inline `new MedaClient` 新建实例**。
3. 桌面端 apps/desktop App.tsx 同插入点同步加同一节 UI 卡 + 同一行为；**UI 样式、preset、点击行为 100% 代码通过 shared-ui 组件化复用**，不要在 desktop 再写一套 6 胶囊硬编码。

组件化复用要求（避免 web/desktop 分叉）：
- 新建 `packages/shared-ui/src/WorkspaceOneClickPubmedDemo.tsx`，props = `{ session, client, workspaceHome?, fallbackProjectId?, onRunCreated: (searchRunId)=>void, onNavigateBack? }`；内部就是紫色卡 + 6 胶囊 + ensureDemoProjectAndQuery + createSearchRun + toast + onRunCreated。WorkspaceShell / App.tsx 直接 `<WorkspaceOneClickPubmedDemo ... />` 引入。

---

## 4. CLI 脚本 Demo（方案三：演示友好可录制）

### 4.1 入口文件

新文件：`apps/agent-core/scripts/demo_pubmed_end2end.py`

> 脚本要满足 **既可 `python scripts/demo_pubmed_end2end.py sglt2i_ckd` 本地独立运行**，也可被 CI 脚本调用；核心逻辑放到可被 pytest 直接 monkeypatch 的纯函数里。

### 4.2 6 预设 key（Python 侧同步真理来源）

**Python 侧禁止重写一整份英文布尔查询**；做法是：
- 从 [apps/agent-core/app/services/sources/\_\_init\_\_.py] 里新增或直接在脚本里：
  - Python 侧 `DEMO_PRESETS_PY` 只存 6 个 key + 对应的 `boolean_text` 字符串（从 shared-sdk presets.ts 直接复制粘贴，**两份必须在 CI 里做内容 diff gating**：见 §6 测试策略里的「presets 一致性测试」）。

### 4.3 脚本结构

```python
# apps/agent-core/scripts/demo_pubmed_end2end.py
from __future__ import annotations

import argparse
import asyncio
import csv
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import re
from app.services.sources.pubmed_adapter import PubMedAdapter
from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext, UnifiedLiteratureEntry

DEMO_PRESETS_PY: dict[str, dict] = {
    # 内容与 §2 的 ts DEMO_PRESETS 的 key + boolean_text 一一对应
    # CI presets 一致性测试（§6.4）断言 ts JSON dump == py JSON dump（仅比 key,boolean_text,pico 四个域）
}


@dataclass
class DemoResult:
    preset_key: str
    search_run_id: int
    raw_hits: int
    after_dedupe_hits: int
    bm25_top3: list[dict]  # title, score, year, doi
    pico_top5: list[dict]  # domain, value, freq
    csv_export_path: str | None
    warnings: list[str]
    fallback_mode: bool  # True 时表示因为网络/反爬走了注入集


def _resolve_mode_or_exit(preset_key: str):
    if preset_key not in DEMO_PRESETS_PY:
        print(f"[demo] ERROR: unknown preset '{preset_key}'.", file=sys.stderr)
        print("[demo] Available keys:", ", ".join(sorted(DEMO_PRESETS_PY.keys())), file=sys.stderr)
        sys.exit(2)


from app.services.bm25_scoring import compute_bm25_scores_for, tokenize_for_bm25
from app.services.literature import _detect_duplicate, _normalize_identifiers
from app.services.pico import _rule_baseline_extract


async def run_pubmed_demo(
    preset_key: str,
    *,
    export_csv: bool = True,
    export_dir: Path | None = None,
) -> DemoResult:
    """核心纯异步函数 —— pytest 直接 import 调用，httpx monkeypatch ConnectError 验证 fallback。

    说明：CLI Demo 不写 DB（不建 project/SearchRun/LiteratureRecord），仅用内存对象跑
    「PubMed adapter → 规范化 → 内存三级去重 → BM25 打分 → rule_baseline PICO 词频」
    四步纯函数管道；要落库拿 SearchRun ID 跑完整四面板联动请走前端 Workspace 一键入口。
    """
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
    adapter_result = await adapter.run_search(norm_q, ctx)

    # 1. 标识符规范化（同 Wave 8 search_worker._execute_single_source 代码）
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

    # 2. 内存三级去重（DOI→PMID→标题+年份，同 Wave 8 _detect_duplicate 语义的纯函数版）
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

    fallback_mode = (
        bool(adapter_result.warnings)
        and any("fallback" in w or "注入" in w for w in adapter_result.warnings)
    )

    # 3. 构造最小 LiteratureRecord duck 对象（只含 title/abstract/year/journal/doi/pmid 字段）
    #    用于 compute_bm25_scores_for 内部的 _doc_tokens(tokenize_for_bm25(title + abstract))，
    #    因为该函数签名只接 Sequence[LiteratureRecord]，最小 duck 对象（@dataclass 或 attrdict）即可：
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

    # 4. BM25 打分：query_tokens = tokenize_for_bm25(boolean_text + p + i + c + o)
    pico = preset.get("pico") or {}
    q_raw = " ".join(
        [preset["boolean_text"]]
        + [str(pico[k]) for k in ("p", "i", "c", "o") if pico.get(k)]
    )
    q_tokens = tokenize_for_bm25(q_raw)
    if mini_records and q_tokens:
        scores = compute_bm25_scores_for(mini_records, q_tokens)
        max_s = max(scores) if scores and max(scores) > 0 else None
        for m, s in zip(mini_records, scores):
            m.bm25_score = (float(s) / float(max_s)) if max_s is not None else None

    # 5. BM25 Top3
    sorted_by_score = sorted(
        mini_records, key=lambda e: (e.bm25_score is not None, e.bm25_score or 0.0), reverse=True
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

    # 6. PICO rule_baseline 提取 + Top5 词频
    #    说明：_rule_baseline_extract(rec: LiteratureRecord) 返回 LiteraturePico(p/i/c/o_json)，
    #    duck 对象需要 title/abstract 两个属性；_MiniRec 已经满足，直接传（内部只 rec.title / rec.abstract）
    pico_domain_words: dict[str, dict[str, int]] = {"p": {}, "i": {}, "c": {}, "o": {}}
    for m in mini_records:
        pico_obj = _rule_baseline_extract(m)  # type: ignore[arg-type]  # duck typing: has title, abstract
        for dom in ("p", "i", "c", "o"):
            val = getattr(pico_obj, f"{dom}_text") or ""
            # 粗切词（与前端 helper 同粒度）
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
        {"domain": dom, "value": tok, "freq": freq}
        for (dom, tok, freq) in flat[:5]
    ]

    # 7. 可选 CSV 导出
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
            w.writerow(["rank", "title", "year", "journal", "doi", "pmid", "source_record_id", "bm25_score"])
            ranked = sorted(
                mini_records,
                key=lambda x: (x.bm25_score is not None, x.bm25_score or 0.0),
                reverse=True,
            )
            for i, m in enumerate(ranked, 1):
                w.writerow([
                    i, m.title, m.year or "", m.journal, m.doi, m.pmid,
                    m.source_record_id, round(m.bm25_score or 0.0, 4),
                ])
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
    print("========================================================")
    print(f"  MedA · PubMed real-data demo   preset = {r.preset_key}")
    print(f"  {'(no-network fallback injected dataset)' if r.fallback_mode else '(used live NCBI E-utilities)'}")
    print("========================================================")
    print(f"  [① Hits] raw PubMed = {r.raw_hits} | after dedupe = {r.after_dedupe_hits}")
    if r.warnings:
        print(f"  [Warnings]")
        for w in r.warnings:
            print(f"    · {w}")
    print()
    print(f"  [② BM25 top-3]")
    for i, row in enumerate(r.bm25_top3, 1):
        print(f"    {i}. [score={row['score']:.3f}] {row['title']}  ({row['year']}) doi={row['doi'] or 'N/A'}")
    print()
    print(f"  [③ PICO frequent tokens (rule_baseline)]")
    for row in r.pico_top5[:5]:
        print(f"    · [{row['domain']}] {row['value']!r} × {row['freq']}")
    if r.csv_export_path:
        print()
        print(f"  [④ CSV exported] → {r.csv_export_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="MedA · PubMed real-data end-to-end CLI demo.")
    parser.add_argument("preset_key", help="One of: " + ", ".join(sorted(DEMO_PRESETS_PY.keys())))
    parser.add_argument("--no-csv", action="store_true", help="Skip CSV export.")
    parser.add_argument("--export-dir", type=Path, default=None, help="Override CSV export directory.")
    parser.add_argument("--json", action="store_true", help="Dump DemoResult as JSON on success.")
    args = parser.parse_args()

    result = asyncio.run(run_pubmed_demo(args.preset_key, export_csv=not args.no_csv, export_dir=args.export_dir))
    _print_report(result)

    if args.json:
        print()
        print("--- JSON ---")
        print(json.dumps(result, ensure_ascii=False, default=lambda o: getattr(o, "__dict__", str(o)), indent=2))

    # 退出码语义（§1 Non-Goals 外的错误语义 contract，脚本 CI 可断言）:
    #   0 success (live OR fallback 但 after_dedupe_hits > 0)
    #   1 network failed + fallback 注入集本身也 0 条（极罕见）
    #   2 参数错误 / unknown preset
    if result.after_dedupe_hits == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**退出码 contract（对外 promise）**：
- `0`：成功。不管真 HTTP 还是 fallback，只要最终 after_dedupe_hits > 0 就算 0。
- `1`：真 HTTP 失败 + fallback 也 0 条（注入集没配 / 解析全失败）；要排查。
- `2`：参数错 / unknown preset_key。

**输出格式 contract**：
- stdout 固定 4 段：[① Hits] / [② BM25 top-3] / [③ PICO frequent tokens] / [④ CSV exported]，标题固定，方便 CI `grep "\[② BM25 top-3\]"` 校验。
- `--json` 时 stdout 末尾再 dump 整份 DemoResult JSON；其他 4 段人类可读文本仍打印，方便录像用。

---

## 5. 错误处理 & User-Facing Feedback

### 5.1 前端一键 Demo 错误处理矩阵

| 场景 | 处理方式 | UI 反馈 |
| --- | --- | --- |
| Workspace 已有 ≥1 个 project | 复用第一个项目（或 workspaceHome 当前项目），不新建 | toast 不弹（静默成功）|
| 0 个 project + `createProject` 201 ✅ | 自动新建 preset.project_name 同名项目 | Workspace 顶部 info toast：「已自动创建 Demo 项目：MedA-Demo-Diabetes-CKD-2026」 |
| `saveSearchQueryVersion` 返回 422 | 捕获 → toast「保存检索式失败：422 · msg=xxx」；6 胶囊按钮解除禁用，可再点 |
| `createSearchRun` 201 返回 search_run_id | ✅ 立即切到 search-run-detail；**不做 422 兜底**（因为 payload 是 preset 常量硬写的，要是 422 就是代码 bug，直接 console.error + throw） | toast 不弹，只在详情页顶部 status=pending spinner |
| 轮询 `getSearchRunDetail`，在 30 次 ×1.5s = 45s 内仍非终态 | 视为超时；toast「PubMed API 慢响应，仍在后台运行，可到「检索运行记录」稍后查看」；screen 留在详情页 |
| Detail 返回 status=failed | SearchRunDetailScreen 已有 warnings / errors 区展示；不再新增 toast |
| 真网络连不上 PubMed（prefer_real → fallback 注入集成功） | SearchRunSource.status = completed 且 warnings 含「fallback 注入数据 6 条」；SearchRunDetail 自动显示 ⚠ chip；**一键 Demo 区底部 warn pill 已说明，不再额外 toast**。 |

### 5.2 脚本 Demo 错误处理矩阵

| 场景 | 处理方式 | 退出码 |
| --- | --- | --- |
| 真 HTTP ✅ | DemoResult.fallback_mode=False | 0 |
| 真 HTTP 失败 → fallback 注入集 ✅（after_dedupe_hits=6） | fallback_mode=True；[① Hits] 段后打印 Warnings | 0 |
| 真 HTTP 失败 + fallback 注入集也是 0 条（配置坏了） | fallback_mode=True；after_dedupe_hits=0 | 1 |
| `--preset-key sglt2i_xxx_wrong` | stderr 提示 6 个可用 key | 2 |
| `--export-dir` 无写入权限 | 捕获 PermissionError，警告到 stderr，CSV 路径置空，但只要 after_dedupe_hits>0 仍算成功 | 0 |

---

## 6. 测试策略（基线保护：零外网 by default）

> Wave 8 已有 conftest `_force_all_sources_force_mock_for_pytest` autouse + pyproject addopts `-m "not needs_network"`，本 spec **不改动任何默认值**；新增的测试默认全部走 force_mock，保证 `pytest apps/agent-core && pnpm --filter web vitest run && pnpm --filter desktop vitest run` 仍然 0 外网。

### 6.1 前端测试（apps/web + apps/desktop，vitest）

新增文件 1：`apps/web/src/components/__tests__/WorkspaceOneClickPubmedDemo.test.tsx`（shared-ui 里也放同一份到 shared-ui 的测试目录，desktop 直接复用不需要自己再加）

测试点至少 5 条：
1. **test_renders_6_preset_chips_with_correct_labels_and_badges**：渲染 `<WorkspaceOneClickPubmedDemo ...>`，断言 `screen.getByText(/💧 糖尿病肾病 SGLT2i/)` 存在、6 颗 chip count=6。
2. **test_zero_projects__clicks_chip__calls_createProject_and_saveSearchQueryVersion_then_createSearchRun**：vi.mock `client.listProjects.mockResolvedValue([])`，vi.mock `client.createProject.mockResolvedValue({id: 11})`，vi.mock `client.saveSearchQueryVersion.mockResolvedValue({query_version: "v1"})`，vi.mock `client.createSearchRun.mockResolvedValue({id: 99})`；点击 💧 胶囊，断言 createProject 的参数 name == `MedA-Demo-Diabetes-CKD-2026`，assert `createSearchRun` selected_sources == ["pubmed"]。
3. **test_existing_matching_project__does_not_create_new**：vi.mock `client.listProjects.mockResolvedValue([{id: 7, name: preset.project_name, ...}])`，点胶囊后断言 `client.createProject` 未被调用。
4. **test_saveSearchQueryVersion_422__toast_shown**：mock saveSearchQueryVersion.reject(new Error("422 grouped_terms empty"))，点胶囊，assert toast.once("Demo 启动失败：422 · grouped_terms empty")（具体文案按实际实现调整，但必须包含 "422" 和失败原因片段）。
5. **test_expression_block_is_literal_boolean_block_containing_preset_text**：点胶囊后捕获传给 `saveSearchQueryVersion` 的 payload.expression_blocks[0]，断言其类型是 LiteralBoolean，expression 字符串 === preset.boolean_text（**防写错 expression 导致 PubMed 实际跑空**）。

### 6.2 后端测试（apps/agent-core，pytest，默认 force_mock）

新增文件 1：`apps/agent-core/tests/test_demo_pubmed_cli.py`

测试点至少 4 条：
1. **test_unknown_preset_exits_code_2**：`subprocess.run([sys.executable, "scripts/demo_pubmed_end2end.py", "nonexistent_xyz"])` 断言 returncode == 2，stderr 包含 "Available keys:"。
2. **test_run_pubmed_demo_live_success_with_mock_pubmed_http**：用 `httpx.MockTransport` 模拟 PubMed esearch/efetch 返回 2 条真实 XML（复用 test_real_pubmed_xml_parse.py 的 FIXED_PUBMED_XML 前两条），直接 `asyncio.run(run_pubmed_demo("sglt2i_hfredef", export_csv=False))`，断言 raw_hits=2 / after_dedupe_hits≥1 / fallback_mode=False / bm25_top3 len≤3。
3. **test_run_pubmed_demo_connect_error_falls_back_to_injected_and_exit_0**：monkeypatch httpx.AsyncClient.get → raise httpx.ConnectError("no route")；`asyncio.run(run_pubmed_demo(...))`，断言 fallback_mode=True；after_dedupe_hits == len(conftest MOCK_PUBMED_DATASET 3)（注入 PubMed 有 3 条）。
4. **test_main_json_flag_outputs_valid_json**：subprocess 调用传 `--json --no-csv`，stdout 最后一行 `--- JSON ---` 之后的内容 `json.loads` 成功，`result["after_dedupe_hits"] > 0` 为 True。

新增文件 2：`apps/agent-core/tests/test_presets_consistency.py`（关键保护：禁止 ts/py 预设分叉）

测试点 1 条：
1. **test_shared_sdk_demo_presets_vs_python_DEMO_PRESETS_PY_have_same_key_boolean_text_pico**：
   - 用 `subprocess.run(["node", "--input-type=module", "-e", "..."])` 读 shared-sdk presets.ts，导出 DEMO_PRESETS dump JSON；
   - 对比 Python DEMO_PRESETS_PY 6 个 key 的集合完全相等；
   - 对每个 key，比对 `boolean_text` 字符串 **完全相等**（两端都做 `replace(/\s+/g, " ").strip()` 后再比较）；
   - 对每个 key，比对 pico P/I/C/O 四字符串完全相等；
   - 任一不一致 → 该测试 **强制 FAIL**；CI 里必须阻塞合并。

### 6.3 手动标记的真网络测试（默认不跑）

- 不新增任何 @pytest.mark.needs_network 用例；Wave 8 已有的 2 个 needs_network 测试保持不变。

---

## 7. 验收标准（User 可验证，对应 PRD §7 条 7.4）

本 spec 全部实现后，以下 7 条 **均可在 1 次本地无调试启动**（pnpm turbo dev / agent-core uvicorn 启动后）内手动重复验证成功：

1. ✅ 打开 apps/web Workspace 首页 → 看到紫色 NEW 一键 PubMed Demo 卡 → 6 个主题胶囊都能 hover → 底部 3 status pill 全部存在。
2. ✅ 第一次打开、数据库里 **0 个 project** → 点「💧 糖尿病肾病 SGLT2i」胶囊 → info toast「已自动创建 Demo 项目：MedA-Demo-Diabetes-CKD-2026」→ 2~6 s 内自动跳到 SearchRunDetailScreen，sources 里 PubMed 显示 completed 绿色。
3. ✅ PRISMA 漏斗 4 横条有实际数值（Identification > 0，Screening == after dedupe > 0，Eligibility / Included 等占位仍 = Screening，PRD 已接受此简化）。
4. ✅ 文献库面板排序 = relevance 默认；**第 1 条文献 hover 出现 ⭐ 0.XX BM25 徽章**；点击任意一条 → 右侧 PicoPanel 出现 P/I/C/O 四色 Tag（rule_baseline 提取，不要求 LLM）。
5. ✅ 再点同一主题胶囊第二次 → **不新建第二个同名 project**（listProjects().filter(name==preset.project_name).length 仍 == 1）。
6. ✅ 终端跑 `python apps/agent-core/scripts/demo_pubmed_end2end.py sglt2i_hfredef --json --no-csv` → stdout 有 [①②③④] 四段 → `--- JSON ---` 后 JSON parse 成功 → 返回码 0。
7. ✅ **pytest/pnpm 全量测试 ≥ 原 baseline 206 passed**（仅新增，无减少；`pytest apps/agent-core` 默认 force_mock，零外网）。

---

## 8. 风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
| --- | --- | --- | --- |
| PubMed API 演示时真的慢（NCBI 高峰期 10s+） | 中 | Demo 观感差 | §5.1 轮询超时 45s 提示仍在后台跑；同时脚本 Demo 用注入集 fallback 可随时演示（1s 内完成）。 |
| TS/Python 两份预设布尔查询分叉，造成一边跑不出来 | 高 | Demo 命中率下降或失败 | §6.2 新增 presets 一致性测试 **CI 阻塞合并**，完全禁止分叉。 |
| 连续点 5 次胶囊建 5 个同名 project | 中 | Workspace 污染 | §3.3 ensureDemoProjectAndQuery **幂等：同名复用**。 |
| `build_grouped_terms_from_pico` 拆分错，导致 saveSearchQueryVersion 422 | 中 | 422 → Demo 失败 | §3.3 helper 用正则按 `/[ ,;，；\/]+/` 粗拆，保证至少 4 个 group、每 group ≥1 term；前端 §6.1 test 5 断言 saveSearchQueryVersion 调用参数里 grouped_terms 非空。 |
