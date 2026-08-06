from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.models import ResearchProject
from app.schemas import (
    DeriveSearchQueryDraftRequest,
    SaveSearchQueryDraftRequest,
    SearchQueryEditorResponse,
    StageEntryResponse,
    WorkspaceHomeResponse,
)
from app.services.search_query import (
    SearchQueryNotFoundError,
    derive_search_query_draft,
    get_or_create_search_query_editor,
    get_search_query_snapshot,
    save_search_query_draft,
    save_search_query_version,
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
