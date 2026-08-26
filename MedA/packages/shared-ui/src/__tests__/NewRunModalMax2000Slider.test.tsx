import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup, rerender } from "@testing-library/react";
import React from "react";
import { NewRunModal } from "../components/NewRunModal";

describe("NewRunModal W11 D3-3 (12 it GREEN)", () => {
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

  it("T1 默认渲染 max=200 step=250 value=200", () => {
    renderModal({ initialPreset: "sglt2i_ckd" });
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input.value).toBe("200");
    expect(Number(input.getAttribute("max"))).toBe(50000);
    expect(Number(input.getAttribute("step"))).toBe(250);
  });

  it("T2 input max属性 = 50000 DOM getAttribute 断言", () => {
    renderModal({ initialPreset: "sglt2i_ckd" });
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input.getAttribute("max")).toBe("50000");
  });

  it("T3 input step 属性 = 250", () => {
    renderModal({ initialPreset: "sglt2i_ckd" });
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input.getAttribute("step")).toBe("250");
  });

  it("T4 fireEvent 拖拽 2000 → value=2000 valid 无 error", () => {
    const { onConfirm } = renderModal({ initialPreset: "sglt2i_ckd" });
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "2000" } });
    expect(input.value).toBe("2000");
    expect(screen.queryByTestId("error-max-records")).toBeNull();
    const btn = screen.getByTestId("btn-confirm") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
    fireEvent.click(btn);
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm.mock.calls[0][0].max_records).toBe(2000);
  });

  it("T5 fireEvent 拖拽 2500 → valid 无 error (buffer cc_max=2500)", () => {
    const { onConfirm } = renderModal({ initialPreset: "sglt2i_ckd" });
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "2500" } });
    expect(input.value).toBe("2500");
    expect(screen.queryByTestId("error-max-records")).toBeNull();
    const btn = screen.getByTestId("btn-confirm") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
    fireEvent.click(btn);
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm.mock.calls[0][0].max_records).toBe(2500);
  });

  it("T6 fireEvent 拖拽 2501 → error 文本 超过最大上限 2500 篇（含 buffer）", () => {
    renderModal({ initialPreset: "sglt2i_ckd" });
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "2501" } });
    expect(input.value).toBe("2501");
    const err = screen.getByTestId("error-max-records");
    expect(err).toBeTruthy();
    expect(err.textContent).toContain("超过最大上限 2500 篇（含 buffer）");
    const btn = screen.getByTestId("btn-confirm") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("T7 preset selector empty → slider disabled=true", () => {
    renderModal();
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input.disabled).toBe(true);
  });

  it("T8 mode===live max=200 → banner 不存在 (false)", () => {
    renderModal({ initialPreset: "sglt2i_ckd" });
    fireEvent.click(screen.getByTestId("mode-live"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "200" } });
    expect(screen.queryByTestId("banner-live-large")).toBeNull();
  });

  it("T9 mode===live max=600 → banner 存在，文本内容含 429 限流", () => {
    renderModal({ initialPreset: "sglt2i_ckd" });
    fireEvent.click(screen.getByTestId("mode-live"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "600" } });
    const banner = screen.getByTestId("banner-live-large");
    expect(banner).toBeTruthy();
    expect(banner.textContent).toContain("429 限流");
  });

  it("T10 mode===snapshot max=2000 → banner 不存在", () => {
    renderModal({ initialPreset: "sglt2i_ckd" });
    fireEvent.click(screen.getByTestId("mode-snapshot"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "2000" } });
    expect(screen.queryByTestId("banner-live-large")).toBeNull();
  });

  it("T11 live mode banner aria-label=warn_live_large", () => {
    renderModal({ initialPreset: "sglt2i_ckd" });
    fireEvent.click(screen.getByTestId("mode-live"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "800" } });
    const banner = screen.getByTestId("banner-live-large");
    expect(banner.getAttribute("aria-label")).toBe("warn_live_large");
  });

  it("T12 max change slider rerender value 同步 (set max 1000 → rerender 显示 1000)", () => {
    const { onClose, onConfirm, rerender: utilsRerender } = renderModal({
      initialPreset: "sglt2i_ckd",
      initialMaxRecords: 200,
    });
    const input1 = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input1.value).toBe("200");
    utilsRerender(
      <NewRunModal
        open={true}
        onClose={onClose}
        onConfirm={onConfirm}
        initialPreset="sglt2i_ckd"
        initialMaxRecords={1000}
      />,
    );
    const input2 = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input2.value).toBe("1000");
  });
});
