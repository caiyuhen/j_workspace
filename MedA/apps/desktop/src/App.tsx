import { useCallback, useEffect, useMemo, useState } from "react";

import {
  createClient,
  createMemorySessionStore,
  getSearchRunCsvUrl,
  type ImportLiteraturePayload,
  type LiteratureLibrarySummary,
  type ProjectSummary,
  type SearchQueryEditorSummary,
  type SearchRunDetail,
  type SearchRunListResponse,
  type SearchSourceCatalog,
  type SearchSourceConfigSummary,
  type SessionContext,
  type StageEntryCardSummary,
  type StageEntrySummary,
  type WorkspaceHomeSummary,
  type WorkspaceItemSummary,
  type WorkspaceStageSummary,
} from "@meda/shared-sdk";

import {
  LiteratureLibraryScreen,
  SearchRunDetailScreen,
  SearchRunListScreen,
  SearchSourceConfigScreen,
  WorkspaceOneClickPubmedDemo,
  serializeRIS,
  serializeBibTeX,
  exportPRISMA,
  downloadBlob,
  downloadDataUrl,
  sanitizeFilename,
  downloadDiagnosticText,
} from "@meda/shared-ui";

import { SearchQueryBuilderScreen } from "./components/SearchQueryBuilderScreen";
import { StageEntryScreen } from "./components/StageEntryScreen";

const API_BASE_URL = "http://localhost:8000";

type Screen =
  | "home"
  | "recent-tasks"
  | "recent-artifacts"
  | "assistant"
  | "stage-entry"
  | "query-builder"
  | "source-config"
  | "literature"
  | "search-runs"
  | "search-run-detail"
  | "stage-subentry";

type SearchTabKey = "query-builder" | "source-config" | "search-runs";

const shellStyle = {
  minHeight: "100vh",
  display: "grid",
  gridTemplateColumns: "220px minmax(0, 1fr) 320px",
  gap: "24px",
  padding: "24px",
  boxSizing: "border-box" as const,
  background: "#f3f4f8",
  color: "#111827",
  fontFamily: "Inter, Arial, sans-serif",
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

const listStyle = {
  listStyle: "none",
  padding: 0,
  margin: 0,
};

const buttonStyle = {
  width: "100%",
  border: "1px solid #d0d7e2",
  background: "#ffffff",
  borderRadius: "14px",
  padding: "12px 14px",
  textAlign: "left" as const,
  cursor: "pointer",
};

const tabStyle = (active: boolean) => ({
  padding: "10px 18px",
  borderRadius: "12px 12px 0 0",
  border: active ? "1px solid #c7d2fe" : "1px solid transparent",
  borderBottom: active ? "none" : undefined,
  background: active ? "#ffffff" : "transparent",
  color: active ? "#1e1b4b" : "#475569",
  fontWeight: active ? 700 : 500,
  cursor: "pointer",
  fontSize: "14px",
});

function SummaryButton({
  item,
  onClick,
}: {
  item: WorkspaceItemSummary | WorkspaceStageSummary | StageEntryCardSummary;
  onClick: () => void;
}) {
  return (
    <button
      aria-label={"title" in item ? item.title : "label" in item ? item.label : (item as any).title ?? ""}
      style={buttonStyle}
      onClick={onClick}
    >
      <div style={{ fontWeight: 600 }}>
        {"title" in item ? item.title : "label" in item ? item.label : (item as any).title ?? ""}
      </div>
      <div style={{ marginTop: "4px", color: "#4b5563", fontSize: "14px" }}>
        {"subtitle" in item
          ? item.subtitle
          : "task_count" in item
            ? `${item.task_count} 个任务 · ${item.artifact_count} 个产物`
            : (item as any).subtitle ?? ""}
      </div>
    </button>
  );
}

function SearchStageTabs({
  activeTab,
  onTabChange,
}: {
  activeTab: SearchTabKey;
  onTabChange: (tab: SearchTabKey) => void;
}) {
  const tabs: Array<{ key: SearchTabKey; label: string }> = [
    { key: "query-builder", label: "检索式编辑器" },
    { key: "source-config", label: "检索源配置" },
    { key: "search-runs", label: "🆕 检索运行记录" },
  ];
  return (
    <div
      style={{
        display: "flex",
        gap: "4px",
        borderBottom: "1px solid #e5e7eb",
        marginBottom: "0",
      }}
    >
      {tabs.map((t) => (
        <button
          key={t.key}
          onClick={() => onTabChange(t.key)}
          style={tabStyle(activeTab === t.key)}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

export default function App() {
  const sessionStore = useMemo(() => createMemorySessionStore("meda_token"), []);
  const client = useMemo(
    () => createClient(API_BASE_URL, sessionStore),
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
  const [sourceCatalog, setSourceCatalog] =
    useState<SearchSourceCatalog | null>(null);
  const [literatureLibrary, setLiteratureLibrary] =
    useState<LiteratureLibrarySummary | null>(null);
  const [searchRuns, setSearchRuns] = useState<SearchRunListResponse | null>(null);
  const [searchRunDetail, setSearchRunDetail] = useState<SearchRunDetail | null>(null);
  const [currentRunId, setCurrentRunId] = useState<number | null>(null);
  const [screen, setScreen] = useState<Screen>("home");
  const [searchTab, setSearchTab] = useState<SearchTabKey>("query-builder");

  useEffect(() => {
    client
      .getMe()
      .then(async (nextSession) => {
        const nextProjects = await client.listProjects();
        const firstProject = nextProjects[0];
        const nextWorkspaceHome = firstProject
          ? await client.getWorkspaceHome(firstProject.id)
          : null;

        setSession(nextSession);
        setProjects(nextProjects);
        setWorkspaceHome(nextWorkspaceHome);
        setSearchQueryEditor(null);
      })
      .catch(() => {
        setSession(null);
        setProjects([]);
        setWorkspaceHome(null);
      });
  }, [client]);

  const handleCreateSearchRun = async () => {
    if (workspaceHome === null) return;
    const projectId = workspaceHome.project.id;
    const querySnapshot =
      searchQueryEditor !== null
        ? {
            query_id: searchQueryEditor.query_id,
            query_name: searchQueryEditor.query_name,
            query_version: searchQueryEditor.query_version,
            selected_sources: searchQueryEditor.selected_sources,
            grouped_terms: searchQueryEditor.grouped_terms,
            expression_blocks: searchQueryEditor.expression_blocks,
          }
        : {};
    await client.createSearchRun(projectId, {
      sources: ["pubmed", "cnki", "wanfang"],
      querySnapshot: querySnapshot,
    });
    const nextRunsRaw = await client.listSearchRuns(projectId).catch(() => null);
    setSearchRuns(
      nextRunsRaw
        ? {
            project: workspaceHome.project,
            stage_key: "search",
            items: nextRunsRaw.items,
            runs: nextRunsRaw.items,
            total: nextRunsRaw.total,
            page: nextRunsRaw.page,
            page_size: nextRunsRaw.pageSize,
            pageSize: nextRunsRaw.pageSize,
          }
        : null,
    );
  };

  const handleOpenSearchRunDetail = async (
    projectIdOrRunId: number,
    runIdIfProjectId?: number,
  ) => {
    const projectId =
      typeof runIdIfProjectId === "number" ? projectIdOrRunId : workspaceHome?.project.id ?? 0;
    const runId = typeof runIdIfProjectId === "number" ? runIdIfProjectId : projectIdOrRunId;
    if (workspaceHome === null && runIdIfProjectId === undefined) return;
    if (projectId === 0) return;
    setCurrentRunId(runId);
    try {
      const detail = await client.getSearchRun(projectId, runId);
      setSearchRunDetail(detail);
    } catch {
      setSearchRunDetail(null);
    }
    setScreen("search-run-detail");
  };

  const handleRetrySearchRunSource = async (sourceKey: string) => {
    if (workspaceHome === null || currentRunId === null) return;
    const projectId = workspaceHome.project.id;
    const _resp = await client.retrySearchRun(projectId, currentRunId);
    const detail = await client.getSearchRun(projectId, currentRunId);
    setSearchRunDetail(detail);
  };

  const handleCancelSearchRun = async () => {
    if (workspaceHome === null || currentRunId === null) return;
    const projectId = workspaceHome.project.id;
    await client.cancelSearchRun(projectId, currentRunId);
    const detail = await client.getSearchRun(projectId, currentRunId).catch(() => null);
    setSearchRunDetail(detail);
    const nextRunsRaw = await client.listSearchRuns(projectId).catch(() => null);
    setSearchRuns(
      nextRunsRaw
        ? {
            project: workspaceHome.project,
            stage_key: "search",
            items: nextRunsRaw.items,
            runs: nextRunsRaw.items,
            total: nextRunsRaw.total,
            page: nextRunsRaw.page,
            page_size: nextRunsRaw.pageSize,
            pageSize: nextRunsRaw.pageSize,
          }
        : null,
    );
  };

  const handleExportSearchRunCsv = () => {
    if (workspaceHome === null || currentRunId === null) return;
    const projectId = workspaceHome.project.id;
    const url = getSearchRunCsvUrl(API_BASE_URL, projectId, currentRunId);
    window.open(url, "_blank", "noopener,noreferrer");
  };

  const YYYYMMDD = (d: Date) => {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, "0");
    const day = String(d.getDate()).padStart(2, "0");
    return `${y}${m}${day}`;
  };

  const handleExportRis = useCallback(() => {
    if (!searchRunDetail) return;
    try {
      const rows = (searchRunDetail as any).records ?? [];
      const ris = serializeRIS(rows);
      downloadBlob(
        sanitizeFilename(
          `meda_run${searchRunDetail.run.id}_${YYYYMMDD(new Date())}_n${rows.length}.ris`,
        ),
        new Blob([ris], { type: "application/x-ris" }),
      );
    } catch (e) {
      downloadDiagnosticText("desktop_ris", e, searchRunDetail?.run.id ?? null, {
        count: (searchRunDetail as any).records?.length,
      });
    }
  }, [searchRunDetail]);

  const handleExportBibTeX = useCallback(() => {
    if (!searchRunDetail) return;
    try {
      const rows = (searchRunDetail as any).records ?? [];
      const bib = serializeBibTeX(rows);
      downloadBlob(
        sanitizeFilename(
          `meda_run${searchRunDetail.run.id}_${YYYYMMDD(new Date())}_n${rows.length}.bib`,
        ),
        new Blob([bib], { type: "application/x-bibtex" }),
      );
    } catch (e) {
      downloadDiagnosticText("desktop_bibtex", e, searchRunDetail?.run.id ?? null, {
        count: (searchRunDetail as any).records?.length,
      });
    }
  }, [searchRunDetail]);

  const handleExportPRISMA = useCallback(async () => {
    if (!searchRunDetail) return;
    try {
      const { svgBlob, pngDataUrl } = await exportPRISMA();
      const countN = ((searchRunDetail as any).records ?? []).length;
      downloadBlob(
        sanitizeFilename(
          `meda_run${searchRunDetail.run.id}_${YYYYMMDD(new Date())}_n${countN}_prisma.svg`,
        ),
        svgBlob,
      );
      if (pngDataUrl) {
        downloadDataUrl(
          sanitizeFilename(
            `meda_run${searchRunDetail.run.id}_${YYYYMMDD(new Date())}_n${countN}_prisma.png`,
          ),
          pngDataUrl,
        );
      }
    } catch (e) {
      downloadDiagnosticText("desktop_prisma", e, searchRunDetail?.run.id ?? null, {
        count: (searchRunDetail as any).records?.length,
      });
    }
  }, [searchRunDetail]);

  if (session === null || workspaceHome === null) {
    return <main>Desktop session unavailable.</main>;
  }

  if (screen === "recent-tasks") {
    return <main style={{ padding: "24px" }}>最近任务承接页</main>;
  }

  if (screen === "recent-artifacts") {
    return <main style={{ padding: "24px" }}>最近产物承接页</main>;
  }

  if (screen === "assistant") {
    return <main style={{ padding: "24px" }}>右侧助手触发面板</main>;
  }

  if (screen === "stage-subentry") {
    return <main style={{ padding: "24px" }}>阶段子入口承接页</main>;
  }

  if (screen === "search-run-detail") {
    return (
      <main style={shellStyle}>
        <section
          style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
            >
              MEDA DESKTOP
            </div>
            <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
              MedA Desktop Workspace
            </h1>
          </div>

          <nav aria-label="主导航">
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
                <li key={item}>
                  <div
                    style={{
                      borderRadius: "12px",
                      padding: "10px 12px",
                      background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                      color: item === "工作台" ? "#3730a3" : "#334155",
                      fontWeight: item === "工作台" ? 600 : 500,
                    }}
                  >
                    {item}
                  </div>
                </li>
              ))}
            </ul>
          </nav>

          <section>
            <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {projects.map((project) => (
                <li key={project.id}>
                  <div
                    style={{
                      border:
                        project.id === workspaceHome.project.id
                          ? "1px solid #c7d2fe"
                          : "1px solid #e5e7eb",
                      background:
                        project.id === workspaceHome.project.id
                          ? "#f8faff"
                          : "#ffffff",
                      borderRadius: "14px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{project.name}</div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {project.workspace_key}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </section>

        <SearchRunDetailScreen
          detail={searchRunDetail}
          onBackToRunList={() => setScreen("search-runs")}
          onRetrySource={handleRetrySearchRunSource}
          onCancelRun={handleCancelSearchRun}
          onCsvExport={handleExportSearchRunCsv}
          onRisExport={handleExportRis}
          onBibTeXExport={handleExportBibTeX}
          onPRISMAExport={handleExportPRISMA}
        />
      </main>
    );
  }

  if (screen === "search-runs") {
    return (
      <main style={shellStyle}>
        <section
          style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
            >
              MEDA DESKTOP
            </div>
            <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
              MedA Desktop Workspace
            </h1>
          </div>

          <nav aria-label="主导航">
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
                <li key={item}>
                  <div
                    style={{
                      borderRadius: "12px",
                      padding: "10px 12px",
                      background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                      color: item === "工作台" ? "#3730a3" : "#334155",
                      fontWeight: item === "工作台" ? 600 : 500,
                    }}
                  >
                    {item}
                  </div>
                </li>
              ))}
            </ul>
          </nav>

          <section>
            <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {projects.map((project) => (
                <li key={project.id}>
                  <div
                    style={{
                      border:
                        project.id === workspaceHome.project.id
                          ? "1px solid #c7d2fe"
                          : "1px solid #e5e7eb",
                      background:
                        project.id === workspaceHome.project.id
                          ? "#f8faff"
                          : "#ffffff",
                      borderRadius: "14px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{project.name}</div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {project.workspace_key}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </section>

        <SearchRunListScreen
          runs={searchRuns}
          editor={searchQueryEditor}
          onBackToStageEntry={() => setScreen("stage-entry")}
          onCreateRun={handleCreateSearchRun}
          onOpenRunDetail={(runId) =>
            handleOpenSearchRunDetail(workspaceHome.project.id, runId)
          }
        />
      </main>
    );
  }

  if (screen === "stage-entry") {
    if (stageEntry === null) {
      return <main style={{ padding: "24px" }}>科研流程模块入口页</main>;
    }

    if (stageEntry.stage_key === "search") {
      return (
        <main style={shellStyle}>
          <section
            style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
          >
            <div>
              <div
                style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
              >
                MEDA DESKTOP
              </div>
              <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
                MedA Desktop Workspace
              </h1>
            </div>

            <nav aria-label="主导航">
              <ul
                style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
              >
                {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
                  <li key={item}>
                    <div
                      style={{
                        borderRadius: "12px",
                        padding: "10px 12px",
                        background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                        color: item === "工作台" ? "#3730a3" : "#334155",
                        fontWeight: item === "工作台" ? 600 : 500,
                      }}
                    >
                      {item}
                    </div>
                  </li>
                ))}
              </ul>
            </nav>

            <section>
              <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
              <ul
                style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
              >
                {projects.map((project) => (
                  <li key={project.id}>
                    <div
                      style={{
                        border:
                          project.id === workspaceHome.project.id
                            ? "1px solid #c7d2fe"
                            : "1px solid #e5e7eb",
                        background:
                          project.id === workspaceHome.project.id
                            ? "#f8faff"
                            : "#ffffff",
                        borderRadius: "14px",
                        padding: "12px 14px",
                      }}
                    >
                      <div style={{ fontWeight: 600 }}>{project.name}</div>
                      <div
                        style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                      >
                        {project.workspace_key}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </section>

          <section style={{ display: "flex", flexDirection: "column", gap: "0" }}>
            <section style={{ ...panelStyle, paddingBottom: "0", borderRadius: "20px 20px 0 0", borderBottom: "none" }}>
              <div style={{ color: "#6b7280", fontSize: "13px" }}>
                {stageEntry.project.name}
              </div>
              <h2 style={{ margin: "8px 0 12px", fontSize: "30px" }}>
                {stageEntry.stage_label}阶段
              </h2>
              <p style={{ margin: "0 0 8px" }}>当前状态：{stageEntry.stage_status}</p>
              <p style={{ margin: 0 }}>{stageEntry.stage_goal}</p>
              <button
                style={{
                  marginTop: "16px",
                  border: "none",
                  borderRadius: "999px",
                  background: "#111827",
                  color: "#f9fafb",
                  padding: "10px 16px",
                  cursor: "pointer",
                  fontWeight: 600,
                }}
                onClick={async () => {
                  if (searchTab === "query-builder") {
                    setSearchQueryEditor(
                      await client.getSearchQueryEditor(workspaceHome.project.id),
                    );
                    setScreen("query-builder");
                  } else if (searchTab === "source-config") {
                    const [nextConfig, nextCatalog] = await Promise.all([
                      client.getSearchSourceConfig(workspaceHome.project.id),
                      client.getSourceCatalog(),
                    ]);
                    setSourceConfig(nextConfig);
                    setSourceCatalog(nextCatalog);
                    setScreen("source-config");
                  } else if (searchTab === "search-runs") {
                    setScreen("search-runs");
                  }
                }}
              >
                {stageEntry.primary_action.label}
              </button>
              <div style={{ marginTop: "20px" }}>
                <SearchStageTabs
                  activeTab={searchTab}
                  onTabChange={(t) => setSearchTab(t)}
                />
              </div>
            </section>
            <section style={{ ...panelStyle, borderRadius: "20px" }}>
              <div style={{ display: searchTab === "query-builder" ? undefined : "none" }}>
                {searchQueryEditor !== null ? (
                  <SearchQueryBuilderScreen
                    editor={searchQueryEditor}
                    onBackToStageEntry={() => {}}
                    onSaveDraft={async () => {
                      setSearchQueryEditor(
                        await client.saveSearchQueryDraft(workspaceHome.project.id, {
                          query_id: searchQueryEditor.query_id,
                          query_name: searchQueryEditor.query_name,
                          selected_sources: searchQueryEditor.selected_sources,
                          grouped_terms: searchQueryEditor.grouped_terms,
                          expression_blocks: searchQueryEditor.expression_blocks,
                        }),
                      );
                    }}
                    onSaveVersion={async () => {
                      setSearchQueryEditor(
                        await client.saveSearchQueryVersion(workspaceHome.project.id, {
                          query_id: searchQueryEditor.query_id,
                          query_name: searchQueryEditor.query_name,
                          selected_sources: searchQueryEditor.selected_sources,
                          grouped_terms: searchQueryEditor.grouped_terms,
                          expression_blocks: searchQueryEditor.expression_blocks,
                        }),
                      );
                    }}
                  />
                ) : (
                  <div style={{ padding: "40px 0", textAlign: "center", color: "#6b7280" }}>
                    加载中…
                  </div>
                )}
              </div>
              <div style={{ display: searchTab === "source-config" ? undefined : "none" }}>
                {sourceConfig !== null ? (
                  <SearchSourceConfigScreen
                    config={sourceConfig}
                    searchFieldOptions={sourceCatalog?.search_field_options ?? []}
                    languageOptions={sourceCatalog?.language_options ?? []}
                    onBackToStageEntry={() => {}}
                    onSave={async (payload) => {
                      setSourceConfig(
                        await client.saveSearchSourceConfig(
                          workspaceHome.project.id,
                          payload,
                        ),
                      );
                    }}
                  />
                ) : (
                  <div style={{ padding: "40px 0", textAlign: "center", color: "#6b7280" }}>
                    加载中…
                  </div>
                )}
              </div>
              <div style={{ display: searchTab === "search-runs" ? undefined : "none" }}>
                <SearchRunListScreen
                  runs={searchRuns}
                  editor={searchQueryEditor}
                  onBackToStageEntry={() => {}}
                  onCreateRun={handleCreateSearchRun}
                  onOpenRunDetail={(runId) =>
                    handleOpenSearchRunDetail(workspaceHome.project.id, runId)
                  }
                />
              </div>
            </section>
            <section style={{ ...panelStyle, marginTop: "20px" }}>
              <h3 style={{ marginTop: 0 }}>子入口导航</h3>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                  gap: "12px",
                }}
              >
                {stageEntry.entry_cards.map((card) => (
                  <SummaryButton
                    key={card.key}
                    item={card}
                    onClick={async () => {
                      if (card.key === "query-builder") {
                        const nextEditor = await client.getSearchQueryEditor(
                          workspaceHome.project.id,
                        );
                        setSearchQueryEditor(nextEditor);
                        setScreen("query-builder");
                        return;
                      }
                      if (card.key === "sources") {
                        const [nextConfig, nextCatalog] = await Promise.all([
                          client.getSearchSourceConfig(workspaceHome.project.id),
                          client.getSourceCatalog(),
                        ]);
                        setSourceConfig(nextConfig);
                        setSourceCatalog(nextCatalog);
                        setScreen("source-config");
                        return;
                      }
                      if (card.key === "literature") {
                        const nextLibrary = await client.getLiteratureLibrary(
                          workspaceHome.project.id,
                        );
                        setLiteratureLibrary(nextLibrary);
                        setScreen("literature");
                        return;
                      }
                      if (card.key === "search-runs") {
                        setScreen("search-runs");
                        return;
                      }
                      setScreen("stage-subentry");
                    }}
                  />
                ))}
              </div>
            </section>
            <section style={{ ...panelStyle, marginTop: "20px" }}>
              <WorkspaceOneClickPubmedDemo
                client={client}
                session={session}
                workspaceHomeProjectId={workspaceHome?.project?.id}
                onRunCreated={(rid, pid) => handleOpenSearchRunDetail(pid, rid)}
                onErrorToast={alert}
                onProjectCreatedToast={(n) =>
                  console.info(`[demo] auto-created project: ${n}`)
                }
              />
            </section>
            <section
              style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                gap: "20px",
                marginTop: "20px",
              }}
            >
              <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>最近任务</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {stageEntry.recent_tasks.map((task) => (
                    <SummaryButton
                      key={task.title}
                      item={task}
                      onClick={() => setScreen("recent-tasks")}
                    />
                  ))}
                </div>
              </div>
              <div style={panelStyle}>
                <h3 style={{ marginTop: 0 }}>最近产物</h3>
                <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                  {stageEntry.recent_artifacts.map((artifact) => (
                    <SummaryButton
                      key={artifact.title}
                      item={artifact}
                      onClick={() => setScreen("recent-artifacts")}
                    />
                  ))}
                </div>
              </div>
            </section>
          </section>

          <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            <section style={panelStyle}>
              <h2 style={{ marginTop: 0 }}>阶段助手 + 下一步建议</h2>
              <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
                {stageEntry.assistant_suggestions.map((item) => (
                  <SummaryButton
                    key={item.title}
                    item={item}
                    onClick={() => setScreen("assistant")}
                  />
                ))}
              </div>
            </section>
            <section style={panelStyle}>
              <h2 style={{ marginTop: 0 }}>阶段提示</h2>
              <ul style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }}>
                {stageEntry.guidance_notes.map((note) => (
                  <li
                    key={note.title}
                    style={{
                      border: "1px solid #e5e7eb",
                      borderRadius: "14px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{note.title}</div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "14px" }}
                    >
                      {note.detail}
                    </div>
                  </li>
                ))}
              </ul>
            </section>
          </aside>
        </main>
      );
    }

    return (
      <main style={shellStyle}>
        <section
          style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
            >
              MEDA DESKTOP
            </div>
            <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
              MedA Desktop Workspace
            </h1>
          </div>

          <nav aria-label="主导航">
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
                <li key={item}>
                  <div
                    style={{
                      borderRadius: "12px",
                      padding: "10px 12px",
                      background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                      color: item === "工作台" ? "#3730a3" : "#334155",
                      fontWeight: item === "工作台" ? 600 : 500,
                    }}
                  >
                    {item}
                  </div>
                </li>
              ))}
            </ul>
          </nav>

          <section>
            <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {projects.map((project) => (
                <li key={project.id}>
                  <div
                    style={{
                      border:
                        project.id === workspaceHome.project.id
                          ? "1px solid #c7d2fe"
                          : "1px solid #e5e7eb",
                      background:
                        project.id === workspaceHome.project.id
                          ? "#f8faff"
                          : "#ffffff",
                      borderRadius: "14px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{project.name}</div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {project.workspace_key}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </section>

        <StageEntryScreen
          stageEntry={stageEntry}
          onOpenPrimaryAction={async () => {
            setSearchQueryEditor(
              await client.getSearchQueryEditor(workspaceHome.project.id),
            );
            setScreen("query-builder");
          }}
          onOpenTaskPage={() => setScreen("recent-tasks")}
          onOpenArtifactPage={() => setScreen("recent-artifacts")}
          onOpenAssistantAction={() => setScreen("assistant")}
          onOpenEntryCard={async (entryKey) => {
            if (entryKey === "query-builder") {
              setSearchQueryEditor(
                await client.getSearchQueryEditor(workspaceHome.project.id),
              );
              setScreen("query-builder");
              return;
            }

            if (entryKey === "sources") {
              const [nextConfig, nextCatalog] = await Promise.all([
                client.getSearchSourceConfig(workspaceHome.project.id),
                client.getSourceCatalog(),
              ]);
              setSourceConfig(nextConfig);
              setSourceCatalog(nextCatalog);
              setScreen("source-config");
              return;
            }

            if (entryKey === "literature") {
              setLiteratureLibrary(
                await client.getLiteratureLibrary(workspaceHome.project.id),
              );
              setScreen("literature");
              return;
            }

            if (entryKey === "search-runs") {
              setScreen("search-runs");
              return;
            }

            setScreen("stage-subentry");
          }}
        />
      </main>
    );
  }

  if (screen === "query-builder") {
    return (
      <main style={shellStyle}>
        <section
          style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
            >
              MEDA DESKTOP
            </div>
            <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
              MedA Desktop Workspace
            </h1>
          </div>

          <nav aria-label="主导航">
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
                <li key={item}>
                  <div
                    style={{
                      borderRadius: "12px",
                      padding: "10px 12px",
                      background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                      color: item === "工作台" ? "#3730a3" : "#334155",
                      fontWeight: item === "工作台" ? 600 : 500,
                    }}
                  >
                    {item}
                  </div>
                </li>
              ))}
            </ul>
          </nav>

          <section>
            <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {projects.map((project) => (
                <li key={project.id}>
                  <div
                    style={{
                      border:
                        project.id === workspaceHome.project.id
                          ? "1px solid #c7d2fe"
                          : "1px solid #e5e7eb",
                      background:
                        project.id === workspaceHome.project.id
                          ? "#f8faff"
                          : "#ffffff",
                      borderRadius: "14px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{project.name}</div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {project.workspace_key}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </section>

        {searchQueryEditor !== null ? (
          <SearchQueryBuilderScreen
            editor={searchQueryEditor}
            onBackToStageEntry={() => setScreen("stage-entry")}
            onSaveDraft={async () => {
              setSearchQueryEditor(
                await client.saveSearchQueryDraft(workspaceHome.project.id, {
                  query_id: searchQueryEditor.query_id,
                  query_name: searchQueryEditor.query_name,
                  selected_sources: searchQueryEditor.selected_sources,
                  grouped_terms: searchQueryEditor.grouped_terms,
                  expression_blocks: searchQueryEditor.expression_blocks,
                }),
              );
            }}
            onSaveVersion={async () => {
              setSearchQueryEditor(
                await client.saveSearchQueryVersion(workspaceHome.project.id, {
                  query_id: searchQueryEditor.query_id,
                  query_name: searchQueryEditor.query_name,
                  selected_sources: searchQueryEditor.selected_sources,
                  grouped_terms: searchQueryEditor.grouped_terms,
                  expression_blocks: searchQueryEditor.expression_blocks,
                }),
              );
            }}
          />
        ) : (
          <section style={panelStyle}>
            <div style={{ padding: "40px 0", textAlign: "center", color: "#6b7280" }}>
              加载中…
            </div>
          </section>
        )}
      </main>
    );
  }

  if (screen === "source-config") {
    return (
      <main style={shellStyle}>
        <section
          style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
            >
              MEDA DESKTOP
            </div>
            <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
              MedA Desktop Workspace
            </h1>
          </div>

          <nav aria-label="主导航">
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
                <li key={item}>
                  <div
                    style={{
                      borderRadius: "12px",
                      padding: "10px 12px",
                      background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                      color: item === "工作台" ? "#3730a3" : "#334155",
                      fontWeight: item === "工作台" ? 600 : 500,
                    }}
                  >
                    {item}
                  </div>
                </li>
              ))}
            </ul>
          </nav>

          <section>
            <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {projects.map((project) => (
                <li key={project.id}>
                  <div
                    style={{
                      border:
                        project.id === workspaceHome.project.id
                          ? "1px solid #c7d2fe"
                          : "1px solid #e5e7eb",
                      background:
                        project.id === workspaceHome.project.id
                          ? "#f8faff"
                          : "#ffffff",
                      borderRadius: "14px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{project.name}</div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {project.workspace_key}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </section>

        {sourceConfig !== null ? (
          <SearchSourceConfigScreen
            config={sourceConfig}
            searchFieldOptions={sourceCatalog?.search_field_options ?? []}
            languageOptions={sourceCatalog?.language_options ?? []}
            onBackToStageEntry={() => setScreen("stage-entry")}
            onSave={async (payload) => {
              setSourceConfig(
                await client.saveSearchSourceConfig(
                  workspaceHome.project.id,
                  payload,
                ),
              );
            }}
          />
        ) : (
          <section style={panelStyle}>
            <div style={{ padding: "40px 0", textAlign: "center", color: "#6b7280" }}>
              加载中…
            </div>
          </section>
        )}
      </main>
    );
  }

  if (screen === "literature") {
    return (
      <main style={shellStyle}>
        <section
          style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
        >
          <div>
            <div
              style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
            >
              MEDA DESKTOP
            </div>
            <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
              MedA Desktop Workspace
            </h1>
          </div>

          <nav aria-label="主导航">
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
                <li key={item}>
                  <div
                    style={{
                      borderRadius: "12px",
                      padding: "10px 12px",
                      background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                      color: item === "工作台" ? "#3730a3" : "#334155",
                      fontWeight: item === "工作台" ? 600 : 500,
                    }}
                  >
                    {item}
                  </div>
                </li>
              ))}
            </ul>
          </nav>

          <section>
            <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
            <ul
              style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
            >
              {projects.map((project) => (
                <li key={project.id}>
                  <div
                    style={{
                      border:
                        project.id === workspaceHome.project.id
                          ? "1px solid #c7d2fe"
                          : "1px solid #e5e7eb",
                      background:
                        project.id === workspaceHome.project.id
                          ? "#f8faff"
                          : "#ffffff",
                      borderRadius: "14px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ fontWeight: 600 }}>{project.name}</div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {project.workspace_key}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          </section>
        </section>

        {literatureLibrary !== null ? (
          <LiteratureLibraryScreen
            library={literatureLibrary}
            onBackToStageEntry={() => setScreen("stage-entry")}
            onImport={async (payload: ImportLiteraturePayload) => {
              setLiteratureLibrary(
                await client.importLiterature(workspaceHome.project.id, payload),
              );
            }}
            onConfirmUnique={async (recordId) => {
              setLiteratureLibrary(
                await client.confirmLiteratureUnique(
                  workspaceHome.project.id,
                  recordId,
                ),
              );
            }}
          />
        ) : (
          <section style={panelStyle}>
            <div style={{ padding: "40px 0", textAlign: "center", color: "#6b7280" }}>
              加载中…
            </div>
          </section>
        )}
      </main>
    );
  }

  return (
    <main style={shellStyle}>
      <section
        style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
      >
        <div>
          <div
            style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
          >
            MEDA DESKTOP
          </div>
          <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>
            MedA Desktop Workspace
          </h1>
        </div>

        <nav aria-label="主导航">
          <ul
            style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
          >
            {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
              <li key={item}>
                <div
                  style={{
                    borderRadius: "12px",
                    padding: "10px 12px",
                    background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                    color: item === "工作台" ? "#3730a3" : "#334155",
                    fontWeight: item === "工作台" ? 600 : 500,
                  }}
                >
                  {item}
                </div>
              </li>
            ))}
          </ul>
        </nav>

        <section>
          <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
          <ul
            style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
          >
            {projects.map((project) => (
              <li key={project.id}>
                <div
                  style={{
                    border:
                      project.id === workspaceHome.project.id
                        ? "1px solid #c7d2fe"
                        : "1px solid #e5e7eb",
                    background:
                      project.id === workspaceHome.project.id
                        ? "#f8faff"
                        : "#ffffff",
                    borderRadius: "14px",
                    padding: "12px 14px",
                  }}
                >
                  <div style={{ fontWeight: 600 }}>{project.name}</div>
                  <div
                    style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                  >
                    {project.workspace_key}
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </section>
      </section>

      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "16px",
              alignItems: "flex-start",
            }}
          >
            <div>
              <div style={{ color: "#6b7280", fontSize: "13px" }}>项目工作台首页</div>
              <h2 style={{ margin: "8px 0 12px", fontSize: "30px" }}>
                {workspaceHome.project.name}
              </h2>
              <p style={{ margin: "0 0 8px" }}>当前机构：{session.organization.name}</p>
              <p style={{ margin: 0 }}>当前阶段：{workspaceHome.project.current_stage}</p>
            </div>
            <div style={{ minWidth: "180px", textAlign: "right" }}>
              <div style={{ color: "#6b7280", fontSize: "13px" }}>
                欢迎，{session.user.display_name}
              </div>
              <div style={{ marginTop: "8px", fontSize: "13px", color: "#4b5563" }}>
                {workspaceHome.project.updated_at_label}
              </div>
            </div>
          </div>

          <div
            style={{
              marginTop: "20px",
              padding: "16px",
              borderRadius: "18px",
              background: "linear-gradient(135deg, #111827 0%, #1f2937 100%)",
              color: "#f9fafb",
            }}
          >
            <div style={{ fontSize: "13px", opacity: 0.84 }}>当前项目空间</div>
            <div style={{ marginTop: "6px", fontSize: "15px" }}>
              {workspaceHome.project.workspace_key}
            </div>
            <button
              style={{
                marginTop: "16px",
                border: "none",
                borderRadius: "999px",
                background: "#f9fafb",
                color: "#111827",
                padding: "10px 16px",
                cursor: "pointer",
                fontWeight: 600,
              }}
              onClick={() => setScreen("recent-tasks")}
            >
              {workspaceHome.hero_cta.label}
            </button>
          </div>
        </section>

        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>研究阶段</h2>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "12px",
            }}
          >
            {workspaceHome.stages.map((stage) => (
              <SummaryButton
                key={stage.key}
                item={stage}
                onClick={async () => {
                  const nextStageEntry = await client.getStageEntry(
                    workspaceHome.project.id,
                    stage.key,
                  );
                  setStageEntry(nextStageEntry);
                  if (stage.key === "search") {
                    const [nextEditor, nextConfig, nextCatalog, nextRunsRaw] =
                      await Promise.all([
                        client.getSearchQueryEditor(workspaceHome.project.id),
                        client.getSearchSourceConfig(workspaceHome.project.id),
                        client.getSourceCatalog(),
                        client.listSearchRuns(workspaceHome.project.id).catch(() => null),
                      ]);
                    setSearchQueryEditor(nextEditor);
                    setSourceConfig(nextConfig);
                    setSourceCatalog(nextCatalog);
                    setSearchRuns(
                      nextRunsRaw
                        ? {
                            project: nextStageEntry.project,
                            stage_key: stage.key,
                            items: nextRunsRaw.items,
                            runs: nextRunsRaw.items,
                            total: nextRunsRaw.total,
                            page: nextRunsRaw.page,
                            page_size: nextRunsRaw.pageSize,
                            pageSize: nextRunsRaw.pageSize,
                          }
                        : null,
                    );
                  }
                  setScreen("stage-entry");
                }}
              />
            ))}
          </div>
        </section>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "20px",
          }}
        >
          <div style={panelStyle}>
            <h2 style={{ marginTop: 0 }}>最近任务</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {workspaceHome.recent_tasks.map((task) => (
                <SummaryButton
                  key={task.title}
                  item={task}
                  onClick={() => setScreen("recent-tasks")}
                />
              ))}
            </div>
          </div>

          <div style={panelStyle}>
            <h2 style={{ marginTop: 0 }}>最近产物</h2>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {workspaceHome.recent_artifacts.map((artifact) => (
                <SummaryButton
                  key={artifact.title}
                  item={artifact}
                  onClick={() => setScreen("recent-artifacts")}
                />
              ))}
            </div>
          </div>
        </section>

        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>协作动态</h2>
          <ul
            style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {workspaceHome.activity.map((activity) => (
              <li
                key={activity.title}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "14px",
                  padding: "12px 14px",
                }}
              >
                <div style={{ fontWeight: 600 }}>{activity.title}</div>
                <div
                  style={{ marginTop: "4px", color: "#6b7280", fontSize: "14px" }}
                >
                  {activity.subtitle}
                </div>
              </li>
            ))}
          </ul>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>{workspaceHome.assistant.headline}</h2>
          <p style={{ margin: "0 0 16px", color: "#4b5563" }}>
            基于当前研究阶段与最近产物，继续推进下一步任务。
          </p>
          <button
            style={{
              ...buttonStyle,
              background: "#111827",
              border: "none",
              color: "#f9fafb",
              textAlign: "center",
            }}
            onClick={() => setScreen("assistant")}
          >
            {workspaceHome.assistant.primary_action_label}
          </button>
        </section>

        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>待办与提醒</h2>
          <ul
            style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {workspaceHome.todos.map((todo) => (
              <li key={todo.title}>
                <SummaryButton item={todo} onClick={() => setScreen("recent-tasks")} />
              </li>
            ))}
          </ul>
        </section>
      </aside>
    </main>
  );
}
