from __future__ import annotations

import csv
import io
import json
from datetime import datetime
from typing import Literal

from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import LiteratureRecord, ResearchProject, SearchRun, SearchRunSource, SearchQueryVersion


class SearchRunError(Exception):
    def __init__(
        self,
        message: str,
        code: Literal[
            "no_sources_selected",
            "nothing_to_retry",
            "already_finished",
            "adapter_not_registered",
            "rate_limit_exceeded",
        ],
    ) -> None:
        super().__init__(message)
        self.code = code


VALID_SOURCES = {"pubmed", "cnki", "wanfang"}


def create_search_run(
    session: Session,
    project_id: int,
    *,
    sources: list[str],
    query_snapshot: dict | None,
    search_query_version_id: int | None,
) -> SearchRun:
    _ensure_project(session, project_id)

    if not sources:
        raise SearchRunError("no_sources_selected", "no_sources_selected")
    unknown = [s for s in sources if s not in VALID_SOURCES]
    if unknown:
        raise SearchRunError(f"adapter_not_registered: {unknown}", "adapter_not_registered")

    if query_snapshot is None and search_query_version_id is None:
        raise SearchRunError(
            "must provide either query_snapshot or search_query_version_id",
            "no_sources_selected",
        )
    snap_dict = dict(query_snapshot) if query_snapshot is not None else {}
    if search_query_version_id is not None and not snap_dict:
        snap_dict = _load_snapshot_from_search_version(session, search_query_version_id)

    run = SearchRun(
        project_id=project_id,
        search_query_version_id=search_query_version_id,
        query_snapshot=json.dumps(snap_dict, ensure_ascii=False),
        selected_sources=",".join(sorted(set(sources))),
        status="pending",
    )
    session.add(run)
    session.flush()

    for s in sources:
        session.add(SearchRunSource(
            search_run_id=run.id,
            source_key=s,
            status="pending",
        ))
    session.commit()
    session.refresh(run)
    return run


def get_search_run_list(
    session: Session,
    project_id: int,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[SearchRun], int]:
    _ensure_project(session, project_id)
    total_q = select(SearchRun).where(SearchRun.project_id == project_id)
    total = len(session.exec(total_q).all())
    q = (
        total_q.order_by(SearchRun.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(session.exec(q).all()), total


def get_search_run_detail(
    session: Session, project_id: int, run_id: int
) -> tuple[SearchRun, list[SearchRunSource]]:
    _ensure_project(session, project_id)
    run = session.get(SearchRun, run_id)
    if run is None or run.project_id != project_id:
        raise HTTPException(status_code=404, detail="search_run not found")
    sources = list(session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all())
    return run, sources


def cancel_search_run(session: Session, run_id: int) -> None:
    run = session.get(SearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="search_run not found")
    if run.status in {"completed", "failed", "cancelled"}:
        raise SearchRunError("already_finished", "already_finished")
    run.status = "cancelled"
    run.finished_at = datetime.utcnow()
    for s in session.exec(
        select(SearchRunSource).where(
            SearchRunSource.search_run_id == run.id,
            SearchRunSource.status.in_(["pending", "running"]),
        )
    ).all():
        s.status = "failed"
        s.error_message = (s.error_message or "") + " [cancelled by user]"
        s.finished_at = datetime.utcnow()
        session.add(s)
    session.add(run)
    session.commit()


def retry_failed_sources(session: Session, run_id: int) -> list[str]:
    run = session.get(SearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="search_run not found")
    if run.status not in {"partial_failed", "failed"}:
        raise SearchRunError("nothing_to_retry", "nothing_to_retry")
    restarted: list[str] = []
    for s in session.exec(
        select(SearchRunSource).where(
            SearchRunSource.search_run_id == run.id,
            SearchRunSource.status == "failed",
        )
    ).all():
        s.status = "pending"
        s.started_at = None
        s.finished_at = None
        s.error_message = None
        s.records_retrieved = 0
        s.records_imported = 0
        s.hits_on_source = None
        session.add(s)
        restarted.append(s.source_key)
    if not restarted:
        raise SearchRunError("nothing_to_retry", "nothing_to_retry")
    run.status = "running"
    run.finished_at = None
    run.error_message = None
    session.add(run)
    session.commit()
    return restarted


def export_search_run_csv_text(session: Session, run_id: int) -> str:
    run = session.get(SearchRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="search_run not found")
    sources = list(session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all())
    records = list(session.exec(
        select(LiteratureRecord)
        .where(LiteratureRecord.search_run_id == run.id)
        .order_by((LiteratureRecord.relevance_score or 0).desc())
    ).all())

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["project_id", run.project_id])
    w.writerow(["search_run_id", run.id])
    w.writerow(["created_at", run.created_at.isoformat() if run.created_at else ""])
    w.writerow([])
    w.writerow(["PRISMA"])
    w.writerow(["Identification", "Screening", "Eligibility", "Included"])
    w.writerow([run.total_hits_raw, run.total_after_dedupe, run.total_after_dedupe, run.total_after_dedupe])
    w.writerow([])
    w.writerow(["Per source"])
    w.writerow(["source_key", "status", "retrieved", "imported", "hits_on_source", "error_message"])
    for s in sources:
        w.writerow([s.source_key, s.status, s.records_retrieved, s.records_imported, s.hits_on_source, s.error_message or ""])
    w.writerow([])
    w.writerow(["Records (after dedupe)"])
    w.writerow([
        "id","score","title","authors","journal","year","doi","pmid",
        "source_key","dedupe_status","pico_status",
    ])
    for r in records:
        w.writerow([
            r.id,
            f"{r.relevance_score:.4f}" if r.relevance_score is not None else "",
            r.title, r.authors, r.journal, r.year or "", r.doi, r.pmid,
            r.source_key, r.dedupe_status, r.pico_status,
        ])
    return buf.getvalue()


def _ensure_project(session: Session, project_id: int) -> None:
    p = session.get(ResearchProject, project_id)
    if p is None:
        raise HTTPException(status_code=404, detail="project not found")


def _load_snapshot_from_search_version(session: Session, version_id: int) -> dict:
    v = session.get(SearchQueryVersion, version_id)
    if v is None:
        raise HTTPException(status_code=404, detail="search_query_version not found")
    out = {
        "boolean_text": v.boolean_text or "" if hasattr(v, 'boolean_text') else "",
        "p": v.p or "" if hasattr(v, 'p') else "",
        "i": v.i or "" if hasattr(v, 'i') else "",
        "c": v.c or "" if hasattr(v, 'c') else "",
        "o": v.o or "" if hasattr(v, 'o') else "",
    }
    try:
        extra = json.loads(v.meta_json or "{}") if hasattr(v, 'meta_json') else {}
    except Exception:
        extra = {}
    out["filters"] = extra.get("filters") or {}
    return out
