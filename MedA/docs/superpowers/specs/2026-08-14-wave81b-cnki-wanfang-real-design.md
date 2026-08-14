# Wave 8.1B · CNKI + 万方真抓取落地（Approach 2 · 词典翻译 + 轻 Schema 扩字段）
- 关联 Wave：Wave 8.1 Scope B（Wave 8.1A = PubMed Demo, 216 tests ✅, baseline 137 passed agent-core）
- 设计日期：2026-08-14
- 审批状态：5 节 Architecture / Schema / Data Flow / Tests / Error Handling 全部通过

---

## 1. Goal / Non-Goal

### Goal
1. 让 Workspace 三源 selected_sources = [pubmed, cnki, wanfang] 时，**CNKI / 万方 adapter 真抓 scholar.cnki.net + s.wanfangdata.com.cn 公开检索 HTML 页，解析出 ≥1 条文献**（默认 prefer_real 模式）。
2. **断网 / 封 IP / 验证码 / 解析失败** 时 100% fallback 注入数据 3 条，不会崩（search_worker 零 panic）。
3. **6 preset Workspace 一键卡** 的 CNKI / 万方检索词能从英文 PubMed boolean_text 中译得到（词级专业词典 20~30 条 + PubMed 标签清洗，AND/OR/NOT 结构保留），不需要手工维护双布尔式。
4. **pytest 零外网默认基线不破**：默认 `uv run pytest tests/` 不碰任何真实外网（needs_network 标记自动 skip），总 agent-core ≥ 145 passed 默认 / ≥ 150 passed 显式真跑。
5. 为后续 Workspace Source Config UI 扩「深度翻页 1-3 页」开关 **预留 shared-sdk schema 字段**，不需要二次 backfill shared-sdk types。

### Non-Goal（Scope 外，后续 Wave 做）
1. ❌ 做中文 BM25 分词 / jieba 集成（Scope B 不优化 BM25 精度，中文文献按现有近似打分即可）。
2. ❌ 手工维护 6 preset 的中文布尔式双字段（留给 Wave 9.x 中文检索精修时再做 Approach 3）。
3. ❌ 做滑块验证码自动过/模拟登录（Scope B 仅抓公开检索第一页，登录/滑块→fallback，不引入 selenium / playwright UI 自动化）。
4. ❌ UA 轮换模块（单 UA Chrome 126 + 同源 Referer 足够覆盖 1 页 20 条 × 3 queries 的风控）。
5. ❌ Source Config UI 翻页深度开关（仅 shared-sdk schema 预留字段 + 后端 clamp，UI 留到 Scope C/E2E 或 Wave 9.x）。

---

## 2. 关键决策（4 clarifying questions 已落地）
| Decision | 选择 | 理由 |
|---|---|---|
| 布尔式翻译策略 | 方案 B：词级 20~30 专业词词典翻译 + PubMed 标签清洗 | 不扩 preset schema 双布尔式字段，零手工维护；TS/PY consistency gate 不改 |
| 翻页深度策略 | 方案 ③：shared-sdk schema 扩 `max_pages_cn?: 1\|2\|3`，默认=1 | 留 UI 扩展位；当前 Scope B 仅第一页 20 条，保证通过率最高 |
| needs_network 默认运行 | 默认 skip + `--runneedsnetwork` 自定义 cmdline flag | 零外网基线不破；有网时一条命令全跑 150 tests |
| UA / Referer 策略 | 单 UA Chrome 126（Windows x64）+ 目标站同源 Referer | 和现有 cnki/wanfang adapter 已实现 100% 一致，零新模块 |

---

## 3. Architecture（目录变更清单 & 模块边界）

### 3.1 新增文件（共 9 个）
```
apps/agent-core/
├── app/services/sources/_cn_dict.py                # 20~30 专业词对 + translate_boolean_for_cn_source() 纯函数
├── tests/fixtures/
│   ├── cnki_20hits.html                            # scholar.cnki.net 第一页 20 条结果（现场抓+脱敏）
│   ├── cnki_0hits.html                             # 知网 0 hits 空页
│   ├── cnki_captcha.html                           # 知网「请完成滑动验证」HTML 片段
│   ├── wanfang_20hits.html                         # 万方第一页 20 条结果
│   ├── wanfang_0hits.html                          # 万方 0 hits
│   └── wanfang_login.html                          # 万方「请登录后查看」弹窗 HTML
├── tests/test_dict_translate_cn.py                 # 5 tests 纯函数
└── tests/test_cnki_wanfang_parse_html.py           # 6 tests bs4 本地 fixture 解析
```

### 3.2 编辑文件（共 6 个）
| 文件 | 改什么 | 不改什么 |
|---|---|---|
| `packages/shared-sdk/src/client.ts` | `NormalizedSearchQuery` 末尾加 `max_pages_cn?: 1 \| 2 \| 3` 可选字段 | `mapNormalizedSearchQuery()` 完全保留（可选字段 undefined 安全） |
| `packages/shared-sdk/src/utils/demoSeedings.ts` | `ensureDemoProjectAndQuery()` 构造 NormalizedSearchQuery payload 时显式传 `max_pages_cn=1` | 其他幂等/匹配逻辑不改 |
| `apps/agent-core/app/services/sources/protocol.py` | `NormalizedSearchQuery` Pydantic 类加 `max_pages_cn: Optional[Literal[1,2,3]] = None` | BaseModel 其他字段不动 |
| `apps/agent-core/app/services/sources/cnki_adapter.py` | `run_search()` 开头加 `translate_boolean_for_cn_source(bt, 'cnki')`；翻页 clamp `max(1, min(3, query.max_pages_cn or 1))` | `_build_url` / `_parse_html` 核心 Selector 不改（必要时现场修 fixture） |
| `apps/agent-core/app/services/sources/wanfang_adapter.py` | 同上，`source='wanfang'` | 同 cnki，核心 Selector 不改 |
| `apps/agent-core/tests/conftest.py` | 加 `pytest_addoption` + `pytest_collection_modifyitems`，自动 skip needs_network 当没传 `--runneedsnetwork` | `_zero_network_mode` autouse monkeypatch force_mock 保留（needs_network 才 pop） |

### 3.3 不改文件（Scope 锁死）
- ❌ `packages/shared-sdk/src/presets.ts` / `DEMO_PRESETS_PY`（schema 不扩 `boolean_text_cn`）
- ❌ `tests/test_presets_consistency.py`（原 gate 正则 100% 继续生效）
- ❌ `apps/agent-core/app/services/search_worker.py`、`bm25_scoring.py`、`pico.py`（三源汇总逻辑 0 改动）
- ❌ `apps/agent-core/app/models.py` / DB schema（LiteratureRecord / LiteraturePico 不变）
- ❌ `apps/web/src/App.tsx` / `apps/desktop/src/App.tsx` / shared-ui 组件（UI 0 改，因为 SearchRunSourceSummary 双字段兼容已经在 Wave 8.1A 完成）

---

## 4. Schema Changes（类型定义）

### 4.1 TS shared-sdk NormalizedSearchQuery
```ts
export type NormalizedSearchQuery = {
  boolean_text: string;
  pico?: SearchQueryPicoInput;
  filters?: SearchQueryFiltersInput;
  grouped_terms?: SearchTermGroupSummary[];
  expression?: SearchQueryExpressionBlock[];
  /** CNKI / 万方翻页深度：1=仅1页20条；最大3；undefined 等价于 1（后端默认） */
  max_pages_cn?: 1 | 2 | 3;
};
```

### 4.2 PY agent-core protocol.py NormalizedSearchQuery
```python
from typing import Literal, Optional

class NormalizedSearchQuery(BaseModel):
    boolean_text: str
    pico: dict[str, Any] | None = None
    filters: dict[str, Any] | None = None
    grouped_terms: list[Any] | None = None
    expression: list[Any] | None = None
    # Scope B 新增，默认 None = 行为等价于 1
    max_pages_cn: Optional[Literal[1, 2, 3]] = None
```

### 4.3 Impact 检查：8 处引用 0 改
| 引用位置 | 说明 |
|---|---|
| `client.ts mapNormalizedSearchQuery` | 可选字段 undefined 安全 |
| `apps/web/App.tsx handleCreateSearchRun` | 未传 max_pages_cn → undefined |
| `apps/desktop/App.tsx handleCreateSearchRun` | 同上 |
| `shared-ui SearchQueryBuilderScreen saveVersion` | 同上 |
| `apps/web/App.test.tsx mock saveSearchQueryVersion` | 不对 payload 精确 assert |
| `pubmed_adapter.py` | 不访问此字段（忽略）|
| `tests/test_search_adapters.py` 构造 | 默认 None 通过 |
| `demoSeedings.ts ensureDemoProjectAndQuery` | **唯一显式传 1 的位置**（本节 3.2 已定义） |

---

## 5. Data Flow（全链路时序）

### 5.1 从 Workspace 紫色一键卡到 PRISMA 入库
```
WorkspaceOneClickPubmedDemo.handlePresetClick
 │
 ├─① ensureDemoProjectAndQuery(client, session, preset)
 │    └─ NormalizedSearchQuery payload.max_pages_cn = 1（仅种子工具传）
 │
 ├─② client.createSearchRun(project_id, { sources, querySnapshot })
 │    └─ HTTP POST /api/projects/{pid}/search-runs
 │         └─ backend search_worker.dispatch(selected_sources)
 │              │
 │              ├── PubMedAdapter.run_search()   (Wave 8.1A 已经跑通, 0 改)
 │              ├── CNKIAdapter.run_search()     (本 Scope B 改入口)
 │              └── WanFangAdapter.run_search()  (本 Scope B 改入口)
 │
 └─③ onRunCreated(run_id, project_id) → handleOpenSearchRunDetail(pid, rid)（双参兼容签名）
```

### 5.2 CNKIAdapter.run_search() 内部细拆
```
run_search(query, ctx):
  ① mode = _resolve_mode()  → prefer_real / force_mock / force_real
  ② if force_mock → return AdapterResult(records=INJECTED_CNKI_3, hits=3, w=["force_mock"])
  ③ cn_bt = translate_boolean_for_cn_source(query.boolean_text, source="cnki")
       (try/except 包裹；任何异常→返回英文原 boolean_text + warning append)
  ④ N = max(1, min(3, query.max_pages_cn or 1))   # clamp [1,3]
  ⑤ merged = []; captcha_hit = False; last_http_ok = True
  ⑥ for p in 1..N:
       a. url = _build_url(cn_bt, page=p)
       b. try: resp = httpx.AsyncClient().get(url, headers=CHROME_126_HEADERS_CNKI, timeout=10)
       c. except httpx.ConnectError/Timeout/HTTPStatusError → warning += [f"page{p} fetch fail: {type}"]; break
       d. html = resp.text
       e. if _is_captcha_html(html) → warning += [f"captcha on page {p}"]; captcha_hit = True; break
       f. if _is_login_required_html(html) → warning += ["login_required on page {p}"]; break
       g. records = _parse_html(html, "cnki")
       h. hits_count_from_page = _extract_hits_count(html) or 0
       i. merged.extend(records)
  ⑦ merged_dedup = dedupe_by_source_record_id(merged)
  ⑧ if len(merged_dedup) == 0 and mode == prefer_real:
        warning += ["fallback injected dataset (抓 0 + prefer_real)"]
        return AdapterResult(hits=3, records=INJECTED_CNKI_3, warnings=warning)
  ⑨ final_hits = max(len(merged_dedup), hits_count_from_page)
  ⑩ return AdapterResult(hits=final_hits, records=merged_dedup, warnings=warning)
```

### 5.3 WanFang 同构替换
- URL template 替换（万方 `q=` 参数 + `pageNum=` + `pageSize=20`）
- HTML Selector 替换（万方 `class=list-item` / 知网 `class=result-item`）
- 登录/验证码 pattern 不同但逻辑一致

---

## 6. Tests 矩阵 & 断言边界（13 new tests）

### 6.1 总数基线
- **Baseline Wave 8.1A**：137 passed（3 deselected needs_network = pubmed 2 + cnki/wanfang 1 合并？——实际是 test_needs_network_cnki_wanfang 旧 1 条 + test_needs_network_pubmed 1 条 → 合计 3）
- **Scope B 新增**：
  - test_dict_translate_cn.py = 5 tests
  - test_cnki_wanfang_parse_html.py = 6 tests
  - test_needs_network_cnki_wanfang.py 从 1 test 扩到 2 tests（cnki 3 queries + wanfang 3 queries 合并成 1 test × 2？不，分 2 个 test 好定位失败）
- **总**：137 + 5 + 6 + (2 new needs_network - 1 old) = 137+12 = **149 collected + 1 pubmed needs_network = 150 collected**
  - 默认跑（无 `--runneedsnetwork`）：needs_network 3 tests 全部自动 skip → **145 passed + 5 skipped**。

### 6.2 每个 Test 详细断言
见 `节 4/5 Tests 策略` 4.2 表格（每个 test 断言已写，这里不重复）。

### 6.3 HTML Fixture 获取 & 脱敏流程
1. 开临时 powershell：`$env:MEDA_PUBMED_MODE='prefer_real'`
2. 单跑 `uv run pytest tests/ -k needs_network --runneedsnetwork -m needs_network --collect-only` 确认能 import
3. 用 `httpx` 直接 GET scholar.cnki.net + s.wanfangdata.com.cn 公开 URL（6 preset 中译第一条），保存 raw response 到 `C:\tmp\brainstorm\`
4. 手动过一遍：用 `re.sub` 去掉所有 `csrf-token` / `<script>` 内非必要全局变量 / Set-Cookie（如果 HTML body 里有）
5. 写入 `tests/fixtures/*.html` 并同步校验 `_parse_html()` 能解析 20 条；如果 selector 失效，现场修 selector + fixture

---

## 7. Error Handling & Fallback 矩阵（7 类失败）
见 `节 5/5 Error Handling` 5.1 表格（prefer_real/force_real/force_mock × E1~E7 全部列清楚，这里不重复）。

### 7.1 关键新增自定义异常（仅 force_real 模式 raise）
- `class AdapterCaptchaError(Exception)`：页中含验证码且 page=1 无已解析记录
- `class AdapterLoginRequiredError(Exception)`：登录弹窗且 page=1 无已解析记录
- `class AdapterParseError(Exception)`：hits_count ≥ 1 但 bs4 parse 返回 0（selector 失效）

prefer_real 模式 **永不 raise** → 全部 fallback injected 3 条 + warning 追加，search_worker 0 panic。

---

## 8. Acceptance Criteria（验收 = 10 条 checklist）
- [ ] ① shared-sdk tsc 0 errors（NormalizedSearchQuery.max_pages_cn 加完，apps/web tsc 0，apps/desktop tsc 0 triple 检查）
- [ ] ② agent-core `uv run pytest tests/`（无 flag）：145 passed + 5 skipped needs_network，0 failed（零外网基线不破）
- [ ] ③ `uv run pytest tests/test_dict_translate_cn.py tests/test_cnki_wanfang_parse_html.py -v`：11/11 passed
- [ ] ④ `uv run pytest tests/ --runneedsnetwork -m needs_network -v`（**有网环境手动跑**）：5/5 needs_network tests（pubmed 1 + cnki 2 + wanfang 2？—— 按 6.1 总数为 pubmed 3 ？按实际 needs_network mark 数量，只要全绿就行）all passed
- [ ] ⑤ 有网环境 真跑 demo_pubmed_end2end.py 的三源版本（新写 `demo_cnki_wanfang_end2end.py`？—— 不，Scope B 不新增 CLI Demo，复用 scripts/demo_pubmed_end2end.py 中 `query.selected_sources=["pubmed","cnki","wanfang"]` 手动传参数）→ PRISMA identification ≥ 14 (3+3+真 PubMed + 真 CNKI + 真 WanFang)
- [ ] ⑥ 断网环境（拔网线 or Windows 防火墙拦外网）→ `uv run pytest tests/` 仍然 145 passed 无异常（fallback injected 正确触发）
- [ ] ⑦ 7 类失败模式 pytest fixture 覆盖：ConnectError / 403 / 502 / timeout / captcha / login / parse_0_hit 全 7 类 prefer_real 下均返回 `len(records)==3 + fallback_mode=True in warning`
- [ ] ⑧ max_pages_cn=4 or 0 传参 → Python 端 clamp 到 [1,3] 且 warning += ["clamped from 4 to 3"]
- [ ] ⑨ 词典 KeyError / re.error → translate_boolean_for_cn_source 正常返回原文（英文 boolean_text 原样，警告追加），不会中断主流程
- [ ] ⑩ `uv run pytest tests/ -k "not needs_network" --forked`（解决 test_pico_service flaky DB isolation）：145 passed 全绿（3 flaky 用 --forked 隔离彻底消失）

---

## 9. Success Metrics（完成后指标）
- **Agent-core pytest 默认**：≥ 145 passed（150 collected，5 skipped needs_network），≥ 137 baseline 显著超。
- **TS 6 端 tsc**：shared-sdk / shared-ui / apps/web / apps/desktop / apps/admin 全 0 errors。
- **真跑通过率**：单 UA 1 页 20 条 × 3 queries × 2 源，抓 1 次 ≥ 60% pages 成功（不成功的自动 fallback 不影响 overall）。
- **总测试 Wave 8.1B**：总 tests 数 = 216 (Wave 8.1A 全端) + (5 + 6) 新增 pytest 默认跑 = **≥ 227 passed 默认**（不包含 needs_network skipped）。

---

## 10. Risks & Mitigations
| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| 知网/万方 selector 现场改结构 → parse_html 6 tests 失败 | 中 | 中（needs_network 2 tests 也会挂）| fixture 现场 HTML 抓完立刻校验 selector，fail 就改 `_parse_html` 到全绿再继续 |
| 抓 scholar.cnki.net 被临时封 IP 403（真跑时）| 低 | 低（prefer_real fallback）| 单 UA + 1 page + 1.5s 间隔；CI 中 --runneedsnetwork 只在本地有网环境手动跑，不阻塞 merge |
| max_pages_cn 改 shared-sdk 类型后 8 处引用有遗漏 tsc error | 低 | 低（都加了可选）| 跑 4 次 triple tsc：shared-sdk + shared-ui + web + desktop；有 fail 1 分钟能修（加 ? / 默认 undefined）|
| TERM_DICT 专业词覆盖不足 → 中文布尔式翻译不地道 → CNKI 抓 0 hits → fallback injected | 中 | 低（失败 fallback 仍过）| 现场看真跑 CNKI results 数，低于 10 就补 10 条词对（比如 `ASCVD / eGFR / DPP-4i / GLP-1RA / uACR / NT-proBNP / KCCQ / EMPA-REG OUTCOME / CANVAS / DECLARE-TIMI 58` 10 条经典），0 schema 改 |
| test_pico_service flaky DB isolation 没解决 → 全跑还是 3 failed | 中 | 低（非 Scope B 引入）| 接受 baseline 已经有的 flaky；用 `--forked` + `-p no:cacheprovider` + 单独跑 test_pico 全 3/3 证明不是 Scope B 的锅，同时 checklist 第 ⑩ 条用 `--forked` 145 passed |
