import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { PipelineCompareResult } from "@meda/shared-sdk";
import {
  usePipelineCompare,
  type InjectPipelineCompareClient,
} from "../hooks/usePipelineCompare";

type MockInjectClient = {
  [K in keyof InjectPipelineCompareClient]: ReturnType<typeof vi.fn>;
};

const makeMockInjectClient = (): MockInjectClient => ({
  compare: vi.fn(),
});

const flushMicrotasks = async (): Promise<void> => {
  await Promise.resolve();
  await Promise.resolve();
  await Promise.resolve();
};

const makeCompareResult = (): PipelineCompareResult => ({
  run_a_id: "rA",
  run_b_id: "rB",
  funnel_delta: [
    { step: "N1 检索", a_n: 1000, b_n: 1200, diff: -200 },
    { step: "N2 去重", a_n: 800, b_n: 950, diff: -150 },
    { step: "E1 题目摘要", a_n: 500, b_n: 600, diff: -100 },
    { step: "E2 摘要筛选", a_n: 300, b_n: 350, diff: -50 },
    { step: "E3 全文筛选", a_n: 180, b_n: 200, diff: -20 },
    { step: "D1 ROB评价", a_n: 140, b_n: 150, diff: -10 },
    { step: "D2 数据提取", a_n: 100, b_n: 110, diff: -10 },
    { step: "D3 PICO提取", a_n: 80, b_n: 85, diff: -5 },
  ],
  rob2_delta: [
    { overall: "low", a: 40, b: 45 },
    { overall: "some", a: 35, b: 40 },
    { overall: "high", a: 25, b: 25 },
  ],
  grade_delta: [
    { outcome: "总病死率", a: "H", b: "M", reason: "样本量差异" },
  ],
  pico: {
    only_in_a_nct_ids: ["NCT00000001", "NCT00000003"],
    only_in_b_nct_ids: ["NCT00000004"],
    both: ["NCT00000002", "NCT00000005", "NCT00000006"],
  },
});

describe("usePipelineCompare W10 D3-1 (10 it)", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch" as never);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("1: compare(a,b) → calls /pipelines/compare/{a}/{b} with default 4 metrics", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.compare.mockResolvedValueOnce(makeCompareResult());

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await result.current.compare("rA", "rB");
    });

    expect(mockClient.compare).toHaveBeenCalledTimes(1);
    const [aId, bId, metrics] = mockClient.compare.mock.lastCall as [
      string, string, string,
    ];
    expect(aId).toBe("rA");
    expect(bId).toBe("rB");
    expect(metrics).toBe("funnel,rob,grade,pico");
  });

  it("2: compare with metrics=funnel → URL query param ?metrics=funnel", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.compare.mockResolvedValueOnce(makeCompareResult());

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await result.current.compare("rX", "rY", "funnel");
    });

    const [, , metrics] = mockClient.compare.mock.lastCall as [
      string, string, string,
    ];
    expect(metrics).toBe("funnel");
  });

  it("3: metrics CSV with spaces trimmed", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.compare.mockResolvedValueOnce(makeCompareResult());

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await result.current.compare("r1", "r2", " funnel , rob , grade ");
    });

    const [, , metrics] = mockClient.compare.mock.lastCall as [
      string, string, string,
    ];
    expect(metrics).toBe("funnel,rob,grade");
  });

  it("4: 404 run_a → error populated", async () => {
    const mockClient = makeMockInjectClient();
    const notFoundA = new Error("404 Not Found: run_a");
    mockClient.compare.mockRejectedValueOnce(notFoundA);

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let threw = false;
    await act(async () => {
      try {
        await result.current.compare("missing-a", "exists-b");
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

  it("5: 404 run_b → error populated", async () => {
    const mockClient = makeMockInjectClient();
    const notFoundB = new Error("404 Not Found: run_b");
    mockClient.compare.mockRejectedValueOnce(notFoundB);

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let threw = false;
    await act(async () => {
      try {
        await result.current.compare("exists-a", "missing-b");
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

  it("6: unauthenticated 401 → error populated", async () => {
    const mockClient = makeMockInjectClient();
    const unauthErr = new Error("401 Unauthorized");
    mockClient.compare.mockRejectedValueOnce(unauthErr);

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let threw = false;
    await act(async () => {
      try {
        await result.current.compare("a", "b");
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

  it("7: result funnel_delta parsed correctly as array of 8 dicts", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.compare.mockResolvedValueOnce(makeCompareResult());

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let ret!: PipelineCompareResult;
    await act(async () => {
      ret = await result.current.compare("rA", "rB");
    });

    expect(Array.isArray(ret.funnel_delta)).toBe(true);
    expect(ret.funnel_delta.length).toBe(8);
    expect(ret.funnel_delta[0]).toHaveProperty("step");
    expect(ret.funnel_delta[0]).toHaveProperty("a_n");
    expect(ret.funnel_delta[0]).toHaveProperty("b_n");
    expect(ret.funnel_delta[0]).toHaveProperty("diff");
    expect(ret.funnel_delta[7].step).toBe("D3 PICO提取");
  });

  it("8: result rob2_delta 3 rows (low/some/high) shape", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.compare.mockResolvedValueOnce(makeCompareResult());

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let ret!: PipelineCompareResult;
    await act(async () => {
      ret = await result.current.compare("rA", "rB");
    });

    expect(Array.isArray(ret.rob2_delta)).toBe(true);
    expect(ret.rob2_delta.length).toBe(3);
    const overalls = ret.rob2_delta.map((r) => r.overall).sort();
    expect(overalls).toEqual(["high", "low", "some"]);
    expect(ret.rob2_delta[0]).toHaveProperty("a");
    expect(ret.rob2_delta[0]).toHaveProperty("b");
  });

  it("9: pico.both is list and sorted ascending (NCT numbers order)", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.compare.mockResolvedValueOnce(makeCompareResult());

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    let ret!: PipelineCompareResult;
    await act(async () => {
      ret = await result.current.compare("rA", "rB");
    });

    expect(Array.isArray(ret.pico.both)).toBe(true);
    const sorted = [...ret.pico.both].sort((a, b) => a.localeCompare(b));
    expect(ret.pico.both).toEqual(sorted);
    expect(ret.pico.both.every((x) => x.startsWith("NCT"))).toBe(true);
  });

  it("10: window.fetch 0 times (inject pattern only)", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.compare.mockResolvedValue(makeCompareResult());

    const windowFetchSpy = vi.spyOn(window, "fetch");

    const { result } = renderHook(() =>
      usePipelineCompare({ workspaceId: "ws-1", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await result.current.compare("r1", "r2");
      await result.current.compare("r3", "r4", "funnel");
      await result.current.compare("r5", "r6", "pico,grade");
    });

    expect(mockClient.compare).toHaveBeenCalledTimes(3);
    expect(windowFetchSpy).toHaveBeenCalledTimes(0);

    windowFetchSpy.mockRestore();
  });
});
