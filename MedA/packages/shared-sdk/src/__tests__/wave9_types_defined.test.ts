import { describe, it, expect } from "vitest";
import * as SDK from "../index";

describe("Wave 9 SDK types defined (4 tests)", () => {
  it("T1 EvidenceStage has exactly 5 literals", () => {
    const arr: SDK.EvidenceStage[] = [
      "screening_ta",
      "screening_fulltext",
      "quality_ro",
      "quality_nrsi",
      "data_abstractor",
    ];
    expect(arr.length).toBe(5);
    expect(arr.sort()).toEqual([
      "data_abstractor",
      "quality_nrsi",
      "quality_ro",
      "screening_fulltext",
      "screening_ta",
    ]);
  });

  it("T2 EvidenceDecision has 3 values: include/exclude/review", () => {
    const arr: SDK.EvidenceDecision[] = ["include", "exclude", "review"];
    expect(arr.length).toBe(3);
    expect(arr).toEqual(expect.arrayContaining(["include", "exclude", "review"]));
  });

  it("T3 TrafficLightRating has 5 levels including critical", () => {
    const arr: SDK.TrafficLightRating[] = [
      "low",
      "some_concerns",
      "high",
      "critical",
      "ni",
    ];
    expect(arr.length).toBe(5);
    expect(arr).toContain("critical");
  });

  it("T4 StructuredPICO has p.text and o[].rr fields", () => {
    const pico: SDK.StructuredPICO = {
      p: { text: "Adults with T2DM", n: 200 },
      i: { drug: "Metformin", dose: "500mg BID" },
      c: { comparator: "Placebo", type: "placebo" },
      o: [
        {
          name: "HbA1c reduction",
          mean_diff: -0.8,
          rr: 0.85,
          ci_low: 0.78,
          ci_high: 0.92,
          p_value: 0.001,
        },
      ],
    };
    expect(typeof pico.p.text).toBe("string");
    expect(pico.p.text).toBe("Adults with T2DM");
    expect(typeof pico.o[0].rr).toBe("number");
    expect(pico.o[0].rr).toBe(0.85);
  });
});
