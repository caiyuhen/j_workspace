export interface Batch {
  id: string;
  filename: string;
  total_rows: number;
  error_rows: number;
  status: string;
  profiling_data?: any;
  created_at: string;
  batch_type?: string;
  dataset_name?: string;
  trigger_mode?: string;
  window_start?: string | null;
  window_end?: string | null;
  inserted_rows?: number;
  updated_rows?: number;
  deleted_rows?: number;
  unchanged_rows?: number;
  core_metrics?: Record<string, unknown> | null;
  detail_stats?: Record<string, unknown> | null;
}
