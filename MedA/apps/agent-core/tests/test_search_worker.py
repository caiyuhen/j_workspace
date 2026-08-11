from __future__ import annotations
import asyncio
from datetime import datetime, timedelta

from sqlmodel import Session, select

from app.models import SearchRun, SearchRunSource
from app.services.search_worker import (
    _reset_timed_out_running_sources,
    _worker_tick_once,
)
from tests.conftest import (
    SOURCE_DATASET_REGISTRY,
    create_test_project,
    create_test_user,
    inject_mock_datasets_into_adapters,
)


def test_worker_completes_3_sources_sets_search_run_completed(
    db_session: Session, monkeypatch
) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    # Inject mocks
    inject_mock_datasets_into_adapters(monkeypatch, SOURCE_DATASET_REGISTRY)

    run = SearchRun(
        project_id=project.id,
        query_snapshot="{}",
        selected_sources="pubmed,cnki,wanfang",
        status="pending",
    )
    db_session.add(run)
    db_session.flush()
    for s in ["pubmed", "cnki", "wanfang"]:
        db_session.add(SearchRunSource(
            search_run_id=run.id, source_key=s, status="pending",
        ))
    db_session.commit()
    db_session.refresh(run)

    # Run 2 ticks (pending→running; running→completed)
    asyncio.run(_worker_tick_once(db_session))
    asyncio.run(_worker_tick_once(db_session))

    db_session.refresh(run)
    # 所有 sources 已完成 → run.status = completed
    assert run.status == "completed"
    # 命中数聚合：mock 3 + 2 + 1 = 6 retrieved
    sources = db_session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all()
    retrieved = sum(s.records_retrieved for s in sources)
    assert retrieved >= 6
    assert run.total_hits_raw >= 6
    assert run.total_after_dedupe >= 1  # Wave 7 dedupe 会干掉 DOI/标题重复


def test_one_source_failed_marks_run_partial_failed(db_session: Session, monkeypatch) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    # 只 inject pubmed，其余两条空 stub 会报错（被我们用 monkeypatch 改成抛异常）
    inject_mock_datasets_into_adapters(monkeypatch, {"pubmed": SOURCE_DATASET_REGISTRY["pubmed"]})

    async def bad_run(*_a, **_k):
        raise RuntimeError("simulated CNKI failure")
    monkeypatch.setattr(
        "app.services.sources.cnki_adapter.CnkiAdapter.run_search", bad_run
    )

    run = SearchRun(
        project_id=project.id,
        query_snapshot="{}",
        selected_sources="pubmed,cnki,wanfang",
        status="pending",
    )
    db_session.add(run)
    db_session.flush()
    for s in ["pubmed", "cnki", "wanfang"]:
        db_session.add(SearchRunSource(
            search_run_id=run.id, source_key=s, status="pending",
        ))
    db_session.commit()

    # 3 ticks 保证 bad_run 的 failure 被写入 error_message
    for _ in range(3):
        asyncio.run(_worker_tick_once(db_session))

    db_session.refresh(run)
    # partial_failed：至少 1 completed，至少 1 failed
    assert run.status == "partial_failed"
    sources = db_session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all()
    statuses = {s.source_key: s.status for s in sources}
    assert statuses.get("pubmed") in {"completed", "running"}
    assert statuses.get("cnki") == "failed"
    assert any(s.error_message for s in sources if s.source_key == "cnki")


def test_reset_timed_out_running_sources_marks_as_failed(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    run = SearchRun(
        project_id=project.id, query_snapshot="{}", selected_sources="pubmed",
        status="running",
    )
    db_session.add(run)
    db_session.flush()
    too_old = datetime.utcnow() - timedelta(minutes=31)
    db_session.add(SearchRunSource(
        search_run_id=run.id,
        source_key="pubmed",
        status="running",
        started_at=too_old,
    ))
    db_session.commit()

    updated = asyncio.run(_reset_timed_out_running_sources(db_session, max_age_minutes=30))
    assert updated == 1

    src = db_session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).one()
    assert src.status == "failed"
    assert "timeout" in (src.error_message or "").lower()
