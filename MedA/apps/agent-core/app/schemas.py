from typing import Literal

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


class WorkspaceHeroAction(BaseModel):
    label: str
    target: str


class WorkspaceStageSummary(BaseModel):
    key: str
    label: str
    status: str
    task_count: int
    artifact_count: int
    target: str


class WorkspaceItemSummary(BaseModel):
    title: str
    subtitle: str
    target: str


class StageEntryAction(BaseModel):
    label: str
    target: str


class StageEntryCardSummary(BaseModel):
    key: str
    title: str
    description: str
    status: str
    target: str


class StageEntryGuidanceNote(BaseModel):
    title: str
    detail: str


class WorkspaceAssistantSummary(BaseModel):
    headline: str
    primary_action_label: str
    primary_action_target: str


class WorkspaceProjectSummary(BaseModel):
    id: int
    name: str
    workspace_key: str
    current_stage: str
    updated_at_label: str


class WorkspaceHomeResponse(BaseModel):
    project: WorkspaceProjectSummary
    hero_cta: WorkspaceHeroAction
    stages: list[WorkspaceStageSummary]
    recent_tasks: list[WorkspaceItemSummary]
    recent_artifacts: list[WorkspaceItemSummary]
    activity: list[WorkspaceItemSummary]
    assistant: WorkspaceAssistantSummary
    todos: list[WorkspaceItemSummary]


class StageEntryResponse(BaseModel):
    project: WorkspaceProjectSummary
    stage_key: str
    stage_label: str
    stage_status: str
    stage_goal: str
    primary_action: StageEntryAction
    entry_cards: list[StageEntryCardSummary]
    recent_tasks: list[WorkspaceItemSummary]
    recent_artifacts: list[WorkspaceItemSummary]
    assistant_suggestions: list[WorkspaceItemSummary]
    guidance_notes: list[StageEntryGuidanceNote]
    prisma_counts: dict | None = None
    extraction_stage_cards: list[dict] | None = None
    analysis_stage_cards: list[dict] | None = None


class SearchTermSummary(BaseModel):
    term_id: str
    label: str
    source_type: str
    selected: bool


class SearchTermGroupSummary(BaseModel):
    group_key: str
    group_label: str
    terms: list[SearchTermSummary]


class SearchExpressionBlock(BaseModel):
    block_id: str
    block_type: str
    operator: str | None = None
    term_ref: str | None = None
    children: list[str] = []
    position: int


class SearchValidationMessage(BaseModel):
    level: str
    code: str
    message: str


class SearchPreviewSummary(BaseModel):
    status: str
    coverage_hint: str
    database_scope_summary: str
    estimated_hit_band: str
    last_generated_from: str


class SearchQueryEditorResponse(BaseModel):
    project: WorkspaceProjectSummary
    stage_key: str
    query_id: int
    query_name: str
    query_version: str
    query_dirty: bool
    query_mode: str
    selected_sources: list[str]
    grouped_terms: list[SearchTermGroupSummary]
    expression_blocks: list[SearchExpressionBlock]
    validation_messages: list[SearchValidationMessage]
    preview_summary: SearchPreviewSummary


class SaveSearchQueryDraftRequest(BaseModel):
    query_id: int
    query_name: str
    selected_sources: list[str]
    grouped_terms: list[SearchTermGroupSummary]
    expression_blocks: list[SearchExpressionBlock]


class DeriveSearchQueryDraftRequest(BaseModel):
    query_id: int
    version_label: str


class SourceCatalogItemResponse(BaseModel):
    key: str
    label: str
    description: str
    supports_full_text: bool


class CatalogOptionResponse(BaseModel):
    key: str
    label: str


class SearchSourceCatalogResponse(BaseModel):
    available_sources: list[SourceCatalogItemResponse]
    search_field_options: list[CatalogOptionResponse]
    language_options: list[CatalogOptionResponse]


class AvailableSourceResponse(BaseModel):
    key: str
    label: str
    description: str
    supports_full_text: bool
    enabled: bool


class SourceImpactSummary(BaseModel):
    enabled_count: int
    coverage_hint: str
    query_impact_hint: str


class SearchSourceConfigResponse(BaseModel):
    project: WorkspaceProjectSummary
    stage_key: str
    available_sources: list[AvailableSourceResponse]
    enabled_source_keys: list[str]
    search_fields: list[str]
    year_from: int | None
    year_to: int | None
    languages: list[str]
    impact_summary: SourceImpactSummary
    validation_messages: list[SearchValidationMessage]


class SaveSearchSourceConfigRequest(BaseModel):
    enabled_source_keys: list[str]
    search_fields: list[str]
    year_from: int | None = None
    year_to: int | None = None
    languages: list[str]


class LiteratureRecordSummary(BaseModel):
    id: int
    title: str
    authors: str
    journal: str
    year: int | None
    doi: str
    pmid: str
    source_key: str
    source_label: str
    dedupe_status: Literal["unique", "duplicate", "confirmed_unique"]
    duplicate_of_id: int | None
    # --- WAVE82B_INSERT_SCREENING_SUMMARY_FIELDS 开始 ---
    screening_stage: Literal["ta", "fulltext"] | None = None
    screening_decision: Literal["include", "exclude"] | None = None
    exclude_reason_json: str | None = None
    screening_notes: str | None = None
    # --- WAVE82B_INSERT_SCREENING_SUMMARY_FIELDS 结束 ---


class LiteratureSourceCount(BaseModel):
    source_key: str
    source_label: str
    count: int


class LiteratureStats(BaseModel):
    total_count: int
    unique_count: int
    duplicate_count: int
    by_source: list[LiteratureSourceCount]
    # --- WAVE82B_INSERT_PRISMA_STATS_FIELDS 开始：PRISMA 2020 4 格 × 2 组 = 8 字段 ---
    # 4 格主计数
    prisma_identification: int | None = None
    prisma_screening: int | None = None
    prisma_eligibility: int | None = None
    prisma_included: int | None = None
    # 4 项 excluded 拆分（用于画 PRISMA 2 条横向排除线）
    prisma_ta_excluded: int | None = None
    prisma_duplicate_excluded: int | None = None
    prisma_fulltext_excluded: int | None = None
    prisma_eligibility_unknown: int | None = None
    # --- WAVE82B_INSERT_PRISMA_STATS_FIELDS 结束 ---


class LiteratureBatchSummary(BaseModel):
    id: int
    source_key: str
    source_label: str
    parsed_count: int
    duplicate_count: int
    skipped_count: int
    created_at_label: str


class ImportResultSummary(BaseModel):
    imported_count: int
    duplicate_count: int
    skipped_count: int


class LiteratureLibraryResponse(BaseModel):
    project: WorkspaceProjectSummary
    stage_key: str
    records: list[LiteratureRecordSummary]
    stats: LiteratureStats
    recent_batches: list[LiteratureBatchSummary]
    available_sources: list[SourceCatalogItemResponse]
    last_import_result: ImportResultSummary | None = None


class ImportLiteratureRequest(BaseModel):
    source_key: str
    raw_text: str


class CreateLiteratureRecordRequest(BaseModel):
    title: str
    authors: str = ""
    journal: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    abstract: str = ""
    source_key: str


SearchRunStatus = Literal[
    "pending","running","completed","partial_failed","failed","cancelled"
]
SearchRunSourceStatus = Literal["pending","running","completed","failed"]
PicoStatus = Literal["not_extracted","extracted","failed"]


class SearchSourceBreakdown(BaseModel):
    source_key: str
    source_label: str
    records_retrieved: int
    records_imported: int


class PrismaReport(BaseModel):
    identification: int
    screening: int
    eligibility: int
    included: int
    by_source: list[SearchSourceBreakdown]


class SearchRunSummary(BaseModel):
    id: int
    project_id: int
    search_query_version_id: int | None
    selected_sources: list[str]
    status: SearchRunStatus
    created_at: str
    started_at: str | None
    finished_at: str | None
    total_hits_raw: int
    total_after_dedupe: int
    prisma: PrismaReport
    eta_seconds: float | None


class SearchRunSourceSummary(BaseModel):
    id: int
    search_run_id: int
    source_key: str
    source_label: str
    status: SearchRunSourceStatus
    hits_on_source: int | None
    records_retrieved: int
    records_imported: int
    started_at: str | None
    finished_at: str | None
    error_message: str | None


class SearchRunDetail(BaseModel):
    run: SearchRunSummary
    sources: list[SearchRunSourceSummary]


class SearchRunCreatePayload(BaseModel):
    search_query_version_id: int | None = None
    query_snapshot: dict | None = None
    sources: list[str]


class SearchRunStatusPoll(BaseModel):
    status: SearchRunStatus
    finished_sources: int
    total_sources: int
    eta_seconds: float | None


class LiteraturePicoResponse(BaseModel):
    record_id: int
    population: str | None
    intervention: str | None
    comparison: str | None
    outcome: str | None
    study_type: str | None
    extraction_method: str
    confidence: float | None
    extracted_at: str


class BatchPicoPayload(BaseModel):
    record_ids: list[int]
    method: Literal["rule_baseline", "llm"] = "rule_baseline"


class BatchPicoResult(BaseModel):
    processed: int
    already_had: int
    failed: int


class PicoAutofillDraft(BaseModel):
    p: str
    i: str
    c: str
    o: str
    supporting_record_ids: list[int]


class LiteratureLibraryRequestExt(BaseModel):
    search_run_id: int | None = None
    sort: Literal["default", "relevance", "year_desc", "journal"] = "default"
    min_score: float | None = None
    page: int = 1
    page_size: int = 100
