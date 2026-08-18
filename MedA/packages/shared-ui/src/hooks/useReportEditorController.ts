import React, { useCallback, useReducer } from "react";
import type { Report8ChaptersDraft, ReportGeneratePayload } from "@meda/shared-sdk";
import { parseSnapshotInto8Chapters } from "../components/ReportContentEditor8";

export type ReportEditorAction =
  | { type: "draft_field_update"; field: keyof Report8ChaptersDraft; value: string }
  | { type: "draft_replace_all"; next: Report8ChaptersDraft }
  | { type: "source_snapshot_set"; id: number | null }
  | { type: "upstream_data_set"; data: Partial<Report8ChaptersDraft> }
  | { type: "tab_change"; next: "editor" | "md" | "html" }
  | { type: "error_set"; detail: string | null }
  | { type: "sha_set"; sha: string | null; versionLabel: string | null; generatedAt: string | null }
  | { type: "generate_pending" }
  | { type: "export_pending" }
  | { type: "reset" };

export type ReportEditorState = {
  draft: Report8ChaptersDraft;
  dirty: Set<keyof Report8ChaptersDraft>;
  sourceSnapshotId: number | null;
  upstreamData: Partial<Report8ChaptersDraft>;
  snapshot: {
    sha: string | null;
    versionLabel: string | null;
    generatedAt: string | null;
    mdContent: string | null;
    htmlContent: string | null;
    txtContent: string | null;
  };
  activeTab: "editor" | "md" | "html";
  errorDetail: string | null;
  generating: boolean;
  exporting: boolean;
};

export type FetchClient = {
  post: <Resp = unknown>(url: string, body: unknown) => Promise<Resp>;
  get?: <Resp = unknown>(url: string) => Promise<Resp>;
};

const EMPTY_DRAFT: Report8ChaptersDraft = {
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

const CHAPTER_OVERRIDE_PREFIX: Record<string, keyof ReportGeneratePayload> = {
  ch1_background: "override_ch1_background",
  ch2_methods: "override_ch2_methods",
  ch3_pico: "override_ch3_pico",
  ch4_results: "override_ch4_results",
  ch5_grade_assessment: "override_ch5_grade_assessment",
  ch6_summary_of_findings: "override_ch6_summary_of_findings",
  ch7_discussion: "override_ch7_discussion",
  ch8_appendices: "override_ch8_appendices",
};

const _CHAPTER_KEYS: Array<keyof Omit<Report8ChaptersDraft, "source_snapshot_id">> = [
  "ch1_background",
  "ch2_methods",
  "ch3_pico",
  "ch4_results",
  "ch5_grade_assessment",
  "ch6_summary_of_findings",
  "ch7_discussion",
  "ch8_appendices",
];

type CreateInitialOpts = {
  initialDraft?: Partial<Report8ChaptersDraft>;
  initialSnapshotId?: number | null;
  initialUpstreamData?: Partial<Report8ChaptersDraft>;
};

function _createInitialState(opts: CreateInitialOpts): ReportEditorState {
  const draft: Report8ChaptersDraft = { ...EMPTY_DRAFT };
  if (opts.initialDraft) {
    for (const k of _CHAPTER_KEYS) {
      if (opts.initialDraft[k] !== undefined) draft[k] = opts.initialDraft[k] as string;
    }
    if (opts.initialDraft.source_snapshot_id !== undefined) {
      draft.source_snapshot_id = opts.initialDraft.source_snapshot_id;
    }
  }
  return {
    draft,
    dirty: new Set<keyof Report8ChaptersDraft>(),
    sourceSnapshotId: opts.initialSnapshotId ?? null,
    upstreamData: opts.initialUpstreamData ?? {},
    snapshot: {
      sha: null,
      versionLabel: null,
      generatedAt: null,
      mdContent: null,
      htmlContent: null,
      txtContent: null,
    },
    activeTab: "editor",
    errorDetail: null,
    generating: false,
    exporting: false,
  };
}

function reducer(state: ReportEditorState, action: ReportEditorAction): ReportEditorState {
  switch (action.type) {
    case "draft_field_update": {
      const nextDraft = { ...state.draft, [action.field]: action.value };
      const nextDirty = new Set(state.dirty);
      if (action.field !== "source_snapshot_id") {
        nextDirty.add(action.field);
      }
      return { ...state, draft: nextDraft, dirty: nextDirty };
    }
    case "draft_replace_all": {
      return { ...state, draft: { ...action.next } };
    }
    case "source_snapshot_set": {
      return { ...state, sourceSnapshotId: action.id };
    }
    case "upstream_data_set": {
      return { ...state, upstreamData: { ...action.data } };
    }
    case "tab_change": {
      return { ...state, activeTab: action.next };
    }
    case "error_set": {
      return {
        ...state,
        errorDetail: action.detail,
        generating: false,
        exporting: false,
      };
    }
    case "sha_set": {
      return {
        ...state,
        generating: false,
        snapshot: {
          ...state.snapshot,
          sha: action.sha,
          versionLabel: action.versionLabel,
          generatedAt: action.generatedAt,
        },
      };
    }
    case "generate_pending": {
      return { ...state, generating: true, errorDetail: null };
    }
    case "export_pending": {
      return { ...state, exporting: true, errorDetail: null };
    }
    case "reset": {
      return _createInitialState({});
    }
    default:
      return state;
  }
}

export function useReportEditorController(opts: {
  projectId: number;
  fetchClient: FetchClient;
  initialDraft?: Partial<Report8ChaptersDraft>;
  initialSnapshotId?: number | null;
  initialUpstreamData?: Partial<Report8ChaptersDraft>;
}) {
  const [state, dispatch] = useReducer(reducer, opts, _createInitialState);

  const onFieldChange = useCallback(
    (field: keyof Report8ChaptersDraft, value: string) => {
      dispatch({ type: "draft_field_update", field, value });
    },
    [],
  );

  const generateFromUpstream = useCallback((upstreamSnapshotMd: string) => {
    try {
      const parsed = parseSnapshotInto8Chapters(upstreamSnapshotMd);
      dispatch({ type: "draft_replace_all", next: parsed });
      dispatch({ type: "error_set", detail: null });
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      dispatch({ type: "error_set", detail: msg });
    }
  }, []);

  const restoreLatestSnapshot = useCallback(() => {
    const md = state.snapshot.mdContent;
    if (!md) return;
    try {
      const parsed = parseSnapshotInto8Chapters(md);
      dispatch({ type: "draft_replace_all", next: parsed });
      dispatch({ type: "source_snapshot_set", id: null });
    } catch (_e) {
      /* no-op on parse error during restore */
    }
  }, [state.snapshot.mdContent]);

  const generateReport = useCallback(async (): Promise<{
    ok: boolean;
    sha?: string | null;
    detail?: string | null;
  }> => {
    dispatch({ type: "generate_pending" });
    const payload: ReportGeneratePayload & { version_label: string } = {
      version_label: "manual-" + String(Date.now()).slice(-6),
    };
    for (const field of state.dirty) {
      if (field === "source_snapshot_id") continue;
      const val = state.draft[field];
      if (typeof val !== "string") continue;
      if (val === "") continue;
      const overrideKey = CHAPTER_OVERRIDE_PREFIX[field];
      if (overrideKey) {
        (payload as Record<string, string>)[overrideKey] = val;
      }
    }
    try {
      const url = `/api/v1/workspaces/projects/${opts.projectId}/report/generate`;
      const resp = await opts.fetchClient.post<{
        sha?: string;
        version_label?: string;
        generated_at?: string;
        detail?: string;
      }>(url, payload);
      const sha = resp?.sha ?? null;
      const versionLabel = resp?.version_label ?? null;
      const generatedAt = resp?.generated_at ?? null;
      dispatch({
        type: "sha_set",
        sha,
        versionLabel,
        generatedAt,
      });
      dispatch({ type: "error_set", detail: null });
      return { ok: true, sha };
    } catch (e: unknown) {
      let detail: string | null = null;
      const anyErr = e as { response?: { detail?: string }; detail?: string };
      if (anyErr.detail) {
        detail = anyErr.detail;
      } else if (anyErr.response?.detail) {
        detail = anyErr.response.detail;
      } else if (e instanceof Error) {
        detail = e.message;
      }
      dispatch({ type: "error_set", detail });
      return { ok: false, sha: null, detail };
    }
  }, [opts.projectId, opts.fetchClient, state.dirty, state.draft]);

  const exportReport = useCallback(
    async (format: "md" | "html" | "txt"): Promise<{
      ok: boolean;
      content?: string | null;
      detail?: string | null;
    }> => {
      dispatch({ type: "export_pending" });
      try {
        const url = `/api/v1/workspaces/projects/${opts.projectId}/report/export/${format}`;
        const resp = await opts.fetchClient.post<{
          content?: string;
          detail?: string;
        }>(url, { format });
        const content = resp?.content ?? null;
        dispatch({ type: "error_set", detail: null });
        return { ok: true, content };
      } catch (e: unknown) {
        let detail: string | null = null;
        const anyErr = e as { response?: { detail?: string }; detail?: string };
        if (anyErr.detail) {
          detail = anyErr.detail;
        } else if (anyErr.response?.detail) {
          detail = anyErr.response.detail;
        } else if (e instanceof Error) {
          detail = e.message;
        }
        dispatch({ type: "error_set", detail });
        return { ok: false, content: null, detail };
      }
    },
    [opts.projectId, opts.fetchClient],
  );

  const reset = useCallback(() => {
    dispatch({ type: "reset" });
  }, []);

  return {
    state,
    dispatch,
    generateFromUpstream,
    restoreLatestSnapshot,
    generateReport,
    exportReport,
    reset,
    onFieldChange,
    dirtyFields: state.dirty,
  };
}
