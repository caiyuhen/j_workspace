import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import React from "react";
import {
  ScreeningToolbar,
  ExcludeReasonDialog,
  ScreeningProgressHeader,
  COCHRANE_PRESET_REASONS_9,
  type ExcludeReasonDialogProps,
} from "../screening/ScreeningTrio";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function makeCountStats(overrides: Partial<any> = {}) {
  return Object.assign(
    {
      total_count: 100,
      unique_count: 90,
      duplicate_count: 10,
      prisma_identification: 100,
      prisma_screening: 100,
      prisma_eligibility: 80,
      prisma_included: 50,
      prisma_ta_excluded: 10,
      prisma_duplicate_excluded: 10,
      prisma_fulltext_excluded: 30,
      prisma_eligibility_unknown: 0,
    },
    overrides,
  );
}

const PRESET_LABEL = COCHRANE_PRESET_REASONS_9;

// ---------------------------------------------------------------------------
// T9 Part 1: ScreeningProgressHeader (6 tests)
// ---------------------------------------------------------------------------
describe("Wave82B T9 ScreeningProgressHeader (6)", () => {
  it("T9-H1: 6 progress bars render with correct labels (N1 N2 N3 N4 / excl_ta_dup / excl_fulltext)", () => {
    render(<ScreeningProgressHeader stats={makeCountStats()} />);
    expect(screen.getByTestId("bar-identification")).toBeTruthy();
    expect(screen.getByTestId("bar-screening")).toBeTruthy();
    expect(screen.getByTestId("bar-eligibility")).toBeTruthy();
    expect(screen.getByTestId("bar-included")).toBeTruthy();
    expect(screen.getByTestId("bar-excl-ta-dup")).toBeTruthy();
    expect(screen.getByTestId("bar-excl-fulltext")).toBeTruthy();
  });

  it("T9-H2: each bar label text = expected n / max", () => {
    const s = makeCountStats({ prisma_identification: 200, prisma_included: 120 });
    render(<ScreeningProgressHeader stats={s} />);
    expect(screen.getByTestId("bar-identification").textContent).toContain("200");
    expect(screen.getByTestId("bar-included").textContent).toContain("120");
  });

  it("T9-H3: prisma_override_applied = true → renders Manual Override badge red", () => {
    render(<ScreeningProgressHeader stats={makeCountStats()} overrideApplied={true} />);
    const badge = screen.getByTestId("override-badge");
    expect(badge.textContent).toMatch(/Manual|Override/i);
    expect(badge.className).toMatch(/override-on/);
  });

  it("T9-H4: overrideApplied=false → badge hidden or OFF text", () => {
    render(<ScreeningProgressHeader stats={makeCountStats()} overrideApplied={false} />);
    const b = screen.getByTestId("override-badge");
    expect(b.textContent).toMatch(/AUTO|off/i);
    expect(b.className).toMatch(/override-off/);
  });

  it("T9-H5: prisma_diff_percent > 30 → badge diff text red warning", () => {
    render(<ScreeningProgressHeader stats={makeCountStats({ prisma_diff_percent: 35 })} />);
    const d = screen.getByTestId("diff-percent");
    expect(d.className).toMatch(/diff-high/);
  });

  it("T9-H6: diff_percent < 10 → green", () => {
    render(<ScreeningProgressHeader stats={makeCountStats({ prisma_diff_percent: 5 })} />);
    const d = screen.getByTestId("diff-percent");
    expect(d.className).toMatch(/diff-low/);
  });
});

// ---------------------------------------------------------------------------
// T9 Part 2: ScreeningToolbar (14 tests)
// ---------------------------------------------------------------------------
describe("Wave82B T9 ScreeningToolbar (14)", () => {
  it("T9-Tb01: render batch include + batch exclude buttons + clear decision + filter dropdowns Run/Source/Year/Decision", () => {
    render(
      <ScreeningToolbar
        selectedCount={3}
        totalRows={100}
        duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()}
        onBatchExclude={vi.fn()}
        onBatchRevoke={vi.fn()}
        onFilterChange={vi.fn()}
        availableSources={[{ key: "pubmed", label: "PubMed" }]}
        availableYears={[2020, 2021, 2022]}
        availableRuns={[{ id: 1, label: "Run #1" }]}
      />,
    );
    expect(screen.getByTestId("btn-batch-include")).toBeTruthy();
    expect(screen.getByTestId("btn-batch-exclude")).toBeTruthy();
    expect(screen.getByTestId("btn-batch-revoke")).toBeTruthy();
    expect(screen.getByTestId("filter-run")).toBeTruthy();
    expect(screen.getByTestId("filter-source")).toBeTruthy();
    expect(screen.getByTestId("filter-year")).toBeTruthy();
    expect(screen.getByTestId("filter-decision")).toBeTruthy();
  });

  it("T9-Tb02: selectedCount=0 → 3 batch buttons disabled", () => {
    render(
      <ScreeningToolbar
        selectedCount={0} totalRows={100} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
      />,
    );
    expect((screen.getByTestId("btn-batch-include") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId("btn-batch-exclude") as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByTestId("btn-batch-revoke") as HTMLButtonElement).disabled).toBe(true);
  });

  it("T9-Tb03: selectedCount=5 → buttons enabled", () => {
    const fns = { onBatchInclude: vi.fn(), onBatchExclude: vi.fn(), onBatchRevoke: vi.fn() };
    render(
      <ScreeningToolbar
        selectedCount={5} totalRows={100} duplicateInSelectionCount={0}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
        {...fns}
      />,
    );
    expect((screen.getByTestId("btn-batch-include") as HTMLButtonElement).disabled).toBe(false);
    fireEvent.click(screen.getByTestId("btn-batch-include"));
    expect(fns.onBatchInclude).toHaveBeenCalledTimes(1);
  });

  it("T9-Tb04: duplicateInSelectionCount > 0 → render warning badge 'X duplicates will be skipped'", () => {
    render(
      <ScreeningToolbar
        selectedCount={7} totalRows={100} duplicateInSelectionCount={2}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
      />,
    );
    const warn = screen.getByTestId("dup-skip-warn");
    expect(warn.textContent).toContain("2");
    expect(warn.textContent).toMatch(/skip|duplicate/i);
  });

  it("T9-Tb05: exclude btn click → opens ExcludeReasonDialog onRequestOpen(true)", () => {
    const onOpen = vi.fn();
    render(
      <ScreeningToolbar
        selectedCount={5} totalRows={100} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={() => onOpen(true)} onBatchRevoke={vi.fn()}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-batch-exclude"));
    expect(onOpen).toHaveBeenCalledWith(true);
  });

  it("T9-Tb06: filter-run selected value change → onFilterChange({run})", () => {
    const fn = vi.fn();
    render(
      <ScreeningToolbar
        selectedCount={0} totalRows={0} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={fn}
        availableSources={[]} availableYears={[]}
        availableRuns={[{ id: 1, label: "Run 1" }, { id: 2, label: "Run 2" }]}
      />,
    );
    fireEvent.change(screen.getByTestId("filter-run"), { target: { value: "2" } });
    expect(fn).toHaveBeenLastCalledWith(expect.objectContaining({ run: "2" }));
  });

  it("T9-Tb07: filter-source change", () => {
    const fn = vi.fn();
    render(
      <ScreeningToolbar
        selectedCount={0} totalRows={0} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={fn}
        availableSources={[{ key: "pubmed", label: "PubMed" }, { key: "cnki", label: "CNKI" }]}
        availableYears={[]} availableRuns={[]}
      />,
    );
    fireEvent.change(screen.getByTestId("filter-source"), { target: { value: "cnki" } });
    expect(fn).toHaveBeenLastCalledWith(expect.objectContaining({ source: "cnki" }));
  });

  it("T9-Tb08: filter-year change", () => {
    const fn = vi.fn();
    render(
      <ScreeningToolbar
        selectedCount={0} totalRows={0} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={fn}
        availableSources={[]} availableYears={[2019, 2020, 2021]} availableRuns={[]}
      />,
    );
    fireEvent.change(screen.getByTestId("filter-year"), { target: { value: "2020" } });
    expect(fn).toHaveBeenLastCalledWith(expect.objectContaining({ year: "2020" }));
  });

  it("T9-Tb09: filter-decision change (all / include / exclude / undecided)", () => {
    const fn = vi.fn();
    render(
      <ScreeningToolbar
        selectedCount={0} totalRows={0} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={fn}
        availableSources={[]} availableYears={[]} availableRuns={[]}
      />,
    );
    fireEvent.change(screen.getByTestId("filter-decision"), { target: { value: "include" } });
    expect(fn).toHaveBeenLastCalledWith(expect.objectContaining({ decision: "include" }));
  });

  it("T9-Tb10: btn batch-revoke → calls onBatchRevoke", () => {
    const fn = vi.fn();
    render(
      <ScreeningToolbar
        selectedCount={3} totalRows={100} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={fn}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
      />,
    );
    fireEvent.click(screen.getByTestId("btn-batch-revoke"));
    expect(fn).toHaveBeenCalledTimes(1);
  });

  it("T9-Tb11: render title with selectedCount / totalRows", () => {
    render(
      <ScreeningToolbar
        selectedCount={5} totalRows={200} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
      />,
    );
    expect(screen.getByTestId("sel-counter").textContent).toContain("5");
    expect(screen.getByTestId("sel-counter").textContent).toContain("200");
  });

  it("T9-Tb12: stage='fulltext' → title says Fulltext Screening", () => {
    render(
      <ScreeningToolbar
        selectedCount={0} totalRows={0} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
        stage="fulltext"
      />,
    );
    expect(screen.getByTestId("stage-title").textContent).toMatch(/Fulltext|全文/i);
  });

  it("T9-Tb13: stage='ta' → Title/Abstract Screening", () => {
    render(
      <ScreeningToolbar
        selectedCount={0} totalRows={0} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
        stage="ta"
      />,
    );
    expect(screen.getByTestId("stage-title").textContent).toMatch(/Title|Abstract|标题|摘要/i);
  });

  it("T9-Tb14: stage undefined → General Screening (default)", () => {
    render(
      <ScreeningToolbar
        selectedCount={0} totalRows={0} duplicateInSelectionCount={0}
        onBatchInclude={vi.fn()} onBatchExclude={vi.fn()} onBatchRevoke={vi.fn()}
        onFilterChange={vi.fn()} availableSources={[]} availableYears={[]} availableRuns={[]}
      />,
    );
    expect(screen.getByTestId("stage-title").textContent).toMatch(/Screening/i);
  });
});

// ---------------------------------------------------------------------------
// T9 Part 3: ExcludeReasonDialog (10 tests)
// ---------------------------------------------------------------------------
describe("Wave82B T9 ExcludeReasonDialog (10)", () => {
  function renderDialog(partial: Partial<ExcludeReasonDialogProps> = {}) {
    return render(
      <ExcludeReasonDialog
        open={true}
        recordCount={3}
        stage="ta"
        initialPreset={null}
        initialNote=""
        onApply={vi.fn()}
        onClose={vi.fn()}
        {...partial}
      />,
    );
  }

  it("T9-D01: open=true → renders 9 radio buttons (preset 1 disabled)", () => {
    renderDialog();
    expect(screen.getByTestId("dlg-title")).toBeTruthy();
    for (let i = 1; i <= 9; i++) {
      expect(screen.getByTestId(`preset-${i}`)).toBeTruthy();
    }
    // preset 1 = "重复文献" → disabled (auto dedupe only)
    expect((screen.getByTestId(`preset-1`) as HTMLInputElement).disabled).toBe(true);
  });

  it("T9-D02: stage=ta → presets 2..9 enabled", () => {
    renderDialog({ stage: "ta" });
    for (let i = 2; i <= 9; i++) {
      const el = screen.getByTestId(`preset-${i}`) as HTMLInputElement;
      expect(el.disabled).toBe(false);
    }
  });

  it("T9-D03: stage=fulltext → presets 2..5 disabled, 6..9 enabled (T/A 错用直接 422 视觉 disabled)", () => {
    renderDialog({ stage: "fulltext" });
    for (let i = 2; i <= 5; i++) {
      const el = screen.getByTestId(`preset-${i}`) as HTMLInputElement;
      expect(el.disabled).toBe(true);
    }
    for (let i = 6; i <= 9; i++) {
      const el = screen.getByTestId(`preset-${i}`) as HTMLInputElement;
      expect(el.disabled).toBe(false);
    }
  });

  it("T9-D04: preset label text matches Cochrane 9 预置 (row textContent contains non-empty label chars)", () => {
    renderDialog();
    for (let i = 1; i <= 9; i++) {
      const row = screen.getByTestId(`preset-${i}-row`);
      const text = row.textContent || "";
      // text must contain "#{i} " prefix + some label chars
      expect(text.length).toBeGreaterThan(5);
      expect(text.includes(`#${i}`)).toBe(true);
    }
  });

  it("T9-D05: no preset chosen → Apply disabled", () => {
    renderDialog();
    expect((screen.getByTestId("btn-apply") as HTMLButtonElement).disabled).toBe(true);
  });

  it("T9-D06: preset=9 (其他) + note empty → Apply disabled (备注必填)", () => {
    renderDialog({ initialPreset: 9, initialNote: "" });
    expect((screen.getByTestId("btn-apply") as HTMLButtonElement).disabled).toBe(true);
  });

  it("T9-D07: preset=9 + note='xxx' → Apply enabled", () => {
    const onApply = vi.fn();
    renderDialog({ initialPreset: 9, initialNote: "xxx", onApply });
    fireEvent.click(screen.getByTestId("btn-apply"));
    expect(onApply).toHaveBeenLastCalledWith({
      preset_class: 9,
      note: "xxx",
    });
  });

  it("T9-D08: select preset 2 + click apply → onApply({preset:2, note:null})", () => {
    const onApply = vi.fn();
    renderDialog({ onApply });
    fireEvent.click(screen.getByTestId("preset-2"));
    fireEvent.click(screen.getByTestId("btn-apply"));
    expect(onApply).toHaveBeenLastCalledWith({ preset_class: 2, note: null });
  });

  it("T9-D09: cancel click → onClose()", () => {
    const onClose = vi.fn();
    renderDialog({ onClose });
    fireEvent.click(screen.getByTestId("btn-cancel"));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it("T9-D10: recordCount text in title = '批量排除 N 条文献'", () => {
    renderDialog({ recordCount: 42 });
    expect(screen.getByTestId("dlg-title").textContent).toContain("42");
  });
});
