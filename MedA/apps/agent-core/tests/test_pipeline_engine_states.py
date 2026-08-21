from __future__ import annotations

import asyncio
import datetime as dt
import time
import uuid

import pytest
from sqlmodel import Session, select

from app.db import engine
from app.models import PipelineRun, PipelineStepResult, Workspace
from app.services.pipeline_engine import (
    MAX_AUTO_RETRIES,
    MAX_RECORDS_HARD_CAP,
    PIPELINE_STEPS,
    RETRY_BACKOFFS_SEC,
    STEP_NAMES_MAP,
    VALID_PRESETS,
    create_pipeline_run,
    get_first_non_success_index,
    mark_run_failed,
    mark_run_success,
    mark_step_failed,
    mark_step_success,
    resume_pipeline,
    run_pipeline,
    run_single_step,
)


STEP_NAMES = [
    "pubmed_fetch",
    "simhash_dedupe",
    "screen_ta",
    "screen_ft",
    "abstractor",
    "rob2_assessment",
    "grade_downgrade",
    "report_generate",
]


def _make_wid() -> str:
    wid = str(uuid.uuid4())
    with Session(engine) as ss:
        if ss.get(Workspace, wid) is None:
            ss.add(Workspace(id=wid))
            ss.commit()
    return wid


def test_E1_PIPELINE_STEPS_order_8_names():
    assert len(PIPELINE_STEPS) == 8
    for i, name in enumerate(STEP_NAMES):
        assert PIPELINE_STEPS[i]["step_index"] == i
        assert PIPELINE_STEPS[i]["step_name"] == name
        assert STEP_NAMES_MAP[name] == i


def test_E2_create_pipeline_run_defaults(db_session):
    wid = _make_wid()
    r = create_pipeline_run(wid, "sglt2i_ckd")
    assert r.id.startswith("p-")
    assert len(r.id) == 32
    assert r.preset == "sglt2i_ckd"
    assert r.mode == "snapshot"
    assert r.max_records == MAX_RECORDS_HARD_CAP
    assert r.status == "queued"
    assert len(r.steps_json) == 8
    for i, s in enumerate(r.steps_json):
        assert s["step_index"] == i
        assert s["step_name"] == STEP_NAMES[i]
        assert s["status"] == "pending"
        assert s["attempt_no"] == 0


@pytest.mark.parametrize("idx", list(range(8)))
def test_E3_to_E10_mark_step_success_each(db_session, idx):
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd")
    n_in = 200 if idx == 0 else 100
    n_out = max(1, int(n_in * 0.8))
    dur = 1234 + idx
    result = mark_step_success(run, idx, dur, n_in, n_out, f"ref/{idx}", attempt_no=1)

    assert result.step_index == idx
    assert result.step_name == STEP_NAMES[idx]
    assert result.attempt_no == 1
    assert result.status == "success"
    assert result.duration_ms == dur
    assert result.n_inputs == n_in
    assert result.n_outputs == n_out
    assert result.payload_ref == f"ref/{idx}"

    with Session(engine) as s2:
        r2 = s2.get(PipelineRun, run.id)
        assert r2.steps_json[idx]["status"] == "success"
        assert r2.steps_json[idx]["duration_ms"] == dur
        assert r2.steps_json[idx]["n_in"] == n_in
        assert r2.steps_json[idx]["n_out"] == n_out
        assert r2.current_step_index == idx + 1
        row = s2.exec(
            select(PipelineStepResult).where(
                PipelineStepResult.run_id == run.id,
                PipelineStepResult.step_index == idx,
                PipelineStepResult.attempt_no == 1,
            )
        ).one()
        assert row.status == "success"
        assert row.duration_ms == dur


@pytest.mark.parametrize("idx", list(range(8)))
async def test_E11_to_E18_retry_once_success(db_session, idx):
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=60)
    ctx: dict = {f"fail_once_step{idx}": True}

    start = time.perf_counter()
    await run_pipeline(run.id, ctx)
    elapsed = time.perf_counter() - start

    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        assert r2.status == "success"
        s = r2.steps_json[idx]
        assert s["status"] == "success"
        assert s["attempt_no"] == 2

        rows = list(ss.exec(
            select(PipelineStepResult).where(
                PipelineStepResult.run_id == run.id,
                PipelineStepResult.step_index == idx,
            ).order_by(PipelineStepResult.attempt_no)
        ).all())
        assert len(rows) == 2
        assert rows[0].attempt_no == 1
        assert rows[0].status == "failed"
        assert rows[0].retryable is True
        assert rows[1].attempt_no == 2
        assert rows[1].status == "success"

    assert elapsed >= RETRY_BACKOFFS_SEC[0] - 0.2


@pytest.mark.parametrize("idx,fail_mode,expected_retryable", [
    (0, "timeout", True),
    (1, "assertion", False),
    (2, "timeout", True),
    (3, "assertion", False),
    (4, "timeout", True),
    (5, "assertion", False),
    (6, "timeout", True),
    (7, "assertion", False),
])
async def test_E19_to_E26_fail_3_attempts(db_session, idx, fail_mode, expected_retryable):
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=50)
    ctx = {f"fail_forever_step{idx}": True, f"fail_mode_step{idx}": fail_mode}

    t0 = time.perf_counter()
    await run_pipeline(run.id, ctx)
    elapsed = time.perf_counter() - t0

    total_attempts = MAX_AUTO_RETRIES + 1
    with Session(engine) as ss:
        rows = list(ss.exec(
            select(PipelineStepResult).where(
                PipelineStepResult.run_id == run.id,
                PipelineStepResult.step_index == idx,
            ).order_by(PipelineStepResult.attempt_no)
        ).all())
        assert len(rows) == total_attempts, f"step{idx} expected {total_attempts} rows, got {len(rows)}"
        for r in rows:
            assert r.status == "failed"
            assert r.retryable == expected_retryable
        r2 = ss.get(PipelineRun, run.id)
        assert r2.status == "failed"
        assert r2.current_step_index == idx

    if expected_retryable:
        min_backoff = sum(RETRY_BACKOFFS_SEC)
        assert elapsed >= min_backoff - 0.3


async def test_E27_duration_monotonic_increasing_in_steps_json():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=50)
    durations = [100, 200, 300, 400, 500, 600, 700, 800]
    for i in range(8):
        mark_step_success(run, i, durations[i], 50 - i * 5, 40 - i * 4, None, attempt_no=1)
    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        got = [r2.steps_json[i]["duration_ms"] for i in range(8)]
        for i in range(7):
            assert got[i] < got[i + 1]


async def test_E28_cancel_flag_stops_after_current_step():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=50)

    from app.services import pipeline_engine as pe_mod
    orig_exec_N = pe_mod._exec_step_N

    call_count = [0]

    def patched_exec(idx, run_obj, ctx):
        call_count[0] += 1
        if idx == 0:
            with Session(engine) as ss:
                rdb = ss.get(PipelineRun, run.id)
                rdb.cancel_flag = True
                ss.add(rdb)
                ss.commit()
        return orig_exec_N(idx, run_obj, ctx)

    pe_mod._exec_step_N = patched_exec
    try:
        await run_pipeline(run.id)
    finally:
        pe_mod._exec_step_N = orig_exec_N

    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        assert r2.status != "success"


async def test_E29_run_pipeline_full_success_8_steps():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=100)
    await run_pipeline(run.id)
    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        assert r2.status == "success"
        assert r2.finished_at is not None
        for i in range(8):
            assert r2.steps_json[i]["status"] == "success"
            assert r2.steps_json[i]["attempt_no"] >= 1
        step7_payload = r2.steps_json[7]["payload_ref"]
        assert step7_payload is not None
        assert run.id in step7_payload
        assert step7_payload.endswith("report.pdf")


def test_E30_get_first_non_success_index_all_pending():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd")
    assert get_first_non_success_index(run) == 0


def test_E31_get_first_non_success_index_partial():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd")
    with Session(engine) as ss:
        r = ss.get(PipelineRun, run.id)
        new_steps = [dict(s) for s in r.steps_json]
        for i in range(3):
            new_steps[i]["status"] = "success"
        r.steps_json = new_steps
        ss.add(r)
        ss.commit()
        refreshed = ss.get(PipelineRun, run.id)
        run.steps_json = [dict(x) for x in refreshed.steps_json]
    assert get_first_non_success_index(run) == 3


def test_E32_get_first_non_success_index_all_done():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd")
    with Session(engine) as ss:
        r = ss.get(PipelineRun, run.id)
        new_steps = [dict(s) for s in r.steps_json]
        for i in range(8):
            new_steps[i]["status"] = "success"
        r.steps_json = new_steps
        ss.add(r)
        ss.commit()
        refreshed = ss.get(PipelineRun, run.id)
        run.steps_json = [dict(x) for x in refreshed.steps_json]
    assert get_first_non_success_index(run) == 8
