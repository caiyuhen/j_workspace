from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from sqlmodel import Session

from app.db import get_session
from app.models import AuthSession, Organization, User
from app.services.jwt_tokens import TokenError, decode_token


@dataclass
class SessionContext:
    token: str
    user_id: str
    display_name: str
    organization_slug: str
    organization_name: str
    role: str
    client_type: str


def get_current_session(
    authorization: str | None = Header(default=None),
    session: Session = Depends(get_session),
) -> SessionContext:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="missing bearer token")

    token = authorization.replace("Bearer ", "", 1)
    try:
        decode_token(token)
    except TokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    # A valid signature is not enough: the session row is what makes revocation
    # possible, so a token whose row is gone must be rejected.
    auth_session = session.get(AuthSession, token)
    if auth_session is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid session")

    user = session.get(User, auth_session.user_id)
    organization = session.get(Organization, auth_session.organization_slug)
    if user is None or organization is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="session context missing")

    return SessionContext(
        token=auth_session.token,
        user_id=user.user_id,
        display_name=user.display_name,
        organization_slug=organization.slug,
        organization_name=organization.name,
        role=auth_session.role,
        client_type=auth_session.client_type,
    )


def require_admin(context: SessionContext = Depends(get_current_session)) -> SessionContext:
    if context.role not in {"org_admin", "super_admin"}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin role required")

    return context
