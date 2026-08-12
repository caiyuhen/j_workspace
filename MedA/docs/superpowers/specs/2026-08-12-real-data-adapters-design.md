# MedA Spec：真实数据 Adapter 落地（PubMed XML 真解析 + CNKI/万方 Web 抓取 + 双轨 fallback）

- Date: 2026-08-12
- Scope scope_label: Post-Wave 8 数据真实性补齐
- Status: Draft awaiting review
- Related docs:
  - 2026-08-11-meda-r004-closeout-wave-8-design.md（Wave 8 文献检索完整设计）
  - 2026-08-11-meda-r004-closeout-wave-8.md（Implementation Plan）

## 1. 背景与目标

Wave 8 R004 收口实现中三数据源成熟度不一致：
| Source | Wave 8 状态 | 真实数据需求 |
|---|---|---|
| PubMed | esearch 真 HTTP，efetch 拿 XML 后 `return []`（占位） | 必须补上 XML→UnifiedLiteratureEntry 解析，完成真数据闭环 |
| CNKI | Stub Adapter（INJECTED_DATASET 注入，无即 warning） | 对接公开学术搜索页 HTML 解析 |
| 万方 | Stub Adapter（INJECTED_DATASET 注入，无即 warning） | 对接 s.wanfangdata.com.cn 公开检索 HTML 解析 |

**目标**：
1. PubMed 完整真数据链路（esearch→efetch→XML parse→dedup→BM25→PICO）
2. CNKI/万方 优先真实 Web 抓取，网络/被封 fallback INJECTED_DATASET（不挂全流程）
3. pytest 默认零外网（force_mock），CI 125 passed 保障不回归；新增 `@pytest.mark.needs_network` 手动执行
4. 模式三级控制（env → ctx.per_source → ctx.global_mode），前端、离线演示、CI 都可切

**非目标**（本次不做，留后续 Wave）：
- 不做 CNKI/万方 机构账号/APP Key 官方 API（拿到凭证后再对接）
- 不做 MeSH 主题词提取、关键词聚合（会存 meta_json 预留字段）
- 不做离线缓存表（Wave 8.5 方案三如有需要再落表）

## 2. 架构总览：双轨模式 Adapter

```
用户创建 SearchRun
  └─> SearchRunService.create  → SearchRunWorker._worker_tick_once
         └─> registry[source_key].run_search(query, ctx)
                ├─ PubMedAdapter
                │     ├─ resolve_mode(ctx) -> prefer_real / force_mock / force_real
                │     ├─ force_mock ? → 直接走 monkeypatch 的 _esearch/_efetch（INJECTED_DATASET 等价路径，测试专用）
                │     ├─ prefer_real: _esearch_pubmed_ids HTTP → _efetch_parse_entries XML parse → try 解析成功
                │     │     ├─ XML parse OK → records = UnifiedLiteratureEntry[]
                │     │     └─ XML parse FAIL → if force_real: raise / prefer_real: 空 records + warning("XML parse failed, 0 returned")
                │     └─ force_real 失败直接抛 → worker 标 source=failed
                │
                ├─ CnkiAdapter（WanfangAdapter 同构）
                │     ├─ resolve_mode(ctx)
                │     ├─ force_mock → INJECTED_DATASET 直接返回
                │     ├─ prefer_real
                │     │     ├─ httpx GET scholar.cnki.net/search?q=... (UA, Referer, 2.5~4s jitter)
                │     │     ├─ 200 + html 无"验证码/安全验证"？
                │     │     │     ├─ YES → bs4 parse list items → records[]
                │     │     │     │         ├─ len(records) > 0 → return records + warning("抓取公开页成功 N")
                │     │     │     │         └─ len(records) == 0 → 触发 fallback 到 INJECTED_DATASET
                │     │     │     └─ NO (403/CAPTCHA) → 触发 fallback
                │     │     └─ httpx 抛异常 (timeout/connect) → fallback
                │     └─ force_real → 任一步失败直接抛，不 fallback
```

## 3. 数据模型 / Protocol 变更

### 3.1 SearchRunContext 扩字段（[protocol.py](file:///d:/workspace/MedA/apps/agent-core/app/services/sources/protocol.py)）
```python
@dataclass
class SearchRunContext:
    ...  # 已有 pubmed_api_key / rate_limit_rps / project_id / search_run_id
    adapter_modes: dict[str, Literal["prefer_real", "force_mock", "force_real"]] = field(default_factory=dict)
```
不需要新 SQL 表，因为 mode 是 runtime 参数，不持久化。

### 3.2 新增 pyproject.toml 依赖
```toml
dependencies = [
  ...
  "beautifulsoup4>=4.12.0",
]
```
仅新增 beautifulsoup4（html.parser 后端，不引 lxml），整体 agent-core 依赖轻量可控。

## 4. 节 1 PubMed XML 解析器（用户已通过）

### 4.1 接口签名
```python
# pubmed_adapter.py（已存在的 _efetch_parse_entries，从占位改为真实）
async def _efetch_parse_entries(pmids: Iterable[str], chunk: int = 500) -> list[UnifiedLiteratureEntry]:
    ids = list(pmids)
    if not ids:
        return []
    out: list[UnifiedLiteratureEntry] = []
    for i in range(0, len(ids), chunk):
        batch = ids[i:i+chunk]
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            xml_resp = await client.get(EFETCH_URL, params={"db":"pubmed","id":",".join(batch),"retmode":"xml","rettype":"abstract"})
            xml_resp.raise_for_status()
            parsed = _parse_pubmed_xml(xml_resp.text)
            out.extend(parsed)
    return out
```

### 4.2 `_parse_pubmed_xml(raw_xml: str) -> list[UnifiedLiteratureEntry]` 纯函数
标准库 xml.etree.ElementTree 实现，路径映射表同设计节 1：
| Unified 字段 | XPath | Fallback |
|---|---|---|
| pmid | `MedlineCitation/PMID.text` | "" |
| doi | `PubmedData/ArticleIdList/ArticleId[@IdType='doi'].text` | `MedlineCitation/Article/ELocationID[@EIdType='doi']` | "" |
| title | `MedlineCitation/Article/ArticleTitle.itertext()`（去首尾空白） | "" |
| authors | 每个 Author = LastName + " " + ForeName；用 "; " join（避免与 journal 里的 "," 混淆）；CollectiveName 直接用 | "" |
| journal | `MedlineCitation/Article/Journal/Title.text` | `./ISOAbbreviation.text` → "" |
| year | `JournalIssue/PubDate/Year.text` int | `PubDate/MedlineDate.text` 正则 `\b(19|20)\d{2}\b` → None |
| abstract | 所有 `AbstractText[@NlmCategory]` 用 `[{Category}] {text}\n` 拼接；NlmCategory 缺失用顺序编号 | None |
| source_key | 固定 "pubmed" | - |
| source_record_id | 同 pmid | f"pm{i}" for index |

### 4.3 容错
- 整体 `try ET.fromstring`：ParseError 直接 raise（上层 prefer_real 转 warning + 0 条 / force_real 标 failed）
- 每条 `<PubmedArticle>` 解析包单独 try：异常 → `continue`，warnings 追加 `pubmed article ${idx}: ${exc_repr}`
- title / abstract 含有嵌套 `<i>/<b>/<sup>`：一律 `itertext()` 去标签

## 5. 节 2 CNKI / 万方 抓取 + fallback（用户已通过）

### 5.1 抓取 URLs 与 headers（每 source 独立）

**CNKI**
- URL：`https://scholar.cnki.net/home/index/search?isrealbtn=true&searchType=SINGLEVIEWSEARCH&dbvalue=CJFQ,CDMD,IPFD,CISD,SNAD,CCND,CMFD,CPFD,SWKD,SCSD,CYFD,BDZK&txt_1_sel=SU$%25=TJ$%25=KY$%25=ZU$%25=AB$%25=AU$%25=CLC$%25=RF$%25=OP=&txt_1_value1=<URL_ENCODED_QUERY>`
  - 如果 scholar 域名反爬重，备选：`https://kns.cnki.net/kns8s/defaultresult/classyliteraturesearch?kw=...`
- Headers（CNKI 反爬最小化）：
  ```
  User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36
  Referer: https://scholar.cnki.net/
  Accept: text/html,application/xhtml+xml
  Accept-Language: zh-CN,zh;q=0.9
  ```
- 每页默认 20 条，只抓第 1 页（SearchRun 只需要粗检索样本，细检索由用户手动筛选）
- 解析字段（BeautifulSoup4 html.parser）：
  - result items: CSS 选择器待真实抓取后取第 1 页的卡片容器，按 class 前缀或 `<h1>/<h2>/<a class=title>` 找锚点
  - title: a.title (get_text strip)
  - authors: 作者 span / em，分号 ; 分隔直接取
  - journal: 期刊名 link 或 span
  - year: 年份正则 `\b(19|20)\d{2}\b`，从 "《期刊》2024, Vol.40..." 里抽
  - abstract: 摘要 div（折叠前摘要优先），无则 ""
  - doi: DOM 中有则取，多数 CNKI 公开 search 页无 doi，留空
  - source_record_id: href 中 querystring `fileName=xxx` 或 url id

**万方**
- URL：`https://s.wanfangdata.com.cn/paper?q=<URL_ENCODED_QUERY>`
- Headers UA/Referer：`https://s.wanfangdata.com.cn/`
- 只抓第 1 页（默认 10~20），万方公开摘要更全，尽量完整
- 解析字段：
  - result items: 论文卡片容器，找 `.paper-item` 或同级 class（以实际抓取 HTML 定）
  - title/author/journal/year: 卡片文本按位置取，万方卡片布局比 CNKI 规律
  - abstract: 摘要段存在则取（万方通常能拿到完整首段）
  - source_record_id: href 中 `/periodical/` 之后编号

### 5.2 fallback 触发条件（prefer_real）
```
任一满足即 fallback：
  ├─ HTTP 抛异常（Timeout / ConnectError / TooManyRedirects / HTTPStatus != 2xx）
  ├─ 响应 html 中出现以下关键词任一（不区分大小写）：
  │    "验证码" | "安全验证" | "人机验证" | "sliderVerification" | "请完成验证" | "403 Forbidden"
  ├─ status_code == 302 and 目标跳转到 /login / captcha
  └─ len(parsed_records) == 0（即真抓解析没抓到任何记录 → 判定结构变了/被静默封，fallback）
```
fallback 时：
- 若 INJECTED_DATASET 有值 → `return AdapterResult(hits=None, records=copy.deepcopy(...), warnings=[f"{source} 抓取失败({reason})，回退注入 {N} 条"])`
- 若 INJECTED_DATASET 无 → `return AdapterResult(hits=None, records=[], warnings=[f"{source} 抓取失败({reason})，且未注册注入数据，返回 0 条"])`

force_real 模式：不 fallback，异常 raise。

### 5.3 反爬节流
- rate_limit_rps 默认：pubmed=3, cnki=0.3, wanfang=0.3（可单独覆盖）
- 除 rps 固定 sleep 外，CNKI/万方每次发请求前加 `random.uniform(2.5, 4.0)` 秒 jitter（更像人类）
- CAPTCHA 关键词命中后，worker 级记录：ctx 内缓存 `_banned_sources: set[str]`，后续所有该 SearchRun 内该 source 的 retry 不跑 HTTP，直接 fallback（避免被封更狠）

## 6. 节 3 模式三级切换 & 测试策略（用户已通过）

### 6.1 模式语义
```
"prefer_real"  : 真抓 → (fail or CAPTCHA or records==0) → fallback? 有 INJECTED_DATASET 用 | 无 0 条警告
"force_mock"   : 直接 INJECTED_DATASET 或 monkeypatch 路径，0 外网
"force_real"   : 只真抓，不 fallback，失败即 source=failed
```

### 6.2 解析顺序（SearchRunContext._resolve_mode(ctx, source_key)）
```
mode = "prefer_real"
if env(f"MEDA_{source_key.upper()}_MODE") in VALID_MODES:
    mode = env_value
if source_key in ctx.adapter_modes:
    mode = ctx.adapter_modes[source_key]      # ctx 覆盖 env
return mode
```
注意：`ctx.adapter_modes` 是字典，能 per-source 单独定；未来前端暴露也只改这个 dict。

### 6.3 测试策略（零外网默认）
**conftest.py 新增 autouse fixture（影响所有测试）**：
```python
@pytest.fixture(autouse=True)
def _default_force_mock_for_tests(monkeypatch):
    monkeypatch.setenv("MEDA_PUBMED_MODE", "force_mock")
    monkeypatch.setenv("MEDA_CNKI_MODE",   "force_mock")
    monkeypatch.setenv("MEDA_WANFANG_MODE","force_mock")
```
→ 现有 125 passed 的所有测试 **不需要改**，仍然走 mock 路径。

**新增测试 6 条（均在 `apps/agent-core/tests/` 下）**：
1. `test_real_pubmed_xml_parse.py::test_parse_fixed_xml_fixture_matches_mock_entries`（offline）
   - 手工拼装 `<PubmedArticleSet>` 6 篇（对应 conftest 的 6 条 mock，PubMed 3 条构造 DOI/PMID/Title/Journal/Year/Abstract/Author 全量字段）
   - `_parse_pubmed_xml(xml_str)` → 断言 titles 精确匹配 / dois ∈ 预期集合 / years 正确
   - 验证嵌套 `<i>`/`<b>` 标签会被 itertext() 去除
2. `test_real_pubmed_xml_parse.py::test_parse_invalid_xml_raises_clean`（offline）
   - 坏 XML → ParseError 被捕获 / prefer_real 分支返回 warning + 空列表（不影响 worker 状态机）
3. `test_real_cnki_parse.py::test_parse_stub_html`（offline）
   - 手工截一段 CNKI 搜索结果 HTML（1 title + 1 no-abstract 两条）→ `_parse_cnki_list(html_str)` 断言
4. `test_real_cnki_parse.py::test_parse_wanfang_stub_html`（offline）
   - 万方一段，同上
5. `test_real_search_fallback.py::test_prefer_real_falls_back_on_connect_error`（offline + monkeypatch httpx 抛 ConnectError）
   - 设 prefer_real + INJECTED_DATASET 非空 + httpx.AsyncClient.get 抛 ConnectError
   - `asyncio.run(CnkiAdapter().run_search(q, ctx))` → records == INJECTED_DATASET len / warnings[0] 含 "回退到注入"
6. `test_real_search_force_real.py::test_force_real_propagates_exception`（offline + monkeypatch）
   - mode=force_real → httpx 抛异常 → run_search **往上抛**，worker 标 failed（不吞）

**可选：`@pytest.mark.needs_network` 3 条（默认跳过，手动 pytest -m needs_network 时执行）**：
- `test_needs_network_pubmed.py`：PubMed "dapagliflozin chronic kidney disease" 前 10 PMID → 至少 1 条解析到非空 title/journal/year
- `test_needs_network_cnki.py`：CNKI "二甲双胍 SGLT2" → 至少 1 条解析成功 或 fallback warning 触发
- `test_needs_network_wanfang.py`：万方 "达格列净 安全性 Meta" → 至少 1 条解析成功 或 fallback

## 7. 验证清单（Done criteria）
- [x] 设计节 1 PubMed XML 解析通过（用户确认 2026-08-12）
- [x] 设计节 2 CNKI/万方抓取策略通过（用户确认 2026-08-12）
- [x] 设计节 3 Mode 切换 + 测试策略通过（用户确认 2026-08-12）
- [ ] pyproject.toml 加 beautifulsoup4
- [ ] 代码落地：pubmed_adapter 真解析 / cnki_adapter / wanfang_adapter 真抓
- [ ] 代码落地：SearchRunContext.adapter_modes + resolve_mode helper
- [ ] 测试落地：6 条 offline + 3 条 needs_network，新增 pytest 收集通过
- [ ] **回归验证：现有 125 passed 不回归**（零外网，autouse force_mock fixture）
- [ ] 最终：全 5 端 ≥ 199（之前 baseline）+ 新 9 条测试通过 → ≥ 208
