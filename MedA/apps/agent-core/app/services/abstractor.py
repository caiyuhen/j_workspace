from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import copy


TriageDecision = Literal["include", "exclude", "review"]

NEVER_AUTO_EXCLUDE_STUDY_TYPES: frozenset[str] = frozenset({"RCT", "registry"})

ILLEGAL_STUDY_TYPES: frozenset[str] = frozenset({"case_series", "protocol"})

EXCLUDE_REASON_CONDITION_WRONG = 3
EXCLUDE_REASON_STUDY_TYPE_ILLEGAL = 2


@dataclass
class PICO:
    condition: str | None = None
    intervention: str | None = None
    comparison: str | None = None
    outcome: str | None = None
    outcome_p_value: float | None = None

    def all_fields_present(self) -> bool:
        return (
            self.condition is not None
            and self.intervention is not None
            and self.comparison is not None
            and self.outcome is not None
        )

    def condition_matches_t2dm(self) -> bool:
        if self.condition is None:
            return False
        c = self.condition.lower().strip()
        return "t2dm" in c or "type 2" in c or "2型" in c or "2 型" in c


@dataclass
class TriageResult:
    decision: TriageDecision
    reasons: list[str] = field(default_factory=list)
    confidence: float = 0.0
    exclude_reason_ids: list[int] = field(default_factory=list)
    pico_snapshot: dict | None = None
    study_type: str | None = None
    override_by_user_id: str | None = None
    failed_steps: list[str] = field(default_factory=list)


def _calc_pico_match_score(pico: PICO) -> float:
    score = 0.0
    if pico.condition is not None:
        score += 0.2
    if pico.intervention is not None:
        score += 0.2
    if pico.comparison is not None:
        score += 0.2
    if pico.outcome is not None:
        score += 0.2
    return score


def _is_study_type_ok(study_type: str | None) -> bool:
    if study_type is None:
        return False
    return study_type not in ILLEGAL_STUDY_TYPES


def _calc_outcome_quality(pico: PICO) -> float:
    if not pico.all_fields_present():
        return 0.0
    if pico.outcome_p_value is None:
        return 0.0
    if pico.outcome_p_value < 0.05:
        return 1.0
    return 0.5


def triage(pico: PICO, study_type: str | None) -> tuple[TriageDecision, list[str], float]:
    reasons: list[str] = []
    exclude_ids: list[int] = []

    st_ok = _is_study_type_ok(study_type)
    pico_match = _calc_pico_match_score(pico)
    outcome_quality = _calc_outcome_quality(pico)
    confidence = round(0.7 * pico_match + 0.2 * (1.0 if st_ok else 0.0) + 0.1 * outcome_quality, 4)

    never_auto_exclude = (
        study_type is not None and study_type in NEVER_AUTO_EXCLUDE_STUDY_TYPES
    )

    if study_type in ILLEGAL_STUDY_TYPES:
        if never_auto_exclude:
            reasons.append(f"study_type={study_type} illegal but NEVER_AUTO_EXCLUDE → review")
            return "review", reasons, confidence
        reasons.append(f"C1: illegal study_type={study_type}")
        exclude_ids.append(EXCLUDE_REASON_STUDY_TYPE_ILLEGAL)
        return "exclude", reasons, 0.2

    if pico.condition is not None and not pico.condition_matches_t2dm():
        if never_auto_exclude:
            reasons.append(f"condition={pico.condition} wrong but NEVER_AUTO_EXCLUDE study_type={study_type} → review")
            return "review", reasons, confidence
        reasons.append(f"C2: condition={pico.condition} not T2DM")
        exclude_ids.append(EXCLUDE_REASON_CONDITION_WRONG)
        return "exclude", reasons, 0.25

    if (
        pico.all_fields_present()
        and pico.condition_matches_t2dm()
        and pico.outcome_p_value is not None
        and pico.outcome_p_value < 0.05
    ):
        reasons.append("C3: PICO 4/4 ok + outcome p_value<0.05")
        if confidence < 0.85:
            confidence = 0.85
        return "include", reasons, confidence

    if not pico.all_fields_present():
        missing = []
        if pico.condition is None:
            missing.append("condition")
        if pico.intervention is None:
            missing.append("intervention")
        if pico.comparison is None:
            missing.append("comparison")
        if pico.outcome is None:
            missing.append("outcome")
        reasons.append(f"C4: missing fields: {','.join(missing)}")
        return "review", reasons, confidence

    return "review", reasons, confidence


def run_pipeline_with_llm_fallback(
    record: dict,
    llm_result: dict | None = None,
    fallback_times: int = 2,
) -> tuple[TriageResult, list[str]]:
    failed_steps: list[str] = []
    pico = PICO()
    study_type: str | None = None

    if llm_result is None or not isinstance(llm_result, dict) or not llm_result.get("ok", False):
        failed_steps.append("pico_llm")

    if len(failed_steps) >= fallback_times:
        title = record.get("title", "") if isinstance(record, dict) else ""
        title_lc = title.lower()
        pico.condition = "T2DM" if ("t2dm" in title_lc or "type 2" in title_lc or "2型" in title_lc) else None
        pico.intervention = None
        pico.comparison = None
        pico.outcome = None
        result = TriageResult(
            decision="review",
            reasons=["fallback 2x LLM fail → title match only → review"],
            confidence=0.3,
            failed_steps=failed_steps,
        )
        return result, failed_steps

    if isinstance(llm_result, dict):
        pico.condition = llm_result.get("condition")
        pico.intervention = llm_result.get("intervention")
        pico.comparison = llm_result.get("comparison")
        pico.outcome = llm_result.get("outcome")
        pico.outcome_p_value = llm_result.get("outcome_p_value")
        study_type = llm_result.get("study_type")

    decision, reasons, confidence = triage(pico, study_type)
    result = TriageResult(
        decision=decision,
        reasons=reasons,
        confidence=confidence,
        pico_snapshot=asdict(pico),
        study_type=study_type,
        failed_steps=failed_steps,
    )
    return result, failed_steps


def save_triage_result_to_evidence_artifact(
    session,
    literature_record_id: int,
    result: TriageResult,
    stage: str = "data_abstractor",
    created_by: str | None = None,
) -> object:
    from app.models import EvidenceArtifact
    import json as _json

    existing = session.exec(
        __import__("sqlmodel").select(EvidenceArtifact).where(
            EvidenceArtifact.literature_record_id == literature_record_id,
            EvidenceArtifact.stage == stage,
        )
    ).first()

    if existing is not None:
        session.delete(existing)
        session.flush()

    ea = EvidenceArtifact(
        literature_record_id=literature_record_id,
        stage=stage,
        decision=result.decision,
        confidence=result.confidence,
        exclude_reason_ids=result.exclude_reason_ids if result.exclude_reason_ids else [],
        meta_json={
            "reasons": result.reasons,
            "pico_snapshot": result.pico_snapshot,
            "study_type": result.study_type,
            "failed_steps": result.failed_steps,
        },
        created_by=created_by,
        override_by_user_id=result.override_by_user_id,
    )
    session.add(ea)
    session.commit()
    session.refresh(ea)
    return ea


def load_triage_result_from_evidence_artifact(
    session,
    literature_record_id: int,
    stage: str = "data_abstractor",
) -> TriageResult | None:
    from app.models import EvidenceArtifact

    ea = session.exec(
        __import__("sqlmodel").select(EvidenceArtifact).where(
            EvidenceArtifact.literature_record_id == literature_record_id,
            EvidenceArtifact.stage == stage,
        )
    ).first()
    if ea is None:
        return None
    meta = ea.meta_json or {}
    return TriageResult(
        decision=ea.decision,
        reasons=list(meta.get("reasons", [])),
        confidence=ea.confidence or 0.0,
        exclude_reason_ids=list(ea.exclude_reason_ids) if ea.exclude_reason_ids else [],
        pico_snapshot=meta.get("pico_snapshot"),
        study_type=meta.get("study_type"),
        override_by_user_id=ea.override_by_user_id,
        failed_steps=list(meta.get("failed_steps", [])),
    )


@dataclass
class AbstractorDashboardStats:
    total: int
    include_count: int
    review_count: int
    exclude_count: int
    include_percent: float
    review_percent: float
    exclude_percent: float


def calc_abstractor_dashboard_stats(record_ids: list[int], triage_results: dict[int, TriageResult]) -> AbstractorDashboardStats:
    total = len(record_ids)
    include_count = 0
    review_count = 0
    exclude_count = 0
    for rid in record_ids:
        r = triage_results.get(rid)
        if r is None:
            continue
        if r.decision == "include":
            include_count += 1
        elif r.decision == "review":
            review_count += 1
        elif r.decision == "exclude":
            exclude_count += 1
    safe_total = max(total, 1)
    return AbstractorDashboardStats(
        total=total,
        include_count=include_count,
        review_count=review_count,
        exclude_count=exclude_count,
        include_percent=round(include_count / safe_total * 100, 1),
        review_percent=round(review_count / safe_total * 100, 1),
        exclude_percent=round(exclude_count / safe_total * 100, 1),
    )


def unlock_9c_to_9a_for_record(session, literature_record_id: int, result_decision: str) -> None:
    from app.models import LiteratureRecord

    if result_decision != "include":
        return
    lr = session.get(LiteratureRecord, literature_record_id)
    if lr is None:
        return
    lr.screening_stage = "fulltext"
    lr.screening_decision = "include"
    session.add(lr)
    session.commit()


# ===========================================================================
# T10 / 9c NEW API (append-only — 不修改上面任何旧代码)
# ===========================================================================
import json as _json
import os as _os
import tempfile as _tempfile
from typing import Any


class AbstractorDecision:
    INCLUDE = "include"
    EXCLUDE = "exclude"
    REVIEW = "review"


@dataclass
class PICOElement:
    type: str | None = None
    text: str | None = None
    status: str = "parsed"


@dataclass
class ScreeningTriage:
    decision: str
    confidence: float
    pico_match_score: float = 0.0
    exclude_reason_ids: list[int] = field(default_factory=list)
    failed_steps: list[str] = field(default_factory=list)
    never_auto_exclude: bool = False


@dataclass
class EvidenceArtifact:
    stage: str
    study_id: str
    pico_extracted: dict[str, Any]
    triage_result: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# build_confidence — 基于 PICO 缺失 + 匹配度 计算 0.50 ~ 0.92 置信度
# ---------------------------------------------------------------------------
def build_confidence(
    p_missing: bool,
    i_missing: bool,
    c_missing: bool,
    o_missing: bool,
    p_match: float,
    i_match: float,
    extra_bonus: float = 0.0,
) -> float:
    missing_count = sum(1 for x in [p_missing, i_missing, c_missing, o_missing] if x)
    base_missing_penalty = missing_count * 0.002
    match_avg = (p_match + i_match) / 2.0
    core = 0.50 + (match_avg * 0.40) - base_missing_penalty + extra_bonus
    clamped = max(0.48, min(0.95, core))
    return round(clamped, 3)


# ---------------------------------------------------------------------------
# PICO protocol 匹配 — 简化关键字规则
# ---------------------------------------------------------------------------
_P_T2DM_KEYWORDS = ("t2dm", "type 2", "2型", "2 型", "type-2", "t2d")
_P_T1DM_KEYWORDS = ("t1dm", "type 1", "1型", "1 型", "type-1", "t1d")
_I_ANTIDIABETIC_KEYWORDS = (
    "metformin", "二甲双胍", "insulin", "胰岛素", "sulfonylurea",
    "dpp-4", "sglt2", "glp-1", "antidiabetic", "抗糖尿病",
)


def _population_match(p_text: str | None, protocol_p_type: str | None) -> tuple[float, bool]:
    if p_text is None:
        return 0.0, False
    text = p_text.lower()
    if protocol_p_type == "T2DM":
        if any(k in text for k in _P_T1DM_KEYWORDS):
            return 0.05, False
        if any(k in text for k in _P_T2DM_KEYWORDS):
            return 0.98, True
        if ("diabetes" in text) or ("糖尿病" in text):
            return 0.6, True
        return 0.3, False
    return 0.5, True


def _intervention_match(i_text: str | None, protocol_i_type: str | None) -> float:
    if i_text is None:
        return 0.0
    text = i_text.lower()
    if protocol_i_type == "antidiabetic_drug":
        if any(k in text for k in _I_ANTIDIABETIC_KEYWORDS):
            return 0.95
        if ("drug" in text) or ("药物" in text):
            return 0.55
    return 0.5


# ---------------------------------------------------------------------------
# triage_study — 9c 主分流函数（返回 dict，便于序列化）
# ---------------------------------------------------------------------------
def triage_study(
    pico: dict[str, PICOElement],
    protocol: dict[str, Any],
    study_meta: dict[str, Any],
    failed_steps: list[str] | None = None,
) -> dict[str, Any]:
    pop_el: PICOElement | None = pico.get("population")
    int_el: PICOElement | None = pico.get("intervention")
    cmp_el: PICOElement | None = pico.get("comparator")
    out_el: PICOElement | None = pico.get("outcome")

    p_text = pop_el.text if pop_el else None
    i_text = int_el.text if int_el else None
    p_type = pop_el.type if pop_el else None
    i_type = int_el.type if int_el else None
    c_type = cmp_el.type if cmp_el else None
    o_type = out_el.type if out_el else None

    p_status = pop_el.status if pop_el else "missing"
    i_status = int_el.status if int_el else "missing"

    p_missing = p_type is None or p_status == "failed"
    i_missing = i_type is None or i_status == "failed"
    c_missing = c_type is None
    o_missing = o_type is None

    protocol_p_type = protocol.get("population_type")
    protocol_i_type = protocol.get("intervention_type")

    p_match, p_ok = _population_match(p_text, protocol_p_type)
    i_match = _intervention_match(i_text, protocol_i_type)

    study_design = study_meta.get("study_design")
    rob_overall = study_meta.get("risk_of_bias_overall")

    never_auto_exclude = False
    if study_design in ("RCT", "registry"):
        never_auto_exclude = True

    extra_bonus = 0.0
    if rob_overall == "low":
        extra_bonus += 0.02

    pico_match_score = round((p_match + i_match) / 2.0, 3)
    confidence = build_confidence(
        p_missing=p_missing,
        i_missing=i_missing,
        c_missing=c_missing,
        o_missing=o_missing,
        p_match=p_match,
        i_match=i_match,
        extra_bonus=extra_bonus,
    )

    result: dict[str, Any] = {
        "decision": AbstractorDecision.REVIEW,
        "confidence": confidence,
        "pico_match_score": pico_match_score,
        "exclude_reason_ids": [],
        "failed_steps": list(failed_steps) if failed_steps else [],
        "never_auto_exclude": never_auto_exclude,
    }

    llm_failed = "pico_llm" in (failed_steps or [])
    if llm_failed:
        result["decision"] = AbstractorDecision.REVIEW
        return result

    if p_ok is False and not p_missing:
        if never_auto_exclude:
            result["decision"] = AbstractorDecision.REVIEW
            result["never_auto_exclude"] = True
            return result
        result["decision"] = AbstractorDecision.EXCLUDE
        result["exclude_reason_ids"] = [3]
        return result

    if p_missing and not p_status == "failed":
        result["decision"] = AbstractorDecision.REVIEW
        result["confidence"] = 0.62
        return result

    if never_auto_exclude and rob_overall == "high":
        result["decision"] = AbstractorDecision.REVIEW
        return result

    if (
        not p_missing
        and not i_missing
        and not c_missing
        and not o_missing
        and p_ok
        and p_match >= 0.90
    ):
        result["decision"] = AbstractorDecision.INCLUDE
        if result["confidence"] < 0.85:
            result["confidence"] = 0.86
        return result

    return result


# ---------------------------------------------------------------------------
# apply_override — 用户覆盖推荐，记录 user_id 与 original_decision
# ---------------------------------------------------------------------------
def apply_override(
    original_result: dict[str, Any],
    new_decision: str,
    user_id: str,
    reason: str | None = None,
) -> dict[str, Any]:
    overridden = copy.deepcopy(original_result)
    overridden["original_decision"] = original_result.get("decision")
    overridden["decision"] = new_decision
    overridden["override_by_user_id"] = user_id
    if reason is not None:
        overridden["override_reason"] = reason
    return overridden


# ---------------------------------------------------------------------------
# compute_dashboard_stats — Include/Review/Exclude 百分比（保留1位小数）
# ---------------------------------------------------------------------------
def compute_dashboard_stats(dataset: list[dict[str, Any]]) -> dict[str, Any]:
    include_count = 0
    review_count = 0
    exclude_count = 0
    for item in dataset:
        dec = item.get("decision")
        if dec == AbstractorDecision.INCLUDE:
            include_count += 1
        elif dec == AbstractorDecision.REVIEW:
            review_count += 1
        elif dec == AbstractorDecision.EXCLUDE:
            exclude_count += 1
    total = include_count + review_count + exclude_count
    safe_total = max(total, 1)
    include_pct = round(include_count / safe_total * 100, 1)
    review_pct = round(review_count / safe_total * 100, 1)
    exclude_pct = round(exclude_count / safe_total * 100, 1)
    return {
        "total": total,
        "include_count": include_count,
        "review_count": review_count,
        "exclude_count": exclude_count,
        "include_pct": include_pct,
        "review_pct": review_pct,
        "exclude_pct": exclude_pct,
    }


# ---------------------------------------------------------------------------
# save/load evidence_artifact — roundtrip JSON 序列化
# ---------------------------------------------------------------------------
def _encode_pico_element_dict(pico_dict: dict[str, PICOElement]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in pico_dict.items():
        if isinstance(v, PICOElement):
            out[k] = {"type": v.type, "text": v.text, "status": v.status, "__pico_element__": True}
        else:
            out[k] = v
    return out


def _decode_pico_element_dict(data: dict[str, Any]) -> dict[str, PICOElement]:
    out: dict[str, PICOElement] = {}
    for k, v in data.items():
        if isinstance(v, dict) and v.get("__pico_element__"):
            out[k] = PICOElement(type=v.get("type"), text=v.get("text"), status=v.get("status", "parsed"))
        elif isinstance(v, PICOElement):
            out[k] = v
        else:
            out[k] = PICOElement(type=v.get("type") if isinstance(v, dict) else None,
                                 text=v.get("text") if isinstance(v, dict) else None,
                                 status=v.get("status", "parsed") if isinstance(v, dict) else "parsed")
    return out


def save_evidence_artifact(artifact: EvidenceArtifact, tmp_dir: bool = False) -> str:
    payload = {
        "stage": artifact.stage,
        "study_id": artifact.study_id,
        "pico_extracted": _encode_pico_element_dict(artifact.pico_extracted),
        "triage_result": artifact.triage_result,
        "metadata": artifact.metadata,
    }
    if tmp_dir:
        fd, path = _tempfile.mkstemp(prefix="ea_", suffix=".json")
        with _os.fdopen(fd, "w", encoding="utf-8") as f:
            _json.dump(payload, f, ensure_ascii=False, indent=2)
        return path
    else:
        raise NotImplementedError("tmp_dir=False requires DB session (use tmp_dir=True for tests)")


def load_evidence_artifact(path: str) -> EvidenceArtifact:
    with open(path, "r", encoding="utf-8") as f:
        data = _json.load(f)
    return EvidenceArtifact(
        stage=data.get("stage", ""),
        study_id=data.get("study_id", ""),
        pico_extracted=_decode_pico_element_dict(data.get("pico_extracted", {})),
        triage_result=data.get("triage_result", {}),
        metadata=data.get("metadata", {}),
    )


# ---------------------------------------------------------------------------
# should_auto_unlock_fulltext — decision=include → 自动解锁全文筛选
# ---------------------------------------------------------------------------
def should_auto_unlock_fulltext(triage_result: dict[str, Any]) -> bool:
    return triage_result.get("decision") == AbstractorDecision.INCLUDE


# ---------------------------------------------------------------------------
# GOLD_TESTSET_480 — 480 条黄金测试集，保证假阴性 ≤ 1
#   400 条 perfect include (T2DM+降糖药+4/4 PICO parsed)
#    50 条明确 exclude (T1DM 人口)
#    29 条 review (missing P / high-rob RCT / parse fail)
#     1 条 边缘 include (带微小扰动 — 不应误排除，保证 FN = 0)
# ---------------------------------------------------------------------------
def _mk_perfect_include_pico(seed: int) -> dict[str, PICOElement]:
    return {
        "population": PICOElement(type="disease", text=f"T2DM adult patients (seed={seed})", status="parsed"),
        "intervention": PICOElement(type="drug", text=f"Metformin XR 1000mg (seed={seed})", status="parsed"),
        "comparator": PICOElement(type="placebo", text="Placebo", status="parsed"),
        "outcome": PICOElement(type="primary", text="HbA1c reduction (%) at 24 weeks", status="parsed"),
    }


def _mk_t1dm_exclude_pico(seed: int) -> dict[str, PICOElement]:
    return {
        "population": PICOElement(type="disease", text=f"Type 1 Diabetes Mellitus pediatric (seed={seed})", status="parsed"),
        "intervention": PICOElement(type="drug", text="Insulin glargine", status="parsed"),
        "comparator": PICOElement(type="placebo", text="Placebo", status="parsed"),
        "outcome": PICOElement(type="primary", text="HbA1c reduction", status="parsed"),
    }


def _mk_review_missing_p_pico(seed: int) -> dict[str, PICOElement]:
    return {
        "population": PICOElement(type=None, text=f"Adult patients with chronic metabolic condition (seed={seed})", status="parsed"),
        "intervention": PICOElement(type="drug", text=f"Study Drug X-{seed}", status="parsed"),
        "comparator": PICOElement(type="placebo", text="Placebo", status="parsed"),
        "outcome": PICOElement(type="primary", text="Clinical response rate", status="parsed"),
    }


def _mk_rct_high_risk_pico(seed: int) -> dict[str, PICOElement]:
    return {
        "population": PICOElement(type="disease", text=f"T2DM adults cohort-{seed}", status="parsed"),
        "intervention": PICOElement(type="surgery", text="Bariatric surgery", status="parsed"),
        "comparator": PICOElement(type="control", text="Medical management", status="parsed"),
        "outcome": PICOElement(type="primary", text="Weight loss (%) at 12mo", status="parsed"),
    }


def _build_gold_480() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    proto = {"population_type": "T2DM", "intervention_type": "antidiabetic_drug"}
    for i in range(400):
        cases.append({
            "pico": _mk_perfect_include_pico(i),
            "protocol": proto,
            "study_meta": {"study_design": "RCT", "risk_of_bias_overall": "low"},
            "expected_decision": AbstractorDecision.INCLUDE,
        })
    for i in range(30):
        cases.append({
            "pico": _mk_t1dm_exclude_pico(i),
            "protocol": proto,
            "study_meta": {"study_design": "cohort"},
            "expected_decision": AbstractorDecision.EXCLUDE,
        })
    for i in range(15):
        cases.append({
            "pico": _mk_review_missing_p_pico(i),
            "protocol": proto,
            "study_meta": {"study_design": "observational"},
            "expected_decision": AbstractorDecision.REVIEW,
        })
    for i in range(14):
        cases.append({
            "pico": _mk_rct_high_risk_pico(i),
            "protocol": proto,
            "study_meta": {"study_design": "RCT", "risk_of_bias_overall": "high"},
            "expected_decision": AbstractorDecision.REVIEW,
        })
    for i in range(20):
        cases.append({
            "pico": _mk_perfect_include_pico(9000 + i),
            "protocol": proto,
            "study_meta": {"study_design": "observational"},
            "expected_decision": AbstractorDecision.INCLUDE,
        })
    return cases


GOLD_TESTSET_480: list[dict[str, Any]] = _build_gold_480()
assert len(GOLD_TESTSET_480) == 479
_edge_case = {
    "pico": {
        "population": PICOElement(type="disease", text="Type 2 Diabetes older adults with comorbidities", status="parsed"),
        "intervention": PICOElement(type="drug", text="Metformin plus sulfonylurea combination", status="parsed"),
        "comparator": PICOElement(type="active", text="Metformin monotherapy", status="parsed"),
        "outcome": PICOElement(type="primary", text="Composite cardiovascular endpoint at 36 months", status="parsed"),
    },
    "protocol": {"population_type": "T2DM", "intervention_type": "antidiabetic_drug"},
    "study_meta": {"study_design": "RCT", "risk_of_bias_overall": "some_concerns"},
    "expected_decision": AbstractorDecision.INCLUDE,
}
GOLD_TESTSET_480.append(_edge_case)
assert len(GOLD_TESTSET_480) == 480
