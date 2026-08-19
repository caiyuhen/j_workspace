import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import { TrafficLightCell } from "./TrafficLightCell";
import { RoB2Matrix } from "./RoB2Matrix";
import type { RoB2Overall, RoB2DomainRating, TrafficLightRating } from "@meda/shared-sdk";

const makeDomains = (ratings: [string, TrafficLightRating][]): RoB2DomainRating[] =>
  ratings.map(([d, r]) => ({
    domain: d as RoB2DomainRating["domain"],
    rating: r,
    signal_answers: {},
    rationale: "",
  }));

const STUDY_A: RoB2Overall = {
  study_id: "S1",
  study_type: "RCT",
  domains: makeDomains([
    ["D1_randomization", "low"],
    ["D2_deviations", "some_concerns"],
    ["D3_missing", "high"],
    ["D4_measurement", "low"],
    ["D5_reporting", "critical"],
  ]),
  overall: "critical",
};

const STUDY_B: RoB2Overall = {
  study_id: "S2",
  study_type: "RCT",
  domains: makeDomains([
    ["D1_randomization", "low"],
    ["D2_deviations", "low"],
    ["D3_missing", "low"],
    ["D4_measurement", "low"],
    ["D5_reporting", "low"],
  ]),
  overall: "low",
};

const STUDY_C: RoB2Overall = {
  study_id: "S3",
  study_type: "RCT",
  domains: makeDomains([
    ["D1_randomization", "some_concerns"],
    ["D2_deviations", "some_concerns"],
    ["D3_missing", "low"],
    ["D4_measurement", "low"],
    ["D5_reporting", "low"],
  ]),
  overall: "some_concerns",
};

const STUDY_D: RoB2Overall = {
  study_id: "S4",
  study_type: "RCT",
  domains: makeDomains([
    ["D1_randomization", "high"],
    ["D2_deviations", "low"],
    ["D3_missing", "low"],
    ["D4_measurement", "low"],
    ["D5_reporting", "low"],
  ]),
  overall: "high",
};

const STUDY_E: RoB2Overall = {
  study_id: "S5",
  study_type: "NRSI",
  domains: makeDomains([
    ["D1_randomization", "ni"],
    ["D2_deviations", "ni"],
    ["D3_missing", "ni"],
    ["D4_measurement", "ni"],
    ["D5_reporting", "ni"],
  ]),
  overall: "ni",
};

const FIVE_STUDIES: RoB2Overall[] = [STUDY_A, STUDY_B, STUDY_C, STUDY_D, STUDY_E];

describe("TrafficLightCell", () => {
  it("Q1 TrafficLightCell low 颜色匹配 snapshot", () => {
    const { container } = render(<TrafficLightCell rating="low" />);
    const el = screen.getByTestId("tlc-low");
    const style = window.getComputedStyle(el);
    expect(style.backgroundColor).toBe("rgb(16, 185, 129)");
    expect(style.color).toBe("rgb(255, 255, 255)");
    expect(el.textContent).toContain("🟢");
  });

  it("Q2 TrafficLightCell some_concerns 颜色匹配 snapshot", () => {
    render(<TrafficLightCell rating="some_concerns" />);
    const el = screen.getByTestId("tlc-some_concerns");
    const style = window.getComputedStyle(el);
    expect(style.backgroundColor).toBe("rgb(251, 191, 36)");
    expect(style.color).toBe("rgb(120, 53, 15)");
    expect(el.textContent).toContain("🟡");
  });

  it("Q3 TrafficLightCell high 颜色匹配 snapshot", () => {
    render(<TrafficLightCell rating="high" />);
    const el = screen.getByTestId("tlc-high");
    const style = window.getComputedStyle(el);
    expect(style.backgroundColor).toBe("rgb(239, 68, 68)");
    expect(style.color).toBe("rgb(255, 255, 255)");
    expect(el.textContent).toContain("🔴");
  });

  it("Q4 TrafficLightCell critical 颜色匹配 snapshot", () => {
    render(<TrafficLightCell rating="critical" />);
    const el = screen.getByTestId("tlc-critical");
    const style = window.getComputedStyle(el);
    expect(style.backgroundColor).toBe("rgb(220, 38, 38)");
    expect(style.color).toBe("rgb(255, 255, 255)");
    expect(el.textContent).toContain("🔥");
  });

  it("Q5 TrafficLightCell ni 颜色匹配 snapshot", () => {
    render(<TrafficLightCell rating="ni" />);
    const el = screen.getByTestId("tlc-ni");
    const style = window.getComputedStyle(el);
    expect(style.backgroundColor).toBe("rgb(241, 245, 249)");
    expect(style.color).toBe("rgb(100, 116, 139)");
    expect(el.textContent).toContain("➖");
  });
});

describe("RoB2Matrix", () => {
  it("Q6 5域 × 5研究 S1 studyId 渲染正确", () => {
    render(<RoB2Matrix studies={FIVE_STUDIES} />);
    expect(screen.getByText("S1")).toBeTruthy();
  });

  it("Q7 5域 × 5研究 S2 studyId 渲染正确", () => {
    render(<RoB2Matrix studies={FIVE_STUDIES} />);
    expect(screen.getByText("S2")).toBeTruthy();
  });

  it("Q8 5域 × 5研究 S3 studyId 渲染正确", () => {
    render(<RoB2Matrix studies={FIVE_STUDIES} />);
    expect(screen.getByText("S3")).toBeTruthy();
  });

  it("Q9 5域 × 5研究 S4 studyId 渲染正确", () => {
    render(<RoB2Matrix studies={FIVE_STUDIES} />);
    expect(screen.getByText("S4")).toBeTruthy();
  });

  it("Q10 5域 × 5研究 S5 studyId 渲染正确", () => {
    render(<RoB2Matrix studies={FIVE_STUDIES} />);
    expect(screen.getByText("S5")).toBeTruthy();
  });

  it("Q11 editable=false → onCellChange 无触发", () => {
    const onCellChange = vi.fn();
    render(<RoB2Matrix studies={FIVE_STUDIES} editable={false} onCellChange={onCellChange} />);
    const cells = document.querySelectorAll("[data-testid^='tlc-']");
    cells.forEach((c) => {
      fireEvent.click(c);
    });
    expect(onCellChange).not.toHaveBeenCalled();
  });

  it("Q12 Overall 列 3px 重边框 (CSS)", () => {
    const { container } = render(<RoB2Matrix studies={FIVE_STUDIES} />);
    const overallCol = container.querySelector(".rob2-overall-col");
    expect(overallCol).toBeTruthy();
    const style = window.getComputedStyle(overallCol!);
    expect(style.borderLeftWidth).toBe("3px");
  });

  it("Q13 NRSI 研究 → cell 显示 ROBINS-I 文字", () => {
    render(<RoB2Matrix studies={FIVE_STUDIES} />);
    expect(screen.queryAllByText(/ROBINS-I/i).length).toBeGreaterThan(0);
  });

  it("Q14 GRADE badge '-1' 出现在标题右侧", () => {
    const { container } = render(<RoB2Matrix studies={FIVE_STUDIES} gradeDowngrade="-1" />);
    const badge = container.querySelector(".rob2-grade-badge");
    expect(badge).toBeTruthy();
    expect(badge!.textContent).toContain("-1");
  });

  it("Q15 onCellChange 传参 (studyId, domain='D3', rating='high') 正确触发", () => {
    const onCellChange = vi.fn();
    const studies: RoB2Overall[] = [STUDY_A];
    render(<RoB2Matrix studies={studies} editable={true} onCellChange={onCellChange} />);
    const s1Row = screen.getByText("S1").closest("tr");
    expect(s1Row).toBeTruthy();
    const cells = within(s1Row!).getAllByTestId(/tlc-/);
    const d3Cell = cells[2];
    fireEvent.click(d3Cell);
    expect(onCellChange).toHaveBeenCalledWith("S1", "D3_missing", "high");
  });
});
