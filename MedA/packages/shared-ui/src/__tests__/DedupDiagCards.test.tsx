import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import {
  DedupDiagCards,
  DedupSizesCard,
  DedupHammingCard,
  DedupPerfCard,
} from "../components/DedupDiagCards";

function rgbToHex(rgbStr: string): string {
  const m = rgbStr.match(/\d+/g);
  if (!m || m.length < 3) return "";
  const [r, g, b] = m.map((x) => parseInt(x, 10));
  return [r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("");
}

describe("DedupSizesCard (8 tests)", () => {
  it("Sizes 1: 空 sizes → 无 chip 不崩", () => {
    const { container } = render(<DedupSizesCard sizes_hist={{}} />);
    const card = screen.getByTestId("dedup-sizes-card");
    expect(card).toBeTruthy();
    const chip1 = screen.queryByTestId("sizes-chip-1");
    const chip2 = screen.queryByTestId("sizes-chip-2");
    const chip3 = screen.queryByTestId("sizes-chip-3");
    const chip4plus = screen.queryByTestId("sizes-chip-4plus");
    expect(chip1).toBeNull();
    expect(chip2).toBeNull();
    expect(chip3).toBeNull();
    expect(chip4plus).toBeNull();
    expect(container).toBeTruthy();
  });

  it("Sizes 2: size=1 绿 chip exact text", () => {
    render(<DedupSizesCard sizes_hist={{ "1": 80 }} />);
    const chip1 = screen.getByTestId("sizes-chip-1");
    expect(chip1.textContent).toBe("1 · 80 (100.0% unique)");
    const style = window.getComputedStyle(chip1);
    const bg = style.backgroundColor || "";
    const greenBgOk = bg.includes("209, 250, 229") || bg.includes("d1fae5") || rgbToHex(bg) === "d1fae5";
    expect(greenBgOk).toBe(true);
    const color = style.color || "";
    const greenColorOk = color.includes("6, 95, 70") || color.includes("#065f46") || rgbToHex(color) === "065f46";
    expect(greenColorOk).toBe(true);
  });

  it("Sizes 3: size=2 amber chip exact text", () => {
    render(<DedupSizesCard sizes_hist={{ "2": 15 }} />);
    const chip2 = screen.getByTestId("sizes-chip-2");
    expect(chip2.textContent).toBe("2 · 15 对");
    const style = window.getComputedStyle(chip2);
    const bg = style.backgroundColor || "";
    const amberBgOk = bg.includes("254, 243, 199") || bg.includes("fef3c7") || rgbToHex(bg) === "fef3c7";
    expect(amberBgOk).toBe(true);
  });

  it("Sizes 4: size=3 orange chip exact text", () => {
    render(<DedupSizesCard sizes_hist={{ "3": 8 }} />);
    const chip3 = screen.getByTestId("sizes-chip-3");
    expect(chip3.textContent).toBe("3 · 8 组");
    const style = window.getComputedStyle(chip3);
    const bg = style.backgroundColor || "";
    const orangeBgOk = bg.includes("255, 237, 213") || bg.includes("ffedd5") || rgbToHex(bg) === "ffedd5";
    expect(orangeBgOk).toBe(true);
  });

  it("Sizes 5: size=4+ red 5篇组", () => {
    render(<DedupSizesCard sizes_hist={{ "4": 3, "5": 2 }} />);
    const chip4plus = screen.getByTestId("sizes-chip-4plus");
    expect(chip4plus.textContent).toContain("4+ · 5 组");
    expect(chip4plus.textContent).toContain("22 篇");
    const style = window.getComputedStyle(chip4plus);
    const bg = style.backgroundColor || "";
    const redBgOk = bg.includes("254, 226, 226") || bg.includes("fee2e2") || rgbToHex(bg) === "fee2e2";
    expect(redBgOk).toBe(true);
  });

  it("Sizes 6: drop% exact 1小数", () => {
    const sizes_hist = { "1": 70, "2": 10, "3": 3, "4": 1 };
    render(<DedupSizesCard sizes_hist={sizes_hist} />);
    const n_total_fixed = 70 * 1 + 10 * 2 + 3 * 3 + 1 * 4;
    const n_kept = 70 + 10 + 3 + 1;
    const dropRate = ((n_total_fixed - n_kept) / n_total_fixed) * 100;
    const bottom = screen.getByTestId("sizes-bottom-row");
    expect(bottom.textContent).toContain(`丢弃率 ${dropRate.toFixed(1)}%`);
  });

  it("Sizes 7: 保留N篇 exact", () => {
    const sizes_hist = { "1": 70, "2": 10, "3": 3, "4": 1 };
    render(<DedupSizesCard sizes_hist={sizes_hist} />);
    const n_kept = 70 + 10 + 3 + 1;
    const bottom = screen.getByTestId("sizes-bottom-row");
    expect(bottom.textContent).toContain(`保留 ${n_kept} 篇`);
  });

  it("Sizes 8: aria-label 丢弃率", () => {
    const sizes_hist = { "1": 90, "2": 5 };
    render(<DedupSizesCard sizes_hist={sizes_hist} />);
    const card = screen.getByTestId("dedup-sizes-card");
    const aria = card.getAttribute("aria-label") || "";
    const n_total_fixed = 90 * 1 + 5 * 2;
    const n_kept = 90 + 5;
    const dropRate = ((n_total_fixed - n_kept) / n_total_fixed) * 100;
    expect(aria).toContain(`丢弃率 ${dropRate.toFixed(1)}%`);
    const bottom = screen.getByTestId("sizes-bottom-row");
    const bottomAria = bottom.getAttribute("aria-label") || "";
    expect(bottomAria).toContain(`丢弃率 ${dropRate.toFixed(1)}%`);
  });
});

describe("DedupHammingCard (8 tests)", () => {
  function _setup() {
    const hamming_hist: Record<string, number> = {
      "0": 5,
      "1": 8,
      "2": 12,
      "3": 10,
      "4": 20,
      "5": 18,
      "6": 15,
    };
    render(<DedupHammingCard hamming_hist={hamming_hist} threshold={6} />);
    const paircount_total = 5 + 8 + 12 + 10 + 20 + 18 + 15;
    return { paircount_total };
  }

  it("Hamming 1: h≤3 bar 宽度 exact %", () => {
    const { paircount_total } = _setup();
    const h_le3_count = 5 + 8 + 12 + 10;
    const expPct = (h_le3_count / paircount_total) * 100;
    const bar = screen.getByTestId("hamming-row-le3-bar") as HTMLDivElement;
    const style = bar.style;
    const pctFromStyle = parseFloat(style.width || "0");
    expect(Math.abs(pctFromStyle - expPct) < 0.01).toBe(true);
  });

  it("Hamming 2: h=4 bar 宽度 exact %", () => {
    const { paircount_total } = _setup();
    const expPct = (20 / paircount_total) * 100;
    const bar = screen.getByTestId("hamming-row-eq4-bar") as HTMLDivElement;
    const style = bar.style;
    const pctFromStyle = parseFloat(style.width || "0");
    expect(Math.abs(pctFromStyle - expPct) < 0.01).toBe(true);
  });

  it("Hamming 3: h=5 bar 宽度 exact %", () => {
    const { paircount_total } = _setup();
    const expPct = (18 / paircount_total) * 100;
    const bar = screen.getByTestId("hamming-row-eq5-bar") as HTMLDivElement;
    const style = bar.style;
    const pctFromStyle = parseFloat(style.width || "0");
    expect(Math.abs(pctFromStyle - expPct) < 0.01).toBe(true);
  });

  it("Hamming 4: h=6 orange, bar 宽度 & count", () => {
    const { paircount_total } = _setup();
    const expPct = (15 / paircount_total) * 100;
    const bar = screen.getByTestId("hamming-row-eq6-bar") as HTMLDivElement;
    const style = bar.style;
    const pctFromStyle = parseFloat(style.width || "0");
    expect(Math.abs(pctFromStyle - expPct) < 0.01).toBe(true);
    const countSpan = screen.getByTestId("hamming-row-eq6-count");
    expect(countSpan.textContent).toContain("15");
    const bg = style.background || style.backgroundImage || "";
    const orangeOk = bg.includes("f59e0b") || bg.includes("fbbf24") || bg.includes("245, 158, 11");
    expect(orangeOk).toBe(true);
  });

  it("Hamming 5: h≥7 红 0", () => {
    _setup();
    const bar = screen.getByTestId("hamming-row-ge7-bar") as HTMLDivElement;
    const style = bar.style;
    expect(style.width === "0%" || style.width?.includes("0")).toBe(true);
    const countSpan = screen.getByTestId("hamming-row-ge7-count");
    expect(countSpan.textContent).toContain("0");
    const bg = style.background || style.backgroundImage || "";
    const redOk = bg.includes("ef4444") || bg.includes("f87171") || bg.includes("239, 68, 68");
    expect(redOk).toBe(true);
  });

  it("Hamming 6: badge THR=6 🔒locked 存在", () => {
    _setup();
    const badge = screen.getByTestId("hamming-thr-badge");
    expect(badge.textContent).toBe("THR=6 🔒locked");
    const aria = badge.getAttribute("aria-label") || "";
    expect(aria).toBe("阈值锁定");
  });

  it("Hamming 7: pct right-aligned (textAlign=right)", () => {
    _setup();
    const countSpan = screen.getByTestId("hamming-row-le3-count");
    const style = window.getComputedStyle(countSpan);
    const ta = (countSpan as HTMLSpanElement).style.textAlign || style.textAlign || "";
    expect(ta).toBe("right");
  });

  it("Hamming 8: labels 不 truncate（min-width 32px）", () => {
    _setup();
    const rows = ["le3", "eq4", "eq5", "eq6", "ge7"];
    for (const r of rows) {
      const label = screen.getByTestId(`hamming-row-${r}-label`) as HTMLSpanElement;
      const style = window.getComputedStyle(label);
      const mw = label.style.minWidth || style.minWidth || "0";
      const mwPx = parseFloat(mw.replace("px", ""));
      expect(mwPx).toBeGreaterThanOrEqual(32);
    }
  });
});

describe("DedupPerfCard (8 tests)", () => {
  function _setup() {
    const perf = {
      nodes: 1234567,
      build_ms: 245.6789,
      query_avg_us: 123.456,
      step1_total_ms: 1899.999,
      speedup_x: 5.67,
      parallel_eff_x: 6.4,
      slo_2000: 3000,
      ratio: 0.63,
    };
    render(<DedupPerfCard perf={perf} />);
    return { perf };
  }

  it("Perf 1: 节点数千位分隔", () => {
    _setup();
    const v = screen.getByTestId("perf-value-nodes");
    expect(v.textContent).toBe("1,234,567");
  });

  it("Perf 2: build_ms 2 decimals", () => {
    _setup();
    const v = screen.getByTestId("perf-value-build");
    expect(v.textContent).toBe("245.68 ms");
  });

  it("Perf 3: query µs 1 decimal", () => {
    _setup();
    const v = screen.getByTestId("perf-value-query");
    expect(v.textContent).toBe("123.5 µs / 次");
  });

  it("Perf 4: STEP1 total ms 绿色 bold", () => {
    _setup();
    const v = screen.getByTestId("perf-value-step1");
    expect(v.textContent).toBe("1900 ms");
    const style = window.getComputedStyle(v);
    const color = style.color || (v as HTMLSpanElement).style.color || "";
    const greenOk =
      color.includes("16, 185, 129") ||
      color.includes("rgb(16, 185, 129)") ||
      rgbToHex(color) === "10b981" ||
      color.includes("#10b981");
    expect(greenOk).toBe(true);
    const fw = style.fontWeight || (v as HTMLSpanElement).style.fontWeight || "";
    const boldOk = fw === "700" || fw === "bold" || parseInt(fw || "0", 10) >= 700;
    expect(boldOk).toBe(true);
  });

  it("Perf 5: speedup 🚀 emoji", () => {
    _setup();
    const v = screen.getByTestId("perf-value-speedup");
    expect(v.textContent).toContain("🚀");
    expect(v.textContent).toBe("🚀 5.7×");
  });

  it("Perf 6: 并行效率 百分比 exact", () => {
    const { perf } = _setup();
    const v = screen.getByTestId("perf-value-parallel");
    const expectedPct = Math.round((perf.parallel_eff_x / 8) * 100);
    expect(v.textContent).toContain("6.40×");
    expect(v.textContent).toContain(`实际 ${expectedPct}%`);
    expect(expectedPct).toBe(80);
  });

  it("Perf 7: SLO headroom 百分比计算 exact", () => {
    const { perf } = _setup();
    const v = screen.getByTestId("perf-value-slo");
    const expectedHeadroom = Math.max(0, 100 - perf.ratio * 100);
    expect(v.textContent).toContain("SLO 3000ms");
    expect(v.textContent).toContain("× 0.6");
    expect(v.textContent).toContain(`headroom ${expectedHeadroom}%`);
    expect(expectedHeadroom).toBe(37);
  });

  it("Perf 8: all 7 rows exist with correct structure", () => {
    _setup();
    const rowKeys = ["nodes", "build", "query", "step1", "speedup", "parallel", "slo"];
    for (const k of rowKeys) {
      const row = screen.getByTestId(`perf-row-${k}`);
      expect(row).toBeTruthy();
      const val = screen.getByTestId(`perf-value-${k}`);
      expect(val).toBeTruthy();
    }
    const card = screen.getByTestId("dedup-perf-card");
    expect(card).toBeTruthy();
  });
});
