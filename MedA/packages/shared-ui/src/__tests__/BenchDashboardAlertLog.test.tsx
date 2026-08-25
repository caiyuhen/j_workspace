import { describe, it, expect, fireEvent } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { BenchDashboardAlertLog } from "../components/bench/BenchDashboardAlertLog";
import { HistoryPayload } from "../components/bench/BenchDashboardSummary";

const base: HistoryPayload = {
  generated_at: "2026-08-24T00:00:00Z", window_days: 7, entries: [
    { sha: "sha1", commit_msg: "a", branch: "main", date: "2026-08-22",
      slo: { } as any, vs_baseline_v0110_speedup_x: { n2000:1, n10000:2, n50000:3 },
      alerts: [
        { severity: "HARD_BLOCK", size: "n50000", message: "n50k over 45s SLO" },
        { severity: "WARN", size: "n10000", message: "n10k warn 9.5s/9.6s" },
      ] },
    { sha: "sha2", commit_msg: "b", branch: "main", date: "2026-08-23",
      slo: { } as any, vs_baseline_v0110_speedup_x: { n2000:1, n10000:2, n50000:3 },
      alerts: [ { severity: "WARN", size: "n2000", message: "n2k approaching 3.0s" } ] },
    { sha: "sha3", commit_msg: "c", branch: "main", date: "2026-08-24",
      slo: { } as any, vs_baseline_v0110_speedup_x: { n2000:1, n10000:2, n50000:3 }, alerts: [] },
  ]
};

describe("BenchDashboardAlertLog (10)", () => {
  it("1 ALL filter default: shows 3 alerts total", () => {
    const { container } = render(<BenchDashboardAlertLog history={base} />);
    expect(container.querySelectorAll(".divide-y > div").length).toBe(3);
  });
  it("2 'No alerts' empty message not shown when alerts present", () => {
    render(<BenchDashboardAlertLog history={base} />);
    expect(screen.queryByText(/No alerts/)).toBeFalsy();
  });
  it("3 empty entries → shows No alerts empty state", () => {
    render(<BenchDashboardAlertLog history={{ generated_at:"", window_days:7, entries:[] }} />);
    expect(screen.getByText(/No alerts/)).toBeTruthy();
  });
  it("4 4 filter buttons rendered (ALL/HARD_BLOCK/WARN/PASS)", () => {
    const { container } = render(<BenchDashboardAlertLog history={base} />);
    ["ALL","HARD_BLOCK","WARN","PASS"].forEach(f => expect(container.textContent).toContain(f));
  });
  it("5 click HARD_BLOCK filter shows exactly 1 alert row", () => {
    const { container } = render(<BenchDashboardAlertLog history={base} />);
    const btn = Array.from(container.querySelectorAll("button")).find(b => b.textContent === "HARD_BLOCK")!;
    fireEvent.click(btn);
    expect(container.querySelectorAll(".divide-y > div").length).toBe(1);
  });
  it("6 click WARN filter → 2 alert rows", () => {
    const { container } = render(<BenchDashboardAlertLog history={base} />);
    fireEvent.click(Array.from(container.querySelectorAll("button")).find(b => b.textContent === "WARN")!);
    expect(container.querySelectorAll(".divide-y > div").length).toBe(2);
  });
  it("7 click PASS filter → 0 rows + No alerts message", () => {
    const { container } = render(<BenchDashboardAlertLog history={base} />);
    fireEvent.click(Array.from(container.querySelectorAll("button")).find(b => b.textContent === "PASS")!);
    expect(container.textContent).toContain("No alerts");
  });
  it("8 HARD_BLOCK severity chip background red #ef4444", () => {
    const { container } = render(<BenchDashboardAlertLog history={base} />);
    const chips = Array.from(container.querySelectorAll("span.px-2.py-0\\.5"));
    const hb = chips.find(c => c.textContent === "HARD_BLOCK")!;
    expect(hb.getAttribute("style")).toContain("rgb(239, 68, 68)");
  });
  it("9 entries count shows 3 when ALL", () => {
    render(<BenchDashboardAlertLog history={base} />);
    expect(screen.getByText(/3 entries/)).toBeTruthy();
  });
  it("10 click WARN → entries count becomes 2", () => {
    const { container } = render(<BenchDashboardAlertLog history={base} />);
    fireEvent.click(Array.from(container.querySelectorAll("button")).find(b => b.textContent === "WARN")!);
    expect(container.textContent).toMatch(/2 entries/);
  });
});
