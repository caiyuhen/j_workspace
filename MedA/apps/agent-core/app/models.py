from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    user_id: str = Field(primary_key=True)
    display_name: str


class Organization(SQLModel, table=True):
    slug: str = Field(primary_key=True)
    name: str


class Membership(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
    organization_slug: str = Field(foreign_key="organization.slug")
    role: str = "org_admin"


class ResearchProject(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    organization_slug: str = Field(foreign_key="organization.slug")
    owner_user_id: str
    name: str
    description: str
    workspace_key: str


class ResearchTaskRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    title: str
    stage_key: str
    status: str


class SearchQuery(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    name: str
    stage_key: str = "search"
    latest_version: str = "v0"


class SearchQueryDraft(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="searchquery.id")
    based_on_version: str = "v0"
    grouped_terms_json: str
    expression_blocks_json: str
    selected_sources_json: str
    query_dirty: bool = False


class SearchQueryVersion(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    query_id: int = Field(foreign_key="searchquery.id")
    version_label: str
    grouped_terms_json: str
    expression_blocks_json: str
    selected_sources_json: str


class SearchSourceConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", unique=True)
    enabled_sources_json: str
    search_fields_json: str
    year_from: int | None = None
    year_to: int | None = None
    languages_json: str


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


class AuthSession(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
    organization_slug: str = Field(foreign_key="organization.slug")
    role: str
    client_type: str
