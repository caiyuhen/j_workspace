import json
import os
import filecmp
import tempfile
import pytest
from app.services.serialize_ris import serialize_ris_py
from app.services.serialize_bibtex import serialize_bibtex_py

FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "export")


@pytest.fixture
def records_3():
    with open(os.path.join(FIXTURE_DIR, "sample_3entries_metadata.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def test_serialize_ris_py_matches_ts_golden(records_3):
    golden = os.path.join(FIXTURE_DIR, "sample_3entries.ris")
    out_str = serialize_ris_py(records_3, ris_utf8_bom=True)
    fd, tmp = tempfile.mkstemp(suffix=".ris")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(out_str.encode("utf-8"))
        assert filecmp.cmp(golden, tmp, shallow=False), "RIS output bytes mismatch TS golden"
    finally:
        os.unlink(tmp)


def test_serialize_ris_py_no_bom_flag(records_3):
    out_bom = serialize_ris_py(records_3, ris_utf8_bom=True)
    out_no = serialize_ris_py(records_3, ris_utf8_bom=False)
    assert out_bom.startswith("\ufeff")
    assert not out_no.startswith("\ufeff")
    assert out_no == out_bom[1:]


def test_serialize_bibtex_py_matches_ts_golden(records_3):
    golden = os.path.join(FIXTURE_DIR, "sample_3entries.bib")
    out_str = serialize_bibtex_py(records_3, cite_key_prefix="meda")
    fd, tmp = tempfile.mkstemp(suffix=".bib")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(out_str.encode("utf-8"))
        assert filecmp.cmp(golden, tmp, shallow=False), "BibTeX output bytes mismatch TS golden"
    finally:
        os.unlink(tmp)
