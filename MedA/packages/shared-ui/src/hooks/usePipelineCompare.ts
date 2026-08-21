import React, { useCallback, useState, useEffect } from "react";
import type { PipelineCompareResult } from "@meda/shared-sdk";

export interface InjectPipelineCompareClient {
  compare: (
    runAId: string,
    runBId: string,
    metrics: string,
  ) => Promise<PipelineCompareResult>;
}

export interface UsePipelineCompareOptions {
  workspaceId: string;
  runAId?: string;
  runBId?: string;
  metrics?: string;
  injectFetchClient?: Partial<InjectPipelineCompareClient>;
}

export interface UsePipelineCompareState {
  compareResult?: PipelineCompareResult;
  loading: boolean;
  error?: unknown;
}

export interface UsePipelineCompareReturn {
  compare: (
    aId: string,
    bId: string,
    metrics?: string,
  ) => Promise<PipelineCompareResult>;
  state: UsePipelineCompareState;
}

function _defaultCompare(): Promise<PipelineCompareResult> {
  return Promise.resolve({} as PipelineCompareResult);
}

function normalizeMetrics(metrics: string): string {
  return metrics
    .split(",")
    .map((m) => m.trim())
    .filter((m) => m.length > 0)
    .join(",");
}

export function usePipelineCompare(
  opts: UsePipelineCompareOptions,
): UsePipelineCompareReturn {
  const defaultMetrics = opts.metrics ?? "funnel,rob,grade,pico";

  const [state, setState] = useState<UsePipelineCompareState>({
    compareResult: undefined,
    loading: false,
    error: undefined,
  });

  const client: InjectPipelineCompareClient = {
    compare: opts.injectFetchClient?.compare ?? _defaultCompare,
  };

  const compare = useCallback(
    async (
      aId: string,
      bId: string,
      metrics?: string,
    ): Promise<PipelineCompareResult> => {
      const resolvedMetrics = normalizeMetrics(
        metrics ?? defaultMetrics,
      );
      setState((prev) => ({ ...prev, loading: true, error: undefined }));
      try {
        const result = await client.compare(aId, bId, resolvedMetrics);
        setState((prev) => ({ ...prev, compareResult: result, loading: false }));
        return result;
      } catch (err) {
        setState((prev) => ({ ...prev, error: err, loading: false }));
        throw err;
      }
    },
    [client, defaultMetrics],
  );

  useEffect(() => {
    if (opts.runAId && opts.runBId) {
      compare(opts.runAId, opts.runBId, defaultMetrics).catch(() => {});
    }
  }, [opts.runAId, opts.runBId]);

  return {
    compare,
    state,
  };
}
