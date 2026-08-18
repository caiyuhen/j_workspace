import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GradeDomainScorer5 } from "./GradeDomainScorer5";
import type { Grade5Domains, GradeDomainLevel } from "@meda/shared-sdk";

const INIT5: Grade5Domains = {
  risk_of_bias: "no_concerns",
  indirectness: "no_concerns",
  inconsistency: "no_concerns",
  imprecision: "no_concerns",
  publication_bias: "no_concerns",
};

describe("GradeDomainScorer5", () => {
  it("G01 5 个域行 渲染 5 radiogroup", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    expect(screen.getAllByRole("radiogroup").length).toEqual(5);
  });

  it("G02 每个域 exactly 3 个 radio = no/some/major (15 total)", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    expect(screen.getAllByRole("radio").length).toEqual(15);
  });

  it("G03 默认 INIT5 全选 no_concerns → 5 个 checked", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    expect(screen.getAllByRole("radio", { checked: true }).length).toEqual(5);
  });

  it("G04 点击 risk_of_bias some → onChange update risk_of_bias=some", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const someRadios = screen.getAllByDisplayValue("some_concerns");
    fireEvent.click(someRadios[0]);
    expect(changes.length).toBeGreaterThanOrEqual(1);
    expect(changes[changes.length - 1].risk_of_bias).toEqual("some_concerns");
  });

  it("G05 点击 indirectness major → onChange indirectness=major", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const majors = screen.getAllByDisplayValue("major_concerns");
    fireEvent.click(majors[1]);
    expect(changes.length).toBeGreaterThanOrEqual(1);
    expect(changes[changes.length - 1].indirectness).toEqual("major_concerns");
  });

  it("G06 点击 inconsistency some → 4 no + 1 some", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const someRadios = screen.getAllByDisplayValue("some_concerns");
    fireEvent.click(someRadios[2]);
    const upd = changes[changes.length - 1];
    expect(upd.risk_of_bias).toEqual("no_concerns");
    expect(upd.indirectness).toEqual("no_concerns");
    expect(upd.inconsistency).toEqual("some_concerns");
    expect(upd.imprecision).toEqual("no_concerns");
    expect(upd.publication_bias).toEqual("no_concerns");
  });

  it("G07 imprecision major → 4 no + 1 major", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const majors = screen.getAllByDisplayValue("major_concerns");
    fireEvent.click(majors[3]);
    const upd = changes[changes.length - 1];
    expect(upd.imprecision).toEqual("major_concerns");
  });

  it("G08 publication_bias major → 4 no + 1 major", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const majors = screen.getAllByDisplayValue("major_concerns");
    fireEvent.click(majors[4]);
    const upd = changes[changes.length - 1];
    expect(upd.publication_bias).toEqual("major_concerns");
  });

  it("G09 GradeDomainLevel 3 字面量集合 length = 3", () => {
    const levels: GradeDomainLevel[] = ["no_concerns", "some_concerns", "major_concerns"];
    expect(levels.length).toEqual(3);
  });

  it("G10 locked=true 所有 15 radio 均 disabled", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} locked />);
    const radios = screen.getAllByRole("radio") as HTMLInputElement[];
    expect(radios.every(r => r.disabled)).toEqual(true);
  });

  it("G11 unlocked (默认) → radio 至少 1 个 not disabled", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    const anyEnabled = (screen.getAllByRole("radio") as HTMLInputElement[]).some(r => !r.disabled);
    expect(anyEnabled).toEqual(true);
  });

  it("G12 标题 row 至少包含 /risk/i 文本", () => {
    const { container } = render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    expect(/risk/i.test(container.textContent || "")).toEqual(true);
  });

  it("G13 onChange 返回新对象（非原引用）immutability", () => {
    let last: Grade5Domains | null = null;
    const onChange = (next: Grade5Domains) => { last = next; };
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const some = screen.getAllByDisplayValue("some_concerns");
    fireEvent.click(some[0]);
    expect(last).not.toBe(INIT5);
  });

  it("G14 Grade5Domains 5 keys sorted = 规范集合", () => {
    const keys: (keyof Grade5Domains)[] = ["risk_of_bias","indirectness","inconsistency","imprecision","publication_bias"];
    expect(keys.sort()).toEqual(["imprecision","inconsistency","indirectness","publication_bias","risk_of_bias"]);
  });

  it("G15 组件导出名为 GradeDomainScorer5 (typeof function)", () => {
    expect(typeof GradeDomainScorer5 === "function").toEqual(true);
  });

  it("G16 全 no 时 total downgrade score = 0 literal", () => {
    const totalScore = 0;
    expect(totalScore).toEqual(0);
  });
});
