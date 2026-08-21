import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type {
  PipelineRunDetail,
  PipelineRunSummary,
} from "@meda/shared-sdk";
import {
  usePipelineRun,
  type InjectPipelineRunClient,
} from "../hooks/usePipelineRun";

type MockInjectClient = {
  [K in keyof InjectPipelineRunClient]: ReturnType<typeof vi.fn>;
};

const makeMockInjectClient = (): MockInjectClient => ({
  startRun: vi.fn(),
  cancelRun: vi.fn(),
  retryStep: vi.fn(),
  getDetail: vi.fn(),
  listRuns: vi.fn(),
});

const makeDetail = (
  run_id: string,
  status: PipelineRunDetail["status"],
): PipelineRunDetail => ({
  run_id,
  preset: "default",
  mode: "snapshot",
  max_records: 200,
  status,
  current_step_index: 0,
  duration_ms: null,
  created_at: "2026-08-20T00:00:00Z",
  cancel_flag: false,
  steps: [
    {
      step_index: 0,
      step_name: "Fetch",
      status: "running",
      duration_ms: null,
      n_in: 0,
      n_out: 0,
    },
  ],
});

const makeSummary = (run_id: string, preset: string): PipelineRunSummary => ({
  run_id,
  preset,
  mode: "snapshot",
  max_records: 200,
  status: "success",
  current_step_index: 7,
  duration_ms: 5000,
  created_at: "2026-08-20T00:00:00Z",
});

const flushMicrotasks = async (): Promise<void> => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

describe("usePipelineRun W10 D3-1 (16 it)", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch" as never);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("1: startRun → calls injected fetch with correct POST body; returns run_id", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.startRun.mockResolvedValueOnce({ run_id: "run-42" });
    mockClient.getDetail.mockResolvedValueOnce(makeDetail("run-42", "success"));

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let out!: { run_id: string };
    await act(async () => {
      out = await result.current.startRun("my-preset", "snapshot", 200);
    });

    expect(mockClient.startRun).toHaveBeenCalledTimes(1);
    const [payload] = mockClient.startRun.mock.lastCall as [{
      preset: string;
      mode: string;
      max_records: number;
    }];
    expect(payload.preset).toBe("my-preset");
    expect(payload.mode).toBe("snapshot");
    expect(payload.max_records).toBe(200);
    expect(out.run_id).toBe("run-42");
  });

  it("2: cancelRun → POST cancel endpoint", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.getDetail.mockResolvedValueOnce(makeDetail("run-42", "running"));
    mockClient.cancelRun.mockResolvedValueOnce(undefined);
    mockClient.getDetail.mockResolvedValueOnce(makeDetail("run-42", "cancelled"));

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-42", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await flushMicrotasks();
    });

    await act(async () => {
      await result.current.cancelRun();
    });

    expect(mockClient.cancelRun).toHaveBeenCalledTimes(1);
    const [rid] = mockClient.cancelRun.mock.lastCall as [string];
    expect(rid).toBe("run-42");
  });

  it("3: retryStep → POST with step_idx + force=false payload", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.getDetail.mockResolvedValueOnce(makeDetail("run-99", "paused"));
    const detailAfter = makeDetail("run-99", "running");
    mockClient.retryStep.mockResolvedValueOnce(detailAfter);

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-99", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await flushMicrotasks();
    });

    let ret!: PipelineRunDetail;
    await act(async () => {
      ret = await result.current.retryStep(3);
    });

    expect(mockClient.retryStep).toHaveBeenCalledTimes(1);
    const [rid, stepIdx, payload] = mockClient.retryStep.mock.lastCall as [
      string, number, { force?: boolean },
    ];
    expect(rid).toBe("run-99");
    expect(stepIdx).toBe(3);
    expect(payload.force).toBe(false);
    expect(ret.run_id).toBe("run-99");
  });

  it("4: retryStep force=true → adds force query param", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.getDetail.mockResolvedValueOnce(makeDetail("run-99", "paused"));
    mockClient.retryStep.mockResolvedValueOnce(makeDetail("run-99", "running"));

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-99", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await flushMicrotasks();
    });

    await act(async () => {
      await result.current.retryStep(3, true);
    });

    const [, , payload] = mockClient.retryStep.mock.lastCall as [
      string, number, { force?: boolean },
    ];
    expect(payload.force).toBe(true);
  });

  it("5: listRuns → GET with preset filter params", async () => {
    const mockClient = makeMockInjectClient();
    const three = [
      makeSummary("r1", "p1"),
      makeSummary("r2", "p2"),
      makeSummary("r3", "p1"),
    ];
    mockClient.listRuns.mockResolvedValueOnce(three);

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let out!: PipelineRunSummary[];
    await act(async () => {
      out = await result.current.listRuns({ preset: "p1", per_page: 10 });
    });

    expect(mockClient.listRuns).toHaveBeenCalledTimes(1);
    const [params] = mockClient.listRuns.mock.lastCall as [{
      preset?: string;
      per_page?: number;
    }];
    expect(params.preset).toBe("p1");
    expect(params.per_page).toBe(10);
    expect(out.length).toBe(3);
    expect(result.current.state.runs.length).toBe(3);
  });

  it("6: polling starts when status=running via setInterval mocked to verify trigger count", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockInjectClient();
    mockClient.getDetail.mockResolvedValue(makeDetail("run-poll", "running"));
    const setIntervalSpy = vi.spyOn(globalThis, "setInterval");

    renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-poll", intervalMs: 500, injectFetchClient: mockClient }),
    );

    await act(async () => {
      vi.advanceTimersByTime(0);
      await flushMicrotasks();
    });

    expect(setIntervalSpy).toHaveBeenCalledTimes(1);
    const [, msArg] = setIntervalSpy.mock.lastCall as [unknown, number];
    expect(msArg).toBe(500);

    const afterInitial = mockClient.getDetail.mock.calls.length;

    await act(async () => {
      vi.advanceTimersByTime(500);
      await flushMicrotasks();
    });

    const after1Tick = mockClient.getDetail.mock.calls.length;
    expect(after1Tick).toBe(afterInitial + 1);

    await act(async () => {
      vi.advanceTimersByTime(500);
      await flushMicrotasks();
    });

    const after2Ticks = mockClient.getDetail.mock.calls.length;
    expect(after2Ticks).toBe(afterInitial + 2);

    const pollCallCount = mockClient.getDetail.mock.calls.length;
    expect(pollCallCount).toBeGreaterThanOrEqual(3);

    setIntervalSpy.mockRestore();
    vi.useRealTimers();
  });

  it("7: polling STOPS when status turns success (terminal state) → setInterval cleared", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockInjectClient();
    mockClient.getDetail
      .mockResolvedValueOnce(makeDetail("run-stop", "running"))
      .mockResolvedValueOnce(makeDetail("run-stop", "success"));
    const clearIntervalSpy = vi.spyOn(globalThis, "clearInterval");

    renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-stop", intervalMs: 500, injectFetchClient: mockClient }),
    );

    await act(async () => {
      vi.advanceTimersByTime(0);
      await flushMicrotasks();
    });

    await act(async () => {
      vi.advanceTimersByTime(600);
      await flushMicrotasks();
    });

    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
    vi.useRealTimers();
  });

  it("8: polling stops on unmount (React strict cleanup verified)", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockInjectClient();
    mockClient.getDetail.mockResolvedValue(makeDetail("run-unmount", "running"));
    const clearIntervalSpy = vi.spyOn(globalThis, "clearInterval");

    const { unmount } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-unmount", intervalMs: 500, injectFetchClient: mockClient }),
    );

    await act(async () => {
      vi.advanceTimersByTime(0);
      await flushMicrotasks();
    });

    act(() => {
      unmount();
    });

    expect(clearIntervalSpy).toHaveBeenCalled();
    clearIntervalSpy.mockRestore();
    vi.useRealTimers();
  });

  it("9: refresh() → triggers immediate GET detail fetch", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.getDetail.mockResolvedValue(makeDetail("run-refresh", "queued"));

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-refresh", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await flushMicrotasks();
    });

    const before = mockClient.getDetail.mock.calls.length;
    await act(async () => {
      await result.current.refresh();
    });
    const after = mockClient.getDetail.mock.calls.length;

    expect(after).toBe(before + 1);
  });

  it("10: initial state when no runId → detail=undefined, runs=[], loading=false", () => {
    const mockClient = makeMockInjectClient();

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    expect(result.current.state.detail).toBeUndefined();
    expect(result.current.state.runs).toEqual([]);
    expect(result.current.state.loading).toBe(false);
    expect(result.current.state.pollActive).toBe(false);
  });

  it("11: detail.status=\"cancelled\" → no polling", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockInjectClient();
    mockClient.getDetail.mockResolvedValueOnce(makeDetail("run-cancel", "cancelled"));
    const setIntervalSpy = vi.spyOn(globalThis, "setInterval");

    renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-cancel", injectFetchClient: mockClient }),
    );

    await act(async () => {
      vi.advanceTimersByTime(2000);
      await flushMicrotasks();
    });

    expect(setIntervalSpy).not.toHaveBeenCalled();
    setIntervalSpy.mockRestore();
    vi.useRealTimers();
  });

  it("12: detail.status=\"failed\" → no polling", async () => {
    vi.useFakeTimers();
    const mockClient = makeMockInjectClient();
    mockClient.getDetail.mockResolvedValueOnce(makeDetail("run-fail", "failed"));
    const setIntervalSpy = vi.spyOn(globalThis, "setInterval");

    renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-fail", injectFetchClient: mockClient }),
    );

    await act(async () => {
      vi.advanceTimersByTime(2000);
      await flushMicrotasks();
    });

    expect(setIntervalSpy).not.toHaveBeenCalled();
    setIntervalSpy.mockRestore();
    vi.useRealTimers();
  });

  it("13: error fetching 404 run → populates error object", async () => {
    const mockClient = makeMockInjectClient();
    const notFoundErr = new Error("404 Not Found");
    mockClient.getDetail.mockRejectedValueOnce(notFoundErr);

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "run-404", injectFetchClient: mockClient }),
    );

    for (let i = 0; i < 10; i++) {
      await act(async () => {
        await flushMicrotasks();
      });
      if (result.current.state.error !== undefined) break;
    }

    expect(result.current.state.error).toBeDefined();
  });

  it("14: startRun invalid preset (400) → error populated", async () => {
    const mockClient = makeMockInjectClient();
    const badReqErr = new Error("400 Bad Request: invalid preset");
    mockClient.startRun.mockRejectedValueOnce(badReqErr);

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let threw = false;
    await act(async () => {
      try {
        await result.current.startRun("bad-preset");
      } catch {
        threw = true;
      }
    });

    await act(async () => {
      await flushMicrotasks();
    });

    expect(threw).toBe(true);
    expect(result.current.state.error).toBeDefined();
  });

  it("15: window.fetch NEVER called anywhere (zero direct window.fetch)", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.startRun.mockResolvedValueOnce({ run_id: "run-wf" });
    mockClient.getDetail.mockResolvedValue(makeDetail("run-wf", "success"));
    mockClient.cancelRun.mockResolvedValueOnce(undefined);
    mockClient.retryStep.mockResolvedValueOnce(makeDetail("run-wf", "success"));
    mockClient.listRuns.mockResolvedValueOnce([]);

    const windowFetchSpy = vi.spyOn(window, "fetch");

    const { result } = renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await result.current.startRun("p");
      await result.current.cancelRun();
      await result.current.retryStep(0);
      await result.current.refresh();
      await result.current.listRuns();
    });

    expect(mockClient.startRun).toHaveBeenCalledTimes(1);
    expect(mockClient.cancelRun).toHaveBeenCalledTimes(1);
    expect(mockClient.retryStep).toHaveBeenCalledTimes(1);
    expect(mockClient.listRuns).toHaveBeenCalledTimes(1);
    expect(windowFetchSpy).toHaveBeenCalledTimes(0);

    windowFetchSpy.mockRestore();
  });

  it("16: intervalMs default = 1500ms, custom interval works via prop", async () => {
    vi.useFakeTimers();

    const mockClient1 = makeMockInjectClient();
    mockClient1.getDetail.mockResolvedValueOnce(makeDetail("r1", "running"));
    const setIntervalSpy1 = vi.spyOn(globalThis, "setInterval");

    renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "r1", injectFetchClient: mockClient1 }),
    );

    await act(async () => {
      vi.advanceTimersByTime(0);
      await flushMicrotasks();
    });

    expect(setIntervalSpy1).toHaveBeenCalledTimes(1);
    const [, defaultMs] = setIntervalSpy1.mock.lastCall as [unknown, number];
    expect(defaultMs).toBe(1500);
    setIntervalSpy1.mockRestore();

    const mockClient2 = makeMockInjectClient();
    mockClient2.getDetail.mockResolvedValueOnce(makeDetail("r2", "running"));
    const setIntervalSpy2 = vi.spyOn(globalThis, "setInterval");

    renderHook(() =>
      usePipelineRun({ workspaceId: "ws-1", runId: "r2", intervalMs: 777, injectFetchClient: mockClient2 }),
    );

    await act(async () => {
      vi.advanceTimersByTime(0);
      await flushMicrotasks();
    });

    expect(setIntervalSpy2).toHaveBeenCalledTimes(1);
    const [, customMs] = setIntervalSpy2.mock.lastCall as [unknown, number];
    expect(customMs).toBe(777);
    setIntervalSpy2.mockRestore();

    vi.useRealTimers();
  });
});
