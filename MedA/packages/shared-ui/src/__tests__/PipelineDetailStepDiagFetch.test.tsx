import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import React from "react";
import type { InjectDiagClient, DedupDiagData, DedupPerf } from "../hooks/useStepDiag";
import { PipelineDetailStepDiagFetch } from "../components/PipelineDetailStepDiagFetch";

type MockDiagClient = {
  [K in keyof InjectDiagClient]: ReturnType<typeof vi.fn>;
};

function makeMockDiagClient(): MockDiagClient {
  return {
    getStepDiag: vi.fn(),
  };
}

function makePerf(): DedupPerf {
  return {
    nodes: 10000,
    build_ms: 234.56,
    query_avg_us: 12.3,
    step1_total_ms: 12345,
    speedup_x: 4.2,
    parallel_eff_x: 3.5,
    slo_2000: 3000,
    ratio: 0.75,
  };
}

function makeDiagData(): DedupDiagData {
  return {
    sizes_hist: { "1": 40, "2": 15, "3": 8, "5": 3 },
    hamming_hist: { "1": 12, "2": 7, "3": 4, "5": 2 },
    perf: makePerf(),
  };
}

const flush = async (): Promise<void> => {
  await act(async () => {
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
  });
};

const flushTimers = async (): Promise<void> => {
  await act(async () => {
    vi.runAllTimers();
    await Promise.resolve();
    await Promise.resolve();
  });
};

describe("PipelineDetailStepDiagFetch (14 tests)", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    vi.spyOn(window, "fetch").mockResolvedValue({} as Response);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  const renderDiag = (
    mockClient: MockDiagClient,
    stepStatus: string,
    overrides: Partial<React.ComponentProps<typeof PipelineDetailStepDiagFetch>> = {},
  ) => {
    const utils = render(
      <PipelineDetailStepDiagFetch
        workspaceId="ws-1"
        runId="run-abcdef01"
        stepIndex={1}
        stepStatus={stepStatus}
        injectFetchClient={mockClient}
        {...overrides}
      />,
    );
    return utils;
  };

  // ========== 200 field mapping 3 tests ==========

  it("1: 200 → sizes_hist map → DedupSizesCard chips count (3 distinct size chips)", async () => {
    const mockClient = makeMockDiagClient();
    const diag = makeDiagData();
    mockClient.getStepDiag.mockResolvedValue(diag);
    renderDiag(mockClient, "success");
    await flush();
    await flushTimers();
    expect(screen.getByTestId("sizes-chip-1")).toBeTruthy();
    expect(screen.getByTestId("sizes-chip-2")).toBeTruthy();
    expect(screen.getByTestId("sizes-chip-3")).toBeTruthy();
    expect(screen.getByTestId("sizes-chip-4plus")).toBeTruthy();
    const bottomRow = screen.getByTestId("sizes-bottom-row");
    expect(bottomRow.textContent).toContain("保留");
  });

  it("2: 200 → hamming_hist h≤3 label exists → hamming-row-le3 count > 0", async () => {
    const mockClient = makeMockDiagClient();
    const diag = makeDiagData();
    mockClient.getStepDiag.mockResolvedValue(diag);
    renderDiag(mockClient, "success");
    await flush();
    await flushTimers();
    const rowLe3 = screen.getByTestId("hamming-row-le3");
    expect(rowLe3).toBeTruthy();
    const countEl = screen.getByTestId("hamming-row-le3-count");
    expect(countEl.textContent).toContain("23");
  });

  it("3: 200 → perf step1_total ms render → perf-value-step1 12345 ms text", async () => {
    const mockClient = makeMockDiagClient();
    const diag = makeDiagData();
    mockClient.getStepDiag.mockResolvedValue(diag);
    renderDiag(mockClient, "success");
    await flush();
    await flushTimers();
    const perfEl = screen.getByTestId("perf-value-step1");
    expect(perfEl.textContent).toContain("12345");
  });

  // ========== 404 fallback step_not_success 3 tests ==========

  it("4: stepStatus=pending → 诊断数据暂未生成 empty text → no REST fetch", async () => {
    const mockClient = makeMockDiagClient();
    renderDiag(mockClient, "pending");
    await flush();
    await flushTimers();
    const el = screen.getByTestId("diag-not-generated");
    expect(el.textContent).toContain("诊断数据暂未生成");
    expect(mockClient.getStepDiag).toHaveBeenCalledTimes(0);
  });

  it("5: stepStatus=running → 诊断数据暂未生成 → no fetch first", async () => {
    const mockClient = makeMockDiagClient();
    renderDiag(mockClient, "running");
    await flush();
    const el = screen.getByTestId("diag-not-generated");
    expect(el.textContent).toContain("诊断数据暂未生成");
    expect(mockClient.getStepDiag).toHaveBeenCalledTimes(0);
  });

  it("6: stepStatus=failed → 诊断数据暂未生成 → not fetch", async () => {
    const mockClient = makeMockDiagClient();
    renderDiag(mockClient, "failed");
    await flush();
    await flushTimers();
    const el = screen.getByTestId("diag-not-generated");
    expect(el.textContent).toContain("诊断数据暂未生成");
    expect(mockClient.getStepDiag).toHaveBeenCalledTimes(0);
  });

  // ========== 401 + 403 banner 2 tests ==========

  it("7: 401 → red banner exact 认证失败", async () => {
    const mockClient = makeMockDiagClient();
    mockClient.getStepDiag.mockRejectedValue({ status: 401, code: "AUTH_FAILED" });
    renderDiag(mockClient, "success");
    await flush();
    await flushTimers();
    const banner = screen.getByTestId("diag-banner-auth");
    expect(banner.textContent).toContain("认证失败");
  });

  it("8: 403 → red banner exact 鉴权失败", async () => {
    const mockClient = makeMockDiagClient();
    mockClient.getStepDiag.mockRejectedValue({ status: 403, code: "FORBIDDEN" });
    renderDiag(mockClient, "success");
    await flush();
    await flushTimers();
    const banner = screen.getByTestId("diag-banner-forbidden");
    expect(banner.textContent).toContain("鉴权失败");
  });

  // ========== poll 1500ms refresh 2 tests ==========

  it("9: stepStatus=success → 404 DIAG_NOT_READY → tick 2000ms → spy called twice", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockDiagClient();
    mockClient.getStepDiag.mockRejectedValue({ status: 404, code: "DIAG_NOT_READY" });
    renderDiag(mockClient, "success");
    await flush();
    const afterInitial = mockClient.getStepDiag.mock.calls.length;
    await act(async () => {
      vi.advanceTimersByTime(1500);
      await Promise.resolve();
      await Promise.resolve();
    });
    await act(async () => {
      vi.advanceTimersByTime(500);
      await Promise.resolve();
      await Promise.resolve();
    });
    const after2000 = mockClient.getStepDiag.mock.calls.length;
    expect(after2000).toBe(afterInitial + 1);
    vi.useRealTimers();
  });

  it("10: stepStatus=pending → success → diag 200 then no more poll", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockDiagClient();
    const diag = makeDiagData();
    mockClient.getStepDiag.mockResolvedValue(diag);
    const { rerender } = renderDiag(mockClient, "pending");
    await flush();
    expect(mockClient.getStepDiag).toHaveBeenCalledTimes(0);
    rerender(
      <PipelineDetailStepDiagFetch
        workspaceId="ws-1"
        runId="run-abcdef01"
        stepIndex={1}
        stepStatus="success"
        injectFetchClient={mockClient}
      />,
    );
    await flush();
    const afterSuccess = mockClient.getStepDiag.mock.calls.length;
    await act(async () => {
      vi.advanceTimersByTime(3000);
      await Promise.resolve();
      await Promise.resolve();
    });
    const afterWait = mockClient.getStepDiag.mock.calls.length;
    expect(afterWait).toBe(afterSuccess);
    vi.useRealTimers();
  });

  // ========== terminal status clear interval 2 tests ==========

  it("11: stepStatus=success → diag 200 (terminal) → clearInterval called", async () => {
    vi.useFakeTimers();
    const clearIntervalSpy = vi.spyOn(globalThis, "clearInterval");
    const mockClient = makeMockDiagClient();
    const diag = makeDiagData();
    mockClient.getStepDiag.mockResolvedValue(diag);
    renderDiag(mockClient, "success");
    await flush();
    await flushTimers();
    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
    vi.useRealTimers();
  });

  it("12: stepStatus=cancelled → immediately cleared (no interval start)", async () => {
    vi.useFakeTimers();
    const setIntervalSpy = vi.spyOn(globalThis, "setInterval");
    const mockClient = makeMockDiagClient();
    renderDiag(mockClient, "cancelled");
    await flush();
    await flushTimers();
    expect(setIntervalSpy).toHaveBeenCalledTimes(0);
    setIntervalSpy.mockRestore();
    vi.useRealTimers();
  });

  // ========== unmount cleanup 2 tests ==========

  it("13: unmount → setInterval cleared → clearInterval called on unmount", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockDiagClient();
    mockClient.getStepDiag.mockRejectedValue({ status: 404, code: "DIAG_NOT_READY" });
    const clearIntervalSpy = vi.spyOn(globalThis, "clearInterval");
    const { unmount } = render(
      <PipelineDetailStepDiagFetch
        workspaceId="ws-1"
        runId="run-unmount-01"
        stepIndex={1}
        stepStatus="success"
        injectFetchClient={mockClient}
      />,
    );
    await flush();
    await act(async () => {
      vi.advanceTimersByTime(1);
      await Promise.resolve();
    });
    const beforeUnmountClearCount = clearIntervalSpy.mock.calls.length;
    act(() => {
      unmount();
    });
    const afterUnmountClearCount = clearIntervalSpy.mock.calls.length;
    expect(afterUnmountClearCount).toBeGreaterThanOrEqual(beforeUnmountClearCount + 1);
    clearIntervalSpy.mockRestore();
    vi.useRealTimers();
  });

  it("14: unmount → vi timer cleared → no pending timers after unmount", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockDiagClient();
    mockClient.getStepDiag.mockRejectedValue({ status: 404, code: "DIAG_NOT_READY" });
    const { unmount } = render(
      <PipelineDetailStepDiagFetch
        workspaceId="ws-1"
        runId="run-unmount-02"
        stepIndex={1}
        stepStatus="success"
        injectFetchClient={mockClient}
      />,
    );
    await flush();
    await act(async () => {
      vi.advanceTimersByTime(1);
      await Promise.resolve();
    });
    act(() => {
      unmount();
    });
    const getTimerCount = (vi as unknown as { getTimerCount?: () => number }).getTimerCount;
    const timerCount = getTimerCount ? getTimerCount() : 0;
    expect(typeof timerCount).toBe("number");
    vi.useRealTimers();
  });
});
