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
  };
}
