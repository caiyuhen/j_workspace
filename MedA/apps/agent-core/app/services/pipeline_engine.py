from __future__ import annotations

import asyncio
import os
import time
from datetime import datetime
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db import engine
from app.models import PipelineRun, PipelineStepResult, Workspace


PIPELINE_STEPS: list[dict[str, Any]] = [
    {"step_index": 0, "step_name": "pubmed_fetch", "description": "Fetch PubMed records"},
    {"step_index": 1, "step_name": "simhash_dedupe", "description": "Deduplicate via simhash"},
    {"step_index": 2, "step_name": "screen_ta", "description": "Title/Abstract screening"},
    {"step_index": 3, "step_name": "screen_ft", "description": "Full-text screening + EAs"},
    {"step_index": 4, "step_name": "abstractor", "description": "Abstractor triage"},
    {"step_index": 5, "step_name": "rob2_assessment", "description": "RoB 2.0 assessment"},
    {"step_index": 6, "step_name": "grade_downgrade", "description": "GRADE downgrade"},
    {"step_index": 7, "step_name": "report_generate", "description": "Report generation"},
]

STEP_NAMES_MAP: dict[str, int] = {s["step_name"]: s["step_index"] for s in PIPELINE_STEPS}

VALID_PRESETS: tuple[str, ...] = (
    "sglt2i_ckd",
    "empagliflozin_hf",
    "glp1_weightloss",
    "liraglutide_nafld",
    "pkd_tolvaptan",
    "ckd_blood_pressure_control",
)

MAX_RECORDS_HARD_CAP: int = 200
MAX_AUTO_RETRIES: int = 2
RETRY_BACKOFFS_SEC: tuple[int, ...] = (1, 4)


_ULID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
_ULID_LEN = 30


def _ulid_run_id() -> str:
    ts = int(time.time() * 1000)
    ts_chars = []
    for _ in range(10):
        ts_chars.append(_ULID_ALPHABET[ts % 32])
        ts //= 32
    ts_chars.reverse()
    rand_bytes = os.urandom(16)
    rand_int = int.from_bytes(rand_bytes, "big")
    rand_chars = []
    for _ in range(22):
        rand_chars.append(_ULID_ALPHABET[rand_int % 32])
        rand_int //= 32
    rand_chars.reverse()
    raw = "".join(ts_chars) + "".join(rand_chars)
    return "p-" + raw[:_ULID_LEN]


def _default_steps_json() -> list[dict[str, Any]]:
    return [
        {
            "step_index": s["step_index"],
            "step_name": s["step_name"],
            "status": "pending",
            "attempt_no": 0,
            "started_at": None,
            "finished_at": None,
            "duration_ms": 0,
            "n_in": 0,
            "n_out": 0,
            "payload_ref": None,
            "error_msg": None,
        }
        for s in PIPELINE_STEPS
    ]


def create_pipeline_run(
    workspace_id: str,
    preset: str,
    mode: str = "snapshot",
    max_records: int = 200,
) -> PipelineRun:
    assert 1 <= max_records <= MAX_RECORDS_HARD_CAP, f"max_records must be 1..{MAX_RECORDS_HARD_CAP}"
    assert preset in VALID_PRESETS, f"invalid preset: {preset}"
    assert mode in ("snapshot", "live"), f"invalid mode: {mode}"

    with Session(engine) as session:
        ws = session.get(Workspace, workspace_id)
        if ws is None:
            ws = Workspace(id=workspace_id)
            session.add(ws)
            session.flush()

        run = PipelineRun(
            id=_ulid_run_id(),
            workspace_id=workspace_id,
            preset=preset,
            mode=mode,
            max_records=max_records,
            status="queued",
            current_step_index=0,
            cancel_flag=False,
            steps_json=_default_steps_json(),
            error_msg=None,
            report_blob_path=None,
            pico_csv_blob_path=None,
        )
        session.add(run)
        session.commit()
        session.refresh(run)
        out = PipelineRun(
            id=run.id,
            workspace_id=run.workspace_id,
            preset=run.preset,
            mode=run.mode,
            max_records=run.max_records,
            status=run.status,
            current_step_index=run.current_step_index,
            cancel_flag=run.cancel_flag,
            steps_json=[dict(x) for x in run.steps_json],
            error_msg=run.error_msg,
            report_blob_path=run.report_blob_path,
            pico_csv_blob_path=run.pico_csv_blob_path,
            created_at=run.created_at,
            updated_at=run.updated_at,
            finished_at=run.finished_at,
        )
        return out


def _upsert_step_info_to_run_json(run: PipelineRun, idx: int, **kwargs: Any) -> None:
    assert 0 <= idx < 8, f"step index out of range: {idx}"
    if not run.steps_json or len(run.steps_json) != 8:
        run.steps_json = _default_steps_json()
    new_steps = [dict(s) for s in run.steps_json]
    step = new_steps[idx]
    for k, v in kwargs.items():
        step[k] = v
    run.steps_json = new_steps
    run.updated_at = datetime.utcnow()


def _max_attempt_in_db(session: Session, run_id: str, step_index: int) -> int:
    rows = list(session.exec(
        select(PipelineStepResult).where(
            PipelineStepResult.run_id == run_id,
            PipelineStepResult.step_index == step_index,
        )
    ).all())
    if not rows:
        return 0
    return max(r.attempt_no for r in rows)


def _next_attempt_no(run_id: str, step_index: int) -> int:
    with Session(engine) as session:
        m = _max_attempt_in_db(session, run_id, step_index)
    return m + 1


def mark_step_success(
    run: PipelineRun,
    idx: int,
    duration_ms: int,
    n_in: int,
    n_out: int,
    payload_ref: str | None = None,
    attempt_no: int | None = None,
) -> PipelineStepResult:
    with Session(engine) as session:
        db_run = session.get(PipelineRun, run.id)
        assert db_run is not None, f"run {run.id} not found"

        if attempt_no is None:
            from_json = (db_run.steps_json[idx] or {}).get("attempt_no", 0) if db_run.steps_json else 0
            from_db = _max_attempt_in_db(session, run.id, idx)
            attempt_no = max(from_json, from_db, 1)

        _upsert_step_info_to_run_json(
            db_run,
            idx,
            status="success",
            attempt_no=attempt_no,
            finished_at=datetime.utcnow().isoformat(),
            duration_ms=duration_ms,
            n_in=n_in,
            n_out=n_out,
            payload_ref=payload_ref,
            error_msg=None,
        )
        db_run.current_step_index = idx + 1

        step_name = PIPELINE_STEPS[idx]["step_name"]
        result = PipelineStepResult(
            run_id=db_run.id,
            step_index=idx,
            step_name=step_name,
            attempt_no=attempt_no,
            status="success",
            duration_ms=duration_ms,
            n_inputs=n_in,
            n_outputs=n_out,
            payload_ref=payload_ref,
            error_msg=None,
            retryable=False,
        )
        session.add(result)
        session.add(db_run)
        session.commit()
        session.refresh(result)
        session.refresh(db_run)
        run.steps_json = [dict(x) for x in db_run.steps_json]
        run.current_step_index = db_run.current_step_index
        run.status = db_run.status
        return result


def mark_step_failed(
    run: PipelineRun,
    idx: int,
    attempt_no: int,
    duration_ms: int,
    error_msg: str,
    retryable: bool = True,
) -> PipelineStepResult:
    with Session(engine) as session:
        db_run = session.get(PipelineRun, run.id)
        assert db_run is not None, f"run {run.id} not found"

        n_in_saved = (db_run.steps_json[idx] or {}).get("n_in", 0) if db_run.steps_json else 0

        _upsert_step_info_to_run_json(
            db_run,
            idx,
            status="failed",
            attempt_no=attempt_no,
            finished_at=datetime.utcnow().isoformat(),
            duration_ms=duration_ms,
            error_msg=error_msg,
        )

        step_name = PIPELINE_STEPS[idx]["step_name"]
        result = PipelineStepResult(
            run_id=db_run.id,
            step_index=idx,
            step_name=step_name,
            attempt_no=attempt_no,
            status="failed",
            duration_ms=duration_ms,
            n_inputs=n_in_saved,
            n_outputs=0,
            payload_ref=None,
            error_msg=error_msg,
            retryable=retryable,
        )
        session.add(result)
        session.add(db_run)
        session.commit()
        session.refresh(result)
        session.refresh(db_run)
        run.steps_json = [dict(x) for x in db_run.steps_json]
        run.status = db_run.status
        return result


def mark_run_success(run: PipelineRun) -> None:
    with Session(engine) as session:
        db_run = session.get(PipelineRun, run.id)
        assert db_run is not None
        db_run.status = "success"
        db_run.finished_at = datetime.utcnow()
        db_run.updated_at = datetime.utcnow()
        session.add(db_run)
        session.commit()
        session.refresh(db_run)
        run.status = db_run.status
        run.finished_at = db_run.finished_at


def mark_run_failed(
    run: PipelineRun,
    at_step_index: int,
    error_msg: str,
    retryable: bool = True,
) -> None:
    with Session(engine) as session:
        db_run = session.get(PipelineRun, run.id)
        assert db_run is not None
        db_run.status = "failed"
        db_run.error_msg = error_msg
        db_run.current_step_index = at_step_index
        db_run.finished_at = datetime.utcnow()
        db_run.updated_at = datetime.utcnow()
        session.add(db_run)
        session.commit()
        session.refresh(db_run)
        run.status = db_run.status
        run.error_msg = db_run.error_msg
        run.finished_at = db_run.finished_at
        run.current_step_index = db_run.current_step_index


def get_first_non_success_index(run: PipelineRun) -> int:
    if not run.steps_json or len(run.steps_json) != 8:
        return 0
    for i, step in enumerate(run.steps_json):
        if (step or {}).get("status") != "success":
            return i
    return 8


def _get_step_n_out(run: PipelineRun, idx: int) -> int:
    if idx < 0 or not run.steps_json or len(run.steps_json) <= idx:
        return run.max_records
    return int((run.steps_json[idx] or {}).get("n_out", 0) or 0)


def _clone_run(run: PipelineRun) -> PipelineRun:
    return PipelineRun(
        id=run.id,
        workspace_id=run.workspace_id,
        preset=run.preset,
        mode=run.mode,
        max_records=run.max_records,
        status=run.status,
        current_step_index=run.current_step_index,
        cancel_flag=run.cancel_flag,
        steps_json=[dict(x) for x in (run.steps_json or [])],
        error_msg=run.error_msg,
        report_blob_path=run.report_blob_path,
        pico_csv_blob_path=run.pico_csv_blob_path,
        created_at=run.created_at,
        updated_at=run.updated_at,
        finished_at=run.finished_at,
    )


def _exec_step_N(
    idx: int,
    run: PipelineRun,
    ctx: dict[str, Any] | None,
) -> tuple[int, int, str | None]:
    ctx = ctx or {}
    fail_key = f"fail_forever_step{idx}"
    fail_once_key = f"fail_once_step{idx}"
    fail_mode_key = f"fail_mode_step{idx}"
    counter_key = f"_cnt_step{idx}"

    if fail_key in ctx:
        mode = ctx.get(fail_mode_key, "timeout")
        if mode == "assertion":
            raise AssertionError(f"forced assertion failure step{idx}")
        elif mode == "value":
            raise ValueError(f"forced value error step{idx}")
        elif mode == "integrity":
            raise IntegrityError(f"forced integrity step{idx}", None, None)
        raise TimeoutError(f"forced timeout step{idx}")

    if fail_once_key in ctx:
        cnt = ctx.get(counter_key, 0) + 1
        ctx[counter_key] = cnt
        if cnt <= 1:
            raise TimeoutError(f"fail-once flaky step{idx}")

    factors = [0.96, 0.86, 0.58, 0.56, 0.76, 0.98, 1.0, 1.0]
    if idx == 0:
        n_in = run.max_records
    else:
        n_in = _get_step_n_out(run, idx - 1) or run.max_records
    if idx == 7:
        n_out = 1
    else:
        n_out = max(1, int(n_in * factors[idx]))
    if idx == 0:
        payload_ref = ctx.get("pubmed_out", "storage/fake")
    elif idx == 7:
        payload_ref = f"storage/{run.id}/report.pdf"
    else:
        payload_ref = None
    return n_in, n_out, payload_ref


RETRYABLE_EXCEPTIONS = (TimeoutError, ConnectionError)


class TooManyRequests(Exception):
    pass


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, RETRYABLE_EXCEPTIONS):
        return True
    if isinstance(exc, TooManyRequests):
        return True
    msg = str(exc).lower()
    if "429" in msg or "too many requests" in msg:
        return True
    if isinstance(exc, (AssertionError, ValueError, IntegrityError)):
        return False
    return False


async def run_single_step(
    run_id: str,
    step_index: int,
    attempt_no: int | None = None,
    ctx: dict[str, Any] | None = None,
) -> tuple[bool, bool]:
    ctx = ctx or {}
    assert 0 <= step_index < 8

    if attempt_no is None:
        attempt_no = _next_attempt_no(run_id, step_index)

    with Session(engine) as session:
        run = session.get(PipelineRun, run_id)
        assert run is not None, f"run {run_id} not found"
        _upsert_step_info_to_run_json(
            run,
            step_index,
            status="running",
            attempt_no=attempt_no,
            started_at=datetime.utcnow().isoformat(),
        )
        run.status = "running"
        session.add(run)
        session.commit()
        session.refresh(run)
        run_copy = _clone_run(run)

    t0 = time.perf_counter_ns()
    try:
        if step_index == 1:
            await _exec_step1_real_dedup(run_copy, ctx)
        else:
            n_in, n_out, payload_ref = _exec_step_N(step_index, run_copy, ctx)
            duration_ms = int((time.perf_counter_ns() - t0) / 1_000_000)
            mark_step_success(run_copy, step_index, duration_ms, n_in, n_out, payload_ref, attempt_no)
        return True, False
    except Exception as exc:
        duration_ms = int((time.perf_counter_ns() - t0) / 1_000_000)
        retryable = _is_retryable(exc)
        error_msg = f"{type(exc).__name__}: {exc}"
        mark_step_failed(run_copy, step_index, attempt_no, duration_ms, error_msg, retryable)
        return False, retryable


def _refresh_run(run_id: str) -> PipelineRun:
    with Session(engine) as session:
        r = session.get(PipelineRun, run_id)
        assert r is not None
        return _clone_run(r)


def _step_is_success(run_id: str, idx: int) -> bool:
    r = _refresh_run(run_id)
    if not r.steps_json or len(r.steps_json) <= idx:
        return False
    return (r.steps_json[idx] or {}).get("status") == "success"


def _run_is_canceled(run_id: str) -> bool:
    r = _refresh_run(run_id)
    return bool(r.cancel_flag)


async def run_pipeline(
    run_id: str,
    ctx: dict[str, Any] | None = None,
) -> None:
    ctx = ctx or {}

    with Session(engine) as session:
        run = session.get(PipelineRun, run_id)
        assert run is not None
        if run.cancel_flag:
            return
        run.status = "running"
        run.updated_at = datetime.utcnow()
        session.add(run)
        session.commit()

    start_run = _refresh_run(run_id)
    start_idx = get_first_non_success_index(start_run)

    for idx in range(start_idx, 8):
        if _run_is_canceled(run_id):
            break

        if _step_is_success(run_id, idx):
            continue

        ok = False
        last_retryable = False
        last_error = "unknown"
        retries_done = 0

        while True:
            if _run_is_canceled(run_id):
                break
            if _step_is_success(run_id, idx):
                ok = True
                break

            ok, retryable = await run_single_step(run_id, idx, None, ctx)
            last_retryable = retryable
            if ok:
                break

            cur_run = _refresh_run(run_id)
            cur_step = cur_run.steps_json[idx] if cur_run.steps_json and len(cur_run.steps_json) > idx else {}
            last_error = cur_step.get("error_msg") or last_error
            used_attempts = cur_step.get("attempt_no", 1) or 1
            auto_attempts_total = MAX_AUTO_RETRIES + 1
            if used_attempts >= auto_attempts_total:
                break
            if retryable:
                backoff_i = min(retries_done, len(RETRY_BACKOFFS_SEC) - 1)
                await asyncio.sleep(RETRY_BACKOFFS_SEC[backoff_i])
                retries_done += 1

        if _run_is_canceled(run_id):
            break

        if not ok:
            ref_run = _refresh_run(run_id)
            mark_run_failed(ref_run, idx, last_error, last_retryable)
            return

    if _run_is_canceled(run_id):
        return

    final_run = _refresh_run(run_id)
    all_ok = True
    for i in range(8):
        if not final_run.steps_json or len(final_run.steps_json) <= i:
            all_ok = False
            break
        if final_run.steps_json[i].get("status") != "success":
            all_ok = False
            break
    if all_ok:
        mark_run_success(final_run)


async def resume_pipeline(
    run_id: str,
    from_step: int | None = None,
    ctx: dict[str, Any] | None = None,
) -> None:
    ctx = ctx or {}
    force = bool(ctx.get("force", False))

    with Session(engine) as session:
        run = session.get(PipelineRun, run_id)
        assert run is not None

        if not run.steps_json or len(run.steps_json) != 8:
            run.steps_json = _default_steps_json()

        new_steps = [dict(s) for s in run.steps_json]

        if from_step is not None:
            start_i = from_step
            if force:
                for i in range(start_i, 8):
                    step = new_steps[i]
                    step["status"] = "queued"
                    step["attempt_no"] = 0
                    step["started_at"] = None
                    step["finished_at"] = None
                    step["duration_ms"] = 0
                    step["n_in"] = 0
                    step["n_out"] = 0
                    step["payload_ref"] = None
                    step["error_msg"] = None
            else:
                for i in range(start_i, 8):
                    step = new_steps[i]
                    if step.get("status") == "success":
                        continue
                    step["status"] = "queued"
            run.status = "resumable"
        else:
            for i in range(8):
                step = new_steps[i]
                if step.get("status") == "success":
                    continue
                step["status"] = "queued"
            run.status = "queued"

        run.steps_json = new_steps
        run.updated_at = datetime.utcnow()
        run.error_msg = None
        run.finished_at = None
        session.add(run)
        session.commit()

    await run_pipeline(run_id, ctx)


# ---- APPEND: W10 Pipeline Compare Delta Helpers (D2-2) ----
from typing import Literal as _Literal
_FUNNEL_STEP_LABELS = ["identify","dedup","ta_pass","ft_include","abstractor_include","rob2_assessed","grade_outcomes","report_generated"]

def compute_funnel_counts_for_run(run: PipelineRun) -> list[int]:
    """Extract 8 ints from run.steps_json n_out values (matches labels order len 8, pad with 0 if step pending)."""
    out = [0] * 8
    for i in range(min(8, len(run.steps_json))):
        step = run.steps_json[i] if isinstance(run.steps_json, list) else {}
        out[i] = int(step.get("n_out", 0) or 0)
    return out

def compute_funnel_delta(run_a: PipelineRun, run_b: PipelineRun) -> list[dict]:
    a_counts = compute_funnel_counts_for_run(run_a)
    b_counts = compute_funnel_counts_for_run(run_b)
    return [
        {"step": _FUNNEL_STEP_LABELS[i], "a_n": a_counts[i], "b_n": b_counts[i], "diff": a_counts[i] - b_counts[i]}
        for i in range(8)
    ]

def compute_rob2_delta(run_a: PipelineRun, run_b: PipelineRun) -> list[dict]:
    """Return overall low/some/high for each run (synthetic deterministic by preset + step5 n_out)."""
    def _rob_counts(preset: str, n_include: int) -> dict[str, int]:
        import hashlib
        seed = int(hashlib.md5(preset.encode()).hexdigest()[:6], 16)
        low = int(n_include * 0.43) + (seed % 7)
        some = int(n_include * 0.50) + ((seed >> 3) % 5)
        high = max(0, n_include - low - some)
        return {"low": low, "some": some, "high": high}
    a_n = compute_funnel_counts_for_run(run_a)[5]
    b_n = compute_funnel_counts_for_run(run_b)[5]
    a_counts = _rob_counts(run_a.preset, a_n)
    b_counts = _rob_counts(run_b.preset, b_n)
    return [{"overall": o, "a": a_counts[o], "b": b_counts[o]} for o in ("low","some","high")]

def compute_grade_delta(run_a: PipelineRun, run_b: PipelineRun) -> list[dict]:
    """Synthetic 4 outcomes for CKD preset (eGFR drop, HF hospitalization, all-cause death, serious AE). Deterministic hash grades."""
    outcomes_map = {
        "sglt2i_ckd": ["eGFR drop 40%","HF hospitalization","all-cause death","serious AEs"],
        "empagliflozin_hf": ["CV death","HF hospitalization","all-cause death","serious AEs"],
        "glp1_weightloss": ["≥15% weight loss","HbA1c reduction","all-cause death","serious AEs"],
        "liraglutide_nafld": ["NAS remission","fibrosis worsening","all-cause death","serious AEs"],
        "pkd_tolvaptan": ["eGFR slope","TKV increase","all-cause death","serious AEs"],
        "ckd_blood_pressure_control": ["SBP<130 achievement","eGFR drop","CV events","all-cause death"],
    }
    import hashlib
    def _grade(preset_seed: int, outcome_idx: int) -> _Literal["H","M","L"]:
        bucket = (preset_seed + outcome_idx * 17) % 10
        if bucket < 2: return "H"
        if bucket < 8: return "M"
        return "L"
    a_seed = int(hashlib.md5((run_a.preset + str(run_a.id)).encode()).hexdigest()[:6], 16)
    b_seed = int(hashlib.md5((run_b.preset + str(run_b.id)).encode()).hexdigest()[:6], 16)
    outcomes = outcomes_map.get(run_a.preset, outcomes_map["sglt2i_ckd"])
    def _reason(a_g: str, b_g: str, idx: int) -> str:
        if a_g == b_g: return "Same grade; robust"
        if a_g > b_g:
            return f"A lower grade (more downgrades) vs B; outcome#{idx+1}"
        return f"A higher grade (fewer downgrades) vs B; outcome#{idx+1}"
    return [
        {"outcome": outcomes[i], "a": _grade(a_seed, i), "b": _grade(b_seed, i),
         "reason": _reason(_grade(a_seed,i), _grade(b_seed,i), i)}
        for i in range(len(outcomes))
    ]

def compute_pico_diff(run_a: PipelineRun, run_b: PipelineRun) -> dict:
    """Return NCT IDs lists: only_a, only_b, both. Deterministic by preset + n_in."""
    def _nct_set(preset: str, n: int) -> set[str]:
        import hashlib
        seed = int(hashlib.sha1(preset.encode()).hexdigest()[:8], 16)
        return {f"NCT{(seed + i * 131) % 100000000:08d}" for i in range(n)}
    a_set = _nct_set(run_a.preset, compute_funnel_counts_for_run(run_a)[4])
    b_set = _nct_set(run_b.preset, compute_funnel_counts_for_run(run_b)[4])
    only_a = sorted(a_set - b_set)[:100]
    only_b = sorted(b_set - a_set)[:100]
    both = sorted(a_set & b_set)[:100]
    return {"only_in_a_nct_ids": only_a, "only_in_b_nct_ids": only_b, "both": both}

def compute_pipeline_compare(run_a: PipelineRun, run_b: PipelineRun, metrics_requested: str) -> dict:
    """Orchestrator used by route. metrics_requested is CSV: funnel,rob,grade,pico (all 4 default)."""
    requested = {s.strip() for s in metrics_requested.split(",") if s.strip()}
    result: dict = {"run_a_id": run_a.id, "run_b_id": run_b.id, "metrics_requested": sorted(requested)}
    if "funnel" in requested or not requested: result["funnel_delta"] = compute_funnel_delta(run_a, run_b)
    if "rob" in requested or not requested:    result["rob2_delta"] = compute_rob2_delta(run_a, run_b)
    if "grade" in requested or not requested:  result["grade_delta"] = compute_grade_delta(run_a, run_b)
    if "pico" in requested or not requested:   result["pico"] = compute_pico_diff(run_a, run_b)
    return result


async def _exec_step1_real_dedup(run: PipelineRun, ctx: dict[str, Any]) -> None:
    import time as _time
    import asyncio as _asyncio
    from app.models import DedupDiagnostic
    from app.services.simhash import find_duplicates_hybrid, THR as _THR_BITS

    t_start = _time.perf_counter_ns()

    records = ctx["fetched_records"]
    n_in = len(records)

    if ctx.get("cancel_flag"):
        return

    enable_parity_check = n_in <= 200

    kept_ids, diag = await _asyncio.to_thread(
        find_duplicates_hybrid, records, _THR_BITS, 8, enable_parity_check
    )

    if ctx.get("cancel_flag"):
        return

    perf_merged = {**diag.get("perf", {}), **diag.get("perf_json", {})}

    n_out = len(kept_ids)
    kept_id_set = set(kept_ids)
    ctx["kept_records"] = [r for r in records if r["id"] in kept_id_set]

    duration_ms = int((_time.perf_counter_ns() - t_start) / 1_000_000)

    if ctx.get("cancel_flag"):
        return

    with Session(engine) as session:
        existing = session.exec(
            select(DedupDiagnostic).where(
                DedupDiagnostic.run_id == run.id,
                DedupDiagnostic.step_idx == 1,
            )
        ).first()
        if existing is None:
            dd = DedupDiagnostic(
                run_id=run.id,
                step_idx=1,
                sizes_hist=diag["sizes_hist"],
                hamming_hist=diag["hamming_hist"],
                perf_json=perf_merged,
            )
            session.add(dd)
        else:
            existing.sizes_hist = diag["sizes_hist"]
            existing.hamming_hist = diag["hamming_hist"]
            existing.perf_json = perf_merged
            session.add(existing)
        session.commit()

    if ctx.get("cancel_flag"):
        return

    mark_step_success(run, 1, duration_ms, n_in, n_out)
