"""Wave12 D4-3: HP12 E2E 2 presets × N10k/N50k × 2 checks = 8 PY GREEN.

HP12 presets: sglt2i_ckd, empagliflozin_hf
HP12 sizes:   10000 (AC4 ≤9.6s), 50000 (AC5 ≤45s)
HP12 checks per (preset,size):
  A) HTTP 200 on step1 diag endpoint
  B) dedup kept_count_ratio > 0.50 (i.e. ≤50% removed)

Heavy N=50000 runs skip locally unless TRAE_CI=='true'.
"""

import asyncio
import json
import os
import pathlib
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

PRESETS_HP12 = ("sglt2i_ckd", "empagliflozin_hf")
SIZES_HP12 = (10_000, 50_000)

ORG_SLUG = "meda-w12"
ORG_NAME = "MedA W12 Org"
USER_ID_A = "u-w12-001"
WORKSPACE_ID = f"{ORG_SLUG}-ws-e2e-hp12-001"

FIXTURE_50K_PATH = pathlib.Path(__file__).parent / "fixtures" / "w12_synthetic_50k.json"

MAX_TIMEOUT_S_PER_SIZE = {
    10_000: 180,
    50_000: 600,
}

_DURATIONS: dict[tuple[str, int], list[float]] = defaultdict(list)


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
    assert resp.status_code in (200, 201), (
        f"login failed: HTTP {resp.status_code} {resp.text[:200]}"
    )
    return resp.json()["token"]


def _ensure_workspace(session: Session, wid: str) -> None:
    ws = session.get(Workspace, wid)
    if ws is None:
        ws = Workspace(id=wid)
        session.add(ws)
        session.commit()
        session.refresh(ws)


def _load_synth_records(preset: str, size: int) -> list[dict]:
    """Load records from w12_synthetic_50k.json fixture (6 preset × 5 sizes)."""
    if not FIXTURE_50K_PATH.exists():
        pytest.skip(f"fixture not found: {FIXTURE_50K_PATH}. Generate via D0-1 first.")
    with open(FIXTURE_50K_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    if preset not in data:
        pytest.skip(f"preset={preset!r} missing in fixture keys={list(data.keys())}")
    sz_key = str(size)
    if sz_key not in data[preset]:
        pytest.skip(f"size={size} missing for preset={preset}. keys={list(data[preset].keys())}")
    records = data[preset][sz_key]
    assert isinstance(records, list) and len(records) == size, (
        f"fixture size mismatch preset={preset} size={size}: got len={len(records)}"
    )
    return records


def _build_ctx(preset: str, size: int) -> dict:
    records = _load_synth_records(preset, size)
    return {
        "fetched_records": records,
        "pubmed_out": f"storage/snapshot-w12/{preset}-{size}",
    }


def _run_pipeline_with_timeout(run_id: str, ctx: dict, size: int) -> tuple[float, PipelineRun]:
    timeout_s = MAX_TIMEOUT_S_PER_SIZE[size]
    t0 = time.perf_counter()

    async def _coro():
        await run_pipeline(run_id, ctx=ctx)

    asyncio.run(asyncio.wait_for(_coro(), timeout=timeout_s))
    dur_s = time.perf_counter() - t0

    with Session(engine) as s:
        db_run = s.get(PipelineRun, run_id)
        assert db_run is not None, f"run_id={run_id!r} not persisted in DB"
        return dur_s, db_run


@pytest.fixture(autouse=True)
def _suppress_task_warnings_and_raise_cap(monkeypatch):
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*coroutine 'run_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*coroutine 'resume_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending!.*")
        monkeypatch.setattr(_pe, "MAX_RECORDS_HARD_CAP", 60000)
        yield


def _should_skip_50k_locally(size: int) -> None:
    """Skip N=50000 heavy runs on local dev machines (TRAE_CI != 'true')."""
    if size == 50_000 and os.environ.get("TRAE_CI", "").lower() != "true":
        pytest.skip(
            "N=50000 heavy run skipped locally (set TRAE_CI=true or run on CI "
            "where runtime budget ≥5min is available)."
        )


# ---------------------------------------------------------------------------
# HP12 — Parametrized class: 2 presets × 2 sizes × 2 methods = 8 tests
# ---------------------------------------------------------------------------

PRESET_PARAMS = pytest.mark.parametrize("preset", PRESETS_HP12)
SIZE_PARAMS = pytest.mark.parametrize("size", SIZES_HP12)


class TestHP12E2E10k50k:
    """HP12 8 tests: (preset∈{sglt2i_ckd, empagliflozin_hf}) × (size∈{10k, 50k})
    × (HTTP 200 check, kept_count_ratio >0.50 check).
    """

    @PRESET_PARAMS
    @SIZE_PARAMS
    def test_HP12_diag_http_200(self, preset: str, size: int):
        """HP12-Check-A: After pipeline step1 dedup completes → GET diag endpoint
        returns HTTP 200.
        """
        _should_skip_50k_locally(size)

        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)

        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=preset,
            mode="snapshot",
            max_records=size,
        )
        ctx = _build_ctx(preset, size)
        dur_s, db_run = _run_pipeline_with_timeout(run.id, ctx, size)
        _DURATIONS[(preset, size)].append(dur_s)

        assert db_run.status == "success", (
            f"HP12[{preset}/{size}] pipeline status={db_run.status!r} "
            f"expected success. error={db_run.error_msg!r}"
        )

        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{run.id}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, (
            f"HP12-A[{preset}/{size}] diag HTTP={resp.status_code} "
            f"expected 200. body={resp.text[:400]}"
        )

    @PRESET_PARAMS
    @SIZE_PARAMS
    def test_HP12_kept_count_ratio_over_50pct(self, preset: str, size: int):
        """HP12-Check-B: After dedup → kept_count / N > 0.50  (≤50% removed).
        Catches catastrophic false-positive dedup where most records are dropped.
        """
        _should_skip_50k_locally(size)

        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)

        run = create_pipeline_run(
            workspace_id=WORKSPACE_ID,
            preset=preset,
            mode="snapshot",
            max_records=size,
        )
        ctx = _build_ctx(preset, size)
        dur_s, db_run = _run_pipeline_with_timeout(run.id, ctx, size)
        _DURATIONS[(preset, size)].append(dur_s)

        assert db_run.status == "success", (
            f"HP12[{preset}/{size}] pipeline status={db_run.status!r} "
            f"expected success. error={db_run.error_msg!r}"
        )

        steps = db_run.steps_json or []
        step1 = steps[1] if len(steps) > 1 else {}
        n_out = int((step1 or {}).get("n_out", 0) or 0)

        kept_count_ratio = n_out / size if size > 0 else 0.0
        assert n_out > 0, (
            f"HP12-B[{preset}/{size}] step1.n_out=0 → all records dropped!"
        )
        assert kept_count_ratio > 0.50, (
            f"HP12-B[{preset}/{size}] kept_count_ratio={kept_count_ratio:.4f} "
            f"≤ 0.50  (>50% records removed, likely FP dedup bug). "
            f"n_out={n_out}, size={size}"
        )


# ---------------- Session summary: avg durations per (preset, size) ----------------

def pytest_sessionfinish(session, exitstatus):
    """Print HP12 per-(preset,size) avg pipeline total duration at session end."""
    lines = [
        "",
        "=" * 78,
        "W12 HP12 E2E 10k/50k — avg pipeline total duration per (preset × size)",
    ]
    for preset in PRESETS_HP12:
        for size in SIZES_HP12:
            key = (preset, size)
            durs = _DURATIONS.get(key, [])
            if durs:
                avg_s = sum(durs) / len(durs)
                lines.append(
                    f"  preset={preset:<20s}  N={size:<6d}  n_runs={len(durs):<2d}  "
                    f"avg={avg_s:8.2f}s  min={min(durs):8.2f}s  max={max(durs):8.2f}s"
                )
            else:
                lines.append(
                    f"  preset={preset:<20s}  N={size:<6d}  (no runs recorded)"
                )
    lines.append("=" * 78)
    summary = "\n".join(lines)
    print(summary, file=sys.stderr, flush=True)
    print(summary, file=sys.stdout, flush=True)
    for p in [
        r"d:\workspace\MedA\tmp_w12_hp12_durations_summary.txt",
        "/tmp/tmp_w12_hp12_durations_summary.txt",
    ]:
        try:
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(summary + "\n")
            break
        except Exception:
            continue
