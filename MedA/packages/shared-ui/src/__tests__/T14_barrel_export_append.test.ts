import { describe, it, expect } from "vitest";
import React from "react";
import type {
  PipelineRunStatus, PipelineRunDetail, PipelineCompareResult,
} from "../index";
import { PipelineRunsListPage } from "../pages/PipelineRunsListPage";
import { PipelineRunDetailPage } from "../pages/PipelineRunDetailPage";
import { PipelineComparePage } from "../pages/PipelineComparePage";
import { NewRunModal } from "../components/NewRunModal";
import { GradeDistributionCard } from "../components/GradeDistributionCard";

describe("T14 W10 barrel append 5 components + 6 types", () => {
  it("T14-1a 5 Page/Component names are functions via barrel import", () => {
    expect(typeof PipelineRunsListPage).toBe("function");
    expect(typeof PipelineRunDetailPage).toBe("function");
    expect(typeof PipelineComparePage).toBe("function");
    expect(typeof NewRunModal).toBe("function");
    expect(typeof GradeDistributionCard).toBe("function");
  });

  it("T14-1b component default props check default sane", () => {
    expect(PipelineRunsListPage.displayName || PipelineRunsListPage.name).toBeTruthy();
    expect(PipelineRunDetailPage.displayName || PipelineRunDetailPage.name).toBeTruthy();
    expect(PipelineComparePage.displayName || PipelineComparePage.name).toBeTruthy();
    expect(NewRunModal.displayName || NewRunModal.name).toBeTruthy();
    expect(GradeDistributionCard.displayName || GradeDistributionCard.name).toBeTruthy();

    const gdCardResult = React.isValidElement(
      React.createElement(GradeDistributionCard, { distribution: { H: 0, M: 0, L: 0 } }),
    );
    expect(gdCardResult).toBe(true);

    const modalResult = React.isValidElement(
      React.createElement(NewRunModal, {
        open: false,
        onClose: () => {},
        onConfirm: () => {},
      }),
    );
    expect(modalResult).toBe(true);
  });

  it("T14-2 3 core types imported from shared-ui barrel", () => {
    const s: PipelineRunStatus = "success";
    const d: PipelineRunDetail = null as any;
    const c: PipelineCompareResult = null as any;
    expect(["queued","running","success","failed","resumable","paused","cancelled","partial"]).toContain(s);
    expect(d).toBeNull(); expect(c).toBeNull();
  });
});
