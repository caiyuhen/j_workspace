import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import React from "react";
import type { PipelineRunDetail } from "@meda/shared-sdk";
import type { InjectPipelineRunClient } from "../hooks/usePipelineRun";
import { PipelineRunDetailPage } from "../pages/PipelineRunDetailPage";

type MockInjectClient = {
  [K in keyof InjectPipelineRunClient]: ReturnType<typeof vi.fn>;
};

function makeMockInjectClient(): MockInjectClient {
  return {
    startRun: vi.fn(),
    cancelRun: vi.fn(),
    retryStep: vi.fn(),
    getDetail: vi.fn(),
    listRuns: vi.fn(),
  };
}

const EIGHT_STEP_NAMES = [
  "Step 0: Fetch",
  "Step 1: Dedupe",
  "Step 2: Title/Abstract",
  "Step 3: Fulltext",
  "Step 4: PICO Extract",
  "Step 5: RoB2 Assess",
  "Step 6: GRADE",
  "Step 7: Report",
];

function makeDetail(
  run_id: string,
  status: PipelineRunDetail["status"],
  overrides: Partial<PipelineRunDetail> = {},
): PipelineRunDetail {
  return {
    run_id,
    preset: "sglt2i_ckd",
    mode: "snapshot",
    max_records: 200,
    status,
    current_step_index: 7,
    duration_ms: 120000,
    created_at: "2026-08-20T12:00:00Z",
    cancel_flag: false,
    steps: EIGHT_STEP_NAMES.map((name, i) => ({
      step_index: i as any,
      step_name: name,
      status: status === "success" ? "success" : i < 3 ? "success" : (i === 3 ? (status === "failed" ? "failed" : "running") : "pending"),
      duration_ms: 15000 + i * 1000,
      n_in: i * 100,
      n_out: Math.max(0, i * 100 - 10),
      attempt_no: 1,
    })),
    pico_csv_url: undefined,
    grade_distribution: { H: 7, M: 28, L: 7 },
    rob2_distribution: { low: 15, some: 20, high: 7 },
    funnel_counts: [1000, 900, 800, 700, 60, 42],
    report_url: undefined,
    ...overrides,
  };
}

const flush = async (): Promise<void> => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
};

describe("PipelineRunDetailPage (22 tests)", () => {
  beforeEach(() => {
    vi.spyOn(window, "fetch").mockResolvedValue({} as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderPage = (
    mockClient: MockInjectClient,
    detail: PipelineRunDetail,
    overrides: Partial<React.ComponentProps<typeof PipelineRunDetailPage>> = {},
  ) => {
    mockClient.getDetail.mockImplementation(async () => detail);
    mockClient.cancelRun.mockImplementation(async () => undefined);
    mockClient.retryStep.mockImplementation(async () => detail);
    const onBack = vi.fn();
    const onNavigateToCompare = vi.fn();
    const utils = render(
      <PipelineRunDetailPage
        workspaceId="ws-1"
        runId={detail.run_id}
        onBack={onBack}
        onNavigateToCompare={onNavigateToCompare}
        injectFetchClient={mockClient}
        {...overrides}
      />,
    );
    return { ...utils, onBack, onNavigateToCompare };
  };

  // ---------- Structure tests (14) ----------

  it("1: [← Back] button exists; onClick fires onBack() handler", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-DETAIL-0001-abcdef", "success");
    const { onBack } = renderPage(mockClient, detail);
    await flush();
    const backBtn = screen.getByTestId("btn-back");
    expect(backBtn).toBeTruthy();
    fireEvent.click(backBtn);
    expect(onBack).toHaveBeenCalledTimes(1);
  });

  it("2: Header shows runId.slice(0,8) truncated correctly", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-ABCDEF01-extra-parts", "success");
    renderPage(mockClient, detail);
    await flush();
    const title = screen.getByTestId("header-title");
    const txt = title.textContent || "";
    const expectedSlice = "run-ABCDEF01".slice(0, 8);
    expect(txt.includes(expectedSlice)).toBe(true);
    expect(txt.includes("run-ABCD")).toBe(true);
  });

  it("3: status=success → green chip success class", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-SUCCESS-01", "success");
    renderPage(mockClient, detail);
    await flush();
    const chip = screen.getByTestId("status-chip");
    expect(chip.className.includes("status-success")).toBe(true);
    const style = window.getComputedStyle(chip);
    const bg = style.backgroundColor || "";
    const greenOk =
      bg.includes("209, 250, 229") ||
      bg.includes("d1fae5") ||
      chip.className.includes("status-success");
    expect(greenOk).toBe(true);
  });

  it("4: status=failed → red chip + show [RESUME #stepN] button", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-FAILED-01", "failed");
    detail.steps = detail.steps.map((s, i) => ({
      ...s,
      status: i < 3 ? "success" : i === 3 ? "failed" : "pending",
    }));
    renderPage(mockClient, detail);
    await flush();
    const chip = screen.getByTestId("status-chip");
    expect(chip.className.includes("status-failed")).toBe(true);
    const resumeBtn = screen.getByTestId("btn-resume");
    expect(resumeBtn).toBeTruthy();
    const resumeTxt = resumeBtn.textContent || "";
    expect(resumeTxt.includes("Resume")).toBe(true);
  });

  it("5: status=running → blue loading spinner + only [Cancel] button visible in actions", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-RUNNING-01", "running");
    renderPage(mockClient, detail);
    await flush();
    const spinner = screen.getByTestId("loading-spinner");
    expect(spinner).toBeTruthy();
    const chip = screen.getByTestId("status-chip");
    expect(chip.className.includes("status-running")).toBe(true);
    const cancelBtn = screen.getByTestId("btn-cancel");
    expect(cancelBtn).toBeTruthy();
    expect(screen.queryByTestId("btn-resume")).toBeNull();
    expect(screen.queryByTestId("btn-download-pdf")).toBeNull();
    expect(screen.queryByTestId("btn-download-csv")).toBeNull();
  });

  it("6: 8 STEP columns rendered (step names in 8 order)", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-8STEPS-01", "success");
    renderPage(mockClient, detail);
    await flush();
    for (let i = 0; i < 8; i++) {
      const col = screen.getByTestId(`step-column-${i}`);
      expect(col).toBeTruthy();
      const nameEl = screen.getByTestId(`step-name-${i}`);
      expect(nameEl).toBeTruthy();
    }
  });

  it("7: FunnelProgressBar rendered in section 3", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-FUNNEL-01", "success");
    renderPage(mockClient, detail);
    await flush();
    const section = screen.getByTestId("funnel-section");
    expect(section).toBeTruthy();
    const fpb = screen.getByTestId("funnel-progress-bar");
    expect(fpb).toBeTruthy();
  });

  it("8: AbstractorCard grid count 10 rendered (EA page=1)", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-EA-01", "success");
    detail.funnel_counts = [1000, 900, 800, 700, 200, 42];
    renderPage(mockClient, detail);
    await flush();
    let eaCardCount = 0;
    for (let i = 0; i < 50; i++) {
      const cardId = `EA-${String(i + 1).padStart(4, "0")}`;
      const el = screen.queryByTestId(`abstractor-card-${cardId}`);
      if (el) eaCardCount++;
    }
    expect(eaCardCount).toBe(10);
  });

  it("9: EA pagination next button clicks → page 2 loads next 10 rows", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-EA-PAGE-01", "success");
    detail.funnel_counts = [1000, 900, 800, 700, 200, 30];
    renderPage(mockClient, detail);
    await flush();
    const pageIndicatorBefore = screen.getByTestId("ea-page-indicator");
    expect(pageIndicatorBefore.textContent?.includes("1/3")).toBe(true);
    const firstPageCards: string[] = [];
    for (let i = 1; i <= 10; i++) {
      const cardId = `EA-${String(i).padStart(4, "0")}`;
      const el = screen.queryByTestId(`abstractor-card-${cardId}`);
      if (el) firstPageCards.push(cardId);
    }
    const nextBtn = screen.getByTestId("btn-ea-next");
    fireEvent.click(nextBtn);
    await flush();
    const pageIndicatorAfter = screen.getByTestId("ea-page-indicator");
    expect(pageIndicatorAfter.textContent?.includes("2/3")).toBe(true);
    for (const firstId of firstPageCards) {
      expect(screen.queryByTestId(`abstractor-card-${firstId}`)).toBeNull();
    }
    let foundSecondPage = false;
    for (let i = 11; i <= 20; i++) {
      const cardId = `EA-${String(i).padStart(4, "0")}`;
      const el = screen.queryByTestId(`abstractor-card-${cardId}`);
      if (el) {
        expect(el).toBeTruthy();
        foundSecondPage = true;
        break;
      }
    }
    expect(foundSecondPage).toBe(true);
  });

  it("10: RoB2Matrix rendered in section 5", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-ROB2-01", "success");
    renderPage(mockClient, detail);
    await flush();
    const wrapper = screen.getByTestId("rob2-matrix-wrapper");
    expect(wrapper).toBeTruthy();
  });

  it("11: GradeDistributionCard rendered in section 6 with correct prop distribution", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-GRADE-01", "success");
    detail.grade_distribution = { H: 10, M: 20, L: 5 };
    renderPage(mockClient, detail);
    await flush();
    const card = screen.getByTestId("grade-distribution-card");
    expect(card).toBeTruthy();
    const aria = card.getAttribute("aria-label") || "";
    expect(aria.includes("High 10")).toBe(true);
    expect(aria.includes("Moderate 20")).toBe(true);
    expect(aria.includes("Low 5")).toBe(true);
  });

  it("12: PICO CSV button disabled when pico_csv_url null", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-CSV-DIS-01", "success");
    detail.pico_csv_url = undefined;
    renderPage(mockClient, detail);
    await flush();
    const btn = screen.getByTestId("btn-download-pico-csv") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("13: PICO CSV button enabled when url present", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-CSV-ENA-01", "success");
    detail.pico_csv_url = "https://example.com/pico.csv";
    renderPage(mockClient, detail);
    await flush();
    const btn = screen.getByTestId("btn-download-pico-csv") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it("14: iframe shown when report_url present; src matches", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-REPORT-01", "success");
    detail.report_url = "https://example.com/report-123.pdf";
    renderPage(mockClient, detail);
    await flush();
    const iframe = screen.getByTestId("report-iframe") as HTMLIFrameElement;
    expect(iframe).toBeTruthy();
    expect(iframe.src).toBe("https://example.com/report-123.pdf");
  });

  // ---------- Interaction tests (8) ----------

  it("15: Click Cancel → calls cancelRun via usePipelineRun", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-CANCEL-01", "running");
    renderPage(mockClient, detail);
    await flush();
    const cancelBtn = screen.getByTestId("btn-cancel");
    fireEvent.click(cancelBtn);
    await flush();
    expect(mockClient.cancelRun).toHaveBeenCalledTimes(1);
    const cancelArgs = mockClient.cancelRun.mock.lastCall as any[];
    expect(cancelArgs[0]).toBe("run-CANCEL-01");
  });

  it("16: Click [RETRY STEP 3] (step3 failed) → calls retryStep(3)", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-RETRY-01", "failed");
    detail.steps = detail.steps.map((s, i) => ({
      ...s,
      status: i < 3 ? "success" : i === 3 ? "failed" : "pending",
    }));
    renderPage(mockClient, detail);
    await flush();
    const retryBtn = screen.getByTestId("btn-retry-step-3");
    expect(retryBtn).toBeTruthy();
    fireEvent.click(retryBtn);
    await flush();
    expect(mockClient.retryStep).toHaveBeenCalled();
    const calls = mockClient.retryStep.mock.calls;
    const hasStep3 = calls.some((c: any[]) => c[1] === 3);
    expect(hasStep3).toBe(true);
  });

  it("17: Click [RETRY STEP 3 force=true context menu] → retryStep(3, true)", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-RETRY-FORCE-01", "failed");
    detail.steps = detail.steps.map((s, i) => ({
      ...s,
      status: i < 3 ? "success" : i === 3 ? "failed" : "pending",
    }));
    renderPage(mockClient, detail);
    await flush();
    const retryBtn = screen.getByTestId("btn-retry-step-3");
    fireEvent.contextMenu(retryBtn);
    await flush();
    const calls = mockClient.retryStep.mock.calls;
    expect(calls.length).toBeGreaterThanOrEqual(1);
    const lastCall = calls[calls.length - 1] as any[];
    expect(lastCall[1]).toBe(3);
    const payload = lastCall[2];
    expect(payload && payload.force === true).toBe(true);
  });

  it("18: Click Compare → onNavigateToCompare(runId)", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-COMPARE-01", "success");
    const { onNavigateToCompare } = renderPage(mockClient, detail);
    await flush();
    const compareBtn = screen.getByTestId("btn-compare");
    fireEvent.click(compareBtn);
    expect(onNavigateToCompare).toHaveBeenCalledTimes(1);
    expect(onNavigateToCompare.mock.calls[0][0]).toBe("run-COMPARE-01");
  });

  it("19: Click Download PDF → a href click or window.open triggered", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-DL-PDF-01", "success");
    detail.report_url = "https://example.com/report.pdf";
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
    renderPage(mockClient, detail);
    await flush();
    const dlBtn = screen.getByTestId("btn-report-download-pdf");
    fireEvent.click(dlBtn);
    await flush();
    expect(openSpy).toHaveBeenCalledTimes(1);
    const [urlArg] = openSpy.mock.lastCall as any[];
    expect(urlArg).toBe("https://example.com/report.pdf");
    openSpy.mockRestore();
  });

  it("20: Click Download Markdown → similar", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-DL-MD-01", "success");
    detail.report_url = "https://example.com/report.pdf";
    const openSpy = vi.spyOn(window, "open").mockImplementation(() => null);
    renderPage(mockClient, detail);
    await flush();
    const mdBtn = screen.getByTestId("btn-report-download-md");
    fireEvent.click(mdBtn);
    await flush();
    expect(openSpy).toHaveBeenCalledTimes(1);
    const [urlArg] = openSpy.mock.lastCall as any[];
    expect(urlArg).toBe("https://example.com/report.md");
    openSpy.mockRestore();
  });

  it("21: window.fetch 0 times (inject pattern)", async () => {
    const fetchSpy = vi.spyOn(window, "fetch");
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("run-NOFETCH-01", "running");
    detail.pico_csv_url = "https://x.com/p.csv";
    detail.report_url = "https://x.com/r.pdf";
    const { onBack, onNavigateToCompare } = renderPage(mockClient, detail);
    await flush();
    fireEvent.click(screen.getByTestId("btn-cancel"));
    await flush();
    fireEvent.click(screen.getByTestId("btn-compare"));
    fireEvent.click(screen.getByTestId("btn-back"));
    await flush();
    expect(mockClient.cancelRun).toHaveBeenCalled();
    expect(mockClient.getDetail).toHaveBeenCalled();
    expect(onBack).toHaveBeenCalled();
    expect(onNavigateToCompare).toHaveBeenCalled();
    expect(fetchSpy).toHaveBeenCalledTimes(0);
    fetchSpy.mockRestore();
  });

  it("22: Polling stops when detail.status turns success (verify clearInterval mock)", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockInjectClient();
    const dRunning = makeDetail("run-STOP-POLL-01", "running");
    const dSuccess = makeDetail("run-STOP-POLL-01", "success");
    mockClient.getDetail
      .mockResolvedValueOnce(dRunning)
      .mockResolvedValueOnce(dSuccess);
    const clearIntervalSpy = vi.spyOn(globalThis, "clearInterval");
    renderPage(mockClient, dRunning);
    await act(async () => {
      vi.advanceTimersByTime(0);
      await flush();
    });
    await act(async () => {
      vi.advanceTimersByTime(2000);
      await flush();
    });
    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
    vi.useRealTimers();
  });
});
