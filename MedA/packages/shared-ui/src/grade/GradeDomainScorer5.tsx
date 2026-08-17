import React from "react";
import type { Grade5Domains, GradeDomainLevel } from "@meda/shared-sdk";

const DOMAIN_ROWS = [
  { key: "risk_of_bias" as const, label: "1. Risk of bias" },
  { key: "indirectness" as const, label: "2. Indirectness" },
  { key: "inconsistency" as const, label: "3. Inconsistency" },
  { key: "imprecision" as const, label: "4. Imprecision" },
  { key: "publication_bias" as const, label: "5. Publication bias" },
];

const LEVELS: { value: GradeDomainLevel; label: string }[] = [
  { value: "no_concerns", label: "No concerns" },
  { value: "some_concerns", label: "Some concerns" },
  { value: "major_concerns", label: "Major concerns" },
];

export function GradeDomainScorer5({
  value,
  onChange,
  locked = false,
}: {
  value: Grade5Domains;
  onChange: (next: Grade5Domains) => void;
  locked?: boolean;
}): JSX.Element {
  return (
    <div className="grade-domain-scorer-5" role="group" aria-label="Grade5Domains">
      <style>{`
        .grade-domain-scorer-5 .g5-row { display: flex; align-items: center; padding: 0.25rem 0; border-bottom: 1px solid #eef2f7; gap: 0.75rem; }
        .grade-domain-scorer-5 .g5-label { min-width: 180px; font-family: system-ui; font-size: 0.9rem; }
        .grade-domain-scorer-5 .g5-levels { display: flex; gap: 0.6rem; font-size: 0.85rem; }
      `}</style>
      {DOMAIN_ROWS.map((row) => (
        <div className="g5-row" role="radiogroup" aria-label={row.label} key={row.key}>
          <span className="g5-label">{row.label}</span>
          <div className="g5-levels">
            {LEVELS.map((lv) => (
              <label key={lv.value} style={{ display: "inline-flex", alignItems: "center", gap: ".25rem" }}>
                <input
                  type="radio"
                  name={`g5-${row.key}`}
                  value={lv.value}
                  checked={value[row.key] === lv.value}
                  disabled={locked}
                  onChange={() => {
                    const next: Grade5Domains = { ...value, [row.key]: lv.value };
                    onChange(next);
                  }}
                />
                <span>{lv.label}</span>
              </label>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}
