# Wave 8.4 收尾 · 方案 2 规格说明书 (Spec)

- **Spec 版本**：v1.0
- **创建日期**：2026-08-18
- **对应计划文档**：[`docs/superpowers/plans/2026-08-17-wave-8-4-plan.md`](file:///d:/workspace/MedA/docs/superpowers/plans/2026-08-17-wave-8-4-plan.md)
- **设计目标**：补齐 Wave 8.4 计划中缺失的 3 个前端报告组件（ReportContentEditor8 / ReportGeneratorPanel / HtmlPreviewFrame）+ 修复 1 个回归（search_worker partial_failed 标记）+ 后端仅 additive 扩展 8 章节覆写字段，**全程不触碰 NOTOUCH-5 基线**。
- **测试目标**：
  - Python pytest ≥ **449 passed**（实际期望 ≥ 450），≥ 8.4 Plan 要求的「≥ 431 GREEN」
  - TypeScript shared-ui vitest ≥ **455 passed**，≥ 8.4 Plan 要求的「≥ 379 GREEN」
  - 合计 ≥ **904 GREEN**（≥ 8.4 Plan 要求的 ≥ 810）

---

## 0. 硬约束 (NOTOUCH-5)

以下 5 类文件/代码块在本任务中**字节级不修改**（如必须扩展，只能走 additive 可选参数 / append-only 类型）：

1. `apps/agent-core/app/services/stats_evidence.py` 内部 Meta 计算逻辑（函数签名、返回结构、常量）
2. `apps/agent-core/app/services/meta_analysis.py` 内部 DL/IV/MH 计算
3. 所有 Wave 8.3 已有的序列化函数签名（`serializeRIS` / `serializeBibTeX` / `serializeCSV` / 所有证据表导出列顺序）
4. 所有 Wave 8.3 模型表字段定义（即 `models.py` 中 `GradeAssessment` / `SofTableRow` / `ReportSnapshot` / `Prisma2020Checklist` 四张表定义完成前的所有表，字段名/类型/默认值不改）
5. 所有 Wave 8.3 REST 端点的响应字段集合（键名不改；本 spec 涉及的 `POST /report/generate` 返回集合不变）

本 spec 所有后端改动都使用「**optional 参数 + if has → 才生效**」模式：**不传 override 时，报告引擎输出字节级与 8.3 baseline 相同**。

---

## 1. 架构总览

### 1.1 五节点数据流

```
[1 ReportContentEditor8.tsx]
        │ produce: Report8ChaptersDraft
        ▼
[2 useReportEditorController.ts]
        │ fetchClient injected
        │ payload = ReportGeneratePayload (version_label + 8 override_chN)
        ▼
[3 POST /projects/{pid}/report/generate  (workspace.py#L1343)]
        │ read 8 override_chN fields with dict.get(...)
        │ (NOT IN PAYLOAD → None → SKIP)
        ▼
[4 report_engine.generate_report_three_formats(pi, overrides=None|dict)]
        │ overrides=None → behavior === 8.3 baseline (NOTOUCH-5)
        │ overrides provided → only override chapters where key present
        ▼
[5 ReportGeneratorPanel.tsx + HtmlPreviewFrame.tsx]
        md / html / txt
        SHA256(grade) + SHA256(analysis) === ReportSnapshot row
        → 单一真相源，UI 展示内容 100% 持久化匹配
```

### 1.2 文件变更清单（12 个 = 7 NEW + 4 MOD additive + 1 FIX）

| # | 文件 | 类型 | 说明 |
|---|---|---|---|
| **F1** | `packages/shared-ui/src/report/ReportContentEditor8.tsx` | NEW 组件 | 8 章节 Markdown 编辑器，受控件，2 个 Import 按钮（上游草稿 / 恢复最近版） |
| **F2** | `packages/shared-ui/src/report/ReportGeneratorPanel.tsx` | NEW 组件 | MD/HTML/TXT 三 Tab + 版本号 + SHA256 徽章 + 3 导出按钮 + status 状态机 + 422 错误提示 |
| **F3** | `packages/shared-ui/src/report/HtmlPreviewFrame.tsx` | NEW 组件 | iframe sandbox="" srcDoc 渲染空态/报告 HTML，禁 scripts/外链 |
| **F4** | `packages/shared-ui/src/hooks/useReportEditorController.ts` | NEW Hook | 状态机 + 2 个 Import 纯函数 + 调 REST（fetchClient injectable）+ 生成 computed Editor/Panel/Preview Props |
| **F5** | `packages/shared-ui/src/__tests__/ReportContentEditor8.test.tsx` | NEW 测试 | 20 vitest（E1~E20） |
| **F6** | `packages/shared-ui/src/__tests__/ReportGeneratorPanel.test.tsx` | NEW 测试 | 15 vitest（P1~P15） |
| **F7** | `packages/shared-ui/src/__tests__/HtmlPreviewFrame.test.tsx` | NEW 测试 | 5 vitest（H1~H5） |
| **F8** | `packages/shared-ui/src/index.ts` | MOD +export | append 导出 3 组件 + 1 Hook + 2 内部纯函数（`parseSnapshotInto8Chapters`, `generateDraftFromUpstream`） |
| **F9** | `packages/shared-sdk/src/index.ts` | MOD +types | append only 两个类型：`Report8ChaptersDraft`、`ReportGeneratePayload`（全部 8.3 已有类型零修改） |
| **F10** | `apps/agent-core/app/routers/workspace.py` | MOD additive | 从 `payload` 读取 8 个 `override_chN_*` 字段；**无 payload 时跳过**（NOTOUCH-5）→ 传进报告引擎 |
| **F11** | `apps/agent-core/app/services/report_engine.py` | MOD additive | `generate_report_three_formats(pi, overrides=None)` 新增 optional 参数；每个 override 键存在且非空字符串才调用 `_replace_section_body(...)` 覆盖对应章 |
| **F12** | `apps/agent-core/app/services/search_worker.py` | FIX 回归 | 修改 `_run_parallel(...)` 的 finally/catch：`success_count < total_sources` → run.status = `"partial_failed"` 且 `run.errors.append(...)` |

### 1.3 shared-sdk append-only 新增类型

```ts
// packages/shared-sdk/src/index.ts 末尾追加（不修改任何已有类型/字段）
export type Report8ChaptersDraft<IdT = number> = {
  ch1_background: string;
  ch2_methods: string;
  ch3_pico: string;
  ch4_results: string;
  ch5_grade_assessment: string;
  ch6_summary_of_findings: string;
  ch7_discussion: string;
  ch8_appendices: string;
  source_snapshot_id?: IdT | null;
};

export type ReportGeneratePayload<IdT = number> = {
  version_label?: string;
  override_ch1_background?: string;
  override_ch2_methods?: string;
  override_ch3_pico?: string;
  override_ch4_results?: string;
  override_ch5_grade_assessment?: string;
  override_ch6_summary_of_findings?: string;
  override_ch7_discussion?: string;
  override_ch8_appendices?: string;
};
```

---

## 2. ReportContentEditor8（F1）

### 2.1 Props 契约

```ts
export function ReportContentEditor8({
  value,
  onChange,
  onImportFromUpstream, // 可选；未传 → 按钮 disabled
  onRestoreSnapshot,    // 可选；未传 → 按钮 disabled
  latestSnapshotId,
  disabled = false,
}: {
  value: Report8ChaptersDraft | null;
  onChange: (next: Report8ChaptersDraft) => void;
  onImportFromUpstream?: () => void;
  onRestoreSnapshot?: () => void;
  latestSnapshotId?: number | null;
  disabled?: boolean;
}): JSX.Element;
```

### 2.2 视觉与 DOM 语义

- 顶部 Toolbar（`role="toolbar" aria-label="editor-toolbar"`）：
  - 按钮 `data-testid=btn-import-upstream`：主色（primary），文字「⬇ 从上游数据生成草稿」
  - 按钮 `data-testid=btn-restore-snapshot`：警告色（warn），文字「↺ 恢复最近版 (id=#N)」，latestSnapshotId 为空时 disabled
  - 右侧状态提示：「草稿状态：未保存（纯前端中间态），生成快照后才持久化」
- 8 章主体：2 × 4 网格（grid-template-columns: 1fr 1fr），第 8 章 Appendices 独占一行 `grid-column: 1 / -1`
- 每章卡片：
  - `<header>`：序号圆标（1~8，蓝色 chip）+ 标题 + 「自动/可自动/人工精修」标签 + 字符数计数（实时统计）
  - `<textarea data-testid=ch{1..8}_textarea>`：
    - 160px 最小高度，resize: vertical
    - **正文不包含 `## 1. Background` 自身标题**（标题由报告引擎输出时自动加上；Editor placeholder 明确提示用户不要在正文里重复写章节名）
    - 字体 `ui-monospace, Menlo, Consolas, monospace` 11.5px
    - focus 蓝色 outline + input 高亮背景
- value=null 时 8 个 textarea 全空，显示 placeholder。

### 2.3 Import 回显纯函数（定义在 useReportEditorController，F4 导出可被 F5 测试）

**A. `parseSnapshotInto8Chapters(md: string): Report8ChaptersDraft`**

8 章节正则匹配锚点（中英文双识别，大小写不敏感，数字后可加 `.`/`、`/空格` 混合）：

| ch | 英文锚（正则一） | 中文锚（正则二） |
|---|---|---|
| 1 | `^##?\s*1\.\s*Background` | `^##?\s*1[.、]\s*(研究)?背景` |
| 2 | `^##?\s*2\.\s*Methods` | `^##?\s*2[.、]\s*(研究)?方法(学)?` |
| 3 | `^##?\s*3\.\s*PICO` | `^##?\s*3[.、]\s*PICO` |
| 4 | `^##?\s*4\.\s*Results?` | `^##?\s*4[.、]\s*(研究)?结果` |
| 5 | `^##?\s*5\.\s*GRADE\s+Assessment` | `^##?\s*5[.、]\s*(证据质量|GRADE)(评估)?` |
| 6 | `^##?\s*6\.\s*Summary\s+of\s+Findings?` | `^##?\s*6[.、]\s*(证据概要(表)?|SoF表|Summary)` |
| 7 | `^##?\s*7\.\s*Discussion` | `^##?\s*7[.、]\s*讨论` |
| 8 | `^##?\s*8\.\s*Append(ix|ices)` | `^##?\s*8[.、]\s*附录` |

算法：
1. `lines = md.split('\n')`，先抽每章首行索引
2. 从「第 N 章首行 + 1」到「下一章首行 - 1 / EOF」为正文
3. 自动 strip 每章正文首尾空行
4. 锚缺失对应 chN = `""`（空字符串）
5. `source_snapshot_id` 由函数调用方额外传（parse 自身不携带）

**B. `generateDraftFromUpstream(input): Report8ChaptersDraft`**

```ts
type UpstreamInput = {
  pico?: { population?: string; intervention?: string; comparator?: string; outcomes?: string[] } | null;
  gradeRows?: GradeAssessment[] | null;
  sofRows?: SofRow[] | null;
  searchMeta?: { hitsPerDb?: Record<string, number>; searchedAt?: string } | null;
};
```

填充规则：

| ch | 填充策略 |
|---|---|
| 1. Background | 有 pico → 骨架：「本系统评价的目标人群：{P}；干预：{I}；对照：{C}。\n\n## 临床背景\n【请补充疾病负担 / 未满足临床需求 / 机制假说】」；无 pico → `""` |
| 2. Methods | 骨架：「## 纳入排除\n【请按 PICOS 细化】\n\n## 检索策略\n【请按数据库逐条写】\n\n## 统计方法\n【请选效应量/模型】」+ 若 searchMeta.hitsPerDb 有值则加一段表格骨架 |
| 3. PICO | 有 pico → 标准四行：`- **Population**：{P}\n- **Intervention**：{I}\n- **Comparator**：{C}\n- **Outcome**：{O1、O2、...}`；无 → `""` |
| 4. Results | 有 sofRows → 自动生成「## 文献检索结果（占位）\n初筛 N 条 → 终筛 K 项 RCT（n = Σ sofRows.participants_n）\n\n## Meta 分析结果\n[对应 SofRow × 每结局：{outcome_label}，效应 {effect_measure_label}]」；无 sofRows → `""` |
| 5. GRADE | 有 gradeRows → 逐结局：「## 结局 {outcome_id}：{outcome_label}\n- Overall Certainty：{certainty_final}\n- RoB：{domains_5.risk_of_bias} / Indirectness：{domains_5.indirectness} / Inconsistency：{domains_5.inconsistency} / Imprecision：{domains_5.imprecision} / PubBias：{domains_5.publication_bias}」；无 → `""` |
| 6. SoF | 有 sofRows → Markdown 12 列表头对齐 sof_table_engine：`\| Outcome \| k \| N \| Effect \| AR Control \| AR Intervention \| GRADE \|` + 行；无 → `""` |
| 7. Discussion | 骨架：「## 总体发现\n【请总结 3-5 点】\n\n## 证据强度\n【结合 GRADE 评级】\n\n## 局限性\n【请按 PICOS / 模型假设 / 数据缺失】\n\n## 与现有研究一致/不一致性\n【请补充外部对照】」|
| 8. Appendices | searchMeta.hitsPerDb 有值 → 按 db 列检索策略骨架；无 → 空。无论如何都附 3 个章节子标题占位（检索策略 / PRISMA 声明 / 纳入研究） |

`source_snapshot_id = null`（从上游生成的草稿无来源快照）。

### 2.4 测试矩阵（20 vitest，F5）

| ID | 断言 | data-testid / Prop |
|---|---|---|
| E1 | 8 个 textarea 存在 + 两个按钮存在 | `ch{1..8}_textarea` ×8 |
| E2 | 修改 ch1 → onChange 被调用 1 次且新对象 deep equal 其他字段不变 | Props onChange mock |
| E3 | 修改 ch1 不影响 source_snapshot_id（保持不变） | value 对比 |
| E4 | 黄金 fixture md（8.4 plan 示例 MD）→ 解析出 8 章节 deep equal 期望 | 新增 fixture 资源 |
| E5 | 全中文标题 md（「1. 研究背景」…）→ 同样解析出 8 章节 | 中文 fixture |
| E6 | md 缺失 ch5、ch7 → 对应字段为 `""`，其余正常 | 残缺 fixture |
| E7 | `generateDraftFromUpstream({})` → 8 字段全空串，`source_snapshot_id = null` | |
| E8 | `generateDraftFromUpstream({ pico })` → ch3 满 + ch1/ch2 骨架，ch5/ch6 空 | |
| E9 | `generateDraftFromUpstream({ gradeRows, sofRows })` → ch4/ch5/ch6 有内容 | |
| E10 | `generateDraftFromUpstream({ 全四种 })` → 八章均有内容（无空 `""`）| |
| E11 | disabled=true → 8 个 textarea 均有 `disabled` 属性，两个按钮 disabled | |
| E12 | `latestSnapshotId = null` → 恢复最近版按钮 disabled；传数字 → 文案含 id=#N | |
| E13 | 空 value 时 8 个 textarea 显示 placeholder（不抛 NPE） | value=null |
| E14 | ch1 每输入一个字符字数实时变化；5000 字符不崩溃，可显示数字 | 字符数显示 |
| E15 | value 从 null → 有值（受控切换）→ 8 textarea 的 defaultValue/value 正确同步 | |
| E16 | onClick btn-import-upstream → `onImportFromUpstream()` 触发 1 次 | |
| E17 | onClick btn-restore-snapshot → `onRestoreSnapshot()` 触发 1 次 | |
| E18 | 8×2 网格布局：第 1/2、3/4、5/6、7/8 对同行；第 8 章独占一行（window ≥ 900px） | 断言 CSS |
| E19 | 各 textarea placeholder 明确提示「不要在正文里重复写章节标题」 | 读取 placeholder |
| E20 | onChange 不抛（即使章节 key 有错拼写）——健壮性测试 | 错误注入 |

---

## 3. ReportGeneratorPanel + HtmlPreviewFrame（F2 + F3）

### 3.1 ReportGeneratorPanel Props（F2）

```ts
export function ReportGeneratorPanel({
  projectId,                         // 仅用于调试 tooltip；可选
  activeFormat,                      // 受控父组件驱动
  onFormatChange,                    // Tab 点击时触发
  mdContent, htmlContent, txtContent, // null = 还没生成
  versionLabel = "v0.1-draft",
  sha256Grade,                       // 64 字 hex；UI 显示前 8 位，title 全量
  sha256Analysis,
  status,
  errorDetail,
  onGenerate,                        // 点击「生成新版」时触发（Controller 负责调 REST）
  onExport,                          // 点击导出按钮触发；内部复用 ReportExportMenu3Formats 子组件
  snapshotId,
}: {
  projectId?: number | string;
  activeFormat: "md" | "html" | "txt";
  onFormatChange: (f: "md" | "html" | "txt") => void;
  mdContent: string | null;
  htmlContent: string | null;
  txtContent: string | null;
  versionLabel?: string | null;
  sha256Grade?: string | null;
  sha256Analysis?: string | null;
  status: "idle" | "loading" | "ok" | "error_422";
  errorDetail?: string | null;
  onGenerate?: () => void;
  onExport?: (x: { format: "md" | "html" | "txt" }) => void;
  snapshotId?: number | null;
}): JSX.Element;
```

### 3.2 DOM 结构 + 状态机

- 上区 Header：三列 Flex
  - 左：`<h3>报告生成面板</h3>` + 版本号输入框（只读显示 versionLabel，若用户输入新 label → 通过 onGenerate(opts) 传父）
  - 中：SHA 两个 `<span class="sha-chip">G:{前8位}</span>` + `<span class="sha-chip">A:{前8位}</span>`（sha null 时显示「—」+ 灰背景）；tooltip `title=` 展示 64 位全文
  - 右：`<button data-testid=btn-generate-report>` 生成新版（主色）；loading 时按钮显示 spinner + disabled
- 中区 Tab + 内容：
  - Tab 栏 `role="tablist"` 三个 Tab：`data-testid=tab-md` / `tab-html` / `tab-txt`，选中的 `aria-selected=true`
  - 内容区：
    - `status=loading` → 三 Tab 共用一个 `aria-busy=true` 灰色骨架屏；`onExport` 三按钮 disabled
    - `status=ok` → 选中 Tab 的对应 `<pre data-testid=format-md-content>` / `format-html-source` / `format-txt-content` 展示全文；max-height: 420px + scroll
    - `status=error_422` → 对应 Tab 内容不显示，改为错误横幅（见下节 3.4）
- 下区 Export 栏：直接嵌入现有 `ReportExportMenu3Formats` 子组件，把 `onExport` 透传；禁用条件 = `status !== ok` 或对应内容为 null

### 3.3 HtmlPreviewFrame Props（F3）

```ts
export function HtmlPreviewFrame({
  srcDoc,
  title = "Report HTML Preview",
  onLoad,
  sandboxAllow = [],
}: {
  srcDoc: string | null;                    // null = 空态（渲染占位，不建 iframe）
  title?: string;
  onLoad?: () => void;
  sandboxAllow?: Array<"allow-forms" | "allow-same-origin">;
}): JSX.Element;
```

**安全不变量（写死在组件内，无法通过 Props 绕过）：**

1. iframe 的 `sandbox` prop = `sandboxAllow.join(' ')`，**绝不默认包含 `allow-scripts` / `allow-popups` / `allow-top-navigation` / `allow-popups-to-escape-sandbox`**；父组件即使传错也会在组件内部过滤掉这 4 个危险关键字
2. `referrerPolicy = "no-referrer"`
3. `csp = "default-src 'unsafe-inline' data:; script-src 'none'; font-src 'unsafe-inline' data:; img-src 'unsafe-inline' data: blob:;"`（浏览器支持时生效；不支持时 sandbox + srcDoc 自包含依然有效）
4. 仅当 `srcDoc != null` 时才渲染 iframe；否则渲染：
   ```html
   <div class="preview-empty" data-testid=preview-empty>
     <p>尚未生成报告，请先点击『生成新版』</p>
   </div>
   ```

### 3.4 HTTP 422 detail 字面值 → UI 映射（严格 switch，default 兜底）

```ts
// F2 内部常量，export 给测试使用
export const HTTP_422_DETAIL_MAP: Record<string, { text: string; action?: "disable-generate" | "go-grade" | "go-prisma" }> = {
  output_stage_locked_cannot_generate_report: {
    text: "Output Stage 处于锁定状态：请先完成 ≥1 个 GRADE 评估，并使 PRISMA 2020 Checklist 完成度 ≥ 5 项。",
    action: "disable-generate",
  },
  rule_o5_no_grade_assessments: {
    text: "还没有任何 GRADE 评估行。请先到 GRADE 面板为至少 1 个结局完成评估。",
    action: "go-grade",
  },
  grade_locked_cannot_change_assessment: {
    text: "GRADE 评估已被锁定，无法修改。",
    action: "disable-generate",
  },
  rule_o1_prisma_lt_5_items_checked: {
    text: "PRISMA 2020 Checklist 完成度不足（≥ 5 项要求），请补充后再生成。",
    action: "go-prisma",
  },
  rule_o6_incomplete: {
    text: "报告引擎返回内容缺失，三格式至少有一项无效。请重试并联系技术支持。",
  },
  report_engine_generate_failed: {
    text: "报告生成失败（后端内部异常）。请重试。",
  },
} as const;
```

**兜底规则**：`errorDetail` 存在但不在上方白名单 → 显示「未知错误（detail = {detail}）」并用**红框**警告（防止将来后端加新 detail 时 UI 静默吞掉）。该兜底本身也是一个测试用例（P13）。

### 3.5 SHA 单一真相源不变量

```
不变量 I：
   onGenerate() 成功后，
   ReportGeneratorPanel 展示的 mdContent
   === GET /projects/{pid}/reports 返回数组中 id === generatedSnapshot.id 那一项的 md_content
   （由后端 get_or_create idempotent 保证；Controller 调 POST 后立刻把返回值作为 generatedSnapshot）

不变量 II：
   如果用户在 Editor 里 0 修改（generateFromUpstream 后不改动 textarea）→
   再次 POST /report/generate 得到的 sha256_grade 和 sha256_analysis 与快照完全一致（idempotent，不会生成新快照）
   → 这是 NOTOUCH-5 的核心证明：后端 hash 生成逻辑未改

不变量 III：
   ReportGeneratorPanel 显示的 sha256Grade、sha256Analysis
   === 后端返回字段的原字面值（不截断不转义）→ 仅在前端视觉上截断做 chip 显示
```

### 3.6 测试矩阵（15 Panel + 5 Frame = 20 vitest，F6 + F7）

**Panel（15）：**

| ID | 断言 |
|---|---|
| P1 | 默认 activeFormat=md → tab-md aria-selected=true；点击 tab-html → onFormatChange('html') 触发 |
| P2 | status=loading → 三内容区 aria-busy=true，三 Export 按钮 disabled，btn-generate disabled 并显示 spinner |
| P3 | status=error_422，detail=rule_o1_prisma_lt_5_items_checked → 横幅含中文文案 + badge 显示原 detail 字面值 |
| P4 | detail=rule_o5_no_grade_assessments → 文案正确且显示「前往 GRADE 面板」button（若父组件传 onGoGrade） |
| P5 | detail=output_stage_locked_cannot_generate_report → 按钮 btn-generate 强制 disabled（即使 onGenerate 存在） |
| P6 | detail=unknown_xxx（非白名单）→ 显示兜底红框 + 原字面值 detail 字符串全文 |
| P7 | mdContent 含 10,000 字长 Markdown → 外层 <pre> 出现滚动条但 Panel 总高不超过 max-height（不溢出卡片） |
| P8 | mdContent/htmlContent/txtContent 三者独立切换 Tab 时内容不串（state not shared） |
| P9 | sha256Grade = 64 个 a → chip 显示前 8 位 `a3f2918c…`，hover 时 title 属性为全 64 字 |
| P10 | sha256Grade = null → chip 显示灰底的「—」 |
| P11 | snapshotId=42 → 显示小 badge「快照 #42 已保存」可点击触发 onJump（若传入）|
| P12 | onGenerate 点击 1 次；loading 未完成前再次点击不会重复调用（内部防抖 500ms 或 useRef lock）|
| P13 | onExport {format=md} → 复用 ReportExportMenu3Formats → 触发一次 onExport({format:'md'}) |
| P14 | versionLabel 为空字符串时显示默认值 v0.1-draft |
| P15 | 无障碍：role=tablist aria-labelledby / aria-selected / aria-busy 正确（axe-core 可过） |

**Frame（5）：**

| ID | 断言 |
|---|---|
| H1 | srcDoc=null → `data-testid=preview-empty` 存在，iframe 不存在 |
| H2 | srcDoc 含 `<script src="https://cdn.tailwindcss.com/">` → iframe.sandbox 属性（字符串化）不含 `allow-scripts`；且组件内部过滤后无关键字 |
| H3 | srcDoc 含 `<script>alert(1)</script>` → sandbox 属性字符串化也不含 `allow-scripts` |
| H4 | 挂载后 onLoad 仅触发 1 次（即使后续 srcDoc prop 多次变化，非 null 时每个变化触发一次）|
| H5 | sandboxAllow=['allow-forms'] → 实际 iframe.sandbox 是 `"allow-forms"`；注入 'allow-scripts' 也被过滤掉 → sandbox 不含 `allow-scripts`（安全硬线测试） |

---

## 4. useReportEditorController（F4）

### 4.1 完整 Hook API（见设计四节 §4.1，略重复）

Hook 状态机内部（用 `useReducer` 写，避免多个 setState race condition）：

```
State = {
  draft: Report8ChaptersDraft | null;
  activeFormat: "md" | "html" | "txt";
  status: "idle" | "loading" | "ok" | "error_422";
  errorDetail: string | null;
  latestSnapshot: ReportSnapshot | null;     // GET /reports 拉回最新一条
  generatedSnapshot: ReportSnapshot | null;  // 最近一次 POST 返回
  generateBusy: boolean;                     // 防抖锁，防止重复 POST
}

Action =
  | { type: "SET_DRAFT"; next: Report8ChaptersDraft | null }
  | { type: "SET_FORMAT"; format: "md" | "html" | "txt" }
  | { type: "GENERATE_FROM_UPSTREAM"; input: UpstreamInput }
  | { type: "LOAD_LATEST_START" }
  | { type: "LOAD_LATEST_OK"; latest: ReportSnapshot | null }
  | { type: "GENERATE_START" }
  | { type: "GENERATE_OK"; snap: ReportSnapshot }
  | { type: "GENERATE_422"; detail: string }
  | { type: "GENERATE_ERROR"; detail: string }
  | { type: "RESET" };
```

### 4.2 五个暴露操作的行为契约

| 方法 | 参数 | 行为 | 对应测试（vitest 新文件，按习惯放 `__tests__/useReportEditorController.test.ts`，约 10 用例，不单独枚举） |
|---|---|---|---|
| generateFromUpstream | 无（从上游数据读取内部 upstreamData） | dispatch GENERATE_FROM_UPSTREAM；调用 `generateDraftFromUpstream(upstreamData)` 结果设 draft | — |
| restoreLatestSnapshot | Promise void | 1) 若 latestSnapshot 已存在且 id 未变 → 直接 parse + dispatch SET_DRAFT；2) 否则调 fetchClient.get('/projects/{pid}/reports')，取数组第 0 项；3) parseSnapshotInto8Chapters + 设置 source_snapshot_id = latest.id | — |
| generateReport | { versionLabel? } | 1) generateBusy=true 时立即 return；2) 组装 ReportGeneratePayload：version_label + 8 override_chN（仅章节 `trim().length > 0` 的才传空字符串也不传 → 命中 NOTOUCH-5「不传走 baseline」）；3) dispatch GENERATE_START → fetchClient.post('/projects/{pid}/report/generate', payload)；4) 422 抓异常 → GENERATE_422；5) 成功 → GENERATE_OK 并更新 generatedSnapshot | — |
| exportReport | format | 1) generatedSnapshot 无对应内容 → NOP；2) 使用 shared-ui 现有 `downloadBlob`（复用 ExportPanel 的工具函数，不重写）→ 生成 `meda_report_{pid}_v{version}_{YYYYMMDD}.{md/html/txt}` 文件名 | — |
| reset | 无 | dispatch RESET → draft=null, status=idle, errorDetail=null, generatedSnapshot=null | — |

### 4.3 computed Props 规则

- `editorProps.value = draft`；`onChange` 内部 wrap 成 SET_DRAFT
- `panelProps.mdContent = generatedSnapshot ? generatedSnapshot.md_content : null`；activeFormat/setFormat 透传；sha256Grade = generatedSnapshot?.sha256_grade；errorDetail/status/generateBusy → panelProps.status、onGenerate 透传
- `previewProps.srcDoc = generatedSnapshot ? generatedSnapshot.html_content : null`；activeFormat==='html' 时同步

`fetchClient` 默认为全局 fetch 包装（`JSON.stringify + headers:{'Content-Type':'application/json'}`），测试环境全部使用注入 Mock，避免 vitest 启动网络。

---

## 5. 后端 Additive 扩展（F10 + F11）

### 5.1 report_engine.py (F11)

**变更契约：**
- 原有签名 `def generate_report_three_formats(pi: ProjectReportInput) -> tuple[str, str, str]` 被**保留**并写为兼容重载；实际上第二个参数 `overrides: dict | None = None` 是 keyword-only optional（传 positional 也可以，但默认值是 None）→ 所有 8.3 调用点不传 override → 行为与 8.3 完全一致（字节级 MD/HTML/TXT 输出相同）
- 新增 3 个内部 helper（下划线前缀，export 不暴露）：
  - `_replace_section_body(md: str, headings: Tuple[str,str], body: str, plain=False) -> str`：找到指定章标题；替换**标题行下方**直到下一个 `^##? \d+[.、] ` 或 `^# ` 或 EOF 之间的所有内容为 body（可 strip 前后空行）；plain=True 用于 txt 纯文本格式
  - `_replace_section_body_html(html: str, headings: Tuple[str,str], body_md: str) -> str`：先把 body_md 转成 minimal HTML（粗体/列表/表格 md→html 简化版），然后找到 `<section id="ch{N}">` 的 innerHTML 整体替换；找不到对应 `<section>` 就不改
  - `_md_to_minimal_html(md_body: str) -> str`：最小必要的 md→html 实现（只支持 `**bold**`、`- list`、`## 子标题`、Markdown 表格）；**不引入外部库（零依赖）**

### 5.2 workspace.py POST /report/generate (F10)

仅在 `payload = payload or {}` 后、构建 `pi = ProjectReportInput(...)` 前，追加：

```python
_OVERRIDE_KEYS = (
    "override_ch1_background", "override_ch2_methods",
    "override_ch3_pico", "override_ch4_results",
    "override_ch5_grade_assessment", "override_ch6_summary_of_findings",
    "override_ch7_discussion", "override_ch8_appendices",
)
overrides_from_payload = {}
for k in _OVERRIDE_KEYS:
    v = payload.get(k)
    if isinstance(v, str) and v.strip():           # 非空字符串才覆盖；空串/None → SKIP (NOTOUCH-5)
        overrides_from_payload[k] = v
_overrides_arg = overrides_from_payload or None

# 原有行不变：
md, html, txt = generate_report_three_formats(pi, overrides=_overrides_arg)
```

空 payload → `_overrides_arg is None` → 报告引擎走 baseline。

### 5.3 Python 新增测试（4 test_report_engine + 2 test_rest_output + 1 search_worker）

- test_report_engine_ac6_ac7.py 追加 4 个新用例（**不修改原有 18 golden fixture 与断言**）：
  - `test_override_ch1_only` → 只有 override_ch1 传 → MD 中 ch1 正文等于传入内容、其他章与 baseline fixture 一致（断言整文件 MD 除 ch1 外字节级 == baseline）
  - `test_override_all_8_chapters` → 全 8 override → 每章正文分别匹配
  - `test_override_ch5_ch6_grade_and_sof` → 只覆盖 5 和 6
  - `test_empty_string_overrides_do_nothing` → 传 8 个空字符串 → 输出字节级等于 baseline（证明 NOTOUCH-5 安全）
- test_rest_output_w84_t4.py 追加 2 个：
  - `test_post_report_generate_with_overrides_roundtrip` → payload 带 override 字段，返回 md 对应章正文被替换；snapshot 记录也正确持久化
  - `test_post_report_generate_empty_overrides_equals_id` → payload override 全空串 / 不存在 → 返回快照 sha256_grade 与现有 golden 调用完全相同（idempotent + NOTOUCH-5 验证）
- test_search_worker.py **修复 1 个 + 新增 2 个（反证）**：
  - FIX：`test_one_source_failed_marks_run_partial_failed` → 通过（原 bug 修正）
  - NEW：`test_all_sources_success_marks_completed` → 全部成功 status=completed（反证不会把 completed 误标 partial_failed）
  - NEW：`test_two_sources_failed_marks_partial_failed` → 两个源失败 → status=partial_failed 且 run.errors 长度 =2（反证不只 catch 第一个错）

---

## 6. 回归修复（F12：search_worker.py）

### 6.1 失败根因假设（先反证验证）

- **H1（最可能）**：`_run_parallel` 中当 `len(results) == len(sources)` 就标记 completed，但实际 results 包含 `{ok:False}` 记录，应统计 success_count 而非总条数；成功阈值应为 `success_count == total_sources → completed`；否则（0 < success_count < total → partial_failed；success_count == 0 → failed）
- **H2**：run.status 赋值位置在 try 内而非 finally，异常提前 return → 没有写库 → 状态为 pending → 触发断言失败

### 6.2 修复范围（最小原则）

- 仅修改 `_run_parallel` / 或对应的结果聚合循环（精确定位需在 `pytest -k partial_failed --tb=long` 下读 traceback 确定，实现时 TDD 第一步先重跑失败用例读 stacktrace）
- 不改 models.py Run.status 字段、不改 REST 响应、不改 workspace.py
- 相关 search_query / workspace 相关 8.3 REST 测试全部保持 GREEN

---

## 7. 测试基线（目标）

| 层 | 当前（2026-08-18 实际运行结果） | 本 Spec 目标 | 备注 |
|---|---|---|---|
| Python pytest（排除网络/浏览器用例） | 346 passed（+ 99 passed W8.4专项 = 445） | **≥ 449 passed（期望 450）** | +4 report_engine + 2 rest + 2 search_worker（反证）— 1 失败（修复）= 净 +8 |
| TypeScript shared-ui vitest | 405 passed | **≥ 455 passed** | +20 Editor + 15 Panel + 5 Frame + 10 Controller Hook = +50 |
| **合计** | **751 passed** | **≥ 904 passed** | ≥ Wave 8.4 Plan 要求的 810 GREEN |

---

## 8. 验收 AC (Acceptance Criteria)

按 Hard-Gate 方式，以下 8 条必须全部成立：

1. **AC1**：Python 全量 `pytest` 排除网络/浏览器 → 至少 449 passed，0 failed（除 4 skipped）
2. **AC2**：`npx vitest run` → 至少 455 passed，0 failed
3. **AC3**：NOTOUCH-5 字节级验证 → 对 5 个受保护文件块计算 SHA256 与 Wave 8.3 final tag（wave-8-2b-final-green-tests-351）对应文件相等 → 无差异（如已 git tag 可直接 diff）
4. **AC4**：`generate_report_three_formats(pi)` **不传 overrides** 的输出字节级等于 Wave 8.3 同 pi fixture（本 spec §5.3 空串测试保证）
5. **AC5**：ReportContentEditor8 + ReportGeneratorPanel + HtmlPreviewFrame 3 组件能通过 `<OutputStageDashboard>` 父组件组装并跑通完整链路的 Happy Path 集成测试（vitest 提供的）：
   - generateFromUpstream → 8 textarea 有内容 → 修改 ch1 → POST /generate 成功 → Panel 三 Tab 有内容 → 切 HTML Tab → PreviewFrame 渲染 iframe
6. **AC6**：`parseSnapshotInto8Chapters(generate_report_three_formats(pi, overrides=all_8)[0])` 后得到的 8 章正文（忽略空字段）roundtrip 还原率 ≥ 99%
7. **AC7**：search_worker 回归：单源失败 → status=partial_failed + 错误列表非空；全成功 → completed；全失败 → failed（三情形测试）
8. **AC8**：零新增第三方依赖 → 检查 workspace root 三个 package.json / pyproject.toml / requirements.txt 的 dependencies block 无变化（除了本来就有的）

---

## 9. 实施优先级与子任务（供 writing-plans Skill 展开）

| 优先级 | 子任务 | 预估 |
|---|---|---|
| **P0-T1**（先测后写） | 重跑 search_worker 回归 → 确定 §6.1 的 H1/H2 → 用 TDD 先写 search_worker 的两个反证用例（全成功、双失败）→ 修复 bug → 绿 → 提交 | 小 |
| **P0-T2** | F9 shared-sdk → 新增 2 个 append-only 类型 → 单测 vitest 类型快照 | 小 |
| **P0-T3** | F11 report_engine.py → 新增 overrides 参数 + 3 helper + 4 pytest → 绿 | 中 |
| **P0-T4** | F10 workspace.py → 读 payload 8 override + 2 rest 测试 → 绿 | 中 |
| **P1-T5** | F1 + F5 → ReportContentEditor8 + 20 vitest → 绿 | 中 |
| **P1-T6** | F2 + F6 → ReportGeneratorPanel + 15 vitest → 绿 | 中 |
| **P1-T7** | F3 + F7 → HtmlPreviewFrame + 5 vitest → 绿 | 小 |
| **P1-T8** | F4 useReportEditorController + 10 vitest → 绿 | 中 |
| **P1-T9** | F8 shared-ui/index.ts → append 导出 + 运行 TypeScript 全量 `tsc --noEmit` | 小 |
| **P2-T10** | Happy Path 集成 vitest（父组件组装 F1+F2+F3+F4 + mock fetchClient）→ 绿 | 小 |
| **P2-T11** | 全量回归 → pytest + vitest 双绿 → git tag（如用户允许） | 小 |
