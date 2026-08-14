"""Real-network PubMed test: dapagliflozin chronic kidney disease RCT.

Marked @pytest.mark.needs_network. Default pytest run (no -m) skips this.
Run manually: uv run python -m pytest tests/ -m needs_network -v
"""
import asyncio

import pytest

pytest.importorskip("httpx")


async def _fake_sleep(*_a, **_kw):
    return None


@pytest.mark.needs_network
def test_pubmed_real_dapagliflozin_ckd_rct_has_nonempty_title(monkeypatch):
    """PubMed dapagliflozin chronic kidney disease (RCT filter) -> at least 1 non-empty title."""
    monkeypatch.setenv("MEDA_PUBMED_MODE", "prefer_real")
    monkeypatch.setattr("app.services.sources.pubmed_adapter.asyncio.sleep", _fake_sleep)

    from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext
    from app.services.sources.pubmed_adapter import PubMedAdapter

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        res = loop.run_until_complete(
            PubMedAdapter().run_search(
                NormalizedSearchQuery(
                    boolean_text="dapagliflozin chronic kidney disease",
                    filters={"study_type": ["rct"]},
                    source_key="pubmed",
                ),
                SearchRunContext(
                    project_id=1,
                    search_run_id=1,
                    rate_limit_rps={"pubmed": 3.0},
                    pubmed_api_key=None,
                ),
            )
        )
    finally:
        loop.close()

    titles = [r.title for r in res.records if (r.title or "").strip()]
    assert len(titles) >= 1, (
        f"Expected >=1 non-empty title; got {len(titles)} titles, "
        f"records={len(res.records)}, warnings={res.warnings}"
    )
