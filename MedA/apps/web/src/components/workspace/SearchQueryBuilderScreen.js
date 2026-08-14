import { jsx as _jsx, jsxs as _jsxs, Fragment as _Fragment } from "react/jsx-runtime";
const panelStyle = {
    background: "#ffffff",
    border: "1px solid #d7dce5",
    borderRadius: "20px",
    padding: "20px",
    boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};
export function SearchQueryBuilderScreen({ editor, onBackToStageEntry, onSaveDraft, onSaveVersion, onDeriveDraft, }) {
    return (_jsxs(_Fragment, { children: [_jsxs("section", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: [_jsxs("section", { style: panelStyle, children: [_jsx("button", { style: {
                                    border: "1px solid #d0d7e2",
                                    background: "#ffffff",
                                    borderRadius: "999px",
                                    padding: "8px 14px",
                                    cursor: "pointer",
                                }, onClick: onBackToStageEntry, children: "\u8FD4\u56DE\u68C0\u7D22\u9636\u6BB5\u5165\u53E3\u9875" }), _jsx("h2", { style: { margin: "16px 0 8px", fontSize: "30px" }, children: "\u68C0\u7D22\u5F0F\u7BA1\u7406" }), _jsx("div", { style: { color: "#6b7280", fontSize: "13px" }, children: editor.project.name }), _jsxs("div", { style: { marginTop: "8px" }, children: ["\u5F53\u524D\u68C0\u7D22\u5F0F\uFF1A", editor.query_name] }), _jsxs("div", { style: { marginTop: "4px" }, children: ["\u5F53\u524D\u7248\u672C\uFF1A", editor.query_version] }), _jsxs("div", { style: { marginTop: "4px" }, children: ["\u6A21\u5F0F\uFF1A", editor.query_mode] }), _jsxs("div", { style: { display: "flex", gap: "12px", marginTop: "16px" }, children: [_jsx("button", { style: {
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
                                        }, onClick: onSaveVersion, children: "\u53E6\u5B58\u4E3A\u65B0\u7248\u672C" }), editor.query_mode === "snapshot" ? (_jsx("button", { style: {
                                            border: "1px solid #d0d7e2",
                                            background: "#ffffff",
                                            borderRadius: "999px",
                                            padding: "10px 16px",
                                            cursor: "pointer",
                                        }, onClick: onDeriveDraft, children: "\u6D3E\u751F\u4E3A\u8349\u7A3F" })) : null] })] }), _jsxs("section", { style: {
                            display: "grid",
                            gridTemplateColumns: "280px minmax(0, 1fr)",
                            gap: "20px",
                        }, children: [_jsxs("section", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u8BCD\u7EC4\u4E0E\u5B57\u6BB5\u533A" }), editor.grouped_terms.map((group) => (_jsxs("div", { style: { marginBottom: "16px" }, children: [_jsx("div", { style: { fontWeight: 600 }, children: group.group_label }), group.terms.map((term) => (_jsxs("div", { style: {
                                                    marginTop: "8px",
                                                    border: "1px solid #e5e7eb",
                                                    borderRadius: "12px",
                                                    padding: "10px 12px",
                                                }, children: [term.label, " \u00B7 ", term.source_type] }, term.term_id)))] }, group.group_key)))] }), _jsxs("section", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u5757\u5F0F\u7F16\u8F91\u5668" }), editor.expression_blocks.map((block) => (_jsx("div", { style: {
                                            marginBottom: "10px",
                                            border: "1px solid #e5e7eb",
                                            borderRadius: "12px",
                                            padding: "10px 12px",
                                        }, children: block.block_type === "term"
                                            ? `TERM · ${block.term_ref ?? ""}`
                                            : `${block.block_type} · ${block.operator ?? ""}` }, block.block_id))), _jsx("div", { style: { marginTop: "16px", color: "#4b5563" }, children: editor.validation_messages.map((message) => message.message).join(" / ") })] })] })] }), _jsx("aside", { style: { display: "flex", flexDirection: "column", gap: "20px" }, children: _jsxs("section", { style: panelStyle, children: [_jsx("h3", { style: { marginTop: 0 }, children: "\u9884\u89C8 + \u52A9\u624B" }), _jsx("div", { children: editor.preview_summary.coverage_hint }), _jsx("div", { style: { marginTop: "8px" }, children: editor.preview_summary.database_scope_summary }), _jsxs("div", { style: { marginTop: "8px" }, children: ["\u9884\u8BA1\u547D\u4E2D\uFF1A", editor.preview_summary.estimated_hit_band] }), _jsxs("div", { style: { marginTop: "8px", color: "#6b7280", fontSize: "13px" }, children: ["\u6765\u6E90\uFF1A", editor.preview_summary.last_generated_from] })] }) })] }));
}
