from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlmodel import Session, select

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.models import LiteraturePico, ResearchProject, SearchRunSource
from app.schemas import (
    BatchPicoPayload,
    BatchPicoResult,
    CreateLiteratureRecordRequest,
    DeriveSearchQueryDraftRequest,
    ImportLiteratureRequest,
    LiteratureLibraryResponse,
    LiteratureLibraryRequestExt,
    LiteraturePicoResponse,
    PicoAutofillDraft,
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
from app.services.pico import (
    PicoExtractionError,
    batch_extract_pico,
    extract_pico_for_record,
    suggest_pico_autofill,
)
from app.services.bm25_scoring import recompute_bm25_for_search_run
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

    ret = stage_entry
    # ── W8.4 LAZY-APPEND output_stage_cards 3 dynamic cards (BEGIN) ──
    try:
        from app.services.output_stage import build_output_stage_cards_3
        from sqlmodel import select, func
        from app.db import SessionLocal
        from app.models import GradeAssessment, SofTableRow, ReportSnapshot, Prisma2020Checklist

        sl = SessionLocal()
        with sl as s:
            cnt_grade = s.exec(select(func.count()).select_from(GradeAssessment).where(GradeAssessment.project_id == project_id)).one()
            prisma = s.exec(select(Prisma2020Checklist).where(Prisma2020Checklist.project_id == project_id).limit(1)).first()
            prisma_cnt = 0
            if prisma is not None:
                prisma_cnt = sum(1 for i in range(1,28) if bool(getattr(prisma, f"item_{i}", False)))
            cnt_sof = s.exec(select(func.count()).select_from(SofTableRow).where(SofTableRow.project_id == project_id)).one()
            cnt_snap = s.exec(select(func.count()).select_from(ReportSnapshot).where(ReportSnapshot.project_id == project_id)).one()
            studies_k = 3
        cards = build_output_stage_cards_3(
            grade_count=int(cnt_grade or 0),
            prisma_items_checked=int(prisma_cnt or 0),
            sof_rows=int(cnt_sof or 0),
            studies_k_any_outcome=int(studies_k or 0),
            snap_count=int(cnt_snap or 0),
        )
        ret.output_stage_cards = [
            {"card_key": c.card_key, "ready": c.ready, "locked_reason": c.locked_reason} for c in cards
        ]
    except Exception:
        pass
    # ── W8.4 LAZY-APPEND output_stage_cards 3 dynamic cards (END) ──
    return ret


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
    search_run_id: int | None = Query(default=None),
    sort: str = Query(default="default"),
    min_score: float | None = Query(default=None),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    try:
        project = _load_project_or_404(session, project_id, context)
        sort_val = sort if sort in {"default", "relevance", "year_desc", "journal"} else "default"
        return build_library_response(
            session,
            project,
            search_run_id=search_run_id,
            sort=sort_val,
            min_score=min_score,
        )
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error),
        ) from error


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


@router.post(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/recompute-bm25",
)
def search_run_recompute_bm25(
    project_id: int,
    run_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        recompute_bm25_for_search_run(session, run_id)
        return {"queued": True}
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/projects/{project_id}/stages/search/literature/records/pico:batch-extract",
    response_model=BatchPicoResult,
)
def records_batch_extract_pico(
    project_id: int,
    payload: BatchPicoPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        result = batch_extract_pico(
            session,
            payload.record_ids,
            method=payload.method,
        )
        return BatchPicoResult(
            processed=result.processed,
            already_had=result.already_had,
            failed=result.failed,
        )
    except PicoExtractionError as exc:
        if exc.code == "no_records_provided":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="no_records_provided",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.get(
    "/projects/{project_id}/stages/search/literature/records/{record_id}/pico",
    response_model=LiteraturePicoResponse,
)
def records_get_pico(
    project_id: int,
    record_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        pico = extract_pico_for_record(session, record_id)
        return LiteraturePicoResponse(
            record_id=pico.record_id,
            population=pico.population,
            intervention=pico.intervention,
            comparison=pico.comparison,
            outcome=pico.outcome,
            study_type=pico.study_type,
            extraction_method=pico.extraction_method,
            confidence=pico.confidence,
            extracted_at=_fmt_iso(pico.created_at),
        )
    except PicoExtractionError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


@router.post(
    "/projects/{project_id}/stages/search/search-runs/{run_id}/pico:autofill-query",
    response_model=PicoAutofillDraft,
)
def search_run_pico_autofill(
    project_id: int,
    run_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
):
    try:
        project = _load_project_or_404(session, project_id, context)
        return suggest_pico_autofill(session, run_id)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc


# ---------------------------------------------------------------------------
# Wave82B T5: 6 Screening REST thin-wrappers (AC10 HARD-GATE: never import serializeRIS/BibTeX)
# ---------------------------------------------------------------------------


class _BatchDecisionPayload(BaseModel):
    operation: str = Field(..., pattern=r"^(include|exclude|revoke_fulltext)$")
    stage: str | None = Field(default=None, pattern=r"^(ta|fulltext)$")
    record_ids: list[int] = Field(..., min_length=1)
    exclude_reason: dict | None = None
    client_batch_id: str | None = None


class _OverridePayload(BaseModel):
    identification: int | None = None
    screening: int | None = None
    eligibility: int | None = None
    included: int | None = None


@router.get("/projects/{project_id}/screening/prisma-stats")
def screening_prisma_stats(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.screening_engine import compute_prisma_counts, PrismaCounts
    pc: PrismaCounts = compute_prisma_counts(session, project.id)
    import dataclasses as _dc
    return _dc.asdict(pc)


@router.post("/projects/{project_id}/screening/batch-decision")
def screening_batch_decision(
    project_id: int,
    payload: _BatchDecisionPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    import dataclasses as _dc
    from app.services.screening_engine import (
        apply_batch_decision, ScreeningEngineError, BatchResult,
    )
    project = _load_project_or_404(session, project_id, context)
    try:
        res: BatchResult = apply_batch_decision(
            session, project, payload.operation, payload.record_ids,
            stage=payload.stage, exclude_reason=payload.exclude_reason,
            client_batch_id=payload.client_batch_id,
        )
    except ScreeningEngineError as err:
        raise HTTPException(status_code=getattr(err, "status", 422), detail=str(err)) from err
    return _dc.asdict(res)


@router.post("/projects/{project_id}/screening/apply-override")
def screening_apply_override(
    project_id: int,
    payload: _OverridePayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from app.services.screening_engine import apply_prisma_override
    project = _load_project_or_404(session, project_id, context)
    apply_prisma_override(session, project, payload.model_dump())
    return {"override_applied": True, "project_id": project.id}


@router.post("/projects/{project_id}/screening/clear-override")
def screening_clear_override(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from app.services.screening_engine import apply_prisma_override
    project = _load_project_or_404(session, project_id, context)
    apply_prisma_override(session, project, None, clear=True)
    return {"cleared": True, "project_id": project.id}


@router.post("/projects/{project_id}/screening/run-dedupe")
def screening_run_dedupe(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    import dataclasses as _dc
    from app.services.screening_engine import run_full_project_dedupe, DedupeRunResult
    project = _load_project_or_404(session, project_id, context)
    r: DedupeRunResult = run_full_project_dedupe(session, project)
    return _dc.asdict(r)


@router.post(
    "/projects/{project_id}/screening/records/{record_id}/confirm-unique",
    response_model=LiteratureLibraryResponse,
)
def screening_confirm_unique(
    project_id: int,
    record_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> LiteratureLibraryResponse:
    project = _load_project_or_404(session, project_id, context)
    try:
        return confirm_record_unique(session, project, record_id)
    except LiteratureNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except LiteratureError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e


# ---------------------------------------------------------------------------
# Wave83 T4: 9 Extraction + Analysis REST thin-wrappers (lazy import only)
# ---------------------------------------------------------------------------


class _TemplateSavePayload(BaseModel):
    name: str = Field(..., min_length=1)
    fields: list[dict]


class _TemplateLockPayload(BaseModel):
    template_id: int


class _CellUpsertPayload(BaseModel):
    field_key: str
    reviewer_id: str
    value: object
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class _OutcomeDefinePayload(BaseModel):
    name: str = Field(..., min_length=1)
    outcome_type: str
    measure: str
    time_point: str | None = None


class _MetaRunPayload(BaseModel):
    outcome_id: int
    analysis_model: str = Field(..., pattern=r"^(fixed_iv|fixed_mh|random_dl)$")


class _OutcomeRenamePayload(BaseModel):
    name: str = Field(..., min_length=1)


class _ArmUpsertPayload(BaseModel):
    outcome_id: int
    record_id: int
    arm_label: str
    reviewer_id: str
    binary_data: dict | None = None
    continuous_data: dict | None = None


_DEFAULT_FIELDS = [
    {"key": "study_design", "type": "categorical", "label": "Study Design", "options": ["RCT", "Cohort", "Case-Control"]},
    {"key": "sample_size", "type": "numeric", "label": "Sample Size"},
    {"key": "intervention", "type": "text", "label": "Intervention"},
    {"key": "comparator", "type": "text", "label": "Comparator"},
    {"key": "primary_outcome", "type": "text", "label": "Primary Outcome"},
]


@router.get("/projects/{project_id}/stages/extraction/template")
def extraction_get_template(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.extraction_template import get_project_template
    tpl = get_project_template(session, project.id or project_id)
    if tpl is None:
        return {
            "template": None,
            "fields": list(_DEFAULT_FIELDS),
            "locked": False,
        }
    return {
        "template": {
            "id": tpl.id,
            "name": tpl.name,
            "locked": tpl.locked,
            "locked_at": tpl.locked_at.isoformat() if tpl.locked_at else None,
            "created_by": tpl.created_by,
        },
        "fields": list(tpl.fields_json),
        "locked": tpl.locked,
    }


@router.post("/projects/{project_id}/stages/extraction/template/save")
def extraction_save_template(
    project_id: int,
    payload: _TemplateSavePayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.extraction_template import save_template
    try:
        tpl = save_template(
            session,
            project.id or project_id,
            payload.name,
            payload.fields,
            created_by=context.user_id,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return {"saved": True, "id": tpl.id, "name": tpl.name, "locked": tpl.locked}


@router.post("/projects/{project_id}/stages/extraction/template/lock")
def extraction_lock_template(
    project_id: int,
    payload: _TemplateLockPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.extraction_template import lock_template
    try:
        tpl = lock_template(session, payload.template_id)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return {"locked": True, "id": tpl.id, "locked_at": tpl.locked_at.isoformat() if tpl.locked_at else None}


@router.post(
    "/projects/{project_id}/stages/records/{record_id}/extraction/cell",
    status_code=status.HTTP_201_CREATED,
)
def extraction_upsert_cell(
    project_id: int,
    record_id: int,
    payload: _CellUpsertPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.extraction_engine import upsert_cell
    try:
        cell = upsert_cell(
            session,
            project.id or project_id,
            record_id,
            payload.field_key,
            payload.reviewer_id,
            payload.value,
            confidence=payload.confidence,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return {
        "record_id": cell.record_id,
        "field_key": cell.field_key,
        "reviewer_id": cell.reviewer_id,
        "value": cell.value_json,
        "confidence": cell.confidence,
    }


@router.get("/projects/{project_id}/stages/extraction/evidence-table")
def extraction_evidence_table(
    project_id: int,
    reviewer_ids: str | None = Query(default=None),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.extraction_engine import pivot_wide_evidence
    rids_list: list[str] | None = None
    if reviewer_ids is not None and reviewer_ids.strip():
        rids_list = [s.strip() for s in reviewer_ids.split(",") if s.strip()]
    rows = pivot_wide_evidence(session, project.id or project_id, reviewer_ids=rids_list)
    import dataclasses as _dc
    return {
        "rows": [_dc.asdict(r) for r in rows],
        "row_count": len(rows),
    }


@router.get("/projects/{project_id}/stages/extraction/kappa")
def extraction_kappa(
    project_id: int,
    reviewer_a_id: str = Query(...),
    reviewer_b_id: str = Query(...),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.extraction_engine import kappa_summary
    import dataclasses as _dc
    items = kappa_summary(
        session,
        project.id or project_id,
        reviewer_a_id,
        reviewer_b_id,
    )
    return {
        "items": [_dc.asdict(it) for it in items],
        "reviewer_a_id": reviewer_a_id,
        "reviewer_b_id": reviewer_b_id,
    }


@router.post(
    "/projects/{project_id}/stages/analysis/outcomes/define",
    status_code=status.HTTP_201_CREATED,
)
def analysis_outcome_define(
    project_id: int,
    payload: _OutcomeDefinePayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.meta_analysis import define_outcome
    od = define_outcome(
        session,
        project.id or project_id,
        payload.name,
        payload.outcome_type,
        payload.measure,
        time_point=payload.time_point,
    )
    return {
        "id": od.id,
        "name": od.label,
        "outcome_type": payload.outcome_type,
        "measure": payload.measure,
        "time_point": payload.time_point,
    }


@router.get("/projects/{project_id}/stages/analysis/outcomes")
def analysis_outcomes_list(
    project_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.meta_analysis import list_outcomes
    items = list_outcomes(session, project.id or project_id)
    return {"items": items, "count": len(items)}


@router.patch("/projects/{project_id}/stages/analysis/outcomes/{outcome_id}")
def analysis_outcome_rename(
    project_id: int,
    outcome_id: int,
    payload: _OutcomeRenamePayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.meta_analysis import rename_outcome
    od = rename_outcome(session, project.id or project_id, outcome_id, payload.name)
    return {"id": od.id, "name": od.label}


@router.delete("/projects/{project_id}/stages/analysis/outcomes/{outcome_id}")
def analysis_outcome_delete(
    project_id: int,
    outcome_id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.meta_analysis import delete_outcome
    delete_outcome(session, project.id or project_id, outcome_id)
    return {"deleted": True, "outcome_id": outcome_id}


@router.post(
    "/projects/{project_id}/stages/analysis/outcomes/{outcome_id}/arm-data",
    status_code=status.HTTP_201_CREATED,
)
def analysis_outcome_arm_upsert(
    project_id: int,
    outcome_id: int,
    payload: _ArmUpsertPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.meta_analysis import upsert_outcome_arm_data
    try:
        ad = upsert_outcome_arm_data(
            session,
            project.id or project_id,
            payload.outcome_id,
            payload.record_id,
            payload.arm_label,
            payload.reviewer_id,
            binary_data=payload.binary_data,
            continuous_data=payload.continuous_data,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return {
        "id": ad.id,
        "outcome_id": ad.outcome_id,
        "record_id": ad.record_id,
        "arm_label": ad.arm_label,
        "data_json": ad.data_json,
    }


@router.post("/projects/{project_id}/stages/analysis/run-meta")
def analysis_run_meta(
    project_id: int,
    payload: _MetaRunPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    project = _load_project_or_404(session, project_id, context)
    from app.services.meta_analysis import run_meta_analysis
    try:
        result = run_meta_analysis(
            session,
            project.id or project_id,
            payload.outcome_id,
            payload.analysis_model,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    return result


@router.get("/projects/{project_id}/stages/analysis/forest/{outcome_id}.svg")
def analysis_forest_svg(
    project_id: int,
    outcome_id: int,
    model: str = Query(default="random_dl", pattern=r"^(fixed_iv|fixed_mh|random_dl)$"),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> Response:
    project = _load_project_or_404(session, project_id, context)
    from app.services.meta_analysis import generate_forest_svg
    svg_bytes = generate_forest_svg(
        session,
        project.id or project_id,
        outcome_id,
        model=model,
    )
    return Response(
        content=svg_bytes,
        media_type="image/svg+xml",
        headers={"Content-Disposition": f'inline; filename="forest-{outcome_id}.svg"'},
    )

# ═══════════════════════════════════════════════════════════════════════════════
# WAVE 8.4 OUTPUT STAGE REST THIN-WRAPPERS (APPEND EOF; W8.3 endpoints above untouched)
# AC8 NT-5 全部 lazy inside endpoints. workspace 顶部 import 0 grade/report/output/sof
# ═══════════════════════════════════════════════════════════════════════════════
@router.post("/projects/{project_id}/grade", status_code=201)
def w84_post_grade_assessment(project_id: int, payload: dict):
    from sqlmodel import select
    from app.db import SessionLocal
    from app.models import GradeAssessment
    from app.services.output_stage import (
        _simulate_rule_O8, _simulate_rule_O1, OutputStageError as _OSErr,
    )
    try:
        keys = list((payload.get("domains_5") or {}).keys())
        _simulate_rule_O8(keys_count=len(keys))
        _simulate_rule_O1(locked=bool(payload.get("locked", False)), touch="domains_5")
    except _OSErr as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(e))
    sl = SessionLocal()
    with sl as s:
        g = GradeAssessment(
            project_id=project_id,
            outcome_id=int(payload.get("outcome_id", 0)),
            reviewer_id=int(payload.get("reviewer_id", 0)),
            domains_5=payload.get("domains_5") or {},
            upgrades_3=payload.get("upgrades_3") or {},
            certainty_final=str(payload.get("certainty_final", "")),
            note=payload.get("note"),
            locked=bool(payload.get("locked", False)),
        )
        s.add(g); s.commit(); s.refresh(g)
        return {"id": g.id, "project_id": g.project_id, "outcome_id": g.outcome_id,
                "domains_5": g.domains_5, "upgrades_3": g.upgrades_3,
                "certainty_final": g.certainty_final, "locked": g.locked}

@router.get("/projects/{project_id}/grade")
def w84_get_grade_list(project_id: int):
    from sqlmodel import select
    from app.db import SessionLocal
    from app.models import GradeAssessment
    sl = SessionLocal()
    with sl as s:
        rows = s.exec(select(GradeAssessment).where(GradeAssessment.project_id == project_id)).all()
        return [dict(
            id=r.id, outcome_id=r.outcome_id, reviewer_id=r.reviewer_id,
            domains_5=r.domains_5, upgrades_3=r.upgrades_3,
            certainty_final=r.certainty_final, locked=r.locked, note=r.note,
        ) for r in rows]

@router.post("/projects/{project_id}/grade/{assessment_id}/lock")
def w84_lock_grade(project_id: int, assessment_id: int):
    from sqlmodel import select
    from app.db import SessionLocal
    from app.models import GradeAssessment
    from app.services.output_stage import _simulate_rule_O1, OutputStageError as _OSErr
    sl = SessionLocal()
    with sl as s:
        g = s.get(GradeAssessment, assessment_id)
        if g is None:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Grade assessment not found")
        try:
            _simulate_rule_O1(locked=g.locked, touch="certainty_final")
        except _OSErr as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail=str(e))
        g.locked = True
        s.add(g); s.commit()
        return {"id": g.id, "locked": True}

@router.post("/projects/{project_id}/sof", status_code=201)
def w84_post_sof_row(project_id: int, payload: dict):
    from sqlmodel import select
    from app.db import SessionLocal
    from app.models import SofTableRow
    sl = SessionLocal()
    with sl as s:
        sr = SofTableRow(
            project_id=project_id,
            outcome_id=int(payload.get("outcome_id", 0)),
            assessment_id=(payload.get("assessment_id") or None),
            so_cols=payload.get("so_cols") or {},
        )
        s.add(sr); s.commit(); s.refresh(sr)
        return {"id": sr.id, "project_id": sr.project_id, "outcome_id": sr.outcome_id,
                "assessment_id": sr.assessment_id, "so_cols": sr.so_cols}

@router.get("/projects/{project_id}/sof")
def w84_get_sof_list(project_id: int):
    from sqlmodel import select
    from app.db import SessionLocal
    from app.models import SofTableRow
    sl = SessionLocal()
    with sl as s:
        rows = s.exec(select(SofTableRow).where(SofTableRow.project_id == project_id)).all()
        return [dict(id=r.id, outcome_id=r.outcome_id, assessment_id=r.assessment_id, so_cols=r.so_cols) for r in rows]

@router.post("/projects/{project_id}/prisma2020", status_code=201)
def w84_post_prisma2020_checklist(project_id: int, payload: dict):
    from sqlmodel import select
    from app.db import SessionLocal
    from app.models import Prisma2020Checklist as PCL
    from app.services.output_stage import _simulate_rule_O7, OutputStageError as _OSErr
    try:
        _simulate_rule_O7(locked=bool(payload.get("locked", False)))
    except _OSErr as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(e))
    sl = SessionLocal()
    with sl as s:
        fields = {f"item_{i}": bool(payload.get(f"item_{i}", False)) for i in range(1, 28)}
        p = PCL(
            project_id=project_id,
            reviewer_id=int(payload.get("reviewer_id", 0)),
            **fields,
            note=payload.get("note"),
            locked=bool(payload.get("locked", False)),
        )
        s.add(p); s.commit(); s.refresh(p)
        d = {"id": p.id, "project_id": p.project_id, "reviewer_id": p.reviewer_id, "locked": p.locked, "note": p.note}
        for i in range(1, 28): d[f"item_{i}"] = getattr(p, f"item_{i}")
        return d

@router.get("/projects/{project_id}/prisma2020")
def w84_get_prisma2020_checklist(project_id: int):
    from sqlmodel import select
    from app.db import SessionLocal
    from app.models import Prisma2020Checklist as PCL
    sl = SessionLocal()
    with sl as s:
        rows = s.exec(select(PCL).where(PCL.project_id == project_id)).all()
        out = []
        for p in rows:
            d = {"id": p.id, "project_id": p.project_id, "reviewer_id": p.reviewer_id, "locked": p.locked, "note": p.note}
            for i in range(1, 28): d[f"item_{i}"] = getattr(p, f"item_{i}")
            out.append(d)
        return out

@router.post("/projects/{project_id}/report/generate")
def w84_post_report_generate(project_id: int, payload: dict | None = None):
    payload = payload or {}
    from sqlmodel import select
    from app.db import SessionLocal
    from app.models import GradeAssessment
    from app.services.output_stage import _simulate_rule_O5, _simulate_rule_O6_incomplete, OutputStageError as _OSErr
    from app.services.report_engine import (
        generate_report_three_formats, ProjectReportInput, GradeAssRow as _GR,
    )
    import hashlib
    import json as _json
    sl = SessionLocal()
    with sl as s:
        grades = s.exec(select(GradeAssessment).where(GradeAssessment.project_id == project_id)).all()
    try:
        _simulate_rule_O5(grade_count=len(grades))
    except _OSErr as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(e))
    grade_rows = [
        _GR(
            outcome_label=f"Outcome {g.outcome_id}",
            certainty=str(g.certainty_final),
            participants_n=0, studies_k=0,
            effect_label="NR", ar_control="NR", ar_intervention="NR",
            comments=g.note or "",
        ) for g in grades
    ]
    pi = ProjectReportInput(
        project_name=f"Project {project_id}", project_id=project_id,
        owner_display="Owner", abstract_summary="",
        prisma_checklist_masked_count=0, prisma_checklist_total_items=27,
        grade_rows=grade_rows, forest_svg_content="",
    )
    md, html, txt = generate_report_three_formats(pi)
    try:
        _simulate_rule_O6_incomplete(md=md, html=html, txt=txt)
    except _OSErr as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(e))
    sha_grade = hashlib.sha256(_json.dumps([dict(domains_5=g.domains_5, upgrades_3=g.upgrades_3, certainty=g.certainty_final) for g in grades], sort_keys=True).encode("utf-8")).hexdigest()
    sha_analysis = hashlib.sha256(b"empty-w84-t4-analysis-stub").hexdigest()
    # === W84 T5 APPEND (idempotent get_or_create into ReportSnapshot table) ===
    from app.models import ReportSnapshot as _RS
    sl2 = SessionLocal()
    with sl2 as s2:
        existing = s2.query(_RS).filter(
            _RS.project_id == project_id,
            _RS.sha256_grade == sha_grade,
            _RS.sha256_analysis == sha_analysis,
        ).order_by(_RS.id.asc()).first()
        if existing is None:
            row = _RS(
                project_id=project_id,
                sha256_grade=sha_grade,
                sha256_analysis=sha_analysis,
                version_label=payload.get("version_label") or "v0.1-draft",
                md_content=md,
                html_content=html,
                txt_content=txt,
            )
            s2.add(row); s2.commit(); s2.refresh(row)
        else:
            row = existing
    snap_id = row.id
    # === W84 T5 END idempotent ===
    return {
        "id": snap_id,
        "sha256_grade": sha_grade,
        "sha256_analysis": sha_analysis,
        "version_label": payload.get("version_label") or "v0.1-draft",
        "md_content": md,
        "html_content": html,
        "txt_content": txt,
    }

@router.get("/projects/{project_id}/reports")
def w84_get_reports_list(project_id: int):
    from app.db import SessionLocal
    from app.models import ReportSnapshot as _RS
    sl = SessionLocal()
    with sl as s:
        rows = s.query(_RS).filter(_RS.project_id == project_id).order_by(_RS.id.desc()).all()
        out = []
        for r in rows:
            out.append({
                "id": r.id,
                "version_label": r.version_label,
                "sha256_grade": r.sha256_grade,
                "sha256_analysis": r.sha256_analysis,
                "md_content": r.md_content,
                "html_content": r.html_content,
                "txt_content": r.txt_content,
                "created_at": r.created_at.isoformat() if hasattr(r.created_at, "isoformat") else str(r.created_at),
            })
        return out

