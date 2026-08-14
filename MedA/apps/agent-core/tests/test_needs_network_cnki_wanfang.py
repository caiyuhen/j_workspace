"""Real-network CNKI + Wanfang tests with fallback allowed.

Marked @pytest.mark.needs_network. Default pytest run (no -m) skips these.
Assert len(records)>=1 OR any warning contains "fallback 注入" (i.e. anti-crawl triggered fallback to INJECTED_DATASET).
"""
import asyncio

import pytest

pytest.importorskip("httpx")


async def _fake_sleep(*_a, **_kw):
    return None


@pytest.mark.needs_network
def test_cnki_real_metformin_sglt2_allow_fallback(monkeypatch):
    """CNKI '二甲双胍 SGLT2' -> len(records)>=1 或 warning 含 'fallback 注入'."""
    monkeypatch.setenv("MEDA_CNKI_MODE", "prefer_real")
    monkeypatch.setattr("app.services.sources.cnki_adapter.asyncio.sleep", _fake_sleep)

    from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext
    from app.services.sources.cnki_adapter import CnkiAdapter
    from tests.conftest import MOCK_CNKI_DATASET, inject_mock_datasets_into_adapters

    inject_mock_datasets_into_adapters(monkeypatch, {"cnki": MOCK_CNKI_DATASET})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        res = loop.run_until_complete(
            CnkiAdapter().run_search(
                NormalizedSearchQuery(
                    boolean_text="二甲双胍 SGLT2",
                    filters={},
                    source_key="cnki",
                ),
                SearchRunContext(
                    project_id=1,
                    search_run_id=1,
                    rate_limit_rps={"cnki": 0.3},
                ),
            )
        )
    finally:
        loop.close()

    ok_len = len(res.records) >= 1
    ok_warn = any("fallback 注入" in w for w in res.warnings)
    assert ok_len or ok_warn, (
        f"CNKI: len(records)={len(res.records)}, warnings={res.warnings}. "
        f"Expected len>=1 OR warning contains 'fallback 注入'."
    )


@pytest.mark.needs_network
def test_wanfang_real_dapagliflozin_safety_meta_allow_fallback(monkeypatch):
    """Wanfang '达格列净 安全性 Meta' -> len(records)>=1 或 warning 含 'fallback 注入'."""
    monkeypatch.setenv("MEDA_WANFANG_MODE", "prefer_real")
    monkeypatch.setattr("app.services.sources.wanfang_adapter.asyncio.sleep", _fake_sleep)

    from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext
    from app.services.sources.wanfang_adapter import WanfangAdapter
    from tests.conftest import MOCK_WANFANG_DATASET, inject_mock_datasets_into_adapters

    inject_mock_datasets_into_adapters(monkeypatch, {"wanfang": MOCK_WANFANG_DATASET})

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        res = loop.run_until_complete(
            WanfangAdapter().run_search(
                NormalizedSearchQuery(
                    boolean_text="达格列净 安全性 Meta",
                    filters={},
                    source_key="wanfang",
                ),
                SearchRunContext(
                    project_id=1,
                    search_run_id=1,
                    rate_limit_rps={"wanfang": 0.3},
                ),
            )
        )
    finally:
        loop.close()

    ok_len = len(res.records) >= 1
    ok_warn = any("fallback 注入" in w for w in res.warnings)
    assert ok_len or ok_warn, (
        f"Wanfang: len(records)={len(res.records)}, warnings={res.warnings}. "
        f"Expected len>=1 OR warning contains 'fallback 注入'."
    )
