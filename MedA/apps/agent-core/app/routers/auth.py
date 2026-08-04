from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.schemas import (
    DevLoginRequest,
    SessionOrganizationResponse,
    SessionResponse,
    SessionUserResponse,
)
from app.services.auth import login_with_dev_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/dev-login", response_model=SessionResponse)
def dev_login(
    payload: DevLoginRequest, session: Session = Depends(get_session)
) -> SessionResponse:
    return login_with_dev_session(session, payload)


@router.get("/me", response_model=SessionResponse)
def get_me(context: SessionContext = Depends(get_current_session)) -> SessionResponse:
    return SessionResponse(
        token=context.token,
        user=SessionUserResponse(
            user_id=context.user_id,
            display_name=context.display_name,
        ),
        organization=SessionOrganizationResponse(
            slug=context.organization_slug,
            name=context.organization_name,
        ),
        role=context.role,
        client_type=context.client_type,
    )
