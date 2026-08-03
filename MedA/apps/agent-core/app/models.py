from sqlmodel import Field, SQLModel


class Organization(SQLModel, table=True):
    slug: str = Field(primary_key=True)
    name: str


class Membership(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str
    organization_slug: str = Field(foreign_key="organization.slug")
    role: str = "org_admin"


class ResearchProject(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    organization_slug: str = Field(foreign_key="organization.slug")
    owner_user_id: str
    name: str
    description: str
    workspace_key: str


class AuditEvent(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    actor: str
    organization_slug: str
    resource_type: str
    resource_id: str
    action: str
    client_type: str
    trace_id: str


class FileRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int
    kind: str
    name: str
    storage_path: str
    checksum: str


class ArtifactRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int
    artifact_type: str
    title: str
    source_file_id: int | None = None
