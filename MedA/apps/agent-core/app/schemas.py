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


class DevLoginRequest(BaseModel):
    organization_slug: str
    organization_name: str
    user_id: str
    display_name: str
    role: str
    client_type: str


class SessionUserResponse(BaseModel):
    user_id: str
    display_name: str


class SessionOrganizationResponse(BaseModel):
    slug: str
    name: str


class SessionResponse(BaseModel):
    token: str
    user: SessionUserResponse
    organization: SessionOrganizationResponse
    role: str
    client_type: str
