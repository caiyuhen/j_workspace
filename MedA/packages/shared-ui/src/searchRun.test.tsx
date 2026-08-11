import { describe, expect, it, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";

import { PrismaChart, calculatePrismaWidths } from "./PrismaChart";
import {
  SearchRunListScreen,
  STATUS_CHIP_STYLES,
  type SearchRunStatus,
  type SearchRunListItem,
} from "./SearchRunListScreen";
import {
  LiteratureLibraryScreen,
  SORT_OPTIONS,
  type LiteratureLibrarySortKey,
} from "./LiteratureLibraryScreen";
import type { LiteratureLibrarySummary } from "@meda/shared-sdk";

const mockLibraryBase = (): LiteratureLibrarySummary => ({
  project: {
    id: 1,
    name: "测试项目",
    workspace_key: "test-ws",
    current_stage: "search",
    updated_at_label: "刚刚",
  },
  stage_key: "search",
  records: [
    {
      id: 1,
      title: "SGLT2i 和 CKD 研究",
      authors: "Neuen BL",
      journal: "NEJM",
      year: 2023,
      doi: "10.1056/nejmoa2212939",
      pmid: "37123457",
      source_key: "pubmed",
      source_label: "PubMed",
      dedupe_status: "unique",
      duplicate_of_id: null,
    },
  ],
  stats: {
    total_count: 1,
    unique_count: 1,
    duplicate_count: 0,
    by_source: [
      { source_key: "pubmed", source_label: "PubMed", count: 1 },
    ],
  },
  recent_batches: [],
  available_sources: [
    {
      key: "pubmed",
      label: "PubMed",
      description: "NCBI 生物医学文献库",
      supports_full_text: false,
    },
  ],
  last_import_result: null,
});

describe("PrismaChart widths proportional", () => {
  it("(i) identification 6, screening 4, eligibility 4, included 4 => identification width > others equal", () => {
    const { container } = render(
      <PrismaChart
        identification={6}
        screening={4}
        eligibility={4}
        included={4}
        maxWidth={600}
      />,
    );
    const identBar = container.querySelector(
      '[data-testid="prisma-bar-identification"]',
    );
    const screenBar = container.querySelector(
      '[data-testid="prisma-bar-screening"]',
    );
    const eligBar = container.querySelector(
      '[data-testid="prisma-bar-eligibility"]',
    );
    const inclBar = container.querySelector(
      '[data-testid="prisma-bar-included"]',
    );
    expect(identBar).not.toBeNull();
    expect(screenBar).not.toBeNull();
    expect(eligBar).not.toBeNull();
    expect(inclBar).not.toBeNull();
    const identW = Number(identBar?.getAttribute("width"));
    const screenW = Number(screenBar?.getAttribute("width"));
    const eligW = Number(eligBar?.getAttribute("width"));
    const inclW = Number(inclBar?.getAttribute("width"));
    expect(identW).toBeGreaterThan(screenW);
    expect(screenW).toBe(eligW);
    expect(eligW).toBe(inclW);
  });
});

const ALL_STATUSES: SearchRunStatus[] = [
  "pending",
  "running",
  "completed",
  "partial_failed",
  "failed",
  "cancelled",
];

describe("Status chip colors 6 states", () => {
  const makeRun = (status: SearchRunStatus): SearchRunListItem => ({
    id: 100 + ALL_STATUSES.indexOf(status),
    status,
    created_at: new Date().toISOString(),
    sources: [],
    prisma: { identification: 0, screening: 0 },
    progress_percent: status === "running" ? 42 : null,
  });

  it("(ii-1) pending renders grey className and color literal", () => {
    render(
      <SearchRunListScreen
        runs={[makeRun("pending")]}
        onCreateRun={() => {}}
      />,
    );
    const chip = screen.getByTestId("status-chip-pending");
    expect(chip.getAttribute("class") ?? "").toContain(
      STATUS_CHIP_STYLES.pending.className ?? "status-pending-grey",
    );
    const style = chip.getAttribute("style") ?? "";
    expect(style).toContain("color");
  });

  it("(ii-2) running renders blue className and color literal", () => {
    render(
      <SearchRunListScreen
        runs={[makeRun("running")]}
        onCreateRun={() => {}}
      />,
    );
    const chip = screen.getByTestId("status-chip-running");
    expect(chip.getAttribute("class") ?? "").toContain(
      STATUS_CHIP_STYLES.running.className ?? "status-running-blue",
    );
    const style = chip.getAttribute("style") ?? "";
    expect(style).toContain("background");
  });

  it("(ii-3) completed renders green className and color literal", () => {
    render(
      <SearchRunListScreen
        runs={[makeRun("completed")]}
        onCreateRun={() => {}}
      />,
    );
    const chip = screen.getByTestId("status-chip-completed");
    expect(chip.getAttribute("class") ?? "").toContain(
      STATUS_CHIP_STYLES.completed.className ?? "status-completed-green",
    );
    const style = chip.getAttribute("style") ?? "";
    expect(style).toContain("background");
  });

  it("(ii-4) partial_failed renders orange className and color literal", () => {
    render(
      <SearchRunListScreen
        runs={[makeRun("partial_failed")]}
        onCreateRun={() => {}}
      />,
    );
    const chip = screen.getByTestId("status-chip-partial_failed");
    expect(chip.getAttribute("class") ?? "").toContain(
      STATUS_CHIP_STYLES.partial_failed.className ?? "status-partial_orange",
    );
    const style = chip.getAttribute("style") ?? "";
    expect(style).toContain("background");
  });

  it("(ii-5) failed renders red className and color literal", () => {
    render(
      <SearchRunListScreen
        runs={[makeRun("failed")]}
        onCreateRun={() => {}}
      />,
    );
    const chip = screen.getByTestId("status-chip-failed");
    expect(chip.getAttribute("class") ?? "").toContain(
      STATUS_CHIP_STYLES.failed.className ?? "status-failed-red",
    );
    const style = chip.getAttribute("style") ?? "";
    expect(style).toContain("background");
  });

  it("(ii-6) cancelled renders neutral grey className and color literal", () => {
    render(
      <SearchRunListScreen
        runs={[makeRun("cancelled")]}
        onCreateRun={() => {}}
      />,
    );
    const chip = screen.getByTestId("status-chip-cancelled");
    expect(chip.getAttribute("class") ?? "").toContain(
      STATUS_CHIP_STYLES.cancelled.className ?? "status-cancelled-grey",
    );
    const style = chip.getAttribute("style") ?? "";
    expect(style).toContain("background");
  });
});

describe("Sort dropdown 4 items rendered", () => {
  it("(iii-1) default sort option rendered on screen", () => {
    render(
      <LiteratureLibraryScreen
        library={mockLibraryBase()}
        onBackToStageEntry={() => {}}
        onImport={() => {}}
        onConfirmUnique={() => {}}
      />,
    );
    const opt = screen.getByTestId("sort-option-default");
    expect(opt).not.toBeNull();
    expect(opt.textContent).toContain("入库顺序 默认");
  });

  it("(iii-2) relevance sort option rendered on screen", () => {
    render(
      <LiteratureLibraryScreen
        library={mockLibraryBase()}
        onBackToStageEntry={() => {}}
        onImport={() => {}}
        onConfirmUnique={() => {}}
      />,
    );
    const opt = screen.getByTestId("sort-option-relevance");
    expect(opt).not.toBeNull();
    expect(opt.textContent).toContain("BM25 相关性");
  });

  it("(iii-3) year_desc sort option rendered on screen", () => {
    render(
      <LiteratureLibraryScreen
        library={mockLibraryBase()}
        onBackToStageEntry={() => {}}
        onImport={() => {}}
        onConfirmUnique={() => {}}
      />,
    );
    const opt = screen.getByTestId("sort-option-year_desc");
    expect(opt).not.toBeNull();
    expect(opt.textContent).toContain("最新发表");
  });

  it("(iii-4) journal sort option rendered on screen", () => {
    render(
      <LiteratureLibraryScreen
        library={mockLibraryBase()}
        onBackToStageEntry={() => {}}
        onImport={() => {}}
        onConfirmUnique={() => {}}
      />,
    );
    const opt = screen.getByTestId("sort-option-journal");
    expect(opt).not.toBeNull();
    expect(opt.textContent).toContain("期刊");
  });
});

describe("Sort onChange callback fires on relevance selection", () => {
  it("(iv) selecting 'relevance' option fires onSortChange callback with 'relevance'", () => {
    const onChange = vi.fn<[LiteratureLibrarySortKey], void>();
    render(
      <LiteratureLibraryScreen
        library={mockLibraryBase()}
        onBackToStageEntry={() => {}}
        onImport={() => {}}
        onConfirmUnique={() => {}}
        onSortChange={onChange}
      />,
    );
    const dropdown = screen.getByTestId(
      "library-sort-dropdown",
    ) as HTMLSelectElement;
    fireEvent.change(dropdown, { target: { value: "relevance" } });
    expect(onChange).toHaveBeenCalledTimes(1);
    expect(onChange).toHaveBeenCalledWith("relevance");
  });
});
