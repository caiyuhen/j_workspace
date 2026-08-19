from __future__ import annotations
import pytest
import json
import copy
from app.services.abstractor import (
    AbstractorDecision,
    PICOElement,
    ScreeningTriage,
    EvidenceArtifact,
    triage_study,
    build_confidence,
    apply_override,
    compute_dashboard_stats,
    save_evidence_artifact,
    load_evidence_artifact,
    should_auto_unlock_fulltext,
    GOLD_TESTSET_480,
)


def _base_pico_perfect():
    return {
        "population": PICOElement(type="disease", text="Type 2 Diabetes Mellitus adults", status="parsed"),
        "intervention": PICOElement(type="drug", text="Metformin 500mg BID", status="parsed"),
        "comparator": PICOElement(type="placebo", text="Placebo", status="parsed"),
        "outcome": PICOElement(type="primary", text="HbA1c reduction at 24 weeks", status="parsed"),
    }


def _base_protocol_pico():
    return {
        "population_type": "T2DM",
        "intervention_type": "antidiabetic_drug",
    }


class TestAbstractor9cBase:
    def test_A1_decision_enum_values(self):
        assert AbstractorDecision.INCLUDE == "include"
        assert AbstractorDecision.EXCLUDE == "exclude"
        assert AbstractorDecision.REVIEW == "review"

    def test_A2_triage_result_structure(self):
        pico = _base_pico_perfect()
        result = triage_study(pico=pico, protocol=_base_protocol_pico(), study_meta={})
        assert "decision" in result
        assert "confidence" in result
        assert isinstance(result["confidence"], float)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_A3_confidence_build_perfect(self):
        conf = build_confidence(p_missing=False, i_missing=False, c_missing=False, o_missing=False, p_match=1.0, i_match=1.0)
        assert conf >= 0.88

    def test_A4_confidence_build_all_missing(self):
        conf = build_confidence(p_missing=True, i_missing=True, c_missing=True, o_missing=True, p_match=0.0, i_match=0.0)
        assert conf <= 0.52

    def test_A5_pico_element_dataclass(self):
        el = PICOElement(type="drug", text="Aspirin", status="parsed")
        assert el.type == "drug"
        assert el.text == "Aspirin"
        assert el.status == "parsed"

    def test_A6_triage_include_basic(self):
        pico = _base_pico_perfect()
        result = triage_study(pico=pico, protocol=_base_protocol_pico(), study_meta={})
        assert result["decision"] == AbstractorDecision.INCLUDE


class TestAbstractor9cNew:
    def test_A7_perfect_pico_include_confidence_085_plus(self):
        pico = _base_pico_perfect()
        result = triage_study(pico=pico, protocol=_base_protocol_pico(), study_meta={})
        assert result["decision"] == AbstractorDecision.INCLUDE
        assert result["confidence"] >= 0.85
        assert "pico_match_score" in result
        assert result["pico_match_score"] >= 0.90

    def test_A8_t1dm_population_against_t2dm_protocol_exclude(self):
        pico = {
            "population": PICOElement(type="disease", text="Type 1 Diabetes Mellitus pediatric", status="parsed"),
            "intervention": PICOElement(type="drug", text="Insulin glargine", status="parsed"),
            "comparator": PICOElement(type="placebo", text="Placebo", status="parsed"),
            "outcome": PICOElement(type="primary", text="HbA1c reduction", status="parsed"),
        }
        protocol = _base_protocol_pico()
        result = triage_study(pico=pico, protocol=protocol, study_meta={})
        assert result["decision"] == AbstractorDecision.EXCLUDE
        assert "exclude_reason_ids" in result
        assert 3 in result["exclude_reason_ids"]

    def test_A9_pico_missing_p_type_review_062_range(self):
        pico = {
            "population": PICOElement(type=None, text="Adult patients with chronic condition", status="parsed"),
            "intervention": PICOElement(type="drug", text="Study Drug X", status="parsed"),
            "comparator": PICOElement(type="placebo", text="Placebo", status="parsed"),
            "outcome": PICOElement(type="primary", text="Clinical response", status="parsed"),
        }
        result = triage_study(pico=pico, protocol=_base_protocol_pico(), study_meta={})
        assert result["decision"] == AbstractorDecision.REVIEW
        assert 0.58 <= result["confidence"] <= 0.68

    def test_A10_llm_pico_parse_fail_twice_review(self):
        pico = {
            "population": PICOElement(type=None, text=None, status="failed"),
            "intervention": PICOElement(type=None, text=None, status="failed"),
            "comparator": PICOElement(type=None, text=None, status="parsed"),
            "outcome": PICOElement(type=None, text=None, status="parsed"),
        }
        result = triage_study(
            pico=pico,
            protocol=_base_protocol_pico(),
            study_meta={},
            failed_steps=["pico_llm", "pico_llm_retry"],
        )
        assert result["decision"] == AbstractorDecision.REVIEW
        assert "failed_steps" in result
        assert "pico_llm" in result["failed_steps"]

    def test_A11_rct_high_risk_never_auto_exclude(self):
        pico = {
            "population": PICOElement(type="disease", text="T2DM adults", status="parsed"),
            "intervention": PICOElement(type="surgery", text="Bariatric surgery", status="parsed"),
            "comparator": PICOElement(type="control", text="Medical management", status="parsed"),
            "outcome": PICOElement(type="primary", text="Weight loss at 12mo", status="parsed"),
        }
        study_meta = {
            "study_design": "RCT",
            "risk_of_bias_overall": "high",
        }
        result = triage_study(pico=pico, protocol=_base_protocol_pico(), study_meta=study_meta)
        assert result["decision"] == AbstractorDecision.REVIEW
        assert result.get("never_auto_exclude") is True

    def test_A12_confidence_perfect_boundary_090_plus(self):
        conf_edge = build_confidence(
            p_missing=False, i_missing=False, c_missing=False, o_missing=False,
            p_match=0.99, i_match=0.99, extra_bonus=0.0
        )
        assert conf_edge >= 0.89
        assert abs(conf_edge - 0.90) <= 0.02
        conf_perfect = build_confidence(
            p_missing=False, i_missing=False, c_missing=False, o_missing=False,
            p_match=1.0, i_match=1.0, extra_bonus=0.02
        )
        assert conf_perfect >= 0.90

    def test_A13_all_missing_boundary_050(self):
        conf = build_confidence(
            p_missing=True, i_missing=True, c_missing=True, o_missing=True,
            p_match=0.0, i_match=0.0
        )
        assert abs(conf - 0.50) <= 0.03

    def test_A14_gold_480_false_negative_le_1(self):
        false_negatives = 0
        for idx, case in enumerate(GOLD_TESTSET_480):
            result = triage_study(
                pico=case["pico"],
                protocol=case["protocol"],
                study_meta=case.get("study_meta", {}),
            )
            if case["expected_decision"] == AbstractorDecision.INCLUDE and result["decision"] != AbstractorDecision.INCLUDE:
                false_negatives += 1
        fn_rate = false_negatives / 480.0
        assert false_negatives <= 1, f"Gold 480 FN={false_negatives} rate={fn_rate:.2%} exceeds 1/480 (0.21%)"
        assert fn_rate <= 0.0021

    def test_A15_evidence_artifact_roundtrip(self):
        artifact = EvidenceArtifact(
            stage="data_abstractor",
            study_id="study_001",
            pico_extracted=_base_pico_perfect(),
            triage_result={"decision": "include", "confidence": 0.92},
            metadata={"version": 1, "source": "unit_test"},
        )
        path = save_evidence_artifact(artifact, tmp_dir=True)
        restored = load_evidence_artifact(path)
        assert restored.stage == "data_abstractor"
        assert restored.study_id == "study_001"
        assert restored.triage_result["decision"] == "include"
        assert restored.pico_extracted["population"].text == _base_pico_perfect()["population"].text

    def test_A16_user_override_records_override_by_user_id(self):
        original = triage_study(pico=_base_pico_perfect(), protocol=_base_protocol_pico(), study_meta={})
        overridden = apply_override(
            original_result=original,
            new_decision=AbstractorDecision.EXCLUDE,
            user_id="user_42",
            reason="Manual exclusion per protocol",
        )
        assert overridden["override_by_user_id"] == "user_42"
        assert overridden["decision"] == AbstractorDecision.EXCLUDE
        assert "original_decision" in overridden
        assert overridden["original_decision"] == original["decision"]

    def test_A17_dashboard_stats_integrity_percentages(self):
        dataset = []
        for _ in range(218):
            dataset.append({"decision": AbstractorDecision.INCLUDE})
        for _ in range(132):
            dataset.append({"decision": AbstractorDecision.REVIEW})
        for _ in range(129):
            dataset.append({"decision": AbstractorDecision.EXCLUDE})
        for _ in range(1):
            dataset.append({"decision": "unknown_ignore"})
        stats = compute_dashboard_stats(dataset)
        total_valid = 218 + 132 + 129
        assert stats["total"] == total_valid
        assert abs(stats["include_pct"] - 45.5) <= 0.2
        assert abs(stats["review_pct"] - 27.5) <= 0.2
        assert abs(stats["exclude_pct"] - 26.9) <= 0.2
        assert abs(stats["include_pct"] + stats["review_pct"] + stats["exclude_pct"] - 100.0) <= 0.5

    def test_A18_include_decision_auto_unlock_screening_fulltext(self):
        pico = _base_pico_perfect()
        result = triage_study(pico=pico, protocol=_base_protocol_pico(), study_meta={})
        unlock = should_auto_unlock_fulltext(result)
        assert unlock is True
        result_review = copy.deepcopy(result)
        result_review["decision"] = AbstractorDecision.REVIEW
        assert should_auto_unlock_fulltext(result_review) is False
        result_exclude = copy.deepcopy(result)
        result_exclude["decision"] = AbstractorDecision.EXCLUDE
        assert should_auto_unlock_fulltext(result_exclude) is False
