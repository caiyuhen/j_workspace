import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { DashboardOutputsW84 } from "../dashboard/DashboardOutputsW84";
import type { OutputStageCard, SofRow, Prisma2020Checklist, ReportSnapshot } from "@meda/shared-sdk";

const CARDS: OutputStageCard[] = [
  { card_key: "protocol_report_draft", ready: true, locked_reason: null },
  { card_key: "sof_attachments_ready", ready: true, locked_reason: null },
  { card_key: "export_version_snapshots_ready", ready: false, locked_reason: "exports_requires_at_least_one_report_snapshot" },
];

const SOF: SofRow[] = [
  {
    project_id: 1, outcome_id: 1, outcome_label: "MACE", participants_n: 5000, studies_k: 5,
    effect_measure_label: "RR 0.82", risk_of_bias: "no_concerns", indirectness: "no_concerns",
    inconsistency: "no_concerns", imprecision: "some_concerns", publication_bias: "no_concerns",
    certainty: "Moderate", absolute_risk_control: "20.0%", absolute_risk_intervention: "16.4%", comments: "",
  },
];

function _make_prisma(): Prisma2020Checklist {
  const base: any = { id: 1, project_id: 1, reviewer_id: 1, locked: false, note: "", created_at: new Date().toISOString() };
  for (let i = 1; i <= 27; i++) base[`item_${i}`] = i <= 10;
  return base as Prisma2020Checklist;
}

const SNAPS: ReportSnapshot[] = [
  {
    id: 1, project_id: 1, version_label: "v0.1",
    sha256_grade: "a".repeat(64), sha256_analysis: "b".repeat(64),
    md_content: "# M", html_content: "<html>M</html>", txt_content: "TXT M",
    created_at: new Date().toISOString(),
  },
];

describe("DashboardOutputsW84 T10", () => {
  it("D04 dashboard-outputs-w84 class in container className（render 无 throw）", () => {
    const { container } = render(
      <DashboardOutputsW84
        outputStageCards={CARDS}
        gradeRows={[]}
        sofRows={SOF}
        prisma={_make_prisma()}
        snapshots={SNAPS}
        onExport={function(){}}
        onDownloadSnapshot={function(){}}
        onPrismaChange={function(){}}
      />
    );
    const root = container.querySelector(".dashboard-outputs-w84");
    expect(root).toBeTruthy();
  });

  it("D05 传入 null gradeRows + empty sofRows → 不应 crash (safe fallback)", () => {
    let threw = false;
    try {
      render(
        <DashboardOutputsW84
          outputStageCards={CARDS}
          gradeRows={null as any}
          sofRows={[]}
          prisma={null as any}
          snapshots={[]}
          onExport={() => {}}
          onDownloadSnapshot={() => {}}
          onPrismaChange={() => {}}
        />
      );
    } catch {
      threw = true;
    }
    expect(threw).toEqual(false);
  });

  it("D06 所有 8 组件 已在 Dashboard 中可访问组合 (render 0 throw)", () => {
    const { container } = render(
      <DashboardOutputsW84
        outputStageCards={null as any}
        gradeRows={[]}
        sofRows={[]}
        prisma={_make_prisma()}
        snapshots={[]}
        onExport={() => {}}
        onDownloadSnapshot={() => {}}
        onPrismaChange={() => {}}
      />
    );
    expect(container).toBeTruthy();
  });
});
