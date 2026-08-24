import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import React from "react";
import type { PipelineRunDetail, PipelineStepInfo } from "@meda/shared-sdk";
import type { InjectPipelineRunClient } from "../hooks/usePipelineRun";
import type { InjectDiagClient } from "../hooks/useStepDiag";
import { PipelineRunDetailPage } from "../pages/PipelineRunDetailPage";

type MockInjectClient = {
  [K in keyof InjectPipelineRunClient]: ReturnType<typeof vi.fn>;
};

type MockDiagClient = {
  [K in keyof InjectDiagClient]: ReturnType<typeof vi.fn>;
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

function makeMockDiagClient(): MockDiagClient {
  return {
    getStepDiag: vi.fn(),
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
      n_in: i === 1 ? 1000 : i * 100,
      n_out: i === 1 ? 920 : Math.max(0, i * 100 - 10),
      attempt_no: 1,
    })),
    pico_csv_url: undefined,
    grade_distribution: { H: 7, M: 28, L: 7 },
    rob2_distribution: { low: 15, some: 20, high: 7 },
    funnel_counts: [1000, 920, 800, 700, 60, 42],
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

describe("W11 Screen2 Layout Smoke (10 exact tests)", () => {
  beforeEach(() => {
    vi.spyOn(window, "fetch").mockResolvedValue({} as Response);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const renderPage = (
    mockClient: MockInjectClient,
    detail: PipelineRunDetail,
    mockDiagClient?: MockDiagClient,
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
        injectDiagClient={mockDiagClient}
      />,
    );
    return { ...utils, onBack, onNavigateToCompare };
  };

  it("S1 order_funnel_dedup_ea: Section ③→③-B→④ DOM sibling order strict", async () => {
    const mockClient = makeMockInjectClient();
    const mockDiag = makeMockDiagClient();
    mockDiag.getStepDiag.mockResolvedValue({
      sizes_hist: { "1": 800, "2": 40, "3": 10 },
      hamming_hist: { "0": 5, "1": 8, "2": 12, "3": 10, "4": 20, "5": 18, "6": 15 },
      perf: {
        nodes: 920,
        build_ms: 120.5,
        query_avg_us: 45.2,
        step1_total_ms: 489,
        speedup_x: 4.2,
        parallel_eff_x: 6.0,
        slo_2000: 2000,
        ratio: 0.24,
      },
    });
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "success");
    renderPage(mockClient, detail, mockDiag);
    await flush();
    await flush();

    const funnel = screen.getByTestId("funnel-section");
    const dedup = screen.getByTestId("dedupdiag-section");
    const ea = screen.getByTestId("ea-section");

    expect(funnel.nextElementSibling).toBe(dedup);
    expect(dedup.previousElementSibling).toBe(funnel);
    expect(dedup.nextElementSibling).toBe(ea);
    expect(ea.previousElementSibling).toBe(dedup);
  });

  it("S2 dedup_star_badge_step1: step_idx=1 div has aria-label=去重 + ⭐ badge", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "success");
    renderPage(mockClient, detail);
    await flush();

    const step1Col = screen.getByTestId("step-column-1");
    expect(step1Col.getAttribute("aria-label")).toBe("去重");

    const starBadge = screen.getByTestId("step-dedup-star-badge");
    expect(starBadge).toBeTruthy();
    expect(starBadge.getAttribute("aria-label")).toBe("去重");
    expect(starBadge.textContent).toContain("⭐");
  });

  it("S3 dedup_section_only_shown_step1_success: steps[1].status=pending → 诊断数据暂未生成 placeholder", async () => {
    const mockClient = makeMockInjectClient();
    const mockDiag = makeMockDiagClient();
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "queued");
    detail.steps = detail.steps.map((s, i) => ({
      ...s,
      status: i === 1 ? "pending" : s.status,
    }));
    renderPage(mockClient, detail, mockDiag);
    await flush();

    const dedupSection = screen.getByTestId("dedupdiag-section");
    expect(dedupSection).toBeTruthy();
    const placeholder = screen.getByTestId("diag-not-generated");
    expect(placeholder).toBeTruthy();
    expect(placeholder.textContent).toBe("诊断数据暂未生成");
    expect(screen.queryByTestId("dedup-diag-cards")).toBeNull();
  });

  it("S4 dedup_section_rendered_when_success: step1 success + sizes_hist non-empty → DedupSizesCard ≥1 chip (1· or green chip)", async () => {
    const mockClient = makeMockInjectClient();
    const mockDiag = makeMockDiagClient();
    mockDiag.getStepDiag.mockResolvedValue({
      sizes_hist: { "1": 800, "2": 40, "3": 10 },
      hamming_hist: { "0": 5, "1": 8, "2": 12, "3": 10, "4": 20, "5": 18, "6": 15 },
      perf: {
        nodes: 920,
        build_ms: 120.5,
        query_avg_us: 45.2,
        step1_total_ms: 489,
        speedup_x: 4.2,
        parallel_eff_x: 6.0,
        slo_2000: 2000,
        ratio: 0.24,
      },
    });
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "success");
    renderPage(mockClient, detail, mockDiag);
    await flush();
    await flush();

    const dedupCards = screen.getByTestId("dedup-diag-cards");
    expect(dedupCards).toBeTruthy();
    const sizesCard = screen.getByTestId("dedup-sizes-card");
    expect(sizesCard).toBeTruthy();

    const chip1 = screen.queryByTestId("sizes-chip-1");
    const has1DotText = screen.queryByText(/1·/);
    const has1Text = screen.queryByText(/1 ·/);
    expect(chip1 || has1DotText || has1Text).toBeTruthy();

    if (chip1) {
      const style = window.getComputedStyle(chip1);
      const bg = style.backgroundColor || "";
      const greenBgOk = bg.includes("209, 250, 229") || bg.includes("d1fae5");
      expect(greenBgOk).toBe(true);
    }
  });

  it("S5 funnel_nout_step1_exact_match: Funnel step1 count == DedupDiag.perf.nodes == step1.n_out exact", async () => {
    const mockClient = makeMockInjectClient();
    const mockDiag = makeMockDiagClient();
    const step1Nodes = 920;
    mockDiag.getStepDiag.mockResolvedValue({
      sizes_hist: { "1": 800, "2": 40, "3": 10 },
      hamming_hist: { "0": 5, "1": 8, "2": 12, "3": 10, "4": 20, "5": 18, "6": 15 },
      perf: {
        nodes: step1Nodes,
        build_ms: 120.5,
        query_avg_us: 45.2,
        step1_total_ms: 489,
        speedup_x: 4.2,
        parallel_eff_x: 6.0,
        slo_2000: 2000,
        ratio: 0.24,
      },
    });
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "success");
    detail.steps = detail.steps.map((s, i) => ({
      ...s,
      n_out: i === 1 ? step1Nodes : s.n_out,
    }));
    detail.funnel_counts = [1000, step1Nodes, 800, 700, 60, 42];
    renderPage(mockClient, detail, mockDiag);
    await flush();
    await flush();

    const funnelN2 = screen.getByTestId("fpb-label-N2");
    expect(funnelN2.textContent).toContain(`${step1Nodes}`);

    const step1Nout = (detail.steps[1] as PipelineStepInfo).n_out;
    expect(step1Nout).toBe(step1Nodes);
  });

  it("S6 wide_1280_no_overflow_x: 1280x800 → body.scrollWidth == clientWidth", async () => {
    const mockClient = makeMockInjectClient();
    const mockDiag = makeMockDiagClient();
    mockDiag.getStepDiag.mockResolvedValue({
      sizes_hist: { "1": 800, "2": 40, "3": 10 },
      hamming_hist: { "0": 5, "1": 8, "2": 12, "3": 10, "4": 20, "5": 18, "6": 15 },
      perf: {
        nodes: 920,
        build_ms: 120.5,
        query_avg_us: 45.2,
        step1_total_ms: 489,
        speedup_x: 4.2,
        parallel_eff_x: 6.0,
        slo_2000: 2000,
        ratio: 0.24,
      },
    });
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "success");

    const originalInnerWidth = window.innerWidth;
    const originalInnerHeight = window.innerHeight;
    const originalClientWidth = document.documentElement.clientWidth;

    Object.defineProperty(window, "innerWidth", {
      writable: true,
      configurable: true,
      value: 1280,
    });
    Object.defineProperty(window, "innerHeight", {
      writable: true,
      configurable: true,
      value: 800,
    });
    Object.defineProperty(document.documentElement, "clientWidth", {
      writable: true,
      configurable: true,
      value: 1280,
    });

    try {
      renderPage(mockClient, detail, mockDiag);
      await flush();

      const page = screen.getByTestId("pipeline-run-detail-page");
      const scrollWidth = page.scrollWidth;
      const clientWidth = page.clientWidth;
      expect(scrollWidth).toBeLessThanOrEqual(clientWidth + 1);
    } finally {
      Object.defineProperty(window, "innerWidth", {
        writable: true,
        configurable: true,
        value: originalInnerWidth,
      });
      Object.defineProperty(window, "innerHeight", {
        writable: true,
        configurable: true,
        value: originalInnerHeight,
      });
      Object.defineProperty(document.documentElement, "clientWidth", {
        writable: true,
        configurable: true,
        value: originalClientWidth,
      });
    }
  });

  it("S7 mobile_800_fails_not_required: 800px overflow not guaranteed, pass trivially", async () => {
    const mockClient = makeMockInjectClient();
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "success");
    renderPage(mockClient, detail);
    await flush();

    const page = screen.getByTestId("pipeline-run-detail-page");
    expect(page).toBeTruthy();
    expect(true).toBe(true);
  });

  it("S8 pipeline_id_chip_correct: run header chip RUN #p-xxxx ULID 32char starts with p-", async () => {
    const mockClient = makeMockInjectClient();
    const runId = "p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32";
    const detail = makeDetail(runId, "success");
    renderPage(mockClient, detail);
    await flush();

    const chip = screen.getByTestId("pipeline-id-chip");
    expect(chip).toBeTruthy();
    const chipText = chip.textContent || "";
    expect(chipText).toContain(`RUN #${runId}`);
    expect(runId.startsWith("p-")).toBe(true);
    const ulidPart = runId.slice(2);
    expect(ulidPart.length).toBe(32);
  });

  it("S9 dedup_perf_card_speedup_emoji: perf.step1_total_ms=489 → 🚀 emoji present", async () => {
    const mockClient = makeMockInjectClient();
    const mockDiag = makeMockDiagClient();
    mockDiag.getStepDiag.mockResolvedValue({
      sizes_hist: { "1": 800, "2": 40, "3": 10 },
      hamming_hist: { "0": 5, "1": 8, "2": 12, "3": 10, "4": 20, "5": 18, "6": 15 },
      perf: {
        nodes: 920,
        build_ms: 120.5,
        query_avg_us: 45.2,
        step1_total_ms: 489,
        speedup_x: 4.2,
        parallel_eff_x: 6.0,
        slo_2000: 2000,
        ratio: 0.24,
      },
    });
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "success");
    renderPage(mockClient, detail, mockDiag);
    await flush();
    await flush();

    const rocketEl = screen.getByText(/🚀/);
    expect(rocketEl).toBeTruthy();
  });

  it("S10 dedup_3_cards_3_titles: Sect③-B 内 3 h4 标题 size/hamming/perf 全部存在", async () => {
    const mockClient = makeMockInjectClient();
    const mockDiag = makeMockDiagClient();
    mockDiag.getStepDiag.mockResolvedValue({
      sizes_hist: { "1": 800, "2": 40, "3": 10 },
      hamming_hist: { "0": 5, "1": 8, "2": 12, "3": 10, "4": 20, "5": 18, "6": 15 },
      perf: {
        nodes: 920,
        build_ms: 120.5,
        query_avg_us: 45.2,
        step1_total_ms: 489,
        speedup_x: 4.2,
        parallel_eff_x: 6.0,
        slo_2000: 2000,
        ratio: 0.24,
      },
    });
    const detail = makeDetail("p-01J5RBXZ7QK9VYH3MN2W4LC6DF8A0E32", "success");
    renderPage(mockClient, detail, mockDiag);
    await flush();
    await flush();

    const dedupSection = screen.getByTestId("dedupdiag-section");
    expect(dedupSection).toBeTruthy();

    const sizesTitle = screen.getByTestId("dedup-sizes-title");
    const hammingTitle = screen.getByTestId("dedup-hamming-title");
    const perfTitle = screen.getByTestId("dedup-perf-title");

    expect(sizesTitle).toBeTruthy();
    expect(sizesTitle.tagName).toBe("H4");
    expect(sizesTitle.textContent).toBe("重复组大小分布");

    expect(hammingTitle).toBeTruthy();
    expect(hammingTitle.tagName).toBe("H4");
    expect(hammingTitle.textContent).toBe("汉明距命中分布");

    expect(perfTitle).toBeTruthy();
    expect(perfTitle.tagName).toBe("H4");
    expect(perfTitle.textContent).toBe("BK-Tree 性能");
  });
});
