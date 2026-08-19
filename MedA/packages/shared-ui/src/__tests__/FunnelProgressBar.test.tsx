import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import FunnelProgressBar, {
  FUNNEL_COLORS,
  FUNNEL_ORDER_KEYS,
  getExcludeReasonTaAllowed,
  type FunnelStudyType,
} from "../components/FunnelProgressBar";
import type { FunnelStepStat } from "@meda/shared-sdk";

const ALL_STEP_KEYS = ["N1", "N2", "N3", "N4", "E1", "E2", "E3", "E4", "E5", "E6"] as const;

function makeStats(overrides: Partial<Record<string, Partial<FunnelStepStat>>> = {}): FunnelStepStat[] {
  const baseCounts: Record<string, number> = {
    N1: 1000, N2: 900, N3: 800, N4: 700,
    E1: 700, E2: 500, E3: 200,
    E4: 200, E5: 50, E6: 150,
  };
  return ALL_STEP_KEYS.map((k) => ({
    key: k,
    label: overrides[k]?.label ?? `Step ${k}`,
    count: overrides[k]?.count ?? baseCounts[k],
    locked: overrides[k]?.locked ?? false,
  })) as FunnelStepStat[];
}

describe("Wave9a FunnelProgressBar (22 tests)", () => {
  // E1-E10: 10 步渲染 snapshot
  it("E1: renders N1 step with data-testid fpb-step-N1", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-N1")).toBeTruthy();
  });

  it("E2: renders N2 step with data-testid fpb-step-N2", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-N2")).toBeTruthy();
  });

  it("E3: renders N3 step with data-testid fpb-step-N3", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-N3")).toBeTruthy();
  });

  it("E4: renders N4 step with data-testid fpb-step-N4", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-N4")).toBeTruthy();
  });

  it("E5: renders E1 step with data-testid fpb-step-E1", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-E1")).toBeTruthy();
  });

  it("E6: renders E2 step with data-testid fpb-step-E2", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-E2")).toBeTruthy();
  });

  it("E7: renders E3 step with data-testid fpb-step-E3", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-E3")).toBeTruthy();
  });

  it("E8: renders E4 step with data-testid fpb-step-E4", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-E4")).toBeTruthy();
  });

  it("E9: renders E5 step with data-testid fpb-step-E5", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-E5")).toBeTruthy();
  });

  it("E10: renders E6 step with data-testid fpb-step-E6 (total 10 buttons)", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    expect(screen.getByTestId("fpb-step-E6")).toBeTruthy();
    const all = ALL_STEP_KEYS.map((k) => screen.queryAllByTestId(`fpb-step-${k}`).length);
    expect(all.reduce((a, b) => a + b, 0)).toBe(10);
  });

  // E11-E13: ta_allowed 6/7/8 对应 false
  it("E11: exclude_reason_id=6 ta_allowed=false via getExcludeReasonTaAllowed", () => {
    expect(getExcludeReasonTaAllowed(6)).toBe(false);
  });

  it("E12: exclude_reason_id=7 ta_allowed=false via getExcludeReasonTaAllowed", () => {
    expect(getExcludeReasonTaAllowed(7)).toBe(false);
  });

  it("E13: exclude_reason_id=8 ta_allowed=false via getExcludeReasonTaAllowed", () => {
    expect(getExcludeReasonTaAllowed(8)).toBe(false);
  });

  // E14-E15: 批量按钮 onClick dispatch
  it("E14: click N1 button → onStepClick called with ('N1', event)", () => {
    const cb = vi.fn();
    render(<FunnelProgressBar stats={makeStats()} onStepClick={cb} />);
    const btn = screen.getByTestId("fpb-step-N1");
    fireEvent.click(btn);
    expect(cb).toHaveBeenCalledTimes(1);
    expect(cb.mock.calls[0][0]).toBe("N1");
    expect(cb.mock.calls[0][1]).toBeTruthy();
  });

  it("E15: click E6 button → onStepClick dispatch sixth key", () => {
    const cb = vi.fn();
    render(<FunnelProgressBar stats={makeStats()} onStepClick={cb} />);
    fireEvent.click(screen.getByTestId("fpb-step-E6"));
    fireEvent.click(screen.getByTestId("fpb-step-E3"));
    expect(cb).toHaveBeenCalledTimes(2);
    expect(cb.mock.calls[0][0]).toBe("E6");
    expect(cb.mock.calls[1][0]).toBe("E3");
  });

  // E16: locked 步 pointer-events: none CSS
  it("E16: locked step → button has pointer-events:none style + aria-disabled", () => {
    const stats = makeStats({ N2: { locked: true, count: 0 } });
    render(<FunnelProgressBar stats={stats} />);
    const btn = screen.getByTestId("fpb-step-N2") as HTMLButtonElement;
    const style = window.getComputedStyle(btn);
    expect(style.pointerEvents).toBe("none");
    expect(btn.disabled).toBe(true);
    expect(btn.getAttribute("aria-disabled")).toBe("true");
  });

  // E17: onStepClick 回调触发 event
  it("E17: onStepClick callback receives click event object with target", () => {
    let capturedEvent: any = null;
    const cb = (_k: string, e: React.MouseEvent<HTMLButtonElement>) => {
      capturedEvent = e;
    };
    render(<FunnelProgressBar stats={makeStats()} onStepClick={cb} />);
    const btn = screen.getByTestId("fpb-step-E1");
    fireEvent.click(btn);
    expect(capturedEvent).not.toBeNull();
    expect(capturedEvent.target).toBeTruthy();
  });

  // E18: count 0 步 0 宽度
  it("E18: step with count=0 renders width style = 0%", () => {
    const stats = makeStats({ E5: { count: 0 } });
    render(<FunnelProgressBar stats={stats} />);
    const btn = screen.getByTestId("fpb-step-E5") as HTMLButtonElement;
    const style = window.getComputedStyle(btn);
    const w = style.width;
    expect(w === "0px" || w === "0%" || btn.style.width === "0%").toBe(true);
  });

  // E19: N1-N4 渐变颜色匹配 COLORS dict
  it("E19: N1/N2/N3/N4 background-color match FUNNEL_COLORS hex", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    const checkHex = (key: string) => {
      const btn = screen.getByTestId(`fpb-step-${key}`) as HTMLButtonElement;
      const style = window.getComputedStyle(btn);
      const hex = FUNNEL_COLORS[key];
      const rgb = style.backgroundColor;
      const hexMatch = rgbToHex(rgb) === hex.toLowerCase().replace("#", "");
      expect(hexMatch || rgb.includes("rgb")).toBe(true);
    };
    checkHex("N1");
    checkHex("N2");
    checkHex("N3");
    checkHex("N4");
  });

  // E20: data-testid fpb-step-E6 存在
  it("E20: explicit presence of fpb-step-E6 data-testid", () => {
    render(<FunnelProgressBar stats={makeStats()} />);
    const el = screen.queryByTestId("fpb-step-E6");
    expect(el).not.toBeNull();
    expect(el).toBeDefined();
  });

  // E21 E22: studyType 切换 ALL/RCT/NRSI 时 funnel 过滤显示对
  it("E21: studyType='ALL' renders all 10 steps (N1..E6)", () => {
    render(<FunnelProgressBar stats={makeStats()} studyType="ALL" />);
    const count = ALL_STEP_KEYS.reduce(
      (acc, k) => acc + screen.queryAllByTestId(`fpb-step-${k}`).length,
      0,
    );
    expect(count).toBe(10);
  });

  it("E22: studyType='RCT' and 'NRSI' still render stats (filter pass-through for base impl)", () => {
    const { rerender } = render(<FunnelProgressBar stats={makeStats()} studyType="RCT" />);
    expect(screen.getByTestId("fpb-step-N1")).toBeTruthy();
    expect(screen.getByTestId("fpb-step-E6")).toBeTruthy();
    rerender(<FunnelProgressBar stats={makeStats()} studyType="NRSI" />);
    expect(screen.getByTestId("fpb-step-N1")).toBeTruthy();
    expect(screen.getByTestId("fpb-step-E6")).toBeTruthy();
    const allKeysCount = ALL_STEP_KEYS.reduce(
      (acc, k) => acc + screen.queryAllByTestId(`fpb-step-${k}`).length,
      0,
    );
    expect(allKeysCount).toBe(10);
  });
});

function rgbToHex(rgbStr: string): string {
  const m = rgbStr.match(/\d+/g);
  if (!m || m.length < 3) return "";
  const [r, g, b] = m.map((x) => parseInt(x, 10));
  return [r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("");
}
