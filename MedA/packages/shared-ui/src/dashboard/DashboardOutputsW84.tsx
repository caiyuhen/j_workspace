import React from "react";
import { DashboardOutputCards } from "../report/DashboardOutputCards";
import { GradeSoFTable } from "../grade/GradeSoFTable";
import { Prisma2020Checklist27 } from "../report/Prisma2020Checklist27";
import { ReportSnapshotList } from "../report/ReportSnapshotList";
import { ReportExportMenu3Formats } from "../report/ReportExportMenu3Formats";
import type { OutputStageCard, SofRow, Prisma2020Checklist, ReportSnapshot } from "@meda/shared-sdk";

export function DashboardOutputsW84({
  outputStageCards,
  gradeRows,
  sofRows,
  prisma,
  snapshots,
  onExport,
  onDownloadSnapshot,
  onPrismaChange,
}: {
  outputStageCards: OutputStageCard[] | null | undefined;
  gradeRows: any[] | null | undefined;
  sofRows: SofRow[] | null | undefined;
  prisma: Prisma2020Checklist | null | undefined;
  snapshots: ReportSnapshot[] | null | undefined;
  onExport: (x: { format: "md" | "html" | "txt" }) => void;
  onDownloadSnapshot: (x: { id: number; format: "md" | "html" | "txt" }) => void;
  onPrismaChange: (next: Prisma2020Checklist) => void;
}): JSX.Element {
  const safeCards: OutputStageCard[] = Array.isArray(outputStageCards) ? outputStageCards : [];
  const safeSof: SofRow[] = Array.isArray(sofRows) ? sofRows : [];
  const safeSnaps: ReportSnapshot[] = Array.isArray(snapshots) ? snapshots : [];

  return (
    <div className="dashboard-outputs-w84" aria-label="Dashboard Outputs W84 Stage">
      <style>{`
        .dashboard-outputs-w84 { display: flex; flex-direction: column; gap: 1rem; padding: 1rem; font-family: system-ui, sans-serif; }
        .dashboard-outputs-w84 .dows84-section { border: 1px solid #e5e7eb; border-radius: .55rem; padding: 1rem; background:#fff; }
        .dashboard-outputs-w84 h2.section-title { font-size:1rem; margin: 0 0 .7rem; font-weight:700; color:#0f172a; }
      `}</style>

      <div className="dows84-section">
        <h2 className="section-title">Stage 6 · Output Stage (Dynamic Locks)</h2>
        <DashboardOutputCards cards={safeCards} />
      </div>

      <div className="dows84-section">
        <h2 className="section-title">Summary of Findings (SoF)</h2>
        <GradeSoFTable rows={safeSof} />
      </div>

      {prisma ? (
        <div className="dows84-section">
          <h2 className="section-title">PRISMA 2020 Checklist (27 items)</h2>
          <Prisma2020Checklist27 value={prisma} onChange={onPrismaChange} />
        </div>
      ) : null}

      <div className="dows84-section">
        <h2 className="section-title">Version Exports (Report Snapshots)</h2>
        <ReportExportMenu3Formats onExport={onExport} disabled={safeSnaps.length === 0} />
        <div style={{ marginTop: ".8rem" }}>
          <ReportSnapshotList snapshots={safeSnaps} onDownload={onDownloadSnapshot} />
        </div>
      </div>
    </div>
  );
}
