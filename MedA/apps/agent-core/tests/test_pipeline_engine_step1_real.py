from __future__ import annotations

import asyncio
import random
import uuid

import pytest
from sqlmodel import Session, select

from app.db import engine
from app.models import DedupDiagnostic, PipelineRun, Workspace
from app.services.pipeline_engine import (
    _exec_step1_real_dedup,
    create_pipeline_run,
    mark_step_success,
    run_single_step,
)


def _make_wid() -> str:
    wid = str(uuid.uuid4())
    with Session(engine) as ss:
        if ss.get(Workspace, wid) is None:
            ss.add(Workspace(id=wid))
            ss.commit()
    return wid


def _make_records_with_duplicates(n: int, dup_ratio: float = 0.15, seed: int = 42) -> list[dict]:
    random.seed(seed)
    base_titles = [
        "SGLT2 Inhibitor Effect on Renal Outcomes in Diabetic Kidney Disease",
        "Cardiovascular Safety of GLP-1 Receptor Agonists in Type 2 Diabetes",
        "RAAS Blockade and Kidney Protection in Chronic Kidney Disease",
        "Empagliflozin and Heart Failure Outcomes in HFrEF Patients",
        "Liraglutide Weight Loss Efficacy in Non-Diabetic Adults",
    ]
    base_abstracts = [
        "Background We studied the effect of SGLT2 inhibition on estimated glomerular filtration rate decline over a median follow-up of 2.5 years in patients with type 2 diabetes and established chronic kidney disease.",
        "Objective This double-blind randomized controlled trial evaluated major adverse cardiovascular events in patients receiving GLP-1 receptor agonist versus placebo.",
        "Methods We enrolled adults with eGFR 20-60 mL/min/1.73m2 and randomly assigned them to maximal RAAS blockade or usual care.",
        "Results In the empagliflozin group the composite outcome of cardiovascular death or hospitalization for heart failure occurred significantly less often.",
        "Conclusion Liraglutide 3.0 mg daily produced clinically meaningful weight reduction compared with placebo at 68 weeks.",
    ]
    records = []
    for i in range(n):
        base_idx = i % len(base_titles)
        title = base_titles[base_idx]
        abstract = base_abstracts[base_idx]
        if i > 0 and random.random() < dup_ratio:
            src = records[random.randint(0, len(records) - 1)]
            title = src["title"]
            abstract = src["abstract"]
            if random.random() < 0.5:
                title = title + " updated"
            else:
                abstract = abstract + " Additional follow-up data available."
        records.append({
            "id": i,
            "title": title,
            "abstract": abstract,
            "preset": "sglt2i_ckd",
        })
    return records


@pytest.fixture()
def db_session():
    with Session(engine) as session:
        yield session


SIZES = [200, 500, 1000, 2000]


@pytest.mark.parametrize("size", SIZES)
async def test_S1_dedup_nout_lt_nin(size):
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=min(size, 200))
    mark_step_success(run, 0, 100, size, size, attempt_no=1)
    records = _make_records_with_duplicates(size, dup_ratio=0.15, seed=size)
    ctx = {"fetched_records": records}
    await _exec_step1_real_dedup(run, ctx)
    assert "kept_records" in ctx
    n_out = len(ctx["kept_records"])
    assert n_out < size, f"Expected n_out={n_out} < size={size}"


@pytest.mark.parametrize("size", SIZES)
async def test_S2_sizes_hist_sum_eq_nin(size, db_session):
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=min(size, 200))
    mark_step_success(run, 0, 100, size, size, attempt_no=1)
    records = _make_records_with_duplicates(size, dup_ratio=0.15, seed=size + 7)
    ctx = {"fetched_records": records}
    await _exec_step1_real_dedup(run, ctx)
    dd = db_session.exec(
        select(DedupDiagnostic).where(
            DedupDiagnostic.run_id == run.id,
            DedupDiagnostic.step_idx == 1,
        )
    ).first()
    assert dd is not None
    total = sum(dd.sizes_hist.values())
    assert total == size, f"sizes_hist sum={total} != n_in={size}"


@pytest.mark.parametrize("size", SIZES)
async def test_S3_hamming_hist_keys_le_6(size, db_session):
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=min(size, 200))
    mark_step_success(run, 0, 100, size, size, attempt_no=1)
    records = _make_records_with_duplicates(size, dup_ratio=0.2, seed=size + 13)
    ctx = {"fetched_records": records}
    await _exec_step1_real_dedup(run, ctx)
    dd = db_session.exec(
        select(DedupDiagnostic).where(
            DedupDiagnostic.run_id == run.id,
            DedupDiagnostic.step_idx == 1,
        )
    ).first()
    assert dd is not None
    for k in dd.hamming_hist.keys():
        try:
            kval = int(k)
        except (ValueError, TypeError):
            pytest.fail(f"hamming_hist key {k!r} not int-convertible")
        assert kval <= 6, f"hamming_hist key={kval} > 6"


@pytest.mark.parametrize("size", SIZES)
async def test_S4_dedup_diag_written_perf_nonneg(size, db_session):
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=min(size, 200))
    mark_step_success(run, 0, 100, size, size, attempt_no=1)
    records = _make_records_with_duplicates(size, dup_ratio=0.12, seed=size + 21)
    ctx = {"fetched_records": records}
    await _exec_step1_real_dedup(run, ctx)
    dd = db_session.exec(
        select(DedupDiagnostic).where(
            DedupDiagnostic.run_id == run.id,
            DedupDiagnostic.step_idx == 1,
        )
    ).first()
    assert dd is not None, "DedupDiagnostic row missing"
    assert dd.perf_json is not None
    total_ms = dd.perf_json.get("step1_total_ms")
    assert total_ms is not None, "perf missing step1_total_ms"
    assert isinstance(total_ms, (int, float))
    assert total_ms >= 0, f"step1_total_ms={total_ms} < 0"


async def test_S5_cancel_flag_before_bktree_no_diag_no_success(db_session):
    wid = _make_wid()
    size = 200
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=200)
    mark_step_success(run, 0, 100, size, size, attempt_no=1)
    records = _make_records_with_duplicates(size, dup_ratio=0.1, seed=501)
    ctx = {"fetched_records": records, "cancel_flag": True}
    await _exec_step1_real_dedup(run, ctx)
    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        step1_status = (r2.steps_json[1] or {}).get("status") if r2.steps_json else None
        assert step1_status != "success", f"step1 status should not be success, got {step1_status}"
        dd = ss.exec(
            select(DedupDiagnostic).where(
                DedupDiagnostic.run_id == run.id,
                DedupDiagnostic.step_idx == 1,
            )
        ).first()
        assert dd is None, "DedupDiagnostic should NOT be written when canceled"


async def test_S6_cancel_flag_before_diag_write_no_success(db_session):
    wid = _make_wid()
    size = 500
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=200)
    mark_step_success(run, 0, 100, size, size, attempt_no=1)
    records = _make_records_with_duplicates(size, dup_ratio=0.1, seed=601)
    ctx = {"fetched_records": records}

    from app.services import simhash as _sh_mod
    orig_bktree = _sh_mod.find_duplicates_bktree

    async def _set_cancel_after_bktree(*args, **kwargs):
        kept_ids, diag = await orig_bktree(*args, **kwargs)
        ctx["cancel_flag"] = True
        return kept_ids, diag

    _sh_mod.find_duplicates_bktree = _set_cancel_after_bktree
    try:
        await _exec_step1_real_dedup(run, ctx)
    finally:
        _sh_mod.find_duplicates_bktree = orig_bktree

    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        step1_status = (r2.steps_json[1] or {}).get("status") if r2.steps_json else None
        assert step1_status != "success", f"step1 should not be success, got {step1_status}"
        dd = ss.exec(
            select(DedupDiagnostic).where(
                DedupDiagnostic.run_id == run.id,
                DedupDiagnostic.step_idx == 1,
            )
        ).first()
        assert dd is None, "DedupDiagnostic should NOT be written when canceled before DB write"


async def test_S7_parity_n200_2presets_no_assertion(db_session):
    for preset, seed in [("sglt2i_ckd", 701), ("empagliflozin_hf", 801)]:
        wid = _make_wid()
        size = 200
        run = create_pipeline_run(wid, preset, max_records=200)
        mark_step_success(run, 0, 100, size, size, attempt_no=1)
        records = _make_records_with_duplicates(size, dup_ratio=0.18, seed=seed)
        for r in records:
            r["preset"] = preset
        ctx = {"fetched_records": records}
        try:
            await _exec_step1_real_dedup(run, ctx)
        except AssertionError as exc:
            pytest.fail(f"Parity check unexpectedly failed (preset={preset}): {exc}")
        dd = db_session.exec(
            select(DedupDiagnostic).where(
                DedupDiagnostic.run_id == run.id,
                DedupDiagnostic.step_idx == 1,
            )
        ).first()
        assert dd is not None


async def test_S8_parity_breaks_on_hacked_pairwise_truth_raises(db_session):
    from app.services import simhash as _sh_mod

    wid = _make_wid()
    size = 200
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=200)
    mark_step_success(run, 0, 100, size, size, attempt_no=1)
    records = _make_records_with_duplicates(size, dup_ratio=0.18, seed=901)
    ctx = {"fetched_records": records}

    orig_pairwise = _sh_mod._find_duplicates_pairwise_ground_truth

    def _hacked_pairwise(*args, **kwargs):
        real_result = orig_pairwise(*args, **kwargs)
        return set()

    _sh_mod._find_duplicates_pairwise_ground_truth = _hacked_pairwise
    try:
        with pytest.raises(AssertionError, match="parity FAILED"):
            await _exec_step1_real_dedup(run, ctx)
    finally:
        _sh_mod._find_duplicates_pairwise_ground_truth = orig_pairwise
