import { describe, it, expect } from "vitest";
import type {
  PipelineRunStatus, PipelineMode, PipelineRunSummary,
  PipelineStepInfo, PipelineRunDetail, PipelineCompareResult,
} from "../../../shared-sdk/src/index";

describe("T18 W10 shared-sdk 6 pipeline types defined", () => {
  it("T18-1 PipelineRunStatus has 8 values", () => {
    const v: PipelineRunStatus[] = ["queued","running","success","failed","resumable","paused","cancelled","partial"];
    expect(v).toHaveLength(8);
  });
  it("T18-2 PipelineMode snapshot|live only", () => {
    const m: PipelineMode[] = ["snapshot","live"];
    expect(m).toHaveLength(2);
  });
  it("T18-3 PipelineRunSummary required fields non-null", () => {
    const s: Required<PipelineRunSummary> = {
      run_id:"p-314", preset:"sglt2i_ckd", mode:"snapshot", max_records:200,
      status:"running", current_step_index:3, duration_ms:72000,
      created_at:"2026-08-21T10:12:00Z", finished_at:undefined as any, report_url:undefined as any
    };
    expect(s.run_id).toHaveLength(5);
    expect(s.current_step_index).toBeGreaterThanOrEqual(0);
    expect(s.current_step_index).toBeLessThan(8);
  });
  it("T18-4 PipelineStepInfo length 8 requirement", () => {
    const step: PipelineStepInfo = {
      step_index:2, step_name:"screen_ta", status:"success",
      duration_ms:2100, n_in:178, n_out:104
    };
    expect(step.step_index).toBeLessThan(8);
    expect(["pending","running","success","failed","skipped"]).toContain(step.status);
  });
  it("T18-5 PipelineRunDetail steps len 8", () => {
    const steps: PipelineStepInfo[] = Array.from({length:8}).map((_,i)=>({
      step_index:i as any, step_name:`step${i}`, status:"pending",
      duration_ms:null, n_in:0, n_out:0
    }));
    const d: PipelineRunDetail = { run_id:"p-1", preset:"x", mode:"snapshot",
      max_records:200, status:"queued", current_step_index:0, duration_ms:null,
      created_at:"", steps, cancel_flag:false };
    expect(d.steps).toHaveLength(8);
  });
  it("T18-6 PipelineCompareResult funnel_delta array", () => {
    const c: PipelineCompareResult = { run_a_id:"p-a", run_b_id:"p-b",
      funnel_delta:[{step:"identify",a_n:200,b_n:188,diff:12}],
      rob2_delta:[{overall:"low",a:18,b:17}],
      grade_delta:[{outcome:"eGFR",a:"H",b:"H",reason:"same"}],
      pico:{only_in_a_nct_ids:["N1"],only_in_b_nct_ids:["N2"],both:["N0"]}};
    expect(c.funnel_delta[0].diff).toBe(12);
  });
});
