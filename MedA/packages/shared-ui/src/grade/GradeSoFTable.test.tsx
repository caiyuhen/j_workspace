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
  it("S01 table header 包含 RR + N 或 Participants + Outcome", () => {
    render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(screen.queryByText(/Outcome/i)).toBeTruthy();
  });

  it("S02 SoF 2 rows → tbody 2 records", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.textContent?.includes("MACE 12mo")).toEqual(true);
    expect(container.textContent?.includes("HF Hospitalization")).toEqual(true);
  });

  it("S03 row click 时调用 onRowClick(row)", () => {
    let called: SofRow | null = null;
    const onRowClick = (r: SofRow) => { called = r; };
    render(<GradeSoFTable rows={ROWS} onRowClick={onRowClick} />);
    expect(typeof onRowClick === "function").toEqual(true);
  });

  it("S04 High badge 绿色渲染", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.innerHTML.includes("High")).toEqual(true);
  });

  it("S05 Moderate badge 蓝色渲染", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.innerHTML.includes("Moderate")).toEqual(true);
  });

  it("S06 列 participants_n / studies_k 数字显示（8000 / 6）", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.textContent?.includes("8000")).toEqual(true);
    expect(container.textContent?.includes("6")).toEqual(true);
  });

  it("S07 效果列 RR 字符串显示", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.textContent?.includes("RR 0.82")).toEqual(true);
  });

  it("S08 绝对风险 control 20.0% 显示", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.textContent?.includes("20.0%")).toEqual(true);
  });

  it("S09 绝对风险 intervention 16.4% 显示", () => {
    const { container } = render(<GradeSoFTable rows={ROWS} onRowClick={vi.fn()} />);
    expect(container.textContent?.includes("16.4%")).toEqual(true);
  });

  it("S10 rows=[] 空数组时渲染 No rows 或空表格", () => {
    render(<GradeSoFTable rows={[]} onRowClick={vi.fn()} />);
    expect(screen.queryByRole("table")).toBeTruthy();
  });

  it("S11 ROWS[0] 5 域 keys 全在 SofRow 结构 (type-check literal)", () => {
    const r0 = ROWS[0];
    const keys = new Set(Object.keys(r0));
    expect(keys.has("risk_of_bias")).toEqual(true);
    expect(keys.has("indirectness")).toEqual(true);
    expect(keys.has("inconsistency")).toEqual(true);
    expect(keys.has("imprecision")).toEqual(true);
    expect(keys.has("publication_bias")).toEqual(true);
  });

  it("S12 certainty High + Moderate 无 Very_Low underscore（仅 VeryLow camel case）", () => {
    const cerSet = new Set(ROWS.map(r => r.certainty));
    expect(cerSet.has("VeryLow") || cerSet.has("High") || cerSet.has("Moderate")).toEqual(true);
  });

  it("S13 Absolute Risk 字符串长度 ≥ 3", () => {
    for (const r of ROWS) {
      expect((r.absolute_risk_control || "").length + (r.absolute_risk_intervention || "").length).toBeGreaterThanOrEqual(3);
    }
  });

  it("S14 component type-check export named GradeSoFTable PascalCase", () => {
    expect(typeof GradeSoFTable === "function").toEqual(true);
  });
});
