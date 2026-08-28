"""Domain profiles for the six demo presets.

The pipeline used to fake steps 2-7 with a table of shrink factors, so the funnel
numbers looked plausible but were not computed from anything. Running the real
screening / RoB 2 / GRADE engines instead needs two things the old synthetic
corpus did not have: text that the PICO extractor can actually match, and an
explicit review protocol to screen against.

Both live here rather than in the PubMed adapter or the pipeline engine because
the adapter (which generates the corpus) and the engine (which screens it) each
need them, and the adapter already imports from the engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PresetProfile:
    """Everything the corpus generator and the screening steps need per preset."""

    snapshot_size: int
    condition: str
    population_text: str
    intervention_text: str
    comparator_text: str
    outcome_labels: tuple[str, ...]
    protocol_population_type: str | None
    protocol_intervention_type: str | None

    def protocol(self) -> dict[str, Any]:
        return {
            "population_type": self.protocol_population_type,
            "intervention_type": self.protocol_intervention_type,
        }


# `outcome_labels` are the labels the compare view has always shown; they stay
# byte-identical so the GRADE comparison keeps naming the same outcomes now that
# the certainty ratings behind them are computed rather than hashed.
PRESET_PROFILES: dict[str, PresetProfile] = {
    "sglt2i_ckd": PresetProfile(
        snapshot_size=178,
        condition="T2DM with chronic kidney disease",
        population_text="T2DM 慢性肾病 CKD adults",
        intervention_text="Dapagliflozin SGLT2i",
        comparator_text="placebo",
        outcome_labels=("eGFR drop 40%", "HF hospitalization", "all-cause death", "serious AEs"),
        protocol_population_type="T2DM",
        protocol_intervention_type="antidiabetic_drug",
    ),
    "empagliflozin_hf": PresetProfile(
        snapshot_size=132,
        condition="T2DM with heart failure",
        population_text="T2DM HFrEF 心衰 adults",
        intervention_text="Empagliflozin SGLT2i",
        comparator_text="placebo",
        outcome_labels=("CV death", "HF hospitalization", "all-cause death", "serious AEs"),
        protocol_population_type="T2DM",
        protocol_intervention_type="antidiabetic_drug",
    ),
    "glp1_weightloss": PresetProfile(
        snapshot_size=188,
        condition="T2DM with obesity",
        population_text="T2DM 肥胖 adults",
        intervention_text="Semaglutide GLP-1",
        comparator_text="placebo",
        outcome_labels=("≥15% weight loss", "HbA1c reduction", "all-cause death", "serious AEs"),
        protocol_population_type="T2DM",
        protocol_intervention_type="antidiabetic_drug",
    ),
    "liraglutide_nafld": PresetProfile(
        snapshot_size=112,
        condition="T2DM with NAFLD",
        population_text="T2DM NAFLD adults",
        intervention_text="Liraglutide GLP-1",
        comparator_text="安慰剂 placebo",
        outcome_labels=("NAS remission", "fibrosis worsening", "all-cause death", "serious AEs"),
        protocol_population_type="T2DM",
        protocol_intervention_type="antidiabetic_drug",
    ),
    # Tolvaptan in ADPKD and blood-pressure targets in CKD are not diabetes
    # questions, so they carry no T2DM population constraint. The screening step
    # treats a null protocol type as "no population restriction" instead of
    # pretending the T2DM rules apply.
    "pkd_tolvaptan": PresetProfile(
        snapshot_size=74,
        condition="autosomal dominant polycystic kidney disease",
        population_text="ADPKD CKD adults",
        intervention_text="Tolvaptan",
        comparator_text="placebo",
        outcome_labels=("eGFR slope", "TKV increase", "all-cause death", "serious AEs"),
        protocol_population_type=None,
        protocol_intervention_type=None,
    ),
    "ckd_blood_pressure_control": PresetProfile(
        snapshot_size=156,
        condition="chronic kidney disease with hypertension",
        population_text="CKD 高血压 adults",
        intervention_text="intensive blood pressure control ACEI ARB",
        comparator_text="usual care",
        outcome_labels=("SBP<130 achievement", "eGFR drop", "CV events", "all-cause death"),
        protocol_population_type=None,
        protocol_intervention_type=None,
    ),
}


def get_profile(preset: str) -> PresetProfile:
    profile = PRESET_PROFILES.get(preset)
    if profile is None:
        raise KeyError(f"no profile for preset: {preset}")
    return profile
