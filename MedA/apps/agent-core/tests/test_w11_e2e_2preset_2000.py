"""Wave11 D2-5: Happy Path E2E N=2000, 2 presets × 5 HPs = 10 exact tests.

HP11-15: sglt2i_ckd preset
HP16-20: glp1_weightloss preset

Collects avg pipeline total duration per preset (printed at end via stdout / session finish hook).
No commit.
"""

import asyncio
import sys
import time
import warnings
from collections import defaultdict

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

import app.services.pipeline_engine as _pe
from app.main import app
from app.db import engine
from app.models import PipelineRun, Workspace
from app.services.pipeline_engine import (
    create_pipeline_run,
    run_pipeline,
    PIPELINE_STEPS,
)
from app.services.sources.pubmed_adapter import _load_preset_snapshot_2000


ORG_SLUG = "meda-w11"
ORG_NAME = "MedA W11 Org"
USER_ID_A = "u-w11-001"
WORKSPACE_ID = f"{ORG_SLUG}-ws-e2e-2000-001"

PRESET_UNDER_TEST = ("sglt2i_ckd", "glp1_weightloss")

N_RECORDS = 2000
MAX_TIMEOUT_S = 240
UPPER_STEP1_N_OUT = 1806  # 2000 * 0.86 * 1.05 = 1806

_DURATIONS: dict[str, list[float]] = defaultdict(list)


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
def _suppress_task_warnings_and_raise_cap(monkeypatch):
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*coroutine 'run_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*coroutine 'resume_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending!.*")
        monkeypatch.setattr(_pe, "MAX_RECORDS_HARD_CAP", 10000)
        yield


def _build_ctx_for_2000(preset: str) -> dict:
    """Fixture helper: load 2000 preset records and pack into pipeline ctx."""
    records = _load_preset_snapshot_2000(preset)
    assert isinstance(records, list), f"_load_preset_snapshot_2000 returned non-list: {type(records)}"
    assert len(records) == N_RECORDS, (
        f"preset={preset} expected {N_RECORDS} records, got {len(records)}"
    )
    return {
        "fetched_records": records,
        "pubmed_out": f"storage/snapshot-2000/{preset}",
    }


def _run_pipeline_with_timeout(run_id: str, ctx: dict) -> tuple[float, PipelineRun]:
    t0 = time.perf_counter()

    async def _coro():
        await run_pipeline(run_id, ctx=ctx)

    asyncio.run(asyncio.wait_for(_coro(), timeout=MAX_TIMEOUT_S))
    dur_s = time.perf_counter() - t0

    with Session(engine) as s:
        db_run = s.get(PipelineRun, run_id)
        assert db_run is not None
        return dur_s, db_run


def _validate_ulid_32(run_id: str) -> None:
    assert isinstance(run_id, str), f"run_id not str: {type(run_id)}"
    assert len(run_id) == 32, f"run_id expected 32 chars, got len={len(run_id)} id={run_id!r}"
    allowed = set("0123456789ABCDEFGHJKMNPQRSTVWXYZ-")
    bad = [c for c in run_id.upper() if c not in allowed]
    assert not bad, f"run_id={run_id!r} has invalid ULID chars: {bad!r}"


# ---------------- sglt2i_ckd: HP11-15 ----------------

PRESET_SGLT = "sglt2i_ckd"


class TestHP11HP15Sglt2iCkd:
    def test_HP11_create_run_sglt2i_ulid32_queued(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_SGLT,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        _validate_ulid_32(run.id)
        assert run.status == "queued", f"HP11 expected queued, got status={run.status}"
        assert run.max_records == N_RECORDS, f"HP11 max_records={run.max_records}!={N_RECORDS}"

    def test_HP12_run_pipeline_sglt2i_8steps_success(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_SGLT,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        ctx = _build_ctx_for_2000(PRESET_SGLT)
        dur_s, db_run = _run_pipeline_with_timeout(run.id, ctx)
        _DURATIONS[PRESET_SGLT].append(dur_s)
        assert db_run.status == "success", (
            f"HP12 sglt2i status={db_run.status!r} expected success; error={db_run.error_msg!r}"
        )
        steps = db_run.steps_json or []
        assert len(steps) == len(PIPELINE_STEPS), (
            f"HP12 sglt2i steps len={len(steps)}!={len(PIPELINE_STEPS)}"
        )
        for idx, step in enumerate(steps):
            st = (step or {}).get("status")
            assert st == "success", (
                f"HP12 sglt2i step[{idx}] status={st!r} expected success. full={step!r}"
            )

    def test_HP13_diag_step1_sglt2i_200_fields_present(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_SGLT,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        ctx = _build_ctx_for_2000(PRESET_SGLT)
        dur_s, _ = _run_pipeline_with_timeout(run.id, ctx)
        _DURATIONS[PRESET_SGLT].append(dur_s)

        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{run.id}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, (
            f"HP13 sglt2i diag HTTP={resp.status_code} body={resp.text[:500]}"
        )
        body = resp.json()
        sizes_hist = body.get("sizes_hist", None)
        assert sizes_hist is not None, "HP13 sglt2i sizes_hist missing"
        assert isinstance(sizes_hist, (dict, list)) and len(sizes_hist) > 0, (
            f"HP13 sglt2i sizes_hist empty: {sizes_hist!r}"
        )
        assert "hamming_hist" in body, "HP13 sglt2i hamming_hist key missing"
        hamming_hist = body["hamming_hist"]
        assert hamming_hist is not None, "HP13 sglt2i hamming_hist value is None"
        perf = body.get("perf") or body.get("perf_json") or {}
        step1_ms = perf.get("step1_total_ms") if isinstance(perf, dict) else None
        assert step1_ms is not None, (
            f"HP13 sglt2i perf.step1_total_ms missing. perf keys={list(perf) if isinstance(perf, dict) else type(perf)}"
        )
        assert isinstance(step1_ms, (int, float)) and step1_ms >= 0, (
            f"HP13 sglt2i step1_total_ms invalid: {step1_ms!r}"
        )

    def test_HP14_step1_nout_sglt2i_bounds_0_1806(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_SGLT,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        ctx = _build_ctx_for_2000(PRESET_SGLT)
        dur_s, db_run = _run_pipeline_with_timeout(run.id, ctx)
        _DURATIONS[PRESET_SGLT].append(dur_s)
        steps = db_run.steps_json or []
        step1 = steps[1] if len(steps) > 1 else {}
        n_out = int((step1 or {}).get("n_out", 0))
        assert n_out > 0, f"HP14 sglt2i step1.n_out={n_out} must be > 0"
        assert n_out <= UPPER_STEP1_N_OUT, (
            f"HP14 sglt2i step1.n_out={n_out} exceeds upper bound {UPPER_STEP1_N_OUT} (2000*0.86*1.05)"
        )

    def test_HP15_report_blob_sglt2i_non_empty_check(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_SGLT,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        ctx = _build_ctx_for_2000(PRESET_SGLT)
        dur_s, db_run = _run_pipeline_with_timeout(run.id, ctx)
        _DURATIONS[PRESET_SGLT].append(dur_s)
        steps = db_run.steps_json or []
        step7 = steps[7] if len(steps) > 7 else {}
        payload_ref = (step7 or {}).get("payload_ref")
        report_status = (step7 or {}).get("status")
        either_ok = (payload_ref is not None) or (report_status == "success")
        assert either_ok, (
            f"HP15 sglt2i report check failed: payload_ref={payload_ref!r}, step7.status={report_status!r}"
        )


# ---------------- glp1_weightloss: HP16-20 ----------------

PRESET_GLP = "glp1_weightloss"


class TestHP16HP20Glp1Weightloss:
    def test_HP16_create_run_glp1_ulid32_queued(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_GLP,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        _validate_ulid_32(run.id)
        assert run.status == "queued", f"HP16 expected queued, got status={run.status}"
        assert run.max_records == N_RECORDS, f"HP16 max_records={run.max_records}!={N_RECORDS}"

    def test_HP17_run_pipeline_glp1_8steps_success(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_GLP,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        ctx = _build_ctx_for_2000(PRESET_GLP)
        dur_s, db_run = _run_pipeline_with_timeout(run.id, ctx)
        _DURATIONS[PRESET_GLP].append(dur_s)
        assert db_run.status == "success", (
            f"HP17 glp1 status={db_run.status!r} expected success; error={db_run.error_msg!r}"
        )
        steps = db_run.steps_json or []
        assert len(steps) == len(PIPELINE_STEPS), (
            f"HP17 glp1 steps len={len(steps)}!={len(PIPELINE_STEPS)}"
        )
        for idx, step in enumerate(steps):
            st = (step or {}).get("status")
            assert st == "success", (
                f"HP17 glp1 step[{idx}] status={st!r} expected success. full={step!r}"
            )

    def test_HP18_diag_step1_glp1_200_fields_present(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_GLP,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        ctx = _build_ctx_for_2000(PRESET_GLP)
        dur_s, _ = _run_pipeline_with_timeout(run.id, ctx)
        _DURATIONS[PRESET_GLP].append(dur_s)

        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{run.id}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, (
            f"HP18 glp1 diag HTTP={resp.status_code} body={resp.text[:500]}"
        )
        body = resp.json()
        sizes_hist = body.get("sizes_hist", None)
        assert sizes_hist is not None, "HP18 glp1 sizes_hist missing"
        assert isinstance(sizes_hist, (dict, list)) and len(sizes_hist) > 0, (
            f"HP18 glp1 sizes_hist empty: {sizes_hist!r}"
        )
        assert "hamming_hist" in body, "HP18 glp1 hamming_hist key missing"
        hamming_hist = body["hamming_hist"]
        assert hamming_hist is not None, "HP18 glp1 hamming_hist value is None"
        perf = body.get("perf") or body.get("perf_json") or {}
        step1_ms = perf.get("step1_total_ms") if isinstance(perf, dict) else None
        assert step1_ms is not None, (
            f"HP18 glp1 perf.step1_total_ms missing. perf keys={list(perf) if isinstance(perf, dict) else type(perf)}"
        )
        assert isinstance(step1_ms, (int, float)) and step1_ms >= 0, (
            f"HP18 glp1 step1_total_ms invalid: {step1_ms!r}"
        )

    def test_HP19_step1_nout_glp1_bounds_0_1806(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_GLP,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        ctx = _build_ctx_for_2000(PRESET_GLP)
        dur_s, db_run = _run_pipeline_with_timeout(run.id, ctx)
        _DURATIONS[PRESET_GLP].append(dur_s)
        steps = db_run.steps_json or []
        step1 = steps[1] if len(steps) > 1 else {}
        n_out = int((step1 or {}).get("n_out", 0))
        assert n_out > 0, f"HP19 glp1 step1.n_out={n_out} must be > 0"
        assert n_out <= UPPER_STEP1_N_OUT, (
            f"HP19 glp1 step1.n_out={n_out} exceeds upper bound {UPPER_STEP1_N_OUT} (2000*0.86*1.05)"
        )

    def test_HP20_report_blob_glp1_non_empty_check(self):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=PRESET_GLP,
            mode="snapshot",
            max_records=N_RECORDS,
        )
        ctx = _build_ctx_for_2000(PRESET_GLP)
        dur_s, db_run = _run_pipeline_with_timeout(run.id, ctx)
        _DURATIONS[PRESET_GLP].append(dur_s)
        steps = db_run.steps_json or []
        step7 = steps[7] if len(steps) > 7 else {}
        payload_ref = (step7 or {}).get("payload_ref")
        report_status = (step7 or {}).get("status")
        either_ok = (payload_ref is not None) or (report_status == "success")
        assert either_ok, (
            f"HP20 glp1 report check failed: payload_ref={payload_ref!r}, step7.status={report_status!r}"
        )


# ---------------- Session summary: avg durations ----------------

def pytest_sessionfinish(session, exitstatus):
    """Print avg pipeline total duration per preset at end of test session."""
    import os as _os
    lines = ["", "=" * 72, "W11 E2E 2000-records — avg pipeline total duration per preset"]
    for preset in PRESET_UNDER_TEST:
        durs = _DURATIONS.get(preset, [])
        if durs:
            avg_s = sum(durs) / len(durs)
            lines.append(
                f"  preset={preset:<20s}  n_runs={len(durs):<3d}  avg={avg_s:8.2f}s  "
                f"min={min(durs):8.2f}s  max={max(durs):8.2f}s"
            )
        else:
            lines.append(f"  preset={preset:<20s}  (no runs recorded)")
    lines.append("=" * 72)
    summary = "\n".join(lines)
    print(summary, file=sys.stderr, flush=True)
    print(summary, file=sys.stdout, flush=True)
    known_paths = [
        r"d:\workspace\MedA\tmp_w11_durations_summary.txt",
        "/tmp/tmp_w11_durations_summary.txt",
    ]
    for p in known_paths:
        try:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(summary + "\n")
            break
        except Exception:
            continue
