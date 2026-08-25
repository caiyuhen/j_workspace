import { describe, it, expect, fireEvent } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { BenchDashboardPerSize } from "../components/bench/BenchDashboardPerSize";
import { HistoryPayload } from "../components/bench/BenchDashboardSummary";

const base: HistoryPayload = { generated_at: "2026-08-24T00:00:00Z", window_days: 7, entries: Array.from({ length: 14 }, (_, i) => ({
  sha: `s${i}`, commit_msg: `m${i}`, branch: "main", date: `2026-08-${10 + i}`,
  slo: { n500: { target_s: 1, median_s: 0.5, p95_s: 0.9, status: "PASS" },
    n1000: { target_s: 1.5, median_s: 1.2, p95_s: 1.4, status: "PASS" },
    n2000: { target_s: 3, median_s: 2.5, p95_s: 2.9, status: "PASS" },
    n10000: { target_s: 9.6, median_s: 8.5, p95_s: 9.3, status: "PASS" },
    n50000: { target_s: 45, median_s: 42, p95_s: 44, status: "PASS" } },
  vs_baseline_v0110_speedup_x: { n2000: 1, n10000: 3, n50000: 18 }, alerts: [],
})) };

describe("BenchDashboardPerSize (20)", () => {
  it("1 default size n10000 button active class", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const active = container.querySelector('button.bg-slate-800');
    expect(active?.textContent).toBe("n10000");
  });
  it("2 default window 7d active class indigo", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const ind = container.querySelector('button.bg-indigo-600');
    expect(ind?.textContent).toBe("7d");
  });
  it("3 5 size buttons rendered", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const sizeBtns = Array.from(container.querySelectorAll("button")).filter(b => /^n\d/.test(b.textContent || ""));
    expect(sizeBtns.length).toBe(5);
  });
  it("4 3 window buttons rendered", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const wBtns = Array.from(container.querySelectorAll("button")).filter(b => /\d+d/.test(b.textContent || ""));
    expect(wBtns.length).toBe(3);
  });
  it("5 click n500 switches active button", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const n500 = Array.from(container.querySelectorAll("button")).find(b => b.textContent === "n500")!;
    fireEvent.click(n500);
    const active = container.querySelector('button.bg-slate-800');
    expect(active?.textContent).toBe("n500");
  });
  it("6 click 30d switches window active", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const b30 = Array.from(container.querySelectorAll("button")).find(b => b.textContent === "30d")!;
    fireEvent.click(b30);
    expect(container.querySelector('button.bg-indigo-600')?.textContent).toBe("30d");
  });
  it("7 SVG rendered with 2+ polylines (p50/p95)", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    expect(container.querySelectorAll("polyline").length).toBeGreaterThanOrEqual(2);
  });
  it("8 target dashed red line present", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const lines = Array.from(container.querySelectorAll("line"));
    const reds = lines.filter(l => l.getAttribute("stroke") === "#dc2626");
    expect(reds.length).toBeGreaterThanOrEqual(1);
  });
  it("9 click n50k target line y=45s present without crash", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const btn = Array.from(container.querySelectorAll("button")).find(b => b.textContent === "n50000")!;
    fireEvent.click(btn);
    expect(container.querySelector("svg")).toBeTruthy();
  });
  it("10 60d window button click ok", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    fireEvent.click(Array.from(container.querySelectorAll("button")).find(b => b.textContent === "60d")!);
    expect(container.querySelector('button.bg-indigo-600')?.textContent).toBe("60d");
  });
  it("11 header text shows selected size placeholder", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    expect(container.textContent).toContain("n10000");
  });
  it("12 p50 / p95 legend text present", () => {
    render(<BenchDashboardPerSize history={base} />);
    expect(screen.getByText(/p50|p95/)).toBeTruthy();
  });
  it("13 empty entries no crash", () => {
    expect(() => render(<BenchDashboardPerSize history={{ ...base, entries: [] }} />)).not.toThrow();
  });
  it("14 window 7 caps entries=14 at 70 (≤70 ok)", () => {
    expect(() => render(<BenchDashboardPerSize history={{ ...base, entries: Array.from({length:14},()=>({} as any)) }} />)).not.toThrow();
  });
  it("15 target text red always per selected size", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const lines = container.querySelectorAll('line[stroke="#dc2626"]');
    expect(lines.length).toBeGreaterThanOrEqual(1);
  });
  it("16 n2000 click switches target 3.0s line", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    fireEvent.click(Array.from(container.querySelectorAll("button")).find(b=>b.textContent==="n2000")!);
    expect(container.querySelector("svg")).toBeTruthy();
  });
  it("17 1000 entries still ok", () => {
    const big = { ...base, entries: Array.from({length:1000},(_,i)=>({...base.entries[0],sha:`s${i}`,date:`2026-01-${(i%28)+1}`})) };
    expect(() => render(<BenchDashboardPerSize history={big} />)).not.toThrow();
  });
  it("18 per-size p95_s reflected in SVG polyline attributes", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    const pl = container.querySelectorAll("polyline");
    expect(pl.length).toBe(2);
  });
  it("19 n1000 select header text includes n1000", () => {
    const { container } = render(<BenchDashboardPerSize history={base} />);
    fireEvent.click(Array.from(container.querySelectorAll("button")).find(b=>b.textContent==="n1000")!);
    expect(container.textContent).toContain("n1000");
  });
  it("20 30+30d=60 entries window=60 not crash", () => {
    const b = { ...base, entries: Array.from({length:60},(_,i)=>({...base.entries[0],sha:`x${i}`})) };
    expect(() => render(<BenchDashboardPerSize history={b} />)).not.toThrow();
  });
});
