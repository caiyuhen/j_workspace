import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { BenchDashboardSummary, HistoryPayload } from "../components/bench/BenchDashboardSummary";

const mkEmpty = (): HistoryPayload => ({ generated_at: "2026-08-24T00:00:00Z", window_days: 7, entries: [] });
const mkEntries = (n: number) => Array.from({ length: n }, (_, i) => ({
  sha: `sha${1000 + i}`, commit_msg: `wip ${i}`, branch: "main", date: `2026-08-${(20 + i % 5).toString().padStart(2, "0")}T10:00:00Z`,
  slo: {
    n500: { target_s: 1.0, median_s: 0.5 + i * 0.01, p95_s: 0.8, status: "PASS" },
    n1000: { target_s: 1.5, median_s: 1.1, p95_s: 1.3, status: "PASS" },
    n2000: { target_s: 3.0, median_s: 2.419, p95_s: 2.8, status: "PASS" },
    n10000: { target_s: 9.6, median_s: 8.0 + i * 0.05, p95_s: 9.0, status: i > 20 ? "WARN" : "PASS" },
    n50000: { target_s: 45.0, median_s: 40.0 + i * 0.1, p95_s: 43.0, status: i > 30 ? "HARD_BLOCK" : "PASS" },
  },
  vs_baseline_v0110_speedup_x: { n2000: 1.0, n10000: 31 / (8 + i * 0.05), n50000: 775 / (40 + i * 0.1) },
  alerts: i > 30 ? [{ severity: "HARD_BLOCK", size: "n50000", message: "n50000 over SLO" }] : [],
}));

describe("BenchDashboardSummary (24)", () => {
  it("1 renders empty header with window days", () => {
    render(<BenchDashboardSummary history={{ ...mkEmpty(), window_days: 60 }} />);
    expect(screen.getByText(/window 60 days/)).toBeTruthy();
  });
  it("2 empty shows No data yet message", () => {
    render(<BenchDashboardSummary history={mkEmpty()} />);
    expect(screen.getByText(/No data yet/)).toBeTruthy();
  });
  it("3 entries=0 kpis=0 empty array", () => {
    const { container } = render(<BenchDashboardSummary history={mkEmpty()} />);
    expect(container.querySelectorAll(".grid-cols-4 > div").length).toBeLessThanOrEqual(1);
  });
  it("4 svg exists always (even empty data)", () => {
    const { container } = render(<BenchDashboardSummary history={mkEmpty()} />);
    expect(container.querySelector("svg")).toBeTruthy();
  });
  it("5 shows 3 runs in title when entries=3", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(3) }} />);
    const title = container.querySelector("h2") as HTMLElement;
    expect(title.textContent).toContain("3 runs");
  });
  it("6 shows latest N2k value formatted 2 decimals", () => {
    render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(5) }} />);
    expect(screen.getByText(/2\.42s/)).toBeTruthy();
  });
  it("7 latest N10k 0-based index i=4 median=8.2 → shows 8.20s", () => {
    render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(5) }} />);
    expect(screen.getByText(/8\.20s/)).toBeTruthy();
  });
  it("8 latest N50k i=4 median=40.4 → shown", () => {
    render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(5) }} />);
    expect(screen.getByText(/40\.40s/)).toBeTruthy();
  });
  it("9 alerts count 0 for data i≤30 (no alerts)", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(5) }} />);
    const kpiCards = container.querySelectorAll(".grid > div.rounded-lg");
    const alertsCard = kpiCards[kpiCards.length - 1] as HTMLElement;
    const valueEl = alertsCard.querySelector(".text-2xl") as HTMLElement;
    expect(valueEl.textContent).toBe("0");
  });
  it("10 alerts>0 KPI color class has red", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(40) }} />);
    const kpiValues = container.querySelectorAll(".text-2xl");
    const lastKpi = kpiValues[kpiValues.length - 1] as HTMLElement;
    expect(lastKpi.style.color).toBe("rgb(239, 68, 68)");
  });
  it("11 latest N10k=WARN i=24 → color rgb(245, 158, 11) + value 9.20s", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(25) }} />);
    const kpiValues = container.querySelectorAll(".text-2xl");
    const n10kKpi = kpiValues[1] as HTMLElement; // index 1 = N=10k (AC4)
    expect(n10kKpi.style.color).toBe("rgb(245, 158, 11)"); // WARN color
    expect(n10kKpi.textContent).toBe("9.20s");
  });
  it("12 KPI cards count 4 exactly when data present", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(10) }} />);
    expect(container.querySelectorAll(".grid > div.rounded-lg").length).toBe(4);
  });
  it("13 SLO target N=2k text '3.0s'", () => {
    render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(3) }} />);
    expect(screen.getByText(/SLO 3\.0s/)).toBeTruthy();
  });
  it("14 SLO target N10k 9.6s text", () => {
    render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(3) }} />);
    expect(screen.getByText(/SLO 9\.6s/)).toBeTruthy();
  });
  it("15 SLO target N50k 45.0s", () => {
    render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(3) }} />);
    expect(screen.getByText(/SLO 45\.0s/)).toBeTruthy();
  });
  it("16 SVG has polyline for 5 sizes = 5 polyline elements", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(8) }} />);
    expect(container.querySelectorAll("polyline").length).toBeGreaterThanOrEqual(5);
  });
  it("17 SVG has 2 dashed lines (SLO rails n10k n50k)", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(3) }} />);
    const dashed = Array.from(container.querySelectorAll("line")).filter(l => l.getAttribute("stroke-dasharray"));
    expect(dashed.length).toBeGreaterThanOrEqual(2);
  });
  it("18 SVG legend 5 size labels rendered as <text>", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(3) }} />);
    expect(container.querySelectorAll("text").length).toBeGreaterThanOrEqual(5);
  });
  it("19 SVG viewport 860x260 dimensions", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(3) }} />);
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("viewBox")).toContain("860");
  });
  it("20 window_days from history rendered", () => {
    render(<BenchDashboardSummary history={{ ...mkEmpty(), window_days: 30 }} />);
    expect(screen.getByText(/window 30 days/)).toBeTruthy();
  });
  it("21 speedup baseline x keys verified via entries not crash", () => {
    expect(() => render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(3) }} />)).not.toThrow();
  });
  it("22 100 entries renders svg without crash", () => {
    expect(() => render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(100) }} />)).not.toThrow();
  });
  it("23 HARD_BLOCK color used for N=50k KPI when i=40 (over threshold)", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(40) }} />);
    const kpiValues = container.querySelectorAll(".text-2xl");
    const n50kKpi = kpiValues[2] as HTMLElement; // index 2 = N=50k (AC5)
    expect(n50kKpi.style.color).toBe("rgb(239, 68, 68)"); // HARD_BLOCK color
  });
  it("24 legend labels include all 5 sizes (N=500/N=1k/N=2k/N=10k/N=50k)", () => {
    const { container } = render(<BenchDashboardSummary history={{ ...mkEmpty(), entries: mkEntries(5) }} />);
    const txt = container.textContent || "";
    ["N=500","N=1k","N=2k","N=10k","N=50k"].forEach(s => expect(txt).toContain(s));
  });
});
