export interface Batch {
  id: string;
  filename: string;
  total_rows: number;
  error_rows: number;
  status: string;
  profiling_data?: any;
  created_at: string;
}
