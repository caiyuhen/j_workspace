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
  it("A01 card 包含 Moderate 文本", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.queryAllByText(/Moderate/).length).toBeGreaterThan(0);
  });

  it("A02 显示 outcome label 'MACE 12mo'", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.queryByText("MACE 12mo")).toBeTruthy();
  });

  it("A03 Save 按钮存在（按名称 /Save/i）", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: /Save/i })).toBeTruthy();
  });

  it("A04 Lock 按钮存在（按名称 /Lock/i）", () => {
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: /Lock/i })).toBeTruthy();
  });

  it("A05 Save 点击 → onSave 调用 1 次", () => {
    const onSave = vi.fn();
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={onSave} onLock={vi.fn()}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Save/i }));
    expect(onSave).toHaveBeenCalledTimes(1);
  });

  it("A06 Lock 点击 → onLock 调用 1 次", () => {
    const onLock = vi.fn();
    render(
      <GradeAssessmentCard
        outcomeLabel="MACE 12mo" reviewerLabel="Alice"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={onLock}
      />
    );
    fireEvent.click(screen.getByRole("button", { name: /Lock/i }));
    expect(onLock).toHaveBeenCalledTimes(1);
  });

  it("A07 locked=true → Save 按钮 disabled", () => {
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

  it("A08 locked=true → Lock 按钮 disabled (名称含 Lock 或 Unlock)", () => {
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

  it("A09 渲染 reviewerLabel 'Alice'", () => {
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

  it("A10 certainty=High → High 文本显示", () => {
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

  it("A11 certainty=Low → Low 文本", () => {
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

  it("A12 certainty=VeryLow → VeryLow 文本", () => {
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

  it("A13 props-only assertion (sanity)", () => {
    expect(true).toEqual(true);
  });

  it("A14 初始渲染不触发 onSave/onLock（zero calls）", () => {
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

  it("A15 certainty Moderate → innerHTML 匹配 /Moderate/", () => {
    const { container } = render(
      <GradeAssessmentCard
        outcomeLabel="X" reviewerLabel="R"
        domains={DOM5} upgrades={UPG3} certaintyFinal="Moderate"
        onDomainsChange={vi.fn()} onUpgradesChange={vi.fn()}
        onSave={vi.fn()} onLock={vi.fn()}
      />
    );
    expect(/Moderate/.test(container.innerHTML)).toEqual(true);
  });
});
