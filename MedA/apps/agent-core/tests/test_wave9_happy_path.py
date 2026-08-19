import pytest
from sqlmodel import Session, select, and_, func
from app.models import (
    User,
    Organization,
    ResearchProject,
    LiteratureRecord,
    EvidenceArtifact as EA,
)
from app.services.screening_engine import (
    calc_funnel_from_records,
    calc_funnel_locks_integrity,
    FUNNEL_ORDER,
    query_evidence_artifact_count,
    bulk_upsert_evidence_artifacts,
)
from app.services.rob2_engine import (
    TL,
    r,
    calc_rob2_overall,
    grade_ro_downgrade,
)


def _create_user_and_project(session: Session):
    user = User(user_id="u-dr-user", display_name="Dr. User")
    session.add(user)
    org = Organization(slug="meda-hospital", name="MedA Hospital")
    session.add(org)
    session.flush()
    project = ResearchProject(
        organization_slug="meda-hospital",
        owner_user_id=user.user_id,
        name="GLP-1 vs Insulin T2DM",
        description="Wave 9 Happy Path Integration Test",
        workspace_key="ws-wave9-happy",
    )
    session.add(project)
    session.flush()
    return user, project


def _create_n_literature_records(
    session: Session, project: ResearchProject, n: int = 100
) -> list[LiteratureRecord]:
    records = []
    for i in range(n):
        lr = LiteratureRecord(
            project_id=project.id,
            title=f"T2DM GLP-1 Study #{i + 1:03d}: Randomized controlled trial",
            authors=f"Author{i+1:02d} A, Author{i+1:02d} B",
            journal="Diabetes Care" if i % 2 == 0 else "Lancet Diabetes Endocrinol",
            year=2020 + (i % 6),
            doi=f"10.1000/doi{i+1:05d}",
            pmid=f"PMID-{38000000 + i}",
            abstract=f"Abstract for study #{i+1:03d}: Comparing GLP-1 receptor agonists vs basal insulin in type 2 diabetes mellitus patients.",
            source_key="pubmed",
            source_label="PubMed",
            dedupe_status="unique",
            pico_status="not_extracted",
            screening_stage=None,
            screening_decision=None,
            exclude_reason_json=None,
            screening_notes=None,
        )
        records.append(lr)
    session.add_all(records)
    session.flush()
    return records


def test_wave9_happy_path_end_to_end(db_session: Session):
    # ========== Step 1: RED Setup — User + Project + 100 LiteratureRecords ==========
    user, project = _create_user_and_project(db_session)
    assert user.display_name == "Dr. User"
    assert project.name == "GLP-1 vs Insulin T2DM"

    records = _create_n_literature_records(db_session, project, n=100)
    assert len(records) == 100
    n3_count = db_session.exec(
        select(func.count(LiteratureRecord.id)).where(
            LiteratureRecord.project_id == project.id
        )
    ).one()
    assert n3_count == 100, f"N3=100 expected, got {n3_count}"

    # ========== Step 2: funnel-stats 返回 N4=100 ==========
    funnel_raw = calc_funnel_from_records(n3=100, n4_dupes_removed=0)
    assert funnel_raw["N3"] == 100
    assert funnel_raw["N4"] == 100, f"N4=100 expected, got {funnel_raw['N4']}"
    assert funnel_raw["E1"] == 100

    funnel_with_locks = calc_funnel_locks_integrity(n3=100, n4_dupes_removed=0)
    assert funnel_with_locks["N4"]["count"] == 100
    assert funnel_with_locks["N4"]["locked"] is False

    # ========== Step 3: 40 TA decisions — 30 include + 10 exclude (#2 Wrong Study Type) ==========
    ta_include_ids = [r.id for r in records[:30]]
    ta_exclude_ids = [r.id for r in records[30:40]]

    ta_include_eas = []
    for rid in ta_include_ids:
        ta_include_eas.append(
            EA(
                literature_record_id=rid,
                stage="screening_ta",
                decision="include",
                confidence=0.9,
                exclude_reason_ids=None,
                meta_json={"auto_by": "dr_user_ta_screen"},
                created_by=user.user_id,
            )
        )

    ta_exclude_eas = []
    for rid in ta_exclude_ids:
        ta_exclude_eas.append(
            EA(
                literature_record_id=rid,
                stage="screening_ta",
                decision="exclude",
                confidence=0.85,
                exclude_reason_ids=[2],
                meta_json={"preset_class": 2, "note": "Wrong Study Type — Observational, not RCT"},
                created_by=user.user_id,
            )
        )

    inserted = bulk_upsert_evidence_artifacts(db_session, ta_include_eas + ta_exclude_eas)
    assert inserted == 40, f"40 TA upserts expected, got {inserted}"
    db_session.flush()

    ta_include_count = query_evidence_artifact_count(
        db_session, stage="screening_ta", decision="include", project_id=project.id
    )
    ta_exclude_count = query_evidence_artifact_count(
        db_session, stage="screening_ta", decision="exclude", project_id=project.id
    )
    assert ta_include_count == 30, f"TA include=30 expected, got {ta_include_count}"
    assert ta_exclude_count == 10, f"TA exclude=10 expected, got {ta_exclude_count}"

    # ========== Step 4: funnel 验证 E3=60 ==========
    e2_ta_excluded = ta_exclude_count
    funnel_ta = calc_funnel_from_records(
        n3=100, n4_dupes_removed=0, e2=e2_ta_excluded
    )
    e3_expected = 100 - e2_ta_excluded
    assert funnel_ta["E3"] == e3_expected, f"E3={e3_expected} expected, got {funnel_ta['E3']}"
    assert funnel_ta["E3"] == 60, f"E3=60 expected, got {funnel_ta['E3']}"

    # ========== Step 5: 4 studies ROB-2 — 3 low + 1 some → grade_ro_downgrade = -1 ==========
    rob_study_ids = [r.id for r in records[:4]]

    rob_studies_meta = [
        {"study_idx": 0, "overall": TL.LOW, "domains": [r(i, TL.LOW) for i in range(1, 6)]},
        {"study_idx": 1, "overall": TL.LOW, "domains": [r(i, TL.LOW) for i in range(1, 6)]},
        {"study_idx": 2, "overall": TL.LOW, "domains": [r(i, TL.LOW) for i in range(1, 6)]},
        {
            "study_idx": 3,
            "overall": TL.SOME,
            "domains": [
                r(1, TL.LOW),
                r(2, TL.SOME),
                r(3, TL.LOW),
                r(4, TL.LOW),
                r(5, TL.LOW),
            ],
        },
    ]

    rob_eas = []
    for meta in rob_studies_meta:
        rid = rob_study_ids[meta["study_idx"]]
        computed_overall = calc_rob2_overall(meta["domains"])
        assert computed_overall == meta["overall"]
        rob_eas.append(
            EA(
                literature_record_id=rid,
                stage="quality_ro",
                decision="include",
                confidence=0.88,
                exclude_reason_ids=None,
                meta_json={
                    "overall": computed_overall,
                    "domains": meta["domains"],
                },
                created_by=user.user_id,
            )
        )
    inserted_rob = bulk_upsert_evidence_artifacts(db_session, rob_eas)
    assert inserted_rob == 4, f"4 ROB-2 upserts expected, got {inserted_rob}"
    db_session.flush()

    rob_overalls = [TL.LOW, TL.LOW, TL.LOW, TL.SOME]
    downgrade = grade_ro_downgrade(rob_overalls)
    assert downgrade == -1, f"grade_ro_downgrade=-1 expected, got {downgrade}"

    # ========== Step 6: abstractor run 10 batch — 3 include / 5 review / 2 exclude (#3 Wrong Population) ==========
    abstractor_batch_ids = [r.id for r in records[40:50]]
    assert len(abstractor_batch_ids) == 10

    abs_include_ids = abstractor_batch_ids[:3]
    abs_review_ids = abstractor_batch_ids[3:8]
    abs_exclude_ids = abstractor_batch_ids[8:10]

    abs_eas = []
    for rid in abs_include_ids:
        abs_eas.append(
            EA(
                literature_record_id=rid,
                stage="screening_fulltext",
                decision="include",
                confidence=0.91,
                exclude_reason_ids=None,
                meta_json={
                    "pico": {"p": "T2DM adults", "i": "GLP-1 RA", "c": "Insulin", "o": "HbA1c"},
                    "reasons": ["All PICO criteria met", "RCT confirmed"],
                },
                created_by=user.user_id,
            )
        )

    for rid in abs_review_ids:
        abs_eas.append(
            EA(
                literature_record_id=rid,
                stage="screening_fulltext",
                decision="review",
                confidence=0.55,
                exclude_reason_ids=None,
                meta_json={
                    "reasons": ["Need full-text review for population confirmation"],
                    "pipeline_steps": ["pico_extracted", "needs_human_review"],
                },
                created_by=user.user_id,
            )
        )

    for rid in abs_exclude_ids:
        abs_eas.append(
            EA(
                literature_record_id=rid,
                stage="screening_fulltext",
                decision="exclude",
                confidence=0.78,
                exclude_reason_ids=[3],
                meta_json={
                    "preset_class": 3,
                    "note": "Wrong Population — includes T1DM patients, not pure T2DM",
                    "reasons": ["Population mismatch: T1DM subjects present >10%"],
                },
                created_by=user.user_id,
            )
        )

    inserted_abs = bulk_upsert_evidence_artifacts(db_session, abs_eas)
    assert inserted_abs == 10, f"10 Abstractor upserts expected, got {inserted_abs}"
    db_session.flush()

    abs_include_count = query_evidence_artifact_count(
        db_session, stage="screening_fulltext", decision="include", project_id=project.id
    )
    abs_review_count = query_evidence_artifact_count(
        db_session, stage="screening_fulltext", decision="review", project_id=project.id
    )
    abs_exclude_count = query_evidence_artifact_count(
        db_session, stage="screening_fulltext", decision="exclude", project_id=project.id
    )
    assert abs_include_count == 3, f"Abstractor include=3 expected, got {abs_include_count}"
    assert abs_review_count == 5, f"Abstractor review=5 expected, got {abs_review_count}"
    assert abs_exclude_count == 2, f"Abstractor exclude=2 expected, got {abs_exclude_count}"

    # ========== Step 7: evidence_artifact WHERE decision='include' count = 33 ==========
    ea_include_total = db_session.exec(
        select(func.count(EA.id)).select_from(EA).join(
            LiteratureRecord, EA.literature_record_id == LiteratureRecord.id
        ).where(
            and_(
                LiteratureRecord.project_id == project.id,
                EA.decision == "include",
            )
        )
    ).one()

    expected_total = 30 + 3
    assert ea_include_total == expected_total, (
        f"evidence_artifact include count = {expected_total} (30 TA + 3 9c) expected, "
        f"got {ea_include_total}"
    )

    db_session.commit()
    assert True
