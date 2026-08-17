import React from "react";
import type { SofRow, GradeCertaintyFinal } from "@meda/shared-sdk";

const COLOR: Record<GradeCertaintyFinal, string> = {
  High: "#166534", Moderate: "#1d4ed8", Low: "#b45309", VeryLow: "#7f1d1d",
};

export function GradeSoFTable({
  rows,
  onRowClick,
}: {
  rows: SofRow[];
  onRowClick?: (row: SofRow) => void;
}): JSX.Element {
  return (
    <table className="grade-sof-table" role="table" aria-label="SoF Table" style={{ borderCollapse: "collapse", width: "100%", fontSize: ".88rem" }}>
      <style>{`
        .grade-sof-table th, .grade-sof-table td { border: 1px solid #d1d5db; padding: .4rem .5rem; vertical-align: top; }
        .grade-sof-table th { background: #f9fafb; font-family: system-ui; text-align: left; }
        .grade-cer { padding: .1rem .4rem; color: #fff; border-radius: .25rem; font-weight: 600; font-family: system-ui; font-size: .8rem; }
      `}</style>
      <thead>
        <tr>
          <th>Outcome</th>
          <th>Certainty</th>
          <th style={{ textAlign: "right" }}>Participants</th>
          <th style={{ textAlign: "right" }}>Studies</th>
          <th>Effect Measure</th>
          <th>AR Control</th>
          <th>AR Intervention</th>
          <th>Comments</th>
        </tr>
      </thead>
      <tbody>
        {rows.length === 0 ? (
          <tr><td colSpan={8} style={{ textAlign: "center", color: "#6b7280", padding: "1rem" }}>No SoF rows — complete GRADE assessments first.</td></tr>
        ) : rows.map((r) => (
          <tr key={`${r.project_id}-${r.outcome_id}`} onClick={() => onRowClick && onRowClick(r)} style={{ cursor: onRowClick ? "pointer" : "default" }}>
            <td>{r.outcome_label}</td>
            <td><span className="grade-cer" style={{ backgroundColor: COLOR[r.certainty as GradeCertaintyFinal] }}>{r.certainty}</span></td>
            <td style={{ textAlign: "right" }}>{r.participants_n}</td>
            <td style={{ textAlign: "right" }}>{r.studies_k}</td>
            <td>{r.effect_measure_label}</td>
            <td>{r.absolute_risk_control ?? "NR"}</td>
            <td>{r.absolute_risk_intervention ?? "NR"}</td>
            <td>{r.comments || ""}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
