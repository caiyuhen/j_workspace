import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { EvidenceArtifact, FunnelStepStat } from "@meda/shared-sdk";
import {
  useEvidenceArtifact,
  type InjectFetchClient,
} from "../hooks/useEvidenceArtifact";

type MockInjectClient = {
  [K in keyof InjectFetchClient]: ReturnType<typeof vi.fn>;
};

const makeMockInjectClient = (): MockInjectClient => ({
  list: vi.fn(),
  decide: vi.fn(),
  funnelStats: vi.fn(),
  robEval: vi.fn(),
  abstractorRun: vi.fn(),
  bulkDecide: vi.fn(),
  exportCSV: vi.fn(),
  undo: vi.fn(),
  resetAll: vi.fn(),
});

const makeEA = (id: string, literature_record_id: string): EvidenceArtifact => ({
  id,
  literature_record_id,
  stage: "screening_ta",
  decision: "include",
  created_at: "2026-08-19T00:00:00Z",
});

const makeFunnel = (): FunnelStepStat[] => [
  { key: "N1", label: "Identification", count: 100, locked: false },
  { key: "N2", label: "After dupe removal", count: 80, locked: false },
  { key: "E1", label: "Screening (TA)", count: 50, locked: false },
];

describe("T12 useEvidenceArtifact C1-C10 (injectable fetchClient)", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch" as never);
    (globalThis.fetch as unknown as ReturnType<typeof vi.fn>).mockClear?.();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("C1 list() → injectable fetchClient.list() called 1x", async () => {
    const mockClient = makeMockInjectClient();
    const threeItems: EvidenceArtifact[] = [
      makeEA("ea-1", "lit-1"),
      makeEA("ea-2", "lit-2"),
      makeEA("ea-3", "lit-3"),
    ];
    mockClient.list.mockResolvedValueOnce(threeItems);

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-1", injectFetchClient: mockClient }),
    );

    let out!: EvidenceArtifact[];
    await act(async () => {
      out = await result.current.list();
    });

    expect(mockClient.list).toHaveBeenCalledTimes(1);
    expect(out.length).toBe(3);
    expect(result.current.state.items.length).toBe(3);
    expect(result.current.state.items[0].id).toBe("ea-1");
  });

  it("C2 decide() → calls .decide(payload) + exact 传参", async () => {
    const mockClient = makeMockInjectClient();
    const decideResult = makeEA("ea-new-1", "1");
    mockClient.decide.mockResolvedValueOnce(decideResult);

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-1", injectFetchClient: mockClient }),
    );

    const payload = {
      literatureRecordId: "1",
      stage: "screening_ta" as const,
      decision: "include" as const,
    };

    let out!: EvidenceArtifact;
    await act(async () => {
      out = await result.current.decide(payload);
    });

    expect(mockClient.decide).toHaveBeenCalledTimes(1);
    const [callPayload] = mockClient.decide.mock.lastCall as [typeof payload];
    expect(callPayload.literatureRecordId).toBe("1");
    expect(callPayload.stage).toBe("screening_ta");
    expect(callPayload.decision).toBe("include");
    expect(out.id).toBe("ea-new-1");
    expect(result.current.state.items.length).toBe(1);
  });

  it("C3 bulkDecide 5 records → called with array len=5", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.bulkDecide.mockResolvedValueOnce({ ok: true, count: 5 });

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-1", injectFetchClient: mockClient }),
    );

    const fiveItems = Array.from({ length: 5 }, (_, i) => ({
      literatureRecordId: String(i + 1),
      stage: "screening_ta",
      decision: "include",
    }));

    let out!: unknown;
    await act(async () => {
      out = await result.current.bulkDecide(fiveItems);
    });

    expect(mockClient.bulkDecide).toHaveBeenCalledTimes(1);
    const [callArr] = mockClient.bulkDecide.mock.lastCall as [unknown[]];
    expect(Array.isArray(callArr)).toBe(true);
    expect(callArr.length).toBe(5);
    expect(out).toEqual({ ok: true, count: 5 });
  });

  it("C4 funnelStats → calls injectClient.funnelStats", async () => {
    const mockClient = makeMockInjectClient();
    const funnel = makeFunnel();
    mockClient.funnelStats.mockResolvedValueOnce(funnel);

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-42", injectFetchClient: mockClient }),
    );

    let out!: FunnelStepStat[];
    await act(async () => {
      out = await result.current.funnelStats();
    });

    expect(mockClient.funnelStats).toHaveBeenCalledTimes(1);
    const [piId] = mockClient.funnelStats.mock.lastCall as [string | number];
    expect(piId).toBe("pi-42");
    expect(out.length).toBe(3);
    expect(result.current.state.funnel.length).toBe(3);
    expect(result.current.state.funnel[0].key).toBe("N1");
    expect(result.current.state.funnel[0].count).toBe(100);
  });

  it("C5 rob2Evaluate → POST 正确 evaluate study_id", async () => {
    const mockClient = makeMockInjectClient();
    const robResult = {
      study_id: "study-123",
      overall: "some_concerns",
      domains: [],
    };
    mockClient.robEval.mockResolvedValueOnce(robResult);

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-1", injectFetchClient: mockClient }),
    );

    let out!: unknown;
    await act(async () => {
      out = await result.current.rob2Evaluate("study-123");
    });

    expect(mockClient.robEval).toHaveBeenCalledTimes(1);
    const [studyId] = mockClient.robEval.mock.lastCall as [string];
    expect(studyId).toBe("study-123");
    expect(out).toEqual(robResult);
  });

  it("C6 abstractorRunPipeline → called batch:10", async () => {
    const mockClient = makeMockInjectClient();
    const runResult = { status: "completed", extracted_fields: {} };
    mockClient.abstractorRun.mockResolvedValueOnce(runResult);

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-1", injectFetchClient: mockClient }),
    );

    let out!: unknown;
    await act(async () => {
      out = await result.current.abstractorRunPipeline();
    });

    expect(mockClient.abstractorRun).toHaveBeenCalledTimes(1);
    const [batchArg] = mockClient.abstractorRun.mock.lastCall as [unknown];
    expect(batchArg).toEqual({ batch: 10 });
    expect(out).toEqual(runResult);
  });

  it("C7 exportAsCSV → CSV 文本头 'record_id,stage,decision\n'", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.exportCSV.mockResolvedValueOnce([
      makeEA("ea-1", "rec-1"),
      makeEA("ea-2", "rec-2"),
    ]);

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-1", injectFetchClient: mockClient }),
    );

    let out!: string;
    await act(async () => {
      out = await result.current.exportAsCSV(["1", "2"]);
    });

    expect(mockClient.exportCSV).toHaveBeenCalledTimes(1);
    const [ids] = mockClient.exportCSV.mock.lastCall as [string[]];
    expect(ids).toEqual(["1", "2"]);
    expect(typeof out).toBe("string");
    expect(out.startsWith("record_id,stage,decision\n")).toBe(true);
    const lines = out.trim().split("\n");
    expect(lines.length).toBe(3);
    expect(lines[1]).toContain("rec-1");
    expect(lines[2]).toContain("rec-2");
  });

  it("C8 undo → restore prior decision (state prev)", async () => {
    const mockClient = makeMockInjectClient();
    const priorItems: EvidenceArtifact[] = [makeEA("ea-1", "lit-1")];

    mockClient.undo.mockResolvedValueOnce({ undone: true });

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-1", injectFetchClient: mockClient }),
    );

    await act(async () => {
      mockClient.list.mockResolvedValueOnce(priorItems);
      await result.current.list();
    });
    expect(result.current.state.items.length).toBe(1);

    await act(async () => {
      mockClient.decide.mockResolvedValueOnce(makeEA("ea-2", "lit-2"));
      await result.current.decide({
        literatureRecordId: "lit-2",
        stage: "screening_ta",
        decision: "exclude",
      });
    });
    expect(result.current.state.items.length).toBe(2);

    await act(async () => {
      await result.current.undo();
    });

    expect(mockClient.undo).toHaveBeenCalledTimes(1);
    const [snapshotArg] = mockClient.undo.mock.lastCall as [unknown];
    expect(Array.isArray(snapshotArg)).toBe(true);
    expect((snapshotArg as EvidenceArtifact[]).length).toBe(2);
    expect(result.current.state.items.length).toBe(1);
    expect(result.current.state.items[0].id).toBe("ea-1");
  });

  it("C9 reset → wipe all evidence", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.resetAll.mockResolvedValueOnce({ reset: true });

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-99", injectFetchClient: mockClient }),
    );

    await act(async () => {
      mockClient.list.mockResolvedValueOnce([
        makeEA("ea-1", "lit-1"),
        makeEA("ea-2", "lit-2"),
      ]);
      await result.current.list();
    });
    expect(result.current.state.items.length).toBe(2);

    await act(async () => {
      await result.current.reset();
    });

    expect(mockClient.resetAll).toHaveBeenCalledTimes(1);
    const [piId] = mockClient.resetAll.mock.lastCall as [string | number];
    expect(piId).toBe("pi-99");
    expect(result.current.state.items.length).toBe(0);
    expect(result.current.state.funnel.length).toBe(0);
  });

  it("C10 Injectable verify: window.fetch 0 次被调用 (所有请求 inject 拦截)", async () => {
    const mockClient = makeMockInjectClient();
    mockClient.list.mockResolvedValueOnce([makeEA("ea-1", "lit-1")]);
    mockClient.decide.mockResolvedValueOnce(makeEA("ea-2", "lit-2"));
    mockClient.funnelStats.mockResolvedValueOnce(makeFunnel());
    mockClient.robEval.mockResolvedValueOnce({});
    mockClient.abstractorRun.mockResolvedValueOnce({});
    mockClient.bulkDecide.mockResolvedValueOnce({});
    mockClient.exportCSV.mockResolvedValueOnce([]);
    mockClient.undo.mockResolvedValueOnce({});
    mockClient.resetAll.mockResolvedValueOnce({});

    const windowFetchSpy = vi.spyOn(window, "fetch");

    const { result } = renderHook(() =>
      useEvidenceArtifact({ literatureRecordId: "pi-all", injectFetchClient: mockClient }),
    );

    await act(async () => {
      await result.current.list();
      await result.current.decide({
        literatureRecordId: "2",
        stage: "screening_ta",
        decision: "include",
      });
      await result.current.funnelStats();
      await result.current.rob2Evaluate("s-1");
      await result.current.abstractorRunPipeline();
      await result.current.bulkDecide([{ a: 1 }, { b: 2 }]);
      await result.current.exportAsCSV(["1"]);
      await result.current.undo();
      await result.current.reset();
    });

    expect(mockClient.list).toHaveBeenCalledTimes(1);
    expect(mockClient.decide).toHaveBeenCalledTimes(1);
    expect(mockClient.funnelStats).toHaveBeenCalledTimes(1);
    expect(mockClient.robEval).toHaveBeenCalledTimes(1);
    expect(mockClient.abstractorRun).toHaveBeenCalledTimes(1);
    expect(mockClient.bulkDecide).toHaveBeenCalledTimes(1);
    expect(mockClient.exportCSV).toHaveBeenCalledTimes(1);
    expect(mockClient.undo).toHaveBeenCalledTimes(1);
    expect(mockClient.resetAll).toHaveBeenCalledTimes(1);

    expect(windowFetchSpy).toHaveBeenCalledTimes(0);
    windowFetchSpy.mockRestore();
  });
});
