from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.db import get_session
from app.models import Membership, Organization, ResearchProject
from app.schemas import CreateProjectRequest, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=list[ProjectResponse])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectResponse]:
    projects = session.exec(select(ResearchProject)).all()
    return [ProjectResponse.model_validate(project, from_attributes=True) for project in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: CreateProjectRequest, session: Session = Depends(get_session)
) -> ProjectResponse:
    organization = session.get(Organization, payload.organization_slug)
    if organization is None:
        organization = Organization(slug=payload.organization_slug, name=payload.organization_slug)
        session.add(organization)

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

    return ProjectResponse.model_validate(project, from_attributes=True)
