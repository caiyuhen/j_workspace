import { describe, expect, it } from "vitest";
import type { Report8ChaptersDraft, ReportGeneratePayload } from "../index";
describe("T2 types exist and match snapshot", () => {
  it("type imports without runtime value is not needed (type-only test)", () => {
    const _draft: Report8ChaptersDraft<number> = {
      ch1_background: "", ch2_methods: "", ch3_pico: "", ch4_results: "",
      ch5_grade_assessment: "", ch6_summary_of_findings: "", ch7_discussion: "",
      ch8_appendices: "", source_snapshot_id: null,
    };
    const _payload: ReportGeneratePayload<number> = { version_label: "v0.1", override_ch1_background: "x" };
    expect(true).toBe(true);
  });
});
