from __future__ import annotations

import math
from typing import Any
from xml.sax.saxutils import escape as xml_escape

from sqlmodel import Session, select, delete

from app.models import OutcomeArmData, OutcomeDefinition, AnalysisRun
from app.services.stats_evidence import (
    binary_rr_95ci,
    compute_heterogeneity,
    dl_random_pooled,
    fixed_iv_pooled,
    fixed_mh_pooled_rr,
)


_META_MIN_STUDIES_MSG = "meta_requires_at_least_2_studies"
_EX3_BINARY_MISMATCH = "outcome_type_mismatch_expected_binary_arms"
_EX4_CONTINUOUS_MISMATCH = "outcome_type_mismatch_expected_continuous"
_EX6_EVENTS_GT_TOTAL = "2x2_events_gt_total_n_invalid"
_EX7_SD_OR_N_INVALID = "continuous_sd_or_n_invalid_nonpositive"
_EX8_ZERO_WEIGHT = "zero_total_weight_cannot_compute_pooled"


def define_outcome(
    db: Session,
    project_id: int,
    name: str,
    outcome_type: str,
    measure: str,
    time_point: str | None = None,
) -> OutcomeDefinition:
    outcome_key = name.lower().replace(" ", "_")
    existing = db.exec(
        select(OutcomeDefinition).where(
            OutcomeDefinition.project_id == project_id,
            OutcomeDefinition.outcome_key == outcome_key,
        )
    ).first()
    if existing is not None:
        existing.label = name
        existing.measure_type = f"{outcome_type}|{measure}"
        if time_point is not None:
            existing.description = time_point
        db.add(existing)
        db.commit()
        db.refresh(existing)
        return existing

    od = OutcomeDefinition(
        project_id=project_id,
        outcome_key=outcome_key,
        label=name,
        description=time_point,
        measure_type=f"{outcome_type}|{measure}",
    )
    db.add(od)
    db.commit()
    db.refresh(od)
    return od


def list_outcomes(db: Session, project_id: int) -> list[dict[str, Any]]:
    stmt = select(OutcomeDefinition).where(OutcomeDefinition.project_id == project_id)
    rows = db.exec(stmt).all()
    items: list[dict[str, Any]] = []
    for r in rows:
        mt = r.measure_type or "binary|RR"
        parts = mt.split("|", 1)
        items.append({
            "id": r.id,
            "name": r.label,
            "outcome_type": parts[0] if len(parts) >= 1 else "binary",
            "measure": parts[1] if len(parts) >= 2 else "RR",
            "time_point": r.description,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return items


def rename_outcome(db: Session, project_id: int, outcome_id: int, new_name: str) -> OutcomeDefinition:
    od = db.get(OutcomeDefinition, outcome_id)
    od.label = new_name
    od.outcome_key = new_name.lower().replace(" ", "_")
    db.add(od)
    db.commit()
    db.refresh(od)
    return od


def delete_outcome(db: Session, project_id: int, outcome_id: int) -> None:
    db.exec(delete(OutcomeArmData).where(
        OutcomeArmData.project_id == project_id,
        OutcomeArmData.outcome_id == outcome_id,
    ))
    db.exec(delete(AnalysisRun).where(
        AnalysisRun.project_id == project_id,
        AnalysisRun.outcome_id == outcome_id,
    ))
    od = db.get(OutcomeDefinition, outcome_id)
    if od is not None:
        db.delete(od)
    db.commit()


def _outcome_is_binary(od: OutcomeDefinition | None) -> bool:
    if od is None:
        return True
    return (od.measure_type or "").startswith("binary|")


def _outcome_is_continuous(od: OutcomeDefinition | None) -> bool:
    return not _outcome_is_binary(od)


def upsert_outcome_arm_data(
    db: Session,
    project_id: int,
    outcome_id: int,
    record_id: int,
    arm_label: str,
    reviewer_id: str,
    binary_data: dict | None = None,
    continuous_data: dict | None = None,
) -> OutcomeArmData:
    outcome = db.get(OutcomeDefinition, outcome_id)

    if _outcome_is_binary(outcome):
        if binary_data is None and continuous_data is not None:
            raise Exception(_EX3_BINARY_MISMATCH)
        if binary_data is not None:
            ev = int(binary_data.get("events", 0))
            nn = int(binary_data.get("n", 0))
            if ev < 0 or nn < 0:
                pass
            if ev > nn:
                raise Exception(_EX6_EVENTS_GT_TOTAL)
            data_json = {"events": ev, "n": nn}
        else:
            data_json = {}
    else:
        if continuous_data is None and binary_data is not None:
            raise Exception(_EX4_CONTINUOUS_MISMATCH)
        if continuous_data is not None:
            mean_v = float(continuous_data.get("mean_val", 0.0))
            sd_v = float(continuous_data.get("sd_val", 0.0))
            nn = int(continuous_data.get("n", 0))
            if sd_v <= 0.0 or nn <= 0:
                raise Exception(_EX7_SD_OR_N_INVALID)
            data_json = {"mean_val": mean_v, "sd_val": sd_v, "n": nn}
        else:
            data_json = {}

    existing = db.exec(
        select(OutcomeArmData).where(
            OutcomeArmData.project_id == project_id,
            OutcomeArmData.outcome_id == outcome_id,
            OutcomeArmData.record_id == record_id,
            OutcomeArmData.arm_label == arm_label,
        )
    ).first()
    if existing is not None:
        existing.reviewer_id = reviewer_id
        existing.data_json = data_json
        db.add(existing)
        db.commit()
        db.refresh(existing)
        _invalidate_cache(db, project_id, outcome_id)
        return existing

    ad = OutcomeArmData(
        project_id=project_id,
        record_id=record_id,
        outcome_id=outcome_id,
        arm_label=arm_label,
        data_json=data_json,
        reviewer_id=reviewer_id,
    )
    db.add(ad)
    db.commit()
    db.refresh(ad)
    _invalidate_cache(db, project_id, outcome_id)
    return ad


def _invalidate_cache(db: Session, project_id: int, outcome_id: int) -> None:
    db.exec(delete(AnalysisRun).where(
        AnalysisRun.project_id == project_id,
        AnalysisRun.outcome_id == outcome_id,
    ))
    db.commit()


def _collect_studies(
    db: Session, project_id: int, outcome_id: int
) -> list[dict[str, Any]]:
    stmt = select(OutcomeArmData).where(
        OutcomeArmData.project_id == project_id,
        OutcomeArmData.outcome_id == outcome_id,
    )
    arms = db.exec(stmt).all()

    by_record: dict[int, dict[str, dict[str, Any]]] = {}
    for arm in arms:
        rid = arm.record_id
        if rid not in by_record:
            by_record[rid] = {}
        by_record[rid][arm.arm_label] = arm.data_json

    studies: list[dict[str, Any]] = []
    for rid, arms_map in by_record.items():
        if "intervention" in arms_map and "control" in arms_map:
            inter = arms_map["intervention"]
            ctrl = arms_map["control"]
            if "events" in inter and "n" in inter:
                studies.append(
                    {
                        "record_id": rid,
                        "a": int(inter.get("events", 0)),
                        "n1": int(inter.get("n", 0)),
                        "c": int(ctrl.get("events", 0)),
                        "n2": int(ctrl.get("n", 0)),
                        "label": f"Study {rid}",
                        "kind": "binary",
                    }
                )
            elif "mean_val" in inter and "n" in inter:
                studies.append(
                    {
                        "record_id": rid,
                        "mean1": float(inter.get("mean_val", 0.0)),
                        "sd1": float(inter.get("sd_val", 0.0)),
                        "n1": int(inter.get("n", 0)),
                        "mean2": float(ctrl.get("mean_val", 0.0)),
                        "sd2": float(ctrl.get("sd_val", 0.0)),
                        "n2": int(ctrl.get("n", 0)),
                        "label": f"Study {rid}",
                        "kind": "continuous",
                    }
                )
    return studies


def _continuous_md_ci(mean1, sd1, n1, mean2, sd2, n2):
    md = mean1 - mean2
    sp_num = (n1 - 1) * sd1 * sd1 + (n2 - 1) * sd2 * sd2
    sp_den = n1 + n2 - 2
    sp2 = sp_num / sp_den if sp_den > 0 else 1.0
    se_diff = math.sqrt(sp2 * (1.0 / n1 + 1.0 / n2)) if sp2 > 0 else float("inf")
    ci_low = md - 1.959963984540054 * se_diff
    ci_high = md + 1.959963984540054 * se_diff
    return {"md": md, "se": se_diff, "ci_low": ci_low, "ci_high": ci_high}


def run_meta_analysis(
    db: Session,
    project_id: int,
    outcome_id: int,
    analysis_model: str,
) -> dict[str, Any]:
    cached = db.exec(
        select(AnalysisRun).where(
            AnalysisRun.project_id == project_id,
            AnalysisRun.outcome_id == outcome_id,
            AnalysisRun.method == analysis_model,
        )
    ).first()
    if cached is not None and cached.result_json is not None:
        return dict(cached.result_json)

    studies = _collect_studies(db, project_id, outcome_id)
    if len(studies) < 2:
        raise Exception(_META_MIN_STUDIES_MSG)

    outcome = db.get(OutcomeDefinition, outcome_id)
    measure_type = outcome.measure_type if outcome else "binary|RR"
    is_binary = measure_type.startswith("binary|")

    estimates: list[float] = []
    ses: list[float] = []
    rr_studies: list[tuple[int, int, int, int]] = []
    study_results: list[dict[str, Any]] = []
    total_weight = 0.0
    weights: list[float] = []

    for s in studies:
        if is_binary:
            a, n1, c, n2 = s["a"], s["n1"], s["c"], s["n2"]
            rr_res = binary_rr_95ci(a, n1, c, n2, cc=True)
            rr = rr_res["rr"]
            log_rr = math.log(max(rr, 1e-9)) if rr > 0 else 0.0
            ci_low = max(rr_res["ci_low"], 1e-9)
            ci_high = max(rr_res["ci_high"], 1e-9)
            se_log = (math.log(ci_high) - math.log(ci_low)) / (2 * 1.959963984540054)
            estimates.append(log_rr)
            ses.append(se_log)
            rr_studies.append((a, n1, c, n2))
            if se_log > 0 and math.isfinite(se_log):
                w = 1.0 / (se_log * se_log)
            else:
                w = 0.0
            if not math.isfinite(w):
                w = 0.0
            weights.append(w)
            total_weight += w
            study_results.append(
                {
                    "record_id": s["record_id"],
                    "label": s["label"],
                    "rr": rr,
                    "ci_low": rr_res["ci_low"],
                    "ci_high": rr_res["ci_high"],
                    "weight": 0.0,
                }
            )
        else:
            res = _continuous_md_ci(s["mean1"], s["sd1"], s["n1"], s["mean2"], s["sd2"], s["n2"])
            estimates.append(res["md"])
            ses.append(res["se"])
            if res["se"] > 0 and math.isfinite(res["se"]):
                w = 1.0 / (res["se"] * res["se"])
            else:
                w = 0.0
            if not math.isfinite(w):
                w = 0.0
            weights.append(w)
            total_weight += w
            study_results.append(
                {
                    "record_id": s["record_id"],
                    "label": s["label"],
                    "md": res["md"],
                    "ci_low": res["ci_low"],
                    "ci_high": res["ci_high"],
                    "weight": 0.0,
                }
            )

    if total_weight <= 0.0 or not math.isfinite(total_weight):
        raise Exception(_EX8_ZERO_WEIGHT)

    for i, sr in enumerate(study_results):
        sr["weight"] = (weights[i] / total_weight * 100.0) if total_weight > 0 else 0.0

    if analysis_model == "fixed_iv":
        pooled = fixed_iv_pooled(estimates, ses)
        log_pooled = pooled["pooled"]
        if is_binary:
            pooled_val = math.exp(log_pooled)
            p_ci_lo = math.exp(pooled["ci_low"])
            p_ci_hi = math.exp(pooled["ci_high"])
        else:
            pooled_val = log_pooled
            p_ci_lo = pooled["ci_low"]
            p_ci_hi = pooled["ci_high"]
        pooled_effect = {
            "value": pooled_val,
            "ci_low": p_ci_lo,
            "ci_high": p_ci_hi,
            "p_value": pooled["p"],
            "z": pooled["z"],
        }
    elif analysis_model == "fixed_mh" and is_binary:
        mh = fixed_mh_pooled_rr(rr_studies)
        pooled_effect = {
            "value": mh["rr"],
            "ci_low": mh["ci_low"],
            "ci_high": mh["ci_high"],
        }
    elif analysis_model == "random_dl":
        pooled = dl_random_pooled(estimates, ses)
        log_pooled = pooled["pooled"]
        if is_binary:
            pooled_val = math.exp(log_pooled)
            p_ci_lo = math.exp(pooled["ci_low"])
            p_ci_hi = math.exp(pooled["ci_high"])
        else:
            pooled_val = log_pooled
            p_ci_lo = pooled["ci_low"]
            p_ci_hi = pooled["ci_high"]
        tau2_v = float(pooled.get("tau2", 0.0))
        pooled_effect = {
            "value": pooled_val,
            "ci_low": p_ci_lo,
            "ci_high": p_ci_hi,
            "tau2": tau2_v if tau2_v >= 0.0 else 0.0,
        }
    else:
        pooled = fixed_iv_pooled(estimates, ses)
        log_pooled = pooled["pooled"]
        if is_binary:
            pooled_val = math.exp(log_pooled)
            p_ci_lo = math.exp(pooled["ci_low"])
            p_ci_hi = math.exp(pooled["ci_high"])
        else:
            pooled_val = log_pooled
            p_ci_lo = pooled["ci_low"]
            p_ci_hi = pooled["ci_high"]
        pooled_effect = {
            "value": pooled_val,
            "ci_low": p_ci_lo,
            "ci_high": p_ci_hi,
        }

    heterogeneity = compute_heterogeneity(estimates, ses)

    result_json = {
        "outcome_id": outcome_id,
        "model": analysis_model,
        "study_count": len(studies),
        "studies": study_results,
        "pooled_effect": pooled_effect,
        "heterogeneity": heterogeneity,
    }

    run = AnalysisRun(
        project_id=project_id,
        outcome_id=outcome_id,
        method=analysis_model,
        config_json={"outcome_id": outcome_id, "model": analysis_model},
        result_json=result_json,
        status="completed",
        created_by=None,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    result_json["id"] = run.id
    db.commit()

    return result_json


def generate_forest_svg(
    db: Session,
    project_id: int,
    outcome_id: int,
    model: str = "random_dl",
) -> bytes:
    """Render the forest plot of a real meta-analysis.

    Whatever `run_meta_analysis` raises propagates: a plot that showed a neutral
    pooled effect for an outcome that cannot be pooled would be
    indistinguishable from a real null result.
    """
    result = run_meta_analysis(db, project_id, outcome_id, model)

    studies = result["studies"]
    pooled = result["pooled_effect"]
    k = len(studies)
    # The axis is a ratio scale centred on 1. A mean difference lives on a
    # difference scale and can be zero or negative, so it is shifted onto the axis
    # by its no-effect value; the printed numbers stay the real estimates.
    is_ratio = bool(studies) and "rr" in studies[0]

    def _axis_x(value: float) -> float:
        return value if is_ratio else value + 1.0

    row_h = 30
    top_pad = 60
    bottom_pad = 50
    left_pad = 140
    right_pad = 160
    total_h = top_pad + (k + 2) * row_h + bottom_pad
    total_w = left_pad + right_pad + 300

    x0 = left_pad + 100
    x1 = left_pad + 300
    def _log_scale(v: float) -> float:
        v = max(v, 0.01)
        l = math.log10(v)
        t = (l + 1.0) / 2.0
        t = max(0.0, min(1.0, t))
        return x0 + t * (x1 - x0)

    lines: list[str] = []
    lines.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">'
    )
    lines.append(f'<rect width="{total_w}" height="{total_h}" fill="white"/>')
    lines.append(
        f'<line x1="{x0}" y1="{top_pad - 10}" x2="{x1}" y2="{top_pad - 10}" stroke="#333" stroke-width="1"/>'
    )
    for tick, label in [(0.1, "0.1"), (0.5, "0.5"), (1, "1"), (2, "2"), (10, "10")]:
        tx = _log_scale(tick)
        lines.append(
            f'<line x1="{tx}" y1="{top_pad - 14}" x2="{tx}" y2="{top_pad - 6}" stroke="#333" stroke-width="1"/>'
        )
        lines.append(
            f'<text x="{tx}" y="{top_pad - 18}" font-size="10" text-anchor="middle" fill="#333">{xml_escape(str(label))}</text>'
        )
    lines.append(
        f'<line x1="{_log_scale(1.0)}" y1="{top_pad - 10}" x2="{_log_scale(1.0)}" y2="{top_pad + (k + 1) * row_h + 10}" stroke="#999" stroke-width="1" stroke-dasharray="3,3"/>'
    )

    for i, s in enumerate(studies):
        y = top_pad + i * row_h + row_h / 2
        label = s["label"]
        lines.append(
            f'<text x="{left_pad - 10}" y="{y + 4}" font-size="11" text-anchor="end" fill="#222">{xml_escape(label)}</text>'
        )
        effect, ci_low, ci_high = s.get("rr"), s["ci_low"], s["ci_high"]
        if effect is None:
            effect = s["md"]
        cx = _log_scale(_axis_x(effect))
        lx = _log_scale(_axis_x(ci_low))
        rx = _log_scale(_axis_x(ci_high))
        w = s["weight"]
        box_size = max(6.0, min(14.0, 6.0 + w / 5.0))
        lines.append(
            f'<line x1="{lx}" y1="{y}" x2="{rx}" y2="{y}" stroke="#2563eb" stroke-width="1.5"/>'
        )
        lines.append(
            f'<rect x="{cx - box_size/2}" y="{y - box_size/2}" width="{box_size}" height="{box_size}" fill="#2563eb" stroke="#1e40af" stroke-width="0.5"/>'
        )
        weight_str = f'{w:.1f}%'
        lines.append(
            f'<text x="{x1 + 20}" y="{y + 4}" font-size="10" fill="#333">{xml_escape(weight_str)}</text>'
        )
        rr_str = f'{effect:.2f} [{ci_low:.2f}, {ci_high:.2f}]'
        lines.append(
            f'<text x="{x1 + 75}" y="{y + 4}" font-size="10" fill="#333">{xml_escape(rr_str)}</text>'
        )

    y_pool = top_pad + (k + 1) * row_h + row_h / 2
    lines.append(
        f'<text x="{left_pad - 10}" y="{y_pool + 4}" font-size="12" font-weight="bold" text-anchor="end" fill="#222">Pooled</text>'
    )
    p_val, p_lo, p_hi = pooled["value"], pooled["ci_low"], pooled["ci_high"]
    pcx = _log_scale(_axis_x(p_val))
    plx = _log_scale(_axis_x(p_lo))
    prx = _log_scale(_axis_x(p_hi))
    lines.append(
        f'<line x1="{plx}" y1="{y_pool}" x2="{prx}" y2="{y_pool}" stroke="#16a34a" stroke-width="2"/>'
    )
    diamond = f"{pcx},{y_pool - 8} {pcx + 10},{y_pool} {pcx},{y_pool + 8} {pcx - 10},{y_pool}"
    lines.append(f'<polygon points="{diamond}" fill="#16a34a" stroke="#15803d" stroke-width="0.5"/>')
    p_str = f'{p_val:.2f} [{p_lo:.2f}, {p_hi:.2f}]'
    lines.append(
        f'<text x="{x1 + 75}" y="{y_pool + 4}" font-size="11" font-weight="bold" fill="#16a34a">{xml_escape(p_str)}</text>'
    )

    het = result.get("heterogeneity", {})
    i2 = het.get("I2", 0.0)
    foot_y = total_h - 20
    lines.append(
        f'<text x="{left_pad}" y="{foot_y}" font-size="10" fill="#555">Model: {xml_escape(model)} | I² = {i2:.1f}% | k = {k}</text>'
    )
    lines.append("</svg>")

    return "\n".join(lines).encode("utf-8")
