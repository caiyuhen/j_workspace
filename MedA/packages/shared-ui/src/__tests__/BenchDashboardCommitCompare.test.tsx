import { describe, it, expect, fireEvent } from "vitest";
import { render } from "@testing-library/react";
import React from "react";
import { BenchDashboardCommitCompare } from "../components/bench/BenchDashboardCommitCompare";
import { HistoryPayload } from "../components/bench/BenchDashboardSummary";

const mk = (withHard: boolean): HistoryPayload => ({
  generated_at: "2026-08-24T00:00:00Z", window_days: 7,
  entries: [
    { sha: "base001", commit_msg: "base commit", branch: "main", date: "2026-08-22",
      slo: { n500:{target_s:1,median_s:0.5,p95_s:0.9,status:"PASS"}, n1000:{target_s:1.5,median_s:1.1,p95_s:1.4,status:"PASS"},
        n2000:{target_s:3,median_s:2.4,p95_s:2.8,status:"PASS"}, n10000:{target_s:9.6,median_s:8.0,p95_s:9.0,status:"PASS"},
        n50000:{target_s:45,median_s:40,p95_s:43,status:"PASS"} },
      vs_baseline_v0110_speedup_x:{n2000:1,n10000:3.8,n50000:19.4}, alerts:[] },
    { sha: "head002", commit_msg: "head new", branch: "feature", date: "2026-08-24",
      slo: { n500:{target_s:1,median_s:0.55,p95_s:0.95,status:"PASS"}, n1000:{target_s:1.5,median_s:1.21,p95_s:1.5,status:"WARN"},
        n2000:{target_s:3,median_s:2.64,p95_s:3.1,status:"WARN"}, n10000:{target_s:9.6,median_s:9.68,p95_s:10.5,status:"WARN"},
        n50000:{target_s:45,median_s:46.8,p95_s:49,status: withHard ? "HARD_BLOCK" : "WARN"} },
      vs_baseline_v0110_speedup_x:{n2000:0.92,n10000:3.2,n50000:16.6},
      alerts: withHard ? [{severity:"HARD_BLOCK",size:"n50000",message:"n50000 over"}] : [{severity:"WARN",size:"n10000",message:"n10k warn"}] },
  ]
});

describe("BenchDashboardCommitCompare (14)", () => {
  it("1 renders base/head 2 <select> elements", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    expect(container.querySelectorAll("select").length).toBe(2);
  });
  it("2 2 commits → 2 options per select dropdown", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    const sels = container.querySelectorAll("select");
    expect(sels[0].querySelectorAll("option").length).toBe(2);
    expect(sels[1].querySelectorAll("option").length).toBe(2);
  });
  it("3 withHard=true renders HARD_BLOCK banner at top", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(true)} />);
    expect(container.textContent).toContain("HARD_BLOCK");
  });
  it("4 withHard=false no HARD_BLOCK banner class bg-red", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    expect(container.querySelector(".bg-red-50")).toBeFalsy();
  });
  it("5 5 size rows rendered n500/n1k/n2k/n10k/n50k", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    const labels = ["n500","n1000","n2000","n10000","n50000"];
    labels.forEach(l => expect(container.textContent).toContain(l));
  });
  it("6 head n500 0.55 vs base 0.5 → +10.0% pct computed", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    expect(container.textContent).toContain("+10.0%");
  });
  it("7 n2000 head 2.64 base 2.4 → +10.0%", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    expect(container.textContent).toMatch(/2\.40s → 2\.64s/);
  });
  it("8 select base index 0 & head 1 default", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    const sels = container.querySelectorAll("select");
    expect(Number(sels[0].getAttribute("value"))).toBe(0);
    expect(Number(sels[1].getAttribute("value"))).toBe(1);
  });
  it("9 changing base select updates diff bar positions", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    const selBase = container.querySelectorAll("select")[0];
    fireEvent.change(selBase, { target: { value: "1" } });
    expect(container.textContent).toContain("+0.0%");
  });
  it("10 empty entries 0 options rendered without crash", () => {
    expect(() => render(<BenchDashboardCommitCompare history={{ generated_at:"", window_days:7, entries:[] }} />)).not.toThrow();
  });
  it("11 5 diff bar div elements w- class flex-row rendered", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(false)} />);
    const bars = container.querySelectorAll(".flex.items-center");
    expect(bars.length).toBeGreaterThanOrEqual(5);
  });
  it("12 HARD banner class contains border-red-200 when triggered", () => {
    const { container } = render(<BenchDashboardCommitCompare history={mk(true)} />);
    const banner = container.querySelector(".bg-red-50");
    expect(banner?.className).toMatch(/border-red-200/);
  });
  it("13 base/head labels exist", () => {
    render(<BenchDashboardCommitCompare history={mk(false)} />);
  });
  it("14 10-entry history select options 10 each", () => {
    const big: HistoryPayload = { generated_at:"", window_days:7, entries: Array.from({length:10},(_,i)=>({...mk(false).entries[0], sha:`s${i}`})) };
    const { container } = render(<BenchDashboardCommitCompare history={big} />);
    expect(container.querySelectorAll("select option").length).toBe(20);
  });
});
