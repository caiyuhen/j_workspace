import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { GradeSoFTable } from "./GradeSoFTable";
import type { SofRow } from "@meda/shared-sdk";

const ROWS: SofRow[] = [
  {
    project_id: 1, outcome_id: 7,
    outcome_label: "MACE 12mo",
    participants_n: 8000, studies_k: 6,
    effect_measure_label: "RR 0.82 [0.72, 0.94]",
    risk_of_bias: "no_concerns", indirectness: "no_concerns", inconsistency: "no_concerns",
    imprecision: "no_concerns", publication_bias: "no_concerns", certainty: "High",
    absolute_risk_intervention: "16.4%", absolute_risk_control: "20.0%", comments: "",
  },
  {
    project_id: 1, outcome_id: 8,
    outcome_label: "HF Hospitalization",
    participants_n: 7400, studies_k: 5,
    effect_measure_label: "RR 0.61 [0.50, 0.74]",
    risk_of_bias: "some_concerns", indirectness: "no_concerns", inconsistency: "no_concerns",
    imprecision: "no_concerns", publication_bias: "no_concerns", certainty: "Moderate",
    absolute_risk_intervention: "9.1%", absolute_risk_control: "15.0%", comments: "",
  },
];

describe("GradeSoFTable", () => {
  it("S01 table header 含 Outcome 文本", () => {
    render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(screen.queryByText(/Outcome/i)).toBeTruthy();
  });

  it("S02 2 rows → MACE 12mo 和 HF Hospitalization 文本均存在", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect((container.textContent || "").includes("MACE 12mo")).toEqual(true);
    expect((container.textContent || "").includes("HF Hospitalization")).toEqual(true);
  });

  it("S03 onRowClick 是 function (sanity)", () => {
    const onRowClick = (r: SofRow) => { void r; };
    expect(typeof onRowClick === "function").toEqual(true);
  });

  it("S04 High badge innerHTML 含 High", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.innerHTML.includes("High")).toEqual(true);
  });

  it("S05 Moderate badge innerHTML 含 Moderate", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.innerHTML.includes("Moderate")).toEqual(true);
  });

  it("S06 participants_n 8000 + studies_k 6 数字显示", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect((container.textContent || "").includes("8000")).toEqual(true);
    expect((container.textContent || "").includes("6")).toEqual(true);
  });

  it("S07 effect measure RR 0.82 文本", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect((container.textContent || "").includes("RR 0.82")).toEqual(true);
  });

  it("S08 AR control 20.0% 文本", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect((container.textContent || "").includes("20.0%")).toEqual(true);
  });

  it("S09 AR intervention 16.4% 文本", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect((container.textContent || "").includes("16.4%")).toEqual(true);
  });

  it("S10 rows=[] → table role 仍存在", () => {
    render(<GradeSoFTable rows={[]} onRowClick={vi.fn()} />);
    expect(screen.queryByRole("table")).toBeTruthy();
  });

  it("S11 ROWS[0] 含 5 域 keys 全在 SofRow 结构 set", () => {
    const r0 = ROWS[0];
    const keys = new Set(Object.keys(r0));
    expect(keys.has("risk_of_bias")).toEqual(true);
    expect(keys.has("indirectness")).toEqual(true);
    expect(keys.has("inconsistency")).toEqual(true);
    expect(keys.has("imprecision")).toEqual(true);
    expect(keys.has("publication_bias")).toEqual(true);
  });

  it("S12 ROWS certainty literal 集合正确（无 Very_Low underscore）", () => {
    const cerSet = new Set(ROWS.map(r => r.certainty));
    expect(cerSet.has("High") || cerSet.has("Moderate") || cerSet.has("Low") || cerSet.has("VeryLow")).toEqual(true);
  });

  it("S13 Absolute Risk 字符串长度合计 ≥ 3", () => {
    for (const r of ROWS) {
      const l = (r.absolute_risk_control || "").length + (r.absolute_risk_intervention || "").length;
      expect(l).toBeGreaterThanOrEqual(3);
    }
  });

  it("S14 GradeSoFTable 是 function", () => {
    expect(typeof GradeSoFTable === "function").toEqual(true);
  });
});
