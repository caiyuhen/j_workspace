from uuid import uuid4

from sqlmodel import Session, select

from app.models import AuthSession, Membership, Organization, User
from app.schemas import (
    DevLoginRequest,
    SessionOrganizationResponse,
    SessionResponse,
    SessionUserResponse,
)


def login_with_dev_session(session: Session, payload: DevLoginRequest) -> SessionResponse:
    user = session.get(User, payload.user_id)
    if user is None:
        user = User(user_id=payload.user_id, display_name=payload.display_name)
        session.add(user)
    else:
        user.display_name = payload.display_name

    organization = session.get(Organization, payload.organization_slug)
    if organization is None:
        organization = Organization(
            slug=payload.organization_slug,
            name=payload.organization_name,
        )
        session.add(organization)
    else:
        organization.name = payload.organization_name

    membership = session.exec(
        select(Membership).where(
            Membership.user_id == payload.user_id,
            Membership.organization_slug == payload.organization_slug,
        )
    ).first()
    if membership is None:
        membership = Membership(
            user_id=payload.user_id,
            organization_slug=payload.organization_slug,
            role=payload.role,
        )
        session.add(membership)
    else:
        membership.role = payload.role

    token = f"meda_{uuid4().hex}"
    auth_session = AuthSession(
        token=token,
        user_id=payload.user_id,
        organization_slug=payload.organization_slug,
        role=payload.role,
        client_type=payload.client_type,
    )
    session.add(auth_session)
    session.commit()

    return SessionResponse(
        token=token,
        user=SessionUserResponse(
            user_id=payload.user_id,
            display_name=payload.display_name,
        ),
        organization=SessionOrganizationResponse(
            slug=payload.organization_slug,
            name=payload.organization_name,
        ),
        role=payload.role,
        client_type=payload.client_type,
    )
