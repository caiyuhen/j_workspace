from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.deps.auth import SessionContext, get_current_session
from app.models import Membership, Organization, ResearchProject, User
from app.schemas import CreateProjectRequest, ProjectResponse
from app.services.audit import record_audit_event
from app.services.events import broker

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> list[ProjectResponse]:
    projects = session.exec(
        select(ResearchProject).where(
            ResearchProject.organization_slug == context.organization_slug
        )
    ).all()
    return [ProjectResponse.model_validate(project, from_attributes=True) for project in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest,
    context: SessionContext = Depends(get_current_session),
    session: Session = Depends(get_session),
) -> ProjectResponse:
    if payload.organization_slug != context.organization_slug:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="organization_slug outside of the current session scope",
        )

    organization = session.get(Organization, context.organization_slug)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="organization not found",
        )

    if session.get(User, payload.owner_user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"owner user not found: {payload.owner_user_id}",
        )

    membership = session.exec(
        select(Membership).where(
            Membership.user_id == payload.owner_user_id,
            Membership.organization_slug == payload.organization_slug,
        )
    ).first()
    if membership is None:
        session.add(
            Membership(
                user_id=payload.owner_user_id,
                organization_slug=payload.organization_slug,
                role="pi",
            )
        )

    project = ResearchProject(
        organization_slug=payload.organization_slug,
        owner_user_id=payload.owner_user_id,
        name=payload.name,
        description=payload.description,
        workspace_key=f"{payload.organization_slug}/{payload.name}",
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    if project.id is None:
        raise HTTPException(status_code=500, detail="project id missing after commit")

    record_audit_event(
        session,
        actor=payload.owner_user_id,
        organization_slug=payload.organization_slug,
        resource_type="research_project",
        resource_id=str(project.id),
        action="project.created",
        client_type="web",
        trace_id=f"project-{project.id}",
    )
    session.commit()

    broker.publish(
        "project.created",
        {
            "project_id": project.id,
            "workspace_key": project.workspace_key,
            "organization_slug": project.organization_slug,
        },
    )

    return ProjectResponse.model_validate(project, from_attributes=True)
