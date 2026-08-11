from datetime import datetime
from sqlmodel import SQLModel, Session, select

from app.models import (
    LiteratureImportBatch,
    LiteraturePico,
    LiteratureRecord,
    ResearchProject,
    SearchRun,
    SearchRunSource,
    User,
)
from tests.conftest import create_test_project, create_test_user


def _statuses_ok(value, allowed) -> bool:
    return value in allowed


def test_search_run_literal_status_and_nullable_fields(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id,
        search_query_version_id=None,
        query_snapshot='{"p":"T2DM","i":"met","boolean":"Metformin[Mesh]"}',
        selected_sources="pubmed,cnki",
        status="pending",
        total_hits_raw=0,
        total_after_dedupe=0,
    )
    db_session.add(run)
    db_session.commit()
    db_session.refresh(run)

    assert _statuses_ok(
        run.status,
        {"pending","running","completed","partial_failed","failed","cancelled"},
    )
    assert isinstance(run.created_at, datetime)
    assert run.search_query_version_id is None
    assert run.id is not None


def test_search_run_source_links_back_to_run(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id,
        query_snapshot="{}",
        selected_sources="pubmed",
        status="pending",
    )
    db_session.add(run)
    db_session.flush()

    src = SearchRunSource(
        search_run_id=run.id,
        source_key="pubmed",
        status="pending",
        records_retrieved=0,
        records_imported=0,
    )
    db_session.add(src)
    db_session.commit()
    db_session.refresh(src)

    assert src.search_run_id == run.id
    assert src.error_message is None
    assert _statuses_ok(src.status, {"pending","running","completed","failed"})


def test_literature_pico_one_to_one_with_record(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    rec = LiteratureRecord(
        project_id=project.id,
        title="A RCT on SGLT2i",
        authors="",
        journal="NEJM",
        year=2024,
        doi="",
        pmid="",
        abstract="",
        source_key="pubmed",
        dedupe_status="unique",
    )
    db_session.add(rec)
    db_session.flush()

    pico = LiteraturePico(
        record_id=rec.id,
        population="成人 T2DM",
        intervention="SGLT2 抑制剂",
        comparison="安慰剂",
        outcome="3P-MACE 发生率",
        study_type="rct",
        extraction_method="rule_baseline",
        confidence=0.72,
    )
    db_session.add(pico)
    db_session.commit()
    db_session.refresh(pico)

    loaded = db_session.exec(
        select(LiteraturePico).where(LiteraturePico.record_id == rec.id)
    ).one()
    assert loaded.study_type == "rct"
    assert loaded.record_id == rec.id


def test_extended_columns_on_record_and_batch(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id,
        query_snapshot="{}",
        selected_sources="pubmed",
        status="completed",
    )
    db_session.add(run)
    db_session.flush()

    srs = SearchRunSource(
        search_run_id=run.id,
        source_key="pubmed",
        status="completed",
        records_retrieved=1,
        records_imported=1,
    )
    db_session.add(srs)
    db_session.flush()

    batch = LiteratureImportBatch(
        project_id=project.id,
        source_key="pubmed",
        parsed_count=1,
        duplicate_count=0,
        skipped_count=0,
        search_run_source_id=srs.id,
    )
    db_session.add(batch)
    db_session.flush()

    rec = LiteratureRecord(
        project_id=project.id,
        title="SGLT2i vs placebo in CKD",
        authors="Neuen BL",
        journal="NEJM",
        year=2023,
        doi="10.1056/nejmoa2212939",
        pmid="",
        source_key="pubmed",
        source_label="PubMed",
        dedupe_status="unique",
        import_batch_id=batch.id,
        search_run_id=run.id,
        relevance_score=2.17,
        pico_status="not_extracted",
    )
    db_session.add(rec)
    db_session.commit()
    db_session.refresh(rec)

    assert rec.search_run_id == run.id
    assert rec.relevance_score == 2.17
    assert rec.pico_status == "not_extracted"
    assert batch.search_run_source_id == srs.id
