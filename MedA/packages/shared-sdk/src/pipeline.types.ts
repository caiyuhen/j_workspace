export type PipelineRunStatus =
  "queued" | "running" | "success" | "failed" |
  "resumable" | "paused" | "cancelled" | "partial";
export type PipelineMode = "snapshot" | "live";

export interface PipelineRunSummary {
  run_id: string;
  preset: string;
  mode: PipelineMode;
  max_records: number;
  status: PipelineRunStatus;
  current_step_index: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;
  duration_ms: number | null;
  created_at: string;
  finished_at?: string;
  report_url?: string;
}

export interface PipelineStepInfo {
  step_index: 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7;
  step_name: string;
  status: "pending" | "running" | "success" | "failed" | "skipped";
  duration_ms: number | null;
  n_in: number;
  n_out: number;
  error?: string;
  retryable?: boolean;
  attempt_no?: 1 | 2 | 3;
}

export interface PipelineRunDetail extends PipelineRunSummary {
  steps: PipelineStepInfo[];
  cancel_flag: boolean;
  pico_csv_url?: string;
  grade_distribution?: { H: number; M: number; L: number };
  rob2_distribution?: { low: number; some: number; high: number };
  funnel_counts?: number[];
}

export interface PipelineCompareResult {
  run_a_id: string;
  run_b_id: string;
  funnel_delta: { step: string; a_n: number; b_n: number; diff: number }[];
  rob2_delta: { overall: "low" | "some" | "high"; a: number; b: number }[];
  grade_delta: { outcome: string; a: "H" | "M" | "L"; b: "H" | "M" | "L"; reason: string }[];
  pico: {
    only_in_a_nct_ids: string[];
    only_in_b_nct_ids: string[];
    both: string[];
  };
}
