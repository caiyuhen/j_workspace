import React from "react";
import type { Grade3Upgrades, GradeCertaintyFinal } from "@meda/shared-sdk";

const UPGRADE_ROWS = [
  { key: "large_effect" as const, label: "a) Large effect" },
  { key: "dose_response" as const, label: "b) Dose-response gradient" },
  { key: "confounders_reduce" as const, label: "c) Confounders reduce effect" },
];

const COLOR_BY_CERTAINTY: Record<GradeCertaintyFinal, string> = {
  High: "#166534",
  Moderate: "#1d4ed8",
  Low: "#b45309",
  VeryLow: "#7f1d1d",
};

export function GradeUpgradeScorer3({
  value,
  onChange,
  certainty,
  locked = false,
}: {
  value: Grade3Upgrades;
  onChange: (next: Grade3Upgrades) => void;
  certainty: GradeCertaintyFinal;
  locked?: boolean;
}): JSX.Element {
  return (
    <div className="grade-upgrade-scorer-3" aria-label="Grade3Upgrades">
      <style>{`
        .grade-upgrade-scorer-3 .gu-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.5rem; }
        .grade-upgrade-scorer-3 .gu-badge { padding: .15rem .55rem; color: #fff; font-weight: 600; border-radius: .3rem; font-family: system-ui; font-size: .85rem; }
        .grade-upgrade-scorer-3 .gu-row { display: flex; align-items: center; gap: .5rem; padding: .15rem 0; }
      `}</style>
      <div className="gu-header">
        <strong>3 upgrade domains</strong>
        <span className="gu-badge" style={{ backgroundColor: COLOR_BY_CERTAINTY[certainty] }}>{certainty}</span>
      </div>
      {UPGRADE_ROWS.map((row) => (
        <label className="gu-row" key={row.key} style={{ fontSize: ".88rem" }}>
          <input
            type="checkbox"
            checked={value[row.key]}
            disabled={locked}
            onChange={() => {
              const next: Grade3Upgrades = { ...value, [row.key]: !value[row.key] };
              onChange(next);
            }}
          />
          <span>{row.label}</span>
        </label>
      ))}
    </div>
  );
}
