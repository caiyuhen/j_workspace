import type { SessionStore } from "./session";
export { createBrowserSessionStore, createMemorySessionStore } from "./session";

export type ProjectSummary = {
  id: number;
  name: string;
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

  return {
    async devLogin(payload: DevLoginPayload): Promise<SessionContext> {
      const response = await fetch(`${baseUrl}/api/auth/dev-login`, {
        method: "POST",
        headers: buildHeaders(),
        body: JSON.stringify(payload),
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "login failed");
      }

      sessionStore?.setToken(data.token);
      return data;
    },

    async getMe(): Promise<SessionContext> {
      const response = await fetch(`${baseUrl}/api/auth/me`, {
        headers: buildHeaders(),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "session bootstrap failed");
      }

      return data;
    },

    async listProjects(): Promise<ProjectSummary[]> {
      const response = await fetch(`${baseUrl}/api/projects`, {
        headers: buildHeaders(),
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "project list failed");
      }

      return data;
    },

    async getWorkspaceHome(projectId: number): Promise<WorkspaceHomeSummary> {
      const response = await fetch(
        `${baseUrl}/api/workspace/projects/${projectId}/home`,
        {
          headers: buildHeaders(),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "workspace home failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "stage entry failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "search query editor failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "search query save failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "search query version failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "search query derive failed");
      }

      return data;
    },

    async getSourceCatalog(): Promise<SearchSourceCatalog> {
      const response = await fetch(
        `${baseUrl}/api/workspace/sources/catalog`,
        {
          headers: buildHeaders(),
        },
      );
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "source catalog failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "source config failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "source config save failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "literature library failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "literature import failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "literature record create failed");
      }

      return data;
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
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail ?? "literature confirm unique failed");
      }

      return data;
    },
  };
}
