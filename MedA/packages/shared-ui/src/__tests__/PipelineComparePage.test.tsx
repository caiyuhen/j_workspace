import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import React from "react";
import type { PipelineRunSummary, PipelineCompareResult } from "@meda/shared-sdk";
import type { InjectPipelineCompareClient } from "../hooks/usePipelineCompare";
import type { InjectPipelineRunClient } from "../hooks/usePipelineRun";
import { PipelineComparePage } from "../pages/PipelineComparePage";

type MockCompareClient = {
  [K in keyof InjectPipelineCompareClient]: ReturnType<typeof vi.fn>;
};

type MockRunClient = {
  [K in keyof InjectPipelineRunClient]: ReturnType<typeof vi.fn>;
};

type CombinedMockClient = MockCompareClient & MockRunClient;

function makeMockClient(): CombinedMockClient {
  return {
    compare: vi.fn(),
    startRun: vi.fn(),
    cancelRun: vi.fn(),
    retryStep: vi.fn(),
    getDetail: vi.fn(),
    listRuns: vi.fn(),
  };
}

const PRESETS = [
  "sglt2i_ckd",
  "empagliflozin_hf",
  "glp1_weightloss",
  "liraglutide_nafld",
];

function makeRunSummary(i: number, preset?: string): PipelineRunSummary {
  return {
    run_id: `run-${String(i).padStart(4, "0")}-abcd`,
    preset: preset ?? PRESETS[i % PRESETS.length],
    mode: i % 2 === 0 ? "snapshot" : "live",
    max_records: 150 + (i % 50),
    status: (["success", "running", "failed", "queued", "partial"][i % 5] as any),
    current_step_index: (Math.min(7, i % 8) as any),
    duration_ms: (120 + i * 17) * 1000,
    created_at: new Date(Date.UTC(2026, 7, 20 + i)).toISOString(),
  };
}

function makeCompareResult(
  funnelScenario: "AgtB" | "AltB" | "AeqB" = "AeqB",
  gradeScenario: "equal" | "mixed" = "mixed",
): PipelineCompareResult {
  const aBase = 200;
  const bBase = funnelScenario === "AgtB" ? 188 : funnelScenario === "AltB" ? 212 : 200;
  const delta = funnelScenario === "AgtB" ? 12 : funnelScenario === "AltB" ? -12 : 0;

  return {
    run_a_id: "run-A001-abcd",
    run_b_id: "run-B002-efgh",
    funnel_delta: [
      { step: "Identify", a_n: aBase + 800, b_n: bBase + 800, diff: delta },
      { step: "Dedup", a_n: aBase + 600, b_n: bBase + 600, diff: delta },
      { step: "TA-pass", a_n: aBase + 300, b_n: bBase + 300, diff: delta },
      { step: "FT-include", a_n: aBase + 100, b_n: bBase + 100, diff: delta },
      { step: "Abstractor-include", a_n: aBase + 42, b_n: bBase + 42, diff: delta },
      { step: "RoB2-assessed", a_n: aBase, b_n: bBase, diff: delta },
    ],
    rob2_delta: [
      { overall: "low", a: 60, b: 55 },
      { overall: "some", a: 90, b: 95 },
      { overall: "high", a: 50, b: 50 },
    ],
    grade_delta: gradeScenario === "equal"
      ? [
          { outcome: "All-cause mortality", a: "H", b: "H", reason: "Same grade; robust" },
          { outcome: "CV mortality", a: "H", b: "H", reason: "Same grade; robust" },
          { outcome: "HF hospitalization", a: "H", b: "H", reason: "Same grade; robust" },
          { outcome: "eGFR decline", a: "H", b: "H", reason: "Same grade; robust" },
        ]
      : [
          { outcome: "All-cause mortality", a: "H", b: "H", reason: "Same grade; robust" },
          { outcome: "CV mortality", a: "H", b: "M", reason: "A lower due to indirectness vs B" },
          { outcome: "HF hospitalization", a: "M", b: "L", reason: "A higher certainty; B downgraded RoB2 high" },
          { outcome: "eGFR decline", a: "H", b: "H", reason: "Same grade; robust" },
        ],
    pico: {
      only_in_a_nct_ids: ["NCT00000001", "NCT00000003"],
      only_in_b_nct_ids: ["NCT00000004"],
      both: ["NCT00000002", "NCT00000005", "NCT00000006"],
    },
  };
}

const flush = async (): Promise<void> => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
};

const renderPage = (
  mockClient: CombinedMockClient,
  runs: PipelineRunSummary[],
  result: PipelineCompareResult,
  overrides: Partial<React.ComponentProps<typeof PipelineComparePage>> = {},
) => {
  mockClient.listRuns.mockResolvedValue(runs);
  mockClient.compare.mockResolvedValue(result);
  mockClient.startRun.mockResolvedValue({ run_id: "x" });
  mockClient.getDetail.mockResolvedValue({} as any);
  mockClient.cancelRun.mockResolvedValue(undefined);
  mockClient.retryStep.mockResolvedValue({} as any);

  const onBack = vi.fn();
  const utils = render(
    <PipelineComparePage
      workspaceId="ws-1"
      injectFetchClient={mockClient}
      onBack={onBack}
      {...overrides}
    />,
  );
  return { ...utils, onBack };
};

describe("PipelineComparePage W10 D3-4 (22 it)", () => {
  beforeEach(() => {
    vi.spyOn(window, "fetch" as never).mockResolvedValue({} as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  // ============ Structure/UI (14) ============

  it("1: Back button exists + onBack handler click fires", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    const { onBack } = renderPage(mockClient, runs, result, {
      defaultRunAId: runs[0].run_id,
      defaultRunBId: runs[1].run_id,
    });
    await flush();
    const backBtn = screen.getByTestId("btn-back");
    expect(backBtn).toBeTruthy();
    fireEvent.click(backBtn);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("2: SYNC PRESET chip renders", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    const syncBtn = screen.getByTestId("btn-sync-preset");
    expect(syncBtn).toBeTruthy();
    expect(syncBtn.textContent).toMatch(/SYNC PRESET/);
  });

  it("3: Run A/B selector dropdowns rendered", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1), makeRunSummary(2)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    expect(screen.getByTestId("selector-run-a")).toBeTruthy();
    expect(screen.getByTestId("selector-run-b")).toBeTruthy();
  });

  it("4: Funnel diff table section header present", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    expect(screen.getByTestId("funnel-diff-header")).toBeTruthy();
  });

  it("5: Funnel diff 6 rows rendered (6 funnel steps rows)", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    for (let i = 0; i < 6; i++) {
      expect(screen.getByTestId(`funnel-diff-row-${i}`)).toBeTruthy();
    }
  });

  it("6: Funnel A > B scenario → Δ cell has class 'diff-positive green'", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult("AgtB");
    renderPage(mockClient, runs, result, {
      defaultRunAId: runs[0].run_id,
      defaultRunBId: runs[1].run_id,
    });
    await flush();
    const diffCell = screen.getByTestId("funnel-diff-cell-0");
    expect(diffCell.className).toContain("diff-positive");
    expect(diffCell.className).toContain("green");
    expect(diffCell.textContent).toContain("+12");
  });

  it("7: Funnel A < B scenario → Δ cell has class 'diff-negative red'", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult("AltB");
    renderPage(mockClient, runs, result, {
      defaultRunAId: runs[0].run_id,
      defaultRunBId: runs[1].run_id,
    });
    await flush();
    const diffCell = screen.getByTestId("funnel-diff-cell-0");
    expect(diffCell.className).toContain("diff-negative");
    expect(diffCell.className).toContain("red");
    expect(diffCell.textContent).toContain("-12");
  });

  it("8: Funnel A = B → Δ = 0 neutral gray", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult("AeqB");
    renderPage(mockClient, runs, result, {
      defaultRunAId: runs[0].run_id,
      defaultRunBId: runs[1].run_id,
    });
    await flush();
    const diffCell = screen.getByTestId("funnel-diff-cell-0");
    expect(diffCell.className).toContain("diff-neutral");
    expect(diffCell.textContent).toContain("0");
  });

  it("9: RoB2 histogram 2 side bars (Run A left + Run B right)", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    expect(screen.getByTestId("rob2-bar-run-a")).toBeTruthy();
    expect(screen.getByTestId("rob2-bar-run-b")).toBeTruthy();
  });

  it("10: RoB2 histogram Low/Some/High number labels present on each stacked bar segment", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    for (const side of ["a", "b"]) {
      for (const level of ["low", "some", "high"]) {
        const label = screen.getByTestId(`rob2-${side}-label-${level}`);
        expect(label).toBeTruthy();
        const num = Number(label.textContent?.trim());
        expect(Number.isFinite(num)).toBe(true);
        expect(num).toBeGreaterThanOrEqual(0);
      }
    }
  });

  it("11: GRADE comparison table rows for 4 outcomes (each row rendered)", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    for (let i = 0; i < 4; i++) {
      expect(screen.getByTestId(`grade-row-${i}`)).toBeTruthy();
    }
  });

  it("12: GRADE row A=H green TrafficLightCell, B=M amber TrafficLightCell (visual color match)", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    const cellA1 = screen.getByTestId("grade-a-cell-1");
    const cellB1 = screen.getByTestId("grade-b-cell-1");
    expect(cellA1.querySelector('[data-testid="tlc-low"]')).toBeTruthy();
    expect(cellB1.querySelector('[data-testid="tlc-some_concerns"]')).toBeTruthy();
  });

  it("13: PICO 3 tabs present (仅A / 仅B / 共有)", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    expect(screen.getByTestId("pico-tab-only-a")).toBeTruthy();
    expect(screen.getByTestId("pico-tab-only-b")).toBeTruthy();
    expect(screen.getByTestId("pico-tab-both")).toBeTruthy();
  });

  it("14: PICO 仅A tab clicked → only Run A's NCT cards shown", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result, {
      defaultRunAId: runs[0].run_id,
      defaultRunBId: runs[1].run_id,
    });
    await flush();
    fireEvent.click(screen.getByTestId("pico-tab-only-a"));
    await flush();
    for (const nctId of result.pico.only_in_a_nct_ids) {
      expect(screen.getByTestId(`nct-card-${nctId}`)).toBeTruthy();
    }
    for (const nctId of result.pico.only_in_b_nct_ids) {
      expect(screen.queryByTestId(`nct-card-${nctId}`)).toBeNull();
    }
  });

  // ============ Interaction/Integration (8) ============

  it("15: Select Run A from dropdown → compare() called with correct run_a_id parameter", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    mockClient.compare.mockClear();
    mockClient.compare.mockResolvedValue(result);
    renderPage(mockClient, runs, result, { defaultRunBId: runs[1].run_id });
    await flush();
    mockClient.compare.mockClear();
    fireEvent.change(screen.getByTestId("selector-run-a"), { target: { value: runs[0].run_id } });
    await flush();
    expect(mockClient.compare).toHaveBeenCalledTimes(1);
    const callArgs = mockClient.compare.mock.lastCall as [string, string, string];
    expect(callArgs[0]).toBe(runs[0].run_id);
    expect(callArgs[1]).toBe(runs[1].run_id);
  });

  it("16: Click SYNC PRESET → runs list filtered by same preset for both A/B selectors", async () => {
    const mockClient = makeMockClient();
    const runs = [
      makeRunSummary(0, "sglt2i_ckd"),
      makeRunSummary(1, "sglt2i_ckd"),
      makeRunSummary(2, "glp1_weightloss"),
    ];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    const selectorA = screen.getByTestId("selector-run-a") as HTMLSelectElement;
    const totalOptsBefore = selectorA.options.length;
    fireEvent.click(screen.getByTestId("btn-sync-preset"));
    await flush();
    const totalOptsAfter = selectorA.options.length;
    expect(totalOptsAfter).toBeLessThan(totalOptsBefore);
    expect(screen.getByTestId("btn-sync-preset").className).toContain("sync-preset-active");
  });

  it("17: Click [⬇ Export MD] → window.open md URL or download blob", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    const savedCreate = (globalThis as any).URL?.createObjectURL;
    const savedRevoke = (globalThis as any).URL?.revokeObjectURL;
    (globalThis as any).URL = (globalThis as any).URL || {};
    (globalThis as any).URL.createObjectURL = vi.fn(() => "blob:test-123");
    (globalThis as any).URL.revokeObjectURL = vi.fn(() => {});
    renderPage(mockClient, runs, result, {
      defaultRunAId: runs[0].run_id,
      defaultRunBId: runs[1].run_id,
    });
    await flush();
    const createElementSpy = vi.spyOn(document, "createElement");
    const appendChildSpy = vi.spyOn(document.body, "appendChild").mockImplementation((el: any) => el);
    const removeChildSpy = vi.spyOn(document.body, "removeChild").mockImplementation((el: any) => el);
    fireEvent.click(screen.getByTestId("btn-export-md"));
    await flush();
    expect((globalThis as any).URL.createObjectURL).toHaveBeenCalled();
    expect(createElementSpy).toHaveBeenCalledWith("a");
    appendChildSpy.mockRestore();
    removeChildSpy.mockRestore();
    createElementSpy.mockRestore();
    if (savedCreate) (globalThis as any).URL.createObjectURL = savedCreate;
    if (savedRevoke) (globalThis as any).URL.revokeObjectURL = savedRevoke;
  });

  it("18: NCT ID card link → opens new tab target='_blank'", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result, {
      defaultRunAId: runs[0].run_id,
      defaultRunBId: runs[1].run_id,
    });
    await flush();
    fireEvent.click(screen.getByTestId("pico-tab-only-a"));
    await flush();
    const firstNctId = result.pico.only_in_a_nct_ids[0];
    const link = screen.getByTestId(`nct-link-${firstNctId}`) as HTMLAnchorElement;
    expect(link).toBeTruthy();
    expect(link.target).toBe("_blank");
    expect(link.href).toMatch(/clinicaltrials\.gov/);
  });

  it("19: window.fetch 0 times (inject pattern only)", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    const windowFetchSpy = vi.spyOn(window, "fetch");
    mockClient.listRuns.mockResolvedValue(runs);
    mockClient.compare.mockResolvedValue(result);
    render(
      <PipelineComparePage
        workspaceId="ws-1"
        defaultRunAId={runs[0].run_id}
        defaultRunBId={runs[1].run_id}
        injectFetchClient={mockClient}
        onBack={vi.fn()}
      />,
    );
    await flush();
    fireEvent.change(screen.getByTestId("selector-run-a"), { target: { value: runs[0].run_id } });
    await flush();
    fireEvent.click(screen.getByTestId("pico-tab-both"));
    await flush();
    expect(windowFetchSpy).toHaveBeenCalledTimes(0);
    windowFetchSpy.mockRestore();
  });

  it("20: Default runA + runB via props → immediate compare call on mount", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    mockClient.compare.mockClear();
    mockClient.compare.mockResolvedValue(result);
    mockClient.listRuns.mockResolvedValue(runs);
    render(
      <PipelineComparePage
        workspaceId="ws-1"
        defaultRunAId={runs[0].run_id}
        defaultRunBId={runs[1].run_id}
        injectFetchClient={mockClient}
        onBack={vi.fn()}
      />,
    );
    await flush();
    const compareCalls = mockClient.compare.mock.calls;
    const wasCalled = compareCalls.some(
      (c) => (c as any)[0] === runs[0].run_id && (c as any)[1] === runs[1].run_id,
    );
    expect(wasCalled).toBe(true);
  });

  it("21: PICO 共有 tab clicked → 3rd tab active state class 'active'", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult();
    renderPage(mockClient, runs, result);
    await flush();
    const bothTab = screen.getByTestId("pico-tab-both");
    expect(bothTab.className).not.toContain("active");
    fireEvent.click(bothTab);
    await flush();
    expect(bothTab.className).toContain("active");
  });

  it("22: GRADE reason cell displays exact reason text 'Same grade; robust' when a=b matches compare result", async () => {
    const mockClient = makeMockClient();
    const runs = [makeRunSummary(0), makeRunSummary(1)];
    const result = makeCompareResult("AeqB", "equal");
    renderPage(mockClient, runs, result, {
      defaultRunAId: runs[0].run_id,
      defaultRunBId: runs[1].run_id,
    });
    await flush();
    const reason0 = screen.getByTestId("grade-reason-0");
    expect(reason0.textContent?.trim()).toBe("Same grade; robust");
    const reason3 = screen.getByTestId("grade-reason-3");
    expect(reason3.textContent?.trim()).toBe("Same grade; robust");
  });
});
