import pytest
from app.services.rob2_engine import (
    TL, r, calc_rob2_overall, calc_robinsi_overall,
    domain_d1_rating, grade_ro_downgrade,
)
from app.models import EvidenceArtifact as EA, User, Organization, ResearchProject, LiteratureRecord
from sqlmodel import Session


def _create_test_user(session):
    user = User(user_id="u-test-001", display_name="Test Doctor")
    session.add(user)
    session.flush()
    org = Organization(slug="demo-hospital", name="Demo Hospital")
    session.add(org)
    session.flush()
    return user


def _create_test_project(session, user):
    project = ResearchProject(
        organization_slug="demo-hospital",
        owner_user_id=user.user_id,
        name="Test Project",
        description="Wave 9 test",
        workspace_key="ws-test",
    )
    session.add(project)
    session.flush()
    return project


def test_r1_rob2_any_high_gives_overall_high():
    domains = [
        r(1, TL.LOW),
        r(2, TL.HIGH),
        r(3, TL.LOW),
        r(4, TL.LOW),
        r(5, TL.LOW),
    ]
    assert calc_rob2_overall(domains) == TL.HIGH


def test_r2_rob2_two_plus_some_concerns_gives_overall_some():
    domains = [
        r(1, TL.SOME),
        r(2, TL.LOW),
        r(3, TL.SOME),
        r(4, TL.LOW),
        r(5, TL.LOW),
    ]
    assert calc_rob2_overall(domains) == TL.SOME


def test_r3_rob2_exactly_one_some_concerns_gives_overall_some():
    domains = [
        r(1, TL.LOW),
        r(2, TL.LOW),
        r(3, TL.LOW),
        r(4, TL.SOME),
        r(5, TL.LOW),
    ]
    assert calc_rob2_overall(domains) == TL.SOME


def test_r4_rob2_all_five_low_gives_overall_low():
    domains = [
        r(1, TL.LOW),
        r(2, TL.LOW),
        r(3, TL.LOW),
        r(4, TL.LOW),
        r(5, TL.LOW),
    ]
    assert calc_rob2_overall(domains) == TL.LOW


def test_r5_robinsi_any_critical_gives_overall_critical_top_rollup():
    domains = [
        r(1, TL.LOW),
        r(2, TL.CRIT),
        r(3, TL.HIGH),
        r(4, TL.SOME),
        r(5, TL.LOW),
    ]
    assert calc_robinsi_overall(domains) == TL.CRIT


def test_r6_rob2_all_some_gives_overall_some_boundary():
    domains = [
        r(1, TL.SOME),
        r(2, TL.SOME),
        r(3, TL.SOME),
        r(4, TL.SOME),
        r(5, TL.SOME),
    ]
    assert calc_rob2_overall(domains) == TL.SOME


def test_r7_rob2_all_low_gives_overall_low_alt_assert():
    domains = [r(i, TL.LOW) for i in range(1, 6)]
    result = calc_rob2_overall(domains)
    assert result == TL.LOW
    assert result != TL.SOME
    assert result != TL.HIGH


def test_r8_rob2_d1_high_gives_overall_high():
    domains = [
        r(1, TL.HIGH),
        r(2, TL.LOW),
        r(3, TL.LOW),
        r(4, TL.LOW),
        r(5, TL.LOW),
    ]
    assert calc_rob2_overall(domains) == TL.HIGH


def test_r9_domain_d1_rating_open_label_hba1c_objective_is_some():
    signals = {
        "open_label": True,
        "outcome": "hba1c",
        "outcome_type": "objective",
    }
    assert domain_d1_rating(signals) == TL.SOME


def test_r10_domain_d1_rating_open_label_pain_subjective_no_blind_is_high():
    signals = {
        "open_label": True,
        "outcome": "pain",
        "outcome_type": "subjective",
        "blinded_outcome": False,
    }
    assert domain_d1_rating(signals) == TL.HIGH


def test_r11_grade_ro_downgrade_4studies_3low_1high_25pct_minus1():
    study_ratings = [TL.LOW, TL.LOW, TL.LOW, TL.HIGH]
    assert grade_ro_downgrade(study_ratings) == -1


def test_r12_grade_ro_downgrade_1critical_minus2():
    study_ratings = [TL.CRIT]
    assert grade_ro_downgrade(study_ratings) == -2


def test_r13_grade_ro_downgrade_all_low_0():
    study_ratings = [TL.LOW, TL.LOW, TL.LOW, TL.LOW]
    assert grade_ro_downgrade(study_ratings) == 0


def test_r14_grade_ro_downgrade_some_50pct_2of4_minus1():
    study_ratings = [TL.SOME, TL.SOME, TL.LOW, TL.LOW]
    assert grade_ro_downgrade(study_ratings) == -1


def test_r15_grade_ro_downgrade_3of4_high_75pct_minus2():
    study_ratings = [TL.HIGH, TL.HIGH, TL.HIGH, TL.LOW]
    assert grade_ro_downgrade(study_ratings) == -2


def test_r16_evidence_artifact_quality_ro_roundtrip(db_session):
    user = _create_test_user(db_session)
    project = _create_test_project(db_session, user)
    lr = LiteratureRecord(
        project_id=project.id,
        title="RoB Roundtrip Study",
        source_key="pubmed",
    )
    db_session.add(lr)
    db_session.flush()
    ea = EA(
        literature_record_id=lr.id,
        stage="quality_ro",
        decision="include",
        confidence=0.8,
        exclude_reason_ids=[],
        meta_json={"overall": TL.SOME, "domains": [r(1, TL.LOW), r(2, TL.SOME)]},
        created_by=user.user_id,
        override_by_user_id=None,
    )
    db_session.add(ea)
    db_session.commit()
    q = db_session.query(EA).filter(
        EA.literature_record_id == lr.id,
        EA.stage == "quality_ro",
    ).first()
    assert q is not None
    assert q.stage == "quality_ro"
    assert q.meta_json["overall"] == TL.SOME
    assert q.meta_json["domains"][1]["rating"] == TL.SOME
