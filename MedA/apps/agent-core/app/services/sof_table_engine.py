from __future__ import annotations
from dataclasses import dataclass
from pydantic import BaseModel
from app.services.grade_engine import Grade5Domains, Grade3Upgrades

@dataclass(frozen=True, slots=True)
class SofInputMeta:
    project_id: int
    outcome_id: int
    outcome_label: str
    participants_n: int
    studies_k: int
    effect_measure_label: str
    pooled_rr: float | None = None
    risk_control_baseline: float = 0.0

class SofRow12(BaseModel):
    project_id: int
    outcome_id: int
    outcome_label: str
    participants_n: int
    studies_k: int
    effect_measure_label: str
    risk_of_bias: str
    indirectness: str
    inconsistency: str
    imprecision: str
    publication_bias: str
    certainty: str
    absolute_risk_intervention: str | None = None
    absolute_risk_control: str | None = None
    comments: str | None = None

def _absolute_risk(meta: SofInputMeta) -> tuple[str, str]:
    rc = max(0.0, min(1.0, float(meta.risk_control_baseline)))
    if meta.pooled_rr is None:
        ri_str = "NR"
    else:
        ri = max(0.0, min(1.0, rc * float(meta.pooled_rr)))
        ri_str = f"{ri*100:.1f}%"
    rc_str = f"{rc*100:.1f}%"
    return ri_str, rc_str

def build_sof_row_12cols(
    meta: SofInputMeta,
    domains: Grade5Domains,
    upgrades: Grade3Upgrades,
    cer: str,
    comments: str | None = None,
) -> SofRow12:
    ri, rc = _absolute_risk(meta)
    return SofRow12(
        project_id=meta.project_id,
        outcome_id=meta.outcome_id,
        outcome_label=meta.outcome_label,
        participants_n=meta.participants_n,
        studies_k=meta.studies_k,
        effect_measure_label=meta.effect_measure_label,
        risk_of_bias=domains.risk_of_bias,
        indirectness=domains.indirectness,
        inconsistency=domains.inconsistency,
        imprecision=domains.imprecision,
        publication_bias=domains.publication_bias,
        certainty=cer,
        absolute_risk_intervention=ri,
        absolute_risk_control=rc,
        comments=comments,
    )
