import hashlib
import sys
import os
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = ROOT

BASELINE_SHA_PREFIX = {
    "serialize_ris.py": "596988705bb3dda4",
    "serialize_bibtex.py": "078c426e4250698e",
    "search_run.py": "25a106b4fd5f4c78",
    "pico.py": "3393c9dd936316ed",
}


def _sha256_prefix(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha256(data).hexdigest()[:16]


class TestT11AC10HardGate:
    def test_t11_ac10_01_sha256_4_serialize_match_82A_baseline(self):
        files_map = {
            "serialize_ris.py": APPS_DIR / "app" / "services" / "serialize_ris.py",
            "serialize_bibtex.py": APPS_DIR / "app" / "services" / "serialize_bibtex.py",
            "search_run.py": APPS_DIR / "app" / "services" / "search_run.py",
            "pico.py": APPS_DIR / "app" / "services" / "pico.py",
        }
        actual_shas = {}
        for key, p in files_map.items():
            assert p.exists(), f"Missing file: {p}"
            actual_shas[key] = _sha256_prefix(p)

        print("\n=== ACTUAL 8.2A BASELINE SHA256 PREFIXES (copy into test) ===")
        for key, val in actual_shas.items():
            print(f'    "{key}": "{val}",')
        print("=============================================================\n")

        for key, expected_prefix in BASELINE_SHA_PREFIX.items():
            if expected_prefix.startswith("PLACEHOLDER"):
                pytest.skip(f"Baseline for {key} not yet captured; run test to get value")
            assert actual_shas[key] == expected_prefix, (
                f"AC10 HARD-GATE FAIL: {key} sha256[:16] mismatch\n"
                f"  expected: {expected_prefix}\n"
                f"  actual:   {actual_shas[key]}"
            )

    def test_t11_ac10_02_workspace_and_screening_engine_no_serialize_import(self):
        from app.services import workspace as ws_mod
        from app.services import screening_engine as se_mod

        ws_syms = set(dir(ws_mod))
        se_syms = set(dir(se_mod))

        forbidden = {
            "serializeRIS",
            "serialize_ris_py",
            "export_csv",
            "serialize_bibtex_py",
            "serializeBibTeX",
            "serialize_bibtex",
            "serialize_ris",
        }

        ws_found = ws_syms & forbidden
        se_found = se_syms & forbidden

        assert not ws_found, (
            f"AC10 HARD-GATE FAIL: workspace.py top-level has serialize* symbols: {ws_found}"
        )
        assert not se_found, (
            f"AC10 HARD-GATE FAIL: screening_engine.py top-level has serialize* symbols: {se_found}"
        )
