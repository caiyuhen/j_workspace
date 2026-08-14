import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
const panelStyle = {
    background: "#ffffff",
    border: "1px solid #d7dce5",
    borderRadius: "20px",
    padding: "20px",
    boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};
export function SearchQueryBuilderScreen({ editor, onBackToStageEntry, onSaveDraft, onSaveVersion, }) {
    return (_jsxs(_Fragment, { children: [_jsx("section", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: _jsxs("section", { style: panelStyle, children: [_jsx("button", { style: {
                                border: "1px solid #d0d7e2",
                                background: "#ffffff",
                                borderRadius: "999px",
                                padding: "8px 14px",
                                cursor: "pointer",
                            }, onClick: onBackToStageEntry, children: "\u8FD4\u56DE\u68C0\u7D22\u9636\u6BB5\u5165\u53E3\u9875" }), _jsx("h2", { style: { margin: "16px 0 8px", fontSize: "30px" }, children: "\u68C0\u7D22\u5F0F\u7BA1\u7406" }), _jsxs("div", { children: ["\u5F53\u524D\u68C0\u7D22\u5F0F\uFF1A", editor.query_name] }), _jsxs("div", { style: { marginTop: "4px" }, children: ["\u5F53\u524D\u7248\u672C\uFF1A", editor.query_version] }), _jsxs("div", { style: { display: "flex", gap: "12px", marginTop: "16px" }, children: [_jsx("button", { style: {
                                        border: "1px solid #d0d7e2",
                                        background: "#ffffff",
                                        borderRadius: "999px",
                                        padding: "10px 16px",
                                        cursor: "pointer",
                                    }, onClick: onSaveDraft, children: "\u4FDD\u5B58" }), _jsx("button", { style: {
                                        border: "none",
                                        background: "#111827",
                                        color: "#f9fafb",
                                        borderRadius: "999px",
                                        padding: "10px 16px",
                                        cursor: "pointer",
                                    }, onClick: onSaveVersion, children: "\u53E6\u5B58\u4E3A\u65B0\u7248\u672C" })] })] }) }), _jsx("aside", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: _jsxs("section", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u9884\u89C8 + \u52A9\u624B" }), _jsx("div", { children: editor.preview_summary.database_scope_summary }), _jsx("div", { style: { marginTop: "8px" }, children: editor.preview_summary.coverage_hint })] }) })] }));
}
