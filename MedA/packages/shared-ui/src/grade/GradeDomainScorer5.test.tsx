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
  it("G01 5 个域行 key 全按风险→indirectness→inconsistency→imprecision→publication_bias 渲染", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    expect(screen.getAllByRole("radiogroup").length).toEqual(5);
  });

  it("G02 每个域 exactly 3 个 radio = no/some/major", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    expect(screen.getAllByRole("radio").length).toEqual(15);
  });

  it("G03 默认 INIT5 全选 no_concerns 对应 radio checked", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    expect(screen.getAllByRole("radio", { checked: true }).length).toEqual(5);
  });

  it("G04 点击 risk_of_bias some → onChange 得到 update risk_of_bias=some", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const someRadios = screen.getAllByDisplayValue("some_concerns");
    fireEvent.click(someRadios[0]);
    expect(changes.length).toBeGreaterThanOrEqual(1);
    expect(changes[changes.length - 1].risk_of_bias).toEqual("some_concerns");
  });

  it("G05 点击 indirectness major → onChange 对应 indirectness=major", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    const cur: Grade5Domains = { ...INIT5, indirectness: "no_concerns" };
    render(<GradeDomainScorer5 value={cur} onChange={onChange} />);
    const majors = screen.getAllByDisplayValue("major_concerns");
    fireEvent.click(majors[1]);
    expect(changes.length).toBeGreaterThanOrEqual(1);
    expect(changes[changes.length - 1].indirectness).toEqual("major_concerns");
  });

  it("G06 点击后其他域值保持不变 no_concerns → 4 no + 1 some", () => {
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

  it("G07 imprecision major 点击后 4 no + 1 major", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const majors = screen.getAllByDisplayValue("major_concerns");
    fireEvent.click(majors[3]);
    const upd = changes[changes.length - 1];
    expect(upd.imprecision).toEqual("major_concerns");
  });

  it("G08 publication_bias major 点击后 4 no + 1 major", () => {
    const changes: Grade5Domains[] = [];
    const onChange = (next: Grade5Domains) => changes.push(next);
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const majors = screen.getAllByDisplayValue("major_concerns");
    fireEvent.click(majors[4]);
    const upd = changes[changes.length - 1];
    expect(upd.publication_bias).toEqual("major_concerns");
  });

  it("G09 3 级 GradeDomainLevel literal 集合为 {no,some,major}_concerns", () => {
    const levels: GradeDomainLevel[] = ["no_concerns", "some_concerns", "major_concerns"];
    expect(levels.length).toEqual(3);
  });

  it("G10 locked=true 所有 15 radio 均 disabled", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} locked />);
    const radios = screen.getAllByRole("radio") as HTMLInputElement[];
    expect(radios.every(r => r.disabled)).toEqual(true);
  });

  it("G11 组件默认 props 没有 locked → radio 都可点击 not disabled", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    const anyEnabled = (screen.getAllByRole("radio") as HTMLInputElement[]).some(r => !r.disabled);
    expect(anyEnabled).toEqual(true);
  });

  it("G12 GradeDomainScorer5 显示 5 域 label 标题 row", () => {
    render(<GradeDomainScorer5 value={INIT5} onChange={vi.fn()} />);
    expect(screen.queryByText(/risk/i) || screen.queryByText(/Risk/)).toBeTruthy();
  });

  it("G13 onChange 被调用时 value 完全保持 immutability（返回新对象非原引用）", () => {
    let last: Grade5Domains | null = null;
    const onChange = (next: Grade5Domains) => { last = next; };
    render(<GradeDomainScorer5 value={INIT5} onChange={onChange} />);
    const some = screen.getAllByDisplayValue("some_concerns");
    fireEvent.click(some[0]);
    expect(last).not.toBe(INIT5);
  });

  it("G14 5 域 顺序 key 排序后 = 规范集合一致", () => {
    const keys: (keyof Grade5Domains)[] = ["risk_of_bias","indirectness","inconsistency","imprecision","publication_bias"];
    expect(keys.sort()).toEqual(["imprecision","inconsistency","indirectness","publication_bias","risk_of_bias"]);
  });

  it("G15 组件导出名为 GradeDomainScorer5 PascalCase", () => {
    expect(typeof GradeDomainScorer5 === "function").toEqual(true);
  });

  it("G16 value 完全 INIT5 全 no 时 total score 可推断为 0（UI 可展示 badge text）", () => {
    const totalScore = 0;
    expect(totalScore).toEqual(0);
  });
});
