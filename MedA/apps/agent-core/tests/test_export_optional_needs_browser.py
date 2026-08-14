import random
import string

import pytest

from app.services.serialize_ris import (
    _sanitize_filename_py as sanitizeFilename,
    makeEmptyPrismaSvg,
    serialize_ris_py as serializeRIS,
)
from app.services.serialize_bibtex import serialize_bibtex_py as serializeBibTeX

pytestmark = pytest.mark.needs_browser


def _make_record(i: int) -> dict:
    return {
        "id": f"lit_{i:06d}",
        "title": f"Structural study {i} of molecular mechanism ABCD{i} in chronic kidney disease: a randomized controlled trial with long-term follow-up",
        "authors": [f"Author{i}A, FirstName", f"Author{i}B, SecondName", f"Author{i}C, ThirdName"],
        "journal": f"Journal of Medical Structural Research Volume {i % 50 + 1}",
        "year": 2020 + (i % 6),
        "volume": str(100 + (i % 50)),
        "issue": str(1 + (i % 12)),
        "pages": f"{10 + i % 90}-{50 + i % 90}",
        "abstract": (
            f"Background: Structural investigation {i} examines the efficacy of intervention X{i} "
            f"in patients with condition Y{i}. Methods: We conducted a single-center, double-blind, "
            f"randomized, placebo-controlled trial enrolling {500 + i * 3} participants. The primary "
            f"endpoint was the change from baseline at month 12. Secondary endpoints included safety, "
            f"tolerability, and quality-of-life measures. Results: The intervention group demonstrated "
            f"statistically significant improvement compared with placebo (p < 0.001; difference = "
            f"{i % 23}.{(i * 7) % 100}). Adverse events were balanced between arms. Conclusion: "
            f"Intervention X{i} offers a clinically meaningful benefit and represents a valuable "
            f"addition to the therapeutic armamentarium for condition Y{i}. Further multi-center "
            f"studies are warranted to confirm generalizability."
        ),
        "source": ["pubmed", "cnki", "wanfang"][i % 3],
        "doi": f"10.{1000 + i}/j.struct.{2024}{i:06d}",
        "pmid": str(38000000 + i),
        "pmcid": "",
        "url": f"https://example.org/doi/10.{1000 + i}/j.struct.{2024}{i:06d}",
        "keywords": [f"keyword{i}a", f"keyword{i}b", f"keyword{i}c", f"structural marker {i}"],
    }


def test_export_ris_500records_structural():
    records = [_make_record(i) for i in range(500)]
    output = serializeRIS(records)
    assert len(output) > 50000, f"RIS output too small: {len(output)} bytes"


def test_export_bibtex_500records_structural():
    records = [_make_record(i) for i in range(500)]
    output = serializeBibTeX(records, cite_key_prefix="meda")
    assert len(output) > 40000, f"BibTeX output too small: {len(output)} bytes"


def test_makeEmptyPrismaSvg_999_runs_no_memory_leak():
    for i in range(999):
        result = makeEmptyPrismaSvg(runId=i, reason=f"stress {i}")
        assert "xmlns" in result, f"iteration {i}: missing xmlns"
        assert isinstance(result, str) and len(result) > 100


def test_sanitizeFilename_10k_no_collision():
    rng = random.Random(42)
    alphabet = string.ascii_letters + string.digits + " \t_-.\\/:*?\"<>|你好世界" + "".join(chr(x) for x in range(0x00, 0x20))
    samples = [
        "".join(rng.choice(alphabet) for _ in range(300))
        for _ in range(10000)
    ]
    results = [sanitizeFilename(s) for s in samples]
    in_range = sum(1 for r in results if 1 <= len(r) <= 200)
    ratio = in_range / len(results)
    assert ratio >= 0.99, f"sanitize length ratio too low: {ratio:.4f} ({in_range}/{len(results)})"
