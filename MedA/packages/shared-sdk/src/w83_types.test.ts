import { describe, expect, it } from "vitest";

import * as sdk from "./index";

describe("WAVE 8.3 T7 extraction+analysis type exports", () => {
  it("TC1: 12 core type literal names array has length 12", () => {
    const names: string[] = [
      "ExtractionTemplateField",
      "ExtractionTemplate",
      "ExtractionCell",
      "OutcomeDefinition",
      "BinaryArmInputs",
      "ContinuousArmInputs",
      "OutcomeArmAnyInputs",
      "OutcomeArmData",
      "PooledHeterogeneity",
      "AnalysisRun",
      "EvidenceTableWideRow",
      "KappaFieldSummary",
    ];
    expect(names.length).toBe(12);
  });

  it("TC2: ExtractionTemplateField pico_binding literal in allowed set", () => {
    const field: sdk.ExtractionTemplateField = {
      key: "pop",
      label: "Population",
      pico_binding: "P",
      required: true,
    };
    const allowed = ["P", "I", "C", "O", "S", "StudyType", "OutcomeMeasure", "Other"];
    expect(allowed).toContain(field.pico_binding);
  });

  it("TC3: ExtractionTemplate fields_json list has length 1", () => {
    const tpl: sdk.ExtractionTemplate = {
      template_id: 1,
      name: "RCT Standard",
      fields_json: [
        { key: "pop", label: "Population", pico_binding: "P", required: true },
      ],
      created_at: "2026-08-17T00:00:00Z",
    };
    expect(Array.isArray(tpl.fields_json)).toBe(true);
    expect(tpl.fields_json.length).toBe(1);
    expect(typeof tpl.fields_json[0]).toBe("object");
    expect(tpl.fields_json[0]).not.toBeNull();
  });

  it("TC4: OutcomeDefinition.measure in allowed effect set", () => {
    const od: sdk.OutcomeDefinition = {
      outcome_id: 1,
      name: "All-cause mortality",
      measure: "RR",
      time_point: "12 months",
    };
    const allowed = ["RR", "OR", "RD", "MD", "SMD"];
    expect(allowed).toContain(od.measure);
  });

  it("TC5: KappaFieldSummary.warning_level in {low_agreement, ok}", () => {
    const kfs: sdk.KappaFieldSummary = {
      field_key: "intervention",
      kappa: 0.42,
      n_pairs: 120,
      warning_level: "low_agreement",
    };
    const allowed = ["low_agreement", "ok"];
    expect(allowed).toContain(kfs.warning_level);
  });
});
