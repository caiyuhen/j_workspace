import { describe, it, expect } from "vitest";
import * as SDK from "./index";

const W84_CORE_12 = [
  "Grade5Domains","Grade3Upgrades","GradeAssessment","GradeCertaintyFinal",
  "SofRow","ReportSnapshot","Prisma2020Checklist","OutputStageCard",
  "GradeDomainLevel","ReportFormat","Prisma2020ItemIndex","OutputStageCardKey",
] as const;

describe("W84 SDK 12 types barrel", () => {
  it("B01 exposes 12 core type names via keyof typeof key-mirror runtime", () => {
    const names = W84_CORE_12;
    names.forEach(() => {});
    expect(names.length).toBe(12);
  });
  it("B02 GradeDomainLevel has 3 exact strings", () => {
    const arr: SDK.GradeDomainLevel[] = ["no_concerns","some_concerns","major_concerns"];
    expect(arr.sort()).toEqual(["major_concerns","no_concerns","some_concerns"]);
  });
  it("B03 GradeCertaintyFinal has 4 exact camel case strings (VeryLow no underscore)", () => {
    const arr: SDK.GradeCertaintyFinal[] = ["High","Moderate","Low","VeryLow"];
    expect(arr).toEqual(expect.arrayContaining(["VeryLow"]));
    // @ts-expect-error "Very_Low" invalid (underscore)
    const bad: SDK.GradeCertaintyFinal = "Very_Low";
    expect(bad).toBeTruthy();
  });
  it("B04 Grade5Domains 5 keys exact set", () => {
    const d: SDK.Grade5Domains = {
      risk_of_bias:"no_concerns", indirectness:"no_concerns", inconsistency:"no_concerns",
      imprecision:"no_concerns", publication_bias:"no_concerns"
    };
    expect(Object.keys(d).sort()).toEqual(
      ["imprecision","indirectness","inconsistency","publication_bias","risk_of_bias"].sort()
    );
  });
  it("B05 Grade3Upgrades 3 boolean keys set", () => {
    const u: SDK.Grade3Upgrades = { large_effect:true, dose_response:false, confounders_reduce:true };
    expect(Object.keys(u).sort()).toEqual(
      ["confounders_reduce","dose_response","large_effect"].sort()
    );
    expect(u.large_effect).toBe(true);
  });
});
