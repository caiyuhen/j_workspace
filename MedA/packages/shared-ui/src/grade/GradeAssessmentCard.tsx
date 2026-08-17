import React from "react";
import { GradeDomainScorer5 } from "./GradeDomainScorer5";
import { GradeUpgradeScorer3 } from "./GradeUpgradeScorer3";
import type { Grade5Domains, Grade3Upgrades, GradeCertaintyFinal } from "@meda/shared-sdk";

const COLOR: Record<GradeCertaintyFinal, string> = {
  High: "#166534", Moderate: "#1d4ed8", Low: "#b45309", VeryLow: "#7f1d1d",
};

export function GradeAssessmentCard({
  outcomeLabel, reviewerLabel,
  domains, upgrades, certaintyFinal,
  onDomainsChange, onUpgradesChange,
  onSave, onLock,
  locked = false,
}: {
  outcomeLabel: string;
  reviewerLabel: string;
  domains: Grade5Domains;
  upgrades: Grade3Upgrades;
  certaintyFinal: GradeCertaintyFinal;
  onDomainsChange: (next: Grade5Domains) => void;
  onUpgradesChange: (next: Grade3Upgrades) => void;
  onSave: () => void;
  onLock: () => void;
  locked?: boolean;
}): JSX.Element {
  return (
    <div className="grade-assessment-card" style={{ border: "1px solid #e5e7eb", padding: "1rem", borderRadius: ".5rem", background: "#fff" }}>
      <style>{`
        .grade-assessment-card .gac-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:.6rem; }
        .grade-assessment-card .gac-title { font-weight: 700; font-size: 1rem; }
        .grade-assessment-card .gac-certainty { padding:.15rem .55rem; color:#fff; font-weight:600; border-radius:.3rem; font-family: system-ui; }
        .grade-assessment-card .gac-actions { display:flex; gap: .4rem; margin-top:.6rem; }
      `}</style>
      <div className="gac-header">
        <div>
          <div className="gac-title">{outcomeLabel}</div>
          <div style={{ fontSize: ".8rem", color: "#4b5563" }}>Reviewer: {reviewerLabel}</div>
        </div>
        <span className="gac-certainty" style={{ backgroundColor: COLOR[certaintyFinal] }}>{certaintyFinal}</span>
      </div>
      <GradeDomainScorer5 value={domains} onChange={onDomainsChange} locked={locked} />
      <div style={{ marginTop: ".6rem" }}>
        <GradeUpgradeScorer3 value={upgrades} onChange={onUpgradesChange} certainty={certaintyFinal} locked={locked} />
      </div>
      <div className="gac-actions">
        <button type="button" onClick={onSave} disabled={locked}>Save</button>
        <button type="button" onClick={onLock} disabled={locked}>{locked ? "Unlock" : "Lock"}</button>
      </div>
    </div>
  );
}
