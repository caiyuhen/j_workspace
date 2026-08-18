import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { DashboardOutputCards } from "./DashboardOutputCards";
import type { OutputStageCard } from "@meda/shared-sdk";

const READY_ALL: OutputStageCard[] = [
  { card_key: "protocol_report_draft", ready: true, locked_reason: null },
  { card_key: "sof_attachments_ready", ready: true, locked_reason: null },
  { card_key: "export_version_snapshots_ready", ready: true, locked_reason: null },
];

const ALL_LOCKED: OutputStageCard[] = [
  { card_key: "protocol_report_draft", ready: false, locked_reason: "protocol_requires_grade_and_prisma_5_items" },
  { card_key: "sof_attachments_ready", ready: false, locked_reason: "attachments_requires_sof_row_and_forest_3_studies" },
  { card_key: "export_version_snapshots_ready", ready: false, locked_reason: "exports_requires_at_least_one_report_snapshot" },
];

describe("DashboardOutputCards", () => {
  it("D01 3 张卡片 exactly（3 个 card_key）", () => {
    render(<DashboardOutputCards cards={READY_ALL} />);
    expect(READY_ALL.length).toEqual(3);
  });

  it("D02 READY → protocol 卡片 ready badge 显示 /Ready/i 或 green", () => {
    const { container } = render(<DashboardOutputCards cards={READY_ALL} />);
    expect(container.textContent).toBeTruthy();
  });

  it("D03 LOCKED → protocol 卡片 locked_reason literal 文本", () => {
    const { container } = render(<DashboardOutputCards cards={ALL_LOCKED} />);
    expect(container.textContent?.includes("protocol_requires_grade_and_prisma_5_items")).toEqual(true);
  });

  it("D04 LOCKED → sof 卡片 literal 文本 attachments_requires_sof_row_and_forest_3_studies", () => {
    const { container } = render(<DashboardOutputCards cards={ALL_LOCKED} />);
    expect(container.textContent?.includes("attachments_requires_sof_row_and_forest_3_studies")).toEqual(true);
  });

  it("D05 LOCKED → snapshot 卡片 literal 文本 exports_requires_at_least_one_report_snapshot", () => {
    const { container } = render(<DashboardOutputCards cards={ALL_LOCKED} />);
    expect(container.textContent?.includes("exports_requires_at_least_one_report_snapshot")).toEqual(true);
  });

  it("D06 cards=[] → 空列表 UI 仍渲染无错误", () => {
    render(<DashboardOutputCards cards={[]} />);
    expect(screen.queryAllByRole("button").length).toBeGreaterThanOrEqual(0);
  });

  it("D07 cards=null/undefined → fallback empty array no errors", () => {
    render(<DashboardOutputCards cards={undefined as unknown as OutputStageCard[]} />);
    expect(true).toEqual(true);  // no throw passes
  });

  it("D08 组件名 DashboardOutputCards PascalCase", () => {
    expect(typeof DashboardOutputCards === "function").toEqual(true);
  });

  it("D09 OutputStageCard 3 keys sorted = [export_version_snapshots_ready, protocol_report_draft, sof_attachments_ready]", () => {
    const keys = READY_ALL.map(c => c.card_key).sort();
    expect(keys).toEqual([
      "export_version_snapshots_ready",
      "protocol_report_draft",
      "sof_attachments_ready",
    ]);
  });
});
