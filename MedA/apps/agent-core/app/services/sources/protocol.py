from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional, Protocol


@dataclass
class NormalizedSearchQuery:
    boolean_text: str
    filters: dict[str, list[str]]
    source_key: str
    max_pages_cn: Optional[Literal[1, 2, 3]] = None

    def __post_init__(self) -> None:
        if self.max_pages_cn is not None and self.max_pages_cn not in (1, 2, 3):
            raise ValueError(
                f"max_pages_cn must be 1, 2, or 3 (got {self.max_pages_cn!r})"
            )


@dataclass
class SearchRunContext:
    project_id: int
    search_run_id: int
    rate_limit_rps: dict[str, float] = field(default_factory=dict)
    pubmed_api_key: str | None = None
    adapter_modes: dict[str, Literal["prefer_real", "force_mock", "force_real"]] = field(default_factory=dict)


@dataclass
class UnifiedLiteratureEntry:
    doi: str
    pmid: str
    title: str
    authors: str
    journal: str
    year: int | None
    abstract: str
    source_key: str
    source_record_id: str | None = None


@dataclass
class AdapterResult:
    hits_on_source: int | None
    records: list[UnifiedLiteratureEntry]
    warnings: list[str]
    # True when `records` come from an injected mock dataset instead of the live
    # source, so callers can persist that provenance rather than storing mock
    # rows as if they had been retrieved for real.
    is_mock: bool = False


class SourceAdapter(Protocol):
    source_key: str

    async def run_search(
        self,
        query: NormalizedSearchQuery,
        ctx: SearchRunContext,
    ) -> AdapterResult: ...
