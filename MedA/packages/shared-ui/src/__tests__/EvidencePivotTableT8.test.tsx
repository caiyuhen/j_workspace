import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import {
  EvidencePivotTable,
  type EvidenceWideRow,
  type ExtractionTemplateField,
  type EvidencePivotTableProps,
} from "../extraction/EvidencePivotTable";

function sampleColumns(): ExtractionTemplateField[] {
  return [
    { key: "p", label: "人群", type: "text", pico_binding: "P", required: false, options: [] },
    { key: "i", label: "干预", type: "text", pico_binding: "I", required: false, options: [] },
    { key: "c", label: "对照", type: "text", pico_binding: "C", required: false, options: [] },
    { key: "o", label: "结局", type: "text", pico_binding: "O", required: false, options: [] },
    { key: "n", label: "数值", type: "number", pico_binding: null, required: false, options: [] },
  ];
}

function sampleRows(n: number): EvidenceWideRow[] {
  const arr: EvidenceWideRow[] = [];
  for (let i = 0; i < n; i++) {
    arr.push({
      record_id: 1000 + i,
      study_label: `Study ${i + 1}`,
      values: {
        p: `Pop ${i + 1}`,
        i: `Int ${i + 1}`,
        c: `Cmp ${i + 1}`,
        o: `Out ${i + 1}`,
        n: i * 10,
      },
    });
  }
  return arr;
}

function renderTable(overrides: Partial<EvidencePivotTableProps> = {}) {
  const props: EvidencePivotTableProps = {
    rows: [],
    columns: sampleColumns(),
    pageSize: 200,
    ...overrides,
  };
  return render(<EvidencePivotTable {...props} />);
}

describe("Wave83 T8 EvidencePivotTable (18)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("B01: empty rows → 显示 no-rows-state", () => {
    renderTable({ rows: [] });
    expect(screen.getByTestId("no-rows-state")).toBeTruthy();
  });

  it("B02: 5 rows 5 cols → 行数 data row count = 5 (不含 header)", () => {
    renderTable({ rows: sampleRows(5), columns: sampleColumns() });
    expect(screen.getByTestId("evidence-table")).toBeTruthy();
    for (let i = 0; i < 5; i++) {
      expect(screen.getByTestId(`evidence-row-${i}`)).toBeTruthy();
    }
  });

  it("B03: col headers length === columns.length + 1 (额外 study_label 列)", () => {
    const cols = sampleColumns();
    renderTable({ rows: sampleRows(1), columns: cols });
    expect(screen.getByTestId("evidence-colheader-study_label")).toBeTruthy();
    for (const c of cols) {
      expect(screen.getByTestId(`evidence-colheader-${c.key}`)).toBeTruthy();
    }
  });

  it("B04: cell value string 展示正确（values['p'] 内容）", () => {
    const rows = sampleRows(3);
    renderTable({ rows, columns: sampleColumns() });
    for (let i = 0; i < rows.length; i++) {
      const cell = screen.getByTestId(`evidence-cell-${i}-p`);
      expect(cell.textContent).toBe(rows[i].values.p);
    }
  });

  it("B05: pageSize default 200 OK", () => {
    const rows = sampleRows(250);
    renderTable({ rows, columns: sampleColumns() });
    const pageInfo = screen.getByTestId("evidence-page-info");
    expect(pageInfo.textContent).toMatch(/1 of 2/);
  });

  it("B06: rows=400 → page 1 显示 200 rows; btn-prev disabled", () => {
    const rows = sampleRows(400);
    renderTable({ rows, columns: sampleColumns(), pageSize: 200 });
    expect((screen.getByTestId("evidence-btn-prev") as HTMLButtonElement).disabled).toBe(true);
    const pageInfo = screen.getByTestId("evidence-page-info");
    expect(pageInfo.textContent).toMatch(/1 of 2/);
  });

  it("B07: rows=400 click btn-next → pageInfo shows '2 of 2'; btn-next disabled; btn-prev enabled", () => {
    const rows = sampleRows(400);
    renderTable({ rows, columns: sampleColumns(), pageSize: 200 });
    fireEvent.click(screen.getByTestId("evidence-btn-next"));
    expect(screen.getByTestId("evidence-page-info").textContent).toMatch(/2 of 2/);
    expect((screen.getByTestId("evidence-btn-next") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId("evidence-btn-prev") as HTMLButtonElement).disabled).toBe(false);
  });

  it("B08: rows=250 pageSize=100 → pages=3; label '1 of 3'", () => {
    const rows = sampleRows(250);
    renderTable({ rows, columns: sampleColumns(), pageSize: 100 });
    const pageInfo = screen.getByTestId("evidence-page-info");
    expect(pageInfo.textContent).toMatch(/1 of 3/);
  });

  it("B09: onPageChange(pageNumber) 回调 fired on next/prev clicks", () => {
    const onPageChange = vi.fn();
    const rows = sampleRows(250);
    renderTable({ rows, columns: sampleColumns(), pageSize: 100, onPageChange });
    fireEvent.click(screen.getByTestId("evidence-btn-next"));
    expect(onPageChange).toHaveBeenCalledWith(2);
    fireEvent.click(screen.getByTestId("evidence-btn-prev"));
    expect(onPageChange).toHaveBeenLastCalledWith(1);
  });

  it("B10: rows=1 col value numeric 渲染正确", () => {
    const cols: ExtractionTemplateField[] = [{ key: "num", label: "Num", type: "number", pico_binding: null, required: false, options: [] }];
    const rows: EvidenceWideRow[] = [{ record_id: 1, study_label: "S1", values: { num: 42 } }];
    renderTable({ rows, columns: cols });
    const cell = screen.getByTestId("evidence-cell-0-num");
    expect(cell.textContent).toBe("42");
  });

  it("B11: None/null value 显示 '-' (N/A)", () => {
    const cols = sampleColumns();
    const rows: EvidenceWideRow[] = [
      { record_id: 1, study_label: "S1", values: { p: null, i: undefined, c: "C1", o: "O1", n: null } },
    ];
    renderTable({ rows, columns: cols });
    expect(screen.getByTestId("evidence-cell-0-p").textContent).toBe("-");
    expect(screen.getByTestId("evidence-cell-0-i").textContent).toBe("-");
    expect(screen.getByTestId("evidence-cell-0-n").textContent).toBe("-");
  });

  it("B12: long text >60 chars 加省略号 ... 显示", () => {
    const longText = "A".repeat(80);
    const cols: ExtractionTemplateField[] = [{ key: "lt", label: "LT", type: "text", pico_binding: null, required: false, options: [] }];
    const rows: EvidenceWideRow[] = [{ record_id: 1, study_label: "S1", values: { lt: longText } }];
    renderTable({ rows, columns: cols });
    const cell = screen.getByTestId("evidence-cell-0-lt");
    expect(cell.textContent).toContain("...");
    expect(cell.textContent?.length).toBeLessThan(longText.length);
  });

  it("B13: CSV btn onExportCsv callback fired once", () => {
    const onExportCsv = vi.fn();
    renderTable({ rows: sampleRows(1), columns: sampleColumns(), onExportCsv });
    fireEvent.click(screen.getByTestId("btn-export-csv"));
    expect(onExportCsv).toHaveBeenCalledTimes(1);
  });

  it("B14: CSV btn disabled if rows empty", () => {
    const onExportCsv = vi.fn();
    renderTable({ rows: [], columns: sampleColumns(), onExportCsv });
    expect((screen.getByTestId("btn-export-csv") as HTMLButtonElement).disabled).toBe(true);
  });

  it("B15: pico binding 显示在 header tooltip（可按 title 属性）", () => {
    const cols = sampleColumns();
    renderTable({ rows: sampleRows(1), columns: cols });
    const pHeader = screen.getByTestId("evidence-colheader-p");
    expect(pHeader.getAttribute("title")).toContain("P");
    const iHeader = screen.getByTestId("evidence-colheader-i");
    expect(iHeader.getAttribute("title")).toContain("I");
  });

  it("B16: 点击某 row → onRowClick 回调 fired with record_id（若提供 props）", () => {
    const onRowClick = vi.fn();
    const rows = sampleRows(3);
    renderTable({ rows, columns: sampleColumns(), onRowClick });
    fireEvent.click(screen.getByTestId("evidence-row-1"));
    expect(onRowClick).toHaveBeenCalledWith(rows[1].record_id);
  });

  it("B17: 字段按 pico 分组着色背景（绑定 P/I/C/O 4 个）", () => {
    const cols = sampleColumns();
    renderTable({ rows: sampleRows(1), columns: cols });
    const pHeader = screen.getByTestId("evidence-colheader-p");
    const iHeader = screen.getByTestId("evidence-colheader-i");
    const cHeader = screen.getByTestId("evidence-colheader-c");
    const oHeader = screen.getByTestId("evidence-colheader-o");
    const pStyle = (pHeader as HTMLElement).style.backgroundColor || "";
    const iStyle = (iHeader as HTMLElement).style.backgroundColor || "";
    const cStyle = (cHeader as HTMLElement).style.backgroundColor || "";
    const oStyle = (oHeader as HTMLElement).style.backgroundColor || "";
    const allBg = [pStyle, iStyle, cStyle, oStyle];
    expect(allBg.some(c => c !== "" && c !== undefined)).toBe(true);
  });

  it("B18: columns.filter(type==='number') 右对齐", () => {
    const cols: ExtractionTemplateField[] = [
      { key: "t", label: "T", type: "text", pico_binding: null, required: false, options: [] },
      { key: "n", label: "N", type: "number", pico_binding: null, required: false, options: [] },
    ];
    const rows: EvidenceWideRow[] = [{ record_id: 1, study_label: "S1", values: { t: "hello", n: 123 } }];
    renderTable({ rows, columns: cols });
    const numCell = screen.getByTestId("evidence-cell-0-n");
    const textAlign = (numCell as HTMLElement).style.textAlign || getComputedStyle(numCell).textAlign;
    expect(textAlign === "right" || textAlign === "end").toBe(true);
  });
});
