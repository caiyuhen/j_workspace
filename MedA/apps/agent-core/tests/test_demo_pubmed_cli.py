from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import types
from pathlib import Path

import httpx
import pytest

SCRIPT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = SCRIPT_DIR / "scripts" / "demo_pubmed_end2end.py"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scripts.demo_pubmed_end2end import DEMO_PRESETS_PY, run_pubmed_demo


def _wrap_pico_obj(orig_obj):
    wrapped = types.SimpleNamespace()
    for attr in ("population", "intervention", "comparison", "outcome",
                 "study_type", "extraction_method", "confidence", "record_id"):
        setattr(wrapped, attr, getattr(orig_obj, attr, None))
    setattr(wrapped, "p_text", getattr(orig_obj, "population", None) or "")
    setattr(wrapped, "i_text", getattr(orig_obj, "intervention", None) or "")
    setattr(wrapped, "c_text", getattr(orig_obj, "comparison", None) or "")
    setattr(wrapped, "o_text", getattr(orig_obj, "outcome", None) or "")
    return wrapped


def _patch_pico_for_demo():
    from app.services import pico as pico_mod
    import scripts.demo_pubmed_end2end as demo_mod

    orig_pico = pico_mod._rule_baseline_extract

    def patched(rec):
        if not hasattr(rec, "id"):
            rec.id = None
        orig = orig_pico(rec)
        return _wrap_pico_obj(orig)

    pico_mod._rule_baseline_extract = patched
    demo_mod._rule_baseline_extract = patched


def test_unknown_preset_exits_code_2():
    proc = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "nonexistent_xyz_999"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 2
    assert "Available keys:" in proc.stderr


def test_run_pubmed_demo_live_success_with_mock_pubmed_http(monkeypatch):
    from tests.test_real_pubmed_xml_parse import FIXED_PUBMED_XML
    _patch_pico_for_demo()

    async def fake_get(self, url, **kwargs):
        url_s = str(url)
        if "esearch.fcgi" in url_s:
            body_dict = {"esearchresult": {"count": "2", "idlist": ["341001", "341002"]}}
            body = json.dumps(body_dict).encode("utf-8")
            req = httpx.Request("GET", url_s)
            return httpx.Response(200, content=body, request=req)
        assert "efetch.fcgi" in url_s
        req = httpx.Request("GET", url_s)
        return httpx.Response(200, content=FIXED_PUBMED_XML.encode("utf-8"), request=req)

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    result = asyncio.run(run_pubmed_demo("sglt2i_hfredef", export_csv=False))
    assert result.raw_hits >= 2
    assert result.after_dedupe_hits >= 1
    assert result.fallback_mode is False
    assert len(result.bm25_top3) <= 3


def test_connect_error_fallback_to_injected_3_hits(monkeypatch):
    from tests.conftest import MOCK_PUBMED_DATASET
    from app.services.sources.protocol import UnifiedLiteratureEntry, AdapterResult
    _patch_pico_for_demo()

    async def fake_get(self, *args, **kwargs):
        raise httpx.ConnectError("no route to NCBI")

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    mock_entries = [
        UnifiedLiteratureEntry(
            doi=e.doi, pmid=e.pmid, title=e.title, authors=e.authors,
            journal=e.journal, year=e.year, abstract=e.abstract,
            source_key="pubmed", source_record_id=e.source_record_id,
        ) for e in MOCK_PUBMED_DATASET
    ]

    import app.services.sources.pubmed_adapter as pa_mod
    original_run_search = pa_mod.PubMedAdapter.run_search

    async def run_search_with_fallback(self, query, ctx):
        try:
            result = await original_run_search(self, query, ctx)
            if result.records:
                return result
        except Exception:
            pass
        return AdapterResult(
            hits_on_source=len(mock_entries),
            records=mock_entries,
            warnings=["fallback 注入数据 3 条"],
        )

    monkeypatch.setattr(pa_mod.PubMedAdapter, "run_search", run_search_with_fallback)

    result = asyncio.run(run_pubmed_demo("sglt2i_ckd", export_csv=False))

    assert result.fallback_mode is True
    assert result.after_dedupe_hits == 3


def test_main_json_flag_outputs_valid_json():
    script_dir_str = str(SCRIPT_DIR).replace("\\", "\\\\")
    script_path_str = str(SCRIPT_PATH).replace("\\", "\\\\")
    wrapper = f'''
import sys
import types
sys.path.insert(0, r"{script_dir_str}")
from tests.conftest import MOCK_PUBMED_DATASET
from app.services.sources.protocol import UnifiedLiteratureEntry
from app.services import pico as pico_mod
import scripts.demo_pubmed_end2end as demo_mod

_orig_pico = pico_mod._rule_baseline_extract
def _wrap_pico_obj(orig_obj):
    wrapped = types.SimpleNamespace()
    for a in ("population", "intervention", "comparison", "outcome",
              "study_type", "extraction_method", "confidence", "record_id"):
        setattr(wrapped, a, getattr(orig_obj, a, None))
    wrapped.p_text = getattr(orig_obj, "population", None) or ""
    wrapped.i_text = getattr(orig_obj, "intervention", None) or ""
    wrapped.c_text = getattr(orig_obj, "comparison", None) or ""
    wrapped.o_text = getattr(orig_obj, "outcome", None) or ""
    return wrapped
def _patched_pico(rec):
    if not hasattr(rec, "id"):
        rec.id = None
    return _wrap_pico_obj(_orig_pico(rec))
pico_mod._rule_baseline_extract = _patched_pico
demo_mod._rule_baseline_extract = _patched_pico

mock_entries = [
    UnifiedLiteratureEntry(
        doi=e.doi, pmid=e.pmid, title=e.title, authors=e.authors,
        journal=e.journal, year=e.year, abstract=e.abstract,
        source_key="pubmed", source_record_id=e.source_record_id,
    ) for e in MOCK_PUBMED_DATASET
]

import app.services.sources.pubmed_adapter as pa

async def fake_esearch(q, ctx, batch_size=10000):
    ids = [e.source_record_id or f"m{{i}}" for i, e in enumerate(mock_entries, 1)]
    return ids, len(mock_entries)

async def fake_efetch(pmids, chunk=500):
    return mock_entries

pa._esearch_pubmed_ids = fake_esearch
pa._efetch_parse_entries = fake_efetch

sys.argv = [r"{script_path_str}", "sglt2i_ckd", "--json", "--no-csv"]
from scripts.demo_pubmed_end2end import main
main()
'''
    proc = subprocess.run(
        [sys.executable, "-c", wrapper],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, f"stderr={proc.stderr}\nstdout={proc.stdout}"
    marker = "--- JSON ---"
    assert marker in proc.stdout, proc.stdout
    json_part = proc.stdout.split(marker)[1]
    obj = json.loads(json_part)
    assert obj["after_dedupe_hits"] > 0
