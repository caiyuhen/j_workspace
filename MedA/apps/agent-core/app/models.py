from datetime import datetime
from typing import Literal

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
    # --- WAVE82B_INSERT_PRISMA_OVERRIDE_FIELD 开始（用户手动改 n 数时存储 override，冻结 Prisma 计算显示）---
    prisma_override_json: str | None = Field(default=None)
    # --- WAVE82B_INSERT_PRISMA_OVERRIDE_FIELD 结束 ---


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


class LiteratureImportBatch(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    source_key: str
    parsed_count: int = 0
    duplicate_count: int = 0
    skipped_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_at_label: str = ""
    search_run_source_id: int | None = Field(default=None, foreign_key="searchrunsource.id")


class LiteratureRecord(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id")
    title: str
    authors: str = ""
    journal: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    abstract: str = ""
    source_key: str
    source_label: str = ""
    dedupe_status: str = "unique"
    duplicate_of_id: int | None = Field(
        default=None, foreign_key="literaturerecord.id"
    )
    import_batch_id: int | None = Field(
        default=None, foreign_key="literatureimportbatch.id"
    )
    search_run_id: int | None = Field(default=None, foreign_key="searchrun.id")
    relevance_score: float | None = None
    pico_status: str = "not_extracted"
    # --- WAVE82B_INSERT_SCREENING_FIELDS 开始（4 nullable，第 5 个 prisma_override 在 ResearchProject 下）---
    screening_stage: str | None = Field(default=None)  # "ta" | "fulltext" | None
    screening_decision: str | None = Field(default=None)  # "include" | "exclude" | None
    exclude_reason_json: str | None = Field(default=None)  # JSON: preset_class 1-9 + note + stage + auto_by
    screening_notes: str | None = Field(default=None)
    # --- WAVE82B_INSERT_SCREENING_FIELDS 结束 ---


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


class SearchRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    search_query_version_id: int | None = Field(
        default=None, foreign_key="searchqueryversion.id", index=True
    )
    query_snapshot: str
    selected_sources: str
    status: str = "pending"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    total_hits_raw: int = 0
    total_after_dedupe: int = 0
    error_message: str | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchRunSource(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    search_run_id: int = Field(foreign_key="searchrun.id", index=True)
    source_key: str = Field(index=True)
    status: str = "pending"
    hits_on_source: int | None = None
    records_retrieved: int = 0
    records_imported: int = 0
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None
    raw_response_excerpt: str | None = None


class LiteraturePico(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    record_id: int = Field(foreign_key="literaturerecord.id", sa_column_kwargs={"unique": True})
    population: str | None = None
    intervention: str | None = None
    comparison: str | None = None
    outcome: str | None = None
    study_type: str | None = None
    extraction_method: str
    confidence: float | None = None
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class AuthSession(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: str = Field(foreign_key="user.user_id")
    organization_slug: str = Field(foreign_key="organization.slug")
    role: str
    client_type: str


import sqlalchemy as sa
from typing import Any


class ExtractionTemplate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", unique=True)
    name: str
    description: str | None = Field(default=None)
    created_by: str | None = Field(default=None, foreign_key="user.user_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    locked: bool = Field(default=False)
    locked_at: datetime | None = Field(default=None)
    fields_json: list[dict[str, Any]] = Field(default_factory=list, sa_column=sa.Column(sa.JSON, nullable=False, default=list))


class ExtractionCell(SQLModel, table=True):
    record_id: int = Field(foreign_key="literaturerecord.id", primary_key=True)
    field_key: str = Field(primary_key=True)
    reviewer_id: str = Field(primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    value_json: Any = Field(default=None, sa_column=sa.Column(sa.JSON, nullable=True))
    confidence: float | None = Field(default=None)
    extracted_at: datetime = Field(default_factory=datetime.utcnow)


class OutcomeDefinition(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    outcome_key: str
    label: str
    description: str | None = None
    measure_type: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OutcomeArmData(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    record_id: int = Field(foreign_key="literaturerecord.id", index=True)
    outcome_id: int = Field(foreign_key="outcomedefinition.id", index=True)
    arm_label: str
    data_json: dict[str, Any] = Field(default_factory=dict, sa_column=sa.Column(sa.JSON, nullable=False, default=dict))
    reviewer_id: str


class AnalysisRun(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    outcome_id: int | None = Field(default=None, foreign_key="outcomedefinition.id")
    method: str
    config_json: dict[str, Any] = Field(default_factory=dict, sa_column=sa.Column(sa.JSON, nullable=False, default=dict))
    result_json: dict[str, Any] | None = Field(default=None, sa_column=sa.Column(sa.JSON, nullable=True))
    status: str = "pending"
    created_by: str | None = Field(default=None, foreign_key="user.user_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
