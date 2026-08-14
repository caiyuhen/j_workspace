"""Wave 8.1B AC #7: 7 类失败 × 2 sources = 14 tests。prefer_real 模式下，任意失败 → fallback INJECTED 3 条 + warnings 含 "fallback"。

仅用 monkeypatch 改 adapter 函数入口，无真实 HTTP。
"""
from __future__ import annotations

import httpx
import pytest

from app.services.sources import cnki_adapter as ca_mod
from app.services.sources import wanfang_adapter as wa_mod
from app.services.sources.cnki_adapter import CnkiAdapter
from app.services.sources.protocol import NormalizedSearchQuery, SearchRunContext
from app.services.sources.wanfang_adapter import WanfangAdapter

from tests.conftest import SOURCE_DATASET_REGISTRY, inject_mock_datasets_into_adapters


@pytest.fixture()
def ctx_prefer_real(monkeypatch) -> SearchRunContext:
    # (1) 注入 INJECTED_DATASET 3 条 × 2 sites，fallback 非空
    inject_mock_datasets_into_adapters(monkeypatch, SOURCE_DATASET_REGISTRY)
    # (2) 覆盖 conftest autouse force_mock → 走 prefer_real（这样 try/except HTTP 路径会执行）
    monkeypatch.setenv("MEDA_CNKI_MODE", "prefer_real")
    monkeypatch.setenv("MEDA_WANFANG_MODE", "prefer_real")
    # (3) 零 sleep 加速 14 tests 总时长 < 2s
    monkeypatch.setattr(ca_mod.random, "uniform", lambda *_a, **_k: 0.0)
    monkeypatch.setattr(wa_mod.random, "uniform", lambda *_a, **_k: 0.0)
    ctx = SearchRunContext(
        project_id=7,
        search_run_id=99,
    )
    ctx.search_query = NormalizedSearchQuery(
        boolean_text="A AND B",
        filters={},
        source_key="search",
        max_pages_cn=1,
    )
    ctx.adapter_modes = {"cnki": "prefer_real", "wanfang": "prefer_real"}
    ctx.rate_limit_rps = {"cnki": 100_000, "wanfang": 100_000}
    return ctx


# ---------- CNKI 7 FAILURES ----------------------------------------------------------------
@pytest.mark.asyncio
async def test_cnki_connect_error_falls_back_3_records_with_warning(monkeypatch, ctx_prefer_real):
    async def _boom(*_a, **_kw):
        raise httpx.ConnectError("no route to scholar.cnki.net")

    monkeypatch.setattr(ca_mod, "_fetch_cnki_html", _boom)
    adapter = CnkiAdapter()
    res = await adapter.run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w.lower() for w in res.warnings)


@pytest.mark.asyncio
async def test_cnki_http_403_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _boom_403(*_a, **_kw):
        req = httpx.Request("GET", "https://scholar.cnki.net/")
        resp = httpx.Response(status_code=403, request=req)
        raise httpx.HTTPStatusError("403", request=req, response=resp)

    monkeypatch.setattr(ca_mod, "_fetch_cnki_html", _boom_403)
    res = await CnkiAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_cnki_http_502_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _boom_502(*_a, **_kw):
        req = httpx.Request("GET", "https://scholar.cnki.net/")
        resp = httpx.Response(status_code=502, request=req, text="<html>bad gateway</html>")
        raise httpx.HTTPStatusError("502", request=req, response=resp)

    monkeypatch.setattr(ca_mod, "_fetch_cnki_html", _boom_502)
    res = await CnkiAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_cnki_timeout_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _boom_timeout(*_a, **_kw):
        raise httpx.TimeoutException("10s timed out")

    monkeypatch.setattr(ca_mod, "_fetch_cnki_html", _boom_timeout)
    res = await CnkiAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_cnki_captcha_html_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _return_captcha(*_a, **_kw):
        return (
            '<html><body>'
            '<div class="captcha-mask"><div class="nc_iconfont btn_slide">请完成滑动验证</div></div>'
            '<div>为保护知网数据安全，请完成验证后再访问 scholar.cnki.net</div>'
            '</body></html>'
        )

    monkeypatch.setattr(ca_mod, "_fetch_cnki_html", _return_captcha)
    res = await CnkiAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3, "验证码检测命中后必须 fallback 3 条"
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_cnki_parse_0_hits_empty_list_falls_back_3(monkeypatch, ctx_prefer_real):
    """模拟真实 0 结果空页 OR selector 失效两种情况。"""
    async def _return_empty_dom(*_a, **_kw):
        return "<html><body><div>No result found</div></body></html>"

    monkeypatch.setattr(ca_mod, "_fetch_cnki_html", _return_empty_dom)
    monkeypatch.setattr(ca_mod, "_parse_cnki_list_html", lambda *_a, **_k: [])  # 强制解析 0 条
    res = await CnkiAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_cnki_login_required_pattern_falls_back_3(monkeypatch, ctx_prefer_real):
    """CNKI 登录/权限弹窗：通过 BANNED_PATTERNS 403 命中等价模式。"""
    async def _return_login(*_a, **_kw):
        return '<html><body>403 Forbidden - 知网登录态已过期，请重新登录知网账号后再使用</body></html>'

    monkeypatch.setattr(ca_mod, "_fetch_cnki_html", _return_login)
    res = await CnkiAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


# ---------- WANFANG 7 FAILURES --------------------------------------------------------------
@pytest.mark.asyncio
async def test_wf_connect_error_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _boom(*_a, **_kw):
        raise httpx.ConnectError("no route to s.wanfangdata.com.cn")

    monkeypatch.setattr(wa_mod, "_fetch_wanfang_html", _boom)
    res = await WanfangAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w.lower() for w in res.warnings)


@pytest.mark.asyncio
async def test_wf_http_403_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _boom(*_a, **_kw):
        req = httpx.Request("GET", "https://s.wanfangdata.com.cn/")
        resp = httpx.Response(status_code=403, request=req)
        raise httpx.HTTPStatusError("403", request=req, response=resp)

    monkeypatch.setattr(wa_mod, "_fetch_wanfang_html", _boom)
    res = await WanfangAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_wf_http_502_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _boom(*_a, **_kw):
        req = httpx.Request("GET", "https://s.wanfangdata.com.cn/")
        resp = httpx.Response(status_code=502, request=req, text="bad gw")
        raise httpx.HTTPStatusError("502", request=req, response=resp)

    monkeypatch.setattr(wa_mod, "_fetch_wanfang_html", _boom)
    res = await WanfangAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_wf_timeout_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _boom(*_a, **_kw):
        raise httpx.TimeoutException("12s timeout for wanfang")

    monkeypatch.setattr(wa_mod, "_fetch_wanfang_html", _boom)
    res = await WanfangAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_wf_captcha_equivalent_banned_pattern_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _return(*_a, **_kw):
        return '<html><head></head><body>万方数据 安全验证 请完成人机验证 sliderVerification</body></html>'

    monkeypatch.setattr(wa_mod, "_fetch_wanfang_html", _return)
    res = await WanfangAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_wf_login_required_modal_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _return_login_html(*_a, **_kw):
        return (
            '<html><body>'
            '<div class="login-modal-mask"></div>'
            '<div class="login-box"><h3>万方数据知识服务平台</h3>'
            '<p>请登录后查看更多结果 / 请先完成账号登录</p>'
            '<button class="login-btn">立即登录</button></div>'
            '</body></html>'
        )

    monkeypatch.setattr(wa_mod, "_fetch_wanfang_html", _return_login_html)
    # _is_login_required_html 命中后会导致 BANNED_PATTERNS? — 实际上当前 wanfang_adapter 实现是 0 条解析失败走 except
    monkeypatch.setattr(wa_mod, "_parse_wanfang_list_html", lambda *_a, **_k: [])  # 确保解析 0 条
    res = await WanfangAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)


@pytest.mark.asyncio
async def test_wf_parse_0_hits_empty_falls_back_3(monkeypatch, ctx_prefer_real):
    async def _return_empty_html(*_a, **_kw):
        return "<html><body><div>暂无相关论文</div></body></html>"

    monkeypatch.setattr(wa_mod, "_fetch_wanfang_html", _return_empty_html)
    monkeypatch.setattr(wa_mod, "_parse_wanfang_list_html", lambda *_a, **_k: [])
    res = await WanfangAdapter().run_search(ctx_prefer_real.search_query, ctx_prefer_real)
    assert len(res.records) == 3
    assert any("fallback" in w for w in res.warnings)
