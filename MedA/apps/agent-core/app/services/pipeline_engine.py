from __future__ import annotations

import asyncio
import os
import re
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


def _apply_fault_injection(idx: int, ctx: dict[str, Any]) -> None:
    """Test-only fault hooks, shared by the simulated steps and the real step1."""
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


# Study designs that title/abstract screening rejects outright: they are secondary
# literature, and the design is always stated in the abstract, so no full text is
# needed to make the call.
_TA_EXCLUDED_DESIGNS: frozenset[str] = frozenset({"review"})

# All six presets ask an intervention-effect question, so full-text screening keeps
# only designs that can answer one. An unknown design is kept rather than dropped:
# absence of design metadata is not evidence of ineligibility.
_FT_ELIGIBLE_DESIGNS: frozenset[str] = frozenset({"RCT", "cohort", "registry"})

# The PICO extractor reports a coarse text-derived study type; map it onto the
# design vocabulary the abstractor and RoB 2 engines speak.
_TEXT_STUDY_TYPE_TO_DESIGN: dict[str, str] = {
    "rct": "RCT",
    "observational": "cohort",
    "review": "review",
}


def _screening_pool(idx: int, run: PipelineRun, ctx: dict[str, Any]) -> list[dict]:
    """Records entering step `idx`, preferring what the previous step actually kept."""
    records = ctx.get("kept_records") or ctx.get("fetched_records")
    if records:
        return records

    # Resuming mid-pipeline: the surviving id set from step1 is gone, so re-fetch the
    # corpus and keep as many records as the previous step reported. The exact set
    # cannot be recovered, but the funnel size can.
    from app.services.sources.pubmed_adapter import _load_preset_snapshot

    records = _load_preset_snapshot(run.preset, run.max_records)
    ctx["fetched_records"] = records
    prev_n_out = _get_step_n_out(run, idx - 1)
    if 0 < prev_n_out < len(records):
        records = records[:prev_n_out]
    return records


def _screen_one(rec: dict, protocol: dict[str, Any]) -> dict[str, Any]:
    """Rule-extract PICO from one record and run the abstractor triage on it."""
    from app.services.abstractor import PICOElement, triage_study
    from app.services.pico import extract_pico_fields

    fields = extract_pico_fields(rec.get("title") or "", rec.get("abstract") or "")
    pico = {
        "population": PICOElement(type=fields["population"], text=fields["population"]),
        "intervention": PICOElement(type=fields["intervention"], text=fields["intervention"]),
        "comparator": PICOElement(type=fields["comparison"], text=fields["comparison"]),
        "outcome": PICOElement(type=fields["outcome"], text=fields["outcome"]),
    }
    design = rec.get("study_design") or _TEXT_STUDY_TYPE_TO_DESIGN.get(
        fields["study_type"] or ""
    )
    study_meta = {"study_design": design, "risk_of_bias_overall": None}
    return {
        "record": rec,
        "pico": fields,
        "study_design": design,
        "triage": triage_study(pico, protocol, study_meta),
    }


def _preset_protocol(preset: str) -> dict[str, Any]:
    from app.services.preset_profiles import PRESET_PROFILES

    profile = PRESET_PROFILES.get(preset)
    return profile.protocol() if profile else {}


def _exec_screen_ta(run: PipelineRun, ctx: dict[str, Any]) -> tuple[int, int, None]:
    """step2 — title/abstract screening: real PICO extraction + abstractor triage.

    `n_out` counts include *and* review: a record the triage cannot resolve from the
    title and abstract alone is exactly what goes on to full-text screening.
    """
    from app.services.abstractor import AbstractorDecision

    pool = _screening_pool(2, run, ctx)
    protocol = _preset_protocol(run.preset)

    kept: list[dict[str, Any]] = []
    for rec in pool:
        screened = _screen_one(rec, protocol)
        if screened["triage"]["decision"] == AbstractorDecision.EXCLUDE:
            continue
        if screened["study_design"] in _TA_EXCLUDED_DESIGNS:
            continue
        kept.append(screened)

    ctx["ta_records"] = kept
    return len(pool), len(kept), None


def _exec_screen_ft(run: PipelineRun, ctx: dict[str, Any]) -> tuple[int, int, None]:
    """step3 — full-text screening: design eligibility + verifiable PICO."""
    screened_in = ctx.get("ta_records")
    if screened_in is None:
        protocol = _preset_protocol(run.preset)
        pool = _screening_pool(3, run, ctx)
        screened_in = [_screen_one(rec, protocol) for rec in pool]

    kept: list[dict[str, Any]] = []
    for screened in screened_in:
        design = screened["study_design"]
        if design is not None and design not in _FT_ELIGIBLE_DESIGNS:
            continue
        pico = screened["pico"]
        # Nothing at all could be pinned down from the retrieved text, so eligibility
        # is unverifiable and the record cannot be carried into extraction.
        if not any(
            pico[k] for k in ("population", "intervention", "comparison", "outcome")
        ):
            continue
        kept.append(screened)

    ctx["ft_records"] = kept
    return len(screened_in), len(kept), None


def _abstract_outcome(rec: dict) -> dict[str, Any] | None:
    """Pull the effect estimate out of one record, or None if it has none.

    Data abstraction is what step4 actually does, and a study whose result cannot be
    abstracted cannot enter RoB 2 or GRADE — there is nothing to rate. Structured
    fields win over the abstract text; the regexes are the fallback for records that
    only carry prose.
    """
    p_value = rec.get("p_value")
    if not isinstance(p_value, (int, float)):
        p_value = None
    sample_size = rec.get("sample_size")
    if not isinstance(sample_size, int):
        sample_size = None

    text = rec.get("abstract") or ""
    if p_value is None:
        m = _RX_P_VALUE.search(text)
        if m:
            # "p<0.001" states an upper bound, not a value; take the bound, which is
            # all the significance test downstream needs.
            p_value = float(m.group("num"))
    if sample_size is None:
        m = _RX_SAMPLE_SIZE.search(text)
        if m:
            sample_size = int(m.group("num"))

    if p_value is None and sample_size is None:
        return None

    hazard_ratio = None
    m = _RX_HAZARD_RATIO.search(text)
    if m:
        hazard_ratio = float(m.group("num"))

    return {"p_value": p_value, "sample_size": sample_size, "hazard_ratio": hazard_ratio}


_RX_P_VALUE = re.compile(r"\bp\s*[=<>]\s*(?P<num>\d*\.?\d+)", re.IGNORECASE)
_RX_SAMPLE_SIZE = re.compile(r"\bn\s*=\s*(?P<num>\d+)", re.IGNORECASE)
_RX_HAZARD_RATIO = re.compile(r"\b(?:HR|RR|OR)\s*[= ]\s*(?P<num>\d*\.?\d+)", re.IGNORECASE)
_RX_DROPOUT = re.compile(r"dropout\s+(?P<num>\d*\.?\d+)\s*%", re.IGNORECASE)


def _exec_abstractor(run: PipelineRun, ctx: dict[str, Any]) -> tuple[int, int, None]:
    """step4 — data abstraction: keep the studies whose results can be abstracted."""
    from app.services.abstractor import AbstractorDecision

    screened_in = ctx.get("ft_records")
    if screened_in is None:
        protocol = _preset_protocol(run.preset)
        screened_in = [_screen_one(rec, protocol) for rec in _screening_pool(4, run, ctx)]

    abstracted: list[dict[str, Any]] = []
    for screened in screened_in:
        if screened["triage"]["decision"] == AbstractorDecision.EXCLUDE:
            continue
        outcome = _abstract_outcome(screened["record"])
        if outcome is None:
            continue
        abstracted.append({**screened, "outcome": outcome})

    ctx["abstracted_records"] = abstracted
    return len(screened_in), len(abstracted), None


def _abstracted_pool(run: PipelineRun, ctx: dict[str, Any]) -> list[dict[str, Any]]:
    """The abstracted studies entering step5, re-deriving them if ctx has none.

    A resume that starts at step5 or later arrives with an empty ctx, so the
    screening and abstraction chain is replayed from the corpus. Step1's reported
    output size is the entry pool, which is what `_screening_pool(2, ...)` uses.
    """
    records = ctx.get("abstracted_records")
    if records is None:
        _exec_screen_ta(run, ctx)
        _exec_screen_ft(run, ctx)
        _exec_abstractor(run, ctx)
        records = ctx["abstracted_records"]
    return records


def _dropout_pct(text: str) -> float | None:
    m = _RX_DROPOUT.search(text)
    return float(m.group("num")) if m else None


def _rob2_domains_for(screened: dict[str, Any]) -> tuple[bool, list[dict[str, str]]]:
    """Derive the five RoB 2 domain ratings for one abstracted study.

    Every signal comes from what the record actually says: the design, whether the
    abstract reports blinding, the reported dropout, and whether an effect estimate
    with a p-value could be abstracted. Nothing is assumed favourably — a signal the
    text does not carry counts as a concern, not as low risk.
    """
    from app.services.rob2_engine import TL, domain_d1_rating, r

    rec = screened["record"]
    text = f"{rec.get('title') or ''} {rec.get('abstract') or ''}".lower()
    randomized = screened["study_design"] == "RCT"
    open_label = not randomized or "double-blind" not in text
    # The abstracted endpoints are event counts and lab values, which are measured
    # the same way regardless of who knows the allocation.
    signals = {
        "open_label": open_label,
        "outcome_type": "objective",
        "blinded_outcome": not open_label,
    }
    domains = [r(1, domain_d1_rating(signals))]
    # D2 deviations from the intended intervention: unblinded care can diverge.
    domains.append(r(2, TL.SOME if open_label else TL.LOW))
    # D3 missing outcome data.
    dropout = _dropout_pct(text)
    if dropout is None:
        d3 = TL.SOME
    elif dropout >= 15.0:
        d3 = TL.HIGH
    elif dropout >= 5.0:
        d3 = TL.SOME
    else:
        d3 = TL.LOW
    domains.append(r(3, d3))
    # D4 outcome measurement.
    domains.append(r(4, TL.LOW if not open_label else TL.SOME))
    # D5 selection of the reported result: with no p-value there is nothing to check
    # the pre-specified analysis against.
    outcome = screened.get("outcome") or {}
    domains.append(r(5, TL.LOW if outcome.get("p_value") is not None else TL.SOME))
    return randomized, domains


# `compute_rob2_delta` reports three buckets. A `critical` ROBINS-I verdict is at
# least high risk, so it is counted as high rather than silently dropped.
_ROB2_BUCKETS: tuple[str, ...] = ("low", "some", "high")
_ROB2_RATING_TO_BUCKET: dict[str, str] = {
    "low": "low",
    "some_concerns": "some",
    "high": "high",
    "critical": "high",
}


def _exec_rob2_assessment(run: PipelineRun, ctx: dict[str, Any]) -> tuple[int, int, str]:
    """step5 — risk of bias: RoB 2 for randomized trials, ROBINS-I for the rest.

    Assessing a study never removes it from the review, so `n_out == n_in`. The
    bucket counts ride along in `payload_ref` so the compare view can read the real
    distribution back without a second pass over the corpus.
    """
    from app.services.rob2_engine import calc_rob2_overall, calc_robinsi_overall

    pool = _abstracted_pool(run, ctx)

    assessed: list[dict[str, Any]] = []
    counts = {bucket: 0 for bucket in _ROB2_BUCKETS}
    for screened in pool:
        randomized, domains = _rob2_domains_for(screened)
        rating = (
            calc_rob2_overall(domains) if randomized else calc_robinsi_overall(domains)
        )
        bucket = _ROB2_RATING_TO_BUCKET[rating]
        counts[bucket] += 1
        assessed.append({
            **screened,
            "rob2": {
                "tool": "rob2" if randomized else "robins_i",
                "domains": domains,
                "rating": rating,
                "overall": bucket,
            },
        })

    ctx["rob2_records"] = assessed
    payload_ref = "rob2:" + ",".join(f"{b}={counts[b]}" for b in _ROB2_BUCKETS)
    return len(pool), len(assessed), payload_ref


def parse_rob2_payload_ref(payload_ref: str | None) -> dict[str, int] | None:
    """Read back the bucket counts step5 recorded, or None if it recorded none."""
    if not payload_ref or not payload_ref.startswith("rob2:"):
        return None
    counts: dict[str, int] = {}
    for part in payload_ref[len("rob2:"):].split(","):
        bucket, _, raw = part.partition("=")
        if bucket in _ROB2_BUCKETS and raw.isdigit():
            counts[bucket] = int(raw)
    if len(counts) != len(_ROB2_BUCKETS):
        return None
    return counts


_GRADE_CERTAINTY_TO_LETTER: dict[str, str] = {
    "High": "H",
    "Moderate": "M",
    "Low": "L",
    # GRADE has four levels and the compare view has three; "very low" certainty is
    # reported as low rather than invented as a fourth letter.
    "VeryLow": "L",
}


def _grade_domains_for_outcome(
    outcome_label: str,
    assessed: list[dict[str, Any]],
) -> tuple[Any, Any]:
    """Rate the five GRADE domains and three upgrade criteria for one outcome."""
    import statistics

    from app.services.grade_engine import Grade3Upgrades, Grade5Domains
    from app.services.rob2_engine import grade_ro_downgrade

    n = len(assessed)
    ratings = [s["rob2"]["rating"] for s in assessed]
    risk_of_bias = {0: "no_concerns", -1: "some_concerns", -2: "major_concerns"}[
        grade_ro_downgrade(ratings)
    ]

    # Indirectness: does the body of evidence report *this* outcome at all?
    needle = outcome_label.lower()
    reporting = sum(
        1
        for s in assessed
        if needle in (s["record"].get("abstract") or "").lower()
    )
    reporting_pct = reporting / n if n else 0.0
    if reporting_pct >= 0.5:
        indirectness = "no_concerns"
    elif reporting_pct > 0.0:
        indirectness = "some_concerns"
    else:
        indirectness = "major_concerns"

    # Inconsistency: how far apart the reported effect estimates are.
    hrs = [
        s["outcome"]["hazard_ratio"]
        for s in assessed
        if s.get("outcome", {}).get("hazard_ratio")
    ]
    if len(hrs) < 2:
        inconsistency = "some_concerns"
    else:
        mean_hr = statistics.fmean(hrs)
        cv = statistics.pstdev(hrs) / mean_hr if mean_hr else 0.0
        if cv >= 0.5:
            inconsistency = "major_concerns"
        elif cv >= 0.3:
            inconsistency = "some_concerns"
        else:
            inconsistency = "no_concerns"

    # Imprecision: the usual sample-size thresholds for an optimally powered body
    # of evidence.
    total_n = sum(s["outcome"].get("sample_size") or 0 for s in assessed)
    if total_n < 400:
        imprecision = "major_concerns"
    elif total_n < 2000:
        imprecision = "some_concerns"
    else:
        imprecision = "no_concerns"

    # Publication bias: below ten studies a funnel plot cannot be interpreted, so
    # the domain is undetectable rather than clean.
    publication_bias = "no_concerns" if n >= 10 else "some_concerns"

    domains = Grade5Domains(
        risk_of_bias=risk_of_bias,
        indirectness=indirectness,
        inconsistency=inconsistency,
        imprecision=imprecision,
        publication_bias=publication_bias,
    )
    upgrades = Grade3Upgrades(
        # A large effect only earns an upgrade at the conventional RR<0.5 / >2.0.
        large_effect=bool(hrs) and not 0.5 < statistics.median(hrs) < 2.0,
        # Neither a dose-response gradient nor residual confounding that would bias
        # towards the null is recoverable from the retrieved text.
        dose_response=False,
        confounders_reduce=False,
    )
    return domains, upgrades


def _exec_grade_downgrade(run: PipelineRun, ctx: dict[str, Any]) -> tuple[int, int, str]:
    """step6 — GRADE certainty, rated once per outcome of the review question.

    The funnel turns from studies into outcomes here, so `n_out` is the number of
    outcomes rated. The letters ride along in `payload_ref` for the compare view.
    """
    from app.services.grade_engine import compute_certainty_final
    from app.services.preset_profiles import get_profile

    assessed = ctx.get("rob2_records")
    if assessed is None:
        _exec_rob2_assessment(run, ctx)
        assessed = ctx["rob2_records"]

    labels = get_profile(run.preset).outcome_labels
    outcomes: list[dict[str, Any]] = []
    for label in labels:
        domains, upgrades = _grade_domains_for_outcome(label, assessed)
        certainty = compute_certainty_final(domains, upgrades, start="High")
        outcomes.append({
            "outcome": label,
            "certainty": certainty,
            "letter": _GRADE_CERTAINTY_TO_LETTER[certainty],
            "domains": dict(domains.items()),
            "n_studies": len(assessed),
        })

    ctx["grade_outcomes"] = outcomes
    payload_ref = "grade:" + ",".join(o["letter"] for o in outcomes)
    return len(assessed), len(outcomes), payload_ref


def parse_grade_payload_ref(payload_ref: str | None) -> list[str] | None:
    """Read back the per-outcome certainty letters step6 recorded."""
    if not payload_ref or not payload_ref.startswith("grade:"):
        return None
    letters = [p for p in payload_ref[len("grade:"):].split(",") if p]
    if not letters or any(x not in ("H", "M", "L") for x in letters):
        return None
    return letters


REPORT_ARTIFACT_FORMATS: tuple[tuple[str, int], ...] = (
    ("report.md", 0),
    ("report.html", 1),
    ("report.txt", 2),
)


def _grade_rows_for_report(
    outcomes: list[dict[str, Any]],
    assessed: list[dict[str, Any]],
) -> list[Any]:
    """Turn the GRADE results into the summary-of-findings rows the renderer takes."""
    import statistics

    from app.services.report_engine import GradeAssRow

    participants = sum(s["outcome"].get("sample_size") or 0 for s in assessed)
    hrs = [
        s["outcome"]["hazard_ratio"]
        for s in assessed
        if s.get("outcome", {}).get("hazard_ratio")
    ]
    # The abstracted effect estimates are not split per outcome, so the pooled
    # median is reported as-is rather than attributed to one outcome in particular.
    effect_label = (
        f"HR {statistics.median(hrs):.2f} (median of {len(hrs)} studies)"
        if hrs
        else "not estimable"
    )

    rows: list[Any] = []
    for o in outcomes:
        downgraded = [d for d, v in o["domains"].items() if v != "no_concerns"]
        rows.append(
            GradeAssRow(
                outcome_label=o["outcome"],
                certainty=o["certainty"],
                participants_n=participants,
                studies_k=o["n_studies"],
                effect_label=effect_label,
                ar_control="not reported",
                ar_intervention="not reported",
                comments=(
                    "downgraded for " + ", ".join(downgraded) if downgraded else "no downgrades"
                ),
            )
        )
    return rows


def _exec_report_generate(run: PipelineRun, ctx: dict[str, Any]) -> tuple[int, int, str]:
    """step7 — render the report from the real GRADE results and write it to storage.

    One report is produced per run, so `n_out` is 1. `report_engine` renders
    Markdown, HTML and plain text; there is no PDF renderer in this service, so the
    three real formats are what gets written and `payload_ref` points at the
    Markdown, which is the canonical one.
    """
    from app.services.preset_profiles import get_profile
    from app.services.report_engine import ProjectReportInput, generate_report_three_formats
    from app.storage import write_run_artifact

    outcomes = ctx.get("grade_outcomes")
    if outcomes is None:
        _exec_grade_downgrade(run, ctx)
        outcomes = ctx["grade_outcomes"]
    assessed = ctx["rob2_records"]

    profile = get_profile(run.preset)
    rob2_buckets: dict[str, int] = {b: 0 for b in _ROB2_BUCKETS}
    for s in assessed:
        rob2_buckets[s["rob2"]["overall"]] += 1

    pi = ProjectReportInput(
        project_name=f"{profile.condition} — {profile.intervention_text} vs {profile.comparator_text}",
        # The report renderer is shared with the project-scoped reports, which key
        # off an integer project id. A pipeline run has no project, so this stays 0.
        project_id=0,
        owner_display=run.workspace_id,
        abstract_summary=(
            f"{len(assessed)} studies were included after screening and data "
            f"abstraction of {run.max_records} retrieved records. Risk of bias: "
            f"{rob2_buckets['low']} low, {rob2_buckets['some']} some concerns, "
            f"{rob2_buckets['high']} high."
        ),
        # PRISMA items are checked off by a reviewer, which no pipeline run does.
        prisma_checklist_masked_count=0,
        prisma_checklist_total_items=27,
        grade_rows=_grade_rows_for_report(outcomes, assessed),
    )
    rendered = generate_report_three_formats(pi)

    paths = [
        write_run_artifact(run.id, filename, rendered[i])
        for filename, i in REPORT_ARTIFACT_FORMATS
    ]
    ctx["report_paths"] = paths

    with Session(engine) as session:
        db_run = session.get(PipelineRun, run.id)
        if db_run is not None:
            db_run.report_blob_path = paths[0]
            session.add(db_run)
            session.commit()
    run.report_blob_path = paths[0]

    return len(outcomes), 1, paths[0]


def _exec_step_N(
    idx: int,
    run: PipelineRun,
    ctx: dict[str, Any] | None,
) -> tuple[int, int, str | None]:
    if ctx is None:
        ctx = {}
    _apply_fault_injection(idx, ctx)

    if idx == 0:
        # Real fetch: load the preset corpus and hand it to step1 through ctx.
        from app.services.sources.pubmed_adapter import _load_preset_snapshot

        records = ctx.get("fetched_records")
        if not records:
            records = _load_preset_snapshot(run.preset, run.max_records)
            ctx["fetched_records"] = records
        n_in = run.max_records
        n_out = len(records)
        return n_in, n_out, ctx.get("pubmed_out", f"snapshot:{run.preset}")

    if idx == 2:
        return _exec_screen_ta(run, ctx)

    if idx == 3:
        return _exec_screen_ft(run, ctx)

    if idx == 4:
        return _exec_abstractor(run, ctx)

    if idx == 5:
        return _exec_rob2_assessment(run, ctx)

    if idx == 6:
        return _exec_grade_downgrade(run, ctx)

    if idx == 7:
        return _exec_report_generate(run, ctx)

    # step1 (dedup) is async and runs through `_exec_step1_real_dedup`, so it never
    # reaches here; every other index is dispatched above.
    raise AssertionError(f"no executor for pipeline step {idx}")


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
    # An empty dict is still the caller's dict: `ctx or {}` would replace it with a
    # fresh one and break the hand-off of fetched/screened records between steps.
    if ctx is None:
        ctx = {}
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
    if ctx is None:
        ctx = {}

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

def _step_payload_ref(run: PipelineRun, idx: int) -> str | None:
    """The payload_ref step `idx` recorded, or None if it never ran."""
    steps = run.steps_json if isinstance(run.steps_json, list) else []
    if len(steps) <= idx:
        return None
    return (steps[idx] or {}).get("payload_ref")


def _replayed_assessment(run: PipelineRun) -> list[dict]:
    """Re-run screening, abstraction and RoB 2 for a run that recorded no summary.

    Compare only receives a `PipelineRun` row, and the per-study results live in the
    run context, not in the database. A run whose step5/step6 summary is missing (an
    older run, or one that never reached those steps) is therefore replayed from its
    preset corpus, which is deterministic. Nothing here is invented; it is the same
    code the pipeline itself executes.
    """
    ctx: dict[str, Any] = {}
    _exec_rob2_assessment(run, ctx)
    return ctx["rob2_records"]


def compute_rob2_delta(run_a: PipelineRun, run_b: PipelineRun) -> list[dict]:
    """Compare the real RoB 2 / ROBINS-I overall judgements of the two runs."""
    def _counts(run: PipelineRun) -> dict[str, int]:
        recorded = parse_rob2_payload_ref(_step_payload_ref(run, 5))
        if recorded is not None:
            return recorded
        counts = {bucket: 0 for bucket in _ROB2_BUCKETS}
        for study in _replayed_assessment(run):
            counts[study["rob2"]["overall"]] += 1
        return counts

    a_counts = _counts(run_a)
    b_counts = _counts(run_b)
    return [{"overall": o, "a": a_counts[o], "b": b_counts[o]} for o in _ROB2_BUCKETS]


_GRADE_LETTER_TO_CERTAINTY: dict[str, str] = {
    "H": "high",
    "M": "moderate",
    "L": "low",
}


def compute_grade_delta(run_a: PipelineRun, run_b: PipelineRun) -> list[dict]:
    """Compare the real GRADE certainty of each outcome of the review question."""
    from app.services.preset_profiles import get_profile

    def _letters(run: PipelineRun) -> list[str]:
        recorded = parse_grade_payload_ref(_step_payload_ref(run, 6))
        if recorded is not None:
            return recorded
        ctx: dict[str, Any] = {}
        _exec_grade_downgrade(run, ctx)
        return [o["letter"] for o in ctx["grade_outcomes"]]

    # The outcomes are the ones the review question asks about, so they are named
    # after run A's preset; a cross-preset comparison lines its certainty up
    # positionally, which is how the two presets' outcome lists are ordered.
    outcomes = get_profile(run_a.preset).outcome_labels
    a_letters = _letters(run_a)
    b_letters = _letters(run_b)

    def _reason(a_g: str, b_g: str) -> str:
        a_word = _GRADE_LETTER_TO_CERTAINTY[a_g]
        b_word = _GRADE_LETTER_TO_CERTAINTY[b_g]
        if a_g == b_g:
            return f"Both runs rated {a_word} certainty"
        # The letters are ordered H > M > L as certainty, which is the reverse of
        # their alphabetical order.
        order = ("H", "M", "L")
        if order.index(a_g) < order.index(b_g):
            return f"A rated {a_word} vs B {b_word}: fewer downgrades in A"
        return f"A rated {a_word} vs B {b_word}: more downgrades in A"

    rows: list[dict] = []
    for i, label in enumerate(outcomes):
        if i >= len(a_letters) or i >= len(b_letters):
            break
        a_g, b_g = a_letters[i], b_letters[i]
        rows.append({"outcome": label, "a": a_g, "b": b_g, "reason": _reason(a_g, b_g)})
    return rows


# The compare payload is served over HTTP, so the id lists are capped rather than
# returning one entry per included study of a large review.
_PICO_DIFF_CAP = 100


def included_study_ids(run: PipelineRun) -> list[str]:
    """Registration ids of the studies that survived screening and abstraction."""
    ids: list[str] = []
    for study in _abstracted_pool(run, {}):
        nct_id = study["record"].get("nct_id")
        if nct_id:
            ids.append(nct_id)
    return ids


def compute_pico_diff(run_a: PipelineRun, run_b: PipelineRun) -> dict:
    """Which included studies the two runs share, by trial registration id."""
    a_set = set(included_study_ids(run_a))
    b_set = set(included_study_ids(run_b))
    return {
        "only_in_a_nct_ids": sorted(a_set - b_set)[:_PICO_DIFF_CAP],
        "only_in_b_nct_ids": sorted(b_set - a_set)[:_PICO_DIFF_CAP],
        "both": sorted(a_set & b_set)[:_PICO_DIFF_CAP],
    }

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

    _apply_fault_injection(1, ctx)

    records = ctx.get("fetched_records")
    if not records:
        # Resuming directly at step1 (or ctx not carried over): re-fetch the corpus.
        from app.services.sources.pubmed_adapter import _load_preset_snapshot

        records = _load_preset_snapshot(run.preset, run.max_records)
        ctx["fetched_records"] = records
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
