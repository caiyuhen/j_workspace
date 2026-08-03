from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    organization_slug: str
    owner_user_id: str
    name: str
    description: str


class ProjectResponse(BaseModel):
    id: int
    organization_slug: str
    owner_user_id: str
    name: str
    description: str
    workspace_key: str
