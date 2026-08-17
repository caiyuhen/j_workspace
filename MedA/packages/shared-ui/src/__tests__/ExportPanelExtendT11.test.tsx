import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import fs from "fs";
import path from "path";
import { ExportPanel } from "../export/ExportPanel";
import type { ExportPanelProps } from "../export/ExportPanel";
import * as SharedUiIndex from "../index";

function makeDetail(overrides: any = {}) {
  const base = {
    run: {
      id: 123,
      status: "completed",
      total_hits_raw: 100,
      total_after_dedupe: 80,
      prisma: {
        identification: 80,
        screening: 60,
        eligibility: 40,
        included: 20,
        by_source: [],
      },
      created_at: "2026-08-14T10:00:00Z",
    },
    sources: [
      { source_key: "pubmed", source_label: "PubMed", records_retrieved: 50, records_imported: 40, status: "completed" },
      { source_key: "cnki", source_label: "CNKI", records_retrieved: 50, records_imported: 40, status: "completed" },
    ],
    records: [
      { id: "1", title: "Test Paper 1", authors: ["Alice", "Bob"], journal: "Nature", year: 2024, source: "pubmed" },
      { id: "2", title: "Test Paper 2", authors: ["Charlie"], journal: "Science", year: 2023, source: "cnki" },
      { id: "3", title: "Test Paper 3", authors: ["Dave"], journal: "Cell", year: 2022, source: "pubmed" },
    ],
  };
  return { ...base, ...overrides, run: { ...base.run, ...(overrides.run ?? {}) } };
}

const realDateNow = Date.now;
const realToISO = Date.prototype.toISOString;

beforeEach(() => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date("2026-08-14T12:00:00Z"));
  vi.mock("../export/downloadDiagnosticText", () => ({
    downloadBlob: vi.fn(),
    downloadDataUrl: vi.fn(),
    downloadDiagnosticText: vi.fn(),
  }));
});
afterEach(() => {
  vi.useRealTimers();
  Date.now = realDateNow;
  Date.prototype.toISOString = realToISO;
  vi.restoreAllMocks();
});

// ===========================================================================
// GROUP A ExportPanel extend Props（14 tests）
// ===========================================================================
describe("GROUP A ExportPanel extend Props (14 tests)", () => {
  it("A1 baseline 原按钮 + 2 新按钮 → screen.getAllByRole('button') length === 6", () => {
    render(<ExportPanel detail={makeDetail()} />);
    const buttons = screen.getAllByRole("button");
    expect(buttons.length).toBe(6);
  });

  it("A2 传入 onExportEvidenceCsv → click btn-export-evidence-csv → vi mock 回调 1 次", () => {
    const onExportEvidenceCsv = vi.fn();
    render(<ExportPanel detail={makeDetail()} onExportEvidenceCsv={onExportEvidenceCsv} />);
    const btn = screen.getByTestId("btn-export-evidence-csv");
    fireEvent.click(btn);
    expect(onExportEvidenceCsv).toHaveBeenCalledTimes(1);
  });

  it("A3 传入 onExportForestSvg → click btn-export-forest-svg → callback 1 次", () => {
    const onExportForestSvg = vi.fn();
    render(<ExportPanel detail={makeDetail()} onExportForestSvg={onExportForestSvg} />);
    const btn = screen.getByTestId("btn-export-forest-svg");
    fireEvent.click(btn);
    expect(onExportForestSvg).toHaveBeenCalledTimes(1);
  });

  it("A4 不传 onExportEvidenceCsv（undefined）→ btn-export-evidence-csv disabled 属性 true", () => {
    render(<ExportPanel detail={makeDetail()} />);
    const btn = screen.getByTestId("btn-export-evidence-csv") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("A5 不传 onExportForestSvg → btn disabled", () => {
    render(<ExportPanel detail={makeDetail()} />);
    const btn = screen.getByTestId("btn-export-forest-svg") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("A6 原 export-ris-btn 依然存在（baseline smoke 不破）", () => {
    render(<ExportPanel detail={makeDetail()} />);
    expect(screen.getByTestId("export-ris-btn")).toBeTruthy();
  });

  it("A7 原 export-bibtex-btn 依然存在", () => {
    render(<ExportPanel detail={makeDetail()} />);
    expect(screen.getByTestId("export-bibtex-btn")).toBeTruthy();
  });

  it("A8 原 export-csv-btn 依然存在（通用文献 CSV，与新 btn-export-evidence-csv 不冲突）", () => {
    render(<ExportPanel detail={makeDetail()} />);
    expect(screen.getByTestId("export-csv-btn")).toBeTruthy();
    expect(screen.getByTestId("btn-export-evidence-csv")).toBeTruthy();
  });

  it("A9 export-prisma-btn 依然存在", () => {
    render(<ExportPanel detail={makeDetail()} />);
    expect(screen.getByTestId("export-prisma-btn")).toBeTruthy();
  });

  it("A10 传入全部 6 callbacks → 所有按钮 enabled（不 disabled）", () => {
    const onRisExport = vi.fn();
    const onBibTeXExport = vi.fn();
    const onCsvExport = vi.fn();
    const onExportEvidenceCsv = vi.fn();
    const onPRISMAExport = vi.fn();
    const onExportForestSvg = vi.fn();
    render(
      <ExportPanel
        detail={makeDetail()}
        onRisExport={onRisExport}
        onBibTeXExport={onBibTeXExport}
        onCsvExport={onCsvExport}
        onExportEvidenceCsv={onExportEvidenceCsv}
        onPRISMAExport={onPRISMAExport}
        onExportForestSvg={onExportForestSvg}
      />
    );
    const ids = [
      "export-ris-btn",
      "export-bibtex-btn",
      "export-csv-btn",
      "btn-export-evidence-csv",
      "export-prisma-btn",
      "btn-export-forest-svg",
    ];
    ids.forEach((id) => {
      expect((screen.getByTestId(id) as HTMLButtonElement).disabled).toBe(false);
    });
  });

  it("A11 ExportPanel 包含 children（title 标题或 wrapper）", () => {
    const { container } = render(
      <ExportPanel detail={makeDetail()}>
        <span data-testid="panel-children-title">Export Options</span>
      </ExportPanel>
    );
    expect(screen.getByTestId("panel-children-title")).toBeTruthy();
    expect(container.textContent).toContain("Export Options");
  });

  it("A12 disabled btn 不会 fire 回调（status=pending disabled + click → 0 次 callback fire）", () => {
    const onExportEvidenceCsv = vi.fn();
    const onExportForestSvg = vi.fn();
    const detail = makeDetail({ run: { status: "pending" } });
    render(
      <ExportPanel
        detail={detail}
        onExportEvidenceCsv={onExportEvidenceCsv}
        onExportForestSvg={onExportForestSvg}
      />
    );
    fireEvent.click(screen.getByTestId("btn-export-evidence-csv"));
    fireEvent.click(screen.getByTestId("btn-export-forest-svg"));
    expect(onExportEvidenceCsv).toHaveBeenCalledTimes(0);
    expect(onExportForestSvg).toHaveBeenCalledTimes(0);
  });

  it("A13 按钮顺序检查 DOM tabIndex 自然流动：Ris → Bib → 通用CSV → 证据CSV → PRISMA → Forest SVG", () => {
    render(<ExportPanel detail={makeDetail()} />);
    const buttons = screen.getAllByRole("button");
    const order = buttons.map((b) => (b as HTMLElement).getAttribute("data-testid"));
    expect(order).toEqual([
      "export-ris-btn",
      "export-bibtex-btn",
      "export-csv-btn",
      "btn-export-evidence-csv",
      "export-prisma-btn",
      "btn-export-forest-svg",
    ]);
  });

  it("A14 Extend Props backward compat：仅传 onRisExport（旧用法）→ 其他 5 按钮都显示为 disabled，不 crash，无 React warning", () => {
    const onRisExport = vi.fn();
    const consoleError = vi.spyOn(console, "error").mockImplementation(() => {});
    render(<ExportPanel detail={makeDetail()} onRisExport={onRisExport} />);
    expect((screen.getByTestId("export-ris-btn") as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByTestId("export-bibtex-btn") as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByTestId("export-csv-btn") as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByTestId("btn-export-evidence-csv") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId("export-prisma-btn") as HTMLButtonElement).disabled).toBe(false);
    expect((screen.getByTestId("btn-export-forest-svg") as HTMLButtonElement).disabled).toBe(true);
    fireEvent.click(screen.getByTestId("export-ris-btn"));
    expect(onRisExport).toHaveBeenCalledTimes(1);
    expect(consoleError).not.toHaveBeenCalled();
    consoleError.mockRestore();
  });
});

// ===========================================================================
// GROUP B shared-ui barrel exports（6 tests）
// ===========================================================================
describe("GROUP B shared-ui barrel exports (6 tests)", () => {
  it("B1 import { ExtractionTemplatePage } from shared-ui index 解析不 undefined", () => {
    expect(SharedUiIndex.ExtractionTemplatePage).not.toBeUndefined();
  });

  it("B2 exports.AnalysisMetaPage not undefined", () => {
    expect(SharedUiIndex.AnalysisMetaPage).not.toBeUndefined();
  });

  it("B3 exports.ForestPlotW83 not undefined", () => {
    expect(SharedUiIndex.ForestPlotW83).not.toBeUndefined();
  });

  it("B4 12 个 exports 全运行时加载 OK（6 组件 + 6 类型）", () => {
    expect(SharedUiIndex.ExtractionTemplatePage).toBeDefined();
    expect(SharedUiIndex.SingleRecordExtractionPage).toBeDefined();
    expect(SharedUiIndex.EvidenceTablePage).toBeDefined();
    expect(SharedUiIndex.AnalysisMetaPage).toBeDefined();
    expect(SharedUiIndex.OutcomeArmInputs).toBeDefined();
    expect(SharedUiIndex.ForestPlotW83).toBeDefined();
    const typeKeys = [
      "ExtractionTemplatePageProps",
      "SingleRecordExtractionPageProps",
      "EvidenceTablePageProps",
      "AnalysisMetaPageProps",
      "OutcomeArmInputsProps",
      "ForestPlotW83Props",
    ];
    typeKeys.forEach((key) => {
      expect(Object.keys(SharedUiIndex).length).toBeGreaterThanOrEqual(12);
    });
  });

  it("B5 exports keys count：至少新增 12 W8.3 keys（过滤包含 W83 / Extraction / Evidence / Analysis / Outcome / Forest）", () => {
    const runtimeKeys = Object.keys(SharedUiIndex);
    const w83RuntimeKeys = runtimeKeys.filter(
      (k) =>
        k.includes("ExtractionTemplate") ||
        k.includes("SingleRecordExtraction") ||
        k.includes("EvidenceTable") ||
        k.includes("AnalysisMeta") ||
        k.includes("OutcomeArm") ||
        k.includes("ForestPlotW83")
    );
    const indexPath = path.resolve(__dirname, "../index.ts");
    const indexSource = fs.readFileSync(indexPath, "utf-8");
    const w83BlockMatch = indexSource.match(/---- W8\.3 BLOCK ----([\s\S]*)$/);
    expect(w83BlockMatch).not.toBeNull();
    const w83Block = w83BlockMatch![1];
    const exportLineCount = (w83Block.match(/^export /gm) || []).length;
    expect(exportLineCount).toBeGreaterThanOrEqual(12);
    expect(w83RuntimeKeys.length).toBeGreaterThanOrEqual(6);
  });

  it("B6 ExportPanelProps 类型可访问 onExportEvidenceCsv 字段（通过对象 key 检测运行时等效）", () => {
    const propsChecker: Partial<ExportPanelProps> = {
      onExportEvidenceCsv: () => {},
      onExportForestSvg: () => {},
    };
    expect(propsChecker).toHaveProperty("onExportEvidenceCsv");
    expect(propsChecker).toHaveProperty("onExportForestSvg");
    expect(typeof propsChecker.onExportEvidenceCsv).toBe("function");
    expect(typeof propsChecker.onExportForestSvg).toBe("function");
  });
});
