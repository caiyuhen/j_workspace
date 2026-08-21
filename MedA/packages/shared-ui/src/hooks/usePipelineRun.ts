import React, { useCallback, useState, useRef, useEffect } from "react";
import type {
  PipelineRunDetail,
  PipelineRunSummary,
  PipelineRunStatus,
  PipelineMode,
} from "@meda/shared-sdk";

export interface PipelineListParams {
  status?: PipelineRunStatus;
  preset?: string;
  page?: number;
  per_page?: number;
}

export interface InjectPipelineRunClient {
  startRun: (payload: {
    preset: string;
    mode: PipelineMode;
    max_records: number;
  }) => Promise<{ run_id: string }>;
  cancelRun: (runId: string) => Promise<void>;
  retryStep: (
    runId: string,
    stepIdx: number,
    payload: { force?: boolean },
  ) => Promise<PipelineRunDetail>;
  getDetail: (runId: string) => Promise<PipelineRunDetail>;
  listRuns: (params: PipelineListParams) => Promise<PipelineRunSummary[]>;
}

export interface UsePipelineRunOptions {
  workspaceId: string;
  runId?: string;
  intervalMs?: number;
  injectFetchClient?: Partial<InjectPipelineRunClient>;
}

export interface UsePipelineRunState {
  detail?: PipelineRunDetail;
  runs: PipelineRunSummary[];
  loading: boolean;
  error?: unknown;
  pollActive: boolean;
}

export interface UsePipelineRunReturn {
  startRun: (
    preset: string,
    mode?: PipelineMode,
    max_records?: number,
  ) => Promise<{ run_id: string }>;
  cancelRun: () => Promise<void>;
  retryStep: (step_idx: number, force?: boolean) => Promise<PipelineRunDetail>;
  refresh: () => Promise<PipelineRunDetail | undefined>;
  listRuns: (params?: PipelineListParams) => Promise<PipelineRunSummary[]>;
  state: UsePipelineRunState;
}

const TERMINAL_STATUSES: PipelineRunStatus[] = [
  "success",
  "failed",
  "cancelled",
  "partial",
  "paused",
];

function _defaultStartRun(): Promise<{ run_id: string }> {
  return Promise.resolve({ run_id: "" });
}

function _defaultCancelRun(): Promise<void> {
  return Promise.resolve();
}

function _defaultRetryStep(): Promise<PipelineRunDetail> {
  return Promise.resolve({} as PipelineRunDetail);
}

function _defaultGetDetail(): Promise<PipelineRunDetail> {
  return Promise.resolve({} as PipelineRunDetail);
}

function _defaultListRuns(): Promise<PipelineRunSummary[]> {
  return Promise.resolve([]);
}

export function usePipelineRun(
  opts: UsePipelineRunOptions,
): UsePipelineRunReturn {
  const intervalMs = opts.intervalMs ?? 1500;
  const runIdRef = useRef<string | undefined>(opts.runId);

  const [state, setState] = useState<UsePipelineRunState>({
    detail: undefined,
    runs: [],
    loading: false,
    error: undefined,
    pollActive: false,
  });

  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const client: InjectPipelineRunClient = {
    startRun: opts.injectFetchClient?.startRun ?? _defaultStartRun,
    cancelRun: opts.injectFetchClient?.cancelRun ?? _defaultCancelRun,
    retryStep: opts.injectFetchClient?.retryStep ?? _defaultRetryStep,
    getDetail: opts.injectFetchClient?.getDetail ?? _defaultGetDetail,
    listRuns: opts.injectFetchClient?.listRuns ?? _defaultListRuns,
  };

  const stopPolling = useCallback((): void => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setState((prev) => (prev.pollActive ? { ...prev, pollActive: false } : prev));
  }, []);

  const shouldPoll = (status?: PipelineRunStatus): boolean => {
    if (!status) return false;
    return (
      status === "queued" ||
      status === "running" ||
      status === "resumable"
    );
  };

  const fetchDetail = useCallback(async (): Promise<
    PipelineRunDetail | undefined
  > => {
    const id = runIdRef.current;
    if (!id) return undefined;
    setState((prev) => ({ ...prev, loading: true, error: undefined }));
    try {
      const detail = await client.getDetail(id);
      setState((prev) => ({ ...prev, detail, loading: false }));
      if (TERMINAL_STATUSES.includes(detail.status)) {
        stopPolling();
      }
      return detail;
    } catch (err) {
      setState((prev) => ({ ...prev, error: err, loading: false }));
      stopPolling();
      throw err;
    }
  }, [client, stopPolling]);

  const startPollingIfNeeded = useCallback(
    (detail?: PipelineRunDetail): void => {
      if (shouldPoll(detail?.status)) {
        if (!intervalRef.current) {
          setState((prev) => ({ ...prev, pollActive: true }));
          intervalRef.current = setInterval(() => {
            fetchDetail().catch(() => {});
          }, intervalMs);
        }
      } else {
        stopPolling();
      }
    },
    [intervalMs, fetchDetail, stopPolling],
  );

  useEffect(() => {
    if (opts.runId) {
      runIdRef.current = opts.runId;
      fetchDetail().then((d) => {
        startPollingIfNeeded(d);
      }).catch(() => {});
    }
    return () => {
      stopPolling();
    };
  }, [opts.runId]);

  const startRun = useCallback(
    async (
      preset: string,
      mode: PipelineMode = "snapshot",
      max_records: number = 200,
    ): Promise<{ run_id: string }> => {
      setState((prev) => ({ ...prev, loading: true, error: undefined }));
      try {
        const result = await client.startRun({ preset, mode, max_records });
        runIdRef.current = result.run_id;
        setState((prev) => ({ ...prev, loading: false }));
        const detail = await client.getDetail(result.run_id);
        setState((prev) => ({ ...prev, detail }));
        startPollingIfNeeded(detail);
        return result;
      } catch (err) {
        setState((prev) => ({ ...prev, error: err, loading: false }));
        throw err;
      }
    },
    [client, startPollingIfNeeded],
  );

  const cancelRun = useCallback(async (): Promise<void> => {
    const id = runIdRef.current;
    if (!id) return;
    setState((prev) => ({ ...prev, loading: true, error: undefined }));
    try {
      await client.cancelRun(id);
      setState((prev) => ({ ...prev, loading: false }));
      stopPolling();
      const updated = await client.getDetail(id);
      setState((prev) => ({ ...prev, detail: updated }));
    } catch (err) {
      setState((prev) => ({ ...prev, error: err, loading: false }));
      throw err;
    }
  }, [client, stopPolling]);

  const retryStep = useCallback(
    async (step_idx: number, force: boolean = false): Promise<PipelineRunDetail> => {
      const id = runIdRef.current;
      if (!id) throw new Error("No active run");
      setState((prev) => ({ ...prev, loading: true, error: undefined }));
      try {
        const detail = await client.retryStep(id, step_idx, { force });
        setState((prev) => ({ ...prev, detail, loading: false }));
        startPollingIfNeeded(detail);
        return detail;
      } catch (err) {
        setState((prev) => ({ ...prev, error: err, loading: false }));
        throw err;
      }
    },
    [client, startPollingIfNeeded],
  );

  const refresh = useCallback(async (): Promise<
    PipelineRunDetail | undefined
  > => {
    return await fetchDetail();
  }, [fetchDetail]);

  const listRuns = useCallback(
    async (params: PipelineListParams = {}): Promise<PipelineRunSummary[]> => {
      setState((prev) => ({ ...prev, loading: true, error: undefined }));
      try {
        const runs = await client.listRuns(params);
        setState((prev) => ({ ...prev, runs, loading: false }));
        return runs;
      } catch (err) {
        setState((prev) => ({ ...prev, error: err, loading: false }));
        throw err;
      }
    },
    [client],
  );

  useEffect(() => {
    startPollingIfNeeded(state.detail);
  }, [state.detail?.status, startPollingIfNeeded]);

  return {
    startRun,
    cancelRun,
    retryStep,
    refresh,
    listRuns,
    state,
  };
}
