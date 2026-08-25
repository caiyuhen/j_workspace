import pytest
import random
import asyncio
import hashlib
import json
from pathlib import Path
from app.services.simhash import (
    find_duplicates_bktree,
    find_duplicates_hybrid,
    _find_duplicates_pairwise_ground_truth,
    simhash64,
    hamming_distance,
    SIMHASH_HAMMING_THRESHOLD as THR,
    FALLBACK_N_PARITY,
)


PRESETS = [
    "sglt2i_ckd",
    "empagliflozin_hf",
    "glp1_weightloss",
    "liraglutide_nafld",
    "pkd_tolvaptan",
    "ckd_blood_pressure_control",
]

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "w10_synthetic_preset_200.json"


def _print_set_diff(label_a: str, set_a: set, label_b: str, set_b: set) -> None:
    extra = sorted(set_a - set_b)[:20]
    missing = sorted(set_b - set_a)[:20]
    print(f"\n  === DIFF SUMMARY ({label_a} vs {label_b}) ===")
    print(f"  |{label_a}|={len(set_a)}  |{label_b}|={len(set_b)}")
    print(f"  extra ({label_a}-{label_b}) first 20: {extra}")
    print(f"  missing ({label_b}-{label_a}) first 20: {missing}")


def _synthetic_records_for_preset(preset: str, n: int = 200) -> list[dict]:
    rng = random.Random()
    seed_bytes = hashlib.sha256(f"w11-parity:{preset}".encode("utf-8")).digest()
    seed_int = int.from_bytes(seed_bytes[:8], "big")
    rng.seed(seed_int)

    title_templates = {
        "sglt2i_ckd": [
            "SGLT2 Inhibitor {drug} in CKD Patients with T2DM: Randomized Trial #{i}",
            "Dapagliflozin vs Placebo on Renal Outcomes in Stage 3 CKD: Study #{i}",
            "Empagliflozin Efficacy in Diabetic Kidney Disease: RCT #{i}",
            "Renoprotective Effects of SGLT2i in CKD with Albuminuria: Trial #{i}",
        ],
        "empagliflozin_hf": [
            "Empagliflozin in Heart Failure with Reduced EF: Phase 3 Trial #{i}",
            "EMPAGLIFLOZIN Outcomes in Chronic HFpEF Patients: Study #{i}",
            "Cardiorenal Benefits of Empagliflozin in HFrEF: RCT #{i}",
            "Empagliflozin vs Standard Care in Hospitalized HF: Trial #{i}",
        ],
        "glp1_weightloss": [
            "GLP-1 Receptor Agonist {drug} for Obesity: Phase 2 Study #{i}",
            "Semaglutide 2.4mg Weekly Weight Loss Efficacy: RCT #{i}",
            "Tirzepatide vs GLP-1 RA on Body Weight Reduction: Trial #{i}",
            "Cardiometabolic Effects of GLP-1 in Severe Obesity: Study #{i}",
        ],
        "liraglutide_nafld": [
            "Liraglutide 1.8mg in Nonalcoholic Fatty Liver Disease: RCT #{i}",
            "GLP-1 Agonist on Liver Histology in NASH Patients: Trial #{i}",
            "Liraglutide vs Pioglitazone for NAFLD Fibrosis: Study #{i}",
            "Metabolic and Hepatic Effects of Liraglutide in NASH: Trial #{i}",
        ],
        "pkd_tolvaptan": [
            "Tolvaptan in Autosomal Dominant Polycystic Kidney Disease: Study #{i}",
            "V2 Receptor Antagonist Tolvaptan on Kidney Growth in ADPKD: RCT #{i}",
            "Tolvaptan Efficacy on eGFR Decline in Early PKD: Trial #{i}",
            "Long-term Tolvaptan Safety in Polycystic Liver-Kidney Disease: #{i}",
        ],
        "ckd_blood_pressure_control": [
            "Intensive vs Standard BP Control in CKD: Systematic Review #{i}",
            "Systolic Target <120 vs <140 mmHg in Diabetic CKD: RCT #{i}",
            "RAAS Inhibition plus ARB on BP in Stage 4 CKD: Trial #{i}",
            "Ambulatory Blood Pressure Patterns and CKD Progression: Study #{i}",
        ],
    }
    drugs = ["Dapagliflozin", "Empagliflozin", "Canagliflozin", "Ertugliflozin", "Semaglutide", "Liraglutide", "Tirzepatide"]
    tmpls = title_templates.get(preset, title_templates["sglt2i_ckd"])
    records = []
    start_id = PRESETS.index(preset) * 10000
    for i in range(n):
        tmpl = tmpls[i % len(tmpls)]
        drug = drugs[(i * 7 + rng.randint(0, len(drugs) - 1)) % len(drugs)]
        title = tmpl.format(drug=drug, i=i)
        if i % 11 == 0 and i > 0:
            twin_idx = i - (i % 11)
            base_tmpl = tmpls[twin_idx % len(tmpls)]
            title = base_tmpl.format(drug=drugs[(twin_idx * 3) % len(drugs)], i=twin_idx)
            if rng.random() < 0.35:
                title = title + " extended followup analysis"
        abs_words = [
            "Background", "Methods", "Results", "Conclusions",
            "randomized", "double-blind", "placebo-controlled",
            "primary", "endpoint", "hazard", "ratio", "confidence",
            "interval", "significant", "p<0.001", "patients", "treatment",
            "cardiovascular", "renal", "composite", "outcome", "safety",
            "tolerability", "followup", "months", "median", "efficacy",
        ]
        rng.shuffle(abs_words)
        abstract = " ".join(abs_words[: rng.randint(12, 22)]) + f" record index {i}"
        records.append({
            "id": start_id + i,
            "nct_id": f"NCT{start_id + i:08d}",
            "title": title,
            "abstract": abstract,
            "preset": preset,
        })
    return records


def _load_or_build_fixture() -> dict[str, list[dict]]:
    if FIXTURE_PATH.exists():
        with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        result = {}
        for p in PRESETS:
            result[p] = [r for r in data if r.get("preset") == p][:200]
            if len(result[p]) < 200:
                result[p].extend(_synthetic_records_for_preset(p, 200 - len(result[p])))
        return result
    return {p: _synthetic_records_for_preset(p, 200) for p in PRESETS}


def _pairwise_hamming_hist(records: list[dict], thr: int) -> dict[int, int]:
    texts = [f"{r.get('title', '')} {r.get('abstract', '')}" for r in records]
    fps = [simhash64(x) for x in texts]
    hist: dict[int, int] = {}
    n = len(fps)
    for i in range(n):
        for j in range(i + 1, n):
            h = hamming_distance(fps[i], fps[j])
            if h <= thr:
                hist[h] = hist.get(h, 0) + 1
    return hist


@pytest.fixture(scope="module")
def preset_records():
    return _load_or_build_fixture()


# ============================================================
# P1-P6 · BK kept_ids set == O(n^2) GT kept_ids set
# ============================================================
def test_P1_sglt2i_ckd_bk_eq_pairwise_kept_set(preset_records):
    records = preset_records["sglt2i_ckd"]
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_gt = _find_duplicates_pairwise_ground_truth(records, THR)
    s_bk, s_gt = set(kept_bk), kept_gt
    if s_bk != s_gt:
        _print_set_diff("BK", s_bk, "GT", s_gt)
    assert s_bk == s_gt, f"P1 BK kept set != O(n^2) GT set: |BK|={len(s_bk)} |GT|={len(s_gt)}"


def test_P2_empagliflozin_hf_bk_eq_pairwise_kept_set(preset_records):
    records = preset_records["empagliflozin_hf"]
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_gt = _find_duplicates_pairwise_ground_truth(records, THR)
    s_bk, s_gt = set(kept_bk), kept_gt
    if s_bk != s_gt:
        _print_set_diff("BK", s_bk, "GT", s_gt)
    assert s_bk == s_gt, f"P2 BK kept set != O(n^2) GT set: |BK|={len(s_bk)} |GT|={len(s_gt)}"


def test_P3_glp1_weightloss_bk_eq_pairwise_kept_set(preset_records):
    records = preset_records["glp1_weightloss"]
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_gt = _find_duplicates_pairwise_ground_truth(records, THR)
    s_bk, s_gt = set(kept_bk), kept_gt
    if s_bk != s_gt:
        _print_set_diff("BK", s_bk, "GT", s_gt)
    assert s_bk == s_gt, f"P3 BK kept set != O(n^2) GT set: |BK|={len(s_bk)} |GT|={len(s_gt)}"


def test_P4_liraglutide_nafld_bk_eq_pairwise_kept_set(preset_records):
    records = preset_records["liraglutide_nafld"]
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_gt = _find_duplicates_pairwise_ground_truth(records, THR)
    s_bk, s_gt = set(kept_bk), kept_gt
    if s_bk != s_gt:
        _print_set_diff("BK", s_bk, "GT", s_gt)
    assert s_bk == s_gt, f"P4 BK kept set != O(n^2) GT set: |BK|={len(s_bk)} |GT|={len(s_gt)}"


def test_P5_pkd_tolvaptan_bk_eq_pairwise_kept_set(preset_records):
    records = preset_records["pkd_tolvaptan"]
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_gt = _find_duplicates_pairwise_ground_truth(records, THR)
    s_bk, s_gt = set(kept_bk), kept_gt
    if s_bk != s_gt:
        _print_set_diff("BK", s_bk, "GT", s_gt)
    assert s_bk == s_gt, f"P5 BK kept set != O(n^2) GT set: |BK|={len(s_bk)} |GT|={len(s_gt)}"


def test_P6_ckd_blood_pressure_control_bk_eq_pairwise_kept_set(preset_records):
    records = preset_records["ckd_blood_pressure_control"]
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_gt = _find_duplicates_pairwise_ground_truth(records, THR)
    s_bk, s_gt = set(kept_bk), kept_gt
    if s_bk != s_gt:
        _print_set_diff("BK", s_bk, "GT", s_gt)
    assert s_bk == s_gt, f"P6 BK kept set != O(n^2) GT set: |BK|={len(s_bk)} |GT|={len(s_gt)}"


# ============================================================
# P7-P12 · BK hamming_hist pair_count == O(n^2) pair_count
# ============================================================
def test_P7_sglt2i_ckd_hamming_hist_paircount_parity(preset_records):
    records = preset_records["sglt2i_ckd"]
    _, diag = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    bk_hist = diag.get("hamming_hist", {})
    gt_hist = _pairwise_hamming_hist(records, THR)
    all_keys = set(bk_hist.keys()) | set(gt_hist.keys())
    diffs = {}
    for k in sorted(all_keys):
        bv = bk_hist.get(k, 0)
        gv = gt_hist.get(k, 0)
        if bv != gv:
            diffs[k] = (bv, gv)
    if diffs:
        print(f"\n  === P7 HAMMING HIST DIFF (bk vs gt) ===")
        print(f"  BK hist: {dict(sorted(bk_hist.items()))}")
        print(f"  GT hist: {dict(sorted(gt_hist.items()))}")
        print(f"  Mismatching h keys (bk_val, gt_val): {diffs}")
    assert not diffs, f"P7 hamming_hist pair_count mismatch keys={list(diffs.keys())}"


def test_P8_empagliflozin_hf_hamming_hist_paircount_parity(preset_records):
    records = preset_records["empagliflozin_hf"]
    _, diag = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    bk_hist = diag.get("hamming_hist", {})
    gt_hist = _pairwise_hamming_hist(records, THR)
    all_keys = set(bk_hist.keys()) | set(gt_hist.keys())
    diffs = {}
    for k in sorted(all_keys):
        bv = bk_hist.get(k, 0)
        gv = gt_hist.get(k, 0)
        if bv != gv:
            diffs[k] = (bv, gv)
    if diffs:
        print(f"\n  === P8 HAMMING HIST DIFF (bk vs gt) ===")
        print(f"  BK hist: {dict(sorted(bk_hist.items()))}")
        print(f"  GT hist: {dict(sorted(gt_hist.items()))}")
        print(f"  Mismatching h keys (bk_val, gt_val): {diffs}")
    assert not diffs, f"P8 hamming_hist pair_count mismatch keys={list(diffs.keys())}"


def test_P9_glp1_weightloss_hamming_hist_paircount_parity(preset_records):
    records = preset_records["glp1_weightloss"]
    _, diag = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    bk_hist = diag.get("hamming_hist", {})
    gt_hist = _pairwise_hamming_hist(records, THR)
    all_keys = set(bk_hist.keys()) | set(gt_hist.keys())
    diffs = {}
    for k in sorted(all_keys):
        bv = bk_hist.get(k, 0)
        gv = gt_hist.get(k, 0)
        if bv != gv:
            diffs[k] = (bv, gv)
    if diffs:
        print(f"\n  === P9 HAMMING HIST DIFF (bk vs gt) ===")
        print(f"  BK hist: {dict(sorted(bk_hist.items()))}")
        print(f"  GT hist: {dict(sorted(gt_hist.items()))}")
        print(f"  Mismatching h keys (bk_val, gt_val): {diffs}")
    assert not diffs, f"P9 hamming_hist pair_count mismatch keys={list(diffs.keys())}"


def test_P10_liraglutide_nafld_hamming_hist_paircount_parity(preset_records):
    records = preset_records["liraglutide_nafld"]
    _, diag = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    bk_hist = diag.get("hamming_hist", {})
    gt_hist = _pairwise_hamming_hist(records, THR)
    all_keys = set(bk_hist.keys()) | set(gt_hist.keys())
    diffs = {}
    for k in sorted(all_keys):
        bv = bk_hist.get(k, 0)
        gv = gt_hist.get(k, 0)
        if bv != gv:
            diffs[k] = (bv, gv)
    if diffs:
        print(f"\n  === P10 HAMMING HIST DIFF (bk vs gt) ===")
        print(f"  BK hist: {dict(sorted(bk_hist.items()))}")
        print(f"  GT hist: {dict(sorted(gt_hist.items()))}")
        print(f"  Mismatching h keys (bk_val, gt_val): {diffs}")
    assert not diffs, f"P10 hamming_hist pair_count mismatch keys={list(diffs.keys())}"


def test_P11_pkd_tolvaptan_hamming_hist_paircount_parity(preset_records):
    records = preset_records["pkd_tolvaptan"]
    _, diag = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    bk_hist = diag.get("hamming_hist", {})
    gt_hist = _pairwise_hamming_hist(records, THR)
    all_keys = set(bk_hist.keys()) | set(gt_hist.keys())
    diffs = {}
    for k in sorted(all_keys):
        bv = bk_hist.get(k, 0)
        gv = gt_hist.get(k, 0)
        if bv != gv:
            diffs[k] = (bv, gv)
    if diffs:
        print(f"\n  === P11 HAMMING HIST DIFF (bk vs gt) ===")
        print(f"  BK hist: {dict(sorted(bk_hist.items()))}")
        print(f"  GT hist: {dict(sorted(gt_hist.items()))}")
        print(f"  Mismatching h keys (bk_val, gt_val): {diffs}")
    assert not diffs, f"P11 hamming_hist pair_count mismatch keys={list(diffs.keys())}"


def test_P12_ckd_blood_pressure_control_hamming_hist_paircount_parity(preset_records):
    records = preset_records["ckd_blood_pressure_control"]
    _, diag = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    bk_hist = diag.get("hamming_hist", {})
    gt_hist = _pairwise_hamming_hist(records, THR)
    all_keys = set(bk_hist.keys()) | set(gt_hist.keys())
    diffs = {}
    for k in sorted(all_keys):
        bv = bk_hist.get(k, 0)
        gv = gt_hist.get(k, 0)
        if bv != gv:
            diffs[k] = (bv, gv)
    if diffs:
        print(f"\n  === P12 HAMMING HIST DIFF (bk vs gt) ===")
        print(f"  BK hist: {dict(sorted(bk_hist.items()))}")
        print(f"  GT hist: {dict(sorted(gt_hist.items()))}")
        print(f"  Mismatching h keys (bk_val, gt_val): {diffs}")
    assert not diffs, f"P12 hamming_hist pair_count mismatch keys={list(diffs.keys())}"


# ============================================================
# P13-P18 · Order shuffle parity: shuffled kept set == original kept set
# ============================================================
def test_P13_sglt2i_ckd_shuffle_parity_kept_set(preset_records):
    records = preset_records["sglt2i_ckd"]
    kept_orig, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    shuffled = list(records)
    random.Random(7).shuffle(shuffled)
    kept_shuf, _ = asyncio.run(find_duplicates_bktree(shuffled, THR, n_jobs=8, enable_parity_check=False))
    s_orig, s_shuf = set(kept_orig), set(kept_shuf)
    if s_orig != s_shuf:
        _print_set_diff("orig", s_orig, "shuf", s_shuf)
    assert s_orig == s_shuf, f"P13 shuffle parity failed: |orig|={len(s_orig)} |shuf|={len(s_shuf)}"


def test_P14_empagliflozin_hf_shuffle_parity_kept_set(preset_records):
    records = preset_records["empagliflozin_hf"]
    kept_orig, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    shuffled = list(records)
    random.Random(7).shuffle(shuffled)
    kept_shuf, _ = asyncio.run(find_duplicates_bktree(shuffled, THR, n_jobs=8, enable_parity_check=False))
    s_orig, s_shuf = set(kept_orig), set(kept_shuf)
    if s_orig != s_shuf:
        _print_set_diff("orig", s_orig, "shuf", s_shuf)
    assert s_orig == s_shuf, f"P14 shuffle parity failed: |orig|={len(s_orig)} |shuf|={len(s_shuf)}"


def test_P15_glp1_weightloss_shuffle_parity_kept_set(preset_records):
    records = preset_records["glp1_weightloss"]
    kept_orig, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    shuffled = list(records)
    random.Random(7).shuffle(shuffled)
    kept_shuf, _ = asyncio.run(find_duplicates_bktree(shuffled, THR, n_jobs=8, enable_parity_check=False))
    s_orig, s_shuf = set(kept_orig), set(kept_shuf)
    if s_orig != s_shuf:
        _print_set_diff("orig", s_orig, "shuf", s_shuf)
    assert s_orig == s_shuf, f"P15 shuffle parity failed: |orig|={len(s_orig)} |shuf|={len(s_shuf)}"


def test_P16_liraglutide_nafld_shuffle_parity_kept_set(preset_records):
    records = preset_records["liraglutide_nafld"]
    kept_orig, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    shuffled = list(records)
    random.Random(7).shuffle(shuffled)
    kept_shuf, _ = asyncio.run(find_duplicates_bktree(shuffled, THR, n_jobs=8, enable_parity_check=False))
    s_orig, s_shuf = set(kept_orig), set(kept_shuf)
    if s_orig != s_shuf:
        _print_set_diff("orig", s_orig, "shuf", s_shuf)
    assert s_orig == s_shuf, f"P16 shuffle parity failed: |orig|={len(s_orig)} |shuf|={len(s_shuf)}"


def test_P17_pkd_tolvaptan_shuffle_parity_kept_set(preset_records):
    records = preset_records["pkd_tolvaptan"]
    kept_orig, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    shuffled = list(records)
    random.Random(7).shuffle(shuffled)
    kept_shuf, _ = asyncio.run(find_duplicates_bktree(shuffled, THR, n_jobs=8, enable_parity_check=False))
    s_orig, s_shuf = set(kept_orig), set(kept_shuf)
    if s_orig != s_shuf:
        _print_set_diff("orig", s_orig, "shuf", s_shuf)
    assert s_orig == s_shuf, f"P17 shuffle parity failed: |orig|={len(s_orig)} |shuf|={len(s_shuf)}"


def test_P18_ckd_blood_pressure_control_shuffle_parity_kept_set(preset_records):
    records = preset_records["ckd_blood_pressure_control"]
    kept_orig, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    shuffled = list(records)
    random.Random(7).shuffle(shuffled)
    kept_shuf, _ = asyncio.run(find_duplicates_bktree(shuffled, THR, n_jobs=8, enable_parity_check=False))
    s_orig, s_shuf = set(kept_orig), set(kept_shuf)
    if s_orig != s_shuf:
        _print_set_diff("orig", s_orig, "shuf", s_shuf)
    assert s_orig == s_shuf, f"P18 shuffle parity failed: |orig|={len(s_orig)} |shuf|={len(s_shuf)}"


# ============================================================
# P19-P42 · D1-3 APPEND 24 tests · 6 preset × 4 sizes (500/1k/5k/10k)
# BK kept_ids set == Hybrid kept_ids set (fallback mode: n≤10000 → BK-only)
# ============================================================
EXTRA_SIZES = [500, 1000, 5000, 10000]
SIZE_LABELS = {500: "n500", 1000: "n1k", 5000: "n5k", 10000: "n10k"}
PRESET_IDX = {p: i for i, p in enumerate(PRESETS)}


def _records_for_preset_size(preset: str, n: int) -> list[dict]:
    base = _synthetic_records_for_preset(preset, max(n, 200))
    if len(base) >= n:
        return base[:n]
    extra = _synthetic_records_for_preset(preset, n + 200)
    return extra[:n]


def test_P19_sglt2i_ckd_n500_bk_eq_hybrid_parity():
    records = _records_for_preset_size("sglt2i_ckd", 500)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P19 BK vs Hybrid parity n500: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P20_empagliflozin_hf_n500_bk_eq_hybrid_parity():
    records = _records_for_preset_size("empagliflozin_hf", 500)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P20 BK vs Hybrid parity n500: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P21_glp1_weightloss_n500_bk_eq_hybrid_parity():
    records = _records_for_preset_size("glp1_weightloss", 500)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P21 BK vs Hybrid parity n500: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P22_liraglutide_nafld_n500_bk_eq_hybrid_parity():
    records = _records_for_preset_size("liraglutide_nafld", 500)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P22 BK vs Hybrid parity n500: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P23_pkd_tolvaptan_n500_bk_eq_hybrid_parity():
    records = _records_for_preset_size("pkd_tolvaptan", 500)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P23 BK vs Hybrid parity n500: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P24_ckd_blood_pressure_control_n500_bk_eq_hybrid_parity():
    records = _records_for_preset_size("ckd_blood_pressure_control", 500)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P24 BK vs Hybrid parity n500: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P25_sglt2i_ckd_n1k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("sglt2i_ckd", 1000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P25 BK vs Hybrid parity n1k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P26_empagliflozin_hf_n1k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("empagliflozin_hf", 1000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P26 BK vs Hybrid parity n1k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P27_glp1_weightloss_n1k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("glp1_weightloss", 1000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P27 BK vs Hybrid parity n1k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P28_liraglutide_nafld_n1k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("liraglutide_nafld", 1000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P28 BK vs Hybrid parity n1k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P29_pkd_tolvaptan_n1k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("pkd_tolvaptan", 1000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P29 BK vs Hybrid parity n1k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P30_ckd_blood_pressure_control_n1k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("ckd_blood_pressure_control", 1000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P30 BK vs Hybrid parity n1k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P31_sglt2i_ckd_n5k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("sglt2i_ckd", 5000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P31 BK vs Hybrid parity n5k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P32_empagliflozin_hf_n5k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("empagliflozin_hf", 5000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P32 BK vs Hybrid parity n5k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P33_glp1_weightloss_n5k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("glp1_weightloss", 5000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P33 BK vs Hybrid parity n5k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P34_liraglutide_nafld_n5k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("liraglutide_nafld", 5000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P34 BK vs Hybrid parity n5k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P35_pkd_tolvaptan_n5k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("pkd_tolvaptan", 5000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P35 BK vs Hybrid parity n5k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P36_ckd_blood_pressure_control_n5k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("ckd_blood_pressure_control", 5000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P36 BK vs Hybrid parity n5k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P37_sglt2i_ckd_n10k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("sglt2i_ckd", 10000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P37 BK vs Hybrid parity n10k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P38_empagliflozin_hf_n10k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("empagliflozin_hf", 10000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P38 BK vs Hybrid parity n10k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P39_glp1_weightloss_n10k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("glp1_weightloss", 10000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P39 BK vs Hybrid parity n10k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P40_liraglutide_nafld_n10k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("liraglutide_nafld", 10000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P40 BK vs Hybrid parity n10k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P41_pkd_tolvaptan_n10k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("pkd_tolvaptan", 10000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P41 BK vs Hybrid parity n10k: |BK|={len(s_bk)} |H|={len(s_h)}"


def test_P42_ckd_blood_pressure_control_n10k_bk_eq_hybrid_parity():
    records = _records_for_preset_size("ckd_blood_pressure_control", 10000)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, _ = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)
    s_bk, s_h = set(kept_bk), set(kept_h)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID", s_h)
    assert s_bk == s_h, f"P42 BK vs Hybrid parity n10k: |BK|={len(s_bk)} |H|={len(s_h)}"


# ============================================================
# D1-3 Red反证 test · monkey.patch FALLBACK_N → tiny 100
# Force n=200 go through full 3-stage hybrid → still equals BK set (0 FN/FP)
# ============================================================
def test_P43_RED_disproof_monkeypatch_fallback_small_n_full_hybrid_eq_bk(monkeypatch):
    import app.services.simhash as simhash_mod

    monkeypatch.setattr(simhash_mod, "FALLBACK_N_PARITY", 100)

    records = _records_for_preset_size("sglt2i_ckd", 200)
    kept_bk, _ = asyncio.run(find_duplicates_bktree(records, THR, n_jobs=8, enable_parity_check=False))
    kept_h, diag_h = find_duplicates_hybrid(records, THR, n_jobs=8, enable_parity_check=False)

    perf = diag_h.get("perf_json", {})
    assert perf.get("fallback_used") is False, (
        "RED反证: monkeypatch FALLBACK_N=100 后 n=200 应走完整 3-stage hybrid (fallback_used=False)"
    )
    assert perf.get("version") == "w12-hybrid-v1"

    s_bk, s_h = set(kept_bk), set(kept_h)
    fn = len(s_bk - s_h)
    fp = len(s_h - s_bk)
    if s_bk != s_h:
        _print_set_diff("BK", s_bk, "HYBRID-3stage", s_h)
        print(f"  FN (BK has but Hybrid missing) = {fn}")
        print(f"  FP (Hybrid has but BK missing)  = {fp}")
    assert fn == 0 and fp == 0, (
        f"RED反证 FAIL: full 3-stage hybrid vs BK 0 FN/FP required. "
        f"Got FN={fn}, FP={fp}, |BK|={len(s_bk)}, |H|={len(s_h)}"
    )
