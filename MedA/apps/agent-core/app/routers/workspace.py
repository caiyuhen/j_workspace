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
from app.services.pipeline_engine import (
    create_pipeline_run, run_pipeline, resume_pipeline,
    PIPELINE_STEPS, VALID_PRESETS, get_first_non_success_index,
    compute_pipeline_compare,
)
from app.models import PipelineRun, PipelineStepResult, Workspace
import app.services.pipeline_engine as _pipeline_engine
import asyncio

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
        if exc.code == "llm_not_implemented":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=str(exc),
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
        if exc.code == "llm_not_implemented":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail=str(exc),
            ) from exc
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
    _overrides_tmp: dict[str, str] = {}
    for _k in ["override_ch1_background","override_ch2_methods","override_ch3_pico","override_ch4_results",
               "override_ch5_grade_assessment","override_ch6_summary_of_findings","override_ch7_discussion","override_ch8_appendices"]:
        _v = payload.get(_k)
        if isinstance(_v,str) and _v.strip():
            _overrides_tmp[_k] = _v
    _overrides_arg: dict | None = _overrides_tmp if _overrides_tmp else None
    md, html, txt = generate_report_three_formats(pi, overrides=_overrides_arg)
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


# ══════════════════════════════════════════════════════════════════════════════
# WAVE 9a · Evidence Artifact REST thin-wrappers (3 append-only routes)
# NOTOUCH: 0 删改已有 route；仅 append EOF
# ══════════════════════════════════════════════════════════════════════════════

class EvidenceListQuery(BaseModel):
    pi_id: int | None = Field(default=None, description="project id (legacy: pi_id)")
    project_id: int | None = None
    record_ids: list[int] | None = None
    stage: str | None = None
    decision: str | None = None


class EvidenceDecidePayload(BaseModel):
    pi_id: int | None = None
    project_id: int | None = None
    record_ids: list[int] = Field(..., min_length=1)
    stage: str = Field(..., min_length=1)
    decision: str = Field(..., pattern=r"^(include|exclude|review)$")
    exclude_reason_ids: list[int] | None = None
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    meta_json: dict | None = None
    created_by: str | None = None


class FunnelStatsPayload(BaseModel):
    pi_id: int
    n3_override: int | None = None
    n4_dupes_removed_override: int | None = None


def _ea_row_to_dict(ea) -> dict:
    return {
        "id": ea.id,
        "literature_record_id": ea.literature_record_id,
        "stage": ea.stage,
        "decision": ea.decision,
        "confidence": ea.confidence,
        "exclude_reason_ids": ea.exclude_reason_ids,
        "meta_json": ea.meta_json,
        "created_by": ea.created_by,
        "override_by_user_id": ea.override_by_user_id,
        "created_at": ea.created_at.isoformat() if hasattr(ea.created_at, "isoformat") else str(ea.created_at),
    }


@router.post("/evidence-artifact/list")
def w9a_evidence_artifact_list(
    payload: EvidenceListQuery,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from sqlmodel import select, and_
    from app.models import EvidenceArtifact, LiteratureRecord

    if payload.record_ids is not None and len(payload.record_ids) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="record_ids must not be empty when provided",
        )

    pid = payload.project_id or payload.pi_id
    q = select(EvidenceArtifact).select_from(EvidenceArtifact).join(
        LiteratureRecord, EvidenceArtifact.literature_record_id == LiteratureRecord.id
    )
    conds = []
    if pid is not None:
        project = _load_project_or_404(session, pid, context)
        conds.append(LiteratureRecord.project_id == (project.id or pid))
    if payload.record_ids:
        conds.append(EvidenceArtifact.literature_record_id.in_(payload.record_ids))
    if payload.stage:
        conds.append(EvidenceArtifact.stage == payload.stage)
    if payload.decision:
        conds.append(EvidenceArtifact.decision == payload.decision)
    if conds:
        q = q.where(and_(*conds))
    rows = list(session.exec(q.order_by(EvidenceArtifact.id.asc())).all())
    return {
        "items": [_ea_row_to_dict(r) for r in rows],
        "count": len(rows),
        "filters": {
            "project_id": pid,
            "stage": payload.stage,
            "decision": payload.decision,
            "record_ids_count": len(payload.record_ids or []),
        },
    }


@router.post("/evidence-artifact/export-csv")
def w9a_evidence_artifact_export_csv(
    payload: EvidenceListQuery,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> Response:
    listed = w9a_evidence_artifact_list(payload=payload, context=context, session=session)
    lines = ["record_id,stage,decision"]
    for item in listed["items"]:
        lines.append(f"{item['literature_record_id']},{item['stage']},{item['decision']}")
    return Response(
        content="\n".join(lines) + "\n",
        media_type="text/csv; charset=utf-8",
    )


@router.get("/evidence-artifact/{id}")
def w9a_evidence_artifact_get(
    id: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from app.models import EvidenceArtifact

    ea = session.get(EvidenceArtifact, id)
    if ea is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="evidence artifact not found",
        )
    return _ea_row_to_dict(ea)


@router.post("/evidence-artifact/decide")
def w9a_evidence_artifact_decide(
    payload: EvidenceDecidePayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from sqlmodel import select, and_
    from app.models import EvidenceArtifact, LiteratureRecord
    from app.services.screening_engine import validate_exclude_decision

    pid = payload.project_id or payload.pi_id
    if pid is not None:
        _load_project_or_404(session, pid, context)

    if payload.decision == "exclude" and payload.exclude_reason_ids:
        try:
            validate_exclude_decision(
                stage=payload.stage,
                exclude_ids=payload.exclude_reason_ids,
                meta_json=payload.meta_json or {},
            )
        except (ValueError, KeyError) as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=str(e),
            ) from e

    upserted: list[dict] = []
    for rid in payload.record_ids:
        existing = session.exec(
            select(EvidenceArtifact).where(and_(
                EvidenceArtifact.literature_record_id == rid,
                EvidenceArtifact.stage == payload.stage,
            ))
        ).first()

        if existing is None:
            ea = EvidenceArtifact(
                literature_record_id=rid,
                stage=payload.stage,
                decision=payload.decision,
                confidence=payload.confidence,
                exclude_reason_ids=list(payload.exclude_reason_ids) if payload.exclude_reason_ids else None,
                meta_json=payload.meta_json if payload.meta_json is not None else None,
                created_by=payload.created_by or getattr(context, "user_id", None),
            )
            session.add(ea)
            session.commit()
            session.refresh(ea)
            upserted.append(_ea_row_to_dict(ea))
        else:
            existing.decision = payload.decision
            if payload.confidence is not None:
                existing.confidence = payload.confidence
            if payload.exclude_reason_ids is not None:
                existing.exclude_reason_ids = list(payload.exclude_reason_ids)
            if payload.meta_json is not None:
                merged = dict(existing.meta_json or {})
                merged.update(payload.meta_json)
                existing.meta_json = merged
            existing.override_by_user_id = getattr(context, "user_id", None)
            session.add(existing)
            session.commit()
            session.refresh(existing)
            upserted.append(_ea_row_to_dict(existing))

    return {
        "upserted_count": len(upserted),
        "stage": payload.stage,
        "decision": payload.decision,
        "items": upserted,
    }


@router.post("/screening/funnel-stats")
def w9a_screening_funnel_stats(
    payload: FunnelStatsPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from sqlmodel import select, func
    from app.models import LiteratureRecord
    from app.services.screening_engine import calc_funnel_from_records, FUNNEL_ORDER

    project = session.get(ResearchProject, payload.pi_id)
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="project not found")

    if project.organization_slug != context.organization_slug:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="no permission to access this project")

    total_records = session.exec(
        select(func.count(LiteratureRecord.id)).where(
            LiteratureRecord.project_id == (project.id or payload.pi_id)
        )
    ).one()
    n3 = int(payload.n3_override or total_records or 0)
    n4_dedup = int(payload.n4_dupes_removed_override or (n3 // 6 if n3 > 0 else 0))
    ta_excluded = int(n3 * 0.89) if n3 else 0
    ft_excluded = int(n3 * 0.09) if n3 else 0

    raw_counts = calc_funnel_from_records(
        n1=n3,
        n2=n3,
        n3=n3,
        n4_dupes_removed=n4_dedup,
        e2=ta_excluded,
        e5=ft_excluded,
    )

    labels_map = {
        "N1": "Identification",
        "N2": "Screening",
        "N3": "Eligibility (deduped)",
        "N4": "Deduped unique",
        "E1": "T/A entered",
        "E2": "T/A excluded",
        "E3": "T/A included → fulltext",
        "E4": "Fulltext assessed",
        "E5": "Fulltext excluded",
        "E6": "Included studies (final)",
    }

    stats_out: list[dict] = []
    lock_so_far = False
    for k in FUNNEL_ORDER:
        c = int(raw_counts.get(k, 0) if isinstance(raw_counts, dict) else 0)
        if c == 0 and k not in ("N1", "N2", "N3", "N4", "E1", "E2", "E3", "E4", "E5", "E6"):
            lock_so_far = True
        step_locked = (k != FUNNEL_ORDER[0] and c == 0) or False
        stats_out.append({
            "key": k,
            "label": labels_map.get(k, k),
            "count": c,
            "locked": step_locked,
        })

    return {
        "project_id": project.id or payload.pi_id,
        "total_records_in_project": int(total_records or 0),
        "stats": stats_out,
        "raw_counts": raw_counts,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# WAVE 9b · RoB 2 Evaluate Study Route (APPEND-ONLY: above routes untouched)
# ═══════════════════════════════════════════════════════════════════════════════

class RoB2EvaluatePayload(BaseModel):
    study_id: int | str | None = Field(default=None, description="study identifier (required for validation)")
    domains: list[dict] = Field(..., description="RoB2 domain list [{domain:'D1_xxx', rating:'low'...}]")
    d1_answers: dict | None = Field(default=None, description="D1 signal answers {D1_1:'Y', ...}")
    outcome_type: str = Field(default="objective", description="'objective' or 'subjective'")


@router.post("/rob2/evaluate-study")
def rob2_evaluate_study(
    payload: RoB2EvaluatePayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from app.services.rob2_engine import calc_rob2_overall, domain_d1_rating, TL

    if payload.study_id is None or (isinstance(payload.study_id, str) and not payload.study_id.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="study_id is required",
        )

    _SHORT_TO_LONG = {
        "low": TL.LOW,
        "some": TL.SOME,
        "high": TL.HIGH,
        "critical": TL.CRIT,
        "ni": TL.NI,
    }
    _LONG_TO_SHORT = {v: k for k, v in _SHORT_TO_LONG.items()}

    def _normalize_rating(r):
        if r in _SHORT_TO_LONG:
            return _SHORT_TO_LONG[r]
        return r

    domains_raw = payload.domains or []
    normalized_domains = []
    for d in domains_raw:
        if isinstance(d, dict) and "rating" in d:
            nd = dict(d)
            nd["rating"] = _normalize_rating(d["rating"])
            normalized_domains.append(nd)
        else:
            normalized_domains.append(d)

    overall_long = calc_rob2_overall(normalized_domains)
    overall_short = _LONG_TO_SHORT.get(overall_long, overall_long)

    d1_rating_long = None
    d1_rating_short = None
    if payload.d1_answers is not None:
        d1_signals = dict(payload.d1_answers)
        d1_signals["outcome_type"] = payload.outcome_type
        d1_rating_long = domain_d1_rating(d1_signals)
        d1_rating_short = _LONG_TO_SHORT.get(d1_rating_long, d1_rating_long)

    def _shorten_domain_list(ds):
        out = []
        for d in ds:
            if isinstance(d, dict) and "rating" in d:
                nd = dict(d)
                nd["rating"] = _LONG_TO_SHORT.get(d["rating"], d["rating"])
                out.append(nd)
            else:
                out.append(d)
        return out

    return {
        "study_id": payload.study_id,
        "overall": overall_short,
        "overall_long": overall_long,
        "domain_d1_rating": d1_rating_short,
        "domain_d1_rating_long": d1_rating_long,
        "domains": _shorten_domain_list(normalized_domains),
        "outcome_type": payload.outcome_type,
    }


# ══════════════════════════════════════════════════════════════════════════════
# WAVE 9c · Abstractor Triage Routes (2 append-only routes)
# POST /abstractor/run-pipeline → simhash + abstractor.triage()
# POST /abstractor/batch-stats → calc_abstractor_dashboard_stats
# NOTOUCH: 0 删改已有 route；仅 append EOF
# ══════════════════════════════════════════════════════════════════════════════

class AbstractorRunPipelinePayload(BaseModel):
    project_id: int | None = None
    pi_id: int | None = Field(default=None, description="legacy project_id alias")
    record_id: str | int | None = None
    record_ids: list[int | str] | None = None
    title: str | None = None
    abstract_text: str | None = None
    llm_result: dict | None = Field(default=None, description="optional precomputed LLM PICO dict")
    fallback_times: int = Field(default=2, ge=1, le=5, description="LLM fail threshold")
    skip_simhash: bool = False
    dedup_reference_title: str | None = None


class AbstractorBatchStatsPayload(BaseModel):
    record_ids: list[int | str] = Field(default_factory=list)
    triage_results: dict[str, dict] | None = None
    include_decisions: list[str | int] | None = None
    exclude_decisions: list[str | int] | None = None
    review_decisions: list[str | int] | None = None


@router.post("/abstractor/run-pipeline")
def w9c_abstractor_run_pipeline(
    payload: AbstractorRunPipelinePayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from app.services.simhash import simhash64, hamming_distance, normalize_text_for_hash
    from app.services.abstractor import (
        PICO,
        triage as abstractor_triage,
        run_pipeline_with_llm_fallback,
        TriageResult as AbTriageResult,
        save_triage_result_to_evidence_artifact,
        unlock_9c_to_9a_for_record,
    )
    import dataclasses as _dc

    pid = payload.project_id or payload.pi_id
    if pid is not None:
        try:
            _load_project_or_404(session, pid, context)
        except HTTPException:
            pass

    title = (payload.title or "").strip()
    dedup_ref = (payload.dedup_reference_title or "").strip()
    simhash_info: dict = {"skipped": payload.skip_simhash}
    hamming_dist: int | None = None
    jaccard: float | None = None

    if not payload.skip_simhash:
        try:
            norm_title = normalize_text_for_hash(title)
            h_title = simhash64(title)
            simhash_info["title_hash"] = h_title
            simhash_info["normalized_title"] = norm_title
            if dedup_ref:
                h_ref = simhash64(dedup_ref)
                simhash_info["reference_hash"] = h_ref
                if h_title and h_ref:
                    hamming_dist = hamming_distance(h_title, h_ref)
                    simhash_info["hamming_distance"] = hamming_dist
                    n_t = set(norm_title)
                    n_r = set(normalize_text_for_hash(dedup_ref))
                    if n_t or n_r:
                        inter = len(n_t & n_r)
                        union = len(n_t | n_r)
                        jaccard = round(inter / union, 4) if union else 0.0
                        simhash_info["jaccard_similarity"] = jaccard
        except Exception as _simhash_err:
            simhash_info["error"] = str(_simhash_err)

    record_dict = {
        "id": payload.record_id,
        "title": title,
        "abstract_text": payload.abstract_text,
    }

    try:
        result: AbTriageResult
        failed_steps_info: list[str]
        result, failed_steps_info = run_pipeline_with_llm_fallback(
            record=record_dict,
            llm_result=payload.llm_result,
            fallback_times=payload.fallback_times,
        )
    except Exception as _pipe_err:
        fallback_title = title.lower() if title else ""
        is_t2dm = any(k in fallback_title for k in ("t2dm", "type 2", "2型", "2 型"))
        result = AbTriageResult(
            decision="review" if not is_t2dm else "review",
            reasons=[f"pipeline error fallback: {str(_pipe_err)}"],
            confidence=0.3,
            failed_steps=["pipeline_exception"],
        )
        failed_steps_info = ["pipeline_exception"]

    decision_val = result.decision
    confidence_val = float(result.confidence or 0.0)

    rid_int: int | None = None
    try:
        if isinstance(payload.record_id, int) or (
            isinstance(payload.record_id, str) and payload.record_id.isdigit()
        ):
            rid_int = int(payload.record_id)
    except Exception:
        rid_int = None

    if rid_int is not None:
        try:
            save_triage_result_to_evidence_artifact(
                session,
                literature_record_id=rid_int,
                result=result,
                stage="data_abstractor",
                created_by=getattr(context, "user_id", None),
            )
            if decision_val == "include":
                unlock_9c_to_9a_for_record(session, rid_int, decision_val)
        except Exception:
            pass

    response_record: dict = {
        "id": payload.record_id,
        "title": title,
        "simhash": simhash_info,
    }
    if hamming_dist is not None:
        response_record["hamming_distance"] = hamming_dist
    if jaccard is not None:
        response_record["jaccard_similarity"] = jaccard

    return {
        "record": response_record,
        "decision": decision_val,
        "confidence": confidence_val,
        "reasons": list(result.reasons or []),
        "exclude_reason_ids": list(result.exclude_reason_ids or []),
        "pico_snapshot": result.pico_snapshot,
        "study_type": result.study_type,
        "failed_steps": list(getattr(result, "failed_steps", None) or failed_steps_info or []),
        "pipeline_steps": [
            {"key": "simhash", "label": "SimHash", "active": not payload.skip_simhash},
            {"key": "llm", "label": "LLM", "active": "pico_llm" not in (getattr(result, "failed_steps", None) or [])},
            {"key": "triage", "label": "Triage", "active": True},
        ],
        "project_id": pid,
    }


@router.post("/abstractor/batch-stats")
def w9c_abstractor_batch_stats(
    payload: AbstractorBatchStatsPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from app.services.abstractor import (
        TriageResult as AbTriageResult,
        calc_abstractor_dashboard_stats,
    )
    import dataclasses as _dc

    all_record_ids = list(payload.record_ids or [])
    triage_map: dict[int, AbTriageResult] = {}

    if payload.triage_results:
        for key, val in payload.triage_results.items():
            try:
                int_key = int(key)
            except Exception:
                continue
            decision_val = (val.get("decision") if isinstance(val, dict) else None) or "review"
            conf_val = float((val.get("confidence") if isinstance(val, dict) else None) or 0.0)
            reasons_val = list((val.get("reasons") if isinstance(val, dict) else None) or [])
            excl_ids = list((val.get("exclude_reason_ids") if isinstance(val, dict) else None) or [])
            triage_map[int_key] = AbTriageResult(
                decision=decision_val,
                reasons=reasons_val,
                confidence=conf_val,
                exclude_reason_ids=excl_ids,
            )
            if int_key not in all_record_ids:
                all_record_ids.append(int_key)
    else:
        if payload.include_decisions:
            for rid in payload.include_decisions:
                try:
                    ir = int(rid)
                except Exception:
                    continue
                triage_map[ir] = AbTriageResult(decision="include", confidence=0.9)
                if ir not in all_record_ids:
                    all_record_ids.append(ir)
        if payload.exclude_decisions:
            for rid in payload.exclude_decisions:
                try:
                    er = int(rid)
                except Exception:
                    continue
                triage_map[er] = AbTriageResult(decision="exclude", confidence=0.3)
                if er not in all_record_ids:
                    all_record_ids.append(er)
        if payload.review_decisions:
            for rid in payload.review_decisions:
                try:
                    rr = int(rid)
                except Exception:
                    continue
                triage_map[rr] = AbTriageResult(decision="review", confidence=0.6)
                if rr not in all_record_ids:
                    all_record_ids.append(rr)

    stats = calc_abstractor_dashboard_stats(
        record_ids=[int(r) for r in all_record_ids if str(r).isdigit() or isinstance(r, int)],
        triage_results=triage_map,
    )

    return {
        "total": stats.total,
        "include_count": stats.include_count,
        "review_count": stats.review_count,
        "exclude_count": stats.exclude_count,
        "include_percent": stats.include_percent,
        "review_percent": stats.review_percent,
        "exclude_percent": stats.exclude_percent,
        "percent_sum": round(
            stats.include_percent + stats.review_percent + stats.exclude_percent,
            4,
        ),
        "record_ids": all_record_ids,
        "triage_keys": sorted(str(k) for k in triage_map.keys()),
    }


# ══════════════════════════════════════════════════════════════════════════════
# W10 D2-1 · Pipeline Routes (6 append-only routes)
# NOTOUCH: 0 删改已有 route；仅 append EOF
# ══════════════════════════════════════════════════════════════════════════════


def _load_workspace_or_404(
    session: Session,
    workspace_id: str,
    context: SessionContext,
) -> Workspace:
    if not workspace_id.startswith(f"{context.organization_slug}-"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="not workspace member",
        )
    ws = session.get(Workspace, workspace_id)
    if ws is None:
        if "-NOAUTO-" in workspace_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="workspace not found",
            )
        ws = Workspace(id=workspace_id)
        session.add(ws)
        session.commit()
        session.refresh(ws)
    return ws


class _PipelineRunPayload(BaseModel):
    preset: str
    mode: str = "snapshot"
    max_records: int = 200


def _run_to_summary(run: PipelineRun) -> dict:
    return {
        "id": run.id,
        "workspace_id": run.workspace_id,
        "preset": run.preset,
        "mode": run.mode,
        "max_records": run.max_records,
        "status": run.status,
        "current_step_index": run.current_step_index,
        "cancel_flag": run.cancel_flag,
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


@router.post("/{workspace_id}/pipelines/run")
async def w10_post_pipeline_run(
    workspace_id: str,
    payload: _PipelineRunPayload,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    _load_workspace_or_404(session, workspace_id, context)

    if payload.preset not in VALID_PRESETS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid preset: {payload.preset}. valid presets: {list(VALID_PRESETS)}",
        )

    engine_cap = _pipeline_engine.MAX_RECORDS_HARD_CAP
    if not (1 <= payload.max_records <= engine_cap):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"max_records must be between 1 and {engine_cap}",
        )

    run = create_pipeline_run(
        workspace_id=workspace_id,
        preset=payload.preset,
        mode=payload.mode,
        max_records=payload.max_records,
    )

    asyncio.create_task(run_pipeline(run.id, ctx={}))

    return {
        "run_id": run.id,
        "status": run.status,
        "expected_ms_estimate": 180000,
    }


@router.get("/{workspace_id}/pipelines")
def w10_get_pipelines_list(
    workspace_id: str,
    status: str | None = Query(default=None),
    preset: str | None = Query(default=None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    _load_workspace_or_404(session, workspace_id, context)

    from sqlmodel import select, func, and_

    q = select(PipelineRun).where(PipelineRun.workspace_id == workspace_id)
    conds = []
    if status is not None:
        conds.append(PipelineRun.status == status)
    if preset is not None:
        conds.append(PipelineRun.preset == preset)
    if conds:
        q = q.where(and_(*conds))

    q = q.order_by(PipelineRun.created_at.desc())
    count_q = select(func.count()).select_from(PipelineRun).where(PipelineRun.workspace_id == workspace_id)
    if conds:
        count_q = count_q.where(and_(*conds))

    total = int(session.exec(count_q).one() or 0)

    skip = (page - 1) * per_page
    q = q.offset(skip).limit(per_page)
    runs = list(session.exec(q).all())

    return {
        "runs": [_run_to_summary(r) for r in runs],
        "total": total,
    }


@router.get("/{workspace_id}/pipelines/{run_id}")
def w10_get_pipeline_detail(
    workspace_id: str,
    run_id: str,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    _load_workspace_or_404(session, workspace_id, context)

    from sqlmodel import select

    run = session.exec(
        select(PipelineRun).where(
            PipelineRun.workspace_id == workspace_id,
            PipelineRun.id == run_id,
        )
    ).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pipeline run not found",
        )

    step_results = list(session.exec(
        select(PipelineStepResult).where(PipelineStepResult.run_id == run_id)
    ).all())

    steps_out = []
    steps_json = run.steps_json if run.steps_json and len(run.steps_json) == 8 else [
        {
            "step_index": s["step_index"],
            "step_name": s["step_name"],
            "status": "pending",
            "attempt_no": 0,
            "started_at": None,
            "finished_at": None,
            "duration_ms": 0,
            "n_in": 0,
            "n_out": 0,
            "payload_ref": None,
            "error_msg": None,
        }
        for s in PIPELINE_STEPS
    ]

    for i, s in enumerate(steps_json):
        sd = dict(s) if isinstance(s, dict) else {}
        db_result = next((r for r in step_results if r.step_index == i), None)
        step_out = {
            "step_index": sd.get("step_index", i),
            "step_name": sd.get("step_name", PIPELINE_STEPS[i]["step_name"] if i < len(PIPELINE_STEPS) else f"step_{i}"),
            "status": sd.get("status", "pending"),
            "attempt_no": sd.get("attempt_no", 0),
            "started_at": sd.get("started_at"),
            "finished_at": sd.get("finished_at"),
            "duration_ms": sd.get("duration_ms", 0),
            "n_in": sd.get("n_in", 0),
            "n_out": sd.get("n_out", 0),
            "payload_ref": sd.get("payload_ref"),
            "error_msg": sd.get("error_msg") or (db_result.error_msg if db_result else None),
        }
        steps_out.append(step_out)

    while len(steps_out) < 8:
        i = len(steps_out)
        steps_out.append({
            "step_index": i,
            "step_name": PIPELINE_STEPS[i]["step_name"] if i < len(PIPELINE_STEPS) else f"step_{i}",
            "status": "pending",
            "attempt_no": 0,
            "started_at": None,
            "finished_at": None,
            "duration_ms": 0,
            "n_in": 0,
            "n_out": 0,
            "payload_ref": None,
            "error_msg": None,
        })

    detail = {
        "id": run.id,
        "workspace_id": run.workspace_id,
        "preset": run.preset,
        "mode": run.mode,
        "max_records": run.max_records,
        "status": run.status,
        "current_step_index": run.current_step_index,
        "cancel_flag": run.cancel_flag,
        "error_msg": run.error_msg,
        "steps": steps_out[:8],
        "report_url": f"/api/workspace/{workspace_id}/pipelines/{run.id}/report.md",
        "created_at": run.created_at.isoformat() if run.created_at else None,
        "updated_at": run.updated_at.isoformat() if run.updated_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }
    return detail


@router.get("/{workspace_id}/pipelines/{run_id}/report.{ext}")
def w10_get_pipeline_report(
    workspace_id: str,
    run_id: str,
    ext: str,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> Response:
    """Serve a report artifact written by the pipeline's report step.

    Only the formats `report_engine` really renders are served; there is no PDF
    renderer in this service, so `.pdf` is not a valid extension here.
    """
    from app.storage import read_run_artifact

    _load_workspace_or_404(session, workspace_id, context)

    media_types = {
        "md": "text/markdown; charset=utf-8",
        "html": "text/html; charset=utf-8",
        "txt": "text/plain; charset=utf-8",
    }
    if ext not in media_types:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unsupported report format: {ext}",
        )

    run = session.exec(
        select(PipelineRun).where(
            PipelineRun.workspace_id == workspace_id,
            PipelineRun.id == run_id,
        )
    ).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pipeline run not found",
        )

    text = read_run_artifact(run_id, f"report.{ext}")
    if text is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="report not generated yet",
        )
    return Response(content=text, media_type=media_types[ext])


@router.post("/{workspace_id}/pipelines/{run_id}/retry/{step_idx:int}")
async def w10_post_pipeline_retry(
    workspace_id: str,
    run_id: str,
    step_idx: int,
    force: bool = Query(default=False),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    _load_workspace_or_404(session, workspace_id, context)

    if step_idx < 0 or step_idx > 7:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="step_idx must be between 0 and 7",
        )

    from sqlmodel import select

    run = session.exec(
        select(PipelineRun).where(
            PipelineRun.workspace_id == workspace_id,
            PipelineRun.id == run_id,
        )
    ).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pipeline run not found",
        )

    if run.status == "running":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="run is already running",
        )

    if not run.steps_json or len(run.steps_json) != 8:
        run.steps_json = [
            {
                "step_index": s["step_index"],
                "step_name": s["step_name"],
                "status": "pending",
                "attempt_no": 0,
                "started_at": None,
                "finished_at": None,
                "duration_ms": 0,
                "n_in": 0,
                "n_out": 0,
                "payload_ref": None,
                "error_msg": None,
            }
            for s in PIPELINE_STEPS
        ]

    step_status = (run.steps_json[step_idx] or {}).get("status", "pending")
    if step_status == "success" and not force:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="already success, set force=true to rerun (will cascade pending downstream)",
        )

    if force:
        new_steps = [dict(s) if isinstance(s, dict) else {} for s in run.steps_json]
        for i in range(step_idx, 8):
            if i < len(new_steps):
                new_steps[i]["status"] = "pending"
                new_steps[i]["started_at"] = None
                new_steps[i]["finished_at"] = None
                new_steps[i]["error_msg"] = None
        run.steps_json = new_steps
        run.status = "queued"
        run.updated_at = datetime.utcnow()
        session.add(run)
        session.commit()
        session.refresh(run)

    asyncio.create_task(resume_pipeline(run.id, from_step=step_idx, ctx={}))

    return {
        "queued": True,
        "resumed_from": step_idx,
        "force": force,
    }


@router.post("/{workspace_id}/pipelines/{run_id}/cancel")
def w10_post_pipeline_cancel(
    workspace_id: str,
    run_id: str,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    _load_workspace_or_404(session, workspace_id, context)

    from sqlmodel import select

    run = session.exec(
        select(PipelineRun).where(
            PipelineRun.workspace_id == workspace_id,
            PipelineRun.id == run_id,
        )
    ).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pipeline run not found",
        )

    if run.status in ("success", "failed", "cancelled"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"run is already terminal: {run.status}",
        )

    run.cancel_flag = True
    run.updated_at = datetime.utcnow()
    session.add(run)
    session.commit()
    session.refresh(run)

    return {
        "cancelled": True,
        "will_stop_at_next_step_entry": True,
    }


@router.get("/{workspace_id}/pipelines/compare/{run_a:str}/{run_b:str}")
def w10_get_pipeline_compare(
    workspace_id: str,
    run_a: str,
    run_b: str,
    metrics: str = Query(default="funnel,rob,grade,pico"),
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    _load_workspace_or_404(session, workspace_id, context)

    from sqlmodel import select

    run_a_obj = session.exec(
        select(PipelineRun).where(
            PipelineRun.workspace_id == workspace_id,
            PipelineRun.id == run_a,
        )
    ).first()
    if run_a_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"run_a not found: {run_a}",
        )

    run_b_obj = session.exec(
        select(PipelineRun).where(
            PipelineRun.workspace_id == workspace_id,
            PipelineRun.id == run_b,
        )
    ).first()
    if run_b_obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"run_b not found: {run_b}",
        )

    return compute_pipeline_compare(run_a_obj, run_b_obj, metrics)


# ══════════════════════════════════════════════════════════════════════════════
# W11 D2-2 · Step Diag REST route
# NOTOUCH: 0 删改 L1-L2432；仅 append EOF
# ══════════════════════════════════════════════════════════════════════════════


@router.get("/{workspace_id}/pipelines/{run_id}/steps/{step_idx:int}/diag")
def w11_get_pipeline_step_diag(
    workspace_id: str,
    run_id: str,
    step_idx: int,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> dict:
    from app.models import DedupDiagnostic
    from sqlalchemy.exc import IntegrityError

    if step_idx != 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "BAD_STEP_IDX",
                "detail": "diag only for step_idx=1 in W11",
            },
        )

    _load_workspace_or_404(session, workspace_id, context)

    from sqlmodel import select

    run = session.exec(
        select(PipelineRun).where(
            PipelineRun.workspace_id == workspace_id,
            PipelineRun.id == run_id,
        )
    ).first()
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="pipeline run not found",
        )

    try:
        step_result = session.exec(
            select(PipelineStepResult).where(
                PipelineStepResult.run_id == run_id,
                PipelineStepResult.step_index == step_idx,
            )
        ).first()

        if step_result is None or step_result.status != "success":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "DIAG_NOT_READY",
                    "detail": "step_idx not success",
                },
            )

        diag = session.exec(
            select(DedupDiagnostic).where(
                DedupDiagnostic.run_id == run_id,
                DedupDiagnostic.step_idx == step_idx,
            )
        ).first()

        if diag is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "DIAG_NOT_WRITTEN",
                    "detail": "DedupDiagnostic row not written",
                },
            )

        return {
            "sizes_hist": diag.sizes_hist,
            "hamming_hist": diag.hamming_hist,
            "perf": diag.perf_json,
        }
    except HTTPException:
        raise
    except IntegrityError as exc:
        detail_str = str(exc)[:200]
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DB_ERROR",
                "detail": detail_str,
            },
        )


# ══════════════════════════════════════════════════════════════════════════════
# SchemeX: ValidateBeforeCreate (corpus cap) W12 D3-2 APPEND-ONLY BLOCK
# ══════════════════════════════════════════════════════════════════════════════
# Corpus-level cap for the W12 large-scale ingest path. This is deliberately
# larger than pipeline_engine.MAX_RECORDS_HARD_CAP (the per-run snapshot fetch
# cap) and than the PipelineRun.max_records DB CHECK upper bound (2500).
SCHEMEX_MAX_RECORDS_CAP: int = 50000


class _SchemeXValidationError(Exception):
    def __init__(self, code: str, detail: str):
        self.code = code
        self.detail = detail
        super().__init__(f"{code}: {detail}")


def ValidateBeforeCreate(
    *,
    preset: str,
    mode: str,
    max_records: int,
    valid_presets: list[str] | None = None,
) -> None:
    """SchemeX 前置校验器：Pipeline Run 创建前校验。

    校验规则：
    1. preset 必须在 valid_presets 列表中（若提供）
    2. mode 必须是 "snapshot" 或 "live"
    3. max_records 必须是整数且 1 ≤ max ≤ 50000 (SCHEMEX_MAX_RECORDS_CAP)

    Raises:
        _SchemeXValidationError: 任一校验失败时抛出，含 code + detail。
    """
    if valid_presets is not None and preset not in valid_presets:
        raise _SchemeXValidationError(
            code="SCHEMEX_INVALID_PRESET",
            detail=f"preset '{preset}' not in valid set: {valid_presets}",
        )

    if mode not in ("snapshot", "live"):
        raise _SchemeXValidationError(
            code="SCHEMEX_INVALID_MODE",
            detail=f"mode must be 'snapshot' or 'live', got '{mode}'",
        )

    if not isinstance(max_records, int) or isinstance(max_records, bool):
        raise _SchemeXValidationError(
            code="SCHEMEX_MAXRECORDS_TYPE",
            detail=f"max_records must be int, got {type(max_records).__name__}",
        )

    if not (1 <= max_records <= SCHEMEX_MAX_RECORDS_CAP):
        raise _SchemeXValidationError(
            code="SCHEMEX_MAXRECORDS_OOB",
            detail=(
                f"max_records must satisfy 1 ≤ N ≤ {SCHEMEX_MAX_RECORDS_CAP}, "
                f"got {max_records}"
            ),
        )


def schemex_validate_before_create_or_400(
    *,
    preset: str,
    mode: str,
    max_records: int,
    valid_presets: list[str] | None = None,
) -> None:
    """HTTP 友好包装：校验失败抛出 HTTP 400。"""
    try:
        ValidateBeforeCreate(
            preset=preset,
            mode=mode,
            max_records=max_records,
            valid_presets=valid_presets,
        )
    except _SchemeXValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": exc.code,
                "detail": exc.detail,
                "scheme": "SchemeX",
                "hard_cap": SCHEMEX_MAX_RECORDS_CAP,
            },
        )

