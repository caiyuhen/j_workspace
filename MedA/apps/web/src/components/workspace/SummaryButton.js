import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
export function SummaryButton({ item, onClick }) {
    const title = "title" in item ? item.title : item.label;
    const subtitle = "subtitle" in item
        ? item.subtitle
        : "description" in item
            ? item.description
            : `${item.task_count} 个任务 · ${item.artifact_count} 个产物`;
    return (_jsxs("button", { "aria-label": title, style: {
            width: "100%",
            border: "1px solid #d0d7e2",
            background: "#ffffff",
            borderRadius: "14px",
            padding: "12px 14px",
            textAlign: "left",
            cursor: "pointer",
        }, onClick: onClick, children: [_jsx("div", { style: { fontWeight: 600 }, children: title }), _jsx("div", { style: { marginTop: "4px", color: "#4b5563", fontSize: "14px" }, children: subtitle })] }));
}
