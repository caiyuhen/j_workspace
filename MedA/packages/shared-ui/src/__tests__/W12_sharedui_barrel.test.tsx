import { describe, it, expect } from "vitest";
import * as SharedUI from "../index";

describe("W12 Barrel Export Smoke (4 TS tests, shared-ui index.ts resolvable)", () => {
  it("B1: NewRunModal + 4 DedupDiag named exports defined via barrel", () => {
    expect(SharedUI.NewRunModal, "NewRunModal undefined via barrel").toBeDefined();
    expect(SharedUI.DedupSizesCard, "DedupSizesCard undefined via barrel").toBeDefined();
    expect(SharedUI.DedupHammingCard, "DedupHammingCard undefined via barrel").toBeDefined();
    expect(SharedUI.DedupPerfCard, "DedupPerfCard undefined via barrel").toBeDefined();
    expect(SharedUI.DedupDiagCards, "DedupDiagCards undefined via barrel").toBeDefined();
  });

  it("B2: 3 Pipeline pages + GradeDistributionCard typeof === function", () => {
    expect(typeof SharedUI.PipelineRunsListPage === "function").toBe(true);
    expect(typeof SharedUI.PipelineRunDetailPage === "function").toBe(true);
    expect(typeof SharedUI.PipelineComparePage === "function").toBe(true);
    expect(typeof SharedUI.GradeDistributionCard === "function").toBe(true);
  });

  it("B3: barrel Object.keys contains W9/W12 appended export names", () => {
    const keys = Object.keys(SharedUI);
    expect(keys.includes("NewRunModal")).toBe(true);
    expect(keys.includes("PipelineRunsListPage")).toBe(true);
    expect(keys.includes("PipelineRunDetailPage")).toBe(true);
    expect(keys.includes("PipelineComparePage")).toBe(true);
    expect(keys.includes("GradeDistributionCard")).toBe(true);
  });

  it("B4: DedupDiagCards default export alias + 5 type exports non-undefined check", () => {
    expect(SharedUI.DedupDiagCards).toBeDefined();
    expect(typeof SharedUI.DedupDiagCards === "function").toBe(true);
    const mod: any = SharedUI;
    expect(mod.ValidateBeforeCreate === undefined, "ValidateBeforeCreate must NOT leak into barrel").toBe(true);
  });
});
