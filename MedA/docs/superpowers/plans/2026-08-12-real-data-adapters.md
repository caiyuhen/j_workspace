# 真实数据 Adapter 落地 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 Wave 8 文献检索的三数据源从"mock/stub 注入"切换到"优先真实数据（PubMed XML 真解析 + CNKI/万方公开搜索 HTML 抓取），网络/反爬失败时 fallback 到注入数据集"，保障 pytest 默认零外网且 125 现有测试不回归。

**Architecture:**
- 新增 beautifulsoup4 依赖，只引标准库 xml.etree + bs4 html.parser 后端
- 每个 Adapter 内部 `_resolve_mode(ctx)` 三级 mode：env `MEDA_PUBMED_MODE` → `ctx.adapter_modes["pubmed"]` → 默认 `prefer_real`
- prefer_real 流程：真抓 HTTP → 解析；异常/反爬关键词/解析 0 条 → 自动 fallback 到 INJECTED_DATASET 并在 AdapterResult.warnings 写明原因
- pytest 全量 autouse fixture 统一把三 source mode 默认设 force_mock，现有 125 测试无外网

**Tech Stack:** Python 3.11, httpx, xml.etree (stdlib), beautifulsoup4, pytest (stdlib monkeypatch)

---

## File Structure

| File | 用途 | 改动类型 |
|---|---|---|
| `apps/agent-core/pyproject.toml` | 追加 `beautifulsoup4>=4.12.0` 依赖 | Modify |
| `apps/agent-core/app/services/sources/protocol.py` | `SearchRunContext` 加 `adapter_modes: dict[str, Literal] = {}` | Modify |
| `apps/agent-core/app/services/sources/pubmed_adapter.py` | `_parse_pubmed_xml(xml)` 新纯函数 + `_efetch_parse_entries` 从占位替换成真解析 + `_resolve_mode` + fallback 分支 | Modify |
| `apps/agent-core/app/services/sources/cnki_adapter.py` | 删除 Stub-only 结构 → 引入 bs4、真抓函数 + 解析函数 + fallback；INJECTED_DATASET 保留 | Modify |
| `apps/agent-core/app/services/sources/wanfang_adapter.py` | 同上 CNKI 同构 | Modify |
| `apps/agent-core/app/services/search_worker.py` | `_execute_single_source` 构造 `SearchRunContext` 时填 `rate_limit_rps` 默认值（pubmed=3, cnki=0.3, wanfang=0.3）+ `adapter_modes` 从 `os.getenv()` 初始字典填入 | Modify |
| `apps/agent-core/tests/conftest.py` | 加 `autouse` fixture 统一 `monkeypatch.setenv("MEDA_*_MODE","force_mock")` 保证现有测试 0 外网；加 pytest.ini options 的 `markers.needs_network` | Modify |
| `apps/agent-core/tests/test_real_pubmed_xml_parse.py` (新) | 固定 PubmedArticleSet XML fixture → 解析断言对应 conftest 6 条 mock；+ 坏 XML ParseError 测试 | Create |
| `apps/agent-core/tests/test_real_cnki_wanfang_parse.py` (新) | 各 1 段固定 HTML list 页 stub → 解析断言 title/journal/year | Create |
| `apps/agent-core/tests/test_real_search_fallback.py` (新) | prefer_real + INJECTED_DATASET + monkeypatch httpx 抛 ConnectError → 断言 records == 注入集 + warnings 含"回退到注入"；force_real 模式下异常直接 raise 不吞 | Create |
| `apps/agent-core/tests/test_needs_network_pubmed.py` (新，可选) | `@pytest.mark.needs_network`，默认 skip；"dapagliflozin chronic kidney disease" 10 PMID → 至少 1 条非空 title | Create (可选) |
| `apps/agent-core/tests/test_needs_network_cnki_wanfang.py` (新，可选) | CNKI "二甲双胍 SGLT2" / 万方 "达格列净 安全性 Meta"，至少 1 条解析成功或 fallback warning | Create (可选) |

---

### Task 1: 依赖 + 基础环境（beautifulsoup4 + 零外网默认）

**Files:**
- Modify: `apps/agent-core/pyproject.toml`
- Modify: `apps/agent-core/tests/conftest.py` (末尾追加)
- Modify: `apps/agent-core/pyproject.toml` [tool.pytest.ini_options] markers

- [ ] **Step 1: 写 conftest autouse fixture（先写测试期望 → 等环境位就绪后 pytest 运行不过也没关系）**
  追加到 `tests/conftest.py` 末尾（在 `inject_mock_datasets_into_adapters` 之后）：
  ```python
  import os as _os
  import pytest as _pytest

  @_pytest.fixture(autouse=True)
  def _force_all_sources_force_mock_for_pytest(monkeypatch):
      """pytest 默认零外网：三 source 全 force_mock。
      needs_network 标记的测试会显式 pop 这些 env。
      """
      monkeypatch.setenv("MEDA_PUBMED_MODE", "force_mock")
      monkeypatch.setenv("MEDA_CNKI_MODE",   "force_mock")
      monkeypatch.setenv("MEDA_WANFANG_MODE","force_mock")
  ```

- [ ] **Step 2: 加 pytest needs_network marker（pyproject.toml [tool.pytest.ini_options] 追加）**
  ```toml
  [tool.pytest.ini_options]
  pythonpath = ["."]
  testpaths = ["tests"]
  addopts = "-p no:warnings --strict-markers"
  markers = [
      "needs_network: 标记需要真实外网的测试，默认 skip。运行：pytest -m needs_network",
  ]
  ```
  *说明*：如果 `--strict-markers` 导致现有 marker 没注册报错，则删掉 strict-markers 行；保留 markers 列表即可。

- [ ] **Step 3: 加 beautifulsoup4 依赖到 pyproject.toml**
  修改 `pyproject.toml:5-12` dependencies：
  ```toml
  dependencies = [
    "fastapi>=0.115.0",
    "uvicorn>=0.30.0",
    "pytest>=8.3.0",
    "httpx>=0.27.0",
    "sqlmodel>=0.0.22",
    "rank-bm25>=0.2.2",
    "beautifulsoup4>=4.12.0",
  ]
  ```

- [ ] **Step 4: 安装依赖并跑现有 1 条 smoke test 看 autouse fixture 没副作用**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv pip install -e . ; uv run python -m pytest tests/test_search_run_models.py -v 2>&1 | Select-Object -Last 6`
  Expected: `4 passed`

- [ ] **Step 5: Commit**
  ```bash
  git add apps/agent-core/pyproject.toml apps/agent-core/tests/conftest.py
  git commit -m "chore: add bs4 dep + pytest default force_mock autouse"
  ```

---

### Task 2: PubMed XML 真解析（核心）

**Files:**
- Modify: `apps/agent-core/app/services/sources/pubmed_adapter.py`
- Test: `apps/agent-core/tests/test_real_pubmed_xml_parse.py` (Create)
- Modify: `apps/agent-core/app/services/sources/protocol.py` (adapter_modes)
- Modify: `apps/agent-core/app/services/search_worker.py` (ctx 构造)

- [ ] **Step 1: 扩 SearchRunContext（protocol.py L14-L20）**
  ```python
  from dataclasses import dataclass, field
  from typing import Literal, Protocol

  ...

  @dataclass
  class SearchRunContext:
      project_id: int
      search_run_id: int
      rate_limit_rps: dict[str, float] = field(default_factory=dict)
      pubmed_api_key: str | None = None
      adapter_modes: dict[str, Literal["prefer_real", "force_mock", "force_real"]] = field(default_factory=dict)
  ```

- [ ] **Step 2: 写 test_real_pubmed_xml_parse.py（先写 failing 测试，T12 spec §4.2 手工拼接 XML fixture 对应 3 条 PubMed mock）**
  ```python
  """Offline parse test: fixed XML -> list[UnifiedLiteratureEntry] matches conftest 3 PubMed mock."""
  from app.services.sources.pubmed_adapter import _parse_pubmed_xml
  from tests.conftest import MOCK_PUBMED_DATASET

  # 手工 XML fixture：3 条 PubmedArticle，PMID=mock_pubmed 对应的 pmid 37123457/37000001/37333333
  FIXED_PUBMED_XML = """<?xml version="1.0"?>
  <!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMed 2024.1//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_240101.dtd">
  <PubmedArticleSet>
    <PubmedArticle>
      <MedlineCitation Status="MEDLINE" Owner="NLM">
        <PMID Version="1">37123457</PMID>
        <Article PubModel="Print-Electronic">
          <Journal>
            <Title>New England Journal of Medicine</Title>
            <JournalIssue CitedMedium="Internet">
              <Volume>388</Volume>
              <Issue>13</Issue>
              <PubDate>
                <Year>2023</Year>
                <Month>03</Month>
                <Day>30</Day>
              </PubDate>
            </JournalIssue>
          </Journal>
          <ArticleTitle>Dapagliflozin in Patients with <i>Chronic Kidney Disease</i></ArticleTitle>
          <Abstract>
            <AbstractText Label="BACKGROUND" NlmCategory="BACKGROUND">The SGLT2 inhibitor in chronic kidney disease (CKD).</AbstractText>
            <AbstractText Label="METHODS" NlmCategory="METHODS">We conducted a double-blind RCT.</AbstractText>
          </Abstract>
          <AuthorList CompleteYN="Y">
            <Author><LastName>Neuen</LastName><ForeName>BL</ForeName></Author>
          </AuthorList>
        </Article>
      </MedlineCitation>
      <PubmedData>
        <ArticleIdList>
          <ArticleId IdType="pubmed">37123457</ArticleId>
          <ArticleId IdType="doi">10.1056/NEJMoa2212939</ArticleId>
        </ArticleIdList>
      </PubmedData>
    </PubmedArticle>
    <PubmedArticle>
      <MedlineCitation Status="Publisher" Owner="NLM">
        <PMID Version="1">37000001</PMID>
        <Article PubModel="Electronic">
          <Journal>
            <Title>Lancet Diabetes Endocrinol</Title>
            <JournalIssue CitedMedium="Internet">
              <PubDate>
                <Year>2023</Year>
              </PubDate>
            </JournalIssue>
          </Journal>
          <ArticleTitle>Effect of Empagliflozin on Cardiovascular Outcomes in T2DM with Established CVD</ArticleTitle>
          <AuthorList><Author><LastName>Zinman</LastName><ForeName>B</ForeName></Author></AuthorList>
        </Article>
      </MedlineCitation>
      <PubmedData><ArticleIdList>
        <ArticleId IdType="pubmed">37000001</ArticleId>
        <ArticleId IdType="doi">10.1016/S2213-8587(23)00042-5</ArticleId>
      </ArticleIdList></PubmedData>
    </PubmedArticle>
    <PubmedArticle>
      <MedlineCitation Status="MEDLINE" Owner="NLM">
        <PMID>37333333</PMID>
        <Article>
          <Journal><Title>JAMA</Title><JournalIssue><PubDate><MedlineDate>2024 May-Jun</MedlineDate></PubDate></JournalIssue></Journal>
          <ArticleTitle>Metformin plus Lifestyle versus Lifestyle Alone in Prediabetes</ArticleTitle>
          <Abstract><AbstractText>This is a RCT of Metformin plus lifestyle against lifestyle.</AbstractText></Abstract>
          <AuthorList>
            <Author><LastName>Chen</LastName><ForeName>L</ForeName></Author>
            <Author><LastName>Zhang</LastName><ForeName>Y</ForeName></Author>
            <Author><LastName>Wang</LastName><ForeName>H</ForeName></Author>
          </AuthorList>
        </Article>
      </MedlineCitation>
      <PubmedData><ArticleIdList>
        <ArticleId IdType="pubmed">37333333</ArticleId>
        <ArticleId IdType="doi">10.1001/JAMA.2023.12345</ArticleId>
      </ArticleIdList></PubmedData>
    </PubmedArticle>
  </PubmedArticleSet>"""


  def test_parse_pubmed_xml_matches_conftest_mock_3():
      entries = _parse_pubmed_xml(FIXED_PUBMED_XML)
      assert len(entries) == 3
      got_pmids = {e.pmid for e in entries}
      want_pmids = {m.pmid for m in MOCK_PUBMED_DATASET}
      assert got_pmids == want_pmids

      # #1 Dapagliflozin
      e1 = next(e for e in entries if e.pmid == "37123457")
      assert e1.source_key == "pubmed"
      assert e1.source_record_id == "37123457"
      assert e1.doi == MOCK_PUBMED_DATASET[0].doi  # "10.1056/nejmoa2212939"（要求小写）
      assert "Chronic Kidney Disease" in e1.title  # 标签去除
      assert "double-blind RCT" in e1.abstract  # METHODS 文本
      assert e1.journal == "New England Journal of Medicine"
      assert e1.year == 2023
      assert "Neuen BL" in e1.authors

      # #3 MedlineDate → 2024
      e3 = next(e for e in entries if e.pmid == "37333333")
      assert e3.year == 2024
      assert e3.authors.count(";") == 2  # 3 位作者 → 2 个分号分隔


  def test_parse_pubmed_xml_broken_xml_returns_empty_with_catch():
      """坏 XML 情况下 prefer_real 不抛：解析失败返回空列表，异常被 _parse_pubmed_xml 吞并返回空。
      （注：force_real 情况下上层再决定是否 raise）"""
      broken = "<PubmedArticleSet><PubmedArticle></Malformed"
      result = _parse_pubmed_xml(broken)
      assert result == []
  ```

- [ ] **Step 3: 运行测试 → 确认 FAIL（_parse_pubmed_xml 还没写）**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_real_pubmed_xml_parse.py -v 2>&1 | Select-Object -Last 15`
  Expected: FAIL with `ImportError: cannot import name '_parse_pubmed_xml' from 'app.services.sources.pubmed_adapter'`

- [ ] **Step 4: 在 pubmed_adapter.py 写 `_parse_pubmed_xml` + 改 `_efetch_parse_entries` 真实现 + `_resolve_mode`**
  新增 imports：
  ```python
  from __future__ import annotations
  import asyncio
  import os
  import re
  from typing import Iterable
  import xml.etree.ElementTree as ET
  import httpx
  from .protocol import AdapterResult, NormalizedSearchQuery, SearchRunContext, SourceAdapter, UnifiedLiteratureEntry
  ```
  在 `_efetch_parse_entries` 之前插入 `_parse_pubmed_xml` 纯函数 + `_resolve_mode` helper：
  ```python
  _MODE_ENV_MAP = {
      "pubmed":   "MEDA_PUBMED_MODE",
      "cnki":     "MEDA_CNKI_MODE",
      "wanfang":  "MEDA_WANFANG_MODE",
  }
  _VALID_MODES = {"prefer_real", "force_mock", "force_real"}


  def _resolve_mode(source_key: str, ctx: SearchRunContext) -> str:
      """三级优先级：ctx.adapter_modes > env > 默认 prefer_real"""
      env_k = _MODE_ENV_MAP.get(source_key)
      mode = "prefer_real"
      if env_k and os.getenv(env_k) in _VALID_MODES:
          mode = os.environ[env_k]
      if source_key in ctx.adapter_modes and ctx.adapter_modes[source_key] in _VALID_MODES:
          mode = ctx.adapter_modes[source_key]
      return mode


  _YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


  def _parse_pubmed_xml(raw_xml: str) -> list[UnifiedLiteratureEntry]:
      """xml.etree 解析 PubmedArticleSet → UnifiedLiteratureEntry[]。
      任何 ParseError / 单条异常均吞掉返回空（上层按 mode 决定 fallback）。"""
      try:
          root = ET.fromstring(raw_xml)
      except ET.ParseError:
          return []
      out: list[UnifiedLiteratureEntry] = []
      for article in root.findall(".//PubmedArticle"):
          try:
              pmid_el = article.find(".//MedlineCitation/PMID")
              pmid = (pmid_el.text or "").strip() if pmid_el is not None else ""

              # DOI: prefer PubmedData ArticleId @IdType=doi，退 ELocationID
              doi = ""
              for aid in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
                  if aid.attrib.get("IdType") == "doi" and aid.text:
                      doi = aid.text.strip().lower()
                      break
              if not doi:
                  loc = article.find(".//MedlineCitation/Article/ELocationID")
                  if loc is not None and loc.attrib.get("EIdType") == "doi" and loc.text:
                      doi = loc.text.strip().lower()

              # Title: itertext() 去 <i><b>
              title_el = article.find(".//MedlineCitation/Article/ArticleTitle")
              title = "".join(title_el.itertext()).strip() if title_el is not None else ""

              # Authors: LastName + " " + ForeName，用 "; " join
              authors = []
              for a in article.findall(".//MedlineCitation/Article/AuthorList/Author"):
                  last = a.find("LastName")
                  fore = a.find("ForeName")
                  coll = a.find("CollectiveName")
                  if coll is not None and coll.text:
                      authors.append(coll.text.strip())
                  elif last is not None and last.text:
                      fn = (fore.text or "").strip() if fore is not None else ""
                      authors.append(f"{last.text.strip()} {fn}".strip())
              authors_str = "; ".join(authors)

              # Journal: Title > ISOAbbreviation
              journal_el = article.find(".//MedlineCitation/Article/Journal/Title")
              journal = (journal_el.text or "").strip() if journal_el is not None else ""
              if not journal:
                  iso = article.find(".//MedlineCitation/Article/Journal/ISOAbbreviation")
                  journal = (iso.text or "").strip() if iso is not None else ""

              # Year: PubDate/Year > MedlineDate regex
              year: int | None = None
              year_el = article.find(".//MedlineCitation/Article/Journal/JournalIssue/PubDate/Year")
              if year_el is not None and year_el.text and year_el.text.isdigit():
                  year = int(year_el.text)
              if year is None:
                  medline_el = article.find(".//MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate")
                  if medline_el is not None and medline_el.text:
                      m = _YEAR_RE.search(medline_el.text)
                      if m:
                          year = int(m.group(0))

              # Abstract: multiple AbstractText lines, [NlmCategory] prefix
              parts = []
              for i, at in enumerate(article.findall(".//MedlineCitation/Article/Abstract/AbstractText")):
                  label = at.attrib.get("NlmCategory") or at.attrib.get("Label") or f"NoLabel-{i}"
                  txt = "".join(at.itertext()).strip() if at.text else ""
                  if not txt:
                      continue
                  parts.append(f"[{label}] {txt}")
              abstract = "\n".join(parts) or ""

              out.append(UnifiedLiteratureEntry(
                  doi=doi,
                  pmid=pmid,
                  title=title,
                  authors=authors_str,
                  journal=journal,
                  year=year,
                  abstract=abstract,
                  source_key="pubmed",
                  source_record_id=pmid or None,
              ))
          except Exception:
              # 单篇文章解析不影响整批（XML 结构部分损坏）
              continue
      return out
  ```

  然后替换 `_efetch_parse_entries`（从占位 → 真）：
  ```python
  async def _efetch_parse_entries(
      pmids: Iterable[str],
      chunk: int = 500,
  ) -> list[UnifiedLiteratureEntry]:
      """按 chunk 分页真 efetch XML，调用 _parse_pubmed_xml。"""
      ids = list(pmids)
      if not ids:
          return []
      out: list[UnifiedLiteratureEntry] = []
      for i in range(0, len(ids), chunk):
          batch = ids[i:i + chunk]
          try:
              async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
                  resp = await client.get(
                      EFETCH_URL,
                      params={"db": "pubmed", "id": ",".join(batch), "retmode": "xml", "rettype": "abstract"},
                  )
                  resp.raise_for_status()
              out.extend(_parse_pubmed_xml(resp.text))
          except (httpx.HTTPError, ET.ParseError):
              # force_real 情况下上层会根据 warnings 判断；这里只返回已解析的
              continue
      return out
  ```

  最后改 `PubMedAdapter.run_search`（加 mode 判断 + force_mock 仍走原 monkeypatch 路径，因为 monkeypatch 会替换这俩 helper，所以不需要额外 if；mode 的作用主要是 warnings）：
  ```python
  class PubMedAdapter:
      source_key = "pubmed"

      async def run_search(
          self, query: NormalizedSearchQuery, ctx: SearchRunContext
      ) -> AdapterResult:
          mode = _resolve_mode("pubmed", ctx)
          # Minimal rate limit sleep based on rps
          rps = ctx.rate_limit_rps.get("pubmed", 3.0)
          await asyncio.sleep(1.0 / max(rps, 0.1))

          try:
              ids, count = await _esearch_pubmed_ids(query, ctx)
              entries = await _efetch_parse_entries(ids)
          except Exception as exc:
              if mode == "force_real":
                  raise
              # prefer_real: 网络异常 → 返回空 + warning（INJECTED_DATASET 机制 pubmed 不用；它的 mock 用 monkeypatch）
              return AdapterResult(
                  hits_on_source=None,
                  records=[],
                  warnings=[f"PubMed (mode={mode}) HTTP 失败: {exc.__class__.__name__}: {exc}"],
              )

          normalized = [
              UnifiedLiteratureEntry(
                  doi=(r.doi or "").strip().lower(),
                  pmid=(r.pmid or "").strip(),
                  title=(r.title or "").strip(),
                  authors=r.authors,
                  journal=r.journal,
                  year=r.year,
                  abstract=r.abstract,
                  source_key="pubmed",
                  source_record_id=r.source_record_id,
              )
              for r in entries
          ]
          warnings = []
          if count > 0 and len(normalized) == 0:
              warnings.append(
                  "PubMed esearch returned hits but XML parsed 0 entries (可能真 efetch 结构变动)。"
              )
          return AdapterResult(hits_on_source=count, records=normalized, warnings=warnings)
  ```

- [ ] **Step 5: 跑测试 → PASS**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_real_pubmed_xml_parse.py -v 2>&1 | Select-Object -Last 8`
  Expected: `2 passed`

- [ ] **Step 6: 修改 search_worker._execute_single_source 给 SearchRunContext 填 rate_limit_rps 默认值**
  改 `search_worker.py L146-149`：
  ```python
  default_rates = {"pubmed": 3.0, "cnki": 0.3, "wanfang": 0.3}
  default_rates.update(run.search_source_config_json.get("rate_limit_rps") or {})
  ctx = SearchRunContext(
      project_id=run.project_id,
      search_run_id=run.id,
      rate_limit_rps=default_rates,
      pubmed_api_key=os.getenv("PUBMED_API_KEY"),
      adapter_modes={},
  )
  ```
  *注意*：文件顶部需 `import os`（搜一下，没有就加）。search_source_config_json 字段如果不存在，退回 {}；需要在文件开头 `import json` 并且 `run.search_source_config_json = json.loads(...)` 若它是字符串。先按 dict 写；如果 models.py 里定义的是 `dict | None = Field(default=None, column=JSON)` 直接用即可。

- [ ] **Step 7: 回归一小段 worker / search_adapters tests 确认 monkeypatch 模式仍然可用**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_adapters.py tests/test_search_worker.py -v 2>&1 | Select-Object -Last 12`
  Expected: `7 passed`（test_search_adapters 4 + test_search_worker 3）

- [ ] **Step 8: Commit**
  ```bash
  git add apps/agent-core/app/services/sources/protocol.py \
          apps/agent-core/app/services/sources/pubmed_adapter.py \
          apps/agent-core/app/services/search_worker.py \
          apps/agent-core/tests/test_real_pubmed_xml_parse.py
  git commit -m "feat(pubmed): XML efetch real parser + adapter_mode resolve helper"
  ```

---

### Task 3: CNKI 真实抓取 + 解析 + fallback

**Files:**
- Modify: `apps/agent-core/app/services/sources/cnki_adapter.py`
- Test: Create `apps/agent-core/tests/test_real_cnki_wanfang_parse.py` CNKI section

*注*：真 URL/selector 要先手动用 httpx 抓 1 次 scholar.cnki.net HTML 才能精确写出。Task 步骤里做了一次 "Step 0 侦察抓一次" 输出到文件里然后定 selector。

- [ ] **Step 1: 侦察抓 scholar.cnki.net 首页/搜索页一次（用 urllib.request 或者 httpx 命令），拿到 HTML stub 供测试 + 解析写 selector（只做 1 次不进 commit）**
  Run:
  ```powershell
  cd d:\workspace\MedA\apps\agent-core ; uv run python -c "
  import httpx, pathlib
  headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36','Referer':'https://scholar.cnki.net/','Accept-Language':'zh-CN,zh;q=0.9'}
  r = httpx.get('https://scholar.cnki.net/home/index/search?isrealbtn=true&searchType=SINGLEVIEWSEARCH&dbvalue=CJFQ&txt_1_value1=%E4%BA%8C%E7%94%B2%E5%8F%8C%E8%84%81%20SGLT2', headers=headers, timeout=20, follow_redirects=True)
  print('status', r.status_code)
  pathlib.Path('_tmp_cnki.html').write_text(r.text, encoding='utf-8')
  print('wrote', len(r.text), 'chars')
  "
  ```
  （如果 scholar 域名被重定向到 kns.cnki.net，就切换 URL 到 `https://kns.cnki.net/kns8s/defaultresult/classyliteraturesearch?kw=...` 同上）
  Expected: status 200 且 `_tmp_cnki.html` > 30KB。把文件里一段卡片 HTML（至少 2 条记录）复制出来做测试 fixture。

- [ ] **Step 2: 写 CNKI 解析测试（tests/test_real_cnki_wanfang_parse.py，CREATE）**
  以侦察步拿到的 DOM 为锚点。如果没拿到 DOM（或 403/CAPTCHA），用下边的简化假 DOM（保证 offline 可测，真抓时再替换 selector）：
  ```python
  """Offline parse tests for CNKI/Wanfang with fixed HTML stub cards."""
  from app.services.sources.cnki_adapter import _parse_cnki_list_html
  from app.services.sources.wanfang_adapter import _parse_wanfang_list_html

  CNKI_STUB_HTML = """
  <html><body>
  <div class="result-table">
    <table>
      <tr>
        <td class="name"><a class="fz14" href="https://kns.cnki.net/kcms2/article/abstract?filename=CJFQ20240001&dbname=CJFD2024">二甲双胍联合 SGLT2 抑制剂治疗 2 型糖尿病合并慢性肾病疗效观察</a></td>
        <td class="author">李明;王建国;赵丽</td>
        <td class="source">《中华内分泌代谢杂志》 2024年 第1期 33-41</td>
        <td class="abstract">目的 观察二甲双胍联合 SGLT2i 治疗 T2DM 合并 CKD 的疗效，评估 eGFR 改善情况。方法 120 例患者分组对照。</td>
      </tr>
      <tr>
        <td class="name"><a class="fz14" href="https://kns.cnki.net/kcms2/article/abstract?filename=CJFQ20232345&dbname=CJFDLAST2023">GLP-1 RA 对心血管结局影响的真实世界研究（单中心）</a></td>
        <td class="author">张伟;刘芳</td>
        <td class="source">《中国糖尿病杂志》 2023年 第11卷 888-893</td>
        <td class="abstract">回顾性纳入 210 例 T2DM 患者，观察 GLP-1 RA 与 SU 的 MACE 发生率差异。</td>
      </tr>
    </table>
  </div>
  </body></html>
  """

  WANFANG_STUB_HTML = """
  <html><body>
  <div class="result-list">
    <div class="paper-item">
      <h3 class="title"><a href="/periodical/zhszb202402011">达格列净在 CKD 非糖尿病人群中的安全性 Meta 分析</a></h3>
      <div class="authors">孙志远;陈曦</div>
      <div class="source-year">《中华肾脏病杂志》 2024, Vol.40(2): 112-120</div>
      <div class="abstract">系统评价达格列净用于非 DM CKD 的安全性，纳入 8 项 RCT，结果总体安全性良好。</div>
    </div>
  </div>
  </body></html>
  """


  def test_parse_cnki_stub_2_records_match_conftest_cnki():
      records = _parse_cnki_list_html(CNKI_STUB_HTML)
      assert len(records) == 2
      r0 = records[0]
      assert r0.source_key == "cnki"
      assert r0.title.startswith("二甲双胍联合")
      assert r0.journal == "中华内分泌代谢杂志"
      assert r0.year == 2024
      assert r0.doi == ""
      assert "SGLT2i 治疗 T2DM" in r0.abstract
      assert "CJFQ20240001" in (r0.source_record_id or "")

      r1 = records[1]
      assert r1.authors == "张伟;刘芳"
      assert r1.year == 2023
      assert "GLP-1 RA" in r1.title


  def test_parse_wanfang_stub_1_record():
      records = _parse_wanfang_list_html(WANFANG_STUB_HTML)
      assert len(records) == 1
      r0 = records[0]
      assert r0.source_key == "wanfang"
      assert "达格列净" in r0.title
      assert r0.journal == "中华肾脏病杂志"
      assert r0.year == 2024
      assert "zhszb202402011" in (r0.source_record_id or "")
      assert "安全性" in r0.abstract
  ```

- [ ] **Step 3: 运行测试 → FAIL（函数未定义）**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_real_cnki_wanfang_parse.py::test_parse_cnki_stub_2_records_match_conftest_cnki -v 2>&1 | Select-Object -Last 10`
  Expected: FAIL ImportError `_parse_cnki_list_html`

- [ ] **Step 4: 重写 cnki_adapter.py（真抓 + fallback，保留 INJECTED_DATASET）**
  ```python
  from __future__ import annotations
  import asyncio
  import os
  import random
  import re
  from urllib.parse import quote
  import httpx
  from bs4 import BeautifulSoup
  from .protocol import AdapterResult, NormalizedSearchQuery, SearchRunContext, SourceAdapter, UnifiedLiteratureEntry
  from .pubmed_adapter import _MODE_ENV_MAP, _VALID_MODES, _resolve_mode  # 复用 PubMed 的 mode helper

  INJECTED_DATASET: list[UnifiedLiteratureEntry] | None = None

  _HEADERS = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
      "Referer": "https://scholar.cnki.net/",
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
  }

  _BANNED_PATTERNS = re.compile(r"验证码|安全验证|人机验证|请完成验证|sliderVerification|403 Forbidden|403 ", re.I)
  _YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


  def _parse_cnki_list_html(html: str) -> list[UnifiedLiteratureEntry]:
      """CNKI list page -> UnifiedLiteratureEntry[]. Selector 以 stub HTML 为准，真抓 DOM 变动时改本函数 selector 即可。"""
      out: list[UnifiedLiteratureEntry] = []
      soup = BeautifulSoup(html, "html.parser")

      # Stub: tr > td.name > a.fz14
      # Real scholar.cnki.net: 侦察后改。两种路径都给，命中任一即可。
      rows = soup.select("div.result-table table tr") or soup.select("div.result-item") or soup.find_all("tr")
      for tr in rows:
          try:
              a = tr.select_one("td.name a.fz14") or tr.select_one("a.title") or tr.find("a", attrs={"class": "fz14"})
              if not a:
                  continue
              title = a.get_text(" ", strip=True)
              href = a.get("href", "")
              m = re.search(r"filename=([^&?#]+)", href)
              source_record_id = m.group(1) if m else None

              authors_el = tr.select_one("td.author") or tr.select_one("div.abstract")
              authors = authors_el.get_text(" ", strip=True) if authors_el is not None else ""

              source_el = tr.select_one("td.source") or tr.select_one(".journal-name")
              journal = ""
              year: int | None = None
              if source_el is not None:
                  s = source_el.get_text(" ", strip=True)
                  m_j = re.search(r"《([^》]+)》", s)
                  if m_j:
                      journal = m_j.group(1).strip()
                  m_y = _YEAR_RE.search(s)
                  if m_y:
                      year = int(m_y.group(0))

              abs_el = tr.select_one("td.abstract") or tr.select_one(".abstract-text")
              abstract = abs_el.get_text(" ", strip=True) if abs_el is not None else ""

              out.append(UnifiedLiteratureEntry(
                  doi="",
                  pmid="",
                  title=title,
                  authors=authors,
                  journal=journal,
                  year=year,
                  abstract=abstract,
                  source_key="cnki",
                  source_record_id=source_record_id,
              ))
          except Exception:
              continue
      return out


  async def _fetch_cnki_html(boolean_text: str, timeout_s: float = 20.0) -> str:
      url = (
          "https://scholar.cnki.net/home/index/search"
          "?isrealbtn=true&searchType=SINGLEVIEWSEARCH"
          "&dbvalue=CJFQ,CDMD,IPFD,CISD,SNAD,CCND,CMFD,CPFD,SWKD,SCSD,CYFD,BDZK"
          f"&txt_1_sel=SU$%25=TJ$%25=KY$%25=ZU$%25=AB$%25=AU$%25=CLC$%25=RF$%25=OP"
          f"&txt_1_value1={quote(boolean_text)}"
      )
      async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_s), follow_redirects=True) as client:
          r = await client.get(url, headers=_HEADERS)
          r.raise_for_status()
          return r.text


  class CnkiAdapter:
      source_key = "cnki"

      async def run_search(
          self, query: NormalizedSearchQuery, ctx: SearchRunContext
      ) -> AdapterResult:
          mode = _resolve_mode("cnki", ctx)
          rps = ctx.rate_limit_rps.get("cnki", 0.3)
          await asyncio.sleep(1.0 / max(rps, 0.05) + random.uniform(0.0, 1.5))

          # force_mock 短路：直接 INJECTED_DATASET（保持与原 stub 同语义）
          if mode == "force_mock":
              if not INJECTED_DATASET:
                  return AdapterResult(None, [], ["CNKI mode=force_mock 但 INJECTED_DATASET 未注册，返回 0 条"])
              out = [
                  UnifiedLiteratureEntry(
                      doi=(r.doi or "").strip().lower(),
                      pmid=(r.pmid or "").strip(),
                      title=(r.title or "").strip(),
                      authors=r.authors,
                      journal=r.journal,
                      year=r.year,
                      abstract=r.abstract,
                      source_key="cnki",
                      source_record_id=r.source_record_id,
                  )
                  for r in INJECTED_DATASET
              ]
              return AdapterResult(hits_on_source=len(out), records=out, warnings=[])

          # prefer_real / force_real
          try:
              html = await _fetch_cnki_html(query.boolean_text)
              if _BANNED_PATTERNS.search(html):
                  raise RuntimeError("CNKI 返回了验证码/被封禁页面（按关键词命中）")
              parsed = _parse_cnki_list_html(html)
              hits = len(parsed) or None
              if len(parsed) == 0:
                  raise RuntimeError("CNKI 解析到 0 条记录")
              return AdapterResult(
                  hits_on_source=hits,
                  records=parsed,
                  warnings=[f"CNKI 公开检索成功 {len(parsed)} 条（粗检索首页）"],
              )
          except Exception as exc:
              if mode == "force_real":
                  raise
              # fallback 分支
              if INJECTED_DATASET:
                  out = [
                      UnifiedLiteratureEntry(
                          doi=(r.doi or "").strip().lower(), pmid=(r.pmid or "").strip(),
                          title=(r.title or "").strip(), authors=r.authors,
                          journal=r.journal, year=r.year, abstract=r.abstract,
                          source_key="cnki", source_record_id=r.source_record_id,
                      )
                      for r in INJECTED_DATASET
                  ]
                  return AdapterResult(
                      hits_on_source=len(out), records=out,
                      warnings=[f"CNKI 真抓失败 ({exc.__class__.__name__}: {exc})，fallback 注入数据 {len(out)} 条"],
                  )
              return AdapterResult(
                  hits_on_source=None, records=[],
                  warnings=[f"CNKI 真抓失败 ({exc.__class__.__name__}: {exc})，且未注册 INJECTED_DATASET，返回 0 条"],
              )
  ```

- [ ] **Step 5: 跑解析测试 → PASS**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_real_cnki_wanfang_parse.py::test_parse_cnki_stub_2_records_match_conftest_cnki -v 2>&1 | Select-Object -Last 8`
  Expected: `1 passed`

- [ ] **Step 6: 回归 conftest 现有 CNKI tests（确保 force_mock 仍然返回注入集）**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_run_api.py tests/test_literature_api.py -v -k "cnki or 二甲双胍" 2>&1 | Select-Object -Last 15`
  Expected: PASS（因为 autouse fixture 默认 force_mock，不会出真 HTTP）

- [ ] **Step 7: 清理 _tmp_cnki.html 临时文件**
  Run: `Remove-Item -Force d:\workspace\MedA\apps\agent-core\_tmp_cnki.html -ErrorAction SilentlyContinue`

- [ ] **Step 8: Commit**
  ```bash
  git add apps/agent-core/app/services/sources/cnki_adapter.py apps/agent-core/tests/test_real_cnki_wanfang_parse.py
  git commit -m "feat(cnki): prefer_real web scraper + fallback to INJECTED_DATASET"
  ```

---

### Task 4: 万方 真抓取 + 解析 + fallback（CNKI 同构）

**Files:**
- Modify: `apps/agent-core/app/services/sources/wanfang_adapter.py`
- Test: 复用 Task 3 中 `test_parse_wanfang_stub_1_record`

- [ ] **Step 1: 先跑一下 wanfang 解析测试 → FAIL（函数没定义）**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_real_cnki_wanfang_parse.py::test_parse_wanfang_stub_1_record -v 2>&1 | Select-Object -Last 10`
  Expected: FAIL ImportError `_parse_wanfang_list_html`

- [ ] **Step 2: 重写 wanfang_adapter.py（同构 CNKI，改 URL/headers/selectors）**
  ```python
  from __future__ import annotations
  import asyncio
  import random
  import re
  from urllib.parse import quote
  import httpx
  from bs4 import BeautifulSoup
  from .protocol import AdapterResult, NormalizedSearchQuery, SearchRunContext, SourceAdapter, UnifiedLiteratureEntry
  from .pubmed_adapter import _resolve_mode

  INJECTED_DATASET: list[UnifiedLiteratureEntry] | None = None

  _HEADERS = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
      "Referer": "https://s.wanfangdata.com.cn/",
      "Accept": "text/html,application/xhtml+xml",
      "Accept-Language": "zh-CN,zh;q=0.9",
  }

  _BANNED_PATTERNS = re.compile(r"验证码|安全验证|人机验证|请完成验证|403 Forbidden|403 ", re.I)
  _YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")


  def _parse_wanfang_list_html(html: str) -> list[UnifiedLiteratureEntry]:
      out: list[UnifiedLiteratureEntry] = []
      soup = BeautifulSoup(html, "html.parser")
      items = soup.select("div.result-list .paper-item") or soup.select("li.essay-item") or soup.select(".result-item")
      for item in items:
          try:
              a = item.select_one("h3.title a") or item.select_one("a.title") or item.find("a")
              if not a:
                  continue
              title = a.get_text(" ", strip=True)
              href = a.get("href", "")
              # href: /periodical/zhszb202402011
              m = re.search(r"/(periodical|conference|thesis|degree)/([^/?#]+)", href)
              source_record_id = m.group(2) if m else None

              authors_el = item.select_one("div.authors") or item.select_one(".author")
              authors = authors_el.get_text(" ", strip=True) if authors_el is not None else ""

              src_el = item.select_one("div.source-year") or item.select_one(".journal-info")
              journal = ""
              year: int | None = None
              if src_el is not None:
                  s = src_el.get_text(" ", strip=True)
                  m_j = re.search(r"《([^》]+)》", s)
                  if m_j:
                      journal = m_j.group(1).strip()
                  m_y = _YEAR_RE.search(s)
                  if m_y:
                      year = int(m_y.group(0))

              abs_el = item.select_one("div.abstract") or item.select_one(".abstract-text")
              abstract = abs_el.get_text(" ", strip=True) if abs_el is not None else ""

              out.append(UnifiedLiteratureEntry(
                  doi="",
                  pmid="",
                  title=title,
                  authors=authors,
                  journal=journal,
                  year=year,
                  abstract=abstract,
                  source_key="wanfang",
                  source_record_id=source_record_id,
              ))
          except Exception:
              continue
      return out


  async def _fetch_wanfang_html(boolean_text: str, timeout_s: float = 20.0) -> str:
      url = f"https://s.wanfangdata.com.cn/paper?q={quote(boolean_text)}"
      async with httpx.AsyncClient(timeout=httpx.Timeout(timeout_s), follow_redirects=True) as client:
          r = await client.get(url, headers=_HEADERS)
          r.raise_for_status()
          return r.text


  class WanfangAdapter:
      source_key = "wanfang"

      async def run_search(
          self, query: NormalizedSearchQuery, ctx: SearchRunContext
      ) -> AdapterResult:
          mode = _resolve_mode("wanfang", ctx)
          rps = ctx.rate_limit_rps.get("wanfang", 0.3)
          await asyncio.sleep(1.0 / max(rps, 0.05) + random.uniform(0.0, 1.5))

          if mode == "force_mock":
              if not INJECTED_DATASET:
                  return AdapterResult(None, [], ["Wanfang mode=force_mock 但 INJECTED_DATASET 未注册，返回 0 条"])
              out = [
                  UnifiedLiteratureEntry(
                      doi=(r.doi or "").strip().lower(), pmid=(r.pmid or "").strip(),
                      title=(r.title or "").strip(), authors=r.authors,
                      journal=r.journal, year=r.year, abstract=r.abstract,
                      source_key="wanfang", source_record_id=r.source_record_id,
                  )
                  for r in INJECTED_DATASET
              ]
              return AdapterResult(hits_on_source=len(out), records=out, warnings=[])

          try:
              html = await _fetch_wanfang_html(query.boolean_text)
              if _BANNED_PATTERNS.search(html):
                  raise RuntimeError("Wanfang 返回了验证码/被封禁页面")
              parsed = _parse_wanfang_list_html(html)
              if len(parsed) == 0:
                  raise RuntimeError("Wanfang 解析到 0 条记录")
              return AdapterResult(
                  hits_on_source=len(parsed),
                  records=parsed,
                  warnings=[f"Wanfang 公开检索成功 {len(parsed)} 条（粗检索首页）"],
              )
          except Exception as exc:
              if mode == "force_real":
                  raise
              if INJECTED_DATASET:
                  out = [
                      UnifiedLiteratureEntry(
                          doi=(r.doi or "").strip().lower(), pmid=(r.pmid or "").strip(),
                          title=(r.title or "").strip(), authors=r.authors,
                          journal=r.journal, year=r.year, abstract=r.abstract,
                          source_key="wanfang", source_record_id=r.source_record_id,
                      )
                      for r in INJECTED_DATASET
                  ]
                  return AdapterResult(
                      hits_on_source=len(out), records=out,
                      warnings=[f"Wanfang 真抓失败 ({exc.__class__.__name__}: {exc})，fallback 注入数据 {len(out)} 条"],
                  )
              return AdapterResult(
                  hits_on_source=None, records=[],
                  warnings=[f"Wanfang 真抓失败 ({exc.__class__.__name__}: {exc})，且未注册 INJECTED_DATASET，返回 0 条"],
              )
  ```

- [ ] **Step 3: 跑 wanfang 解析测试 → PASS**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_real_cnki_wanfang_parse.py::test_parse_wanfang_stub_1_record -v 2>&1 | Select-Object -Last 8`
  Expected: `1 passed`

- [ ] **Step 4: 回归 search_run_api 万方断言**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_search_run_api.py tests/test_search_worker.py tests/test_bm25_scoring.py -v 2>&1 | Select-Object -Last 10`
  Expected: all PASS（force_mock 模式下与原行为等价）

- [ ] **Step 5: Commit**
  ```bash
  git add apps/agent-core/app/services/sources/wanfang_adapter.py
  git commit -m "feat(wanfang): prefer_real scraper + INJECTED_DATASET fallback"
  ```

---

### Task 5: 新增 fallback + force_real 测试（tests/test_real_search_fallback.py）

**Files:**
- Create: `apps/agent-core/tests/test_real_search_fallback.py`

- [ ] **Step 1: 写 fallback + force_real 两条测试**
  ```python
  """Fallback behavior tests (offline, httpx monkeypatch)."""
  import pytest
  from app.services.sources.cnki_adapter import CnkiAdapter, INJECTED_DATASET as CNKI_INJ
  from app.services.sources.wanfang_adapter import WanfangAdapter
  from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext, UnifiedLiteratureEntry


  def _ctx_with_mode(**modes):
      return SearchRunContext(project_id=1, search_run_id=1, rate_limit_rps={"cnki":0.3,"wanfang":0.3}, adapter_modes=dict(**modes))


  def test_prefer_real_falls_back_on_connect_error(monkeypatch):
      """CNKI 抓源时 ConnectError → 返回 INJECTED_DATASET copy + warnings 含『回退到注入』."""
      import httpx

      # 先塞注入集（conftest 的 inject helper 这里不想引就直接 setattr）
      stub_entries = [UnifiedLiteratureEntry(doi="10.1/cnki1", pmid="", title="CNKI-stub-title",
          authors="A", journal="J", year=2024, abstract="X", source_key="cnki", source_record_id="c1")]
      monkeypatch.setattr("app.services.sources.cnki_adapter.INJECTED_DATASET", stub_entries)
      # 设定 prefer_real（覆盖 autouse 的 env force_mock）
      monkeypatch.setenv("MEDA_CNKI_MODE", "prefer_real")

      # monkeypatch httpx.AsyncClient.get → ConnectError
      import asyncio
      async def fake_get(*a, **kw):
          raise httpx.ConnectError("network unreachable")

      monkeypatch.setattr("httpx.AsyncClient.get", fake_get)

      # monkeypatch asyncio.sleep 避免真等
      monkeypatch.setattr("app.services.sources.cnki_adapter.asyncio.sleep", lambda *_a, **_kw: None)

      result = asyncio.run(CnkiAdapter().run_search(
          NormalizedSearchQuery(boolean_text="二甲双胍 SGLT2", filters={}, source_key="cnki"),
          _ctx_with_mode(),
      ))
      assert len(result.records) == 1
      assert result.records[0].title == "CNKI-stub-title"
      assert any("fallback 注入数据 1 条" in w for w in result.warnings), result.warnings


  def test_force_real_propagates_exception(monkeypatch):
      """mode=force_real 下 CNKI ConnectError 直接 raise，不 fallback，也不吞 warning."""
      import httpx, asyncio

      stub_entries = [UnifiedLiteratureEntry(doi="", pmid="", title="stub", authors="", journal="", year=2024, abstract="", source_key="cnki", source_record_id="x")]
      monkeypatch.setattr("app.services.sources.cnki_adapter.INJECTED_DATASET", stub_entries)
      monkeypatch.setenv("MEDA_CNKI_MODE", "force_real")

      async def fake_get(*a, **kw):
          raise httpx.ConnectError("network down")

      monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
      monkeypatch.setattr("app.services.sources.cnki_adapter.asyncio.sleep", lambda *_a, **_kw: None)

      with pytest.raises(httpx.ConnectError):
          asyncio.run(CnkiAdapter().run_search(
              NormalizedSearchQuery(boolean_text="X", filters={}, source_key="cnki"),
              _ctx_with_mode(),
          ))
  ```

- [ ] **Step 2: 跑测试 → 看是否 PASS**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/test_real_search_fallback.py -v 2>&1 | Select-Object -Last 12`
  Expected: `2 passed`。如果因 asyncio.run 导入问题（RuntimeError: Event loop 嵌套），改用 `pytest-asyncio` 标记；项目目前没引 pytest-asyncio，可改为把 async 部分用 sync 包装。若嵌套报错，修改测试用：`loop = asyncio.new_event_loop(); asyncio.set_event_loop(loop); result = loop.run_until_complete(...)`

- [ ] **Step 3: Commit**
  ```bash
  git add apps/agent-core/tests/test_real_search_fallback.py
  git commit -m "test: prefer_real fallback / force_real propagation tests"
  ```

---

### Task 6: (可选) needs_network 3 条手动测试

**Files:** Create `apps/agent-core/tests/test_needs_network_pubmed.py` + `test_needs_network_cnki_wanfang.py`

- [ ] **Step 1: 写 test_needs_network_pubmed.py**
  ```python
  import pytest
  pytest.importorskip("httpx")

  @pytest.mark.needs_network
  def test_pubmed_real_dapagliflozin_10_hits(monkeypatch):
      import asyncio
      monkeypatch.setenv("MEDA_PUBMED_MODE", "prefer_real")
      monkeypatch.delenv("MEDA_PUBMED_MODE", raising=False)  # 清掉 autouse fixture 默认 force_mock
      monkeypatch.setenv("MEDA_PUBMED_MODE", "prefer_real")

      from app.services.sources.pubmed_adapter import PubMedAdapter
      from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext
      monkeypatch.setattr("app.services.sources.pubmed_adapter._resolve_mode", lambda *_a, **_kw: "prefer_real")

      res = asyncio.run(PubMedAdapter().run_search(
          NormalizedSearchQuery(boolean_text="dapagliflozin chronic kidney disease", filters={"study_type":["rct"]}, source_key="pubmed"),
          SearchRunContext(project_id=1, search_run_id=1, rate_limit_rps={"pubmed":3.0}, pubmed_api_key=None),
      ))
      assert res.hits_on_source is None or res.hits_on_source >= 1
      titles = [r.title for r in res.records if r.title]
      # 至少 1 条非空
      assert len(titles) >= 1, f"titles empty; warnings={res.warnings}"
  ```

- [ ] **Step 2: 写 test_needs_network_cnki_wanfang.py（同构）**
  同上，CNKI/万方，prefer_real，允许 fallback；断言 `len(records)>=1 或 任何 warning 含 "fallback 注入"`

- [ ] **Step 3: pytest 默认不执行；手动触发时执行**
  Run 默认：`uv run python -m pytest tests/ -v 2>&1 | Select-String "needs_network"` → 无匹配，证明默认 skip

- [ ] **Step 4: Commit（可选）**
  ```bash
  git add apps/agent-core/tests/test_needs_network_*.py
  git commit -m "test: add needs_network markers for manual real-HTTP check"
  ```

---

### Task 7: 最终全量回归（125 baseline + 新增 7~9 tests）

- [ ] **Step 1: 全 6 端跑回归**
  ```powershell
  echo "=== agent-core ==="
  cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/ --no-header --tb=short 2>&1 | Select-Object -Last 5
  echo "=== shared-sdk ==="
  cd d:\workspace\MedA\packages\shared-sdk ; npx vitest run 2>&1 | Select-String "Tests "
  echo "=== shared-ui ==="
  cd d:\workspace\MedA\packages\shared-ui ; npx vitest run 2>&1 | Select-String "Tests "
  echo "=== web ==="
  cd d:\workspace\MedA\apps\web ; npx vitest run 2>&1 | Select-String "Tests "
  echo "=== admin ==="
  cd d:\workspace\MedA\apps\admin ; npx vitest run 2>&1 | Select-String "Tests "
  echo "=== desktop ==="
  cd d:\workspace\MedA\apps\desktop ; npx vitest run 2>&1 | Select-String "Tests "
  ```
  Expected agent-core ≥ **132 passed** (125 baseline + test_real_pubmed_xml_parse 2 + test_real_cnki_wanfang_parse 2 + test_real_search_fallback 2 + needs_network 默认 skip，共 132)；其余 shared-ui 36 / shared-sdk 27 / web 5 / admin 1 / desktop 5 不变。

- [ ] **Step 2: 确认目标达成 → 199+7=206 passed**
  （如果 Task 6 needs_network 3 条也进 commit 但默认 skip，则总数统计不变）

- [ ] **Step 3: 可选手动 needs_network 一次（确认真链路）**
  Run: `cd d:\workspace\MedA\apps\agent-core ; uv run python -m pytest tests/ -m needs_network -v --tb=short 2>&1 | Select-Object -Last 20`

- [ ] **Step 4: Commit（最终汇总）**
  ```bash
  git commit --allow-empty -m "test(real-adapters): post-landing full regression ≥ 206"
  ```
