import pytest
import random
import asyncio
import hashlib
import json
from pathlib import Path
from app.services.simhash import (
    find_duplicates_bktree,
    _find_duplicates_pairwise_ground_truth,
    simhash64,
    hamming_distance,
    SIMHASH_HAMMING_THRESHOLD as THR,
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
