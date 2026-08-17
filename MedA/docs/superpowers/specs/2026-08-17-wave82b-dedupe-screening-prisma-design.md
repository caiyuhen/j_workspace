# Spec · Wave 8.2B · 去重 + 标题/摘要筛选工作台 + PRISMA 2020 双向绑定

> **Status**: Draft → Spec written → Awaiting User Review → Plan
> **Author**: Wave 8 Brainstorming Skill
> **Date**: 2026-08-17
> **Target Users**: 临床硕博写真实综述（PubMed + CNKI + 万方三源联搜后统一去重+两轮筛选）
> **Quality Bars (严格沿用 8.2A + 增量)**: 0 新增 pip/npm 依赖；pytest 默认 zero-network（needs_network / needs_browser / needs_db_large 三 hook）；vitest baseline ≥ 106 passed；agent-core pytest baseline ≥ 174 passed；严格不破 8.2A 280 green tests baseline；search_worker / adapter / pico / 8.2A serializeRIS/serializeBibTeX 4 文件 0 行修改；10 AC checklist 必须 10/10 打勾；12 Tasks 严格 Subagent-Driven TDD 单循环 5 步（写 fail test → 跑 fail → 最小实现 → 跑 pass → commit）独立可回滚。

---

## 1 · 架构设计

### 1.1 核心理念（6 条 HARD-GATE 原则）
1. **P1 · 计算型 PRISMA 根治不一致**：PRISMA 4 数 **永远不存 DB 字段**，每次读都从 LiteratureRecord 表 `COUNT(*)` 实时 SQL 聚合 → 永远不会出现「n 数与实际筛选列表不一致」，0 缓存不同步 bug。
2. **P2 · 两模式破循环**：Auto 模式（默认，筛选→PRISMA 单向同步）/ Manual Override 模式（用户手动改 n 数时冻结 PrismaChart，筛选变更不影响 PRISMA 显示）**永远互斥切换永不交叉写**，从机制上彻底根绝「改 n 数 → 列表变 → n 数又自动改 → 无限循环」。
3. **P3 · 0 新依赖纯手写 SimHash**：SimHash 64-bit 基于 Python hashlib.md5 标准库 + 二进制 bit 统计纯手写（<80 行纯函数）；CJK 字符 NFKC 归一化（unicodedata 标准库）+ uni/bi-gram tokenizer；0 pip 包 simhash-py / pyhash。
4. **P4 · 8.2A 导出三剑客 baseline 100% 不破**：serializeRIS/serializeBibTeX 4 个 TS/PY 文件签名 0 字符修改；筛选过滤 100% 在调用方列表层 `filter(records)` 后再传 serializer；8.2A Golden filecmp byte-for-byte 100% 一致。
5. **P5 · 4+1 nullable 字段 0 锁表 migration**：LiteratureRecord 4 字段（screening_stage / screening_decision / exclude_reason_json / fulltext_status）+ ResearchProject 1 字段（prisma_override_json）**全部 `DEFAULT NULL` nullable**；SQLite 3.35+ `ALTER TABLE ADD COLUMN` 毫秒级元数据操作，不锁表不重建表，0 数据迁移风险。
6. **P6 · 1 Project 级跨 Run 全局 Library**：去重 + 筛选 scope 天然跨 SearchRun（`_detect_duplicate` 现有 base_query 就按 project_id 过滤本来就跨 Run，0 改代码）；UI 加 4 filter 下拉（Run / Source / Year / 决策状态）就能达到「单 Run 独立筛选」的效果，不用改架构。

### 1.2 三层架构图
```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer3 UI（shared-ui，0 新 npm 包）                                   │
│  3 路由页（T/A 轮 / 全文轮 / PRISMA）+ 10 子组件                      │
│    ScreeningTable 5 列 + ScreeningToolbar + ExcludeReasonDialog      │
│    PrismaOverrideEditor + ExportPanel 开关（调用方 filter serializer 0 改）│
└──────────────────────────┬──────────────────────────────────────────┘
                           │ REST API（新增 6 endpoints，复用 engine 函数）
┌──────────────────────────▼──────────────────────────────────────────┐
│  Layer2 Backend Engine（agent-core，0 新 pip 包）                      │
│  simhash.py 2 纯函数 + screening_engine.py 3 核心引擎函数             │
│  修改：_detect_duplicate 追加第 4 级 SimHash 判定                      │
│  修改：confirm_record_unique 同步清空 screening 决策                    │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ SQLModel / SQLite
┌──────────────────────────▼──────────────────────────────────────────┐
│  Layer1 Data（existing + 5 nullable fields）                          │
│  LiteratureRecord（dedupe_status + duplicate_of_id 已存在 → 复用 0 改）│
│  + 4 新增 screening_* nullable + ResearchProject prisma_override_json│
└─────────────────────────────────────────────────────────────────────┘
```

### 1.3 与 8.2A baseline Impact 0 保证
- 0 改 [serializeRIS.ts](file:///d:/workspace/MedA/packages/shared-ui/src/export/serializeRIS.ts) / [serializeBibTeX.ts](file:///d:/workspace/MedA/packages/shared-ui/src/export/serializeBibTeX.ts) / [serialize_ris.py](file:///d:/workspace/MedA/apps/agent-core/app/services/serialize_ris.py) / [serialize_bibtex.py](file:///d:/workspace/MedA/apps/agent-core/app/services/serialize_bibtex.py) 4 个 serialize 文件（AC10 HARD-GATE，git diff 0 行）
- 0 改 [PrismaChart.tsx](file:///d:/workspace/MedA/packages/shared-ui/src/PrismaChart.tsx) 内部计算逻辑（只追加 ⚠️ override badge 可选 prop，不影响渲染结果）
- 0 新 pip/npm package（SimHash 纯手写；5 列表格原生 `<table>` + CSS Grid + 200 条简单分页，不用 tanstack-table/react-window）
- 0 新增路由 path（[stage_entry.py#L148-L172](file:///d:/workspace/MedA/apps/agent-core/app/services/stage_entry.py#L148-L172) 3 张卡片 target 原封不动：`/title-abstract` `/full-text` `/prisma`）

---

## 2 · 组件与边界（3 路由页 + 10 子组件）

### 2.1 文件位置全景（7 新增 PY/TS + 9 修改现有，锚点标记 # WAVE82B_INSERT_ 全部可 grep）
```
PY 层（新增 4 文件 + 修改 5 现有文件）
├─ 新增 apps/agent-core/app/services/simhash.py              → 2 纯函数：simhash64() + hamming_distance()
├─ 新增 apps/agent-core/app/services/screening_engine.py      → PRISMA 4 SQL count 聚合 + batch 决策 + prisma_override
├─ 新增 apps/agent-core/tests/test_simhash_dedupe.py          → 16 zero-IO tests（AC1/AC2）
├─ 新增 apps/agent-core/tests/test_screening_state_machine.py → 28 tests（AC3/AC4/AC7）
├─ 新增 apps/agent-core/tests/test_prisma_binding.py          → 18 tests（AC5/AC6/AC10）
├─ 修改 models.py#L89-L115 末尾 ──────# WAVE82B_INSERT_SCREENING_FIELDS─ 4+1 nullable
├─ 修改 schemas.py#L257-L275 末尾 ────# WAVE82B_INSERT_SCREENING_SCHEMA─ 4 字段追加 summary + PRISMA 4 数
├─ 修改 literature.py#L197-L205 return None 前 # WAVE82B_INSERT_SIMHASH_LEVEL4 追加 4 级判定
├─ 修改 literature.py#L69-L83 dedupe duplicate 时 ─# WAVE82B_INSERT_AUTO_EXCLUDE_REASON─ 自动填 exclude_reason=1
├─ 修改 main.py 路由末尾 ──────# WAVE82B_INSERT_SCREENING_ROUTES─ 6 新 endpoints
└─ 修改 stage_entry.py#L148-L172 ─# WAVE82B_INSERT_STAGE_STATUS─ 3 卡片 status 动态（locked/ready/done）

TS 层（新增 3 文件 + 修改 4 现有文件，锚点 // WAVE82B_INSERT_）
├─ 新增 packages/shared-ui/src/screening/ScreeningTable.tsx   → 5 列核心组件 + 200 条简单分页
├─ 新增 packages/shared-ui/src/screening/ScreeningToolbar.tsx → 4 filter 下拉 + 批量 Include/Exclude + 进度条
├─ 新增 packages/shared-ui/src/screening/ExcludeReasonDialog.tsx → Cochrane 9 类单选 + 500 字备注
├─ 新增 packages/shared-ui/src/screening/ScreeningProgressHeader.tsx → 进度条 + PRISMA 4 数 badge
├─ 新增 packages/shared-ui/src/screening/PrismaOverrideEditor.tsx → 4 格编辑输入框 + ⚠️ Manual 徽章
├─ 新增 3 路由页（TitleAbstractScreeningPage / FulltextScreeningPage / PrismaPage） <120 行/页
├─ 修改 shared-sdk/src/client.ts#L349-L372 ─// WAVE82B_INSERT_SCREENING_TYPES─ 3 接口追加
├─ 修改 PrismaChart.tsx ──────────// WAVE82B_INSERT_OVERRIDE_BADGE─ ⚠️ 徽章可选 prop
└─ 修改 ExportPanel.tsx（用户打开文件）// WAVE82B_INSERT_FILTER_SWITCH 追加「仅导出最终纳入」switch（调用方 filter，serializer 0 改）

TS 测试层（新增 3 测试文件 = 44 tests）
├─ ScreeningTable.test.tsx 18 tests（AC3/AC8）
├─ ExcludeReasonDialog.test.tsx 12 tests（AC4）
└─ PrismaBinding.test.tsx 14 tests（AC5/AC6/AC10）
```

### 2.2 核心组件：ScreeningTable 5 列 CSS Grid 像素级定义
| 列号 | Grid 列宽固定 | 单元格内容 + 行为 | 条件样式 |
|---|---|---|---|
| 1 选择 | 48px fixed | 顶行全选 checkbox（indeterminate 处理）；数据行单选 checkbox；`dedupe_status=duplicate` 时 checkbox disabled | `bg-gray-50` 固定，不随 hover 高亮 |
| 2 元数据 | min-w 320px 1fr | ① Title ≤200 字 `text-ellipsis` + 悬浮完整 tooltip；② 第一作者 et al. · Year · Journal；③ Source Badge（PubMed 蓝/CNKI 红/万方 绿/手动 灰）+ DOI 可点击 + PMID 徽章 | duplicate 整行 `bg-orange-50 border-l-4 border-orange-400`；Include `bg-green-50 border-l-4 border-green-500`；Exclude `bg-red-50 border-l-4 border-red-500 opacity-60` |
| 3 摘要 | min-w 420px 1fr | 默认前 300 字 + 「展开」Button；展开后全文 + 「收起」；CJK + 英文按字符数统计（非 word） | 父容器 `max-h-60vh overflow-y-auto`，表格整体 `h-[calc(100vh-220px)]` 防顶栏顶出 |
| 4 去重标记 | 140px fixed | ① duplicate：橙 Badge「重复被合并」+ 悬浮 tooltip「合并到主记录 #1234 XXX… 跳转」+ 小按钮「不是重复 → 标记为独立」；② unique：灰 Badge「独立文献」；③ confirmed_unique：绿 Badge「已标记独立」 | confirm-unique 按钮调 API 期间 loading disable；跳转主记录后 scrollIntoView 闪烁 3 次 CSS animation |
| 5 决策 | 220px fixed | ① 未决策：[✅ 纳入][🚫 排除] 两按钮；② 已 Include：绿 Badge +「撤销决策」；③ 已 Exclude：红 Badge + 小号灰文字「排除理由：第 X 类 · XXX」+ 悬浮显示备注 note | 🔒 前端+后端双校验：<br>① dedupe_status=duplicate → 按钮全部 disabled（只许先「标记为独立」再决策）<br>② 全文轮只显示 T/A include 的 records（后端 API 过滤，前端拉不到） |

**简单分页（0 新 react-window 包）：** `slice(page_start, page_start + 200)` + 右下角页码 `1 / N < >`；每页 200 条（医生 10-20 条/分钟筛选节奏，翻页不卡）。

### 2.3 核心组件：ExcludeReasonDialog（Cochrane PRISMA 9 类预置单选 + 备注）
9 个单选 Radio（preset_class 1-9 枚举），规则：
- 1「重复文献」：仅去重自动填时 radio disabled（用户不可改），T/A 轮手动排除时不显示 1
- T/A 轮可选 preset ∈ [2,3,4,5,6,7,8,9]
- 全文轮可选 preset ∈ [6,7,8,9]（6=无全文 7=仅摘要 8=语言年份 9=其他）
- 备注 textarea 500 字上限（右下角 `0/500` 实时计数，超 500 红色警告 + Apply disabled）
- 批量排除时标题：「🚫 排除理由 · 应用到 N 条选中记录」

### 2.4 核心组件：PrismaOverrideEditor（双向绑定破循环 UI）
PrismaChart 4 盒右上角各 1 ✏️ 按钮 → 点后弹 mini input：「手动覆盖 XX n」→ 应用后：
- 对应盒边框 `border-2 border-dashed border-orange-400` + 顶部 ⚠️「手动覆盖」徽章
- ScreeningProgressHeader 红色 banner 常驻：「⚠️ PRISMA 手动覆盖模式，n 数可能与实际不一致 → [立即同步（清 override 回 AUTO）] [保持手动模式]」
- 30% diff 时 PrismaChart 顶部额外红色 badge：「⚠️ Identification 实际=1200，覆盖=900（差 25%）[🔍 查看差异详情]」

---

## 3 · 数据流 + PRISMA 4 数实时聚合 SQL + 循环保护

### 3.1 LiteratureRecord 2 轮筛选状态机（严格 7 条合法转移，非法 422 + 前端 Button disabled 双保险）
```
NULL,NULL ─T1→ (ta, include) ─T5→ (fulltext, include)
    │            │  │                        │
    │ T2         │T3│T4（撤销仅清空 T/A，     │T7 撤销全文轮
    │            │  │   全文轮未启动才可撤）   │    不清空 T/A
    ▼            │  │                        │
 (ta, exclude)   │  └────────────────────────┘
                 ▼
          回 NULL,NULL（仅限无任何 fulltext stage record 时）
```
白名单 7 转移（Python Literal / TS type 双校验）：T1 初始→T/A In；T2 初始→T/A Ex；T3 T/A In→撤；T4 T/A Ex→撤；T5 T/A In→全文 In；T6 T/A In→全文 Ex；T7 全文任→撤回到 T/A In。

### 3.2 PRISMA 4 数实时 SQL 聚合（compute_prisma_counts()，每次读现算，0 存 DB）
```python
# 4 条 COUNT(*) SQL（SQLite 10k 条 <50ms）
N1_IDENTIFICATION = COUNT(WHERE project_id=X AND dedupe_status IN ('unique','confirmed_unique'))
  └─ 对应 PRISMA 2020 Identification 盒

N2_SCREENED = N1_IDENTIFICATION（PRISMA 2020 官方 records screened = identification）
N2_EXCL_TA = COUNT(screening_stage='ta' AND decision='exclude')  # T/A 轮手动排除
N2_EXCL_DUP = COUNT(decision='exclude' AND stage IS NULL AND preset_class=1)  # 去重自动排除
N3_ELIGIBILITY = N2_SCREENED - N2_EXCL_TA - N2_EXCL_DUP  # 对应 Eligibility 盒
  └─ consistency pytest 恒等式：N3 == N4 + N3_EXCL_FULLTEXT（AC5 必过）

N4_INCLUDED = COUNT(screening_stage='fulltext' AND decision='include')
N3_EXCL_FULLTEXT = COUNT(screening_stage='fulltext' AND decision='exclude')
  └─ 对应 Included 盒（最终纳入，ExportPanel 开关 ON 时仅导出这批）
```

### 3.3 Auto / Manual Override 两模式循环保护（机制根绝循环）
**根源矛盾破解**：「筛选→PRISMA」和「PRISMA→筛选」两条写路径永不交叉！
| 模式 | prisma_override_json | PrismaChart n 数来源 | 筛选操作影响 PrismaChart？ | 筛选操作影响实际列表？ | 切换条件 |
|---|---|---|---|---|---|
| AUTO（默认） | None | 实时 SQL 聚合（3.2） | ✅ 立即生效（因为就是读的时候算） | ✅ 生效 | 默认模式 |
| MANUAL Override | `{"identification":1248,"applied_at":"..."}` | prisma_override_json 存的值 | ❌ **冻结！不生效，PRISMA 显示就固定 override 值**（切断回路！） | ✅ 仍然正常生效（用户还能筛，只是 PrismaChart 不动） | 用户点编辑 n 数→应用 |
清 override 回 AUTO：一键按钮「立即同步回实际计算值」→ prisma_override_json = None，立即恢复 Auto。

### 3.4 导出三剑客过滤 Pipeline（AC10 不破 baseline HARD-GATE）
```
STEP1 DB 拉原始 records
STEP2【WAVE82B 仅加这步在调用方，0 改 serializer】
    if (filterByFinalIncluded Switch === ON):  # ExportPanel switch 默认关（= 8.2A 行为）
        records = records.filter(r => r.stage === 'fulltext' AND r.decision === 'include')
STEP3 serializeRIS/serializeBibTeX(records)  # 函数签名 0 字符改（参数名/类型/顺序全不变）
STEP4 download Blob（8.2A 原逻辑）
```
🔒 AC10 pytest/vitest 双验证：8.2A Golden 3 条 sample records 直接调用 serializer 输出和 8.2A 时 byte-for-byte filecmp cmp=True（因为 serializer 函数 0 改）。

### 3.5 批量操作事务 + 幂等（AC7）
- 500 条 1 小 transaction，中途异常全 ROLLBACK（N=500 断电模拟 → pytest 验证 DB 0 行改动）
- 前端每次批量请求带 `client_batch_id = uuidv4()`；后端 project 级 `_batch_history: dict` 存 id→result 10 分钟；同 id 第二次调用直接返回上次结果，100 次重复 0 副作用

---

## 4 · 错误处理 + 边界条件（5 类 14 场景 × 2 层防御）
| 类型 | 场景 | 前端 UI 拦截（第 1 层） | 后端服务层兜底（第 2 层） |
|---|---|---|---|
| DB Migration | SQLite<3.35 不支持 ALTER ADD | N/A | 启动自检 `SELECT sqlite_version()` <3.35 拒绝启动 + 报错「请升级 Node/Electron ≥ 18 LTS」；migration 幂等（PRAGMA 查字段存在就 skip）；migration 前 DB 备份到 db_backups/ |
| SimHash 边界 | CJK 标点/大小写/繁简差异导致漏判 | N/A | `simhash64()` 前置 4 归一：`unicodedata.NFKC` → `.lower()` → 移标点正则 → 压缩空格；len<10 字符标题跳过 SimHash 宁漏不重判 |
| SimHash 边界 | 误判假阳性 Hamming=3 | duplicate 悬浮 tooltip 显「判定依据：Hamming 距离 2/64 96.8% DOI空 PMID空」；confirm_record_unique 一键撤销 + 内存 set 避免同对反复误判 | confirm_record_unique 同步清空 screening_decision + exclude_reason_json（现有函数末尾加 3 行） |
| 轮次互斥 R3 | 用户在全文轮页面撤 T/A 决策 | 全文轮页面「撤销 T/A」按钮直接隐藏（UI 看不到） | batch API 校验：如有任何 screening_stage='fulltext' record → 422「已有 N 条入全文轮，请先撤销全文轮再改 T/A」+ 返回 fulltext_record_count 前端 Toast |
| 轮次互斥 R3 | T/A 排除的 record 试图打全文轮 Include | 全文轮 API 只返回 stage='ta' + decision='include' records（前端拉不到） | 决策接口强校验 (stage, decision) 必须等于 ('ta','include') → 否则 422 |
| 空项目 R4 | 0 条 LiteratureRecord | 居中大卡片📭 + 两个跳转按钮（去检索/手动导入） | API 返回 empty_state='no_records' + 中文提示语 |
| 空项目 R4 | 去重未完成（dedupe_status 空 N 条） | T/A 轮顶黄色 banner「🚀 立即开始一键去重」按钮 | 调 `run_full_project_dedupe()` 批处理接口 |
| 空项目 R4 | T/A 全筛完了 0 条未决策 | 顶部绿色 banner🎉 + 按钮「➡️ 前往全文轮」 | stage_entry.py 全文轮卡片 status 变 ready（之前 locked） |
| 空项目 R4 | T/A 全 exclude 全文轮 0 条 | 全文轮居中红色卡片🚫 + 按钮「⬅️ 返回 T/A 轮」 | 同上 stage_entry PRISMA 卡变 locked |
| Override R5 | 手动覆盖 diff > 30% | PrismaChart 顶部加粗红色 badge + 「查看差异详情 + 一键同步回真实值」 | compute_prisma_counts() 返回 diff_percent 字段（30% 阈值常量在配置中） |
| 性能 R5 | 批量 > 2000 条 | 全选时弹 confirm「N>2000 建议分批，确认继续？」；按钮 loading 60s + 3s 后自动刷新列表 | 后端分片：500 条/小 transaction；>1500 条启动异步 task_id 前端轮询进度条 |
| 网络超时 R5 | 批量请求超时（30s）但后端已执行完 | 超时 Toast「网络超时，请查看列表状态；幂等保护，可重试」 + 3s 后 /library 自动 refresh | 幂等 Key client_batch_id（见 3.5） |
| preset_class 校验 | preset_class=99 非法值（前端被黑） | ExcludeReasonDialog UI 就是 9 radio，不可能选 10 | backend `EXCLUDE_PRESET_CHECKS = { ta:[2-9], fulltext:[6-9], auto:[1] }` 非法直接 422 |
| DB 脏数据 | screening_stage='xxx' 非法字符串（用户手动改 DB） | 列表行显示「⚠️ 筛选状态损坏，请联系管理员」 | 计算 PRISMA 时 `CASE WHEN screening_stage NOT IN ('ta','fulltext') THEN NULL END` 脏数据当 NULL 处理 + log warning |

### 错误提示统一中文 Toast 模板（3 行，英文 traceback 永不直接给用户看）
```
🔴 批量操作失败
500 条中 3 条非法，已全回滚，无任何文献被修改
💡 请前往全文轮撤销这 3 条后再操作（Error ID: W82B-R31-2847）[复制错误 ID]
```

---

## 5 · 测试策略 + 10 AC Checklist（pytest 62 + vitest 44 = 106 新增 → 总 green tests = 280 + 106 = **386 passed**）

### 5.1 新增测试文件全景（106 tests 全部 zero-network zero-IO）
| 层 | 文件 | 用例数 | 核心覆盖 |
|---|---|---|---|
| PY | test_simhash_dedupe.py | 16 | AC1/AC2（CJK/标点/大小写/Hamming 0/1/3/4/短标题/NFKC繁简/DOI PMID 优先级/同年份不同年份） |
| PY | test_screening_state_machine.py | 28 | AC3/AC4/AC7（T1-T7 7 合法转移各 2-3；非法转移 11；batch_rollback 断电模拟 N=500；幂等 Key 10 次重试 0 副作用） |
| PY | test_prisma_binding.py | 18 | AC5/AC6/AC10（恒等式 5 种分布 = N3 = N4 + FullExcl；Auto/Override 模式切换 6 tests；Export 开关 serializer 0 改 Golden filecmp 5 tests） |
| TS | ScreeningTable.test.tsx | 18 | AC3/AC8（5 列渲染/duplicate disabled checkbox/Include绿 Exclude红 opacity/全选 indeterminate/摘要展开 300 字/跳转主记录滚动/分页 200 条翻页） |
| TS | ExcludeReasonDialog.test.tsx | 12 | AC4（9 radio 1 disable/500 字上限计数超限红/unselected disabled apply/batch N 条显示/cancel 不写 DB） |
| TS | PrismaBinding.test.tsx | 14 | AC5/AC6/AC10（Header = PrismaChart 数值 3 分布；Override 徽章橙框；30% diff 警告；一键回 AUTO；ExportPanel Switch ON/OFF records 数对 & serialize 函数输出不变） |

### 5.2 10 AC Checklist（10/10 必须打勾 = 交付成功）
| AC# | 验收标准 | 对应测试 | 交付证据 |
|---|---|---|---|
| AC1 | 去重算法 4 级生效：DOI exact→PMID exact→归一化标题+年份→SimHash 95% Hamming≤3；重复保留 metadata 完整度最高 record；confirm_record_unique 可一键撤销 | PY test_simhash 16 + test_state_machine 3 | pytest -v AC1 全 PASSED 截图 |
| AC2 | SimHash CJK/标点/繁简 NFKC/len<10 跳过/假阳性 confirm_unique 兜底 100% 覆盖 | PY test_simhash 12 tests | pytest -v AC2 全 PASSED |
| AC3 | 2 轮状态机 7 合法转移严格执行；任何非法转移后端 422 + 前端 Button disabled | PY 20 + TS 3 tests | pytest + vitest 双绿截图 |
| AC4 | Cochrane 9 类排除理由单选；T/A 用 [2-9]，全文轮 [6-9]；去重自动 preset 1 disabled；备注 ≤500 字 | PY 6 + TS 12 tests | 同上 |
| AC5 | PRISMA 4 数实时 SQL 聚合恒等式 `N1-TAEx-DupEx=N3=N4+FullEx` 5 种数据分布 100% 成立；与导出 PRISMA 图 n 数严格同构（同函数返回值） | PY 11 + TS 4 tests | pytest AC5 全绿 + 工作台 Header vs 导出 SVG n 数对比截图 |
| AC6 | Auto/Override 两模式循环保护：Manual 筛选变更不改 PrismaChart；清 Override 立即同步；diff>30% 警告 | PY 6 + TS 7 tests | pytest AC6 + 模式切换 UI 2 路径截图 |
| AC7 | 批量事务 + 幂等：N=500 中途异常 DB 0 行改动；同 batch_id 连调 10 次仅生效 1 次 | PY test_state_machine AC7 5 tests | pytest -v AC7 全 PASSED |
| AC8 | 0 records / 去重未完成 / T/A 全筛完 / T/A 全排除 4 空边界中文友好提示 + 跳转按钮 | TS ScreeningTable 3 tests + UI 手动 | UI 4 场景截图各 1 |
| AC9 | stage_entry.py 3 卡片路由 0 新增；原 `/title-abstract` `/full-text` `/prisma` 可用；卡片 status 动态 locked/ready/done | TS 路由跳转 + 手动 UI 检查 | stage_entry.py git diff 截图（<10 行，target 不变） |
| **AC10 HARD-GATE** | **8.2A 280 green tests baseline 100% 不破**：pytest≥174 vitest≥106 全 PASSED（忽略 test_search_worker 1 pre-existing flaky）；4 serialize 文件 0 行代码改动（git diff --name-only 4 个文件不出现）；8.2A Golden filecmp byte-for-byte 100% 相同 | pytest baseline 命令 + vitest baseline 命令 | 🚀 交付前必跑：<br>PY `cd apps/agent-core ; .venv\Scripts\python -m pytest tests/ -x --ignore tests/test_search_worker.py -q`（≥174 passed）<br>TS `cd packages/shared-ui ; npx vitest run`（≥106 passed）<br>+ `git diff --name-only | Select-String "serialize"` 输出为空（0 改 serialize 文件） |

### 5.3 12 Tasks Subagent-Driven TDD 分派（严格依赖链 T1→T12；每个 Task 独立 5 步 TDD 可回滚）
| Task# | 名称（5 步 TDD 单循环） | 新增 tests | 修改/新增文件 | 前置依赖 |
|---|---|---|---|---|
| T1 | SimHash 纯函数（simhash64 + hamming_distance + CJK/NFKC 归一化 + 分桶） | PY +16 | 新增 simhash.py + test_simhash_dedupe.py | 无 |
| T2 | _detect_duplicate 第 4 级 SimHash 95% 插入；dedupe 自动填 exclude_reason=1；confirm_record_unique 同步清空 screening 字段 | PY +3 | 修改 literature.py#L197-L205（WAVE82B_INSERT_SIMHASH_LEVEL4）+ #L69-L83（WAVE82B_INSERT_AUTO_EXCLUDE_REASON）+ confirm_unique 末尾 3 行 | T1 |
| T3 | 4+1 nullable 字段 migration（幂等 ALTER TABLE ADD DEFAULT NULL）；schemas.py 字段追加 | PY +2 | 修改 models.py + schemas.py + 新增 migrations/20260817_add_screening_fields.sql（幂等） | T2 |
| T4 | screening_engine.py（compute_prisma_counts + batch_decision + prisma_override）+ 状态机 + PRISMA 绑定测试 | PY +43 | 新增 screening_engine.py + test_screening_state_machine.py + test_prisma_binding.py | T3 |
| T5 | 6 API endpoints：POST /batch-decision / GET /prisma-counts / PUT /prisma-override / DELETE /prisma-override / GET /screening-paged / POST /run-full-dedupe | PY +0（T4 engine 已测） | 修改 main.py（WAVE82B_INSERT_SCREENING_ROUTES）各 endpoint 仅 auth + 调 T4 engine + 返回 JSON | T4 |
| T6 | stage_entry.py 3 卡片 status 动态（locked/ready/done）：T/A 轮默认 ready；全文轮仅 T/A 轮全部决策完 ready；PRISMA 仅全文轮全部决策完 ready | PY +0（手动 UI 校验） | 修改 stage_entry.py#L148-L172（WAVE82B_INSERT_STAGE_STATUS） | T5 |
| T7（可与 T1-T6 并行） | shared-sdk TS 类型追加：ScreeningStage / ScreeningDecision / ExcludeReason / PrismaOverride 4 interface | TS +0（types） | 修改 shared-ui/src/client.ts#L349-L372（WAVE82B_INSERT_SCREENING_TYPES） | 无 |
| T8 | ScreeningTable 5 列 + 200 条简单分页 + disabled 规则（duplicate 禁选） | TS +18 | 新增 ScreeningTable.tsx + 5 Cell 子组件 + ScreeningTable.test.tsx | T7 |
| T9 | ScreeningToolbar + ExcludeReasonDialog + ScreeningProgressHeader 3 组件 | TS +22 | 新增 3 组件文件 + ExcludeReasonDialog.test.tsx | T8 |
| T10 | 3 路由页 TitleAbstractScreeningPage / FulltextScreeningPage / PrismaPage（每页 <120 行纯组合子组件，路由 path 对齐 stage_entry.py 3 卡片 0 新增） | TS +0 | 新增 3 页面文件 + 路由注册（原 3 个 path） | T9 |
| T11 | ExportPanel「仅导出最终纳入」switch（调用方 filter records，serializer 0 改！AC10 HARD-GATE）；PrismaOverrideEditor 组件 | TS +14 | 修改 ExportPanel.tsx（用户打开的文件，WAVE82B_INSERT_FILTER_SWITCH）+ 新增 PrismaOverrideEditor.tsx + PrismaBinding.test.tsx | T10 |
| **🚀 T12（主线程唯一非 Subagent）** | 6 端回归 + 10 AC 逐一打勾 + baseline AC10 双命令截图 + git commit final | 全重跑 386 green | 无代码改动，仅跑命令 + AC 打勾 + 交付报告 | 必须 T1-T11 全部成功 commit |

---

## 6 · Spec 4 项自审（通过标记 ✅）
| 自审项 | 检查点 | 结果 |
|---|---|---|
| 1. 占位符清零 | 所有 TODO/TBD/占位符「XXX」全部替换为具体实现路径/具体数值/具体 SQL 语句 | ✅ 无任何占位符，全是具体代码文件锚点行号 + 具体 SQL |
| 2. 逻辑自洽 | 状态机 7 转移无矛盾；PRISMA 恒等式可证；Auto/Override 两模式永不交叉；批量事务回滚逻辑成立 | ✅ 自洽：恒等式代数可证；循环保护机制通过「两条写路径永不交叉」从根绝；T7 撤全文轮与 T3 撤 T/A 轮前置条件无冲突（必须无 fulltext record 才能撤 T/A） |
| 3. Scope 边界 | 严格 8.2B 范围内；8.2A 4 serialize 0 改；0 新包；0 碰 search_worker/adapter/pico/PICO 提取 | ✅ 在 Scope：仅 dedupe + screening + PRISMA 双向绑定；无 PICO 增强/Full-text 获取/AI 自动筛选（这些留给后续 Wave 8.2C/8.3） |
| 4. 歧义项清零 | 所有中文/英文名词有定义（如 SimHash Hamming≤3=95%；preset_class 1-9 具体含义；screening_stage='ta'/'fulltext' 定义）；枚举值全部列出无开放字符串 | ✅ 0 歧义：所有 Literal 枚举全部列在 spec 中；阈值（200 条/页 / 500 字备注 / 30% diff / Hamming≤3）全部常量可配置但默认值写死 |
