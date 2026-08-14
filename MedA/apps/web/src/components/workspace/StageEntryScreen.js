import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
import { SummaryButton } from "./SummaryButton";
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
export function StageEntryScreen({ stageEntry, onOpenPrimaryAction, onOpenTaskPage, onOpenArtifactPage, onOpenAssistantAction, onOpenEntryCard, }) {
    return (_jsxs(_Fragment, { children: [_jsxs("section", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("section", { style: panelStyle, children: [_jsx("div", { style: { color: "#6b7280", fontSize: "13px" }, children: stageEntry.project.name }), _jsxs("h2", { style: { margin: "8px 0 12px", fontSize: "30px" }, children: [stageEntry.stage_label, "\u9636\u6BB5"] }), _jsxs("p", { style: { margin: "0 0 8px" }, children: ["\u5F53\u524D\u72B6\u6001\uFF1A", stageEntry.stage_status] }), _jsx("p", { style: { margin: 0 }, children: stageEntry.stage_goal }), _jsx("button", { style: {
                                    marginTop: "16px",
                                    border: "none",
                                    borderRadius: "999px",
                                    background: "#111827",
                                    color: "#f9fafb",
                                    padding: "10px 16px",
                                    cursor: "pointer",
                                    fontWeight: 600,
                                }, onClick: onOpenPrimaryAction, children: stageEntry.primary_action.label })] }), _jsxs("section", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u5B50\u5165\u53E3\u5BFC\u822A" }), _jsx("div", { style: {
                                    display: "grid",
                                    gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                                    gap: "12px",
                                }, children: stageEntry.entry_cards.map((card) => (_jsx(SummaryButton, { item: card, onClick: () => onOpenEntryCard(card.key) }, card.key))) })] }), _jsxs("section", { style: {
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                            gap: "20px",
                        }, children: [_jsxs("div", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u6700\u8FD1\u4EFB\u52A1" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.recent_tasks.map((task) => (_jsx(SummaryButton, { item: task, onClick: onOpenTaskPage }, task.title))) })] }), _jsxs("div", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u6700\u8FD1\u4EA7\u7269" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.recent_artifacts.map((artifact) => (_jsx(SummaryButton, { item: artifact, onClick: onOpenArtifactPage }, artifact.title))) })] })] })] }), _jsxs("aside", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u9636\u6BB5\u52A9\u624B + \u4E0B\u4E00\u6B65\u5EFA\u8BAE" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.assistant_suggestions.map((item) => (_jsx(SummaryButton, { item: item, onClick: onOpenAssistantAction }, item.title))) })] }), _jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u9636\u6BB5\u63D0\u793A" }), _jsx("ul", { style: { ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.guidance_notes.map((note) => (_jsxs("li", { style: {
                                        border: "1px solid #e5e7eb",
                                        borderRadius: "14px",
                                        padding: "12px 14px",
                                    }, children: [_jsx("div", { style: { fontWeight: 600 }, children: note.title }), _jsx("div", { style: { marginTop: "4px", color: "#6b7280", fontSize: "14px" }, children: note.detail })] }, note.title))) })] })] })] }));
}
