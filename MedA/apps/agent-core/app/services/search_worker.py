from __future__ import annotations

import asyncio
import os
from datetime import datetime, timedelta
from typing import Iterable

from sqlmodel import Session, select

from app.models import (
    LiteratureRecord,
    SearchRun,
    SearchRunSource,
)
from app.services.literature import (
    _normalize_identifiers,
    import_unified_entries,
)
from app.services.sources import get_source_adapter
from app.services.sources.protocol import (
    NormalizedSearchQuery,
    SearchRunContext,
    UnifiedLiteratureEntry,
)
from app.services.bm25_scoring import recompute_bm25_for_search_run


STALE_SOURCE_TIMEOUT_MINUTES = 30
PARALLEL_SOURCES_PER_RUN = 3


# ---------------------------------------------------------------- lifecycle hooks

_worker_stop_event: asyncio.Event | None = None
_worker_task: asyncio.Task | None = None


async def start_worker_loop(get_session_factory, poll_seconds: float = 1.0) -> None:
    """Called from main.py startup event. Runs until stop event is set."""
    global _worker_stop_event, _worker_task
    _worker_stop_event = asyncio.Event()

    async def _loop():
        while not _worker_stop_event.is_set():
            try:
                session_factory = get_session_factory()
                with session_factory() as sess:
                    await _reset_timed_out_running_sources(sess)
                    await _worker_tick_once(sess)
                    sess.commit()
            except Exception as exc:  # noqa: BLE001 - worker never crashes the server
                # TODO(in production): attach sentry/logger
                print(f"[search_worker] tick error: {exc!r}")
            finally:
                await asyncio.sleep(poll_seconds)

    _worker_task = asyncio.create_task(_loop())


async def stop_worker_loop(wait_timeout: float = 2.0) -> None:
    """Called from main.py shutdown event."""
    global _worker_stop_event
    if _worker_stop_event is None:
        return
    _worker_stop_event.set()
    if _worker_task is not None and not _worker_task.done():
        try:
            await asyncio.wait_for(_worker_task, timeout=wait_timeout)
        except (TimeoutError, asyncio.TimeoutError):
            _worker_task.cancel()
            try:
                await _worker_task
            except asyncio.CancelledError:
                pass


# ------------------------------------------------------------- public helpers

async def _reset_timed_out_running_sources(
    session: Session, *, max_age_minutes: int = STALE_SOURCE_TIMEOUT_MINUTES
) -> int:
    """Mark any SearchRunSource stuck in running for too long as failed."""
    cutoff = datetime.utcnow() - timedelta(minutes=max_age_minutes)
    stales = session.exec(
        select(SearchRunSource).where(
            SearchRunSource.status == "running",
            SearchRunSource.started_at < cutoff,
        )
    ).all()
    for s in stales:
        s.status = "failed"
        s.error_message = (s.error_message or "") + " [timeout reset at startup]"
        s.finished_at = datetime.utcnow()
    session.add_all(stales)
    return len(stales)


# ---------------------------------------------------------------- state machine

async def _worker_tick_once(session: Session) -> None:
    # ① claim pending → running: up to PARALLEL_SOURCES_PER_RUN sources that aren't running yet
    claimed: list[SearchRunSource] = _claim_pending_sources(session, PARALLEL_SOURCES_PER_RUN)
    for srs in claimed:
        srs.status = "running"
        srs.started_at = datetime.utcnow()
    session.add_all(claimed)
    session.flush()

    # ② execute those claimed
    for srs in claimed:
        await _execute_single_source(session, srs)
    session.flush()

    # ③ Aggregate per-run counts, update status, recompute BM25 when run done
    _update_runs_status_and_counts(session)


def _claim_pending_sources(session: Session, k: int) -> list[SearchRunSource]:
    # 只从「未取消、未完成、非失败父运行」中拿 pending
    subq = (
        select(SearchRun.id)
        .where(SearchRun.status.in_(["pending", "running", "partial_failed"]))
        .subquery()
    )
    q = (
        select(SearchRunSource)
        .where(
            SearchRunSource.status == "pending",
            SearchRunSource.search_run_id.in_(subq),
        )
        .order_by(SearchRunSource.id.asc())
        .limit(k)
    )
    return list(session.exec(q).all())


async def _execute_single_source(session: Session, srs: SearchRunSource) -> None:
    try:
        run = session.get(SearchRun, srs.search_run_id)
        assert run is not None
        adapter = get_source_adapter(srs.source_key)
        query = NormalizedSearchQuery(
            boolean_text=_extract_bool_from_snapshot(run.query_snapshot),
            filters=_extract_filters_from_snapshot(run.query_snapshot),
            source_key=srs.source_key,
        )
        default_rates = {"pubmed": 3.0, "cnki": 0.3, "wanfang": 0.3}
        cfg = getattr(run, "search_source_config_json", None) or {}
        if isinstance(cfg, dict):
            default_rates.update(cfg.get("rate_limit_rps") or {})
        ctx = SearchRunContext(
            project_id=run.project_id,
            search_run_id=run.id,
            rate_limit_rps=default_rates,
            pubmed_api_key=os.getenv("PUBMED_API_KEY"),
            adapter_modes={},
        )
        result = await adapter.run_search(query, ctx)
        # 写入：去重、规范化、import_unified_entries（Task 5 定义）
        normalized_records = [
            UnifiedLiteratureEntry(
                doi=_normalize_identifiers(r.doi, "", "")[0],
                pmid=_normalize_identifiers("", r.pmid, "")[1],
                title=r.title.strip(),
                authors=r.authors,
                journal=r.journal,
                year=r.year,
                abstract=r.abstract,
                source_key=r.source_key,
                source_record_id=r.source_record_id,
            ) for r in result.records
        ]
        imported = import_unified_entries(
            session,
            run.project_id,
            source_key=srs.source_key,
            entries=normalized_records,
            search_run_id=run.id,
            search_run_source_id=srs.id,
        )

        srs.status = "completed"
        srs.hits_on_source = result.hits_on_source
        srs.records_retrieved = len(result.records)
        srs.records_imported = imported.count
        if imported.skipped_count > 0:
            srs.error_message = (
                f"skipped {imported.skipped_count} malformed entries"
            )
    except Exception as exc:  # noqa: BLE001
        srs.status = "failed"
        srs.error_message = (
            (srs.error_message or "") +
            f" worker exception: {exc.__class__.__name__}: {exc!s}"
        )[:400]
    finally:
        srs.finished_at = datetime.utcnow()
        session.add(srs)


def _update_runs_status_and_counts(session: Session) -> None:
    run_ids = {
        s.search_run_id
        for s in session.exec(
            select(SearchRunSource).where(
                SearchRunSource.status.in_(["completed", "failed"])
            )
        ).all()
    }
    # Also include runs that have non-pending sources
    for run in session.exec(
        select(SearchRun).where(SearchRun.id.in_(list(run_ids) or [-1]))
    ).all():
        sources = session.exec(
            select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
        ).all()
        if not sources:
            continue

        total_raw = sum(s.records_retrieved for s in sources if s.status == "completed")
        dedupe_q = (
            select(LiteratureRecord.id)
            .where(LiteratureRecord.search_run_id == run.id)
            .where(LiteratureRecord.dedupe_status != "duplicate")
        )
        total_dedupe = len(session.exec(dedupe_q).all())

        run.total_hits_raw = total_raw
        run.total_after_dedupe = total_dedupe

        statuses = {s.status for s in sources}
        all_done = statuses <= {"completed", "failed"}
        if not all_done:
            run.status = "running" if "running" in statuses or run.status == "running" else run.status
            session.add(run)
            continue

        success_count = sum(1 for s in sources if s.status == "completed")
        total_sources = len(sources)
        if success_count == total_sources:
            run.status = "completed"
        elif success_count == 0:
            run.status = "failed"
        else:
            run.status = "partial_failed"
        run.finished_at = datetime.utcnow()
        session.add(run)

        # Once fully finished (any success), compute BM25 once
        if run.total_after_dedupe > 0 and run.status != "failed":
            try:
                recompute_bm25_for_search_run(session, run.id)
            except Exception:  # noqa: BLE001
                # BM25 is non-fatal: records still exist without score
                pass


def _extract_bool_from_snapshot(snapshot: str) -> str:
    import json
    try:
        obj = json.loads(snapshot)
    except Exception:
        return ""
    return obj.get("boolean_text") or obj.get("boolean") or ""


def _extract_filters_from_snapshot(snapshot: str) -> dict[str, list[str]]:
    import json
    try:
        obj = json.loads(snapshot)
    except Exception:
        return {}
    return obj.get("filters") or {}
