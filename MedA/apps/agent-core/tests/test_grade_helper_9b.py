import pytest
from sqlmodel import Session
from app.models import User, Organization, ResearchProject, LiteratureRecord
from app.models import EvidenceArtifact as EA
from app.services.grade_engine import grade_ro_downgrade_evidence_artifact


def _setup_project_with_records(db_session: Session, n_records: int = 4):
    user = User(user_id="u-gh-9b", display_name="GradeHelper 9b")
    db_session.add(user)
    org = Organization(slug="gh-hospital", name="GH Hospital")
    db_session.add(org)
    db_session.flush()
    project = ResearchProject(
        organization_slug="gh-hospital",
        owner_user_id=user.user_id,
        name="GradeHelper 9b Project",
        description="G1/G2/G3 Grade Downgrade Tests",
        workspace_key="ws-gh-9b",
    )
    db_session.add(project)
    db_session.flush()
    record_ids: list[int] = []
    for i in range(n_records):
        lr = LiteratureRecord(
            project_id=project.id,
            title=f"Literature Record {i + 1}",
            source_key="pubmed",
        )
        db_session.add(lr)
        db_session.flush()
        record_ids.append(lr.id)
    return user, record_ids


def _ea_factory(record_id: int, overall: str, stage: str = "quality_ro") -> EA:
    return EA(
        literature_record_id=record_id,
        stage=stage,
        decision="include",
        confidence=0.9,
        exclude_reason_ids=[],
        meta_json={"overall": overall, "tool": "RoB2"},
        created_by="u-gh-9b",
        override_by_user_id=None,
    )


def test_r13_g1_some_concerns_ge_25pct_returns_minus_1(db_session):
    """G1: Some >=25% → return -1. 4 records: 1 some_concerns + 3 low = 25% → -1"""
    _, rids = _setup_project_with_records(db_session, n_records=4)
    db_session.add_all([
        _ea_factory(rids[0], "some_concerns"),
        _ea_factory(rids[1], "low"),
        _ea_factory(rids[2], "low"),
        _ea_factory(rids[3], "low"),
    ])
    db_session.commit()
    result = grade_ro_downgrade_evidence_artifact(rids, db_session)
    assert result == -1


def test_r14_g2_crit_high_ge_25pct_returns_minus_2(db_session):
    """G2: CRIT/High >=25% → return -2. 4 records: 1 critical + 3 low = 25% → -2"""
    _, rids = _setup_project_with_records(db_session, n_records=4)
    db_session.add_all([
        _ea_factory(rids[0], "critical"),
        _ea_factory(rids[1], "low"),
        _ea_factory(rids[2], "low"),
        _ea_factory(rids[3], "low"),
    ])
    db_session.commit()
    result = grade_ro_downgrade_evidence_artifact(rids, db_session)
    assert result == -2


def test_r15_g3_all_low_returns_0(db_session):
    """G3: all low → return 0. 4 records: all low → 0"""
    _, rids = _setup_project_with_records(db_session, n_records=4)
    db_session.add_all([
        _ea_factory(rids[0], "low"),
        _ea_factory(rids[1], "low"),
        _ea_factory(rids[2], "low"),
        _ea_factory(rids[3], "low"),
    ])
    db_session.commit()
    result = grade_ro_downgrade_evidence_artifact(rids, db_session)
    assert result == 0
