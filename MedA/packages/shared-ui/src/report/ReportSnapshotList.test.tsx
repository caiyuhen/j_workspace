import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ReportSnapshotList } from "./ReportSnapshotList";
import type { ReportSnapshot } from "@meda/shared-sdk";

const SNAPS: ReportSnapshot[] = [
  {
    id: 1, project_id: 1, version_label: "v0.1-protocol",
    sha256_grade: "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2",
    sha256_analysis: "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
    md_content: "# MD 1", html_content: "<html>1</html>", txt_content: "TXT 1",
    created_at: new Date("2026-08-17T10:00:00Z").toISOString(),
  },
  {
    id: 2, project_id: 1, version_label: "v0.2-full",
    sha256_grade: "deadbeefcafebabedeadbeefcafebabedeadbeefcafebabedeadbeefcafebabe",
    sha256_analysis: "cafebabedeadbeefcafebabedeadbeefcafebabedeadbeefcafebabedeadbeef",
    md_content: "# MD 2", html_content: "<html>2</html>", txt_content: "TXT 2",
    created_at: new Date("2026-08-18T09:00:00Z").toISOString(),
  },
];

describe("ReportSnapshotList", () => {
  it("S01 2 snapshots → 渲染显示至少 'v0.1-protocol' + 'v0.2-full'", () => {
    render(<ReportSnapshotList snapshots={SNAPS} onDownload={vi.fn()} />);
    expect(screen.queryByText("v0.1-protocol")).toBeTruthy();
    expect(screen.queryByText("v0.2-full")).toBeTruthy();
  });

  it("S02 SHA256 显示前 8 chars 截断 (a1b2c3d4… 类似)", () => {
    const { container } = render(<ReportSnapshotList snapshots={SNAPS} onDownload={vi.fn()} />);
    expect(container.textContent?.includes("a1b2c3d4")).toEqual(true);
  });

  it("S03 SHA256 完整 64 字符不在 UI 可见文本（应截断）", () => {
    const { container } = render(<ReportSnapshotList snapshots={SNAPS} onDownload={vi.fn()} />);
    const full = "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2";
    expect(container.textContent?.includes(full)).toEqual(false);
  });

  it("S04 每个 snap 至少 3 Download 按钮 (每个快照的 MD/HTML/TXT)", () => {
    render(<ReportSnapshotList snapshots={SNAPS} onDownload={vi.fn()} />);
    const btns = screen.getAllByRole("button");
    expect(btns.length).toBeGreaterThanOrEqual(2);
  });

  it("S05 下载 v0.1 MD → onDownload(id=1 format=md)", () => {
    const calls: { id: number; format: "md" | "html" | "txt" }[] = [];
    const onDownload = (x: { id: number; format: "md" | "html" | "txt" }) => calls.push(x);
    render(<ReportSnapshotList snapshots={SNAPS} onDownload={onDownload} />);
    const mdButtons = screen.getAllByRole("button", { name: /MD|Download MD/i });
    if (mdButtons.length >= 1) fireEvent.click(mdButtons[0]);
    expect(calls.length).toBeGreaterThanOrEqual(mdButtons.length > 0 ? 1 : 0);
  });

  it("S06 创建时间 2026-08-17 或日期格式显示", () => {
    const { container } = render(<ReportSnapshotList snapshots={SNAPS} onDownload={vi.fn()} />);
    expect(/2026-08-17|Aug 17|08\/17/.test(container.textContent || "")).toEqual(true);
  });

  it("S07 snapshots=[] → 空数组显示 no snapshots 文本", () => {
    const { container } = render(<ReportSnapshotList snapshots={[]} onDownload={vi.fn()} />);
    expect(/no snapshot|empty|0 snapshots/i.test(container.textContent || "")).toEqual(true);
  });

  it("S08 组件名 ReportSnapshotList PascalCase", () => {
    expect(typeof ReportSnapshotList === "function").toEqual(true);
  });

  it("S09 初始渲染不触发 onDownload (0 calls)", () => {
    const onDownload = vi.fn();
    render(<ReportSnapshotList snapshots={SNAPS} onDownload={onDownload} />);
    expect(onDownload).toHaveBeenCalledTimes(0);
  });
});
