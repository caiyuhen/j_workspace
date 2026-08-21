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

# ─────────────────────────────────────────────────────────────────────
# WAVE 8.4 OUTPUT STAGE 4 NEW TABLES
# (APPEND ONLY; WAVE 8.3 14 tables above MUST NOT change byte content)
# ─────────────────────────────────────────────────────────────────────
try:
    from sqlalchemy import UniqueConstraint as _w84_UniqueConstraint
    from sqlalchemy import Column as _w84_Column
    from sqlalchemy import JSON as _w84_JSON
    from sqlalchemy import Text as _w84_Text
except Exception:  # pragma: no cover - fallback if already imported elsewhere
    _w84_UniqueConstraint = sa.UniqueConstraint
    _w84_Column = sa.Column
    _w84_JSON = sa.JSON
    _w84_Text = sa.Text

def datetime_utcnow():
    return datetime.utcnow()

UniqueConstraint = _w84_UniqueConstraint
Column = _w84_Column
JSON = _w84_JSON
Text = _w84_Text

class GradeAssessment(SQLModel, table=True):
    __tablename__ = "gradeassessment"
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    outcome_id: int = Field(foreign_key="outcomedefinition.id", index=True)
    reviewer_id: int = Field(index=True)
    domains_5: dict = Field(sa_column=Column(JSON, nullable=False))
    upgrades_3: dict = Field(sa_column=Column(JSON, nullable=False))
    certainty_final: str = Field(max_length=16, nullable=False)
    note: str | None = Field(default=None, max_length=2000)
    locked: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime_utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("outcome_id", "reviewer_id", name="uq_grade_outcome_reviewer"),)

class SofTableRow(SQLModel, table=True):
    __tablename__ = "softablenode"
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    outcome_id: int = Field(foreign_key="outcomedefinition.id", index=True)
    assessment_id: int | None = Field(default=None, foreign_key="gradeassessment.id")
    so_cols: dict = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = Field(default_factory=datetime_utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("project_id", "outcome_id", name="uq_sof_project_outcome"),)

class ReportSnapshot(SQLModel, table=True):
    __tablename__ = "reportsnapshot"
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    sha256_grade: str = Field(max_length=64, nullable=False)
    sha256_analysis: str = Field(max_length=64, nullable=False)
    version_label: str = Field(max_length=64, nullable=False, default="v0.1-draft")
    md_content: str = Field(sa_column=Column(Text, nullable=False))
    html_content: str = Field(sa_column=Column(Text, nullable=False))
    txt_content: str = Field(sa_column=Column(Text, nullable=False))
    created_at: datetime = Field(default_factory=datetime_utcnow, nullable=False)

class Prisma2020Checklist(SQLModel, table=True):
    __tablename__ = "prisma2020checklist"
    id: int | None = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="researchproject.id", index=True)
    reviewer_id: int = Field(index=True)
    item_1: bool = False;  item_2: bool = False;  item_3: bool = False;  item_4: bool = False
    item_5: bool = False;  item_6: bool = False;  item_7: bool = False;  item_8: bool = False
    item_9: bool = False;  item_10: bool = False; item_11: bool = False; item_12: bool = False
    item_13: bool = False; item_14: bool = False; item_15: bool = False; item_16: bool = False
    item_17: bool = False; item_18: bool = False; item_19: bool = False; item_20: bool = False
    item_21: bool = False; item_22: bool = False; item_23: bool = False; item_24: bool = False
    item_25: bool = False; item_26: bool = False; item_27: bool = False
    note: str | None = Field(default=None, max_length=2000)
    locked: bool = Field(default=False, nullable=False)
    created_at: datetime = Field(default_factory=datetime_utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("project_id", "reviewer_id", name="uq_prisma_project_reviewer"),)

# ─────────────────────────────────────────────────────────────────────
# WAVE 9a EVIDENCE ARTIFACT TABLE
# ─────────────────────────────────────────────────────────────────────

class EvidenceArtifact(SQLModel, table=True):
    __tablename__ = "evidenceartifact"
    id: int | None = Field(default=None, primary_key=True)
    literature_record_id: int = Field(foreign_key="literaturerecord.id", index=True)
    stage: str = Field(max_length=32, nullable=False)
    decision: str = Field(max_length=16, nullable=False)
    confidence: float | None = Field(default=None)
    exclude_reason_ids: list | dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    meta_json: list | dict | None = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_by: str | None = Field(default=None, foreign_key="user.user_id")
    override_by_user_id: str | None = Field(default=None, foreign_key="user.user_id")
    created_at: datetime = Field(default_factory=datetime_utcnow, nullable=False)
    __table_args__ = (UniqueConstraint("literature_record_id", "stage", name="uq_evidenceartifact_lr_stage"),)


class Workspace(SQLModel, table=True):
    __tablename__ = "workspace"
    id: str = Field(sa_column=Column(sa.CHAR(36), primary_key=True))


class PipelineRun(SQLModel, table=True):
    __tablename__ = "pipelinerun"
    id: str = Field(sa_column=Column(sa.CHAR(32), primary_key=True))
    workspace_id: str = Field(sa_column=Column(sa.CHAR(36), sa.ForeignKey("workspace.id"), nullable=False, index=True))
    preset: str = Field(sa_column=Column(sa.String(64), nullable=False, index=True))
    mode: str = Field(sa_column=Column(sa.CHAR(8), nullable=False))
    max_records: int = Field(default=200, sa_column=Column(sa.SmallInteger, nullable=False, default=200))
    status: str = Field(sa_column=Column(sa.String(16), nullable=False, index=True))
    current_step_index: int = Field(default=0, sa_column=Column(sa.SmallInteger, nullable=False, default=0))
    cancel_flag: bool = Field(default=False, sa_column=Column(sa.Boolean, nullable=False, default=False))
    steps_json: list = Field(default_factory=list, sa_column=Column(JSON, nullable=False, default=list))
    error_msg: str | None = Field(default=None, sa_column=Column(Text, nullable=True, default=None))
    report_blob_path: str | None = Field(default=None, sa_column=Column(sa.String(256), nullable=True, default=None))
    pico_csv_blob_path: str | None = Field(default=None, sa_column=Column(sa.String(256), nullable=True, default=None))
    created_at: datetime = Field(default_factory=datetime_utcnow, sa_column=Column(sa.DateTime, nullable=False))
    updated_at: datetime = Field(default_factory=datetime_utcnow, sa_column=Column(sa.DateTime, nullable=False, onupdate=datetime_utcnow))
    finished_at: datetime | None = Field(default=None, sa_column=Column(sa.DateTime, nullable=True, default=None))
    __table_args__ = (
        sa.Index("ix_pipelinerun_ws_created_at_desc", "workspace_id", sa.desc("created_at")),
        sa.CheckConstraint("max_records >= 1 AND max_records <= 500", name="cc_pipelinerun_max_records"),
    )


class PipelineStepResult(SQLModel, table=True):
    __tablename__ = "pipelinestepresult"
    id: int | None = Field(default=None, primary_key=True)
    run_id: str = Field(sa_column=Column(sa.CHAR(32), sa.ForeignKey("pipelinerun.id"), nullable=False))
    step_index: int = Field(sa_column=Column(sa.SmallInteger, nullable=False))
    step_name: str = Field(sa_column=Column(sa.String(32), nullable=False))
    attempt_no: int = Field(default=1, sa_column=Column(sa.SmallInteger, nullable=False, default=1))
    status: str = Field(sa_column=Column(sa.String(8), nullable=False))
    duration_ms: int = Field(sa_column=Column(sa.Integer, nullable=False))
    n_inputs: int = Field(default=0, sa_column=Column(sa.Integer, nullable=False, default=0))
    n_outputs: int = Field(default=0, sa_column=Column(sa.Integer, nullable=False, default=0))
    payload_ref: str | None = Field(default=None, sa_column=Column(sa.String(128), nullable=True, default=None))
    error_msg: str | None = Field(default=None, sa_column=Column(Text, nullable=True, default=None))
    retryable: bool = Field(default=True, sa_column=Column(sa.Boolean, nullable=False, default=True))
    created_at: datetime = Field(default_factory=datetime_utcnow, sa_column=Column(sa.DateTime, nullable=False))
    __table_args__ = (
        UniqueConstraint("run_id", "step_index", "attempt_no", name="uq_pipelinestep_run_step_attempt"),
        sa.Index("ix_pipelinestepresult_run_id", "run_id"),
    )
