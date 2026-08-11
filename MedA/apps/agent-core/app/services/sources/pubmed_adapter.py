from __future__ import annotations

import asyncio
from typing import Iterable

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
    """Low-level helper (module-level so tests can monkeypatch).

    Signature: (pmids) -> list[UnifiedLiteratureEntry]
    Tests monkeypatch this directly with fixture entries. The real
    HTTP path is a placeholder in Wave 8: it issues a smoke HTTP call
    (using a transient client) but returns an empty list — the real
    XML → UnifiedLiteratureEntry parser comes in a follow-up commit.
    """
    ids = list(pmids)
    if not ids:
        return []
    # Real impl will paginate over ids in `chunk` batches and parse XML.
    # Placeholder branch for non-monkeypatched path:
    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
        params = {"db": "pubmed", "id": ",".join(ids), "retmode": "xml"}
        _ = await client.get(EFETCH_URL, params=params)  # smoke call
    return []  # Follow-up commit: implement XML → entries parser


class PubMedAdapter:
    source_key = "pubmed"

    async def run_search(
        self, query: NormalizedSearchQuery, ctx: SearchRunContext
    ) -> AdapterResult:
        # Minimal rate limit sleep based on rps
        rps = ctx.rate_limit_rps.get("pubmed", 3.0)
        await asyncio.sleep(1.0 / max(rps, 0.1))

        ids, count = await _esearch_pubmed_ids(query, ctx)
        entries = await _efetch_parse_entries(ids)

        # Enforce DOI lower case + strip, title strip regardless of whether efetch filled them.
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
                "PubMed esearch returned IDs but XML efetch → entries parser "
                "is a placeholder in Wave 8. Inject monkeypatch for tests."
            )
        return AdapterResult(hits_on_source=count, records=normalized, warnings=warnings)
