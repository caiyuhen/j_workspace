import { jsx as _jsx, jsxs as _jsxs } from "react/jsx-runtime";
import { useState } from "react";
export function LoginForm({ onSubmit }) {
    const [organizationSlug, setOrganizationSlug] = useState("demo-hospital");
    const [userId, setUserId] = useState("u-001");
    const handleSubmit = async (event) => {
        event.preventDefault();
        await onSubmit({ organizationSlug, userId });
    };
    return (_jsxs("form", { onSubmit: handleSubmit, children: [_jsxs("label", { children: ["\u673A\u6784\u6807\u8BC6", _jsx("input", { "aria-label": "\u673A\u6784\u6807\u8BC6", value: organizationSlug, onChange: (event) => setOrganizationSlug(event.target.value) })] }), _jsxs("label", { children: ["\u7528\u6237\u7F16\u53F7", _jsx("input", { "aria-label": "\u7528\u6237\u7F16\u53F7", value: userId, onChange: (event) => setUserId(event.target.value) })] }), _jsx("button", { type: "submit", children: "\u8FDB\u5165\u5DE5\u4F5C\u53F0" })] }));
}
