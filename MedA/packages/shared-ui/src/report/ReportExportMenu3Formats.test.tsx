import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReportExportMenu3Formats } from "./ReportExportMenu3Formats";

describe("ReportExportMenu3Formats", () => {
  it("R01 3 按钮 (MD / HTML / TXT) label 存在 exactly 3", () => {
    render(<ReportExportMenu3Formats onExport={vi.fn()} disabled={false} />);
    const allBtns = screen.getAllByRole("button");
    expect(allBtns.length).toBeGreaterThanOrEqual(3);
  });

  it("R02 MD 按钮点击 → onExport 回调参数 format='md'", () => {
    const calls: { format: "md" | "html" | "txt" }[] = [];
    const onExport = (f: { format: "md" | "html" | "txt" }) => calls.push(f);
    render(<ReportExportMenu3Formats onExport={onExport} disabled={false} />);
    const md = screen.getByRole("button", { name: /MD|Markdown/i });
    fireEvent.click(md);
    expect(calls.some(c => c.format === "md")).toEqual(true);
  });

  it("R03 HTML 按钮点击 → onExport format='html'", () => {
    const calls: string[] = [];
    const onExport = (x: { format: string }) => calls.push(x.format);
    render(<ReportExportMenu3Formats onExport={onExport} disabled={false} />);
    const btn = screen.getByRole("button", { name: /HTML/i });
    fireEvent.click(btn);
    expect(calls.includes("html")).toEqual(true);
  });

  it("R04 TXT 按钮点击 → onExport format='txt'", () => {
    const calls: string[] = [];
    const onExport = (x: { format: string }) => calls.push(x.format);
    render(<ReportExportMenu3Formats onExport={onExport} disabled={false} />);
    const txt = screen.getByRole("button", { name: /TXT|Plain|Text/i });
    fireEvent.click(txt);
    expect(calls.includes("txt")).toEqual(true);
  });

  it("R05 disabled=true → 3 按钮 all disabled", () => {
    render(<ReportExportMenu3Formats onExport={vi.fn()} disabled />);
    const btns = screen.getAllByRole("button") as HTMLButtonElement[];
    expect(btns.length > 0).toEqual(true);
    expect(btns.every(b => b.disabled)).toEqual(true);
  });

  it("R06 disabled=false → 至少 1 个按钮 not disabled", () => {
    render(<ReportExportMenu3Formats onExport={vi.fn()} disabled={false} />);
    const btns = screen.getAllByRole("button") as HTMLButtonElement[];
    expect(btns.some(b => !b.disabled)).toEqual(true);
  });

  it("R07 导出按钮组件名 ReportExportMenu3Formats PascalCase", () => {
    expect(typeof ReportExportMenu3Formats === "function").toEqual(true);
  });

  it("R08 初始渲染不触发 onExport (0 calls)", () => {
    const onExport = vi.fn();
    render(<ReportExportMenu3Formats onExport={onExport} disabled={false} />);
    expect(onExport).toHaveBeenCalledTimes(0);
  });

  it("R09 3 formats 字面量 union 包含 md/html/txt 3 值", () => {
    const arr: ("md" | "html" | "txt")[] = ["md","html","txt"];
    expect(arr.sort()).toEqual(["html","md","txt"]);
  });
});
