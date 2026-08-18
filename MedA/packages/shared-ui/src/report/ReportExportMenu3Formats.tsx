import React from "react";

export function ReportExportMenu3Formats({
  onExport,
  disabled = false,
}: {
  onExport: (x: { format: "md" | "html" | "txt" }) => void;
  disabled?: boolean;
}): JSX.Element {
  return (
    <div className="report-export-menu" role="group" aria-label="report-export-3-formats">
      <style>{`
        .report-export-menu button { padding: .4rem .8rem; border-radius: .35rem; border: 1px solid #d1d5db; background:#fff; cursor: pointer; font-family: system-ui; }
        .report-export-menu button[disabled] { opacity: .45; cursor: not-allowed; }
        .report-export-menu { display:flex; gap: .5rem; align-items:center; }
      `}</style>
      <strong style={{ fontFamily: "system-ui", fontSize: ".9rem" }}>Export:</strong>
      <button type="button" disabled={disabled} onClick={() => onExport({ format: "md" })}>Markdown (MD)</button>
      <button type="button" disabled={disabled} onClick={() => onExport({ format: "html" })}>HTML</button>
      <button type="button" disabled={disabled} onClick={() => onExport({ format: "txt" })}>Plain Text (TXT)</button>
    </div>
  );
}
