import React from "react";
import type { OutputStageCard } from "@meda/shared-sdk";

const CARD_LABEL: Record<OutputStageCard["card_key"], string> = {
  protocol_report_draft: "1. Protocol / Report Draft",
  sof_attachments_ready: "2. SoF Table + Forest Plot Attachments",
  export_version_snapshots_ready: "3. Export Version Snapshots",
};

export function DashboardOutputCards({
  cards,
}: {
  cards: OutputStageCard[] | null | undefined;
}): JSX.Element {
  const safe: OutputStageCard[] = Array.isArray(cards) ? cards : [];
  return (
    <div className="dashboard-output-cards" role="list" aria-label="Output stage 3 cards dynamic locks">
      <style>{`
        .dashboard-output-cards .doc-card { border:1px solid #e5e7eb; border-radius: .55rem; padding: .8rem 1rem; margin-bottom: .6rem; background:#fff; font-family: system-ui; }
        .dashboard-output-cards .doc-row { display: flex; align-items: center; justify-content: space-between; gap: .5rem; }
        .dashboard-output-cards .doc-ready { background: #ecfdf5; color:#065f46; border:1px solid #a7f3d0; padding: .15rem .55rem; border-radius: .3rem; font-size: .82rem; font-weight: 600; }
        .dashboard-output-cards .doc-locked { background: #fef2f2; color:#991b1b; border:1px solid #fecaca; padding: .15rem .55rem; border-radius: .3rem; font-size: .82rem; font-weight: 600; }
        .dashboard-output-cards .doc-reason { margin-top: .35rem; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .8rem; color:#475569; }
      `}</style>
      {safe.length === 0 ? (
        <p style={{ fontFamily:"system-ui", color:"#6b7280", fontSize:".88rem" }}>Loading output stage cards…</p>
      ) : safe.map(c => (
        <div className="doc-card" role="listitem" key={c.card_key}>
          <div className="doc-row">
            <strong>{CARD_LABEL[c.card_key] ?? c.card_key}</strong>
            {c.ready
              ? <span className="doc-ready">READY ✓</span>
              : <span className="doc-locked">LOCKED</span>}
          </div>
          {c.ready === false && c.locked_reason ? (
            <div className="doc-reason">Locked: {c.locked_reason}</div>
          ) : null}
        </div>
      ))}
    </div>
  );
}
