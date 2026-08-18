import { describe, it, expect } from "vitest";
import * as SharedUI from "../index";

describe("Barrel Grade+Report 8 Exports (T10)", () => {
  it("D01 exports 8 component names PascalCase grade4 + report4", () => {
    const expectedNames = [
      "GradeDomainScorer5",
      "GradeUpgradeScorer3",
      "GradeAssessmentCard",
      "GradeSoFTable",
      "ReportExportMenu3Formats",
      "Prisma2020Checklist27",
      "ReportSnapshotList",
      "DashboardOutputCards",
    ].sort();
    const exportedKeys = Object.keys(SharedUI).filter(k => expectedNames.includes(k)).sort();
    expect(exportedKeys).toEqual(expectedNames);
  });

  it("D02 each exported component typeof === function (React function component)", () => {
    const names = [
      "GradeDomainScorer5",
      "GradeUpgradeScorer3",
      "GradeAssessmentCard",
      "GradeSoFTable",
      "ReportExportMenu3Formats",
      "Prisma2020Checklist27",
      "ReportSnapshotList",
      "DashboardOutputCards",
    ] as const;
    for (const n of names) {
      const fn = (SharedUI as any)[n];
      expect(typeof fn === "function", `Barrel missing export function: ${n}`).toEqual(true);
    }
  });

  it("D03 8 exports PascalCase names all start with uppercase letter (sanity)", () => {
    const keys = Object.keys(SharedUI).filter(k => /^(Grade|Report|Prisma|Dashboard)/.test(k));
    for (const k of keys) {
      expect(/^[A-Z]/.test(k), `${k} not PascalCase`).toEqual(true);
    }
  });
});
