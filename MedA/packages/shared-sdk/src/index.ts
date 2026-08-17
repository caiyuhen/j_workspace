export { createBrowserSessionStore, createMemorySessionStore, createClient, ApiError } from "./client";
export type {
  ProjectSummary,
  WorkspaceHeroAction,
  WorkspaceStageSummary,
  WorkspaceItemSummary,
  StageEntryAction,
  StageEntryCardSummary,
  StageEntryGuidanceNote,
  WorkspaceAssistantSummary,
  WorkspaceProjectSummary,
  WorkspaceHomeSummary,
  StageEntrySummary,
  SessionContext,
  CreateProjectRequest,
  ProjectResponse,
  SearchTermSummary,
  SearchTermGroupSummary,
  SearchExpressionBlock,
  SearchValidationMessage,
  SearchPreviewSummary,
  SearchQueryEditorSummary,
  SaveSearchQueryDraftPayload,
  DeriveSearchQueryDraftPayload,
  SourceCatalogItem,
  CatalogOption,
  SearchSourceCatalog,
  AvailableSource,
  SourceImpactSummary,
  SearchSourceConfigSummary,
  SaveSearchSourceConfigPayload,
  LiteratureRecordSummary,
  LiteratureSourceCount,
  LiteratureStats,
  LiteratureBatchSummary,
  ImportResultSummary,
  LiteratureLibrarySummary,
  ImportLiteraturePayload,
  CreateLiteratureRecordPayload,
  DevLoginPayload,
  SearchRunStatus,
  SearchRunSourceStatus,
  PicoStatus,
  LibrarySortKey,
  SearchSourceBreakdown,
  PrismaReport,
  SearchRunSummary,
  SearchRunSourceSummary,
  SearchRunDetail,
  SearchRunCreatePayload,
  SearchRunStatusPoll,
  LiteraturePicoResponse,
  BatchPicoPayload,
  BatchPicoResult,
  PicoAutofillDraft,
  ScreeningStage,
  ScreeningDecision,
  ExcludeReasonJson,
  PrismaOverride,
  LiteratureStatsW82B,
} from "./client";

export function getSearchRunCsvUrl(baseUrl: string, projectId: number, runId: number): string {
  return `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}/export.csv`;
}

import type {
  WorkspaceProjectSummary as _WPS,
  SearchRunSummary as _SRS,
  SearchRunStatus as _SRS_STATUS,
} from "./client";
export type SearchRunListResponse = {
  project: _WPS;
  stage_key: string;
  items: _SRS[];
  runs: _SRS[];
  total: number;
  page: number;
  page_size: number;
  pageSize: number;
};

export type SearchRunListItem = {
  id: number;
  status: _SRS_STATUS;
  created_at: string;
  sources: Array<{
    key: string;
    retrieved: number;
    imported: number;
  }>;
  prisma: {
    identification: number;
    screening: number;
  };
  progress_percent: number | null;
};

export {
  DEMO_PRESETS,
  DEMO_PRESET_BY_KEY,
  type DemoPreset,
  type DemoPresetKey,
} from "./presets";
export {
  build_grouped_terms_from_pico,
  build_expression_from_boolean_text,
  ensureDemoProjectAndQuery,
  type EnsureDemoResult,
  type EnsureDemoOptions,
  type MedaClient,
} from "./utils/demoSeedings";
