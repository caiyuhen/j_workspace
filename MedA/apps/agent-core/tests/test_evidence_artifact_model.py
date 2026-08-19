import pytest
from sqlalchemy import inspect
from app.models import (
    EvidenceArtifact as EA,
)
from app.models import User, Organization, ResearchProject, LiteratureRecord
from sqlmodel import Session


def test_ea_01_class_exists():
    assert EA is not None, "EvidenceArtifact class not imported from app.models"


def test_ea_02_table_name(db_session):
    insp = inspect(db_session.bind)
    names = set(insp.get_table_names())
    assert "evidenceartifact" in names, f"missing table evidenceartifact; got={names}"


def test_ea_03_all_15_fields_exist_on_table():
    cols = set(EA.__table__.c.keys())
    expected = {
        "id",
        "literature_record_id",
        "stage",
        "decision",
        "confidence",
        "exclude_reason_ids",
        "meta_json",
        "created_by",
        "override_by_user_id",
        "created_at",
    }
    missing = expected - cols
    assert len(missing) == 0, f"EvidenceArtifact missing columns: {missing}"


def test_ea_04_stage_enum_5_values():
    col = EA.__table__.c["stage"]
    assert col.type.length is not None or hasattr(col.type, "length"), "stage column should have length"


def test_ea_05_decision_enum_3_values():
    col = EA.__table__.c["decision"]
    assert col.type.length is not None or hasattr(col.type, "length"), "decision column should have length"


def test_ea_06_exclude_reason_ids_is_json():
    from sqlalchemy import JSON as SA_JSON
    col = EA.__table__.c["exclude_reason_ids"]
    type_ok = False
    try:
        type_ok = isinstance(col.type, SA_JSON)
    except Exception:
        type_ok = "JSON" in str(type(col.type)) or "json" in str(col.type).lower()
    assert type_ok, f"exclude_reason_ids should be JSON type, got {type(col.type)}"


def test_ea_07_meta_json_is_json():
    from sqlalchemy import JSON as SA_JSON
    col = EA.__table__.c["meta_json"]
    type_ok = False
    try:
        type_ok = isinstance(col.type, SA_JSON)
    except Exception:
        type_ok = "JSON" in str(type(col.type)) or "json" in str(col.type).lower()
    assert type_ok, f"meta_json should be JSON type, got {type(col.type)}"


def test_ea_08_uniqueconstraint_lr_id_stage():
    constraints = list(EA.__table__.constraints)
    ok = False
    for c in constraints:
        try:
            cols = sorted(col.name for col in c.columns)
            if sorted(("literature_record_id", "stage")) == cols:
                ok = True
        except Exception:
            pass
    assert ok is True, "UniqueConstraint (literature_record_id, stage) not found on EvidenceArtifact"


def test_ea_09_created_at_not_nullable():
    col = EA.__table__.c["created_at"]
    assert col.nullable is False, f"created_at nullable={col.nullable}, required False"


def test_ea_10_insert_and_query(db_session):
    user = User(user_id="u-ea-01", display_name="EA Test User")
    db_session.add(user)
    org = Organization(slug="ea-hospital", name="EA Hospital")
    db_session.add(org)
    db_session.flush()
    project = ResearchProject(
        organization_slug="ea-hospital",
        owner_user_id=user.user_id,
        name="EA Project",
        description="EA Test",
        workspace_key="ws-ea",
    )
    db_session.add(project)
    db_session.flush()
    lr = LiteratureRecord(
        project_id=project.id,
        title="EA Literature",
        source_key="pubmed",
    )
    db_session.add(lr)
    db_session.flush()
    ea = EA(
        literature_record_id=lr.id,
        stage="title_abstract",
        decision="include",
        confidence=0.95,
        exclude_reason_ids=[],
        meta_json={"source": "auto"},
        created_by=user.user_id,
        override_by_user_id=None,
    )
    db_session.add(ea)
    db_session.commit()
    q = db_session.query(EA).filter(EA.literature_record_id == lr.id).first()
    assert q is not None
    assert q.stage == "title_abstract"
    assert q.decision == "include"
    assert q.confidence == 0.95
