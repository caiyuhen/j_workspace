import React from "react";
import type { ReportSnapshot } from "@meda/shared-sdk";

function _fmtDate(s: string): string {
  try {
    const d = new Date(s);
    return d.toISOString().slice(0,10) + " " + d.toTimeString().slice(0,5);
  } catch { return s.slice(0,16); }
}
function _sha8(s: string): string { return (s || "").slice(0, 8); }

export function ReportSnapshotList({
  snapshots,
  onDownload,
}: {
  snapshots: ReportSnapshot[];
  onDownload: (x: { id: number; format: "md" | "html" | "txt" }) => void;
}): JSX.Element {
  return (
    <div className="report-snapshot-list" role="list" aria-label="Report snapshots list">
      <style>{`
        .report-snapshot-list .rsl-card { border: 1px solid #e5e7eb; border-radius: .5rem; padding: .7rem 1rem; margin-bottom: .5rem; background:#fff; font-family: system-ui; }
        .report-snapshot-list .rsl-row { display:flex; align-items:center; justify-content:space-between; gap: .5rem; margin: .3rem 0; }
        .report-snapshot-list .rsl-ver { font-weight: 700; }
        .report-snapshot-list .rsl-sha { font-family: ui-monospace, monospace; font-size: .8rem; color: #6b7280; }
        .report-snapshot-list .rsl-actions { display: flex; gap: .35rem; }
        .report-snapshot-list .rsl-actions button { padding: .2rem .5rem; border-radius: .3rem; border: 1px solid #d1d5db; background:#fff; cursor: pointer; font-size: .82rem; }
      `}</style>
      {snapshots.length === 0 ? (
        <p style={{ color: "#6b7280", fontFamily: "system-ui", fontSize: ".88rem" }}>No snapshots yet — generate a report to create versioned exports.</p>
      ) : snapshots.map(sn => (
        <div className="rsl-card" role="listitem" key={sn.id}>
          <div className="rsl-row">
            <div>
              <span className="rsl-ver">{sn.version_label}</span>
              <span style={{ margin: "0 .5rem", color:"#94a3b8" }}>·</span>
              <span className="rsl-sha" title={sn.sha256_grade + " / " + sn.sha256_analysis}>
                sha g:{_sha8(sn.sha256_grade)} / a:{_sha8(sn.sha256_analysis)}
              </span>
            </div>
            <span style={{ fontSize: ".82rem", color: "#475569" }}>{_fmtDate(sn.created_at)}</span>
          </div>
          <div className="rsl-row">
            <div></div>
            <div className="rsl-actions">
              <button type="button" onClick={() => onDownload({ id: sn.id, format: "md" })}>Download MD</button>
              <button type="button" onClick={() => onDownload({ id: sn.id, format: "html" })}>Download HTML</button>
              <button type="button" onClick={() => onDownload({ id: sn.id, format: "txt" })}>Download TXT</button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
