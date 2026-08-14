import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
const panelStyle = {
    background: "#ffffff",
    border: "1px solid #d7dce5",
    borderRadius: "20px",
    padding: "20px",
    boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
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
function StageButton({ title, subtitle, onClick, }) {
    return (_jsxs("button", { "aria-label": title, style: buttonStyle, onClick: onClick, children: [_jsx("div", { style: { fontWeight: 600 }, children: title }), _jsx("div", { style: { marginTop: "4px", color: "#4b5563", fontSize: "14px" }, children: subtitle })] }));
}
function cardSubtitle(card) {
    return `${card.description} · ${card.status}`;
}
function itemSubtitle(item) {
    return item.subtitle;
}
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
                                }, children: stageEntry.entry_cards.map((card) => (_jsx(StageButton, { title: card.title, subtitle: cardSubtitle(card), onClick: () => onOpenEntryCard(card.key) }, card.key))) })] }), _jsxs("section", { style: {
                            display: "grid",
                            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
                            gap: "20px",
                        }, children: [_jsxs("div", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u6700\u8FD1\u4EFB\u52A1" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.recent_tasks.map((task) => (_jsx(StageButton, { title: task.title, subtitle: itemSubtitle(task), onClick: onOpenTaskPage }, task.title))) })] }), _jsxs("div", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u6700\u8FD1\u4EA7\u7269" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.recent_artifacts.map((artifact) => (_jsx(StageButton, { title: artifact.title, subtitle: itemSubtitle(artifact), onClick: onOpenArtifactPage }, artifact.title))) })] })] })] }), _jsxs("aside", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u9636\u6BB5\u52A9\u624B + \u4E0B\u4E00\u6B65\u5EFA\u8BAE" }), _jsx("div", { style: { display: "flex", flexDirection: "column", gap: "12px" }, children: stageEntry.assistant_suggestions.map((item) => (_jsx(StageButton, { title: item.title, subtitle: itemSubtitle(item), onClick: onOpenAssistantAction }, item.title))) })] }), _jsxs("section", { style: panelStyle, children: [_jsx("h2", { style: { marginTop: 0 }, children: "\u9636\u6BB5\u63D0\u793A" }), _jsx("ul", { style: { margin: 0, paddingLeft: "20px", color: "#374151" }, children: stageEntry.guidance_notes.map((note) => (_jsxs("li", { style: { marginBottom: "10px" }, children: [_jsx("strong", { children: note.title }), "\uFF1A", note.detail] }, note.title))) })] })] })] }));
}
