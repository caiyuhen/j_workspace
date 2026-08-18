import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Prisma2020Checklist27 } from "./Prisma2020Checklist27";
import type { Prisma2020Checklist } from "@meda/shared-sdk";

const INIT: Prisma2020Checklist = {
  id: 1, project_id: 1, reviewer_id: 1,
  item_1: true, item_2: true, item_3: true, item_4: true, item_5: true,
  item_6: false, item_7: false, item_8: false, item_9: false, item_10: false,
  item_11: false, item_12: false, item_13: false, item_14: false, item_15: false,
  item_16: false, item_17: false, item_18: false, item_19: false, item_20: false,
  item_21: false, item_22: false, item_23: false, item_24: false, item_25: false,
  item_26: false, item_27: false,
  note: "", locked: false, created_at: new Date().toISOString(),
};

describe("Prisma2020Checklist27", () => {
  it("P01 27 个 checkboxes exactly (items 1-27)", () => {
    render(<Prisma2020Checklist27 value={INIT} onChange={vi.fn()} />);
    expect(screen.getAllByRole("checkbox").length).toEqual(27);
  });

  it("P02 INIT 前 5 true → 5 checked", () => {
    render(<Prisma2020Checklist27 value={INIT} onChange={vi.fn()} />);
    expect(screen.getAllByRole("checkbox", { checked: true }).length).toEqual(5);
  });

  it("P03 点击 item_6 (第一个 false 的) → onChange 返回 item_6=true 其他不变", () => {
    let last: Prisma2020Checklist | null = null;
    const onChange = (next: Prisma2020Checklist) => { last = next; };
    render(<Prisma2020Checklist27 value={INIT} onChange={onChange} />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    // boxes[0..4] = items 1-5 true; boxes[5] = item_6
    fireEvent.click(boxes[5]);
    expect(last).not.toBeNull();
    expect(last!.item_6).toEqual(true);
    expect(last!.item_1).toEqual(true);
  });

  it("P04 progress 5/27 → 文本包含 5 或 18% 或 19% 近似", () => {
    const { container } = render(<Prisma2020Checklist27 value={INIT} onChange={vi.fn()} />);
    const text = container.textContent || "";
    expect(/5\/27|18\.5%|19%|18%|5 of 27/.test(text)).toEqual(true);
  });

  it("P05 locked=true → 27 checkboxes all disabled", () => {
    render(<Prisma2020Checklist27 value={{ ...INIT, locked: true }} onChange={vi.fn()} />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(boxes.every(b => b.disabled)).toEqual(true);
  });

  it("P06 locked=false → 至少 1 checkbox enabled", () => {
    render(<Prisma2020Checklist27 value={INIT} onChange={vi.fn()} />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(boxes.some(b => !b.disabled)).toEqual(true);
  });

  it("P07 全 27 true → 27 个 checked", () => {
    const allTrue: Prisma2020Checklist = { ...INIT };
    for (let i = 1; i <= 27; i++) (allTrue as any)[`item_${i}`] = true;
    render(<Prisma2020Checklist27 value={allTrue} onChange={vi.fn()} />);
    expect(screen.getAllByRole("checkbox", { checked: true }).length).toEqual(27);
  });

  it("P08 全 27 false → 0 checked", () => {
    const allFalse: Prisma2020Checklist = { ...INIT };
    for (let i = 1; i <= 27; i++) (allFalse as any)[`item_${i}`] = false;
    render(<Prisma2020Checklist27 value={allFalse} onChange={vi.fn()} />);
    expect(screen.getAllByRole("checkbox", { checked: false }).length).toEqual(27);
  });

  it("P09 组件名 Prisma2020Checklist27 PascalCase", () => {
    expect(typeof Prisma2020Checklist27 === "function").toEqual(true);
  });
});
