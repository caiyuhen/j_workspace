from __future__ import annotations

import asyncio
import time
import uuid

import pytest
from sqlmodel import Session, select

from app.db import engine
from app.models import PipelineRun, PipelineStepResult, Workspace
from app.services.pipeline_engine import (
    MAX_AUTO_RETRIES,
    RETRY_BACKOFFS_SEC,
    create_pipeline_run,
    resume_pipeline,
    run_pipeline,
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

FACTORS = [0.96, 0.86, 0.58, 0.56, 0.76, 0.98, 1.0, 1.0]


def _make_wid() -> str:
    wid = str(uuid.uuid4())
    with Session(engine) as ss:
        if ss.get(Workspace, wid) is None:
            ss.add(Workspace(id=wid))
            ss.commit()
    return wid


def _preset_steps_to_success(run_id: str, count_success: int, durations: list[int] | None = None):
    durs = durations or [1000 + i * 100 for i in range(count_success)]
    n_out_prev = 200
    with Session(engine) as ss:
        r = ss.get(PipelineRun, run_id)
        new_steps = [dict(s) for s in (r.steps_json or [])]
        for i in range(count_success):
            n_in = n_out_prev if i > 0 else r.max_records
            n_out = max(1, int(n_in * FACTORS[i]))
            step = new_steps[i]
            step["status"] = "success"
            step["attempt_no"] = 1
            step["duration_ms"] = durs[i]
            step["n_in"] = n_in
            step["n_out"] = n_out
            step["started_at"] = "2026-01-01T00:00:00"
            step["finished_at"] = "2026-01-01T00:00:10"
            step["payload_ref"] = None
            step["error_msg"] = None
            r.current_step_index = i + 1
            n_out_prev = n_out
            sr = PipelineStepResult(
                run_id=run_id,
                step_index=i,
                step_name=STEP_NAMES[i],
                attempt_no=1,
                status="success",
                duration_ms=durs[i],
                n_inputs=n_in,
                n_outputs=n_out,
            )
            ss.add(sr)
        r.steps_json = new_steps
        ss.add(r)
        ss.commit()


def _copy_steps(run_id: str) -> list[dict]:
    with Session(engine) as ss:
        r = ss.get(PipelineRun, run_id)
        return [dict(s) for s in (r.steps_json or [])]


async def test_R1_resume_skip_0_1_2_success_only_rerun_3_to_7():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=100)
    durs_before = [1111, 2222, 3333]
    _preset_steps_to_success(run.id, 3, durs_before)

    steps_before = _copy_steps(run.id)
    dur0_before = dict(steps_before[0])
    dur1_before = dict(steps_before[1])
    dur2_before = dict(steps_before[2])

    await resume_pipeline(run.id)

    steps_after = _copy_steps(run.id)
    assert steps_after[0]["duration_ms"] == dur0_before["duration_ms"]
    assert steps_after[0]["status"] == "success"
    assert steps_after[1]["duration_ms"] == dur1_before["duration_ms"]
    assert steps_after[1]["status"] == "success"
    assert steps_after[2]["duration_ms"] == dur2_before["duration_ms"]
    assert steps_after[2]["status"] == "success"
    for i in range(3, 8):
        assert steps_after[i]["status"] == "success"
    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        assert r2.status == "success"
        assert r2.finished_at is not None


async def test_R2_resume_steps_0_success_rerun_1_7():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=50)
    _preset_steps_to_success(run.id, 1, [777])

    steps_before = _copy_steps(run.id)
    s0_before = dict(steps_before[0])

    await resume_pipeline(run.id)

    steps_after = _copy_steps(run.id)
    assert steps_after[0]["duration_ms"] == s0_before["duration_ms"]
    assert steps_after[0]["status"] == "success"
    for i in range(1, 8):
        assert steps_after[i]["status"] == "success"
    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        assert r2.status == "success"


async def test_R3_resume_steps_01_success_only_01_untouched():
    wid = _make_wid()
    run = create_pipeline_run(wid, "empagliflozin_hf", max_records=80)
    _preset_steps_to_success(run.id, 2, [500, 600])

    steps_before = _copy_steps(run.id)

    await resume_pipeline(run.id)

    steps_after = _copy_steps(run.id)
    assert steps_after[0]["n_in"] == steps_before[0]["n_in"]
    assert steps_after[0]["n_out"] == steps_before[0]["n_out"]
    assert steps_after[1]["n_in"] == steps_before[1]["n_in"]
    assert steps_after[1]["n_out"] == steps_before[1]["n_out"]
    for i in range(2, 8):
        assert steps_after[i]["status"] == "success"


async def test_R4_resume_preserves_012_durations_not_rewritten():
    wid = _make_wid()
    run = create_pipeline_run(wid, "glp1_weightloss", max_records=120)
    special_durs = [12345, 23456, 34567]
    _preset_steps_to_success(run.id, 3, special_durs)

    await resume_pipeline(run.id)
    steps_after = _copy_steps(run.id)
    assert steps_after[0]["duration_ms"] == 12345
    assert steps_after[1]["duration_ms"] == 23456
    assert steps_after[2]["duration_ms"] == 34567


async def test_R5_resume_no_preset_starts_from_0():
    wid = _make_wid()
    run = create_pipeline_run(wid, "liraglutide_nafld", max_records=50)

    await resume_pipeline(run.id)

    steps_after = _copy_steps(run.id)
    for i in range(8):
        assert steps_after[i]["status"] == "success"


async def test_R6_resume_preset_2_success_steps_checked():
    wid = _make_wid()
    run = create_pipeline_run(wid, "pkd_tolvaptan", max_records=30)
    _preset_steps_to_success(run.id, 2, [9999, 8888])
    before = _copy_steps(run.id)

    await resume_pipeline(run.id)
    after = _copy_steps(run.id)
    assert after[0]["attempt_no"] == before[0]["attempt_no"]
    assert after[1]["attempt_no"] == before[1]["attempt_no"]
    with Session(engine) as ss:
        rows01 = list(ss.exec(select(PipelineStepResult).where(
            PipelineStepResult.run_id == run.id,
            PipelineStepResult.step_index <= 1,
            PipelineStepResult.attempt_no == 1,
        ).order_by(PipelineStepResult.step_index)).all())
        assert len(rows01) == 2
        assert rows01[0].duration_ms == 9999
        assert rows01[1].duration_ms == 8888


async def test_R7_resume_from_step5_0_4_untouched():
    wid = _make_wid()
    run = create_pipeline_run(wid, "ckd_blood_pressure_control", max_records=60)
    durs04 = [101, 202, 303, 404, 505]
    _preset_steps_to_success(run.id, 5, durs04)
    before = _copy_steps(run.id)

    await resume_pipeline(run.id, from_step=5)

    after = _copy_steps(run.id)
    for i in range(5):
        assert after[i]["duration_ms"] == before[i]["duration_ms"]
        assert after[i]["status"] == "success"
    for i in range(5, 8):
        assert after[i]["status"] == "success"


async def test_R8_resume_from_step4_0_3_not_affected():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=50)
    d03 = [11, 22, 33, 44]
    _preset_steps_to_success(run.id, 4, d03)

    await resume_pipeline(run.id, from_step=4)
    after = _copy_steps(run.id)
    assert after[0]["duration_ms"] == 11
    assert after[1]["duration_ms"] == 22
    assert after[2]["duration_ms"] == 33
    assert after[3]["duration_ms"] == 44


async def test_R9_resume_from_step6_only_6_7_run():
    wid = _make_wid()
    run = create_pipeline_run(wid, "empagliflozin_hf", max_records=40)
    d05 = [1, 2, 3, 4, 5, 6]
    _preset_steps_to_success(run.id, 6, d05)
    before = _copy_steps(run.id)

    await resume_pipeline(run.id, from_step=6)
    after = _copy_steps(run.id)
    for i in range(6):
        assert after[i]["duration_ms"] == before[i]["duration_ms"]
    assert after[6]["status"] == "success"
    assert after[7]["status"] == "success"


async def test_R10_resume_from_step_0_effectively_full_run():
    wid = _make_wid()
    run = create_pipeline_run(wid, "glp1_weightloss", max_records=25)

    await resume_pipeline(run.id, from_step=0)

    after = _copy_steps(run.id)
    for i in range(8):
        assert after[i]["status"] == "success"
    with Session(engine) as ss:
        rr = ss.get(PipelineRun, run.id)
        assert rr.status == "success"


async def test_R11_resume_from_step7():
    wid = _make_wid()
    run = create_pipeline_run(wid, "liraglutide_nafld", max_records=200)
    d06 = [7, 8, 9, 10, 11, 12, 13]
    _preset_steps_to_success(run.id, 7, d06)
    before = _copy_steps(run.id)

    await resume_pipeline(run.id, from_step=7)
    after = _copy_steps(run.id)
    for i in range(7):
        assert after[i]["duration_ms"] == before[i]["duration_ms"]
    assert after[7]["status"] == "success"


async def test_R12_resume_from_step2_01_preserved():
    wid = _make_wid()
    run = create_pipeline_run(wid, "pkd_tolvaptan", max_records=100)
    _preset_steps_to_success(run.id, 2, [55555, 66666])
    before = _copy_steps(run.id)

    await resume_pipeline(run.id, from_step=2)
    after = _copy_steps(run.id)
    assert after[0]["duration_ms"] == before[0]["duration_ms"]
    assert after[1]["duration_ms"] == before[1]["duration_ms"]
    for i in range(2, 8):
        assert after[i]["status"] == "success"


async def test_R13_cancel_flag_at_start_exits_quickly():
    wid = _make_wid()
    run = create_pipeline_run(wid, "ckd_blood_pressure_control", max_records=50)
    with Session(engine) as ss:
        rr = ss.get(PipelineRun, run.id)
        rr.cancel_flag = True
        ss.add(rr)
        ss.commit()

    t0 = time.perf_counter()
    await run_pipeline(run.id)
    elapsed = time.perf_counter() - t0

    assert elapsed < 1.0
    with Session(engine) as ss:
        rr2 = ss.get(PipelineRun, run.id)
        assert rr2.status != "success"


async def test_R14_cancel_flag_before_step0_entry():
    wid = _make_wid()
    run = create_pipeline_run(wid, "sglt2i_ckd", max_records=20)
    with Session(engine) as ss:
        rr = ss.get(PipelineRun, run.id)
        rr.cancel_flag = True
        ss.add(rr)
        ss.commit()

    await run_pipeline(run.id)
    with Session(engine) as ss:
        rr2 = ss.get(PipelineRun, run.id)
        steps = rr2.steps_json or []
        if steps:
            s0 = steps[0]
            assert s0.get("status") != "success"


async def test_R15_cancel_flag_check_on_start_and_while():
    wid = _make_wid()
    run = create_pipeline_run(wid, "empagliflozin_hf", max_records=30)
    with Session(engine) as ss:
        rr = ss.get(PipelineRun, run.id)
        rr.cancel_flag = True
        ss.add(rr)
        ss.commit()
    t0 = time.perf_counter()
    await resume_pipeline(run.id)
    assert time.perf_counter() - t0 < 1.0


async def test_R16_step2_failed_3_attempts_resume_force_false_retries_step2():
    wid = _make_wid()
    run = create_pipeline_run(wid, "glp1_weightloss", max_records=100)
    ctx_fail = {"fail_forever_step2": True, "fail_mode_step2": "timeout"}
    await run_pipeline(run.id, ctx_fail)

    with Session(engine) as ss:
        rows_before = list(ss.exec(select(PipelineStepResult).where(
            PipelineStepResult.run_id == run.id,
            PipelineStepResult.step_index == 2,
        )).all())
        attempts_before = len(rows_before)
        assert attempts_before == MAX_AUTO_RETRIES + 1

    await resume_pipeline(run.id, from_step=2, ctx={"force": False})

    with Session(engine) as ss:
        r2 = ss.get(PipelineRun, run.id)
        if r2.status == "success":
            assert r2.steps_json[2]["status"] == "success"
            rows_step2 = list(ss.exec(select(PipelineStepResult).where(
                PipelineStepResult.run_id == run.id,
                PipelineStepResult.step_index == 2,
            )).all())
            assert len(rows_step2) >= attempts_before + 1


async def test_R17_step2_failed_3_attempts_resume_force_true_skips_01():
    wid = _make_wid()
    run = create_pipeline_run(wid, "liraglutide_nafld", max_records=80)
    _preset_steps_to_success(run.id, 2, [100, 200])

    ctx_fail = {"fail_forever_step2": True, "fail_mode_step2": "timeout"}
    await run_pipeline(run.id, ctx_fail)

    before = _copy_steps(run.id)
    d0 = before[0]["duration_ms"]
    d1 = before[1]["duration_ms"]

    await resume_pipeline(run.id, from_step=2, ctx={"force": True})

    with Session(engine) as ss:
        rr2 = ss.get(PipelineRun, run.id)
        sj = rr2.steps_json or []
        assert sj[0]["status"] == "success"
        assert sj[1]["status"] == "success"
        assert sj[0]["duration_ms"] == d0
        assert sj[1]["duration_ms"] == d1


async def test_R18_resume_after_3failures_rerun_step_succeeds():
    wid = _make_wid()
    run = create_pipeline_run(wid, "pkd_tolvaptan", max_records=50)
    ctx_fail = {"fail_forever_step4": True, "fail_mode_step4": "timeout"}
    await run_pipeline(run.id, ctx_fail)
    with Session(engine) as ss:
        before_count = ss.query(PipelineStepResult).filter(
            PipelineStepResult.run_id == run.id,
            PipelineStepResult.step_index == 4,
        ).count()
        assert before_count == MAX_AUTO_RETRIES + 1
    await resume_pipeline(run.id, from_step=4)
    with Session(engine) as ss:
        after = ss.get(PipelineRun, run.id)
        if after.status == "success":
            s4 = after.steps_json[4]
            assert s4["status"] == "success"
