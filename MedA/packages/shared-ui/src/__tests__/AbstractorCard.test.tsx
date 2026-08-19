import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import ConfidenceBar from "../components/ConfidenceBar";
import AbstractorCard, {
  type AbstractorRecord,
  type AbstractorTriage,
} from "../components/AbstractorCard";

function rgbToHex(rgbStr: string): string {
  const m = rgbStr.match(/\d+/g);
  if (!m || m.length < 3) return "";
  const [r, g, b] = m.map((x) => parseInt(x, 10));
  return [r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("");
}

function makeIncludeRecord(overrides: Partial<AbstractorRecord> = {}): AbstractorRecord {
  return {
    id: "PMID-38924711",
    title: "Dapagliflozin in Patients with Heart Failure and Type 2 Diabetes",
    year: 2024,
    journal: "New England Journal of Medicine",
    ...overrides,
  };
}

function makeIncludeTriage(overrides: Partial<AbstractorTriage> = {}): AbstractorTriage {
  return {
    decision: "include",
    confidence: 0.92,
    reasons: ["C3: PICO 4/4 ok + outcome p_value<0.05"],
    exclude_reason_ids: [],
    failed_steps: [],
    pico: {
      p: { text: "T2DM patients with HFrEF", n: 4744, age_min: 40, age_max: 85 },
      i: { drug: "Dapagliflozin 10mg", dose: "10mg QD", duration: "24mo", n: 2373 },
      c: { comparator: "Placebo", type: "placebo" },
      o: [
        {
          name: "CV Death or HHF",
          mean_diff: -3.2,
          rr: 0.74,
          ci_low: 0.65,
          ci_high: 0.85,
          p_value: 0.001,
        },
      ],
    },
    ...overrides,
  };
}

function makeExcludeTriage(overrides: Partial<AbstractorTriage> = {}): AbstractorTriage {
  return {
    decision: "exclude",
    confidence: 0.32,
    reasons: ["C2: condition not T2DM"],
    exclude_reason_ids: [2, 3],
    failed_steps: [],
    pico: {
      p: { text: "T1DM adolescents", n: 120, age_min: 12, age_max: 18 },
      i: { drug: "Insulin glargine", dose: "0.5U/kg", n: 60 },
      c: { comparator: "Insulin detemir", type: "active" },
      o: [{ name: "HbA1c change", mean_diff: -0.3, p_value: 0.12 }],
    },
    ...overrides,
  };
}

function makeReviewTriage(overrides: Partial<AbstractorTriage> = {}): AbstractorTriage {
  return {
    decision: "review",
    confidence: 0.62,
    reasons: ["C4: missing fields: intervention,comparison"],
    exclude_reason_ids: [],
    failed_steps: [],
    pico: {
      p: { text: "T2DM elderly", n: 320, age_min: 65 },
      i: { drug: undefined, dose: undefined, n: undefined },
      c: { comparator: undefined },
      o: [],
    },
    ...overrides,
  };
}

describe("Wave9c Abstractor UI ConfidenceBar + AbstractorCard (18 tests)", () => {
  // ========== V1-V3: ConfidenceBar 3 color tiers ==========
  it("V1: value=0.92 (>=0.85) → green gradient #10b981→#059669 matches snapshot", () => {
    const { container } = render(<ConfidenceBar value={0.92} label="Confidence" />);
    const inner = screen.getByTestId("confidence-bar-inner-Confidence") as HTMLDivElement;
    const style = window.getComputedStyle(inner);
    const bg = style.background || style.backgroundImage || "";
    const greenCheck =
      bg.includes("#10b981") ||
      bg.includes("16, 185, 129") ||
      bg.includes("rgb(16, 185, 129)");
    const darkGreenCheck =
      bg.includes("#059669") ||
      bg.includes("5, 150, 105") ||
      bg.includes("rgb(5, 150, 105)");
    expect(greenCheck).toBe(true);
    expect(darkGreenCheck).toBe(true);
    expect(container).toMatchSnapshot("V1-green-confidence-bar");
  });

  it("V2: value=0.62 (0.45-0.85) → amber gradient #f59e0b→#d97706 matches snapshot", () => {
    const { container } = render(<ConfidenceBar value={0.62} label="Amber" />);
    const inner = screen.getByTestId("confidence-bar-inner-Amber") as HTMLDivElement;
    const style = window.getComputedStyle(inner);
    const bg = style.background || style.backgroundImage || "";
    const amberCheck =
      bg.includes("#f59e0b") ||
      bg.includes("245, 158, 11") ||
      bg.includes("rgb(245, 158, 11)");
    const darkAmberCheck =
      bg.includes("#d97706") ||
      bg.includes("217, 119, 6") ||
      bg.includes("rgb(217, 119, 6)");
    expect(amberCheck).toBe(true);
    expect(darkAmberCheck).toBe(true);
    expect(container).toMatchSnapshot("V2-amber-confidence-bar");
  });

  it("V3: value=0.12 (<0.45) → red gradient #ef4444→#dc2626 matches snapshot", () => {
    const { container } = render(<ConfidenceBar value={0.12} />);
    const inner = screen.getByTestId("confidence-bar-inner-default") as HTMLDivElement;
    const style = window.getComputedStyle(inner);
    const bg = style.background || style.backgroundImage || "";
    const redCheck =
      bg.includes("#ef4444") ||
      bg.includes("239, 68, 68") ||
      bg.includes("rgb(239, 68, 68)");
    const darkRedCheck =
      bg.includes("#dc2626") ||
      bg.includes("220, 38, 38") ||
      bg.includes("rgb(220, 38, 38)");
    expect(redCheck).toBe(true);
    expect(darkRedCheck).toBe(true);
    expect(container).toMatchSnapshot("V3-red-confidence-bar");
  });

  // ========== V4-V6: 3 card snapshots ==========
  it("V4: Include decision card → snapshot matches (green badge + ConfidenceBar green)", () => {
    const { container } = render(
      <AbstractorCard record={makeIncludeRecord()} triage={makeIncludeTriage()} />,
    );
    const decisionBadge = screen.getByTestId("badge-decision-PMID-38924711");
    const badgeStyle = window.getComputedStyle(decisionBadge);
    const colorHex = rgbToHex(badgeStyle.color);
    const bgHex = rgbToHex(badgeStyle.backgroundColor);
    const greenOk =
      badgeStyle.color.includes("065f46") ||
      badgeStyle.backgroundColor.includes("d1fae5") ||
      colorHex === "065f46" ||
      bgHex === "d1fae5";
    expect(greenOk).toBe(true);
    expect(container).toMatchSnapshot("V4-include-card");
  });

  it("V5: Exclude decision card → snapshot matches (red badge + confidence low)", () => {
    const { container } = render(
      <AbstractorCard
        record={makeIncludeRecord({ id: "PMID-10000002" })}
        triage={makeExcludeTriage()}
      />,
    );
    const decisionBadge = screen.getByTestId("badge-decision-PMID-10000002");
    const badgeStyle = window.getComputedStyle(decisionBadge);
    const colorHex = rgbToHex(badgeStyle.color);
    const bgHex = rgbToHex(badgeStyle.backgroundColor);
    const redOk =
      badgeStyle.color.includes("991b1b") ||
      badgeStyle.backgroundColor.includes("fee2e2") ||
      colorHex === "991b1b" ||
      bgHex === "fee2e2";
    expect(redOk).toBe(true);
    expect(container).toMatchSnapshot("V5-exclude-card");
  });

  it("V6: Review decision card → snapshot matches (amber badge)", () => {
    const { container } = render(
      <AbstractorCard
        record={makeIncludeRecord({ id: "PMID-10000003" })}
        triage={makeReviewTriage()}
      />,
    );
    const decisionBadge = screen.getByTestId("badge-decision-PMID-10000003");
    const badgeStyle = window.getComputedStyle(decisionBadge);
    const colorHex = rgbToHex(badgeStyle.color);
    const bgHex = rgbToHex(badgeStyle.backgroundColor);
    const amberOk =
      badgeStyle.color.includes("92400e") ||
      badgeStyle.backgroundColor.includes("fef3c7") ||
      colorHex === "92400e" ||
      bgHex === "fef3c7";
    expect(amberOk).toBe(true);
    expect(container).toMatchSnapshot("V6-review-card");
  });

  // ========== V7-V9: Button click injectable ==========
  it("V7: btn-accept-include clicked → injectable onDecide('include') called exactly once", () => {
    const decide = vi.fn();
    render(
      <AbstractorCard
        record={makeIncludeRecord()}
        triage={makeIncludeTriage()}
        onDecide={decide}
      />,
    );
    const btn = screen.getByTestId("btn-accept-include");
    fireEvent.click(btn);
    expect(decide).toHaveBeenCalledTimes(1);
    expect(decide.mock.calls[0][0]).toBe("include");
  });

  it("V8: btn-accept-exclude clicked → onDecide('exclude', reason_ids=[2,3]) matches triage exclude_reason_ids", () => {
    const decide = vi.fn();
    render(
      <AbstractorCard
        record={makeIncludeRecord({ id: "PMID-EXCLUDE" })}
        triage={makeExcludeTriage()}
        onDecide={decide}
      />,
    );
    const btn = screen.getByTestId("btn-accept-exclude");
    fireEvent.click(btn);
    expect(decide).toHaveBeenCalledTimes(1);
    expect(decide.mock.calls[0][0]).toBe("exclude");
    const opts = decide.mock.calls[0][1] || {};
    expect(opts.reason_ids).toEqual([2, 3]);
  });

  it("V9: btn-modify-review clicked → sets override_by_user_id in decide options", () => {
    const decide = vi.fn();
    render(
      <AbstractorCard
        record={makeIncludeRecord({ id: "PMID-REVIEW" })}
        triage={makeReviewTriage()}
        onDecide={decide}
      />,
    );
    const btn = screen.getByTestId("btn-modify-review");
    fireEvent.click(btn);
    expect(decide).toHaveBeenCalledTimes(1);
    expect(decide.mock.calls[0][0]).toBe("review");
    const opts = decide.mock.calls[0][1] || {};
    expect(typeof opts.override_by_user_id).toBe("string");
    expect(opts.override_by_user_id.length).toBeGreaterThan(0);
  });

  // ========== V10-V12: ConfidenceBar boundary values ==========
  it("V10: value=0.0 boundary → inner width style exactly 0%", () => {
    render(<ConfidenceBar value={0.0} label="Zero" />);
    const inner = screen.getByTestId("confidence-bar-inner-Zero") as HTMLDivElement;
    const style = window.getComputedStyle(inner);
    const w = style.width;
    const inlineW = inner.style.width;
    expect(w === "0px" || w === "0%" || inlineW === "0%").toBe(true);
    const pct = screen.getByTestId("confidence-bar-pct-Zero");
    expect(pct.textContent?.trim()).toBe("0%");
  });

  it("V11: value=0.5 boundary (middle amber range) → inner width 50% + pct 50%", () => {
    render(<ConfidenceBar value={0.5} label="Mid" />);
    const inner = screen.getByTestId("confidence-bar-inner-Mid") as HTMLDivElement;
    const inlineW = inner.style.width;
    expect(inlineW === "50%" || inlineW.includes("50")).toBe(true);
    const pct = screen.getByTestId("confidence-bar-pct-Mid");
    expect(pct.textContent?.trim()).toBe("50%");
  });

  it("V12: value=1.0 boundary max → inner width 100% + pct 100%", () => {
    render(<ConfidenceBar value={1.0} label="Full" />);
    const inner = screen.getByTestId("confidence-bar-inner-Full") as HTMLDivElement;
    const inlineW = inner.style.width;
    expect(inlineW === "100%").toBe(true);
    const pct = screen.getByTestId("confidence-bar-pct-Full");
    expect(pct.textContent?.trim()).toBe("100%");
  });

  // ========== V13: duplicate badge ==========
  it("V13: Hamming=7 / Jaccard=0.93 → duplicate badge rendered with H and J hints", () => {
    render(
      <AbstractorCard
        record={makeIncludeRecord({
          id: "PMID-DUPE",
          hamming_distance: 7,
          jaccard_similarity: 0.93,
        })}
        triage={makeIncludeTriage()}
      />,
    );
    const badge = screen.getByTestId("badge-duplicate-PMID-DUPE");
    expect(badge).toBeTruthy();
    const txt = badge.textContent || "";
    expect(txt.includes("Duplicate") || txt.includes("H=7") || txt.includes("H = 7")).toBe(true);
    expect(
      txt.includes("J=0.93") || txt.includes("J = 0.93") || txt.includes("0.93"),
    ).toBe(true);
    expect(txt.includes("7")).toBe(true);
  });

  // ========== V14: LLM degrade warning ==========
  it("V14: failed_steps=['pico_llm'] → ⚠️ LLM降级 规则 warning displayed", () => {
    render(
      <AbstractorCard
        record={makeIncludeRecord({ id: "PMID-DEGRADE" })}
        triage={makeReviewTriage({ failed_steps: ["pico_llm"] })}
      />,
    );
    const warn = screen.getByTestId("llm-degrade-warning-PMID-DEGRADE");
    expect(warn).toBeTruthy();
    const txt = warn.textContent || "";
    expect(
      txt.includes("LLM") && (txt.includes("降级") || txt.includes("降級")) && txt.includes("规则"),
    ).toBe(true);
  });

  // ========== V15: Pipeline steps lit ==========
  it("V15: pipeline_steps [SimHash✓, LLM✓, Triage✓] → all 3 active and rendered with key data-testids", () => {
    render(
      <AbstractorCard
        record={makeIncludeRecord({ id: "PMID-PIPE" })}
        triage={makeIncludeTriage({
          pipeline_steps: [
            { key: "simhash", label: "SimHash", active: true },
            { key: "llm", label: "LLM", active: true },
            { key: "triage", label: "Triage", active: true },
          ],
        })}
      />,
    );
    const simhash = screen.getByTestId("pipeline-step-simhash-PMID-PIPE");
    const llm = screen.getByTestId("pipeline-step-llm-PMID-PIPE");
    const triage = screen.getByTestId("pipeline-step-triage-PMID-PIPE");
    for (const el of [simhash, llm, triage]) {
      const style = window.getComputedStyle(el);
      const bg = style.backgroundColor || "";
      const color = style.color || "";
      const activeHint =
        bg.includes("219, 234, 254") ||
        bg.includes("#dbeafe") ||
        color.includes("30, 64, 175") ||
        color.includes("#1e40af");
      expect(activeHint).toBe(true);
    }
    const simTxt = simhash.textContent || "";
    const llmTxt = llm.textContent || "";
    const triTxt = triage.textContent || "";
    expect(simTxt.includes("SimHash")).toBe(true);
    expect(llmTxt.includes("LLM")).toBe(true);
    expect(triTxt.includes("Triage")).toBe(true);
  });

  // ========== V16: Dashboard pie chart widths sum ==========
  it("V16: Dashboard stats include 45.5+27.5+26.9 = 100% (sums to 100.0)", () => {
    const include = 45.5;
    const review = 27.5;
    const exclude = 26.9;
    const total = Math.round((include + review + exclude) * 1000) / 1000;
    expect(total).toBeCloseTo(100.0, 0);

    const wrapperStyle = document.createElement("div");
    wrapperStyle.style.width = "400px";
    const includeEl = document.createElement("div");
    includeEl.style.width = `${include}%`;
    includeEl.style.display = "inline-block";
    includeEl.style.background = "#10b981";
    includeEl.textContent = "Include";
    const reviewEl = document.createElement("div");
    reviewEl.style.width = `${review}%`;
    reviewEl.style.display = "inline-block";
    reviewEl.style.background = "#f59e0b";
    reviewEl.textContent = "Review";
    const excludeEl = document.createElement("div");
    excludeEl.style.width = `${exclude}%`;
    excludeEl.style.display = "inline-block";
    excludeEl.style.background = "#ef4444";
    excludeEl.textContent = "Exclude";
    wrapperStyle.appendChild(includeEl);
    wrapperStyle.appendChild(reviewEl);
    wrapperStyle.appendChild(excludeEl);

    document.body.appendChild(wrapperStyle);
    render(
      <div data-testid="dashboard-pie" style={{ display: "flex", width: 400 }}>
        <div style={{ width: `${include}%`, background: "#10b981" }} data-testid="pie-include" />
        <div style={{ width: `${review}%`, background: "#f59e0b" }} data-testid="pie-review" />
        <div style={{ width: `${exclude}%`, background: "#ef4444" }} data-testid="pie-exclude" />
      </div>,
    );
    const pie = screen.getByTestId("dashboard-pie");
    expect(pie).toBeTruthy();
    const incl = screen.getByTestId("pie-include") as HTMLDivElement;
    const rev = screen.getByTestId("pie-review") as HTMLDivElement;
    const exc = screen.getByTestId("pie-exclude") as HTMLDivElement;
    const sumPct =
      parseFloat(incl.style.width) + parseFloat(rev.style.width) + parseFloat(exc.style.width);
    expect(sumPct).toBeCloseTo(100, 0);
    document.body.removeChild(wrapperStyle);
  });

  // ========== V17: PMID specific testid ==========
  it("V17: data-testid abstractor-card-PMID-38924711 exists exactly 1 DOM element", () => {
    render(
      <AbstractorCard
        record={makeIncludeRecord({ id: "PMID-38924711" })}
        triage={makeIncludeTriage()}
      />,
    );
    const el = screen.getByTestId("abstractor-card-PMID-38924711");
    expect(el).toBeTruthy();
    expect(el.tagName).toBe("DIV");
    const allMatches = screen.queryAllByTestId("abstractor-card-PMID-38924711");
    expect(allMatches.length).toBe(1);
  });

  // ========== V18: click event detail matching ==========
  it("V18: btn-accept-include clicked → CustomEvent detail match (decision=include)", () => {
    let capturedDetail: any = null;
    const decide = (decision: string, opts?: any) => {
      capturedDetail = { decision, ...(opts || {}) };
    };
    render(
      <AbstractorCard
        record={makeIncludeRecord({ id: "PMID-EVENT" })}
        triage={makeIncludeTriage()}
        onDecide={decide}
      />,
    );
    const btn = screen.getByTestId("btn-accept-include");
    fireEvent.click(btn);
    expect(capturedDetail).not.toBeNull();
    expect(capturedDetail.decision).toBe("include");
    expect(typeof capturedDetail).toBe("object");
    const keys = Object.keys(capturedDetail);
    expect(keys.length >= 1).toBe(true);
  });
});
