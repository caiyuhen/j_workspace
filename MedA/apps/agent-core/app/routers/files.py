from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.db import get_session
from app.schemas import FileResponse, RegisterFileRequest
from app.services.files import register_file

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/register", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
def register_file_route(
    payload: RegisterFileRequest, session: Session = Depends(get_session)
) -> FileResponse:
    return register_file(session, payload)
