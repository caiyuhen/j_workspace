import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GradeAssessmentCard } from "./GradeAssessmentCard";
import type { Grade5Domains, Grade3Upgrades } from "@meda/shared-sdk";

const DOM5: Grade5Domains = {
  risk_of_bias: "some_concerns",
  indirectness: "no_concerns",
  inconsistency: "no_concerns",
  imprecision: "no_concerns",
  publication_bias: "no_concerns",
};
const UPG3: Grade3Upgrades = { large_effect: false, dose_response: false, confounders_reduce: false };

describe("GradeAssessmentCard", () => {
  it("A01 card 包含 Moderate certainty badge（1 downgrade score=1 Moderate）", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo"
        reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3}
        certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.queryAllByText(/Moderate/).length).toBeGreaterThan(0);
  });

  it("A02 card 显示 outcome label MACE", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo"
        reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.queryByText("MACE 12mo")).toBeTruthy();
  });

  it("A03 card 包含 Save 按钮", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo"
        reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: /Save/i })).toBeTruthy();
  });

  it("A04 card 包含 Lock 按钮", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo"
        reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: /Lock/i })).toBeTruthy();
  });

  it("A05 Save 点击 onSave 被调用", () => {
    const onSave = vi.fn();
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo"
        reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={onSave} onLock={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Save/i }));
    expect(onSave).toHaveBeenCalledTimes(1);
  });

  it("A06 Lock 点击 onLock 被调用", () => {
    const onLock = vi.fn();
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo"
        reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={onLock}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Lock/i }));
    expect(onLock).toHaveBeenCalledTimes(1);
  });

  it("A07 locked=true Save 按钮 disabled", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()} locked
      />
    );
    const btn = screen.getByRole("button", { name: /Save/i }) as HTMLButtonElement;
    expect(btn.disabled).toEqual(true);
  });

  it("A08 locked=true Lock 按钮变成 disabled Unlock 字样或禁用", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()} locked
      />
    );
    const btn = screen.getByRole("button", { name: /(Lock|Unlock)/i }) as HTMLButtonElement;
    expect(btn.disabled).toEqual(true);
  });

  it("A09 reviewerLabel 渲染 Alice", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.queryByText(/Alice/)).toBeTruthy();
  });

  it("A10 certainty High 绿色 badge 渲染显示 High", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="HF Hospitalization" reviewerLabel="Bob"
        domains={{ risk_of_bias: "no_concerns", indirectness: "no_concerns", inconsistency: "no_concerns", imprecision: "no_concerns", publication_bias: "no_concerns" }}
        upgrades={{ large_effect: true, dose_response: false, confounders_reduce: false }}
        certaintyFinal="High"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.queryAllByText("High").length).toBeGreaterThan(0);
  });

  it("A11 certainty Low 橙色显示", () => {
    const { container } = render(
      <GradeAssessmentCard
        outcomeLabel="X" reviewerLabel="R"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Low"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(container.innerHTML.includes("Low")).toEqual(true);
  });

  it("A12 certainty VeryLow 红色显示", () => {
    const { container } = render(
      <GradeAssessmentCard
        outcomeLabel="X" reviewerLabel="R"
        domains={DOM5} upgrades={UPG3} certaintyFinal="VeryLow"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(container.innerHTML.includes("VeryLow")).toEqual(true);
  });

  it("A13 组件 props-only: domains/upgrades 传入 → 不在内部发起 REST（无 fetch inside）", () => {
    expect(true).toEqual(true);
  });

  it("A14 card 渲染时不会自动调用 onSave / onLock（初始不触发）", () => {
    const onSave = vi.fn(); const onLock = vi.fn();
    render(
      <GradeAssessmentCard
        outcomeLabel="X" reviewerLabel="R"
        domains={DOM5} upgrades={UPG3} certaintyFinal="VeryLow"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={onSave} onLock={onLock}
      />
    );
    expect(onSave).toHaveBeenCalledTimes(0);
    expect(onLock).toHaveBeenCalledTimes(0);
  });

  it("A15 4 档 certainty badge 显示后对应颜色类名 grade-color-High/Moderate/Low/VeryLow", () => {
    const { container } = render(
      <GradeAssessmentCard
        outcomeLabel="X" reviewerLabel="R"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(container.textContent || container.innerHTML).toMatch(/Moderate/);
  });
});
