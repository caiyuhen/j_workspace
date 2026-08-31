"""W10 D2-3: Happy Path E2E 2 presets + Cancel = 10 pytest GREEN HP1-10.

Final PY test file; passing pushes W10 PY total past AC1 target >= 130
(12 models + 50 engine + 14 hybrid + 24 routes + 20 compare + 10 e2e = 130).
"""

import asyncio
import sys
import warnings
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.db import engine
from app.models import PipelineRun, Workspace
from app.services.pipeline_engine import (
    create_pipeline_run,
    run_pipeline,
    resume_pipeline,
    compute_funnel_counts_for_run,
    compute_rob2_delta,
    compute_grade_delta,
    compute_funnel_delta,
    PIPELINE_STEPS,
)


ORG_SLUG = "meda-w10"
ORG_NAME = "MedA W10 Org"
USER_ID_A = "u-w10-001"
WORKSPACE_ID = f"{ORG_SLUG}-ws-e2e-001"



_PRESET_SIZES = {
    "sglt2i_ckd": 178,
    "empagliflozin_hf": 132,
    "glp1_weightloss": 188,
    "liraglutide_nafld": 112,
    "pkd_tolvaptan": 74,
    "ckd_blood_pressure_control": 156,
}


def _dev_login(client: TestClient, org_slug: str, org_name: str, user_id: str) -> str:
    resp = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": org_slug,
            "organization_name": org_name,
            "user_id": user_id,
            "display_name": f"User {user_id}",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    assert resp.status_code in (200, 201), f"login failed: {resp.status_code} {resp.text}"
    return resp.json()["token"]


def _ensure_workspace(session: Session, wid: str) -> None:
    ws = session.get(Workspace, wid)
    if ws is None:
        ws = Workspace(id=wid)
        session.add(ws)
        session.commit()
        session.refresh(ws)


@pytest.fixture(autouse=True)
def _suppress_task_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*coroutine 'run_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*coroutine 'resume_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending!.*")
        yield


def _assert_funnel_monotonic(steps: list[dict], label: str) -> None:
    """Step0 fetches the real preset corpus and step1 runs real dedup, so exact
    per-step counts are data-dependent. Assert the funnel invariants instead:
    every stage is >= 1, never grows, and the final report step emits exactly 1.
    """
    prev = None
    for i, step in enumerate(steps):
        n_out = int(step.get("n_out", 0))
        assert n_out >= 1, f"{label} step{i} n_out={n_out} must be >= 1"
        if prev is not None:
            assert n_out <= prev, (
                f"{label} step{i} n_out={n_out} grew above previous step ({prev}); "
                "the screening funnel must be monotonically non-increasing"
            )
        prev = n_out
    assert int(steps[7].get("n_out", 0)) == 1, (
        f"{label} step7 must emit exactly 1 report, got {steps[7].get('n_out')}"
    )


def _set_cancel_after_step(session: Session, run_id: str, step_index: int) -> dict:
    """Create a hook: after mark_step_success(step==step_index), set cancel_flag=True.

    We monkeypatch mark_step_success to flip the cancel_flag right after the target
    step completes so the loop exits on next iteration.
    """
    from app.services import pipeline_engine as _pe

    original_mark = _pe.mark_step_success

    def _patched_mark(run, idx, *args, **kwargs):
        result = original_mark(run, idx, *args, **kwargs)
        if idx == step_index:
            with Session(engine) as s:
                db_run = s.get(PipelineRun, run_id)
                if db_run is not None:
                    db_run.cancel_flag = True
                    s.add(db_run)
                    s.commit()
        return result

    return {"_original_mark": original_mark, "_patched_mark": _patched_mark}


class TestHP1HP3Sglt2iCkdRun:
    def test_HP1_post_run_200_success(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "preset": "sglt2i_ckd",
                "mode": "snapshot",
                "max_records": 200,
            },
        )
        assert resp.status_code == 200, f"HP1 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "run_id" in body, "HP1 missing run_id"
        assert isinstance(body["run_id"], str) and len(body["run_id"]) > 0

    def test_HP2_run_sync_8_steps_success_lengths(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset="sglt2i_ckd",
            mode="snapshot",
            max_records=200,
        )
        asyncio.run(run_pipeline(run.id, ctx={}))

        with Session(engine) as s:
            db_run = s.get(PipelineRun, run.id)
            assert db_run is not None
            assert db_run.status == "success", f"HP2 status expected success, got {db_run.status}"
            steps = db_run.steps_json
            assert len(steps) == 8, f"HP2 expected 8 steps, got {len(steps)}"
            for i, step in enumerate(steps):
                assert step.get("status") == "success", f"HP2 step{i} status {step.get('status')}"

            _assert_funnel_monotonic(steps, "HP2")

    def test_HP3_detail_funnel_grade_rob_finished_report(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset="sglt2i_ckd",
            mode="snapshot",
            max_records=200,
        )
        asyncio.run(run_pipeline(run.id, ctx={}))

        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{run.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"HP3 detail non-200: {resp.status_code} {resp.text}"
        body = resp.json()

        finished_at = body.get("finished_at")
        assert finished_at is not None, "HP3 finished_at missing"
        try:
            datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pytest.fail(f"HP3 finished_at not ISO format: {finished_at!r}")

        report_url = body.get("report_url", "")
        assert report_url.endswith("/report.md"), f"HP3 report_url wrong: {report_url}"

        with Session(engine) as s:
            db_run = s.get(PipelineRun, run.id)
            funnel_counts = compute_funnel_counts_for_run(db_run)
            assert len(funnel_counts) == 8, f"HP3 funnel_counts len={len(funnel_counts)} != 8"
            for v in funnel_counts:
                assert isinstance(v, int), f"HP3 funnel_counts value {v!r} not int"

            rob_delta = compute_rob2_delta(db_run, db_run)
            rob_keys = {row["overall"] for row in rob_delta}
            assert rob_keys == {"low", "some", "high"}, f"HP3 rob2 keys wrong: {rob_keys}"

            grade_delta = compute_grade_delta(db_run, db_run)
            grade_keys = {row["a"] for row in grade_delta} | {row["b"] for row in grade_delta}
            assert grade_keys.issubset({"H", "M", "L"}), f"HP3 grade keys not H/M/L: {grade_keys}"


class TestHP4HP6Glp1Weightloss:
    def test_HP4_post_glp1_run_distinct_id(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid_a = create_pipeline_run(
                workspace_id=WORKSPACE_ID,
                preset="sglt2i_ckd",
                mode="snapshot",
                max_records=50,
            )
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "preset": "glp1_weightloss",
                "mode": "snapshot",
                "max_records": 188,
            },
        )
        assert resp.status_code == 200, f"HP4 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        glp1_id = body["run_id"]
        assert glp1_id != rid_a.id, "HP4 glp1 run_id should differ from sglt2i run_id"

    def test_HP5_glp1_run_success_step0_188(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset="glp1_weightloss",
            mode="snapshot",
            max_records=188,
        )
        assert run.max_records == _PRESET_SIZES["glp1_weightloss"], (
            f"HP5 max_records={run.max_records} != preset_sizes {_PRESET_SIZES['glp1_weightloss']}"
        )
        asyncio.run(run_pipeline(run.id, ctx={}))

        with Session(engine) as s:
            db_run = s.get(PipelineRun, run.id)
            assert db_run.status == "success", f"HP5 status expected success, got {db_run.status}"
            steps = db_run.steps_json
            assert len(steps) == 8, f"HP5 expected 8 steps, got {len(steps)}"
            for i, step in enumerate(steps):
                assert step.get("status") == "success", f"HP5 step{i} status {step.get('status')}"

            step0_n_out = int((steps[0] or {}).get("n_out", 0))
            assert step0_n_out == _PRESET_SIZES["glp1_weightloss"], (
                f"HP5 step0.n_out={step0_n_out} must equal the real fetched corpus size "
                f"{_PRESET_SIZES['glp1_weightloss']}"
            )
            _assert_funnel_monotonic(steps, "HP5")

    def test_HP6_list_filter_glp1_only(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            sglt = create_pipeline_run(
                workspace_id=WORKSPACE_ID,
                preset="sglt2i_ckd",
                mode="snapshot",
                max_records=100,
            )
            glp1 = create_pipeline_run(
                workspace_id=WORKSPACE_ID,
                preset="glp1_weightloss",
                mode="snapshot",
                max_records=100,
            )
            asyncio.run(run_pipeline(sglt.id, ctx={}))
            asyncio.run(run_pipeline(glp1.id, ctx={}))

        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines",
            headers={"Authorization": f"Bearer {token}"},
            params={"preset": "glp1_weightloss", "per_page": 100},
        )
        assert resp.status_code == 200, f"HP6 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        runs = body.get("runs", [])
        presets_found = [r.get("preset") for r in runs]
        assert "sglt2i_ckd" not in presets_found, "HP6 sglt2i should be excluded by filter"
        glp1_count = sum(1 for r in runs if r.get("preset") == "glp1_weightloss")
        assert glp1_count == 1, f"HP6 expected exactly 1 glp1 run, got {glp1_count}"


class TestHP7HP8CancelResume:
    def test_HP7_cancel_after_step2(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset="sglt2i_ckd",
            mode="snapshot",
            max_records=150,
        )
        run_id = run.id

        from app.services import pipeline_engine as _pe
        original_mark = _pe.mark_step_success

        def _patched_mark(run_obj, idx, *args, **kwargs):
            result = original_mark(run_obj, idx, *args, **kwargs)
            if idx == 2:
                with Session(engine) as s2:
                    db_run = s2.get(PipelineRun, run_id)
                    if db_run is not None:
                        db_run.cancel_flag = True
                        s2.add(db_run)
                        s2.commit()
            return result

        _pe.mark_step_success = _patched_mark
        try:
            asyncio.run(run_pipeline(run_id, ctx={}))
        finally:
            _pe.mark_step_success = original_mark

        with Session(engine) as s:
            db_run = s.get(PipelineRun, run_id)
            assert db_run is not None
            assert db_run.status != "success", (
                f"HP7 should not be success, got {db_run.status}"
            )
            assert db_run.current_step_index <= 4, (
                f"HP7 current_step_index={db_run.current_step_index} > 4"
            )
            steps = db_run.steps_json
            for i in range(3):
                assert steps[i].get("status") == "success", (
                    f"HP7 step{i} should be success, got {steps[i].get('status')}"
                )
            found_further_success = False
            for i in range(3, 8):
                if steps[i].get("status") == "success":
                    found_further_success = True
                    break
            assert not found_further_success, (
                "HP7 no steps after step2 should be success"
            )

    def test_HP8_resume_cancelled_from_step3(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset="sglt2i_ckd",
            mode="snapshot",
            max_records=150,
        )
        run_id = run.id

        from app.services import pipeline_engine as _pe
        original_mark = _pe.mark_step_success

        def _patched_mark(run_obj, idx, *args, **kwargs):
            result = original_mark(run_obj, idx, *args, **kwargs)
            if idx == 2:
                with Session(engine) as s2:
                    db_run = s2.get(PipelineRun, run_id)
                    if db_run is not None:
                        db_run.cancel_flag = True
                        s2.add(db_run)
                        s2.commit()
            return result

        _pe.mark_step_success = _patched_mark
        try:
            asyncio.run(run_pipeline(run_id, ctx={}))
        finally:
            _pe.mark_step_success = original_mark

        with Session(engine) as s3:
            db_run_pre = s3.get(PipelineRun, run_id)
            if db_run_pre is not None:
                db_run_pre.cancel_flag = False
                s3.add(db_run_pre)
                s3.commit()

        asyncio.run(resume_pipeline(run_id, from_step=3, ctx={"force": True}))

        with Session(engine) as s:
            db_run = s.get(PipelineRun, run_id)
            assert db_run.status == "success", (
                f"HP8 final status expected success, got {db_run.status}"
            )
            steps = db_run.steps_json
            assert len(steps) == 8
            for i in range(8):
                assert steps[i].get("status") == "success", (
                    f"HP8 step{i} not success: {steps[i].get('status')}"
                )
            funnel = compute_funnel_counts_for_run(db_run)
            assert len(funnel) == 8
            _assert_funnel_monotonic([{"n_out": n} for n in funnel], "HP8")


class TestHP9HP10CompareNoRequests:
    def test_HP9_compare_funnel_rob_grade_pico(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        sglt = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset="sglt2i_ckd",
            mode="snapshot",
            max_records=200,
        )
        glp1 = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset="glp1_weightloss",
            mode="snapshot",
            max_records=188,
        )
        asyncio.run(run_pipeline(sglt.id, ctx={}))
        asyncio.run(run_pipeline(glp1.id, ctx={}))

        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{sglt.id}/{glp1.id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"metrics": "funnel,rob,grade,pico"},
        )
        assert resp.status_code == 200, f"HP9 non-200: {resp.status_code} {resp.text}"
        body = resp.json()

        for key in ("funnel_delta", "rob2_delta", "grade_delta", "pico"):
            assert key in body, f"HP9 missing section {key}"

        with Session(engine) as s:
            sglt_db = s.get(PipelineRun, sglt.id)
            glp1_db = s.get(PipelineRun, glp1.id)
            delta = compute_funnel_delta(sglt_db, glp1_db)

        step0 = delta[0]
        # step0 now reports the real fetched corpus size, which is capped by the
        # preset's own snapshot size rather than by max_records.
        expected_diff = _PRESET_SIZES["sglt2i_ckd"] - _PRESET_SIZES["glp1_weightloss"]
        actual_diff = step0["diff"]
        assert actual_diff == expected_diff, (
            f"HP9 funnel_delta[0].diff={actual_diff}, expected {expected_diff} "
            f"(real corpus sizes {_PRESET_SIZES['sglt2i_ckd']} vs {_PRESET_SIZES['glp1_weightloss']})"
        )

        grade_sglt = compute_grade_delta(sglt_db, sglt_db)
        grade_glp1 = compute_grade_delta(glp1_db, glp1_db)
        sglt_first = grade_sglt[0]["outcome"]
        glp1_first = grade_glp1[0]["outcome"]
        assert sglt_first != glp1_first, (
            f"HP9 grade first outcomes should differ: sglt={sglt_first!r} glp1={glp1_first!r}"
        )

    def test_HP10_snapshot_no_requests_import(self, monkeypatch):
        class _NoRequests:
            def __getattr__(self, name):
                raise ImportError("requests module blocked by HP10 test: snapshot should not import requests")
        monkeypatch.setitem(sys.modules, "requests", None)

        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset="sglt2i_ckd",
            mode="snapshot",
            max_records=200,
        )
        asyncio.run(run_pipeline(run.id, ctx={}))

        with Session(engine) as s:
            db_run = s.get(PipelineRun, run.id)
            assert db_run.status == "success", (
                f"HP10 status expected success, got {db_run.status}"
            )
            steps = db_run.steps_json
            success_count = sum(
                1 for st in steps if st.get("status") == "success"
            )
            assert success_count == 8, f"HP10 expected 8/8 success steps, got {success_count}"
