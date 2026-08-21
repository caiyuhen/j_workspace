import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, cleanup } from "@testing-library/react";
import React from "react";
import { NewRunModal } from "../components/NewRunModal";

const PRESET_CHIPS = [
  "sglt2i_ckd",
  "empagliflozin_hf",
  "glp1_weightloss",
  "liraglutide_nafld",
  "pkd_tolvaptan",
  "ckd_blood_pressure_control",
];

describe("NewRunModal W10 D3-2 (18 it)", () => {
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

  it("1: 默认 render 6 preset chips", () => {
    renderModal();
    for (const p of PRESET_CHIPS) {
      expect(screen.getByTestId(`preset-chip-${p}`)).toBeTruthy();
    }
    expect(screen.getAllByTestId(/^preset-chip-/).length).toBe(6);
  });

  it("2: 无 preset 选择 → confirm button disabled", () => {
    renderModal();
    const btn = screen.getByTestId("btn-confirm") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("3: 选 sglt2i_ckd → preset state set → confirm enabled", () => {
    renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const btn = screen.getByTestId("btn-confirm") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it("4: mode 切到 Live → payload.mode = \"live\"", () => {
    const { onConfirm } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    fireEvent.click(screen.getByTestId("mode-live"));
    fireEvent.click(screen.getByTestId("btn-confirm"));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    const payload = onConfirm.mock.calls[0][0];
    expect(payload.mode).toBe("live");
  });

  it("5: 默认 max_records = 200", () => {
    renderModal();
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(input.value).toBe("200");
  });

  it("6: max_records = 0 → invalid + confirm disabled", () => {
    const { onConfirm } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "0" } });
    const btn = screen.getByTestId("btn-confirm") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
    fireEvent.click(btn);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("7: max_records = 201 → 显示 red error \"≤200\" text visible", () => {
    renderModal();
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "201" } });
    const err = screen.getByTestId("error-max-records");
    expect(err).toBeTruthy();
    const txt = err.textContent || "";
    expect(txt.includes("≤200") || txt.includes("200")).toBe(true);
  });

  it("8: max_records = 99 → valid", () => {
    renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "99" } });
    const btn = screen.getByTestId("btn-confirm") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it("9: 点击取消 → onClose called 1 次", () => {
    const { onClose } = renderModal();
    fireEvent.click(screen.getByTestId("btn-cancel"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("10: confirm → onConfirm called with exact payload shape {preset, mode=\"snapshot\", max_records: 200}", () => {
    const { onConfirm } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    fireEvent.click(screen.getByTestId("btn-confirm"));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    const payload = onConfirm.mock.calls[0][0];
    expect(payload.preset).toBe("sglt2i_ckd");
    expect(payload.mode).toBe("snapshot");
    expect(payload.max_records).toBe(200);
    expect(Object.keys(payload).sort()).toEqual(["max_records", "mode", "preset"]);
  });

  it("11: confirm → payload with max=150 works", () => {
    const { onConfirm } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "150" } });
    fireEvent.click(screen.getByTestId("btn-confirm"));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm.mock.calls[0][0].max_records).toBe(150);
  });

  it("12: Live + max=199 → payload.mode=\"live\"", () => {
    const { onConfirm } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-empagliflozin_hf"));
    fireEvent.click(screen.getByTestId("mode-live"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "199" } });
    fireEvent.click(screen.getByTestId("btn-confirm"));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    const payload = onConfirm.mock.calls[0][0];
    expect(payload.mode).toBe("live");
    expect(payload.max_records).toBe(199);
  });

  it("13: ESC 关闭 → onClose called", () => {
    const { onClose } = renderModal();
    fireEvent.keyDown(screen.getByTestId("new-run-modal"), { key: "Escape" });
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("14: 预设 ckd_blood_pressure_control chosen → payload.preset matches", () => {
    const { onConfirm } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-ckd_blood_pressure_control"));
    fireEvent.click(screen.getByTestId("btn-confirm"));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm.mock.calls[0][0].preset).toBe("ckd_blood_pressure_control");
  });

  it("15: 多次切换 preset 后 confirm → final preset selected wins", () => {
    const { onConfirm } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    fireEvent.click(screen.getByTestId("preset-chip-glp1_weightloss"));
    fireEvent.click(screen.getByTestId("preset-chip-liraglutide_nafld"));
    fireEvent.click(screen.getByTestId("preset-chip-pkd_tolvaptan"));
    fireEvent.click(screen.getByTestId("btn-confirm"));
    expect(onConfirm).toHaveBeenCalledTimes(1);
    expect(onConfirm.mock.calls[0][0].preset).toBe("pkd_tolvaptan");
  });

  it("16: max_records = \"\" (空串) → disabled confirm", () => {
    const { onConfirm } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "" } });
    const btn = screen.getByTestId("btn-confirm") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
    fireEvent.click(btn);
    expect(onConfirm).not.toHaveBeenCalled();
  });

  it("17: form aria-label \"启动新 Pipeline Run dialog\" present", () => {
    renderModal();
    const dialog = screen.getByRole("dialog");
    expect(dialog.getAttribute("aria-label")).toBe("启动新 Pipeline Run dialog");
  });

  it("18: 所有交互 window.fetch 调用次数 = 0 (纯交互)", () => {
    const fetchSpy = vi.spyOn(window, "fetch");
    const { unmount } = renderModal();
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    fireEvent.click(screen.getByTestId("mode-live"));
    const input = screen.getByTestId("input-max-records") as HTMLInputElement;
    fireEvent.change(input, { target: { value: "123" } });
    fireEvent.click(screen.getByTestId("btn-cancel"));
    fireEvent.keyDown(screen.getByTestId("new-run-modal"), { key: "Escape" });
    fireEvent.click(screen.getByTestId("preset-chip-empagliflozin_hf"));
    fireEvent.click(screen.getByTestId("btn-confirm"));
    unmount();
    expect(fetchSpy).toHaveBeenCalledTimes(0);
  });
});
