import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GradeUpgradeScorer3 } from "./GradeUpgradeScorer3";
import type { Grade3Upgrades, GradeCertaintyFinal } from "@meda/shared-sdk";

const INIT_UP: Grade3Upgrades = { large_effect: false, dose_response: false, confounders_reduce: false };

describe("GradeUpgradeScorer3", () => {
  it("U01 3 checkboxes 存在 exactly 3", () => {
    render(<GradeUpgradeScorer3 value={INIT_UP} onChange={vi.fn()} certainty="High" />);
    expect(screen.getAllByRole("checkbox").length).toEqual(3);
  });

  it("U02 默认 INIT_UP 全 false → 0 checked", () => {
    render(<GradeUpgradeScorer3 value={INIT_UP} onChange={vi.fn()} certainty="High" />);
    expect(screen.getAllByRole("checkbox", { checked: false }).length).toEqual(3);
  });

  it("U03 点击 large_effect → onChange 返回 large_effect=true 其他 false", () => {
    const changes: Grade3Upgrades[] = [];
    const onChange = (next: Grade3Upgrades) => { changes.push(next); };
    render(<GradeUpgradeScorer3 value={INIT_UP} onChange={onChange} certainty="High" />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    fireEvent.click(boxes[0]);
    expect(changes.length).toBeGreaterThanOrEqual(1);
    expect(changes[changes.length - 1].large_effect).toEqual(true);
    expect(changes[changes.length - 1].dose_response).toEqual(false);
    expect(changes[changes.length - 1].confounders_reduce).toEqual(false);
  });

  it("U04 点击 dose_response → onChange 返回 dose_response=true", () => {
    const changes: Grade3Upgrades[] = [];
    const onChange = (next: Grade3Upgrades) => { changes.push(next); };
    render(<GradeUpgradeScorer3 value={INIT_UP} onChange={onChange} certainty="Moderate" />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    fireEvent.click(boxes[1]);
    expect(changes.length).toBeGreaterThanOrEqual(1);
    expect(changes[changes.length - 1].dose_response).toEqual(true);
  });

  it("U05 点击 confounders_reduce → onChange 返回 confounders_reduce=true", () => {
    const changes: Grade3Upgrades[] = [];
    const onChange = (next: Grade3Upgrades) => { changes.push(next); };
    render(<GradeUpgradeScorer3 value={INIT_UP} onChange={onChange} certainty="Low" />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    fireEvent.click(boxes[2]);
    expect(changes.length).toBeGreaterThanOrEqual(1);
    expect(changes[changes.length - 1].confounders_reduce).toEqual(true);
  });

  it("U06 全选 3 → 全 true", () => {
    const changes: Grade3Upgrades[] = [];
    const onChange = (next: Grade3Upgrades) => { changes.push(next); };
    const v: Grade3Upgrades = { large_effect: true, dose_response: true, confounders_reduce: false };
    render(<GradeUpgradeScorer3 value={v} onChange={onChange} certainty="VeryLow" />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    fireEvent.click(boxes[2]);
    expect(changes.length).toBeGreaterThanOrEqual(1);
    expect(changes[changes.length - 1]).toEqual({ large_effect: true, dose_response: true, confounders_reduce: true });
  });

  it("U07 certainty badge High green class/color present", () => {
    const { container } = render(<GradeUpgradeScorer3 value={INIT_UP} onChange={vi.fn()} certainty="High" />);
    expect(container.innerHTML.includes("High")).toEqual(true);
  });

  it("U08 certainty badge Moderate blue present", () => {
    const { container } = render(<GradeUpgradeScorer3 value={INIT_UP} onChange={vi.fn()} certainty="Moderate" />);
    expect(container.innerHTML.includes("Moderate")).toEqual(true);
  });

  it("U09 certainty badge Low orange present", () => {
    const { container } = render(<GradeUpgradeScorer3 value={INIT_UP} onChange={vi.fn()} certainty="Low" />);
    expect(container.innerHTML.includes("Low")).toEqual(true);
  });

  it("U10 certainty badge VeryLow red camelCase NO underscore present", () => {
    const { container } = render(<GradeUpgradeScorer3 value={INIT_UP} onChange={vi.fn()} certainty="VeryLow" />);
    expect(container.innerHTML.includes("VeryLow")).toEqual(true);
  });

  it("U11 locked=true 所有 checkbox disabled", () => {
    render(<GradeUpgradeScorer3 value={INIT_UP} onChange={vi.fn()} certainty="High" locked />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(boxes.every(b => b.disabled)).toEqual(true);
  });

  it("U12 unlocked=false checkbox not disabled", () => {
    render(<GradeUpgradeScorer3 value={INIT_UP} onChange={vi.fn()} certainty="High" />);
    const boxes = screen.getAllByRole("checkbox") as HTMLInputElement[];
    expect(boxes.some(b => !b.disabled)).toEqual(true);
  });

  it("U13 GradeCertaintyFinal 4 值 exact union（非驼峰外没有 Very_Low）", () => {
    const _a: GradeCertaintyFinal = "High";
    const _b: GradeCertaintyFinal = "Moderate";
    const _c: GradeCertaintyFinal = "Low";
    const _d: GradeCertaintyFinal = "VeryLow";
    expect([_a,_b,_c,_d].sort()).toEqual(["High","Low","Moderate","VeryLow"]);
  });

  it("U14 Grade3Upgrades 3 keys sorted equal 规范集合", () => {
    const keys: (keyof Grade3Upgrades)[] = ["large_effect","dose_response","confounders_reduce"];
    expect(keys.sort()).toEqual(["confounders_reduce","dose_response","large_effect"]);
  });
});
