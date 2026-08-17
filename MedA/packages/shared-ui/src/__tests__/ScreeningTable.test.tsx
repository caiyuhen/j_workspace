import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import React from "react";
import {
  ScreeningTable,
  type ScreeningTableRow,
  SCREENING_TABLE_COL_WIDTHS,
} from "../screening/ScreeningTable";

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------
function makeRow(overrides: Partial<ScreeningTableRow> = {}): ScreeningTableRow {
  return {
    id: 1,
    title: "A Randomized Trial of Aspirin in Elderly Patients",
    authors: "Smith A, Jones B",
    journal: "N Engl J Med",
    year: 2022,
    doi: "10.1056/nejmoa2111111",
    pmid: "34999999",
    abstract:
      "Background: Low-dose aspirin reduces cardiovascular events but increases bleeding. We evaluated net benefit in elderly patients...",
    dedupe_status: "unique",
    duplicate_of_id: null,
    screening_stage: "ta",
    screening_decision: null,
    exclude_reason_json: null,
    screening_notes: null,
    ...overrides,
  };
}

const N = 500;
function make500Rows(): ScreeningTableRow[] {
  const rows: ScreeningTableRow[] = [];
  for (let i = 1; i <= N; i++) {
    rows.push(
      makeRow({
        id: i,
        title: `Trial Record #${String(i).padStart(3, "0")} - Effect of Drug X in Population Y`,
        year: 2020 + (i % 5),
      }),
    );
  }
  return rows;
}

// ---------------------------------------------------------------------------
// T8 tests (18)
// ---------------------------------------------------------------------------
describe("Wave82B T8 ScreeningTable", () => {
  // 1. renders 5 columns with correct widths
  it("T8-01: renders 5 column headers with exact configured widths", () => {
    render(<ScreeningTable rows={[makeRow()]} onSelectionChange={vi.fn()} />);
    const grid = screen.getByRole("grid");
    const style = window.getComputedStyle(grid);
    expect(style.display).toBe("grid");
    expect(style.gridTemplateColumns).toContain(`${SCREENING_TABLE_COL_WIDTHS.select}px`);
    expect(style.gridTemplateColumns).toContain("minmax(320px");
    expect(style.gridTemplateColumns).toContain("minmax(420px");
    expect(style.gridTemplateColumns).toContain(`${SCREENING_TABLE_COL_WIDTHS.dedupe}px`);
    expect(style.gridTemplateColumns).toContain(`${SCREENING_TABLE_COL_WIDTHS.decision}px`);
  });

  // 2. include/exclude visual class
  it("T8-02: include row has green left 4px border; exclude has red; duplicate has orange-red 4px border", () => {
    const rows = [
      makeRow({ id: 10, screening_decision: "include", dedupe_status: "unique" }),
      makeRow({ id: 20, screening_decision: "exclude", dedupe_status: "unique" }),
      makeRow({ id: 30, dedupe_status: "duplicate", duplicate_of_id: 10 }),
    ];
    render(<ScreeningTable rows={rows} onSelectionChange={vi.fn()} />);
    const r10 = screen.getByTestId("row-10");
    const r20 = screen.getByTestId("row-20");
    const r30 = screen.getByTestId("row-30");
    expect(r10.className).toMatch(/decision-include/);
    expect(r20.className).toMatch(/decision-exclude/);
    expect(r30.className).toMatch(/row-duplicate/);
  });

  // 3. checkbox per row
  it("T8-03: 3 rows → 3 row checkboxes + 1 select-all checkbox", () => {
    const rows = [makeRow({ id: 1 }), makeRow({ id: 2 }), makeRow({ id: 3 })];
    render(<ScreeningTable rows={rows} onSelectionChange={vi.fn()} />);
    const cbs = screen.getAllByRole("checkbox");
    expect(cbs).toHaveLength(4); // 1 all + 3 rows
  });

  // 4. checkbox selection fires callback
  it("T8-04: check row #5 → onSelectionChange receives Set{5}", () => {
    const cb = vi.fn();
    const rows = [makeRow({ id: 5 }), makeRow({ id: 6 })];
    render(<ScreeningTable rows={rows} onSelectionChange={cb} />);
    const cb5 = screen.getByTestId("selrow-5") as HTMLInputElement;
    fireEvent.click(cb5);
    expect(cb).toHaveBeenLastCalledWith(new Set([5]));
  });

  // 5. select all
  it("T8-05: click select-all → 3 rows all selected", () => {
    const cb = vi.fn();
    const rows = [makeRow({ id: 7 }), makeRow({ id: 8 }), makeRow({ id: 9 })];
    render(<ScreeningTable rows={rows} onSelectionChange={cb} />);
    const all = screen.getByTestId("select-all") as HTMLInputElement;
    fireEvent.click(all);
    const last = cb.mock.calls[cb.mock.calls.length - 1][0];
    expect(Array.from(last).sort()).toEqual([7, 8, 9]);
  });

  // 6. indeterminate state: 1/3 selected
  it("T8-06: 1/3 selected → select-all checkbox.indeterminate = true", () => {
    const rows = [makeRow({ id: 1 }), makeRow({ id: 2 }), makeRow({ id: 3 })];
    render(<ScreeningTable rows={rows} selection={new Set([1])} onSelectionChange={vi.fn()} />);
    const all = screen.getByTestId("select-all") as HTMLInputElement;
    expect(all.indeterminate).toBe(true);
  });

  // 7. all selected → select-all.checked=true
  it("T8-07: all 3 selected → select-all.checked = true; indeterminate = false", () => {
    const rows = [makeRow({ id: 1 }), makeRow({ id: 2 }), makeRow({ id: 3 })];
    render(<ScreeningTable rows={rows} selection={new Set([1, 2, 3])} onSelectionChange={vi.fn()} />);
    const all = screen.getByTestId("select-all") as HTMLInputElement;
    expect(all.checked).toBe(true);
    expect(all.indeterminate).toBe(false);
  });

  // 8. duplicate row → checkbox disabled (cant select dup for screening)
  it("T8-08: duplicate-of-id set → row checkbox disabled; has scroll-to-master button", () => {
    const rows = [makeRow({ id: 11, dedupe_status: "duplicate", duplicate_of_id: 55 })];
    render(<ScreeningTable rows={rows} onSelectionChange={vi.fn()} />);
    const rcb = screen.getByTestId("selrow-11") as HTMLInputElement;
    expect(rcb.disabled).toBe(true);
    expect(screen.getByTestId("scroll-to-master-11")).toBeTruthy();
  });

  // 9. scroll to master → calls scrollIntoView on master row element
  it("T8-09: click scroll-to-master → master row scrollIntoView() called once", () => {
    const scrollFn = vi.fn();
    const rows = [
      makeRow({ id: 100, title: "ORIGINAL" }),
      makeRow({ id: 200, dedupe_status: "duplicate", duplicate_of_id: 100 }),
    ];
    render(<ScreeningTable rows={rows} onSelectionChange={vi.fn()} />);
    const master = screen.getByTestId("row-100");
    (master as any).scrollIntoView = scrollFn;
    const btn = screen.getByTestId("scroll-to-master-200");
    fireEvent.click(btn);
    expect(scrollFn).toHaveBeenCalledTimes(1);
    expect(scrollFn).toHaveBeenCalledWith({ behavior: "smooth", block: "center" });
  });

  // 10. duplicate-of points to non-existent → no scrollIntoView called, show tooltip
  it("T8-10: master row not rendered (other page) → scroll btn shows 'Record on other page' title", () => {
    const rows = [makeRow({ id: 300, dedupe_status: "duplicate", duplicate_of_id: 999 })];
    render(<ScreeningTable rows={rows} onSelectionChange={vi.fn()} />);
    const btn = screen.getByTestId("scroll-to-master-300") as HTMLButtonElement;
    expect(btn.title).toMatch(/page|not present/);
  });

  // 11. abstract < 300 chars → no "展开" btn
  it("T8-11: short abstract (no truncation) → no toggle expand button", () => {
    const r = makeRow({ id: 1, abstract: "Short abstract." });
    render(<ScreeningTable rows={[r]} onSelectionChange={vi.fn()} />);
    expect(screen.queryAllByTestId("abs-expand-1")).toHaveLength(0);
  });

  // 12. abstract > 300 → truncate + expand btn
  it("T8-12: long abstract → truncated to 300 chars + shows toggle button", () => {
    const LONG = "A".repeat(450);
    const r = makeRow({ id: 1, abstract: LONG });
    render(<ScreeningTable rows={[r]} onSelectionChange={vi.fn()} />);
    const abs = screen.getByTestId("abstract-1").textContent!;
    expect(abs.length).toBeLessThan(LONG.length);
    expect(screen.getByTestId("abs-expand-1")).toBeTruthy();
  });

  // 13. click expand → full 450 chars + btn changes label "收起"
  it("T8-13: expand abstract → full 450 chars visible; btn label changes", () => {
    const LONG = "Z".repeat(450);
    const r = makeRow({ id: 2, abstract: LONG });
    render(<ScreeningTable rows={[r]} onSelectionChange={vi.fn()} />);
    const btn = screen.getByTestId("abs-expand-2") as HTMLButtonElement;
    fireEvent.click(btn);
    const abs = screen.getByTestId("abstract-2").textContent!;
    expect(abs).toBe(LONG);
    expect(btn.textContent).toMatch(/收起|collapse/i);
  });

  // 14. click collapse again → back to 300 chars
  it("T8-14: collapse after expand → back to ~300 chars", () => {
    const LONG = "Q".repeat(450);
    const r = makeRow({ id: 3, abstract: LONG });
    render(<ScreeningTable rows={[r]} onSelectionChange={vi.fn()} />);
    const btn = screen.getByTestId("abs-expand-3");
    fireEvent.click(btn);
    fireEvent.click(btn); // collapse
    const abs = screen.getByTestId("abstract-3").textContent!;
    expect(abs.length).toBeLessThan(LONG.length);
  });

  // 15. 500 rows → page 1 200 records
  it("T8-15: 500 rows default pagination → 1st page renders rows id 1..200 (no #201)", () => {
    render(<ScreeningTable rows={make500Rows()} onSelectionChange={vi.fn()} />);
    expect(screen.queryAllByTestId("row-1").length).toBe(1);
    expect(screen.queryAllByTestId("row-200").length).toBe(1);
    expect(screen.queryAllByTestId("row-201").length).toBe(0);
    expect(screen.queryAllByTestId("row-500").length).toBe(0);
  });

  // 16. 500 rows → pagination 3 页 (200 + 200 + 100)
  it("T8-16: 500 rows → pagination shows 3 pages (200 + 200 + 100)", () => {
    render(<ScreeningTable rows={make500Rows()} onSelectionChange={vi.fn()} />);
    const pages = screen.getAllByTestId(/^page-\d$/);
    expect(pages).toHaveLength(3);
  });

  // 17. click page 2 → shows rows 201-400
  it("T8-17: click page 2 → renders rows 201 and 400, no row 1", () => {
    render(<ScreeningTable rows={make500Rows()} onSelectionChange={vi.fn()} />);
    const page2 = screen.getByTestId("page-2");
    fireEvent.click(page2);
    expect(screen.queryAllByTestId("row-201").length).toBe(1);
    expect(screen.queryAllByTestId("row-400").length).toBe(1);
    expect(screen.queryAllByTestId("row-1").length).toBe(0);
    expect(screen.queryAllByTestId("row-401").length).toBe(0);
  });

  // 18. click page 3 → shows rows 401-500
  it("T8-18: click page 3 → renders rows 401 and 500 only", () => {
    render(<ScreeningTable rows={make500Rows()} onSelectionChange={vi.fn()} />);
    const page3 = screen.getByTestId("page-3");
    fireEvent.click(page3);
    expect(screen.queryAllByTestId("row-401").length).toBe(1);
    expect(screen.queryAllByTestId("row-500").length).toBe(1);
    expect(screen.queryAllByTestId("row-200").length).toBe(0);
    expect(screen.queryAllByTestId("row-501").length).toBe(0);
  });
});
