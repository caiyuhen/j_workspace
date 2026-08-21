import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, waitFor, act } from "@testing-library/react";
import React from "react";
import type { PipelineRunSummary, PipelineRunStatus, PipelineMode } from "@meda/shared-sdk";
import type { InjectPipelineRunClient } from "../hooks/usePipelineRun";
import { PipelineRunsListPage } from "../pages/PipelineRunsListPage";

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

const PRESETS = [
  "sglt2i_ckd",
  "empagliflozin_hf",
  "glp1_weightloss",
  "liraglutide_nafld",
  "pkd_tolvaptan",
  "ckd_blood_pressure_control",
];

function makeSummary(
  i: number,
  overrides: Partial<PipelineRunSummary> = {},
): PipelineRunSummary {
  const hourOffset = 100 - i;
  const d = new Date(Date.UTC(2026, 7, 20, 12, 0, 0) + hourOffset * 3600 * 1000);
  return {
    run_id: `run-${String(i).padStart(4, "0")}`,
    preset: PRESETS[i % PRESETS.length],
    mode: i % 2 === 0 ? "snapshot" : "live",
    max_records: 150 + (i % 50),
    status: (["success", "running", "failed", "queued", "partial", "cancelled", "resumable"][i % 7] as PipelineRunStatus),
    current_step_index: (Math.min(7, i % 8) as 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7),
    duration_ms: overrides.duration_ms ?? (i % 3 === 0 ? null : (120 + i * 17) * 1000),
    created_at: overrides.created_at ?? d.toISOString(),
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

describe("PipelineRunsListPage W10 D3-2 (22 it)", () => {
  beforeEach(() => {
    vi.spyOn(window, "fetch" as never).mockResolvedValue({} as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderPage = (
    mockClient: MockInjectClient,
    runs: PipelineRunSummary[],
    overrides: Partial<React.ComponentProps<typeof PipelineRunsListPage>> = {},
  ) => {
    mockClient.listRuns.mockImplementation(async () => [...runs]);
    mockClient.startRun.mockImplementation(async () => ({ run_id: "run-new" }));
    mockClient.getDetail.mockImplementation(async () => ({} as any));
    const onNavigateToDetail = vi.fn();
    const onNavigateToCompare = vi.fn();
    const utils = render(
      <PipelineRunsListPage
        workspaceId="ws-1"
        injectFetchClient={mockClient}
        onNavigateToDetail={onNavigateToDetail}
        onNavigateToCompare={onNavigateToCompare}
        {...overrides}
      />,
    );
    return { ...utils, onNavigateToDetail, onNavigateToCompare };
  };

  it("1: 初始 loading → render loading spinner", async () => {
    const mockClient = makeMockInjectClient();
    let resolveList!: (r: PipelineRunSummary[]) => void;
    mockClient.listRuns.mockImplementation(
      () => new Promise((res) => { resolveList = res; }),
    );
    render(
      <PipelineRunsListPage
        workspaceId="ws-1"
        injectFetchClient={mockClient}
        onNavigateToDetail={vi.fn()}
        onNavigateToCompare={vi.fn()}
      />,
    );
    expect(screen.getByTestId("loading-spinner")).toBeTruthy();
    await act(async () => { resolveList([]); });
    await flush();
  });

  it("2: 0 runs → show Empty state text", async () => {
    const mockClient = makeMockInjectClient();
    renderPage(mockClient, []);
    await flush();
    const empty = screen.getByTestId("empty-state");
    expect(empty).toBeTruthy();
    const txt = empty.textContent || "";
    expect(txt.includes("暂无 Pipeline Run")).toBe(true);
    expect(txt.includes("启动新 Run")).toBe(true);
  });

  it("3: 20 runs → render 20 table rows", async () => {
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 20 }, (_, i) => makeSummary(i));
    renderPage(mockClient, runs);
    await flush();
    for (let i = 0; i < 20; i++) {
      expect(screen.getByTestId(`table-row-run-${String(i).padStart(4, "0")}`)).toBeTruthy();
    }
  });

  it("4: 20 runs, per_page=10 → only 10 rows render", async () => {
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 20 }, (_, i) => makeSummary(i));
    renderPage(mockClient, runs);
    await flush();
    fireEvent.change(screen.getByTestId("per-page-select"), { target: { value: "10" } });
    await flush();
    const first10 = Array.from({ length: 10 }, (_, i) => i);
    for (const i of first10) {
      expect(screen.getByTestId(`table-row-run-${String(i).padStart(4, "0")}`)).toBeTruthy();
    }
    for (let i = 10; i < 20; i++) {
      expect(screen.queryByTestId(`table-row-run-${String(i).padStart(4, "0")}`)).toBeNull();
    }
  });

  it("5: preset filter chip 点 sglt2i → listRuns called with preset param", async () => {
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 5 }, (_, i) => makeSummary(i));
    renderPage(mockClient, runs);
    await flush();
    const callsBefore = mockClient.listRuns.mock.calls.length;
    fireEvent.click(screen.getByTestId("preset-filter-sglt2i_ckd"));
    await flush();
    const callsAfter = mockClient.listRuns.mock.calls.length;
    expect(callsAfter).toBeGreaterThan(callsBefore);
    const lastParams = mockClient.listRuns.mock.lastCall?.[0] || {};
    expect(lastParams.preset).toBe("sglt2i_ckd");
  });

  it("6: status dropdown select \"success\" → listRuns called with status=\"success\"", async () => {
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 5 }, (_, i) => makeSummary(i));
    renderPage(mockClient, runs);
    await flush();
    fireEvent.change(screen.getByTestId("status-select"), { target: { value: "success" } });
    await flush();
    const lastParams = mockClient.listRuns.mock.lastCall?.[0] || {};
    expect(lastParams.status).toBe("success");
  });

  it("7: pagination page=2 → listRuns called with page=2", async () => {
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 50 }, (_, i) => makeSummary(i));
    renderPage(mockClient, runs);
    await flush();
    fireEvent.click(screen.getByTestId("btn-next-page"));
    await flush();
    const calls = mockClient.listRuns.mock.calls;
    const hasPage2 = calls.some((c) => (c[0] || {}).page === 2);
    expect(hasPage2).toBe(true);
    const indicator = screen.getByTestId("page-indicator");
    expect(indicator.textContent?.includes("2")).toBe(true);
  });

  it("8: [+ New Run] → NewRunModal open", async () => {
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 3 }, (_, i) => makeSummary(i));
    renderPage(mockClient, runs);
    await flush();
    expect(screen.queryByTestId("new-run-modal")).toBeNull();
    fireEvent.click(screen.getByTestId("btn-new-run"));
    expect(screen.getByTestId("new-run-modal")).toBeTruthy();
  });

  it("9: confirm NewRunModal → calls startRun() then reloads listRuns (1 extra call)", async () => {
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 3 }, (_, i) => makeSummary(i));
    renderPage(mockClient, runs);
    await flush();
    const beforeListCalls = mockClient.listRuns.mock.calls.length;
    fireEvent.click(screen.getByTestId("btn-new-run"));
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    fireEvent.click(screen.getByTestId("btn-confirm"));
    await flush();
    expect(mockClient.startRun).toHaveBeenCalledTimes(1);
    const afterListCalls = mockClient.listRuns.mock.calls.length;
    expect(afterListCalls).toBeGreaterThan(beforeListCalls);
  });

  it("10: [详情 →] → onNavigateToDetail called with correct run_id", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [makeSummary(5, { run_id: "run-DETAIL-01" })];
    const { onNavigateToDetail } = renderPage(mockClient, runs);
    await flush();
    fireEvent.click(screen.getByTestId("btn-detail-run-DETAIL-01"));
    expect(onNavigateToDetail).toHaveBeenCalledTimes(1);
    expect(onNavigateToDetail.mock.calls[0][0]).toBe("run-DETAIL-01");
  });

  it("11: success row → [⬇ CSV] button enabled", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [makeSummary(0, { status: "success", run_id: "run-CSV-OK" })];
    renderPage(mockClient, runs);
    await flush();
    const btn = screen.getByTestId("btn-csv-run-CSV-OK") as HTMLButtonElement;
    expect(btn.disabled).toBe(false);
  });

  it("12: failed row → [⬇ CSV] button disabled", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [makeSummary(2, { status: "failed", run_id: "run-CSV-FAIL" })];
    renderPage(mockClient, runs);
    await flush();
    const btn = screen.getByTestId("btn-csv-run-CSV-FAIL") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("13: cancelled row → [⬇ CSV] disabled", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [makeSummary(5, { status: "cancelled", run_id: "run-CSV-CANCEL" })];
    renderPage(mockClient, runs);
    await flush();
    const btn = screen.getByTestId("btn-csv-run-CSV-CANCEL") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
  });

  it("14: status color: success → green success badge class applied", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [makeSummary(0, { status: "success", run_id: "run-ST-SUCCESS" })];
    renderPage(mockClient, runs);
    await flush();
    const badge = screen.getByTestId("status-badge-run-ST-SUCCESS");
    expect(badge.className.includes("status-success")).toBe(true);
    const style = window.getComputedStyle(badge);
    const bg = style.backgroundColor || "";
    const color = style.color || "";
    const greenOk =
      bg.includes("d1fae5") || bg.includes("209, 250, 229") ||
      color.includes("065f46") || color.includes("6, 95, 70");
    expect(greenOk).toBe(true);
  });

  it("15: status color: failed → red badge", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [makeSummary(0, { status: "failed", run_id: "run-ST-FAILED" })];
    renderPage(mockClient, runs);
    await flush();
    const badge = screen.getByTestId("status-badge-run-ST-FAILED");
    expect(badge.className.includes("status-failed")).toBe(true);
    const style = window.getComputedStyle(badge);
    const bg = style.backgroundColor || "";
    const color = style.color || "";
    const redOk =
      bg.includes("fee2e2") || bg.includes("254, 226, 226") ||
      color.includes("991b1b") || color.includes("153, 27, 27");
    expect(redOk).toBe(true);
  });

  it("16: mode=snapshot → 🔵 blue badge; mode=live → 🟢 green live badge", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [
      makeSummary(0, { mode: "snapshot", run_id: "run-MODE-SNAP" }),
      makeSummary(1, { mode: "live", run_id: "run-MODE-LIVE" }),
    ];
    renderPage(mockClient, runs);
    await flush();
    const snapBadge = screen.getByTestId("mode-badge-snapshot-run-MODE-SNAP");
    const liveBadge = screen.getByTestId("mode-badge-live-run-MODE-LIVE");
    const snapStyle = window.getComputedStyle(snapBadge);
    const liveStyle = window.getComputedStyle(liveBadge);
    const snapBlue =
      snapStyle.backgroundColor.includes("dbeafe") ||
      snapStyle.backgroundColor.includes("219, 234, 254") ||
      snapStyle.color.includes("1e40af") ||
      (snapBadge.textContent || "").includes("🔵");
    const liveGreen =
      liveStyle.backgroundColor.includes("dcfce7") ||
      liveStyle.backgroundColor.includes("220, 252, 231") ||
      liveStyle.color.includes("166534") ||
      (liveBadge.textContent || "").includes("🟢");
    expect(snapBlue).toBe(true);
    expect(liveGreen).toBe(true);
  });

  it("17: 8 dots progress dots — 3 success / 1 running / 4 pending → dot colors match", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [makeSummary(0, { current_step_index: 3, status: "running", run_id: "run-DOTS-8" })];
    renderPage(mockClient, runs);
    await flush();
    for (let i = 0; i < 8; i++) {
      const dot = screen.getByTestId(`progress-dot-run-DOTS-8-${i}`) as HTMLSpanElement;
      const style = window.getComputedStyle(dot);
      const bg = style.backgroundColor || dot.style.backgroundColor || "";
      if (i < 3) {
        const successOk =
          bg.includes("10b981") || bg.includes("16, 185, 129") || bg.includes("#10b981");
        expect(successOk).toBe(true);
      } else if (i === 3) {
        const runningOk =
          bg.includes("3b82f6") || bg.includes("59, 130, 246") || bg.includes("#3b82f6");
        expect(runningOk).toBe(true);
      } else {
        const pendingOk =
          bg.includes("d1d5db") || bg.includes("209, 213, 219") || bg.includes("#d1d5db") ||
          bg === "rgba(0, 0, 0, 0)" || bg === "";
        expect(pendingOk || dot.style.border !== "").toBe(true);
      }
    }
  });

  it("18: duration display for finished_at - created_at format mm:ss", async () => {
    const mockClient = makeMockInjectClient();
    const created = "2026-08-20T10:00:00Z";
    const finished = "2026-08-20T10:02:30Z";
    const runs = [
      makeSummary(0, {
        run_id: "run-DUR",
        created_at: created,
        finished_at: finished,
        duration_ms: null,
      }),
    ];
    renderPage(mockClient, runs);
    await flush();
    const dur = screen.getByTestId("duration-run-DUR");
    const txt = dur.textContent || "";
    const mm = "02";
    const ss = "30";
    expect(txt.includes(`${mm}:${ss}`)).toBe(true);
  });

  it("19: [⟲ 重跑] → NewRunModal open with preset/max autofilled from source row", async () => {
    const mockClient = makeMockInjectClient();
    const runs = [
      makeSummary(0, {
        run_id: "run-RERUN",
        preset: "liraglutide_nafld",
        max_records: 188,
      }),
    ];
    renderPage(mockClient, runs);
    await flush();
    fireEvent.click(screen.getByTestId("btn-rerun-run-RERUN"));
    expect(screen.getByTestId("new-run-modal")).toBeTruthy();
    const inputMax = screen.getByTestId("input-max-records") as HTMLInputElement;
    expect(inputMax.value).toBe("188");
  });

  it("20: window.fetch 0 times (all fetch via inject client)", async () => {
    const fetchSpy = vi.spyOn(window, "fetch");
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 10 }, (_, i) => makeSummary(i));
    const { onNavigateToDetail } = renderPage(mockClient, runs);
    await flush();
    fireEvent.click(screen.getByTestId("preset-filter-sglt2i_ckd"));
    await flush();
    fireEvent.change(screen.getByTestId("status-select"), { target: { value: "success" } });
    await flush();
    fireEvent.click(screen.getByTestId("btn-detail-run-0000"));
    fireEvent.click(screen.getByTestId("btn-new-run"));
    fireEvent.click(screen.getByTestId("preset-chip-sglt2i_ckd"));
    fireEvent.click(screen.getByTestId("btn-confirm"));
    await flush();
    expect(mockClient.listRuns).toHaveBeenCalled();
    expect(fetchSpy).toHaveBeenCalledTimes(0);
    fetchSpy.mockRestore();
  });

  it("21: 50 runs, per_page=20 → 3 pages, page 2 shows rows 21-40", async () => {
    const mockClient = makeMockInjectClient();
    const runs = Array.from({ length: 50 }, (_, i) => makeSummary(i));
    renderPage(mockClient, runs);
    await flush();
    fireEvent.change(screen.getByTestId("per-page-select"), { target: { value: "20" } });
    await flush();
    expect(screen.getByTestId("page-indicator").textContent?.includes("1")).toBe(true);
    fireEvent.click(screen.getByTestId("btn-next-page"));
    await flush();
    expect(screen.getByTestId("page-indicator").textContent?.includes("2")).toBe(true);
    for (let i = 0; i < 20; i++) {
      expect(screen.queryByTestId(`table-row-run-${String(i).padStart(4, "0")}`)).toBeNull();
    }
    for (let i = 20; i < 40; i++) {
      expect(screen.getByTestId(`table-row-run-${String(i).padStart(4, "0")}`)).toBeTruthy();
    }
    for (let i = 40; i < 50; i++) {
      expect(screen.queryByTestId(`table-row-run-${String(i).padStart(4, "0")}`)).toBeNull();
    }
  });

  it("22: default sort order created_at DESC (newest first)", async () => {
    const mockClient = makeMockInjectClient();
    const rOld = makeSummary(999, { run_id: "run-OLD", created_at: "2026-08-01T00:00:00Z" });
    const rNew = makeSummary(1, { run_id: "run-NEW", created_at: "2026-08-30T00:00:00Z" });
    const rMid = makeSummary(500, { run_id: "run-MID", created_at: "2026-08-15T00:00:00Z" });
    const runs = [rOld, rMid, rNew];
    renderPage(mockClient, runs);
    await flush();
    const table = screen.getByTestId("runs-table");
    const rows = table.querySelectorAll('[data-testid^="table-row-"]');
    const first = rows[0]?.getAttribute("data-testid") || "";
    const last = rows[rows.length - 1]?.getAttribute("data-testid") || "";
    expect(first.includes("run-NEW")).toBe(true);
    expect(last.includes("run-OLD")).toBe(true);
  });
});
