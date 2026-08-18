import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import React from "react";
import { ExportPanel } from "../export/ExportPanel";
import { PrismaOverrideEditorT11 } from "../index";
import type { PrismaOverrideEditorT11Props } from "../index";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
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

// ---------------------------------------------------------------------------
// Wave82B T11 ExportPanel (14 vitest)
// ---------------------------------------------------------------------------
describe("Wave82B T11 ExportPanel (14 vitest)", () => {
  it("T11-EP01 ExportPanel present: export-panel data-testid 存在", () => {
    render(<ExportPanel detail={makeDetail()} />);
    expect(screen.getByTestId("export-panel")).toBeTruthy();
  });

  it("T11-EP02 6 导出按钮 present（新增 Evidence CSV/Forest SVG 两个）", () => {
    render(<ExportPanel detail={makeDetail()} />);
    expect(screen.getByTestId("export-ris-btn")).toBeTruthy();
    expect(screen.getByTestId("export-bibtex-btn")).toBeTruthy();
    expect(screen.getByTestId("export-csv-btn")).toBeTruthy();
    expect(screen.getByTestId("btn-export-evidence-csv")).toBeTruthy();
    expect(screen.getByTestId("export-prisma-btn")).toBeTruthy();
    expect(screen.getByTestId("btn-export-forest-svg")).toBeTruthy();
  });

  it("T11-EP03 status=pending → 6 buttons 全 disabled", () => {
    const detail = makeDetail({ run: { status: "pending" } });
    render(
      <ExportPanel
        detail={detail}
        onExportEvidenceCsv={() => {}}
        onExportForestSvg={() => {}}
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
      expect((screen.getByTestId(id) as HTMLButtonElement).disabled).toBe(true);
    });
  });

  it("T11-EP04 status=completed + records[]=empty → 仍 enabled（空态非 disabled）", () => {
    const detail = makeDetail({ records: [] });
    render(
      <ExportPanel
        detail={detail}
        onExportEvidenceCsv={() => {}}
        onExportForestSvg={() => {}}
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

  it("T11-EP05 RIS click → onDone('ris',{filename,count})", () => {
    const onDone = vi.fn();
    const detail = makeDetail();
    render(<ExportPanel detail={detail} onDone={onDone} />);
    fireEvent.click(screen.getByTestId("export-ris-btn"));
    expect(onDone).toHaveBeenCalledWith("ris", expect.objectContaining({ count: 3 }));
  });

  it("T11-EP06 BibTeX click → onDone('bibtex',{filename,count})", () => {
    const onDone = vi.fn();
    const detail = makeDetail();
    render(<ExportPanel detail={detail} onDone={onDone} />);
    fireEvent.click(screen.getByTestId("export-bibtex-btn"));
    expect(onDone).toHaveBeenCalledWith("bibtex", expect.objectContaining({ count: 3 }));
  });

  it("T11-EP07 CSV click → onDone('csv',{filename,count})", () => {
    const onDone = vi.fn();
    const detail = makeDetail();
    render(<ExportPanel detail={detail} onDone={onDone} />);
    fireEvent.click(screen.getByTestId("export-csv-btn"));
    expect(onDone).toHaveBeenCalledWith("csv", expect.objectContaining({ count: 3 }));
  });

  it("T11-EP08 Evidence CSV click → onExportEvidenceCsv callback 1 次", () => {
    const onExportEvidenceCsv = vi.fn();
    const detail = makeDetail();
    render(
      <ExportPanel
        detail={detail}
        onExportEvidenceCsv={onExportEvidenceCsv}
      />
    );
    fireEvent.click(screen.getByTestId("btn-export-evidence-csv"));
    expect(onExportEvidenceCsv).toHaveBeenCalledTimes(1);
  });

  it("T11-EP09 CSV file extension .csv in filename", () => {
    const onDone = vi.fn();
    const detail = makeDetail();
    render(<ExportPanel detail={detail} onDone={onDone} />);
    fireEvent.click(screen.getByTestId("export-csv-btn"));
    const args = onDone.mock.calls[0];
    expect(args[1].filename).toMatch(/\.csv$/);
  });

  it("T11-EP10 Forest SVG click → onExportForestSvg callback 1 次", () => {
    const onExportForestSvg = vi.fn();
    const detail = makeDetail();
    render(
      <ExportPanel
        detail={detail}
        onExportForestSvg={onExportForestSvg}
      />
    );
    fireEvent.click(screen.getByTestId("btn-export-forest-svg"));
    expect(onExportForestSvg).toHaveBeenCalledTimes(1);
  });

  it("T11-EP11 RIS error path → onDone('ris_error',{error})", () => {
    const onDone = vi.fn();
    const badSerialize = vi.fn(() => {
      throw new Error("bad ris");
    });
    const detail = makeDetail();
    render(<ExportPanel detail={detail} onDone={onDone} serializeRIS={badSerialize} />);
    fireEvent.click(screen.getByTestId("export-ris-btn"));
    expect(onDone).toHaveBeenCalledWith("ris_error", expect.objectContaining({ error: "bad ris" }));
  });

  it("T11-EP12 custom serializeCSV prop injected 替代默认", () => {
    const onDone = vi.fn();
    const customCsv = vi.fn(() => "custom,csv\n1,2");
    const detail = makeDetail();
    render(<ExportPanel detail={detail} onDone={onDone} serializeCSV={customCsv} />);
    fireEvent.click(screen.getByTestId("export-csv-btn"));
    expect(customCsv).toHaveBeenCalledTimes(1);
    expect(customCsv).toHaveBeenCalledWith(detail.records);
    expect(onDone).toHaveBeenCalledWith("csv", expect.objectContaining({ count: 3 }));
  });

  it("T11-EP13 PRISMA click → async await onDone('prisma',{svgFilename,hasPng})", async () => {
    const onDone = vi.fn();
    const mockPrisma = vi.fn(async () => ({
      svgBlob: new Blob(["x"]),
      pngDataUrl: "data:image/png;base64,YYY",
    }));
    const detail = makeDetail();
    render(<ExportPanel detail={detail} onDone={onDone} exportPRISMA={mockPrisma} />);
    await act(async () => {
      fireEvent.click(screen.getByTestId("export-prisma-btn"));
    });
    expect(mockPrisma).toHaveBeenCalledTimes(1);
    expect(onDone).toHaveBeenCalledWith("prisma", expect.objectContaining({ svgFilename: expect.any(String), hasPng: true }));
  });

  it("T11-EP14 empty status completed → 按钮有 dashed border（export-panel-empty 样式 className）", () => {
    const detail = makeDetail({ records: [] });
    const { container } = render(<ExportPanel detail={detail} />);
    const panel = container.firstChild as HTMLElement;
    expect(panel.className).toContain("export-panel-empty");
  });
});

// ---------------------------------------------------------------------------
// Wave82B T11 PrismaOverrideEditor (8 vitest)
// ---------------------------------------------------------------------------
describe("Wave82B T11 PrismaOverrideEditor (8 vitest)", () => {
  function renderEditor(props: Partial<PrismaOverrideEditorT11Props> = {}) {
    const defaultProps: PrismaOverrideEditorT11Props = {
      open: true,
      initialStats: { identification: 100, screening: 90, eligibility: 70, included: 40 },
      onApply: vi.fn(),
      onClear: vi.fn(),
      onCancel: vi.fn(),
      ...props,
    };
    return { ...defaultProps, ...render(<PrismaOverrideEditorT11 {...defaultProps} />) };
  }

  it("T11-PR01 PrismaOverrideEditor dialog mount: data-testid=prisma-override-editor 存在", () => {
    renderEditor();
    expect(screen.getByTestId("prisma-override-editor")).toBeTruthy();
  });

  it("T11-PR02 Open dialog shows 4 number inputs + title 'Manual PRISMA Override'", () => {
    renderEditor();
    expect(screen.getByTestId("ov-identification")).toBeTruthy();
    expect(screen.getByTestId("ov-screening")).toBeTruthy();
    expect(screen.getByTestId("ov-eligibility")).toBeTruthy();
    expect(screen.getByTestId("ov-included")).toBeTruthy();
    const dialog = screen.getByTestId("prisma-override-editor");
    expect(dialog.textContent).toMatch(/Manual PRISMA Override/i);
  });

  it("T11-PR03 onCancel 点击关闭 → fn called", () => {
    const { onCancel } = renderEditor();
    fireEvent.click(screen.getByTestId("btn-override-cancel"));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("T11-PR04 ov-identification 输入 250 + apply → onApply 4 fields 全部传出（0 填缺失）", () => {
    const { onApply } = renderEditor({
      initialStats: { identification: undefined, screening: undefined, eligibility: undefined, included: undefined },
    });
    fireEvent.change(screen.getByTestId("ov-identification"), { target: { value: "250" } });
    fireEvent.click(screen.getByTestId("btn-override-apply"));
    expect(onApply).toHaveBeenCalledWith({
      identification: 250,
      screening: 0,
      eligibility: 0,
      included: 0,
    });
  });

  it("T11-PR05 Clear button click → onClear() 回调", () => {
    const { onClear } = renderEditor();
    fireEvent.click(screen.getByTestId("btn-override-clear"));
    expect(onClear).toHaveBeenCalledTimes(1);
  });

  it("T11-PR06 ov-eligibility > ov-included error hint → included <= eligibility 校验（按钮 disabled）", () => {
    renderEditor({
      initialStats: { identification: 100, screening: 90, eligibility: 50, included: 80 },
    });
    expect((screen.getByTestId("btn-override-apply") as HTMLButtonElement).disabled).toBe(true);
  });

  it("T11-PR07 badge 'Override Applied 30%' 当 diff_ratio 超过 0.2 时出现 data-testid=override-badge-30", () => {
    const { container } = renderEditor({
      initialStats: { identification: 100, screening: 90, eligibility: 70, included: 40 },
      diffRatio: 0.3,
    } as any);
    expect(screen.getByTestId("override-badge-30")).toBeTruthy();
    expect(screen.getByTestId("override-badge-30").textContent).toMatch(/30%/);
  });

  it("T11-PR08 4 number inputs default = 传入的 initialStats 字段值", () => {
    renderEditor({
      initialStats: { identification: 100, screening: 90, eligibility: 70, included: 40 },
    });
    expect((screen.getByTestId("ov-identification") as HTMLInputElement).value).toBe("100");
    expect((screen.getByTestId("ov-screening") as HTMLInputElement).value).toBe("90");
    expect((screen.getByTestId("ov-eligibility") as HTMLInputElement).value).toBe("70");
    expect((screen.getByTestId("ov-included") as HTMLInputElement).value).toBe("40");
  });
});
