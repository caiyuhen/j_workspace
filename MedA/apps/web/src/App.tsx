import { useMemo, useState } from "react";

import {
  createBrowserSessionStore,
  createClient,
  type ProjectSummary,
  type SearchQueryEditorSummary,
  type SearchSourceConfigSummary,
  type SessionContext,
  type StageEntrySummary,
  type WorkspaceHomeSummary,
} from "@meda/shared-sdk";

import { LoginForm } from "./components/LoginForm";
import { WorkspaceShell } from "./components/WorkspaceShell";

export default function App() {
  const sessionStore = useMemo(() => createBrowserSessionStore(), []);
  const client = useMemo(
    () => createClient("http://localhost:8000", sessionStore),
    [sessionStore],
  );
  const [session, setSession] = useState<SessionContext | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [workspaceHome, setWorkspaceHome] = useState<WorkspaceHomeSummary | null>(
    null,
  );
  const [stageEntry, setStageEntry] = useState<StageEntrySummary | null>(null);
  const [searchQueryEditor, setSearchQueryEditor] =
    useState<SearchQueryEditorSummary | null>(null);
  const [sourceConfig, setSourceConfig] =
    useState<SearchSourceConfigSummary | null>(null);

  const handleLogin = async (payload: {
    organizationSlug: string;
    userId: string;
  }) => {
    const nextSession = await client.devLogin({
      organization_slug: payload.organizationSlug,
      organization_name: "Demo Hospital",
      user_id: payload.userId,
      display_name: "Dr. Chen",
      role: "org_admin",
      client_type: "web",
    });
    const nextProjects = await client.listProjects();
    const firstProject = nextProjects[0];
    const nextWorkspaceHome = firstProject
      ? await client.getWorkspaceHome(firstProject.id)
      : null;

    setSession(nextSession);
    setProjects(nextProjects);
    setWorkspaceHome(nextWorkspaceHome);
    setStageEntry(null);
    setSearchQueryEditor(null);
    setSourceConfig(null);
  };

  const handleOpenStage = async (projectId: number, stageKey: string) => {
    const nextStageEntry = await client.getStageEntry(projectId, stageKey);
    setStageEntry(nextStageEntry);
  };

  const handleOpenSearchQueryBuilder = async (
    projectId: number,
    options?: { queryId?: number; version?: string },
  ) => {
    const nextEditor = await client.getSearchQueryEditor(projectId, options);
    setSearchQueryEditor(nextEditor);
  };

  const handleSaveSearchQueryDraft = async (projectId: number) => {
    if (searchQueryEditor === null) {
      return;
    }

    const nextEditor = await client.saveSearchQueryDraft(projectId, {
      query_id: searchQueryEditor.query_id,
      query_name: searchQueryEditor.query_name,
      selected_sources: searchQueryEditor.selected_sources,
      grouped_terms: searchQueryEditor.grouped_terms,
      expression_blocks: searchQueryEditor.expression_blocks,
    });
    setSearchQueryEditor(nextEditor);
  };

  const handleSaveSearchQueryVersion = async (projectId: number) => {
    if (searchQueryEditor === null) {
      return;
    }

    const nextEditor = await client.saveSearchQueryVersion(projectId, {
      query_id: searchQueryEditor.query_id,
      query_name: searchQueryEditor.query_name,
      selected_sources: searchQueryEditor.selected_sources,
      grouped_terms: searchQueryEditor.grouped_terms,
      expression_blocks: searchQueryEditor.expression_blocks,
    });
    setSearchQueryEditor(nextEditor);
  };

  const handleDeriveSearchQueryDraft = async (
    projectId: number,
    queryId: number,
    versionLabel: string,
  ) => {
    const nextEditor = await client.deriveSearchQueryDraft(
      projectId,
      queryId,
      versionLabel,
    );
    setSearchQueryEditor(nextEditor);
  };

  const handleOpenSourceConfig = async (projectId: number) => {
    const nextConfig = await client.getSearchSourceConfig(projectId);
    setSourceConfig(nextConfig);
  };

  const handleSaveSourceConfig = async (
    projectId: number,
    payload: {
      enabled_source_keys: string[];
      search_fields: string[];
      year_from: number | null;
      year_to: number | null;
      languages: string[];
    },
  ) => {
    const nextConfig = await client.saveSearchSourceConfig(projectId, payload);
    setSourceConfig(nextConfig);
  };

  if (session === null) {
    return <LoginForm onSubmit={handleLogin} />;
  }

  if (workspaceHome === null) {
    return <main>Workspace unavailable.</main>;
  }

  return (
    <WorkspaceShell
      session={session}
      projects={projects}
      workspaceHome={workspaceHome}
      stageEntry={stageEntry}
      searchQueryEditor={searchQueryEditor}
      onOpenStage={handleOpenStage}
      onOpenSearchQueryBuilder={handleOpenSearchQueryBuilder}
      onSaveSearchQueryDraft={handleSaveSearchQueryDraft}
      onSaveSearchQueryVersion={handleSaveSearchQueryVersion}
      onDeriveSearchQueryDraft={handleDeriveSearchQueryDraft}
      sourceConfig={sourceConfig}
      onOpenSourceConfig={handleOpenSourceConfig}
      onSaveSourceConfig={handleSaveSourceConfig}
    />
  );
}
