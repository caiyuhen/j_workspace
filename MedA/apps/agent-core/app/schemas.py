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


class RegisterFileRequest(BaseModel):
    project_id: int
    kind: str
    name: str
    storage_path: str
    checksum: str


class FileResponse(BaseModel):
    id: int
    project_id: int
    kind: str
    name: str
    storage_path: str
    checksum: str
