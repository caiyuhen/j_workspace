import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useCallback, useEffect, useMemo, useState } from "react";
import { createClient, createMemorySessionStore, getSearchRunCsvUrl, } from "@meda/shared-sdk";
import { LiteratureLibraryScreen, SearchRunDetailScreen, SearchRunListScreen, SearchSourceConfigScreen, WorkspaceOneClickPubmedDemo, serializeRIS, serializeBibTeX, exportPRISMA, downloadBlob, downloadDataUrl, sanitizeFilename, downloadDiagnosticText, } from "@meda/shared-ui";
import { SearchQueryBuilderScreen } from "./components/SearchQueryBuilderScreen";
import { StageEntryScreen } from "./components/StageEntryScreen";
const API_BASE_URL = "http://localhost:8000";
const shellStyle = {
    minHeight: "100vh",
    display: "grid",
    gridTemplateColumns: "220px minmax(0, 1fr) 320px",
    gap: "24px",
    padding: "24px",
    boxSizing: "border-box",
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
    textAlign: "left",
    cursor: "pointer",
};
const tabStyle = (active) => ({
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
function SummaryButton({ item, onClick, }) {
    return (_jsxs("button", { "aria-label": "title" in item ? item.title : "label" in item ? item.label : item.title ?? "", style: buttonStyle, onClick: onClick, children: [_jsx("div", { style: { fontWeight: 600 }, children: "title" in item ? item.title : "label" in item ? item.label : item.title ?? "" }), _jsx("div", { style: { marginTop: "4px", color: "#4b5563", fontSize: "14px" }, children: "subtitle" in item
                    ? item.subtitle
                    : "task_count" in item
                        ? `${item.task_count} 个任务 · ${item.artifact_count} 个产物`
                        : item.subtitle ?? "" })] }));
}
function SearchStageTabs({ activeTab, onTabChange, }) {
    const tabs = [
        { key: "query-builder", label: "检索式编辑器" },
        { key: "source-config", label: "检索源配置" },
        { key: "search-runs", label: "🆕 检索运行记录" },
    ];
    return (_jsx("div", { style: {
            display: "flex",
            gap: "4px",
            borderBottom: "1px solid #e5e7eb",
            marginBottom: "0",
        }, children: tabs.map((t) => (_jsx("button", { onClick: () => onTabChange(t.key), style: tabStyle(activeTab === t.key), children: t.label }, t.key))) }));
}
export default function App() {
    const sessionStore = useMemo(() => createMemorySessionStore("meda_token"), []);
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
    const [screen, setScreen] = useState("home");
    const [searchTab, setSearchTab] = useState("query-builder");
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
        setScreen("search-run-detail");
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
    const YYYYMMDD = (d) => {
        const y = d.getFullYear();
        const m = String(d.getMonth() + 1).padStart(2, "0");
        const day = String(d.getDate()).padStart(2, "0");
        return `${y}${m}${day}`;
    };
    const handleExportRis = useCallback(() => {
        if (!searchRunDetail)
            return;
        try {
            const rows = searchRunDetail.records ?? [];
            const ris = serializeRIS(rows);
            downloadBlob(sanitizeFilename(`meda_run${searchRunDetail.run.id}_${YYYYMMDD(new Date())}_n${rows.length}.ris`), new Blob([ris], { type: "application/x-ris" }));
        }
        catch (e) {
            downloadDiagnosticText("desktop_ris", e, searchRunDetail?.run.id ?? null, {
                count: searchRunDetail.records?.length,
            });
        }
    }, [searchRunDetail]);
    const handleExportBibTeX = useCallback(() => {
        if (!searchRunDetail)
            return;
        try {
            const rows = searchRunDetail.records ?? [];
            const bib = serializeBibTeX(rows);
            downloadBlob(sanitizeFilename(`meda_run${searchRunDetail.run.id}_${YYYYMMDD(new Date())}_n${rows.length}.bib`), new Blob([bib], { type: "application/x-bibtex" }));
        }
        catch (e) {
            downloadDiagnosticText("desktop_bibtex", e, searchRunDetail?.run.id ?? null, {
                count: searchRunDetail.records?.length,
            });
        }
    }, [searchRunDetail]);
    const handleExportPRISMA = useCallback(async () => {
        if (!searchRunDetail)
            return;
        try {
            const { svgBlob, pngDataUrl } = await exportPRISMA();
            const countN = (searchRunDetail.records ?? []).length;
            downloadBlob(sanitizeFilename(`meda_run${searchRunDetail.run.id}_${YYYYMMDD(new Date())}_n${countN}_prisma.svg`), svgBlob);
            if (pngDataUrl) {
                downloadDataUrl(sanitizeFilename(`meda_run${searchRunDetail.run.id}_${YYYYMMDD(new Date())}_n${countN}_prisma.png`), pngDataUrl);
            }
        }
        catch (e) {
            downloadDiagnosticText("desktop_prisma", e, searchRunDetail?.run.id ?? null, {
                count: searchRunDetail.records?.length,
            });
        }
    }, [searchRunDetail]);
    if (session === null || workspaceHome === null) {
        return _jsx("main", { children: "Desktop session unavailable." });
    }
    if (screen === "recent-tasks") {
        return _jsx("main", { style: { padding: "24px" }, children: "\u6700\u8FD1\u4EFB\u52A1\u627F\u63A5\u9875" });
    }
    if (screen === "recent-artifacts") {
        return _jsx("main", { style: { padding: "24px" }, children: "\u6700\u8FD1\u4EA7\u7269\u627F\u63A5\u9875" });
    }
    if (screen === "assistant") {
        return _jsx("main", { style: { padding: "24px" }, children: "\u53F3\u4FA7\u52A9\u624B\u89E6\u53D1\u9762\u677F" });
    }
    if (screen === "stage-subentry") {
        return _jsx("main", { style: { padding: "24px" }, children: "\u9636\u6BB5\u5B50\u5165\u53E3\u627F\u63A5\u9875" });
    }
    if (screen === "search-run-detail") {
        return (_jsxs("main", { style: shellStyle, children: [_jsxs("section", { style: { ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }, children: "MEDA DESKTOP" }), _jsx("h1", { style: { margin: "8px 0 0", fontSize: "24px" }, children: "MedA Desktop Workspace" })] }), _jsx("nav", { "aria-label": "\u4E3B\u5BFC\u822A", children: _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: ["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (_jsx("li", { children: _jsx("div", { style: {
                                            borderRadius: "12px",
                                            padding: "10px 12px",
                                            background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                                            color: item === "工作台" ? "#3730a3" : "#334155",
                                            fontWeight: item === "工作台" ? 600 : 500,
                                        }, children: item }) }, item))) }) }), _jsxs("section", { children: [_jsx("h2", { style: { margin: "0 0 12px", fontSize: "16px" }, children: "\u9879\u76EE\u4E0A\u4E0B\u6587" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: projects.map((project) => (_jsx("li", { children: _jsxs("div", { style: {
                                                border: project.id === workspaceHome.project.id
                                                    ? "1px solid #c7d2fe"
                                                    : "1px solid #e5e7eb",
                                                background: project.id === workspaceHome.project.id
                                                    ? "#f8faff"
                                                    : "#ffffff",
                                                borderRadius: "14px",
                                                padding: "12px 14px",
                                            }, children: [_jsx("div", { style: { fontWeight: 600 }, children: project.name }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "13px" }, children: project.workspace_key })] }) }, project.id))) })] })] }), _jsx(SearchRunDetailScreen, { detail: searchRunDetail, onBackToRunList: () => setScreen("search-runs"), onRetrySource: handleRetrySearchRunSource, onCancelRun: handleCancelSearchRun, onCsvExport: handleExportSearchRunCsv, onRisExport: handleExportRis, onBibTeXExport: handleExportBibTeX, onPRISMAExport: handleExportPRISMA })] }));
    }
    if (screen === "search-runs") {
        return (_jsxs("main", { style: shellStyle, children: [_jsxs("section", { style: { ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }, children: "MEDA DESKTOP" }), _jsx("h1", { style: { margin: "8px 0 0", fontSize: "24px" }, children: "MedA Desktop Workspace" })] }), _jsx("nav", { "aria-label": "\u4E3B\u5BFC\u822A", children: _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: ["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (_jsx("li", { children: _jsx("div", { style: {
                                            borderRadius: "12px",
                                            padding: "10px 12px",
                                            background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                                            color: item === "工作台" ? "#3730a3" : "#334155",
                                            fontWeight: item === "工作台" ? 600 : 500,
                                        }, children: item }) }, item))) }) }), _jsxs("section", { children: [_jsx("h2", { style: { margin: "0 0 12px", fontSize: "16px" }, children: "\u9879\u76EE\u4E0A\u4E0B\u6587" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: projects.map((project) => (_jsx("li", { children: _jsxs("div", { style: {
                                                border: project.id === workspaceHome.project.id
                                                    ? "1px solid #c7d2fe"
                                                    : "1px solid #e5e7eb",
                                                background: project.id === workspaceHome.project.id
                                                    ? "#f8faff"
                                                    : "#ffffff",
                                                borderRadius: "14px",
                                                padding: "12px 14px",
                                            }, children: [_jsx("div", { style: { fontWeight: 600 }, children: project.name }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "13px" }, children: project.workspace_key })] }) }, project.id))) })] })] }), _jsx(SearchRunListScreen, { runs: searchRuns, editor: searchQueryEditor, onBackToStageEntry: () => setScreen("stage-entry"), onCreateRun: handleCreateSearchRun, onOpenRunDetail: (runId) => handleOpenSearchRunDetail(workspaceHome.project.id, runId) })] }));
    }
    if (screen === "stage-entry") {
        if (stageEntry === null) {
            return _jsx("main", { style: { padding: "24px" }, children: "\u79D1\u7814\u6D41\u7A0B\u6A21\u5757\u5165\u53E3\u9875" });
        }
        if (stageEntry.stage_key === "search") {
            return (_jsxs("main", { style: shellStyle, children: [_jsxs("section", { style: { ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }, children: "MEDA DESKTOP" }), _jsx("h1", { style: { margin: "8px 0 0", fontSize: "24px" }, children: "MedA Desktop Workspace" })] }), _jsx("nav", { "aria-label": "\u4E3B\u5BFC\u822A", children: _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: ["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (_jsx("li", { children: _jsx("div", { style: {
                                                borderRadius: "12px",
                                                padding: "10px 12px",
                                                background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                                                color: item === "工作台" ? "#3730a3" : "#334155",
                                                fontWeight: item === "工作台" ? 600 : 500,
                                            }, children: item }) }, item))) }) }), _jsxs("section", { children: [_jsx("h2", { style: { margin: "0 0 12px", fontSize: "16px" }, children: "\u9879\u76EE\u4E0A\u4E0B\u6587" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: projects.map((project) => (_jsx("li", { children: _jsxs("div", { style: {
                                                    border: project.id === workspaceHome.project.id
                                                        ? "1px solid #c7d2fe"
                                                        : "1px solid #e5e7eb",
                                                    background: project.id === workspaceHome.project.id
                                                        ? "#f8faff"
                                                        : "#ffffff",
                                                    borderRadius: "14px",
                                                    padding: "12px 14px",
                                                }, children: [_jsx("div", { style: { fontWeight: 600 }, children: project.name }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "13px" }, children: project.workspace_key })] }) }, project.id))) })] })] }), _jsxs("section", { style: { display: "flex", flexDirection: "column", gap: "0" }, children: [_jsxs("section", { style: { ...panelStyle, paddingBottom: "0", borderRadius: "20px 20px 0 0", borderBottom: "none" }, children: [_jsx("div", { style: { color: "#6b7280", fontSize: "13px" }, children: stageEntry.project.name }), _jsxs("h2", { style: { margin: "8px 0 12px", fontSize: "30px" }, children: [stageEntry.stage_label, "\u9636\u6BB5"] }), _jsxs("p", { style: { margin: "0 0 8px" }, children: ["\u5F53\u524D\u72B6\u6001\uFF1A", stageEntry.stage_status] }), _jsx("p", { style: { margin: 0 }, children: stageEntry.stage_goal }), _jsx("button", { style: {
                                            marginTop: "16px",
                                            border: "none",
                                            borderRadius: "999px",
                                            background: "#111827",
                                            color: "#f9fafb",
                                            padding: "10px 16px",
                                            cursor: "pointer",
                                            fontWeight: 600,
                                        }, onClick: async () => {
                                            if (searchTab === "query-builder") {
                                                setSearchQueryEditor(await client.getSearchQueryEditor(workspaceHome.project.id));
                                                setScreen("query-builder");
                                            }
                                            else if (searchTab === "source-config") {
                                                const [nextConfig, nextCatalog] = await Promise.all([
                                                    client.getSearchSourceConfig(workspaceHome.project.id),
                                                    client.getSourceCatalog(),
                                                ]);
                                                setSourceConfig(nextConfig);
                                                setSourceCatalog(nextCatalog);
                                                setScreen("source-config");
                                            }
                                            else if (searchTab === "search-runs") {
                                                setScreen("search-runs");
                                            }
                                        }, children: stageEntry.primary_action.label }), _jsx("div", { style: { marginTop: "20px" }, children: _jsx(SearchStageTabs, { activeTab: searchTab, onTabChange: (t) => setSearchTab(t) }) })] }), _jsxs("section", { style: { ...panelStyle, borderRadius: "20px" }, children: [_jsx("div", { style: { display: searchTab === "query-builder" ? undefined : "none" }, children: searchQueryEditor !== null ? (_jsx(SearchQueryBuilderScreen, { editor: searchQueryEditor, onBackToStageEntry: () => { }, onSaveDraft: async () => {
                                                setSearchQueryEditor(await client.saveSearchQueryDraft(workspaceHome.project.id, {
                                                    query_id: searchQueryEditor.query_id,
                                                    query_name: searchQueryEditor.query_name,
                                                    selected_sources: searchQueryEditor.selected_sources,
                                                    grouped_terms: searchQueryEditor.grouped_terms,
                                                    expression_blocks: searchQueryEditor.expression_blocks,
                                                }));
                                            }, onSaveVersion: async () => {
                                                setSearchQueryEditor(await client.saveSearchQueryVersion(workspaceHome.project.id, {
                                                    query_id: searchQueryEditor.query_id,
                                                    query_name: searchQueryEditor.query_name,
                                                    selected_sources: searchQueryEditor.selected_sources,
                                                    grouped_terms: searchQueryEditor.grouped_terms,
                                                    expression_blocks: searchQueryEditor.expression_blocks,
                                                }));
                                            } })) : (_jsx("div", { style: { padding: "40px 0", textAlign: "center", color: "#6b7280" }, children: "\u52A0\u8F7D\u4E2D\u2026" })) }), _jsx("div", { style: { display: searchTab === "source-config" ? undefined : "none" }, children: sourceConfig !== null ? (_jsx(SearchSourceConfigScreen, { config: sourceConfig, searchFieldOptions: sourceCatalog?.search_field_options ?? [], languageOptions: sourceCatalog?.language_options ?? [], onBackToStageEntry: () => { }, onSave: async (payload) => {
                                                setSourceConfig(await client.saveSearchSourceConfig(workspaceHome.project.id, payload));
                                            } })) : (_jsx("div", { style: { padding: "40px 0", textAlign: "center", color: "#6b7280" }, children: "\u52A0\u8F7D\u4E2D\u2026" })) }), _jsx("div", { style: { display: searchTab === "search-runs" ? undefined : "none" }, children: _jsx(SearchRunListScreen, { runs: searchRuns, editor: searchQueryEditor, onBackToStageEntry: () => { }, onCreateRun: handleCreateSearchRun, onOpenRunDetail: (runId) => handleOpenSearchRunDetail(workspaceHome.project.id, runId) }) })] }), _jsxs("section", { style: { ...panelStyle, marginTop: "20px" }, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u5B50\u5165\u53E3\u5BFC\u822A" }), _jsx("div", { style: {
                                            display: "grid",
                                            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                                            gap: "12px",
                                        }, children: stageEntry.entry_cards.map((card) => (_jsx(SummaryButton, { item: card, onClick: async () => {
                                                if (card.key === "query-builder") {
                                                    const nextEditor = await client.getSearchQueryEditor(workspaceHome.project.id);
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
                                                    const nextLibrary = await client.getLiteratureLibrary(workspaceHome.project.id);
                                                    setLiteratureLibrary(nextLibrary);
                                                    setScreen("literature");
                                                    return;
                                                }
                                                if (card.key === "search-runs") {
                                                    setScreen("search-runs");
                                                    return;
                                                }
                                                setScreen("stage-subentry");
                                            } }, card.key))) })] }), _jsx("section", { style: { ...panelStyle, marginTop: "20px" }, children: _jsx(WorkspaceOneClickPubmedDemo, { client: client, session: session, workspaceHomeProjectId: workspaceHome?.project?.id, onRunCreated: (rid, pid) => handleOpenSearchRunDetail(pid, rid), onErrorToast: alert, onProjectCreatedToast: (n) => console.info(`[demo] auto-created project: ${n}`) }) }), _jsxs("section", { style: {
                                    display: "grid",
                                    gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                                    gap: "20px",
                                    marginTop: "20px",
                                }, children: [_jsxs("div", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u6700\u8FD1\u4EFB\u52A1" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.recent_tasks.map((task) => (_jsx(SummaryButton, { item: task, onClick: () => setScreen("recent-tasks") }, task.title))) })] }), _jsxs("div", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u6700\u8FD1\u4EA7\u7269" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.recent_artifacts.map((artifact) => (_jsx(SummaryButton, { item: artifact, onClick: () => setScreen("recent-artifacts") }, artifact.title))) })] })] })] }), _jsxs("aside", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u9636\u6BB5\u52A9\u624B + \u4E0B\u4E00\u6B65\u5EFA\u8BAE" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.assistant_suggestions.map((item) => (_jsx(SummaryButton, { item: item, onClick: () => setScreen("assistant") }, item.title))) })] }), _jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u9636\u6BB5\u63D0\u793A" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.guidance_notes.map((note) => (_jsxs("li", { style: {
                                                border: "1px solid #e5e7eb",
                                                borderRadius: "14px",
                                                padding: "12px 14px",
                                            }, children: [_jsx("div", { style: { fontWeight: 600 }, children: note.title }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "14px" }, children: note.detail })] }, note.title))) })] })] })] }));
        }
        return (_jsxs("main", { style: shellStyle, children: [_jsxs("section", { style: { ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }, children: "MEDA DESKTOP" }), _jsx("h1", { style: { margin: "8px 0 0", fontSize: "24px" }, children: "MedA Desktop Workspace" })] }), _jsx("nav", { "aria-label": "\u4E3B\u5BFC\u822A", children: _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: ["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (_jsx("li", { children: _jsx("div", { style: {
                                            borderRadius: "12px",
                                            padding: "10px 12px",
                                            background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                                            color: item === "工作台" ? "#3730a3" : "#334155",
                                            fontWeight: item === "工作台" ? 600 : 500,
                                        }, children: item }) }, item))) }) }), _jsxs("section", { children: [_jsx("h2", { style: { margin: "0 0 12px", fontSize: "16px" }, children: "\u9879\u76EE\u4E0A\u4E0B\u6587" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: projects.map((project) => (_jsx("li", { children: _jsxs("div", { style: {
                                                border: project.id === workspaceHome.project.id
                                                    ? "1px solid #c7d2fe"
                                                    : "1px solid #e5e7eb",
                                                background: project.id === workspaceHome.project.id
                                                    ? "#f8faff"
                                                    : "#ffffff",
                                                borderRadius: "14px",
                                                padding: "12px 14px",
                                            }, children: [_jsx("div", { style: { fontWeight: 600 }, children: project.name }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "13px" }, children: project.workspace_key })] }) }, project.id))) })] })] }), _jsx(StageEntryScreen, { stageEntry: stageEntry, onOpenPrimaryAction: async () => {
                        setSearchQueryEditor(await client.getSearchQueryEditor(workspaceHome.project.id));
                        setScreen("query-builder");
                    }, onOpenTaskPage: () => setScreen("recent-tasks"), onOpenArtifactPage: () => setScreen("recent-artifacts"), onOpenAssistantAction: () => setScreen("assistant"), onOpenEntryCard: async (entryKey) => {
                        if (entryKey === "query-builder") {
                            setSearchQueryEditor(await client.getSearchQueryEditor(workspaceHome.project.id));
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
                            setLiteratureLibrary(await client.getLiteratureLibrary(workspaceHome.project.id));
                            setScreen("literature");
                            return;
                        }
                        if (entryKey === "search-runs") {
                            setScreen("search-runs");
                            return;
                        }
                        setScreen("stage-subentry");
                    } })] }));
    }
    if (screen === "query-builder") {
        return (_jsxs("main", { style: shellStyle, children: [_jsxs("section", { style: { ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }, children: "MEDA DESKTOP" }), _jsx("h1", { style: { margin: "8px 0 0", fontSize: "24px" }, children: "MedA Desktop Workspace" })] }), _jsx("nav", { "aria-label": "\u4E3B\u5BFC\u822A", children: _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: ["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (_jsx("li", { children: _jsx("div", { style: {
                                            borderRadius: "12px",
                                            padding: "10px 12px",
                                            background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                                            color: item === "工作台" ? "#3730a3" : "#334155",
                                            fontWeight: item === "工作台" ? 600 : 500,
                                        }, children: item }) }, item))) }) }), _jsxs("section", { children: [_jsx("h2", { style: { margin: "0 0 12px", fontSize: "16px" }, children: "\u9879\u76EE\u4E0A\u4E0B\u6587" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: projects.map((project) => (_jsx("li", { children: _jsxs("div", { style: {
                                                border: project.id === workspaceHome.project.id
                                                    ? "1px solid #c7d2fe"
                                                    : "1px solid #e5e7eb",
                                                background: project.id === workspaceHome.project.id
                                                    ? "#f8faff"
                                                    : "#ffffff",
                                                borderRadius: "14px",
                                                padding: "12px 14px",
                                            }, children: [_jsx("div", { style: { fontWeight: 600 }, children: project.name }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "13px" }, children: project.workspace_key })] }) }, project.id))) })] })] }), searchQueryEditor !== null ? (_jsx(SearchQueryBuilderScreen, { editor: searchQueryEditor, onBackToStageEntry: () => setScreen("stage-entry"), onSaveDraft: async () => {
                        setSearchQueryEditor(await client.saveSearchQueryDraft(workspaceHome.project.id, {
                            query_id: searchQueryEditor.query_id,
                            query_name: searchQueryEditor.query_name,
                            selected_sources: searchQueryEditor.selected_sources,
                            grouped_terms: searchQueryEditor.grouped_terms,
                            expression_blocks: searchQueryEditor.expression_blocks,
                        }));
                    }, onSaveVersion: async () => {
                        setSearchQueryEditor(await client.saveSearchQueryVersion(workspaceHome.project.id, {
                            query_id: searchQueryEditor.query_id,
                            query_name: searchQueryEditor.query_name,
                            selected_sources: searchQueryEditor.selected_sources,
                            grouped_terms: searchQueryEditor.grouped_terms,
                            expression_blocks: searchQueryEditor.expression_blocks,
                        }));
                    } })) : (_jsx("section", { style: panelStyle, children: _jsx("div", { style: { padding: "40px 0", textAlign: "center", color: "#6b7280" }, children: "\u52A0\u8F7D\u4E2D\u2026" }) }))] }));
    }
    if (screen === "source-config") {
        return (_jsxs("main", { style: shellStyle, children: [_jsxs("section", { style: { ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }, children: "MEDA DESKTOP" }), _jsx("h1", { style: { margin: "8px 0 0", fontSize: "24px" }, children: "MedA Desktop Workspace" })] }), _jsx("nav", { "aria-label": "\u4E3B\u5BFC\u822A", children: _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: ["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (_jsx("li", { children: _jsx("div", { style: {
                                            borderRadius: "12px",
                                            padding: "10px 12px",
                                            background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                                            color: item === "工作台" ? "#3730a3" : "#334155",
                                            fontWeight: item === "工作台" ? 600 : 500,
                                        }, children: item }) }, item))) }) }), _jsxs("section", { children: [_jsx("h2", { style: { margin: "0 0 12px", fontSize: "16px" }, children: "\u9879\u76EE\u4E0A\u4E0B\u6587" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: projects.map((project) => (_jsx("li", { children: _jsxs("div", { style: {
                                                border: project.id === workspaceHome.project.id
                                                    ? "1px solid #c7d2fe"
                                                    : "1px solid #e5e7eb",
                                                background: project.id === workspaceHome.project.id
                                                    ? "#f8faff"
                                                    : "#ffffff",
                                                borderRadius: "14px",
                                                padding: "12px 14px",
                                            }, children: [_jsx("div", { style: { fontWeight: 600 }, children: project.name }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "13px" }, children: project.workspace_key })] }) }, project.id))) })] })] }), sourceConfig !== null ? (_jsx(SearchSourceConfigScreen, { config: sourceConfig, searchFieldOptions: sourceCatalog?.search_field_options ?? [], languageOptions: sourceCatalog?.language_options ?? [], onBackToStageEntry: () => setScreen("stage-entry"), onSave: async (payload) => {
                        setSourceConfig(await client.saveSearchSourceConfig(workspaceHome.project.id, payload));
                    } })) : (_jsx("section", { style: panelStyle, children: _jsx("div", { style: { padding: "40px 0", textAlign: "center", color: "#6b7280" }, children: "\u52A0\u8F7D\u4E2D\u2026" }) }))] }));
    }
    if (screen === "literature") {
        return (_jsxs("main", { style: shellStyle, children: [_jsxs("section", { style: { ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }, children: "MEDA DESKTOP" }), _jsx("h1", { style: { margin: "8px 0 0", fontSize: "24px" }, children: "MedA Desktop Workspace" })] }), _jsx("nav", { "aria-label": "\u4E3B\u5BFC\u822A", children: _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: ["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (_jsx("li", { children: _jsx("div", { style: {
                                            borderRadius: "12px",
                                            padding: "10px 12px",
                                            background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                                            color: item === "工作台" ? "#3730a3" : "#334155",
                                            fontWeight: item === "工作台" ? 600 : 500,
                                        }, children: item }) }, item))) }) }), _jsxs("section", { children: [_jsx("h2", { style: { margin: "0 0 12px", fontSize: "16px" }, children: "\u9879\u76EE\u4E0A\u4E0B\u6587" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: projects.map((project) => (_jsx("li", { children: _jsxs("div", { style: {
                                                border: project.id === workspaceHome.project.id
                                                    ? "1px solid #c7d2fe"
                                                    : "1px solid #e5e7eb",
                                                background: project.id === workspaceHome.project.id
                                                    ? "#f8faff"
                                                    : "#ffffff",
                                                borderRadius: "14px",
                                                padding: "12px 14px",
                                            }, children: [_jsx("div", { style: { fontWeight: 600 }, children: project.name }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "13px" }, children: project.workspace_key })] }) }, project.id))) })] })] }), literatureLibrary !== null ? (_jsx(LiteratureLibraryScreen, { library: literatureLibrary, onBackToStageEntry: () => setScreen("stage-entry"), onImport: async (payload) => {
                        setLiteratureLibrary(await client.importLiterature(workspaceHome.project.id, payload));
                    }, onConfirmUnique: async (recordId) => {
                        setLiteratureLibrary(await client.confirmLiteratureUnique(workspaceHome.project.id, recordId));
                    } })) : (_jsx("section", { style: panelStyle, children: _jsx("div", { style: { padding: "40px 0", textAlign: "center", color: "#6b7280" }, children: "\u52A0\u8F7D\u4E2D\u2026" }) }))] }));
    }
    return (_jsxs("main", { style: shellStyle, children: [_jsxs("section", { style: { ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("div", { children: [_jsx("div", { style: { fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }, children: "MEDA DESKTOP" }), _jsx("h1", { style: { margin: "8px 0 0", fontSize: "24px" }, children: "MedA Desktop Workspace" })] }), _jsx("nav", { "aria-label": "\u4E3B\u5BFC\u822A", children: _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: ["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (_jsx("li", { children: _jsx("div", { style: {
                                        borderRadius: "12px",
                                        padding: "10px 12px",
                                        background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                                        color: item === "工作台" ? "#3730a3" : "#334155",
                                        fontWeight: item === "工作台" ? 600 : 500,
                                    }, children: item }) }, item))) }) }), _jsxs("section", { children: [_jsx("h2", { style: { margin: "0 0 12px", fontSize: "16px" }, children: "\u9879\u76EE\u4E0A\u4E0B\u6587" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }, children: projects.map((project) => (_jsx("li", { children: _jsxs("div", { style: {
                                            border: project.id === workspaceHome.project.id
                                                ? "1px solid #c7d2fe"
                                                : "1px solid #e5e7eb",
                                            background: project.id === workspaceHome.project.id
                                                ? "#f8faff"
                                                : "#ffffff",
                                            borderRadius: "14px",
                                            padding: "12px 14px",
                                        }, children: [_jsx("div", { style: { fontWeight: 600 }, children: project.name }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "13px" }, children: project.workspace_key })] }) }, project.id))) })] })] }), _jsxs("section", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("section", { style: panelStyle, children: [_jsxs("div", { style: {
                                    display: "flex",
                                    justifyContent: "space-between",
                                    gap: "16px",
                                    alignItems: "flex-start",
                                }, children: [_jsxs("div", { children: [_jsx("div", { style: { color: "#6b7280", fontSize: "13px" }, children: "\u9879\u76EE\u5DE5\u4F5C\u53F0\u9996\u9875" }), _jsx("h2", { style: { margin: "8px 0 12px", fontSize: "30px" }, children: workspaceHome.project.name }), _jsxs("p", { style: { margin: "0 0 8px" }, children: ["\u5F53\u524D\u673A\u6784\uFF1A", session.organization.name] }), _jsxs("p", { style: { margin: 0 }, children: ["\u5F53\u524D\u9636\u6BB5\uFF1A", workspaceHome.project.current_stage] })] }), _jsxs("div", { style: { minWidth: "180px", textAlign: "right" }, children: [_jsxs("div", { style: { color: "#6b7280", fontSize: "13px" }, children: ["\u6B22\u8FCE\uFF0C", session.user.display_name] }), _jsx("div", { style: { marginTop: "8px", fontSize: "13px", color: "#4b5563" }, children: workspaceHome.project.updated_at_label })] })] }), _jsxs("div", { style: {
                                    marginTop: "20px",
                                    padding: "16px",
                                    borderRadius: "18px",
                                    background: "linear-gradient(135deg, #111827 0%, #1f2937 100%)",
                                    color: "#f9fafb",
                                }, children: [_jsx("div", { style: { fontSize: "13px", opacity: 0.84 }, children: "\u5F53\u524D\u9879\u76EE\u7A7A\u95F4" }), _jsx("div", { style: { marginTop: "6px", fontSize: "15px" }, children: workspaceHome.project.workspace_key }), _jsx("button", { style: {
                                            marginTop: "16px",
                                            border: "none",
                                            borderRadius: "999px",
                                            background: "#f9fafb",
                                            color: "#111827",
                                            padding: "10px 16px",
                                            cursor: "pointer",
                                            fontWeight: 600,
                                        }, onClick: () => setScreen("recent-tasks"), children: workspaceHome.hero_cta.label })] })] }), _jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u7814\u7A76\u9636\u6BB5" }), _jsx("div", { style: {
                                    display: "grid",
                                    gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
                                    gap: "12px",
                                }, children: workspaceHome.stages.map((stage) => (_jsx(SummaryButton, { item: stage, onClick: async () => {
                                        const nextStageEntry = await client.getStageEntry(workspaceHome.project.id, stage.key);
                                        setStageEntry(nextStageEntry);
                                        if (stage.key === "search") {
                                            const [nextEditor, nextConfig, nextCatalog, nextRunsRaw] = await Promise.all([
                                                client.getSearchQueryEditor(workspaceHome.project.id),
                                                client.getSearchSourceConfig(workspaceHome.project.id),
                                                client.getSourceCatalog(),
                                                client.listSearchRuns(workspaceHome.project.id).catch(() => null),
                                            ]);
                                            setSearchQueryEditor(nextEditor);
                                            setSourceConfig(nextConfig);
                                            setSourceCatalog(nextCatalog);
                                            setSearchRuns(nextRunsRaw
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
                                                : null);
                                        }
                                        setScreen("stage-entry");
                                    } }, stage.key))) })] }), _jsxs("section", { style: {
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                            gap: "20px",
                        }, children: [_jsxs("div", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u6700\u8FD1\u4EFB\u52A1" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: workspaceHome.recent_tasks.map((task) => (_jsx(SummaryButton, { item: task, onClick: () => setScreen("recent-tasks") }, task.title))) })] }), _jsxs("div", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u6700\u8FD1\u4EA7\u7269" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: workspaceHome.recent_artifacts.map((artifact) => (_jsx(SummaryButton, { item: artifact, onClick: () => setScreen("recent-artifacts") }, artifact.title))) })] })] }), _jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u534F\u4F5C\u52A8\u6001" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }, children: workspaceHome.activity.map((activity) => (_jsxs("li", { style: {
                                        border: "1px solid #e5e7eb",
                                        borderRadius: "14px",
                                        padding: "12px 14px",
                                    }, children: [_jsx("div", { style: { fontWeight: 600 }, children: activity.title }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "14px" }, children: activity.subtitle })] }, activity.title))) })] })] }), _jsxs("aside", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: workspaceHome.assistant.headline }), _jsx("p", { style: { margin: "0 0 16px", color: "#4b5563" }, children: "\u57FA\u4E8E\u5F53\u524D\u7814\u7A76\u9636\u6BB5\u4E0E\u6700\u8FD1\u4EA7\u7269\uFF0C\u7EE7\u7EED\u63A8\u8FDB\u4E0B\u4E00\u6B65\u4EFB\u52A1\u3002" }), _jsx("button", { style: {
                                    ...buttonStyle,
                                    background: "#111827",
                                    border: "none",
                                    color: "#f9fafb",
                                    textAlign: "center",
                                }, onClick: () => setScreen("assistant"), children: workspaceHome.assistant.primary_action_label })] }), _jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u5F85\u529E\u4E0E\u63D0\u9192" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }, children: workspaceHome.todos.map((todo) => (_jsx("li", { children: _jsx(SummaryButton, { item: todo, onClick: () => setScreen("recent-tasks") }) }, todo.title))) })] })] })] }));
}
