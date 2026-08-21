from __future__ import annotations

import sys
import types

import pytest

from app.services.pipeline_engine import VALID_PRESETS, create_pipeline_run


_PRESET_SIZES = {
    "sglt2i_ckd": 178,
    "empagliflozin_hf": 132,
    "glp1_weightloss": 188,
    "liraglutide_nafld": 112,
    "pkd_tolvaptan": 74,
    "ckd_blood_pressure_control": 156,
}


def _import_wrapper():
    from app.services.sources.pubmed_adapter import search_records_wrapper
    return search_records_wrapper


def _make_fake_requests_module(get_fn=None):
    """Build a fake requests module with exceptions classes so `import requests as _req` works inside wrapper."""
    fake_requests = types.ModuleType("requests")

    class _ReqBaseException(Exception):
        pass

    class _RequestException(_ReqBaseException):
        pass

    class _ConnectionError(_RequestException):
        pass

    class _TimeoutError(_RequestException):
        pass

    fake_exceptions = types.ModuleType("requests.exceptions")
    fake_exceptions.RequestException = _RequestException
    fake_exceptions.ConnectionError = _ConnectionError
    fake_exceptions.Timeout = _TimeoutError
    fake_requests.exceptions = fake_exceptions

    def _default_get(*args, **kwargs):
        raise _ConnectionError("default fake network error")

    fake_requests.get = get_fn if get_fn is not None else _default_get
    return fake_requests, fake_exceptions


def _inject_fake_requests(monkeypatch, get_fn=None):
    fake_req, fake_exc = _make_fake_requests_module(get_fn)
    monkeypatch.setitem(sys.modules, "requests", fake_req)
    monkeypatch.setitem(sys.modules, "requests.exceptions", fake_exc)
    return fake_req


def test_H1_sglt2i_ckd_snapshot():
    search_records_wrapper = _import_wrapper()
    preset = "sglt2i_ckd"
    records, resolved = search_records_wrapper(preset, mode="snapshot")
    assert resolved == "snapshot"
    assert 1 <= len(records) <= 200
    assert len(records) == _PRESET_SIZES[preset]
    for r in records:
        assert r["source"] == f"snapshot:{preset}"
        assert "nct_id" in r
        assert r["nct_id"].startswith("NCT")


def test_H2_empagliflozin_hf_snapshot():
    search_records_wrapper = _import_wrapper()
    preset = "empagliflozin_hf"
    records, resolved = search_records_wrapper(preset, mode="snapshot")
    assert resolved == "snapshot"
    assert 1 <= len(records) <= 200
    assert len(records) == _PRESET_SIZES[preset]
    for r in records:
        assert r["source"] == f"snapshot:{preset}"


def test_H3_glp1_weightloss_snapshot():
    search_records_wrapper = _import_wrapper()
    preset = "glp1_weightloss"
    records, resolved = search_records_wrapper(preset, mode="snapshot")
    assert resolved == "snapshot"
    assert 1 <= len(records) <= 200
    assert len(records) == _PRESET_SIZES[preset]
    for r in records:
        assert r["source"] == f"snapshot:{preset}"


def test_H4_liraglutide_nafld_snapshot():
    search_records_wrapper = _import_wrapper()
    preset = "liraglutide_nafld"
    records, resolved = search_records_wrapper(preset, mode="snapshot")
    assert resolved == "snapshot"
    assert 1 <= len(records) <= 200
    assert len(records) == _PRESET_SIZES[preset]
    for r in records:
        assert r["source"] == f"snapshot:{preset}"


def test_H5_pkd_tolvaptan_snapshot():
    search_records_wrapper = _import_wrapper()
    preset = "pkd_tolvaptan"
    records, resolved = search_records_wrapper(preset, mode="snapshot")
    assert resolved == "snapshot"
    assert 1 <= len(records) <= 200
    assert len(records) == _PRESET_SIZES[preset]
    for r in records:
        assert r["source"] == f"snapshot:{preset}"


def test_H6_ckd_blood_pressure_control_snapshot():
    search_records_wrapper = _import_wrapper()
    preset = "ckd_blood_pressure_control"
    records, resolved = search_records_wrapper(preset, mode="snapshot")
    assert resolved == "snapshot"
    assert 1 <= len(records) <= 200
    assert len(records) == _PRESET_SIZES[preset]
    for r in records:
        assert r["source"] == f"snapshot:{preset}"


def test_H7_live_connection_error_falls_back_to_snapshot(monkeypatch):
    search_records_wrapper = _import_wrapper()

    call_log = []

    def _fake_get(*args, **kwargs):
        call_log.append(("called", args, kwargs))
        fake_req_mod = sys.modules["requests"]
        raise fake_req_mod.exceptions.ConnectionError("fake network down (test H7)")

    _inject_fake_requests(monkeypatch, _fake_get)

    records, resolved = search_records_wrapper("sglt2i_ckd", mode="live")
    assert resolved == "snapshot-fallback-after-live-failed"
    assert len(call_log) >= 1
    assert 1 <= len(records) <= 200
    for r in records:
        assert r["source"].startswith("snapshot:")


class _Fake429Response:
    status_code = 429
    def raise_for_status(self):
        pass
    def json(self):
        return {"esearchresult": {"idlist": [], "count": "0"}}


def test_H8_live_429_triggers_fallback(monkeypatch):
    search_records_wrapper = _import_wrapper()

    call_counter = {"n": 0}

    def _fake_get_429(*args, **kwargs):
        call_counter["n"] += 1
        return _Fake429Response()

    _inject_fake_requests(monkeypatch, _fake_get_429)

    records, resolved = search_records_wrapper("sglt2i_ckd", mode="live")
    assert resolved == "snapshot-fallback-after-live-failed"
    assert call_counter["n"] >= 1
    assert 1 <= len(records) <= 200


def test_H9_snapshot_never_calls_requests_get(monkeypatch):
    search_records_wrapper = _import_wrapper()

    call_log = []

    def _spying_get(*args, **kwargs):
        call_log.append(("called", args, kwargs))
        fake_req_mod = sys.modules["requests"]
        raise fake_req_mod.exceptions.ConnectionError("should not be called in snapshot mode")

    _inject_fake_requests(monkeypatch, _spying_get)

    records, resolved = search_records_wrapper("sglt2i_ckd", mode="snapshot")
    assert resolved == "snapshot"
    assert len(records) > 0
    assert len(call_log) == 0


def test_H10_max_records_201_assertion_error():
    search_records_wrapper = _import_wrapper()
    with pytest.raises(AssertionError):
        search_records_wrapper("sglt2i_ckd", mode="snapshot", max_records=201)


def test_H11_create_pipeline_run_id_starts_with_p(db_session):
    import uuid
    wid = f"ws-test-{uuid.uuid4().hex[:8]}"
    r = create_pipeline_run(wid, "sglt2i_ckd")
    assert r.id.startswith("p-")
    assert len(r.id) >= 3


def test_H12_invalid_preset_assertion_error():
    search_records_wrapper = _import_wrapper()
    with pytest.raises(AssertionError):
        search_records_wrapper("invalid_preset_xxx", mode="snapshot")


def test_H13_invalid_mode_assertion_error():
    search_records_wrapper = _import_wrapper()
    with pytest.raises(AssertionError):
        search_records_wrapper("sglt2i_ckd", mode="invalid_mode_xx")


def test_H14_snapshot_deterministic_same_len_and_nct_ids():
    search_records_wrapper = _import_wrapper()
    preset = "sglt2i_ckd"

    records1, _ = search_records_wrapper(preset, mode="snapshot")
    records2, _ = search_records_wrapper(preset, mode="snapshot")

    assert len(records1) == len(records2)

    nct_ids_1 = [r["nct_id"] for r in records1]
    nct_ids_2 = [r["nct_id"] for r in records2]

    assert nct_ids_1 == nct_ids_2

    ids_1 = [r["id"] for r in records1]
    ids_2 = [r["id"] for r in records2]
    assert ids_1 == ids_2

    titles_1 = [r["title"] for r in records1]
    titles_2 = [r["title"] for r in records2]
    assert titles_1 == titles_2
