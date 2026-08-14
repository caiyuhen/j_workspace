from __future__ import annotations

import asyncio
import os
import re
from typing import Iterable
import xml.etree.ElementTree as ET

import httpx

from .protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    SourceAdapter,
    UnifiedLiteratureEntry,
)

ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

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


async def _esearch_pubmed_ids(
    query: NormalizedSearchQuery,
    ctx: SearchRunContext,
    batch_size: int = 10000,
) -> tuple[list[str], int]:
    """Low-level helper. Module-level so tests can monkeypatch.

    Real impl creates its own httpx client. Test monkeypatch replaces
    this entire function, so the signature matches what the test patch
    provides: (query, ctx) -> (ids, count).
    """
    params = {
        "db": "pubmed",
        "term": query.boolean_text,
        "retmax": str(batch_size),
        "retmode": "json",
        "usehistory": "n",
    }
    if ctx.pubmed_api_key:
        params["api_key"] = ctx.pubmed_api_key
    extra = []
    for lt in query.filters.get("language", []):
        if lt.lower() == "chinese":
            extra.append("Chinese[LA]")
        elif lt.lower() == "english":
            extra.append("English[LA]")
    if "rct" in [s.lower() for s in query.filters.get("study_type", [])]:
        extra.append("randomized controlled trial[pt]")
    if extra:
        params["term"] = f'({query.boolean_text}) AND {" AND ".join(extra)}'

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        resp = await client.get(ESEARCH_URL, params=params)
        resp.raise_for_status()
        data = resp.json()["esearchresult"]
    return list(data["idlist"]), int(data["count"])


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
