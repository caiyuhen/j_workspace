import type { SessionStore } from "./session";
export { createBrowserSessionStore, createMemorySessionStore } from "./session";

export class ApiError extends Error {
  readonly statusCode: number;

  constructor(message: string, statusCode: number) {
    super(message);
    this.name = "ApiError";
    this.statusCode = statusCode;
  }
}

export type ProjectSummary = {
  id: number;
  name: string;
  workspace_key: string;
};

export type CreateProjectRequest = {
  organization_slug: string;
  owner_user_id: string;
  name: string;
  description: string;
};

export type ProjectResponse = {
  id: number;
  name: string;
  description: string;
  organization_slug: string;
  owner_user_id: string;
  workspace_key: string;
};

export type SessionContext = {
  token: string;
  user: { user_id: string; display_name: string };
  organization: { slug: string; name: string };
  role: string;
  client_type: string;
};

export type WorkspaceHeroAction = {
  label: string;
  target: string;
};

export type WorkspaceStageSummary = {
  key: string;
  label: string;
  status: string;
  task_count: number;
  artifact_count: number;
  target: string;
};

export type WorkspaceItemSummary = {
  title: string;
  subtitle: string;
  target: string;
};

export type StageEntryAction = {
  label: string;
  target: string;
};

export type StageEntryCardSummary = {
  key: string;
  title: string;
  description: string;
  status: string;
  target: string;
};

export type StageEntryGuidanceNote = {
  title: string;
  detail: string;
};

export type WorkspaceAssistantSummary = {
  headline: string;
  primary_action_label: string;
  primary_action_target: string;
};

export type WorkspaceProjectSummary = {
  id: number;
  name: string;
  workspace_key: string;
  current_stage: string;
  updated_at_label: string;
};

export type WorkspaceHomeSummary = {
  project: WorkspaceProjectSummary;
  hero_cta: WorkspaceHeroAction;
  stages: WorkspaceStageSummary[];
  recent_tasks: WorkspaceItemSummary[];
  recent_artifacts: WorkspaceItemSummary[];
  activity: WorkspaceItemSummary[];
  assistant: WorkspaceAssistantSummary;
  todos: WorkspaceItemSummary[];
};

export type StageEntrySummary = {
  project: WorkspaceProjectSummary;
  stage_key: string;
  stage_label: string;
  stage_status: string;
  stage_goal: string;
  primary_action: StageEntryAction;
  entry_cards: StageEntryCardSummary[];
  recent_tasks: WorkspaceItemSummary[];
  recent_artifacts: WorkspaceItemSummary[];
  assistant_suggestions: WorkspaceItemSummary[];
  guidance_notes: StageEntryGuidanceNote[];
};

export type SearchTermSummary = {
  term_id: string;
  label: string;
  source_type: string;
  selected: boolean;
};

export type SearchTermGroupSummary = {
  group_key: string;
  group_label: string;
  terms: SearchTermSummary[];
};

export type SearchExpressionBlock = {
  block_id: string;
  block_type: string;
  operator?: string | null;
  term_ref?: string | null;
  children: string[];
  position: number;
};

export type SearchValidationMessage = {
  level: string;
  code: string;
  message: string;
};

export type SearchPreviewSummary = {
  status: string;
  coverage_hint: string;
  database_scope_summary: string;
  estimated_hit_band: string;
  last_generated_from: string;
};

export type SearchQueryEditorSummary = {
  project: WorkspaceProjectSummary;
  stage_key: string;
  query_id: number;
  query_name: string;
  query_version: string;
  query_dirty: boolean;
  query_mode: string;
  selected_sources: string[];
  grouped_terms: SearchTermGroupSummary[];
  expression_blocks: SearchExpressionBlock[];
  validation_messages: SearchValidationMessage[];
  preview_summary: SearchPreviewSummary;
};

export type SaveSearchQueryDraftPayload = {
  query_id: number;
  query_name: string;
  selected_sources: string[];
  grouped_terms: SearchTermGroupSummary[];
  expression_blocks: SearchExpressionBlock[];
  /**
   * CNKI / 万方翻页深度。
   * 1 = 仅第 1 页 20 条；最大 3；undefined 等价于 1（后端默认）。
   * 预留字段，后续 Workspace Source Config UI 开关复用。
   */
  max_pages_cn?: 1 | 2 | 3;
};

export type DeriveSearchQueryDraftPayload = {
  query_id: number;
  version_label: string;
};

export type SourceCatalogItem = {
  key: string;
  label: string;
  description: string;
  supports_full_text: boolean;
};

export type CatalogOption = {
  key: string;
  label: string;
};

export type SearchSourceCatalog = {
  available_sources: SourceCatalogItem[];
  search_field_options: CatalogOption[];
  language_options: CatalogOption[];
};

export type AvailableSource = SourceCatalogItem & {
  enabled: boolean;
};

export type SourceImpactSummary = {
  enabled_count: number;
  coverage_hint: string;
  query_impact_hint: string;
};

export type SearchSourceConfigSummary = {
  project: WorkspaceProjectSummary;
  stage_key: string;
  available_sources: AvailableSource[];
  enabled_source_keys: string[];
  search_fields: string[];
  year_from: number | null;
  year_to: number | null;
  languages: string[];
  config_dirty: boolean;
  impact_summary: SourceImpactSummary;
  validation_messages: SearchValidationMessage[];
};

export type SaveSearchSourceConfigPayload = {
  enabled_source_keys: string[];
  search_fields: string[];
  year_from: number | null;
  year_to: number | null;
  languages: string[];
};

export type LiteratureRecordSummary = {
  id: number;
  title: string;
  authors: string;
  journal: string;
  year: number | null;
  doi: string;
  pmid: string;
  source_key: string;
  source_label: string;
  dedupe_status: string;
  duplicate_of_id: number | null;
};

export type LiteratureSourceCount = {
  source_key: string;
  source_label: string;
  count: number;
};

export type LiteratureStats = {
  total_count: number;
  unique_count: number;
  duplicate_count: number;
  by_source: LiteratureSourceCount[];
};

export type LiteratureBatchSummary = {
  id: number;
  source_key: string;
  source_label: string;
  parsed_count: number;
  duplicate_count: number;
  skipped_count: number;
  created_at_label: string;
};

export type ImportResultSummary = {
  imported_count: number;
  duplicate_count: number;
  skipped_count: number;
};

export type LiteratureLibrarySummary = {
  project: WorkspaceProjectSummary;
  stage_key: string;
  records: LiteratureRecordSummary[];
  stats: LiteratureStats;
  recent_batches: LiteratureBatchSummary[];
  available_sources: SourceCatalogItem[];
  last_import_result: ImportResultSummary | null;
};

export type ImportLiteraturePayload = {
  source_key: string;
  raw_text: string;
};

export type CreateLiteratureRecordPayload = {
  title: string;
  authors: string;
  journal: string;
  year: number | null;
  doi: string;
  pmid: string;
  abstract: string;
  source_key: string;
};

export type DevLoginPayload = {
  organization_slug: string;
  organization_name: string;
  user_id: string;
  display_name: string;
  role: string;
  client_type: string;
};

export type SearchRunStatus =
  | "pending"
  | "running"
  | "completed"
  | "partial_failed"
  | "failed"
  | "cancelled";

export type SearchRunSourceStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

export type PicoStatus = "not_extracted" | "extracted" | "failed";

export type LibrarySortKey =
  | "default"
  | "relevance"
  | "year_desc"
  | "journal";

export type SearchSourceBreakdown = {
  sourceKey: string;
  sourceLabel: string;
  recordsRetrieved: number;
  recordsImported: number;
};

export type PrismaReport = {
  identification: number;
  screening: number;
  eligibility: number;
  included: number;
  bySource: SearchSourceBreakdown[];
};

export type SearchRunSummary = {
  id: number;
  projectId: number;
  searchQueryVersionId: number | null;
  selectedSources: string[];
  status: SearchRunStatus;
  createdAt: string;
  startedAt: string | null;
  finishedAt: string | null;
  totalHitsRaw: number;
  totalAfterDedupe: number;
  prisma: PrismaReport;
  etaSeconds: number | null;
  // snake_case aliases for UI compatibility
  project_id?: number;
  search_query_version_id?: number | null;
  selected_sources?: string[];
  created_at?: string;
  started_at?: string | null;
  finished_at?: string | null;
  total_hits_raw?: number;
  total_after_dedupe?: number;
  eta_seconds?: number | null;
  sources?: Array<{
    key: string;
    label: string;
    retrieved: number;
    imported: number;
  }>;
  progress_percent?: number | null;
};

export type SearchRunSourceSummary = {
  id: number;
  searchRunId: number;
  sourceKey: string;
  sourceLabel: string;
  status: SearchRunSourceStatus;
  hitsOnSource: number | null;
  recordsRetrieved: number;
  recordsImported: number;
  startedAt: string | null;
  finishedAt: string | null;
  errorMessage: string | null;
  // snake_case aliases for UI compatibility
  search_run_id?: number;
  source_key?: string;
  source_label?: string;
  hits_on_source?: number | null;
  records_retrieved?: number;
  records_imported?: number;
  started_at?: string | null;
  finished_at?: string | null;
  error_message?: string | null;
};

export type SearchRunDetail = {
  run: SearchRunSummary;
  sources: SearchRunSourceSummary[];
};

export type SearchRunCreatePayload = {
  searchQueryVersionId?: number;
  querySnapshot?: object;
  sources: string[];
};

export type SearchRunStatusPoll = {
  status: SearchRunStatus;
  finishedSources: number;
  totalSources: number;
  etaSeconds: number | null;
};

export type LiteraturePicoResponse = {
  recordId: number;
  population?: string | null;
  intervention?: string | null;
  comparison?: string | null;
  outcome?: string | null;
  studyType?: string | null;
  extractionMethod: string;
  confidence?: number | null;
  extractedAt: string;
};

export type BatchPicoPayload = {
  recordIds: number[];
  method?: "rule_baseline" | "llm";
};

export type BatchPicoResult = {
  processed: number;
  alreadyHad: number;
  failed: number;
};

export type PicoAutofillDraft = {
  p: string;
  i: string;
  c: string;
  o: string;
  supportingRecordIds: number[];
};

export function createClient(
  baseUrl = "http://localhost:8000",
  sessionStore?: SessionStore,
) {
  const buildHeaders = () => {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };

    const token = sessionStore?.getToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }

    return headers;
  };

  const handleResponse = async <T>(
    response: Response,
    fallbackMessage: string,
  ): Promise<T> => {
    const headers =
      "headers" in response && typeof response.headers?.get === "function"
        ? response.headers
        : null;
    const contentType = headers ? headers.get("content-type") ?? "" : "";
    const isJson =
      contentType === "" ||
      contentType.toLowerCase().includes("application/json");
    if (!isJson) {
      throw new ApiError(
        `server returned non-JSON response (status ${response.status})`,
        response.status,
      );
    }

    const data = await response.json();
    if (!response.ok) {
      throw new ApiError(data.detail ?? fallbackMessage, response.status);
    }

    return data as T;
  };

  const mapSearchRunSummary = (raw: {
    id: number;
    project_id: number;
    search_query_version_id: number | null;
    selected_sources: string[];
    status: SearchRunStatus;
    created_at: string;
    started_at: string | null;
    finished_at: string | null;
    total_hits_raw: number;
    total_after_dedupe: number;
    prisma: {
      identification: number;
      screening: number;
      eligibility: number;
      included: number;
      by_source: {
        source_key: string;
        source_label: string;
        records_retrieved: number;
        records_imported: number;
      }[];
    };
    eta_seconds: number | null;
  }): SearchRunSummary => ({
    id: raw.id,
    projectId: raw.project_id,
    searchQueryVersionId: raw.search_query_version_id,
    selectedSources: raw.selected_sources,
    status: raw.status,
    createdAt: raw.created_at,
    startedAt: raw.started_at,
    finishedAt: raw.finished_at,
    totalHitsRaw: raw.total_hits_raw,
    totalAfterDedupe: raw.total_after_dedupe,
    prisma: {
      identification: raw.prisma.identification,
      screening: raw.prisma.screening,
      eligibility: raw.prisma.eligibility,
      included: raw.prisma.included,
      bySource: raw.prisma.by_source.map((bs) => ({
        sourceKey: bs.source_key,
        sourceLabel: bs.source_label,
        recordsRetrieved: bs.records_retrieved,
        recordsImported: bs.records_imported,
      })),
    },
    etaSeconds: raw.eta_seconds,
    // snake_case aliases for UI compatibility
    project_id: raw.project_id,
    search_query_version_id: raw.search_query_version_id,
    selected_sources: raw.selected_sources,
    created_at: raw.created_at,
    started_at: raw.started_at,
    finished_at: raw.finished_at,
    total_hits_raw: raw.total_hits_raw,
    total_after_dedupe: raw.total_after_dedupe,
    eta_seconds: raw.eta_seconds,
    sources: raw.prisma.by_source.map((bs) => ({
      key: bs.source_key,
      label: bs.source_label,
      retrieved: bs.records_retrieved,
      imported: bs.records_imported,
    })),
    progress_percent: null,
  });

  const mapSearchRunSourceSummary = (raw: {
    id: number;
    search_run_id: number;
    source_key: string;
    source_label: string;
    status: SearchRunSourceStatus;
    hits_on_source: number | null;
    records_retrieved: number;
    records_imported: number;
    started_at: string | null;
    finished_at: string | null;
    error_message: string | null;
  }): SearchRunSourceSummary => ({
    id: raw.id,
    searchRunId: raw.search_run_id,
    sourceKey: raw.source_key,
    sourceLabel: raw.source_label,
    status: raw.status,
    hitsOnSource: raw.hits_on_source,
    recordsRetrieved: raw.records_retrieved,
    recordsImported: raw.records_imported,
    startedAt: raw.started_at,
    finishedAt: raw.finished_at,
    errorMessage: raw.error_message,
    search_run_id: raw.search_run_id,
    source_key: raw.source_key,
    source_label: raw.source_label,
    hits_on_source: raw.hits_on_source,
    records_retrieved: raw.records_retrieved,
    records_imported: raw.records_imported,
    started_at: raw.started_at,
    finished_at: raw.finished_at,
    error_message: raw.error_message,
  });

  return {
    async devLogin(payload: DevLoginPayload): Promise<SessionContext> {
      const response = await fetch(`${baseUrl}/api/auth/dev-login`, {
        method: "POST",
        headers: buildHeaders(),
        body: JSON.stringify(payload),
      });

      const result =
        await handleResponse<SessionContext>(response, "login failed");
      sessionStore?.setToken(
        (result as unknown as { token?: string }).token ?? "",
      );
      return result;
    },

    async getMe(): Promise<SessionContext> {
      const response = await fetch(`${baseUrl}/api/auth/me`, {
        headers: buildHeaders(),
      });
      return handleResponse<SessionContext>(response, "session bootstrap failed");
    },

    async listProjects(): Promise<ProjectSummary[]> {
      const response = await fetch(`${baseUrl}/api/projects`, {
        headers: buildHeaders(),
      });
      return handleResponse<ProjectSummary[]>(response, "project list failed");
    },

    async createProject(payload: CreateProjectRequest): Promise<ProjectResponse> {
      const response = await fetch(`${baseUrl}/api/projects`, {
        method: "POST",
        headers: {
          ...buildHeaders(),
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });
      return handleResponse<ProjectResponse>(response, "project create failed");
    },

    async getWorkspaceHome(projectId: number): Promise<WorkspaceHomeSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/home`,
        {
          headers: buildHeaders(),
        },
      );
      return handleResponse<WorkspaceHomeSummary>(
        response,
        "workspace home failed",
      );
    },

    async getStageEntry(
      projectId: number,
      stageKey: string,
    ): Promise<StageEntrySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/${stageKey}`,
        {
          headers: buildHeaders(),
        },
      );
      return handleResponse<StageEntrySummary>(
        response,
        "stage entry failed",
      );
    },

    async getSearchQueryEditor(
      projectId: number,
      options?: { queryId?: number; version?: string },
    ): Promise<SearchQueryEditorSummary> {
      const queryString = new URLSearchParams();
      if (options?.queryId !== undefined) {
        queryString.set("query_id", String(options.queryId));
      }
      if (options?.version !== undefined) {
        queryString.set("version", options.version);
      }
      const suffix = queryString.size > 0 ? `?${queryString.toString()}` : "";

      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/query-builder${suffix}`,
        {
          headers: buildHeaders(),
        },
      );
      return handleResponse<SearchQueryEditorSummary>(
        response,
        "search query editor failed",
      );
    },

    async saveSearchQueryDraft(
      projectId: number,
      payload: SaveSearchQueryDraftPayload,
    ): Promise<SearchQueryEditorSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/query-builder/save`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      return handleResponse<SearchQueryEditorSummary>(
        response,
        "search query save failed",
      );
    },

    async saveSearchQueryVersion(
      projectId: number,
      payload: SaveSearchQueryDraftPayload,
    ): Promise<SearchQueryEditorSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/query-builder/save-as-version`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      return handleResponse<SearchQueryEditorSummary>(
        response,
        "search query version failed",
      );
    },

    async deriveSearchQueryDraft(
      projectId: number,
      queryId: number,
      versionLabel: string,
    ): Promise<SearchQueryEditorSummary> {
      const payload: DeriveSearchQueryDraftPayload = {
        query_id: queryId,
        version_label: versionLabel,
      };
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/query-builder/derive-draft`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      return handleResponse<SearchQueryEditorSummary>(
        response,
        "search query derive failed",
      );
    },

    async getSourceCatalog(): Promise<SearchSourceCatalog> {
      const response = await fetch(
        `${baseUrl}/api/workspace/sources/catalog`,
        {
          headers: buildHeaders(),
        },
      );
      return handleResponse<SearchSourceCatalog>(
        response,
        "source catalog failed",
      );
    },

    async getSearchSourceConfig(
      projectId: number,
    ): Promise<SearchSourceConfigSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/sources`,
        {
          headers: buildHeaders(),
        },
      );
      return handleResponse<SearchSourceConfigSummary>(
        response,
        "source config failed",
      );
    },

    async saveSearchSourceConfig(
      projectId: number,
      payload: SaveSearchSourceConfigPayload,
    ): Promise<SearchSourceConfigSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/sources`,
        {
          method: "PUT",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      return handleResponse<SearchSourceConfigSummary>(
        response,
        "source config save failed",
      );
    },

    async getLiteratureLibrary(
      projectId: number,
    ): Promise<LiteratureLibrarySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature`,
        {
          headers: buildHeaders(),
        },
      );
      return handleResponse<LiteratureLibrarySummary>(
        response,
        "literature library failed",
      );
    },

    async importLiterature(
      projectId: number,
      payload: ImportLiteraturePayload,
    ): Promise<LiteratureLibrarySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature/import`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      return handleResponse<LiteratureLibrarySummary>(
        response,
        "literature import failed",
      );
    },

    async createLiteratureRecord(
      projectId: number,
      payload: CreateLiteratureRecordPayload,
    ): Promise<LiteratureLibrarySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature/records`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify(payload),
        },
      );
      return handleResponse<LiteratureLibrarySummary>(
        response,
        "literature record create failed",
      );
    },

    async confirmLiteratureUnique(
      projectId: number,
      recordId: number,
    ): Promise<LiteratureLibrarySummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature/records/${recordId}/confirm-unique`,
        {
          method: "POST",
          headers: buildHeaders(),
        },
      );
      return handleResponse<LiteratureLibrarySummary>(
        response,
        "literature confirm unique failed",
      );
    },

    async createSearchRun(
      projectId: number,
      payload: SearchRunCreatePayload,
    ): Promise<SearchRunSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify({
            search_query_version_id: payload.searchQueryVersionId,
            query_snapshot: payload.querySnapshot,
            sources: payload.sources,
          }),
        },
      );
      const raw = await handleResponse<{
        id: number;
        project_id: number;
        search_query_version_id: number | null;
        selected_sources: string[];
        status: SearchRunStatus;
        created_at: string;
        started_at: string | null;
        finished_at: string | null;
        total_hits_raw: number;
        total_after_dedupe: number;
        prisma: {
          identification: number;
          screening: number;
          eligibility: number;
          included: number;
          by_source: {
            source_key: string;
            source_label: string;
            records_retrieved: number;
            records_imported: number;
          }[];
        };
        eta_seconds: number | null;
      }>(response, "search run create failed");
      return mapSearchRunSummary(raw);
    },

    async listSearchRuns(
      projectId: number,
      options: { page?: number; pageSize?: number } = {},
    ): Promise<{
      items: SearchRunSummary[];
      total: number;
      page: number;
      pageSize: number;
    }> {
      const page = options.page ?? 1;
      const pageSize = options.pageSize ?? 20;
      const queryString = new URLSearchParams({
        page: String(page),
        page_size: String(pageSize),
      });
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs?${queryString.toString()}`,
        {
          headers: buildHeaders(),
        },
      );
      const data = await handleResponse<{
        items: {
          id: number;
          project_id: number;
          search_query_version_id: number | null;
          selected_sources: string[];
          status: SearchRunStatus;
          created_at: string;
          started_at: string | null;
          finished_at: string | null;
          total_hits_raw: number;
          total_after_dedupe: number;
          prisma: {
            identification: number;
            screening: number;
            eligibility: number;
            included: number;
            by_source: {
              source_key: string;
              source_label: string;
              records_retrieved: number;
              records_imported: number;
            }[];
          };
          eta_seconds: number | null;
        }[];
        total: number;
        page: number;
        page_size: number;
      }>(response, "search run list failed");
      return {
        items: data.items.map(mapSearchRunSummary),
        total: data.total,
        page: data.page,
        pageSize: data.page_size,
      };
    },

    async getSearchRun(
      projectId: number,
      runId: number,
    ): Promise<SearchRunDetail> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}`,
        {
          headers: buildHeaders(),
        },
      );
      const raw = await handleResponse<{
        run: {
          id: number;
          project_id: number;
          search_query_version_id: number | null;
          selected_sources: string[];
          status: SearchRunStatus;
          created_at: string;
          started_at: string | null;
          finished_at: string | null;
          total_hits_raw: number;
          total_after_dedupe: number;
          prisma: {
            identification: number;
            screening: number;
            eligibility: number;
            included: number;
            by_source: {
              source_key: string;
              source_label: string;
              records_retrieved: number;
              records_imported: number;
            }[];
          };
          eta_seconds: number | null;
        };
        sources: {
          id: number;
          search_run_id: number;
          source_key: string;
          source_label: string;
          status: SearchRunSourceStatus;
          hits_on_source: number | null;
          records_retrieved: number;
          records_imported: number;
          started_at: string | null;
          finished_at: string | null;
          error_message: string | null;
        }[];
      }>(response, "search run detail failed");
      return {
        run: mapSearchRunSummary(raw.run),
        sources: raw.sources.map(mapSearchRunSourceSummary),
      };
    },

    async cancelSearchRun(
      projectId: number,
      runId: number,
    ): Promise<{ status: string }> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}/cancel`,
        {
          method: "POST",
          headers: buildHeaders(),
        },
      );
      return handleResponse<{ status: string }>(
        response,
        "search run cancel failed",
      );
    },

    async retrySearchRun(
      projectId: number,
      runId: number,
    ): Promise<{ restartedSources: number }> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}/retry`,
        {
          method: "POST",
          headers: buildHeaders(),
        },
      );
      const data = await handleResponse<{ restarted_sources: number }>(
        response,
        "search run retry failed",
      );
      return { restartedSources: data.restarted_sources };
    },

    getSearchRunCsvUrl(projectId: number, runId: number): string {
      return `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}/export.csv`;
    },

    async pollSearchRunStatus(
      projectId: number,
      runId: number,
    ): Promise<SearchRunStatusPoll> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}/status`,
        {
          headers: buildHeaders(),
        },
      );
      const raw = await handleResponse<{
        status: SearchRunStatus;
        finished_sources: number;
        total_sources: number;
        eta_seconds: number | null;
      }>(response, "search run status poll failed");
      return {
        status: raw.status,
        finishedSources: raw.finished_sources,
        totalSources: raw.total_sources,
        etaSeconds: raw.eta_seconds,
      };
    },

    async recomputeBm25(
      projectId: number,
      runId: number,
    ): Promise<{ queued: boolean }> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}/recompute-bm25`,
        {
          method: "POST",
          headers: buildHeaders(),
        },
      );
      return handleResponse<{ queued: boolean }>(
        response,
        "recompute bm25 failed",
      );
    },

    async getLiteratureLibraryExt(
      projectId: number,
      options: {
        searchRunId?: number;
        sort?: LibrarySortKey;
        minScore?: number;
      } = {},
    ): Promise<LiteratureLibrarySummary> {
      const queryString = new URLSearchParams();
      if (options.searchRunId !== undefined) {
        queryString.set("search_run_id", String(options.searchRunId));
      }
      if (options.sort !== undefined) {
        queryString.set("sort", options.sort);
      }
      if (options.minScore !== undefined) {
        queryString.set("min_score", String(options.minScore));
      }
      const suffix = queryString.size > 0 ? `?${queryString.toString()}` : "";
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature${suffix}`,
        {
          headers: buildHeaders(),
        },
      );
      return handleResponse<LiteratureLibrarySummary>(
        response,
        "literature library ext failed",
      );
    },

    async batchExtractPico(
      projectId: number,
      payload: BatchPicoPayload,
    ): Promise<BatchPicoResult> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature/records/pico:batch-extract`,
        {
          method: "POST",
          headers: buildHeaders(),
          body: JSON.stringify({
            record_ids: payload.recordIds,
            method: payload.method,
          }),
        },
      );
      const data = await handleResponse<{
        processed: number;
        already_had: number;
        failed: number;
      }>(response, "batch extract pico failed");
      return {
        processed: data.processed,
        alreadyHad: data.already_had,
        failed: data.failed,
      };
    },

    async getRecordPico(
      projectId: number,
      recordId: number,
      method?: "rule_baseline" | "llm",
    ): Promise<LiteraturePicoResponse> {
      const queryString = new URLSearchParams();
      if (method !== undefined) {
        queryString.set("method", method);
      }
      const suffix = queryString.size > 0 ? `?${queryString.toString()}` : "";
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/literature/records/${recordId}/pico${suffix}`,
        {
          headers: buildHeaders(),
        },
      );
      const raw = await handleResponse<{
        record_id: number;
        population?: string | null;
        intervention?: string | null;
        comparison?: string | null;
        outcome?: string | null;
        study_type?: string | null;
        extraction_method: string;
        confidence?: number | null;
        extracted_at: string;
      }>(response, "get record pico failed");
      return {
        recordId: raw.record_id,
        population: raw.population,
        intervention: raw.intervention,
        comparison: raw.comparison,
        outcome: raw.outcome,
        studyType: raw.study_type,
        extractionMethod: raw.extraction_method,
        confidence: raw.confidence,
        extractedAt: raw.extracted_at,
      };
    },

    async autofillPicoFromRun(
      projectId: number,
      runId: number,
    ): Promise<PicoAutofillDraft> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/stages/search/search-runs/${runId}/pico:autofill-query`,
        {
          method: "POST",
          headers: buildHeaders(),
        },
      );
      const data = await handleResponse<{
        p: string;
        i: string;
        c: string;
        o: string;
        supporting_record_ids: number[];
      }>(response, "autofill pico from run failed");
      return {
        p: data.p,
        i: data.i,
        c: data.c,
        o: data.o,
        supportingRecordIds: data.supporting_record_ids,
      };
    },
  };
}
