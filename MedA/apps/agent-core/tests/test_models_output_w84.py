import pytest
from sqlalchemy import inspect
from app.models import (
    GradeAssessment as GA, SofTableRow as STR,
    ReportSnapshot as RS, Prisma2020Checklist as PC,
)

def test_mig_01_four_tables_exist(db_session):
    insp = inspect(db_session.bind)
    names = set(insp.get_table_names())
    for n in {"gradeassessment","softablenode","reportsnapshot","prisma2020checklist"}:
        assert n in names, f"missing table {n}; got={names}"

def test_mig_02_gradeassessment_has_uniqueconstraint_outcome_reviewer():
    constraints = list(GA.__table__.constraints)
    # Find uq with 2 cols outcome_id+reviewer_id
    ok = False
    for c in constraints:
        try:
            cols = sorted(col.name for col in c.columns)
            if sorted(("outcome_id","reviewer_id")) == cols:
                ok = True
        except Exception:
            pass
    assert ok is True, "UniqueConstraint (outcome_id,reviewer_id) not found on gradeassessment"

def test_mig_03_reportsnapshot_sha256_grade_not_nullable():
    col = RS.__table__.c["sha256_grade"]
    assert col.nullable is False, f"sha256_grade nullable={col.nullable}, required False"

def test_mig_04_prisma_default_all_false_insert_count_0(db_session):
    count = db_session.query(PC).count()
    assert count == 0

def test_rule_O1_locked_cannot_change_domains_literal_exact():
    from app.services.output_stage import assert_rule_O1, OutputStageError
    with pytest.raises(OutputStageError) as ei:
        assert_rule_O1(locked=True, touch="domains_5")
    assert str(ei.value) == "grade_locked_cannot_change_assessment", f"got: {str(ei.value)!r}"

def test_rule_O2_grade_requires_completed_meta_analysis_literal():
    from app.services.output_stage import assert_rule_O2, OutputStageError
    with pytest.raises(OutputStageError) as ei:
        assert_rule_O2(has_meta=False)
    assert str(ei.value) == "grade_requires_completed_meta_analysis", f"got={str(ei.value)!r}"

def test_rule_O5_no_grade_report_requires_at_least_one_literal():
    from app.services.output_stage import assert_rule_O5, OutputStageError
    with pytest.raises(OutputStageError) as ei:
        assert_rule_O5(grade_count=0)
    assert str(ei.value) == "report_requires_at_least_one_grade_assessment", f"got={str(ei.value)!r}"

def test_rule_O6_incomplete_missing_content_sections_literal():
    from app.services.output_stage import assert_rule_O6_complete, OutputStageError
    with pytest.raises(OutputStageError) as ei:
        assert_rule_O6_complete(md="", html="<x>", txt="T")
    assert str(ei.value) == "report_snapshot_incomplete_missing_content_sections", f"got={str(ei.value)!r}"

def test_rule_O7_prisma_locked_cannot_change_items_literal():
    from app.services.output_stage import assert_rule_O7, OutputStageError
    with pytest.raises(OutputStageError) as ei:
        assert_rule_O7(locked=True)
    assert str(ei.value) == "prisma_checklist_locked_cannot_change_items", f"got={str(ei.value)!r}"

def test_rule_O8_grade_invalid_domain_count_require_exact_5_keys_literal():
    from app.services.output_stage import assert_rule_O8, OutputStageError
    with pytest.raises(OutputStageError) as ei:
        assert_rule_O8(keys_count=4)
    assert str(ei.value) == "grade_invalid_domain_count_require_exact_5_keys", f"got={str(ei.value)!r}"
