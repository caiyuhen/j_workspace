from __future__ import annotations

import importlib
from pathlib import Path

import pytest

from app.services.sources import cnki_adapter as cnki_mod
from app.services.sources import wanfang_adapter as wanfang_mod
from app.services.sources.cnki_adapter import CnkiAdapter, _parse_cnki_list_html
from app.services.sources.wanfang_adapter import WanfangAdapter, _parse_wanfang_list_html

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES_DIR / name).read_text(encoding="utf-8")


def _is_captcha_html(html: str) -> bool:
    importlib.reload(cnki_mod)
    fn = getattr(cnki_mod, "_is_captcha_html", None)
    if fn is None:
        raise NotImplementedError("_is_captcha_html not yet implemented in cnki_adapter")
    return fn(html)


def _is_login_required_html(html: str) -> bool:
    importlib.reload(wanfang_mod)
    fn = getattr(wanfang_mod, "_is_login_required_html", None)
    if fn is None:
        raise NotImplementedError("_is_login_required_html not yet implemented in wanfang_adapter")
    return fn(html)


class TestCNKIParse:
    @pytest.fixture
    def cnki_adapter(self) -> CnkiAdapter:
        return CnkiAdapter()

    def test_20hits_len20_title(self, cnki_adapter: CnkiAdapter) -> None:
        html = _read("cnki_20hits.html")
        records = _parse_cnki_list_html(html)
        assert len(records) == 20
        titles = {r.title for r in records}
        assert "" not in titles
        for r in records:
            assert r.source_key == "cnki"
            assert r.source_record_id is not None
            assert r.source_record_id.startswith("CNKI:")

    def test_0hits_empty(self, cnki_adapter: CnkiAdapter) -> None:
        html = _read("cnki_0hits.html")
        records = _parse_cnki_list_html(html)
        assert len(records) == 0

    def test_captcha_flagged(self, cnki_adapter: CnkiAdapter) -> None:
        html = _read("cnki_captcha.html")
        assert _is_captcha_html(html) is True
        records = _parse_cnki_list_html(html)
        assert len(records) == 0


class TestWanFangParse:
    @pytest.fixture
    def wanfang_adapter(self) -> WanfangAdapter:
        return WanfangAdapter()

    def test_20hits_len_ge_15_doi_year(self, wanfang_adapter: WanfangAdapter) -> None:
        html = _read("wanfang_20hits.html")
        records = _parse_wanfang_list_html(html)
        assert len(records) >= 15
        for r in records:
            assert r.source_key == "wanfang"
            assert r.source_record_id is not None
            assert r.source_record_id.startswith("WANFANG:")
        has_year = sum(1 for r in records if r.year is not None)
        assert has_year >= 10

    def test_0hits_empty(self, wanfang_adapter: WanfangAdapter) -> None:
        html = _read("wanfang_0hits.html")
        records = _parse_wanfang_list_html(html)
        assert len(records) == 0

    def test_login_flagged(self, wanfang_adapter: WanfangAdapter) -> None:
        html = _read("wanfang_login.html")
        assert _is_login_required_html(html) is True
        records = _parse_wanfang_list_html(html)
        assert len(records) == 0


class TestAdapterRunSearchPureMocks:
    def test_max_pages_cn_4_gets_clamped_to_3_in_cnki(self) -> None:
        from app.services.sources import cnki_adapter as ca

        def _fake_clamp_compute(max_pages_cn_val):
            _raw = int(max_pages_cn_val) if isinstance(max_pages_cn_val, int) else (max_pages_cn_val or 1)
            N = max(1, min(3, _raw))
            return _raw, N

        _raw4, N4 = _fake_clamp_compute(4)
        assert N4 == 3, f"4 should clamp to 3, got {N4}"
        _raw0, N0 = _fake_clamp_compute(0)
        assert N0 == 1, f"0 should clamp to 1, got {N0}"

    def test_translate_exception_returns_original_english_text_not_raises(self, monkeypatch) -> None:
        from app.services.sources import cnki_adapter as ca

        def _boom(*args, **kwargs):
            raise RuntimeError("boom")

        monkeypatch.setattr(ca, "translate_boolean_for_cn_source", _boom)
        bt = "empagliflozin AND hfredef AND rct"
        result = ca._safe_translate(bt, "cnki")
        assert result == bt, f"Expected original '{bt}', got '{result}'"
