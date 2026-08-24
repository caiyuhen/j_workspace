import React, { useCallback, useState, useRef, useEffect } from "react";

export interface DedupPerf {
  nodes: number;
  build_ms: number;
  query_avg_us: number;
  step1_total_ms: number;
  speedup_x: number;
  parallel_eff_x: number;
  slo_2000: number;
  ratio: number;
}

export interface DedupDiagData {
  sizes_hist: Record<string, number>;
  hamming_hist: Record<string, number>;
  perf?: DedupPerf;
  [key: string]: unknown;
}

export type DiagErrorCode =
  | "DIAG_NOT_READY"
  | "DIAG_NOT_WRITTEN"
  | "AUTH_FAILED"
  | "FORBIDDEN"
  | "UNKNOWN";

export interface DiagError {
  code: DiagErrorCode;
  status: number;
  message?: string;
}

export interface InjectDiagClient {
  getStepDiag: (
    workspaceId: string,
    runId: string,
    stepIndex: number,
  ) => Promise<DedupDiagData>;
}

export interface UseStepDiagOptions {
  workspaceId: string;
  runId: string;
  stepIndex: number;
  stepStatus: string;
  intervalMs?: number;
  injectFetchClient?: Partial<InjectDiagClient>;
}

export interface UseStepDiagState {
  diag?: DedupDiagData;
  loading: boolean;
  error?: DiagError;
  pollActive: boolean;
}

export interface UseStepDiagReturn {
  refresh: () => Promise<DedupDiagData | undefined>;
  state: UseStepDiagState;
}

const STEP_TERMINAL_STATUSES = new Set(["failed", "cancelled", "partial", "paused", "skipped"]);
const STEP_POLL_BEFORE_SUCCESS = new Set(["pending", "running", "queued", "resumable"]);

function _defaultGetStepDiag(): Promise<DedupDiagData> {
  return Promise.resolve({
    sizes_hist: {},
    hamming_hist: {},
    perf: undefined,
  });
}

const NO_POLL_ERROR_CODES = new Set<DiagErrorCode>([
  "DIAG_NOT_WRITTEN",
  "AUTH_FAILED",
  "FORBIDDEN",
]);

export function useStepDiag(
  opts: UseStepDiagOptions,
): UseStepDiagReturn {
  const intervalMs = opts.intervalMs ?? 1500;
  const stepStatusRef = useRef<string>(opts.stepStatus);
  stepStatusRef.current = opts.stepStatus;

  const errorRef = useRef<DiagError | undefined>(undefined);
  const diagRef = useRef<DedupDiagData | undefined>(undefined);

  const [state, setState] = useState<UseStepDiagState>({
    diag: undefined,
    loading: false,
    error: undefined,
    pollActive: false,
  });

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const client: InjectDiagClient = {
    getStepDiag: opts.injectFetchClient?.getStepDiag ?? _defaultGetStepDiag,
  };

  const stopPolling = useCallback((): void => {
    clearInterval(intervalRef.current ?? undefined);
    intervalRef.current = null;
    setState((prev) => (prev.pollActive ? { ...prev, pollActive: false } : prev));
  }, []);

  const shouldPoll = useCallback((): boolean => {
    const s = stepStatusRef.current;
    if (STEP_POLL_BEFORE_SUCCESS.has(s)) return true;
    if (STEP_TERMINAL_STATUSES.has(s)) return false;
    if (s === "success") {
      if (diagRef.current) return false;
      if (errorRef.current && NO_POLL_ERROR_CODES.has(errorRef.current.code)) return false;
      return true;
    }
    return false;
  }, []);

  const fetchDiag = useCallback(async (): Promise<
    DedupDiagData | undefined
  > => {
    setState((prev) => ({ ...prev, loading: true, error: undefined }));
    try {
      const diag = await client.getStepDiag(
        opts.workspaceId,
        opts.runId,
        opts.stepIndex,
      );
      diagRef.current = diag;
      errorRef.current = undefined;
      setState((prev) => ({ ...prev, diag, loading: false }));
      if (!shouldPoll()) {
        stopPolling();
      }
      return diag;
    } catch (err: unknown) {
      let diagErr: DiagError;
      const anyErr = err as { status?: number; code?: string; message?: string };
      const status = anyErr.status ?? 500;
      if (status === 401) {
        diagErr = { code: "AUTH_FAILED", status, message: "认证失败" };
      } else if (status === 403) {
        diagErr = { code: "FORBIDDEN", status, message: "鉴权失败" };
      } else if (status === 404) {
        const code = anyErr.code ?? "DIAG_NOT_READY";
        if (code === "DIAG_NOT_WRITTEN") {
          diagErr = { code: "DIAG_NOT_WRITTEN", status, message: "诊断数据缺失" };
        } else {
          diagErr = { code: "DIAG_NOT_READY", status, message: "step 诊断尚未写入" };
        }
      } else {
        diagErr = { code: "UNKNOWN", status, message: anyErr.message ?? "未知错误" };
      }
      diagRef.current = undefined;
      errorRef.current = diagErr;
      setState((prev) => ({ ...prev, error: diagErr, loading: false }));
      if (!shouldPoll()) {
        stopPolling();
      }
      return undefined;
    }
  }, [client, opts.workspaceId, opts.runId, opts.stepIndex, stopPolling, shouldPoll]);

  const startPollingIfNeeded = useCallback((): void => {
    if (shouldPoll()) {
      if (!intervalRef.current) {
        setState((prev) => ({ ...prev, pollActive: true }));
        intervalRef.current = setInterval(() => {
          fetchDiag().catch(() => {});
        }, intervalMs);
      }
    } else {
      stopPolling();
    }
  }, [intervalMs, fetchDiag, stopPolling, shouldPoll]);

  useEffect(() => {
    if (opts.stepStatus === "success") {
      fetchDiag().then(() => {
        startPollingIfNeeded();
      }).catch(() => {});
    } else {
      stopPolling();
    }
    return () => {
      stopPolling();
    };
  }, [opts.stepStatus]);

  useEffect(() => {
    startPollingIfNeeded();
  }, [state.diag, state.error, opts.stepStatus, startPollingIfNeeded]);

  const refresh = useCallback(async (): Promise<
    DedupDiagData | undefined
  > => {
    return await fetchDiag();
  }, [fetchDiag]);

  return {
    refresh,
    state,
  };
}
