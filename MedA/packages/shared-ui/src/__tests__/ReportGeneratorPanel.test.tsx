import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import {
  ReportGeneratorPanel,
  HTTP_422_DETAIL_MAP,
} from "../components/ReportGeneratorPanel";

const realDateNow = Date.now;
const TEST_SHA_LONG = "sha256_aabbccddeeff0011223344556677889900";

function makeProps(overrides: Partial<React.ComponentProps<typeof ReportGeneratorPanel>> = {}) {
  return {
    projectId: 1,
    sha256: null as string | null,
    versionLabel: null as string | null,
    errorDetailLiteral: null as string | null,
    activeTab: "editor" as const,
    onActiveTabChange: vi.fn(),
    editorSlot: <div data-testid="t-inject">injected-editor</div>,
    mdPreviewSlot: null as string | null,
    htmlPreviewSlot: null as string | null,
    onGenerateClick: vi.fn(),
    onExportClick: vi.fn(),
    isGenerating: false,
    isExporting: false,
    generatedAt: null as string | null,
    exportButtons: [] as Array<{label: string; onClick: () => void; testId?: string; variant?: "primary" | "ghost"}>,
    ...overrides,
  };
}

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-08-18T12:00:00Z"));
});

afterEach(() => {
  vi.useRealTimers();
  Date.now = realDateNow;
});

describe("Wave 8.4 T6 ReportGeneratorPanel P1~P15", () => {
  it("P1 渲染三 Tab (tab-editor/tab-md/tab-html) 全部存在", () => {
    const props = makeProps();
    render(<ReportGeneratorPanel {...props} />);
    expect(screen.getByTestId("tab-editor")).toBeTruthy();
    expect(screen.getByTestId("tab-md")).toBeTruthy();
    expect(screen.getByTestId("tab-html")).toBeTruthy();
  });

  it("P2 activeTab='editor' → tab-editor 高亮 aria-selected=true", () => {
    const props = makeProps({ activeTab: "editor" });
    render(<ReportGeneratorPanel {...props} />);
    const tabEditor = screen.getByTestId("tab-editor");
    const tabMd = screen.getByTestId("tab-md");
    const tabHtml = screen.getByTestId("tab-html");
    expect(tabEditor.getAttribute("aria-selected")).toBe("true");
    expect(tabMd.getAttribute("aria-selected")).toBe("false");
    expect(tabHtml.getAttribute("aria-selected")).toBe("false");
  });

  it("P3 点击 tab-md → 回调 onActiveTabChange('md') 触发", () => {
    const onActiveTabChange = vi.fn();
    const props = makeProps({ activeTab: "editor", onActiveTabChange });
    render(<ReportGeneratorPanel {...props} />);
    fireEvent.click(screen.getByTestId("tab-md"));
    expect(onActiveTabChange).toHaveBeenCalledTimes(1);
    expect(onActiveTabChange).toHaveBeenCalledWith("md");
  });

  it("P4 errorDetailLiteral='prisma_less_than_five' → err-detail 显示中文映射(包含 PRISMA 2020)", () => {
    const props = makeProps({ errorDetailLiteral: "prisma_less_than_five" });
    render(<ReportGeneratorPanel {...props} />);
    const err = screen.getByTestId("err-detail");
    expect(err.textContent).toContain("PRISMA 2020");
    expect(err.textContent).toBe(HTTP_422_DETAIL_MAP["prisma_less_than_five"]);
  });

  it("P5 errorDetailLiteral='forest_no_svg_content' → 包含 森林图 SVG 为空", () => {
    const props = makeProps({ errorDetailLiteral: "forest_no_svg_content" });
    render(<ReportGeneratorPanel {...props} />);
    const err = screen.getByTestId("err-detail");
    expect(err.textContent).toContain("森林图 SVG 为空");
    expect(err.textContent).toBe(HTTP_422_DETAIL_MAP["forest_no_svg_content"]);
  });

  it("P6 errorDetailLiteral='unknown_key_not_in_map' → err-detail 直接显示原文", () => {
    const props = makeProps({ errorDetailLiteral: "unknown_key_not_in_map" });
    render(<ReportGeneratorPanel {...props} />);
    const err = screen.getByTestId("err-detail");
    expect(err.textContent).toBe("unknown_key_not_in_map");
  });

  it("P7 sha256 为 null → 不渲染 sha row", () => {
    const props = makeProps({ sha256: null });
    render(<ReportGeneratorPanel {...props} />);
    expect(screen.queryByTestId("sha-row")).toBeNull();
  });

  it("P8 sha256='sha256_aabbccddeeff0011223344556677889900' → SHA 行显示前缀", () => {
    const props = makeProps({ sha256: TEST_SHA_LONG });
    render(<ReportGeneratorPanel {...props} />);
    expect(screen.getByTestId("sha-row")).toBeTruthy();
    const shaVal = screen.getByTestId("sha-value").textContent ?? "";
    expect(shaVal).toContain("sha256_");
    expect(shaVal.substring(0, 12)).toBe(TEST_SHA_LONG.substring(0, 12));
    expect(shaVal.slice(-4)).toBe(TEST_SHA_LONG.slice(-4));
  });

  it("P9 versionLabel='v0.1-draft' → 显示版本标签", () => {
    const props = makeProps({ sha256: TEST_SHA_LONG, versionLabel: "v0.1-draft" });
    render(<ReportGeneratorPanel {...props} />);
    const v = screen.getByTestId("version-label");
    expect(v.textContent).toBe("v0.1-draft");
  });

  it("P10 editorSlot 显示 children content (render t-inject)", () => {
    const props = makeProps({
      activeTab: "editor",
      editorSlot: <div data-testid="t-inject">slot-ok</div>,
    });
    render(<ReportGeneratorPanel {...props} />);
    const injected = screen.getByTestId("t-inject");
    expect(injected.textContent).toBe("slot-ok");
  });

  it("P11 mdPreviewSlot='## 1. Background\\nHello' → md-previewer 显示字符串", () => {
    const md = "## 1. Background\nHello";
    const props = makeProps({ activeTab: "md", mdPreviewSlot: md });
    render(<ReportGeneratorPanel {...props} />);
    const pre = screen.getByTestId("md-previewer");
    expect(pre.textContent).toBe(md);
  });

  it("P12 isGenerating=true → btn-generate-report disabled 且 spinner 存在", () => {
    const props = makeProps({ isGenerating: true });
    render(<ReportGeneratorPanel {...props} />);
    const btn = screen.getByTestId("btn-generate-report");
    expect(btn).toBeDisabled();
    expect(screen.queryByTestId("btn-spinner")).toBeTruthy();
  });

  it("P13 点击 btn-generate-report → onGenerateClick 触发", () => {
    const onGenerateClick = vi.fn();
    const props = makeProps({ onGenerateClick });
    render(<ReportGeneratorPanel {...props} />);
    fireEvent.click(screen.getByTestId("btn-generate-report"));
    expect(onGenerateClick).toHaveBeenCalledTimes(1);
  });

  it("P14 点击 export btn → onExportClick 触发", () => {
    const onExportClick = vi.fn();
    const props = makeProps({ onExportClick });
    render(<ReportGeneratorPanel {...props} />);
    const btn = screen.getByTestId("btn-export-report");
    fireEvent.click(btn);
    expect(onExportClick).toHaveBeenCalledTimes(1);
  });

  it("P15 exportButtons 数组 2 项 → 两个额外按钮分别点击触发对应 onClick", () => {
    const onClick1 = vi.fn();
    const onClick2 = vi.fn();
    const exportButtons = [
      { label: "下载 MD", onClick: onClick1, testId: "btn-download-md" },
      { label: "下载 HTML", onClick: onClick2, testId: "btn-download-html" },
    ];
    const props = makeProps({ exportButtons });
    render(<ReportGeneratorPanel {...props} />);
    const btn1 = screen.getByTestId("btn-download-md");
    const btn2 = screen.getByTestId("btn-download-html");
    expect(btn1.textContent).toBe("下载 MD");
    expect(btn2.textContent).toBe("下载 HTML");
    fireEvent.click(btn1);
    fireEvent.click(btn2);
    expect(onClick1).toHaveBeenCalledTimes(1);
    expect(onClick2).toHaveBeenCalledTimes(1);
  });
});
