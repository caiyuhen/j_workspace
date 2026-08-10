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
    config_dirty: bool
    impact_summary: SourceImpactSummary
    validation_messages: list[SearchValidationMessage]


class SaveSearchSourceConfigRequest(BaseModel):
    enabled_source_keys: list[str]
    search_fields: list[str]
    year_from: int | None = None
    year_to: int | None = None
    languages: list[str]
