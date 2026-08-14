# Spec · Wave 8.2A · 导出三剑客 RIS + BibTeX + PRISMA 流程图

> **Status**: Draft → Spec written → Awaiting User Review → Plan
> **Author**: Wave 8 Brainstorming Skill
> **Date**: 2026-08-14
> **Target Users**: 临床医生 / 硕博做真实综述
> **Quality Bars (严格沿用 8.1B)**: 0 新增 pip/npm 依赖；pytest 默认 zero-network；每 Scope 10 AC checklist；vitest baseline ≥ 79 passed；agent-core pytest baseline ≥ 164 passed；6 端回归不破 8.1B 246 green tests；search_worker / adapter / pico 代码 0 行修改；任何 handler 永不抛 window.onerror 白屏。

---

## 1 · 架构设计

### 1.1 核心理念（3 条原则）
1. **P1 · Serializer 双端同构**：RIS/BibTeX 序列化 TS/PY 各一份纯函数（字符串拼接 zero IO），TS vitest snapshot + PY pytest filecmp 对比同一个 Golden Sample（`tests/fixtures/export/sample_3entries.{ris,bib}`）保证字节一致。
2. **P2 · PRISMA 浏览器端 SVG→PNG/SVG**：复用现有 [PrismaChart.tsx](file:///d:/workspace/MedA/packages/shared-ui/src/PrismaChart.tsx) 渲染的 `<svg id="prisma-chart">`，TS 端 `XMLSerializer` 出 SVG；`canvas 2d drawImage` + `toDataURL('image/png', 0.92)` 出 PNG 2× 抗锯齿；**零新增 npm/html2canvas/canvg/puppeteer**。
3. **P3 · 不写后端文件系统**：所有导出走 `URL.createObjectURL(new Blob([text], {mime}))` + `<a download> programmatic click`。backend 不新增 endpoint，复用已经存在的 records JSON 路由（WorkspaceShell 打开详情页时已拉到内存）。

### 1.2 三层架构图
```
Layer3 UI Export ──► serializeRIS/BibTeX ──► downloadBlob/<a download>
                  └─► exportPRISMA (svg→png+svg) ──► downloadDataUrl / Blob
                    ▲
                    │ GET 已有 records JSON (already in state)
Layer2 Backend ──► serialize_ris / serialize_bibtex PY pure funcs (pytest only)
                    ▲
Layer1 Data (existing) ──► LiteratureEntry / SearchRunRecord SQLite tables
```

### 1.3 与 8.1B Impact 0 保证
- 0 改 adapter/search_worker/protocol/pico
- 0 新 SQLModel 字段 / 0 改 DB schema（PRISMA n 数直接从已有的 prisma counts 现算）
- 0 新 pip/npm 包（RIS/BibTeX 手写 serializer；PNG 用原生 Canvas；BOM/BibTeX 转义表手写 18 个）

---

## 2 · 组件与边界（6 大 + 4 helper 纯函数）

### 2.1 文件位置全景
```
packages/shared-ui/src/export/       ← 新建子目录（4 纯函数 + 2 组件 + 2 导出器）
  serializeRIS.ts         → NormalizedLiteratureRow[] -> string (with UTF-8 BOM)
  serializeBibTeX.ts      → rows + citeKeyPrefix -> string (no BOM, ctex safe)
  exportPRISMA.ts         → svgRootEl -> Promise<{svgBlob, pngDataUrl}>
  ExportPanel.tsx         → 3 按钮挂到 SearchRunDetailScreen 顶部右侧
  sanitizeFilename.ts     → 纯函数 E5 文件名兜底
  truncateField.ts        → E2 字段截断（UTF-8 字节边界，尽量标点断）
  makeEmptyPrismaSvg.ts   → E1 0 records 生成有效 SVG（非空文件）
  downloadDiagnosticText.ts→ E6 终极兜底下载诊断 txt

apps/agent-core/app/services/literature/   ← 新建两个 PY 纯函数（pytest + CLI）
  serialize_ris.py      → list[UnifiedLiteratureEntry] -> str (对齐 TS Golden)
  serialize_bibtex.py   → 同上

packages/shared-sdk/src/client.ts   ← 可选：LiteratureExportOptions + LiteratureExportFormat (all optional)

apps/web + desktop WorkspaceShell  ← 3 prop handler 内联绑定（<SearchRunDetailScreen onX /> 4 行改）
```

### 2.2 签名与职责（SRP 单一职责）

#### TS serializeRIS(records, opts?) → string
- 必出 6 字段：TY / AU / TI / AB / PY / ER（其他可选有就写）
- TY 映射：JOUR（期刊）/ RPRT（Meta/系统评价）/ UNKN（兜底）；AU `; ` 分号分隔 >25 截 "et al."；TI Unicode 不转义直接写（中文 CJK 安全）
- AB 按 UTF-8 字节 6KB 上限截断 + 追加 `...[truncated]`（按句号边界）
- PY：非空数字 → `${year}/01/01`；year null/undefined → 空 `PY  - `（RIS 允许空字段）
- 默认 prepend BOM `\uFEFF` 给 Windows EndNote；risUtf8Bom=false 关

#### TS serializeBibTeX(records, citeKeyPrefix='meda') → string
- entry 类型：@article / @inproceedings / @misc（兜底）
- 18 LaTeX 特殊字符转义表手写（零 latex 包）：`& % # _ { } ~ \ ^ < > | " ' ``  → 对应的 \& \% 等；中文字符完全不转义（留给 \usepackage[UTF8]{ctex}）
- Citekey: `${prefix}_${source_key}_${doi/pid/idx}`，冲突时加 _dup1/_dup2
- 字段最少 7：title / author / journal / year / doi / abstract / note（note 写 pmid 或 fallback 其他 meta）
- 超长 abstract BibTeX 允许多行花括号自动折行（1KB 换行）

#### TS exportPRISMA(chartRoot) → Promise<{svgBlob, pngDataUrl}>
- `chartRoot` 找不到 / 不是 <svg> → 走 makeEmptyPrismaSvg + toast 提示
- SVG：加 XML 头 + DOCTYPE（Illustrator/Figma 兼容），blob type `image/svg+xml;charset=utf-8`
- PNG：`img.src = SVG Blob` + `onload` → 2x 抗锯齿 `quality=0.92` → 1500ms timeout + tainted CORS 失败时 toast 警告"已下载 SVG，PNG 因浏览器限制跳过"，但 SVG 已先下载绝不丢失

#### ExportPanel 3 按钮（UI 位置：SearchRunDetailScreen 现有 CSV 按钮右侧追加）
- `[导出 .ris]`、`[导出 .bib]`、`[导出 PRISMA 图]`
- disabled 条件：`run.status ∉ {completed, partial_failed}`（pending/running/cancelled/failed 全灰，tooltip 写原因）
- records=0 时：黄色描边 enabled 仍然可点（下载骨架诊断 + EMPTY_0_RECORDS_ 文件名前缀 + toast 提示"0 条记录，已下载占位诊断文件"）

### 2.3 4 个 Error-Handling 纯函数签名
```ts
sanitizeFilename(raw: string, fallback?: string): string      // E5
truncateField(value: unknown, maxBytes: number, suffix?: string): string  // E2
makeEmptyPrismaSvg(runId: number, reason: string): string      // E1
downloadDiagnosticText(stage: string, err: unknown, runId: number|null, extra?: Record<string,unknown>): void  // E6
```

---

## 3 · 数据流与下载时序（3 管线 + 4 步通用 fallback）

### 3.1 RIS 9 步（同步，无额外 HTTP）
1. status check（completed/partial_failed 否则 disabled）
2. rows = detail.records（WorkspaceShell openDetail 时已经在内存，0 网络）
3. rows==0 → EMPTY_0_RECORDS + skeleton 骨架
4. `serializeRIS(rows, opts)`
5. BOM prepend default on
6. sanitizeFilename(`meda_run${id}_${date}_n${rows.length}.ris`)
7. Blob(`application/x-research-info-systems`)
8. downloadBlob（createObjectURL + <a download>，1s 后 revoke 防泄漏）
9. onDone({format, bytes, count}) → 绿色 toast：`RIS 下载成功 ${n} 条`

### 3.2 BibTeX 9 步（同 RIS 同步）
同上仅 mime=`application/x-bibtex`（fallback text/plain;charset=utf-8）+ citeKeyPrefix 选项 + BOM 不写 + 18 LaTeX 转义。

### 3.3 PRISMA 11 步（唯一异步）
1~3. 同 status check + rows + records==0 → makeEmptyPrismaSvg
4. `document.getElementById('prisma-chart')` → null：自动 `scrollIntoView(smooth)` + toast 提示"请滚动到 PRISMA 图让它渲染好再下载"（不 throw，不崩溃）
5. XMLSerializer 拿 SVG string
6. 包装 XML 声明 + DOCTYPE
7. **先下载 SVG**（100% 成功保证）
8. 异步合成 PNG：scale 默认 2×（抗锯齿，3× 可选，1× 省带宽）
9. canvas / onload 失败 → toast 警告（SVG 已下），不中断
10. PNG 成功则下载 PNG（第二个文件）
11. onDone({svgBytes, pngOk})

### 3.4 WorkspaceShell 绑定
Props 扩展 3 条（全 optional，backward 兼容）：
```tsx
onExportSearchRunRis?: () => void;
onExportSearchRunBibTeX?: () => void;
onExportSearchRunPRISMA?: () => Promise<void>;
```
在 render `<SearchRunDetailScreen />` 透传，handlers 直接 import shared-ui/export 调 serialize + downloadBlob，**不用新 Context / 不用 Redux / 不用 QueryClient**。

### 3.5 缓存与 0 额外请求
所有导出数据点（RIS/BibTeX records、PRISMA counts、SVG DOM）都来自已经拉好的 `searchRunDetail` state 和 DOM，**0 额外 HTTP**。1000 用户并发导出 = 0 backend QPS。

---

## 4 · 错误处理矩阵（6 大类 × 3 管线全兜底）

> 总原则 S1~S4：S1 永不白屏/throw；S2 Unicode CJK/emoji 100% 保留；S3 0 records 绝对不是 0 字节空文件；S4 任何导出失败至少 clipboard / 诊断 txt 两种兜底之一。

| # | 类别 | RIS 动作 | BibTeX | PRISMA | 保证 |
|---|---|---|---|---|---|
| E1 | 0 条 records | TY-UNKN 骨架 + `EMPTY_0_RECORDS_` 文件名前缀 + 写 `N1  - 本次检索 0 条 运行 ID XXXX` | `@misc{meda_empty_0_records_YYYYMMDD, title={{MEDA EXPORT 0 条}}, note="...诊断"}` | makeEmptyPrismaSvg 4 格写 0 + `<desc>` 写原因 | S3 非空文件 |
| E2 | 字段缺失/Unicode 异常（year 前 / CJK emoji、abstract 64KB 超长、坏 doi） | TY UNKN、空 PY 行、UTF-8 字节 truncate 标点断边界、坏 doi → N1 字段 | @misc 兜底、18 LaTeX 转义、多行花括号折 abstract | n=0 按真实空处理、SVG label 写空串安全 | S2 Unicode 安全 S1 不 throw |
| E3 | Blob / createObjectURL 老浏览器抛罕见 | fallback data:text/plain base64 downloadDataUrl；再失败 → `navigator.clipboard.writeText(risString)` + toast 复制成功 | 同 RIS | Blob 失败 clipboard 写 SVG raw 字符串 | S1 永保用户拿到内容 |
| E4 | PRISMA PNG 专属（img.onerror / canvas tainted CORS / 1500ms timeout） | — | — | toast 警告「**已下载 SVG 矢量，PNG 跳过（浏览器限制）**」绝不 0 文件，onDone pngOk=false | SVG 成功优先，PNG 是可选增强 |
| E5 | 文件名 Windows 保留字符 / MAX_PATH 260 超限 / 末尾空格/点 | sanitizeFilename 替换保留字为 `_`，200 字符截，末尾空格点清，空结果 fallback `meda_export.ris` | 同 RIS | SVG/PNG 同 sanitize | Windows 资源管理器 0 冲突 |
| E6 | ExportPanel onClick 最外层终极兜底（任何未分类异常：serialize 抛 / download 抛内部） | 红色 toast（80 字符 err.message 切片）+ 下载 `meda_run${id}_RIS_ERROR_DIAGNOSTIC.txt` 内容包含 JSON.stringify(err.stack 前 500 + runId + nRecords + extra) | 同 RIS BibTeX 诊断版 | 同 PRISMA 诊断版 | S1 绝对无 window.onerror 白屏 |

---

## 5 · 测试策略 + 10 条 Acceptance Criteria

### 5.1 测试金字塔 5 层（≈ 30+ 新 Tests）
```
L1 Pure Functions (12 tests = TS 8 + PY 4): sanitize/truncate/makeEmpty/downloadDiag
L2 Golden Diff (6 tests = TS 3 snapshot + PY 3 filecmp sample_3entries 字节对字节对齐)
L3 React Smoke ExportPanel (4 tests vitest jsdom): disabled rules / records=0 黄色 / click handlers 调用 / PRISMA null svg toast
L4 (Optional) needs_browser 标记 默认 skip 大文件 200 条 (4 tests)
L5 6-End Regression (1 次总跑): vitest 79+6 + pytest 164+12 + tsc triple 0 errors
```

### 5.2 新增文件清单（TS + PY 双端对称）
```
PY: app/services/literature/serialize_ris.py / serialize_bibtex.py
    tests/test_export_serialize_ris_bibtex_py.py (6 tests)
    tests/fixtures/export/sample_3entries.{ris,bib,json}
TS: shared-ui/src/export/*.ts + *.tsx（8 files）
    shared-ui/src/__tests__/{export-serializers.test.ts, ExportPanel.smoke.test.tsx}（12 tests）
```

### 5.3 8 Tasks Subagent-Driven TDD 拆分（每 Task 独立回滚独立 commit）
| T | 内容 | 新 Tests |
|---|---|---|
| T1 | L1 4 纯函数（TS sanitize/truncate/makeEmpty/downloadDiag + PY）→ 12 tests | 12 |
| T2 | TS RIS/BibTeX 序列化（shared-ui） → L2 3 snapshot pass | 3 |
| T3 | PY RIS/BibTeX 序列化 → 字节对齐 T2 Golden → L2 3 filecmp pass | 3 |
| T4 | ExportPanel 3 按钮组件 + L3 4 smoke tests green | 4 |
| T5 | PRISMA SVG/PNG 导出 + canvas tainted fallback → L? 2 tests | 2 |
| T6 | apps/web + desktop WorkspaceShell 透传 3 prop handlers → 无状态 smoke 2 tests | 2 |
| T7 | (可选) needs_browser playwright 默认 skip → 200 records 大文件 4 tests（0 新增 npm playwright，仅结构级 needs_browser 标记） | 4 |
| T8 | 主线程 6 端回归 + 10 AC 打勾 + commit final | 0 |

### 5.4 10 条 Acceptance Criteria Checklist（交付后逐个打勾）
| # | 描述 | 验证方法 | ☐ |
|---|---|---|---|
| ① | apps/shared-sdk + apps/web + apps/desktop **三端 tsc triple 0 our-code errors**（electron/@types 第三方冲突忽略） | 三端 tsc --noEmit | ☐ |
| ② | **Vitest 5 端 ≥ 85 passed**（shared-sdk 27 + shared-ui 41+6new + admin 1 + web 5 + desktop 5 = 85，超基线 79） | vitest run 5 端各一次 | ☐ |
| ③ | **agent-core Pytest ≥ 176 passed**（8.1B baseline 164 + 约 12 new），needs_network 默认 skip（addopts + hook 双保险） | pytest --ignore test_search_worker | ☐ |
| ④ | **L2 Golden 字节对齐：TS RIS/BibTeX = PY RIS/BibTeX = fixture Golden 文件 diff=0**（同一 3 条 records 输入） | vitest snapshot toMatchFileSnapshot + pytest filecmp | ☐ |
| ⑤ | **E1 0 records：RIS/BibTeX/PRISMA 3 个文件非空**，文件名含 `EMPTY_0_RECORDS_` 前缀，内容含诊断 runId + 原因 | ExportPanel smoke × 0 records | ☐ |
| ⑥ | **E2 Unicode + 转义安全：CJK 标题 `二甲双胍 SGLT2i 联合 💊 + %#_ 特符` → RIS CJK 原样 + BibTeX `\%\#\_` 18 字符全转义，RIS 首字节 BOM = EF BB BF** | 3 CJK records Golden L2 | ☐ |
| ⑦ | **PRISMA SVG 永远先下成功；monkeypatch canvas.toDataURL 抛 SecurityError（模拟 CORS tainted）时：SVG Blob 下载成功 + toast 警告 + 不抛异常** | jsdom monkeypatch HTMLCanvasElement.prototype.toDataURL | ☐ |
| ⑧ | **sanitizeFilename 9 条用例全通过**（保留字符 / ctrl / 超长 300 / 末尾空格点 / 空串 fallback 等）→ 返回合法 1-200 文件名 | 8/9 sanitize 单元 tests | ☐ |
| ⑨ | **E6 终极兜底：monkeypatch serializeRIS 抛 TypeError** → ExportPanel onClick 触发后：红色 toast 80 字出现 + 诊断 DIAGNOSTIC.txt 文件下载成功 + window.onerror 0 触发 + 不白屏 | jsdom addEventListener error | ☐ |
| ⑩ | **运行时 Impact 0：现有 CSV 导出按钮功能正常；8.1B 246 green tests 全部保留 ≥ 246；git diff --name-only 不含 services/sources/*（adapter）、services/search_worker.py、services/pico.py 3 类路径** | git diff + T8 回归 | ☐ |

---

## 6 · 自审记录（4 项 Spec BS6 Checklist）
✅ **占位符扫描**：无任何 "TBD"/"TODO"/"待定" 字眼。所有字段名文件位置都是明确真实路径（已经实际存在的 client.ts / PrismaChart.tsx / WorkspaceShell.tsx 引用全部有效，不是幻想）。
✅ **内部一致性**：架构节 P3 不写磁盘，数据流 3 条管线全走 Blob/<a download>，错误处理 E3 兜底 dataUrl/clipboard，完全和 P3 一致，无矛盾。
✅ **范围检查**：严格 Scope = RIS + BibTeX + PRISMA 三导出，不含 Dedupe/筛选（留给 8.2B），不含 SourceConfig UI（留给 8.2C），不含本地 PDF 上传（留给 Wave 9），边界清晰。
✅ **歧义检查**：所有默认值显式写（risUtf8Bom=true, citeKeyPrefix='meda', pngScale=2, quality=0.92, 200 chars 文件名上限，6KB UTF-8 截断）→ 实现时无"到底要不要做？"的二义性。
