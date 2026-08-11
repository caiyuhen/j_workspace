from __future__ import annotations

from app.services.sources import get_source_adapter
from app.services.sources.protocol import (
    AdapterResult,
    NormalizedSearchQuery,
    SearchRunContext,
    SourceAdapter,
)


async def _run(adapter: SourceAdapter) -> AdapterResult:
    ctx = SearchRunContext(
        project_id=1,
        search_run_id=1,
        rate_limit_rps={"pubmed": 3, "cnki": 3, "wanfang": 3},
    )
    query = NormalizedSearchQuery(
        boolean_text="(Metformin[Mesh] OR SGLT2i[Title/Abstract]) AND 2022:2024[Date - Publication]",
        filters={"language": ["chinese","english"], "study_type": ["rct"]},
        source_key=adapter.source_key,
    )
    return await adapter.run_search(query, ctx)


def test_adapter_factory_returns_3_sources() -> None:
    assert get_source_adapter("pubmed").source_key == "pubmed"
    assert get_source_adapter("cnki").source_key == "cnki"
    assert get_source_adapter("wanfang").source_key == "wanfang"


def test_cnki_stub_returns_zero_with_warning_when_mock_not_injected(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "app.services.sources.cnki_adapter.INJECTED_DATASET", [], raising=False
    )
    import asyncio
    res = asyncio.run(_run(get_source_adapter("cnki")))
    assert res.records == []
    assert any("stub" in w.lower() or "mock" in w.lower() for w in res.warnings)


def test_wanfang_stub_returns_zero_with_warning(monkeypatch) -> None:
    monkeypatch.setattr(
        "app.services.sources.wanfang_adapter.INJECTED_DATASET", [], raising=False
    )
    import asyncio
    res = asyncio.run(_run(get_source_adapter("wanfang")))
    assert res.records == []
    assert len(res.warnings) >= 1


def test_pubmed_monkeypatch_parses_entries(monkeypatch) -> None:
    """把 PubMed adapter 的 HTTP 层替换成本地 fixture，模拟 esearch/efetch 往返两次。"""
    from tests.conftest import MOCK_PUBMED_DATASET
    import asyncio

    # 用 monkeypatch 直接跳过 httpx，让 esearch_ids 返回 [1..N]，efetch_xml 反序列化成 UnifiedLiteratureEntry
    esearch_ids = [e.source_record_id or str(i) for i, e in enumerate(MOCK_PUBMED_DATASET, 1)]

    async def fake_fetch(_q, _ctx):
        return esearch_ids, len(MOCK_PUBMED_DATASET)
    async def fake_parse(_ids):
        return MOCK_PUBMED_DATASET

    monkeypatch.setattr(
        "app.services.sources.pubmed_adapter._esearch_pubmed_ids", fake_fetch
    )
    monkeypatch.setattr(
        "app.services.sources.pubmed_adapter._efetch_parse_entries", fake_parse
    )

    result = asyncio.run(_run(get_source_adapter("pubmed")))
    assert result.hits_on_source == len(MOCK_PUBMED_DATASET)
    assert len(result.records) == len(MOCK_PUBMED_DATASET)
    # 首条 DOI/PMID/标题规范化（DOI 小写、strip，标题 strip）
    first = result.records[0]
    assert first.doi == first.doi.lower()
    assert "\n" not in first.title
    assert first.source_key == "pubmed"
