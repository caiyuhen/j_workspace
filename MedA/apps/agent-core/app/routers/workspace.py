from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from sqlmodel import Session, select

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.models import ResearchProject, SearchRunSource
from app.schemas import (
    CreateLiteratureRecordRequest,
    DeriveSearchQueryDraftRequest,
    ImportLiteratureRequest,
    LiteratureLibraryResponse,
    SaveSearchQueryDraftRequest,
    SaveSearchSourceConfigRequest,
    SearchQueryEditorResponse,
    SearchRunCreatePayload,
    SearchRunDetail as _SDetail,
    SearchRunSourceSummary,
    SearchRunStatusPoll,
    SearchRunSummary,
    SearchSourceCatalogResponse,
    SearchSourceConfigResponse,
    StageEntryResponse,
    WorkspaceHomeResponse,
)
from app.services.literature import (
    LiteratureError,
    LiteratureNotFoundError,
    build_library_response,
    confirm_record_unique,
    create_literature_record,
    import_literature,
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
from app.services.search_query import (
    SearchQueryNotFoundError,
    derive_search_query_draft,
    get_or_create_search_query_editor,
    get_search_query_snapshot,
    save_search_query_draft,
    save_search_query_version,
)
from app.services.search_source import (
    SearchSourceConfigError,
    build_source_catalog,
    get_source_config,
    save_source_config,
)
from app.services.stage_entry import build_stage_entry
from app.services.workspace import build_workspace_home

router = APIRouter(prefix="/api/workspace", tags=["workspace"])


def _load_project_or_404(
    session: Session,
    project_id: int,
    context: SessionContext,
) -> ResearchProject:
    project = session.get(ResearchProject, project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    return project


@router.get("/projects/{project_id}/home", response_model=WorkspaceHomeResponse)
def get_workspace_home(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> WorkspaceHomeResponse:
    project = _load_project_or_404(session, project_id, context)

    return build_workspace_home(session, project)


@router.get("/projects/{project_id}/stages/{stage_key}", response_model=StageEntryResponse)
def get_stage_entry(
    project_id: int,
    stage_key: str,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> StageEntryResponse:
    project = _load_project_or_404(session, project_id, context)

    stage_entry = build_stage_entry(session, project, stage_key)
    if stage_entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="stage not found")

    return stage_entry


@router.get(
    "/projects/{project_id}/stages/search/query-builder",
    response_model=SearchQueryEditorResponse,
)
def get_search_query_editor(
    project_id: int,
    query_id: int | None = Query(default=None),
    version: str | None = Query(default=None),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        if version is not None:
            if query_id is None:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="query_id is required when version is provided",
                )
            return get_search_query_snapshot(session, project, query_id, version)

        return get_or_create_search_query_editor(session, project, query_id)
    except SearchQueryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.post(
    "/projects/{project_id}/stages/search/query-builder/save",
    response_model=SearchQueryEditorResponse,
)
def post_search_query_save(
    project_id: int,
    payload: SaveSearchQueryDraftRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        return save_search_query_draft(session, project, payload)
    except SearchQueryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.post(
    "/projects/{project_id}/stages/search/query-builder/save-as-version",
    response_model=SearchQueryEditorResponse,
)
def post_search_query_save_as_version(
    project_id: int,
    payload: SaveSearchQueryDraftRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        return save_search_query_version(session, project, payload)
    except SearchQueryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.post(
    "/projects/{project_id}/stages/search/query-builder/derive-draft",
    response_model=SearchQueryEditorResponse,
)
def post_search_query_derive_draft(
    project_id: int,
    payload: DeriveSearchQueryDraftRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchQueryEditorResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        return derive_search_query_draft(session, project, payload)
    except SearchQueryNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error


@router.get("/sources/catalog", response_model=SearchSourceCatalogResponse)
def get_search_source_catalog(
    context: SessionContext = Depends(get_current_session),
) -> SearchSourceCatalogResponse:
    return build_source_catalog()


@router.get(
    "/projects/{project_id}/stages/search/sources",
    response_model=SearchSourceConfigResponse,
)
def get_search_source_config(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchSourceConfigResponse:
    project = _load_project_or_404(session, project_id, context)

    return get_source_config(session, project)


@router.put(
    "/projects/{project_id}/stages/search/sources",
    response_model=SearchSourceConfigResponse,
)
def put_search_source_config(
    project_id: int,
    payload: SaveSearchSourceConfigRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> SearchSourceConfigResponse:
    project = _load_project_or_404(session, project_id, context)

    try:
        return save_source_config(session, project, payload)
    except SearchSourceConfigError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.get(
    "/projects/{project_id}/stages/search/literature",
    response_model=LiteratureLibraryResponse,
)
def get_literature_library(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    project = _load_project_or_404(session, project_id, context)

    return build_library_response(session, project)


@router.post(
    "/projects/{project_id}/stages/search/literature/import",
    response_model=LiteratureLibraryResponse,
)
def post_literature_import(
    project_id: int,
    payload: ImportLiteratureRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    try:
        project = _load_project_or_404(session, project_id, context)
        return import_literature(session, project, payload)
    except LiteratureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.post(
    "/projects/{project_id}/stages/search/literature/records",
    response_model=LiteratureLibraryResponse,
)
def post_literature_record(
    project_id: int,
    payload: CreateLiteratureRecordRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    try:
        project = _load_project_or_404(session, project_id, context)
        return create_literature_record(session, project, payload)
    except LiteratureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


@router.post(
    "/projects/{project_id}/stages/search/literature/records/{record_id}/confirm-unique",
    response_model=LiteratureLibraryResponse,
)
def post_literature_confirm_unique(
    project_id: int,
    record_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    try:
        project = _load_project_or_404(session, project_id, context)
        return confirm_record_unique(session, project, record_id)
    except LiteratureNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(error)
        ) from error
    except LiteratureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error


# ---------- Wave 8: S1~S7 search run endpoints ----------

_SOURCE_LABELS_ROUTE = {"pubmed": "PubMed", "cnki": "CNKI", "wanfang": "万方"}


def _prisma_for_run(session: Session, run):
    raw = run.total_hits_raw
    after = run.total_after_dedupe
    sources = list(session.exec(
        select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
    ).all())
    by_source = [
        {
            "source_key": s.source_key,
            "source_label": _SOURCE_LABELS_ROUTE.get(s.source_key, s.source_key),
            "records_retrieved": s.records_retrieved,
            "records_imported": s.records_imported,
        } for s in sources
    ]
    return {
        "identification": raw,
        "screening": after,
        "eligibility": after,
        "included": after,
        "by_source": by_source,
    }


def _fmt_iso(t):
    return t.isoformat() if t else None


def _map_search_run_summary(session: Session, run):
    eta = None
    if run.status == "running" and run.started_at:
        sources = list(session.exec(
            select(SearchRunSource).where(SearchRunSource.search_run_id == run.id)
        ).all())
        done = sum(1 for s in sources if s.status in {"completed", "failed"})
        remaining = len(sources) - done
        eta = remaining * 2.0
    return SearchRunSummary(
        id=run.id,
        project_id=run.project_id,
        search_query_version_id=run.search_query_version_id,
        selected_sources=[s for s in run.selected_sources.split(",") if s],
        status=run.status,
        created_at=_fmt_iso(run.created_at),
        started_at=_fmt_iso(run.started_at),
        finished_at=_fmt_iso(run.finished_at),
        total_hits_raw=run.total_hits_raw,
        total_after_dedupe=run.total_after_dedupe,
        prisma=_prisma_for_run(session, run),
        eta_seconds=eta,
    )


def _map_source_summary(s):
    return SearchRunSourceSummary(
        id=s.id,
        search_run_id=s.search_run_id,
        source_key=s.source_key,
        source_label=_SOURCE_LABELS_ROUTE.get(s.source_key, s.source_key),
        status=s.status,
        hits_on_source=s.hits_on_source,
        records_retrieved=s.records_retrieved,
        records_imported=s.records_imported,
        started_at=_fmt_iso(s.started_at),
        finished_at=_fmt_iso(s.finished_at),
        error_message=s.error_message,
    )


@router.post(
    "/projects/{project_id}/stages/search/search-runs",
    status_code=status.HTTP_201_CREATED,
    response_model=SearchRunSummary,
)
def search_run_create(
    project_id: int,
    payload: SearchRunCreatePayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        run = create_search_run(
            session,
            project.id or project_id,
            sources=payload.sources,
            query_snapshot=payload.query_snapshot,
            search_query_version_id=payload.search_query_version_id,
        )
        return _map_search_run_summary(session, run)
    except SearchRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        ) from exc


@router.get(
    "/projects/{project_id}/stages/search/search-runs",
    response_model=dict,
)
def search_run_list(
    project_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        runs, total = get_search_run_list(
            session, project.id or project_id, page=page, page_size=page_size
        )
        return {
            "items": [_map_search_run_summary(session, r) for r in runs],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    except SearchRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        ) from exc


@router.get(
    "/projects/{project_id}/stages/search/search-runs/{run_id}",
    response_model=_SDetail,
)
def search_run_detail(
    project_id: int,
    run_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        run, sources = get_search_run_detail(
            session, project.id or project_id, run_id
        )
        return _SDetail(
            run=_map_search_run_summary(session, run),
            sources=[_map_source_summary(s) for s in sources],
        )
    except SearchRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        ) from exc


@router.post(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/cancel",
)
def search_run_cancel(
    project_id: int,
    run_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        cancel_search_run(session, run_id)
        return {"status": "cancelled"}
    except SearchRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        ) from exc


@router.post(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/retry",
)
def search_run_retry(
    project_id: int,
    run_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        restarted = retry_failed_sources(session, run_id)
        return {"restarted_sources": restarted}
    except SearchRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        ) from exc


@router.get(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/export.csv",
)
def search_run_export_csv(
    project_id: int,
    run_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        text = export_search_run_csv_text(session, run_id)
    except SearchRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        ) from exc
    import re
    safe_id = re.sub(r"[^A-Za-z0-9_-]+", "", f"search-run-{run_id}")
    date_str = datetime.utcnow().strftime("%Y%m%d")
    filename = f"{safe_id}-{date_str}.csv"
    return Response(
        content="\ufeff" + text,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/status",
    response_model=SearchRunStatusPoll,
)
def search_run_status_poll(
    project_id: int,
    run_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        run, sources = get_search_run_detail(
            session, project.id or project_id, run_id
        )
        total = len(sources)
        finished = sum(1 for s in sources if s.status in {"completed", "failed"})
        eta = None
        if total and finished < total and run.started_at is not None:
            elapsed = (datetime.utcnow() - run.started_at).total_seconds()
            per_item = elapsed / finished if finished > 0 else 0
            eta = max(0.0, per_item * (total - finished))
        return SearchRunStatusPoll(
            status=run.status,
            finished_sources=finished,
            total_sources=total,
            eta_seconds=eta,
        )
    except SearchRunError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.args[0],
        ) from exc
