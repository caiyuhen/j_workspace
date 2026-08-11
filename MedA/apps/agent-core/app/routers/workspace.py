from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.models import ResearchProject
from app.schemas import (
    CreateLiteratureRecordRequest,
    DeriveSearchQueryDraftRequest,
    ImportLiteratureRequest,
    LiteratureLibraryResponse,
    SaveSearchQueryDraftRequest,
    SaveSearchSourceConfigRequest,
    SearchQueryEditorResponse,
    SearchSourceCatalogResponse,
    SearchSourceConfigResponse,
    StageEntryResponse,
    WorkspaceHomeResponse,
)
from app.services.literature import (
    LiteratureError,
    build_library_response,
    create_literature_record,
    import_literature,
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
    project = _load_project_or_404(session, project_id, context)

    try:
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
    project = _load_project_or_404(session, project_id, context)

    try:
        return create_literature_record(session, project, payload)
    except LiteratureError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(error)
        ) from error
