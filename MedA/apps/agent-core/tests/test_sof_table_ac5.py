import pytest
from app.services.sof_table_engine import build_sof_row_12cols, SofInputMeta
from app.services.grade_engine import Grade5Domains, Grade3Upgrades, compute_certainty_final

MACE_META = SofInputMeta(
    project_id=1, outcome_id=7, outcome_label="MACE at 12mo",
    participants_n=500, studies_k=5,
    effect_measure_label="RR 0.82 [0.72, 0.94]",
    pooled_rr=0.82, risk_control_baseline=0.20,
)

GOLDEN_12_KEYS = sorted([
    "project_id","outcome_id","outcome_label","participants_n","studies_k",
    "effect_measure_label","risk_of_bias","indirectness","inconsistency",
    "imprecision","publication_bias","certainty",
])

def _dom(r="no_concerns", ind="no_concerns", inc="no_concerns", imp="no_concerns", pub="no_concerns"):
    return Grade5Domains(risk_of_bias=r, indirectness=ind, inconsistency=inc, imprecision=imp, publication_bias=pub)
def _up(le=False, dr=False, cr=False):
    return Grade3Upgrades(large_effect=le, dose_response=dr, confounders_reduce=cr)

def test_ac5_sof_12_keys_exact_set_and_certainty_moderate_1_downgrade():
    d = _dom(r="some_concerns")  # only 1 some = Moderate
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, domains=d, upgrades=_up(), cer=cer)
    keys = sorted(row.model_dump(exclude_none=False).keys())
    missing = [k for k in GOLDEN_12_KEYS if k not in keys]
    assert missing == [], f"missing 12-key cols: {missing}; got={keys}"
    assert cer == "Moderate"
    assert row.certainty == "Moderate"

def test_sof_numeric_participants_and_studies_k():
    d = _dom(r="some_concerns")
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer)
    assert row.participants_n == 500
    assert row.studies_k == 5

def test_sof_outcome_label_string_match():
    d = _dom()
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer)
    assert row.outcome_label == "MACE at 12mo"

def test_sof_effect_measure_label_starts_RR():
    d = _dom()
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer)
    assert row.effect_measure_label.startswith("RR "), f"got={row.effect_measure_label!r}"

def test_sof_absolute_risk_intervention_baseline_20pct_times_082_equals_16pct4():
    d = _dom()
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer)
    assert isinstance(row.absolute_risk_intervention, str) and len(row.absolute_risk_intervention) >= 3
    # 20% * 0.82 = 16.4% -> expect "16.4%" in string
    assert "16.4%" in row.absolute_risk_intervention, f"got={row.absolute_risk_intervention!r}"

def test_sof_absolute_risk_control_baseline_20pct():
    d = _dom()
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer)
    assert "20.0%" in (row.absolute_risk_control or ""), f"got={row.absolute_risk_control!r}"

def test_sof_comments_default_none_ok():
    d = _dom()
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer, comments=None)
    assert row.comments is None

def test_sof_comments_non_none_value_preserved():
    d = _dom()
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer, comments="Dose-response unclear")
    assert row.comments == "Dose-response unclear"

def test_sof_certainty_low_when_two_some_downgrade():
    d = _dom(r="some_concerns", ind="some_concerns")  # score 2 -> Low
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer)
    assert row.certainty == "Low", f"got={row.certainty!r} cer={cer}"

def test_sof_certainty_verylow_when_five_some_score_5_bucket3():
    d = _dom("some_concerns","some_concerns","some_concerns","some_concerns","some_concerns")
    cer = compute_certainty_final(d, _up(), "High")
    row = build_sof_row_12cols(MACE_META, d, _up(), cer=cer)
    assert cer == "VeryLow"
    assert row.certainty == "VeryLow"
