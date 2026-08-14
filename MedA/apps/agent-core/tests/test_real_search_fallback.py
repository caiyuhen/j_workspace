"""Fallback behavior tests (offline, httpx monkeypatch)."""
import asyncio

import httpx
import pytest

from app.services.sources.cnki_adapter import CnkiAdapter
from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext, UnifiedLiteratureEntry


def _ctx_with_mode(**modes):
    return SearchRunContext(
        project_id=1,
        search_run_id=1,
        rate_limit_rps={"cnki": 0.3, "wanfang": 0.3},
        adapter_modes=dict(**modes),
    )


async def _fake_sleep(*_a, **_kw):
    return None


def test_prefer_real_falls_back_on_connect_error(monkeypatch):
    """prefer_real + httpx ConnectError → fallback INJECTED_DATASET 返回 1 条 + warnings 含『fallback 注入数据 1 条』."""
    stub_entries = [
        UnifiedLiteratureEntry(
            doi="10.1/cnki1",
            pmid="",
            title="CNKI-stub-title",
            authors="A",
            journal="J",
            year=2024,
            abstract="X",
            source_key="cnki",
            source_record_id="c1",
        )
    ]
    monkeypatch.setattr("app.services.sources.cnki_adapter.INJECTED_DATASET", stub_entries)
    monkeypatch.setenv("MEDA_CNKI_MODE", "prefer_real")

    async def fake_get(*a, **kw):
        raise httpx.ConnectError("network unreachable")

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    monkeypatch.setattr("app.services.sources.cnki_adapter.asyncio.sleep", _fake_sleep)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            CnkiAdapter().run_search(
                NormalizedSearchQuery(boolean_text="二甲双胍 SGLT2", filters={}, source_key="cnki"),
                _ctx_with_mode(),
            )
        )
    finally:
        loop.close()

    assert len(result.records) == 1
    assert result.records[0].title == "CNKI-stub-title"
    assert any("fallback 注入数据 1 条" in w for w in result.warnings), result.warnings


def test_force_real_propagates_exception(monkeypatch):
    """force_real + httpx ConnectError → 直接 raise 不吞，pytest.raises(httpx.ConnectError) 命中."""
    stub_entries = [
        UnifiedLiteratureEntry(
            doi="",
            pmid="",
            title="stub",
            authors="",
            journal="",
            year=2024,
            abstract="",
            source_key="cnki",
            source_record_id="x",
        )
    ]
    monkeypatch.setattr("app.services.sources.cnki_adapter.INJECTED_DATASET", stub_entries)
    monkeypatch.setenv("MEDA_CNKI_MODE", "force_real")

    async def fake_get(*a, **kw):
        raise httpx.ConnectError("network down")

    monkeypatch.setattr("httpx.AsyncClient.get", fake_get)
    monkeypatch.setattr("app.services.sources.cnki_adapter.asyncio.sleep", _fake_sleep)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        with pytest.raises(httpx.ConnectError):
            loop.run_until_complete(
                CnkiAdapter().run_search(
                    NormalizedSearchQuery(boolean_text="X", filters={}, source_key="cnki"),
                    _ctx_with_mode(),
                )
            )
    finally:
        loop.close()
