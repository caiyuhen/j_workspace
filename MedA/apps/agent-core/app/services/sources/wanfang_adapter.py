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


def _is_login_required_html(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    if soup.select_one("div.login-modal-mask"):
        return True
    if soup.select_one("div.login-box") or soup.select_one(".login-modal"):
        if "万方数据知识服务平台" in html and "请登录后查看更多结果" in html:
            return True
    if "请登录" in html and ("登录" in html[:3000]):
        if soup.select_one(".login-modal-mask") or soup.select_one("#loginframe"):
            return True
    return False


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
