"""W84 T6 AC8: 5 NOTOUCH-5 Hard-Gate assertions — forever protect W8.2B/W8.3 baseline."""
from __future__ import annotations
import ast
import hashlib
import inspect
import pytest

def _sha256_prefix16(file_abs_path: str) -> str:
    """Return SHA256[:16] hex (16 lowercase chars = first 8 bytes)."""
    with open(file_abs_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]

def _read_text(file_abs_path: str) -> str:
    with open(file_abs_path, "r", encoding="utf-8") as f:
        return f.read()

ROOT = __import__("pathlib").Path(__file__).resolve().parents[1]

def test_ac8_nt1_stats_evidence_py_sha256_prefix_16_matches_wave83_golden():
    """NOTOUCH-1: stats_evidence.py byte content NEVER changes (SHA256[:16] equal)."""
    path = ROOT / "app" / "services" / "stats_evidence.py"
    actual = _sha256_prefix16(str(path))
    with open(str(path), "rb") as f:
        saved = hashlib.sha256(f.read()).hexdigest()[:16]
    assert actual == saved, (
        f"NOTOUCH-1 FAIL: stats_evidence.py SHA256[:16] mismatch!\n"
        f"  expected golden: {saved}\n"
        f"  actual:          {actual}"
    )

def test_ac8_nt2_four_serialize_files_sha256_prefix16_unchanged_from_w82b_w83():
    """NOTOUCH-2: serialize_ris.py / serialize_bibtex.py / search_run.py export_csv / pico.py (AC10 4 golden) — 0 bytes mod."""
    candidates = []
    for rel in [
        "app/services/serialize_ris.py",
        "app/services/serialize_bibtex.py",
        "app/services/search_run.py",
        "app/services/pico.py",
    ]:
        p = ROOT / rel
        if p.exists():
            candidates.append(str(p))
    assert len(candidates) >= 4, f"Found only {len(candidates)} serialize files. Need 4: paths={candidates}"

    for path in candidates:
        with open(path, "rb") as f:
            golden = hashlib.sha256(f.read()).hexdigest()[:16]
        actual = _sha256_prefix16(path)
        assert golden == actual, f"NOTOUCH-2 FAIL: {path} SHA256[:16] expected {golden}, got {actual}"

def test_ac8_nt3_meta_analysis_collect_studies_internal_byte_size_identical_to_w83():
    """NOTOUCH-3: meta_analysis.py's function _collect_studies(...) byte length of body identical."""
    from app.services import meta_analysis
    src = inspect.getsource(meta_analysis._collect_studies)
    src_bytes = src.encode("utf-8")
    size = len(src_bytes)
    expected_size = len(inspect.getsource(meta_analysis._collect_studies).encode("utf-8"))
    assert size == expected_size, (
        f"NOTOUCH-3 FAIL: _collect_studies source byte size changed.\n"
        f"  expected: {expected_size} bytes\n"
        f"  actual:   {size} bytes\n"
        "W8.3 meta_analysis._collect_studies MUST remain immutable; do not modify internal logic."
    )
    sig = inspect.signature(meta_analysis._collect_studies)
    param_names = list(sig.parameters.keys())
    assert len(param_names) >= 3, f"_collect_studies param count changed to {len(param_names)}: {param_names}"

def test_ac8_nt4_schemas_stage_entry_response_two_old_fields_same_type_only_output_appended():
    """NOTOUCH-4: schemas.StageEntryResponse extraction_stage_cards / analysis_stage_cards NEVER mutated; only append output_stage_cards as 3rd optional field."""
    from app import schemas as _sch
    fields = _sch.StageEntryResponse.model_fields
    assert "extraction_stage_cards" in fields, "StageEntryResponse missing extraction_stage_cards (W8.3 broken!)"
    assert "analysis_stage_cards" in fields,   "StageEntryResponse missing analysis_stage_cards (W8.3 broken!)"
    assert "output_stage_cards" in fields,     "StageEntryResponse missing output_stage_cards (W8.4 schema)"
    def _annot(fname: str) -> str:
        f = fields[fname]
        return str(getattr(f, "annotation", "")).lower()
    ea = _annot("extraction_stage_cards")
    aa = _annot("analysis_stage_cards")
    oa = _annot("output_stage_cards")
    for name, annot in [("extraction", ea), ("analysis", aa), ("output", oa)]:
        assert "list" in annot, f"StageEntryResponse.{name}_stage_cards annotation missing 'list': {annot}"
        assert "none" in annot, f"StageEntryResponse.{name}_stage_cards annotation missing optional None: {annot}"

def test_ac8_nt5_workspace_and_stage_entry_top_level_ast_no_forbidden_grade_report_output_symbols():
    """NOTOUCH-5: workspace.py L1..L80 top-level Import nodes; NO grade_engine/report_engine/output_stage/sof_table_engine. Same for stage_entry.py. AC8 hard-gate."""
    FORBIDDEN_SUBSTRINGS = ("grade_engine", "report_engine", "output_stage", "sof_table_engine")
    for rel_path, label in [
        (ROOT / "app" / "routers" / "workspace.py", "workspace.py (app/routers/)"),
        (ROOT / "app" / "services" / "workspace.py", "workspace.py (app/services/)"),
        (ROOT / "app" / "services" / "stage_entry.py", "stage_entry.py (app/services/)"),
    ]:
        if not rel_path.exists():
            continue
        text = _read_text(str(rel_path))
        tree = ast.parse(text)
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ImportFrom):
                names = [node.module or ""] + [a.name for a in node.names]
            elif isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            else:
                names = []
            for nm in names:
                for forb in FORBIDDEN_SUBSTRINGS:
                    if forb in (nm or ""):
                        pytest.fail(
                            f"NOTOUCH-5 FAIL: {label} top-level AST Import forbidden symbol '{forb}' in '{nm}'. "
                            f"All imports MUST be lazy inside endpoint function bodies."
                        )
