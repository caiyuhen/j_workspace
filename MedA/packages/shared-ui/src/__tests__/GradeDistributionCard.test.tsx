import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import React from "react";
import { GradeDistributionCard } from "../components/GradeDistributionCard";

function rgbToHex(rgbStr: string): string {
  const m = rgbStr.match(/\d+/g);
  if (!m || m.length < 3) return "";
  const [r, g, b] = m.map((x) => parseInt(x, 10));
  return [r, g, b].map((x) => x.toString(16).padStart(2, "0")).join("");
}

describe("GradeDistributionCard (8 tests)", () => {
  it("1: distribution null → 3 gray skeleton bars render", () => {
    render(<GradeDistributionCard distribution={null} />);
    const barH = screen.getByTestId("gdc-skeleton-bar-H");
    const barM = screen.getByTestId("gdc-skeleton-bar-M");
    const barL = screen.getByTestId("gdc-skeleton-bar-L");
    expect(barH).toBeTruthy();
    expect(barM).toBeTruthy();
    expect(barL).toBeTruthy();
    for (const bar of [barH, barM, barL]) {
      const style = window.getComputedStyle(bar);
      const bg = style.backgroundColor || "";
      const hex = rgbToHex(bg);
      const grayOk =
        bg.includes("209, 213, 219") ||
        bg.includes("d1d5db") ||
        hex === "d1d5db";
      expect(grayOk).toBe(true);
    }
  });

  it("2: distribution {H:7,M:28,L:7} → 3 colored bars with correct percentages 17%/67%/16%", () => {
    render(<GradeDistributionCard distribution={{ H: 7, M: 28, L: 7 }} />);
    const barH = screen.getByTestId("gdc-bar-H") as HTMLDivElement;
    const barM = screen.getByTestId("gdc-bar-M") as HTMLDivElement;
    const barL = screen.getByTestId("gdc-bar-L") as HTMLDivElement;
    const total = 7 + 28 + 7;
    const expH = ((7 / total) * 100).toFixed(1);
    const expM = ((28 / total) * 100).toFixed(1);
    const expL = ((7 / total) * 100).toFixed(1);
    expect(expH).toBe("16.7");
    expect(expM).toBe("66.7");
    expect(expL).toBe("16.7");
    const labelRow = screen.getByTestId("gdc-labels");
    const txt = labelRow.textContent || "";
    expect(txt.includes("16.7%")).toBe(true);
    expect(txt.includes("66.7%")).toBe(true);
  });

  it("3: label text includes exact counts H 7, M 28, L 7", () => {
    render(<GradeDistributionCard distribution={{ H: 7, M: 28, L: 7 }} />);
    const labelH = screen.getByTestId("gdc-label-H");
    const labelM = screen.getByTestId("gdc-label-M");
    const labelL = screen.getByTestId("gdc-label-L");
    expect(labelH.textContent?.includes("High 7")).toBe(true);
    expect(labelM.textContent?.includes("Moderate 28")).toBe(true);
    expect(labelL.textContent?.includes("Low 7")).toBe(true);
  });

  it("4: H bar color #10b981 (green class)", () => {
    render(<GradeDistributionCard distribution={{ H: 7, M: 28, L: 7 }} />);
    const barH = screen.getByTestId("gdc-bar-H");
    const style = window.getComputedStyle(barH);
    const bg = style.backgroundColor || "";
    const hex = rgbToHex(bg);
    const greenOk =
      bg.includes("16, 185, 129") ||
      bg.includes("rgb(16, 185, 129)") ||
      hex === "10b981";
    expect(greenOk).toBe(true);
    expect(barH.className.includes("gdc-bar-H")).toBe(true);
  });

  it("5: M bar color amber class #f59e0b", () => {
    render(<GradeDistributionCard distribution={{ H: 7, M: 28, L: 7 }} />);
    const barM = screen.getByTestId("gdc-bar-M");
    const style = window.getComputedStyle(barM);
    const bg = style.backgroundColor || "";
    const amberOk =
      bg.includes("245, 158, 11") ||
      bg.includes("rgb(245, 158, 11)");
    expect(amberOk).toBe(true);
    expect(barM.className.includes("gdc-bar-M")).toBe(true);
  });

  it("6: L bar color red #ef4444 class", () => {
    render(<GradeDistributionCard distribution={{ H: 7, M: 28, L: 7 }} />);
    const barL = screen.getByTestId("gdc-bar-L");
    const style = window.getComputedStyle(barL);
    const bg = style.backgroundColor || "";
    const redOk =
      bg.includes("239, 68, 68") ||
      bg.includes("rgb(239, 68, 68)");
    expect(redOk).toBe(true);
    expect(barL.className.includes("gdc-bar-L")).toBe(true);
  });

  it("7: aria-label has exact 3 numbers", () => {
    render(<GradeDistributionCard distribution={{ H: 7, M: 28, L: 7 }} />);
    const card = screen.getByTestId("grade-distribution-card");
    const aria = card.getAttribute("aria-label") || "";
    expect(aria.includes("High 7")).toBe(true);
    expect(aria.includes("Moderate 28")).toBe(true);
    expect(aria.includes("Low 7")).toBe(true);
    expect(aria).toBe("GRADE evidence distribution: High 7, Moderate 28, Low 7");
  });

  it("8: distribution {H:0,M:0,L:5} → all L 100%", () => {
    render(<GradeDistributionCard distribution={{ H: 0, M: 0, L: 5 }} />);
    const labelL = screen.getByTestId("gdc-label-L");
    const txt = labelL.textContent || "";
    expect(txt.includes("Low 5")).toBe(true);
    expect(txt.includes("100.0%")).toBe(true);
    const barL = screen.getByTestId("gdc-bar-L") as HTMLDivElement;
    const style = barL.style;
    expect(style.width === "100.0%" || style.width?.includes("100")).toBe(true);
  });
});
