from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas import DevLoginRequest, SessionResponse
from app.services.auth import login_with_dev_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/dev-login", response_model=SessionResponse)
def dev_login(
    payload: DevLoginRequest, session: Session = Depends(get_session)
) -> SessionResponse:
    return login_with_dev_session(session, payload)
