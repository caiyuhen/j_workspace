import { jsx as _jsx } from "react/jsx-runtime";
import { useMemo, useState } from "react";
import { createBrowserSessionStore, createClient, getSearchRunCsvUrl, } from "@meda/shared-sdk";
import { LoginForm } from "./components/LoginForm";
import { WorkspaceShell } from "./components/WorkspaceShell";
const API_BASE_URL = "http://localhost:8000";
export default function App() {
    const sessionStore = useMemo(() => createBrowserSessionStore(), []);
    const client = useMemo(() => createClient(API_BASE_URL, sessionStore), [sessionStore]);
    const [session, setSession] = useState(null);
    const [projects, setProjects] = useState([]);
    const [workspaceHome, setWorkspaceHome] = useState(null);
    const [stageEntry, setStageEntry] = useState(null);
    const [searchQueryEditor, setSearchQueryEditor] = useState(null);
    const [sourceConfig, setSourceConfig] = useState(null);
    const [sourceCatalog, setSourceCatalog] = useState(null);
    const [literatureLibrary, setLiteratureLibrary] = useState(null);
    const [searchRuns, setSearchRuns] = useState(null);
    const [searchRunDetail, setSearchRunDetail] = useState(null);
    const [currentRunId, setCurrentRunId] = useState(null);
    const handleLogin = async (payload) => {
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
        setLiteratureLibrary(null);
        setSearchRuns(null);
        setSearchRunDetail(null);
    };
    const handleOpenStage = async (projectId, stageKey) => {
        const nextStageEntry = await client.getStageEntry(projectId, stageKey);
        setStageEntry(nextStageEntry);
        if (stageKey === "search") {
            const [nextRunsRaw] = await Promise.all([
                client.listSearchRuns(projectId).catch(() => null),
            ]);
            setSearchRuns(nextRunsRaw
                ? {
                    project: nextStageEntry.project,
                    stage_key: stageKey,
                    items: nextRunsRaw.items,
                    runs: nextRunsRaw.items,
                    total: nextRunsRaw.total,
                    page: nextRunsRaw.page,
                    page_size: nextRunsRaw.pageSize,
                    pageSize: nextRunsRaw.pageSize,
                }
                : null);
        }
    };
    const handleOpenSearchQueryBuilder = async (projectId, options) => {
        const nextEditor = await client.getSearchQueryEditor(projectId, options);
        setSearchQueryEditor(nextEditor);
    };
    const handleSaveSearchQueryDraft = async (projectId) => {
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
    const handleSaveSearchQueryVersion = async (projectId) => {
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
    const handleDeriveSearchQueryDraft = async (projectId, queryId, versionLabel) => {
        const nextEditor = await client.deriveSearchQueryDraft(projectId, queryId, versionLabel);
        setSearchQueryEditor(nextEditor);
    };
    const handleOpenSourceConfig = async (projectId) => {
        const [nextConfig, nextCatalog] = await Promise.all([
            client.getSearchSourceConfig(projectId),
            client.getSourceCatalog(),
        ]);
        setSourceConfig(nextConfig);
        setSourceCatalog(nextCatalog);
    };
    const handleSaveSourceConfig = async (projectId, payload) => {
        const nextConfig = await client.saveSearchSourceConfig(projectId, payload);
        setSourceConfig(nextConfig);
    };
    const handleOpenLiteratureLibrary = async (projectId) => {
        const nextLibrary = await client.getLiteratureLibrary(projectId);
        setLiteratureLibrary(nextLibrary);
    };
    const handleImportLiterature = async (projectId, payload) => {
        const nextLibrary = await client.importLiterature(projectId, payload);
        setLiteratureLibrary(nextLibrary);
    };
    const handleConfirmLiteratureUnique = async (projectId, recordId) => {
        const nextLibrary = await client.confirmLiteratureUnique(projectId, recordId);
        setLiteratureLibrary(nextLibrary);
    };
    const handleCreateSearchRun = async () => {
        if (workspaceHome === null)
            return;
        const projectId = workspaceHome.project.id;
        const querySnapshot = searchQueryEditor !== null
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
        setSearchRuns(nextRunsRaw
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
            : null);
    };
    const handleOpenSearchRunDetail = async (projectIdOrRunId, runIdIfProjectId) => {
        const projectId = typeof runIdIfProjectId === "number" ? projectIdOrRunId : workspaceHome?.project.id ?? 0;
        const runId = typeof runIdIfProjectId === "number" ? runIdIfProjectId : projectIdOrRunId;
        if (workspaceHome === null && runIdIfProjectId === undefined)
            return;
        if (projectId === 0)
            return;
        setCurrentRunId(runId);
        try {
            const detail = await client.getSearchRun(projectId, runId);
            setSearchRunDetail(detail);
        }
        catch {
            setSearchRunDetail(null);
        }
    };
    const handleRetrySearchRunSource = async (sourceKey) => {
        if (workspaceHome === null || currentRunId === null)
            return;
        const projectId = workspaceHome.project.id;
        const _resp = await client.retrySearchRun(projectId, currentRunId);
        const detail = await client.getSearchRun(projectId, currentRunId);
        setSearchRunDetail(detail);
    };
    const handleCancelSearchRun = async () => {
        if (workspaceHome === null || currentRunId === null)
            return;
        const projectId = workspaceHome.project.id;
        await client.cancelSearchRun(projectId, currentRunId);
        const detail = await client.getSearchRun(projectId, currentRunId).catch(() => null);
        setSearchRunDetail(detail);
        const nextRunsRaw = await client.listSearchRuns(projectId).catch(() => null);
        setSearchRuns(nextRunsRaw
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
            : null);
    };
    const handleExportSearchRunCsv = () => {
        if (workspaceHome === null || currentRunId === null)
            return;
        const projectId = workspaceHome.project.id;
        const url = getSearchRunCsvUrl(API_BASE_URL, projectId, currentRunId);
        window.open(url, "_blank", "noopener,noreferrer");
    };
    if (session === null) {
        return _jsx(LoginForm, { onSubmit: handleLogin });
    }
    if (workspaceHome === null) {
        return _jsx("main", { children: "Workspace unavailable." });
    }
    return (_jsx(WorkspaceShell, { client: client, session: session, projects: projects, workspaceHome: workspaceHome, stageEntry: stageEntry, searchQueryEditor: searchQueryEditor, onOpenStage: handleOpenStage, onOpenSearchQueryBuilder: handleOpenSearchQueryBuilder, onSaveSearchQueryDraft: handleSaveSearchQueryDraft, onSaveSearchQueryVersion: handleSaveSearchQueryVersion, onDeriveSearchQueryDraft: handleDeriveSearchQueryDraft, sourceConfig: sourceConfig, sourceCatalog: sourceCatalog, onOpenSourceConfig: handleOpenSourceConfig, onSaveSourceConfig: handleSaveSourceConfig, literatureLibrary: literatureLibrary, onOpenLiteratureLibrary: handleOpenLiteratureLibrary, onImportLiterature: handleImportLiterature, onConfirmLiteratureUnique: handleConfirmLiteratureUnique, searchRuns: searchRuns, searchRunDetail: searchRunDetail, onCreateSearchRun: handleCreateSearchRun, onOpenSearchRunDetail: handleOpenSearchRunDetail, onRetrySearchRunSource: handleRetrySearchRunSource, onCancelSearchRun: handleCancelSearchRun, onExportSearchRunCsv: handleExportSearchRunCsv, navigateParams: currentRunId !== null ? { runId: currentRunId } : null }));
}
