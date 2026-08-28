from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.models import ResearchProject
from app.schemas import FileResponse, RegisterFileRequest
from app.services.files import register_file

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/register", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def register_file_route(
    payload: RegisterFileRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> FileResponse:
    project = session.get(ResearchProject, payload.project_id)
    if project is None or project.organization_slug != context.organization_slug:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"project not found: {payload.project_id}",
        )

    return register_file(session, payload)
