import { describe, expect, it } from "vitest";
import type { Report8ChaptersDraft, ReportGeneratePayload } from "@meda/shared-sdk";

type _draft = Report8ChaptersDraft<number>;
type _payload = ReportGeneratePayload<number>;

const _validDraft: _draft = {
  ch1_background: "",
  ch2_methods: "",
  ch3_pico: "",
  ch4_results: "",
  ch5_grade_assessment: "",
  ch6_summary_of_findings: "",
  ch7_discussion: "",
  ch8_appendices: "",
  source_snapshot_id: null,
};

const _validPayload: _payload = {
  version_label: "v0.1",
  override_ch1_background: "x",
};

describe("T2 types exist and match snapshot", () => {
  it("type imports without runtime value is not needed (type-only test)", () => {
    expect(typeof _validDraft.ch1_background).toBe("string");
    expect(typeof _validDraft.ch2_methods).toBe("string");
    expect(typeof _validDraft.ch3_pico).toBe("string");
    expect(typeof _validDraft.ch4_results).toBe("string");
    expect(typeof _validDraft.ch5_grade_assessment).toBe("string");
    expect(typeof _validDraft.ch6_summary_of_findings).toBe("string");
    expect(typeof _validDraft.ch7_discussion).toBe("string");
    expect(typeof _validDraft.ch8_appendices).toBe("string");
    expect(_validDraft.source_snapshot_id).toBeNull();

    expect(_validPayload.version_label).toBe("v0.1");
    expect(_validPayload.override_ch1_background).toBe("x");
    expect(true).toBe(true);
  });
});
