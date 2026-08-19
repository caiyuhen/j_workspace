import React, { useCallback, useState, useRef } from "react";
import type {
  EvidenceArtifact,
  FunnelStepStat,
  EvidenceStage,
  EvidenceDecision,
} from "@meda/shared-sdk";

export interface InjectFetchClient {
  list: (q?: unknown) => Promise<EvidenceArtifact[]>;
  decide: (payload: {
    literatureRecordId: string;
    stage: EvidenceStage;
    decision: EvidenceDecision;
    [key: string]: unknown;
  }) => Promise<EvidenceArtifact>;
  funnelStats: (projectId: string | number) => Promise<FunnelStepStat[]>;
  robEval: (id: string, p?: unknown) => Promise<unknown>;
  abstractorRun: (batch: unknown, llm?: unknown) => Promise<unknown>;
  bulkDecide: (arr: unknown[]) => Promise<unknown>;
  exportCSV: (ids: string[]) => Promise<EvidenceArtifact[]>;
  undo: (lastSnapshot: unknown) => Promise<unknown>;
  resetAll: (projectId: string | number) => Promise<unknown>;
}

export interface UseEvidenceArtifactOptions {
  literatureRecordId: string | number;
  injectFetchClient?: Partial<InjectFetchClient>;
}

export interface UseEvidenceArtifactState {
  items: EvidenceArtifact[];
  funnel: FunnelStepStat[];
}

export interface UseEvidenceArtifactReturn {
  list: () => Promise<EvidenceArtifact[]>;
  decide: (payload: {
    literatureRecordId: string;
    stage: EvidenceStage;
    decision: EvidenceDecision;
    [key: string]: unknown;
  }) => Promise<EvidenceArtifact>;
  bulkDecide: (arr: unknown[]) => Promise<unknown>;
  funnelStats: () => Promise<FunnelStepStat[]>;
  rob2Evaluate: (study_id: string) => Promise<unknown>;
  abstractorRunPipeline: () => Promise<unknown>;
  exportAsCSV: (ids: string[]) => Promise<string>;
  undo: () => Promise<unknown>;
  reset: () => Promise<unknown>;
  state: UseEvidenceArtifactState;
}

function _defaultList(): Promise<EvidenceArtifact[]> {
  return Promise.resolve([]);
}

function _defaultDecide(): Promise<EvidenceArtifact> {
  return Promise.resolve({} as EvidenceArtifact);
}

function _defaultFunnelStats(): Promise<FunnelStepStat[]> {
  return Promise.resolve([]);
}

function _default(): Promise<unknown> {
  return Promise.resolve(undefined);
}

function _defaultExportCSV(): Promise<EvidenceArtifact[]> {
  return Promise.resolve([]);
}

export function useEvidenceArtifact(
  opts: UseEvidenceArtifactOptions,
): UseEvidenceArtifactReturn {
  const [state, setState] = useState<UseEvidenceArtifactState>({
    items: [],
    funnel: [],
  });
  const historyRef = useRef<EvidenceArtifact[][]>([]);

  const client: InjectFetchClient = {
    list: opts.injectFetchClient?.list ?? _defaultList,
    decide: opts.injectFetchClient?.decide ?? _defaultDecide,
    funnelStats: opts.injectFetchClient?.funnelStats ?? _defaultFunnelStats,
    robEval: opts.injectFetchClient?.robEval ?? _default,
    abstractorRun: opts.injectFetchClient?.abstractorRun ?? _default,
    bulkDecide: opts.injectFetchClient?.bulkDecide ?? _default,
    exportCSV: opts.injectFetchClient?.exportCSV ?? _defaultExportCSV,
    undo: opts.injectFetchClient?.undo ?? _default,
    resetAll: opts.injectFetchClient?.resetAll ?? _default,
  };

  const list = useCallback(async (): Promise<EvidenceArtifact[]> => {
    const items = await client.list();
    historyRef.current.push([...state.items]);
    setState((prev) => ({ ...prev, items }));
    return items;
  }, [client, state.items]);

  const decide = useCallback(
    async (payload: {
      literatureRecordId: string;
      stage: EvidenceStage;
      decision: EvidenceDecision;
      [key: string]: unknown;
    }): Promise<EvidenceArtifact> => {
      const result = await client.decide(payload);
      historyRef.current.push([...state.items]);
      setState((prev) => {
        const exists = prev.items.findIndex(
          (x) =>
            x.literature_record_id === payload.literatureRecordId &&
            x.stage === payload.stage,
        );
        const nextItems = [...prev.items];
        if (exists >= 0) {
          nextItems[exists] = result;
        } else {
          nextItems.push(result);
        }
        return { ...prev, items: nextItems };
      });
      return result;
    },
    [client, state.items],
  );

  const bulkDecide = useCallback(
    async (arr: unknown[]): Promise<unknown> => {
      return await client.bulkDecide(arr);
    },
    [client],
  );

  const funnelStats = useCallback(async (): Promise<FunnelStepStat[]> => {
    const funnel = await client.funnelStats(opts.literatureRecordId);
    setState((prev) => ({ ...prev, funnel }));
    return funnel;
  }, [client, opts.literatureRecordId]);

  const rob2Evaluate = useCallback(
    async (study_id: string): Promise<unknown> => {
      return await client.robEval(study_id);
    },
    [client],
  );

  const abstractorRunPipeline = useCallback(
    async (): Promise<unknown> => {
      return await client.abstractorRun({ batch: 10 });
    },
    [client],
  );

  const exportAsCSV = useCallback(
    async (ids: string[]): Promise<string> => {
      const records = await client.exportCSV(ids);
      const header = "record_id,stage,decision\n";
      const rows = records
        .map(
          (ea) =>
            `${ea.literature_record_id},${ea.stage},${ea.decision}`,
        )
        .join("\n");
      return header + (rows ? rows + "\n" : "");
    },
    [client],
  );

  const undo = useCallback(async (): Promise<unknown> => {
    const lastSnapshot = state.items;
    const result = await client.undo(lastSnapshot);
    const prevState = historyRef.current.pop() ?? [];
    setState((prev) => ({ ...prev, items: prevState }));
    return result;
  }, [client, state.items]);

  const reset = useCallback(async (): Promise<unknown> => {
    const result = await client.resetAll(opts.literatureRecordId);
    historyRef.current = [];
    setState({ items: [], funnel: [] });
    return result;
  }, [client, opts.literatureRecordId]);

  return {
    list,
    decide,
    bulkDecide,
    funnelStats,
    rob2Evaluate,
    abstractorRunPipeline,
    exportAsCSV,
    undo,
    reset,
    state,
  };
}
