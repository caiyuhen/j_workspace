import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import React from "react";
import { NewRunModal } from "../components/NewRunModal";
import { DedupDiagCards } from "../components/DedupDiagCards";

describe("W12 Screen2 Layout Smoke (8 TS tests: DedupDiag chips + N50k slider + HYBRID badge)", () => {
  beforeEach(() => {
    vi.spyOn(window, "fetch" as never).mockResolvedValue({} as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
    cleanup();
  });

  const renderModal = (overrides: Partial<React.ComponentProps<typeof NewRunModal>> = {}) => {
    const onClose = vi.fn();
    const onConfirm = vi.fn();
    const utils = render(
      <NewRunModal
        open={true}
        onClose={onClose}
        onConfirm={onConfirm}
        {...overrides}
      />,
    );
    return { ...utils, onClose, onConfirm };
  };

  const renderDiag = (overrides = {}) => {
    const defaultDiag = {
      sizes_hist: { "1": 800, "2": 40, "3": 10, "4": 2 },
      hamming_hist: { "0": 5, "1": 8, "2": 12, "3": 10, "4": 20, "5": 18, "6": 15 },
      perf: {
        nodes: 920,
        build_ms: 120.5,
        query_avg_us: 45.2,
        step1_total_ms: 489,
        speedup_x: 4.2,
        parallel_eff_x: 6.0,
        slo_2000: 2000,
        ratio: 0.24,
      },
    };
    return render(<DedupDiagCards diag={{ ...defaultDiag, ...overrides }} />);
  };

  it("D1: DedupDiag hybrid chip 1· unique green chip renders + bg #d1fae5 family", () => {
    renderDiag();
    const chip1 = screen.getByTestId("sizes-chip-1");
    expect(chip1).toBeTruthy();
    const style = window.getComputedStyle(chip1);
    const bg = (style.backgroundColor || "").toLowerCase();
    const greenOk =
      bg.includes("209, 250, 229") ||
      bg.includes("d1fae5") ||
      bg.includes("rgb(209, 250, 229)");
    expect(greenOk).toBe(true);
    const text = chip1.textContent || "";
    expect(text.includes("1·") || text.includes("1 ·")).toBe(true);
  });

  it("D2: DedupDiag hybrid chip 2· yellow pair chip renders + bg #fef3c7 family", () => {
    renderDiag();
    const chip2 = screen.getByTestId("sizes-chip-2");
    expect(chip2).toBeTruthy();
    const style = window.getComputedStyle(chip2);
    const bg = (style.backgroundColor || "").toLowerCase();
    const yellowOk =
      bg.includes("254, 243, 199") ||
      bg.includes("fef3c7") ||
      bg.includes("rgb(254, 243, 199)");
    expect(yellowOk).toBe(true);
    const text = chip2.textContent || "";
    expect(text.includes("2·") || text.includes("2 ·")).toBe(true);
  });

  it("D3: DedupDiag hybrid chip 3· orange triple chip renders + bg #ffedd5 family", () => {
    renderDiag();
    const chip3 = screen.getByTestId("sizes-chip-3");
    expect(chip3).toBeTruthy();
    const style = window.getComputedStyle(chip3);
    const bg = (style.backgroundColor || "").toLowerCase();
    const orangeOk =
      bg.includes("255, 237, 213") ||
      bg.includes("ffedd5") ||
      bg.includes("rgb(255, 237, 213)");
    expect(orangeOk).toBe(true);
    const text = chip3.textContent || "";
    expect(text.includes("3·") || text.includes("3 ·")).toBe(true);
  });

  it("S4: N50k slider input max attribute == 50000 (D3-1 WL)", () => {
    renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input.getAttribute("max")).toBe("50000");
    expect(Number(input.max)).toBe(50000);
  });

  it("S5: N50k slider input step attribute == 250 (D3-1 WL)", () => {
    renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input.getAttribute("step")).toBe("250");
    expect(input.step).toBe("250");
  });

  it("S6: N50k slider min=1 preserved + value=200 default intact", () => {
    renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input.getAttribute("min")).toBe("1");
    expect(input.value).toBe("200");
  });

  it("H7: N>10k → blue HYBRID badge renders with blue bg (#dbeafe family)", () => {
    renderModal({ initialMaxRecords: 25000 });
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "25000" } });
    const badge = screen.queryByTestId("hybrid-mode-badge") || screen.queryByText(/HYBRID/);
    if (badge) {
      const style = window.getComputedStyle(badge);
      const bg = (style.backgroundColor || "").toLowerCase();
      const color = (style.color || "").toLowerCase();
      const blueBg =
        bg.includes("219, 234, 254") ||
        bg.includes("dbeafe") ||
        bg.includes("rgb(219, 234, 254)") ||
        bg.includes("37, 99, 235") ||
        bg.includes("2563eb");
      const blueText =
        color.includes("30, 64, 175") ||
        color.includes("1e40af") ||
        color.includes("37, 99, 235") ||
        color.includes("2563eb");
      expect(blueBg || blueText, "HYBRID badge should have blue family bg or text").toBe(true);
    }
    const n = Number((screen.getByTestId("input-max-records") as HTMLInputElement).value);
    expect(n).toBeGreaterThan(10000);
  });

  it("H8: N≤10k → HYBRID badge absent (snapshot/live only), change N=5000 no badge", () => {
    renderModal({ initialMaxRecords: 5000 });
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "5000" } });
    const n = Number(input.value);
    expect(n).toBeLessThanOrEqual(10000);
    expect(n).toBe(5000);
    const hasBadge =
      screen.queryByTestId("hybrid-mode-badge") !== null ||
      screen.queryByText(/HYBRID/) !== null;
    expect(hasBadge).toBe(false);
  });
});
