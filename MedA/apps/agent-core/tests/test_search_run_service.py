from __future__ import annotations
from datetime import datetime

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import (
    LiteratureRecord,
    ResearchProject,
    SearchRun,
    SearchRunSource,
    SearchQueryVersion,
)
from app.services.search_run import (
    SearchRunError,
    cancel_search_run,
    create_search_run,
    export_search_run_csv_text,
    get_search_run_detail,
    get_search_run_list,
    retry_failed_sources,
)
from tests.conftest import create_test_project, create_test_user


def test_create_rejects_no_sources(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    try:
        create_search_run(db_session, project.id, sources=[], query_snapshot=None, search_query_version_id=None)
    except SearchRunError as exc:
        assert exc.code == "no_sources_selected"
        return
    raise AssertionError("expected SearchRunError no_sources_selected")


def test_create_rejects_both_snapshot_and_version_empty(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    try:
        create_search_run(
            db_session, project.id, sources=["pubmed"],
            query_snapshot=None, search_query_version_id=None,
        )
    except SearchRunError:
        return
    raise AssertionError("expected SearchRunError when both snapshot and version are null")


def test_cancel_sets_status_cancelled_for_pending_or_running(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    run = create_search_run(
        db_session, project.id,
        sources=["pubmed","cnki"],
        query_snapshot={"boolean_text":"Dapagliflozin","filters":{}},
        search_query_version_id=None,
    )
    src_pub = SearchRunSource(search_run_id=run.id, source_key="pubmed", status="pending")
    src_cnk = SearchRunSource(search_run_id=run.id, source_key="cnki", status="running", started_at=datetime.utcnow())
    db_session.add_all([src_pub, src_cnk])
    db_session.commit()
    cancel_search_run(db_session, run.id)
    db_session.refresh(run)
    assert run.status == "cancelled"
    for s in db_session.exec(select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)).all():
        assert s.status == "failed"
        assert "cancelled" in (s.error_message or "").lower()


def test_retry_failed_sources_only_retries_failed_or_partial(
    db_session: Session,
) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id, query_snapshot="{}",
        selected_sources="pubmed,cnki", status="partial_failed",
    )
    db_session.add(run)
    db_session.flush()
    ok = SearchRunSource(search_run_id=run.id, source_key="pubmed", status="completed", records_retrieved=3, records_imported=3)
    bad = SearchRunSource(search_run_id=run.id, source_key="cnki", status="failed", error_message="x")
    db_session.add_all([ok, bad])
    db_session.commit()
    restarted = retry_failed_sources(db_session, run.id)
    assert set(restarted) == {"cnki"}
    db_session.refresh(bad)
    assert bad.status == "pending"
    assert bad.error_message is None
    db_session.refresh(run)
    assert run.status == "running"


def test_export_csv_contains_expected_headers_and_counts(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id, query_snapshot="{}", selected_sources="pubmed",
        status="completed", total_hits_raw=5, total_after_dedupe=3,
    )
    db_session.add(run)
    db_session.flush()
    srs = SearchRunSource(
        search_run_id=run.id, source_key="pubmed", status="completed",
        records_retrieved=5, records_imported=3,
    )
    db_session.add(srs)
    db_session.flush()
    rec1 = LiteratureRecord(
        project_id=project.id, title="Paper A", authors="", journal="J",
        year=2024, doi="10.1/a", pmid="", source_key="pubmed",
        source_label="PubMed", dedupe_status="unique",
        search_run_id=run.id, relevance_score=1.2, pico_status="not_extracted",
    )
    rec2 = LiteratureRecord(
        project_id=project.id, title="Paper B", authors="", journal="J",
        year=2023, doi="10.1/b", pmid="", source_key="pubmed",
        source_label="PubMed", dedupe_status="unique",
        search_run_id=run.id, relevance_score=0.8, pico_status="not_extracted",
    )
    db_session.add_all([rec1, rec2])
    db_session.commit()
    db_session.refresh(run)

    text = export_search_run_csv_text(db_session, run.id)
    assert "Identification,Screening,Eligibility,Included" in text
    assert "Paper A" in text
    assert "10.1/a" in text
    assert "Paper B" in text
    assert "10.1/b" in text
