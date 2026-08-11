from __future__ import annotations

from .protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    SourceAdapter,
    UnifiedLiteratureEntry,
)

INJECTED_DATASET: list[UnifiedLiteratureEntry] | None = None


class CnkiAdapter:
    source_key = "cnki"

    async def run_search(
        self, query: NormalizedSearchQuery, ctx: SearchRunContext
    ) -> AdapterResult:
        if not INJECTED_DATASET:
            return AdapterResult(
                hits_on_source=None,
                records=[],
                warnings=[
                    "CNKI adapter is a stub; real institutional API not wired yet. "
                    "Please register INJECTED_DATASET for demo/testing."
                ],
            )
        # 浅拷贝；已经是 UnifiedLiteratureEntry，保证 source_key == "cnki"
        out = [
            UnifiedLiteratureEntry(
                doi=r.doi.strip().lower(),
                pmid=r.pmid.strip(),
                title=r.title.strip(),
                authors=r.authors,
                journal=r.journal,
                year=r.year,
                abstract=r.abstract,
                source_key="cnki",
                source_record_id=r.source_record_id,
            )
            for r in INJECTED_DATASET
        ]
        return AdapterResult(
            hits_on_source=len(out),
            records=out,
            warnings=[],
        )
