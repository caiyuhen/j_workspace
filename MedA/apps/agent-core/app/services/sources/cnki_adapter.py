from __future__ import annotations

import asyncio
import os
import random
import re
from typing import List
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from ._cn_dict import translate_boolean_for_cn_source
from .protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    SourceAdapter,
    UnifiedLiteratureEntry,
)
from .pubmed_adapter import _MODE_ENV_MAP, _VALID_MODES, _resolve_mode

INJECTED_DATASET: list[UnifiedLiteratureEntry] | None = None


class AdapterCaptchaError(Exception):
    """验证码且page=1无结果仅 force_real 模式抛"""
    pass


class AdapterLoginRequiredError(Exception):
    """强制登录要求 page=1 无结果"""
    pass


class AdapterParseError(Exception):
    """hits_count≥1 parse 返回 0 selector失效"""
    pass


def _safe_translate(boolean_text: str, source: str) -> str:
    try:
        return translate_boolean_for_cn_source(boolean_text, source)
    except Exception:
        return boolean_text


_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Referer": "https://scholar.cnki.net/",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
}

_BANNED_PATTERNS = re.compile(r"验证码|安全验证|人机验证|请完成验证|sliderVerification|403 Forbidden|403 ", re.I)
_YEAR_RE = re.compile(r"(19|20)\d{2}")


def _is_captcha_html(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one("div.captcha-mask"):
        return True
    if soup.select_one(".nc_iconfont.btn_slide") or soup.select_one(".btn_slide.nc_iconfont"):
        if "请完成滑动验证" in html:
            return True
    if _BANNED_PATTERNS.search(html):
        return True
    return False


def _parse_cnki_list_html(html: str) -> list[UnifiedLiteratureEntry]:
    """CNKI list page -> UnifiedLiteratureEntry[]. Selector 以 stub HTML 为准，真抓 DOM 变动时改本函数 selector 即可。"""
    out: list[UnifiedLiteratureEntry] = []
    soup = BeautifulSoup(html, "html.parser")

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
        "&txt_1_sel=SU$%25=TJ$%25=KY$%25=ZU$%25=AB$%25=AU$%25=CLC$%25=RF$%25=OP"
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

        cn_bt = _safe_translate(query.boolean_text, "cnki")
        _raw = int(query.max_pages_cn) if isinstance(getattr(query, "max_pages_cn", None), int) else (query.max_pages_cn or 1)
        N = max(1, min(3, _raw))
        warnings_list: List[str] = []
        if N != _raw:
            warnings_list.append(f"clamped max_pages_cn from {_raw} to {N}")

        try:
            html = await _fetch_cnki_html(cn_bt)
            if _BANNED_PATTERNS.search(html):
                raise RuntimeError("CNKI 返回了验证码/被封禁页面（按关键词命中）")
            parsed = _parse_cnki_list_html(html)
            hits = len(parsed) or None
            if len(parsed) == 0:
                raise RuntimeError("CNKI 解析到 0 条记录")
            return AdapterResult(
                hits_on_source=hits,
                records=parsed,
                warnings=[f"CNKI 公开检索成功 {len(parsed)} 条（粗检索首页）"] + warnings_list,
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
                        source_key="cnki", source_record_id=r.source_record_id,
                    )
                    for r in INJECTED_DATASET
                ]
                return AdapterResult(
                    hits_on_source=len(out), records=out,
                    warnings=[f"CNKI 真抓失败 ({exc.__class__.__name__}: {exc})，fallback 注入数据 {len(out)} 条"] + warnings_list,
                )
            return AdapterResult(
                hits_on_source=None, records=[],
                warnings=[f"CNKI 真抓失败 ({exc.__class__.__name__}: {exc})，且未注册 INJECTED_DATASET，返回 0 条"] + warnings_list,
            )
