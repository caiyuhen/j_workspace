import React, { useState, useEffect, useMemo } from "react";
import {
  usePipelineRun,
  type InjectPipelineRunClient,
} from "../hooks/usePipelineRun";
import type { PipelineRunSummary, PipelineRunStatus } from "@meda/shared-sdk";
import { NewRunModal } from "../components/NewRunModal";

const PRESETS: string[] = [
  "sglt2i_ckd",
  "empagliflozin_hf",
  "glp1_weightloss",
  "liraglutide_nafld",
  "pkd_tolvaptan",
  "ckd_blood_pressure_control",
];

const STATUS_OPTIONS: (PipelineRunStatus | "all")[] = [
  "all",
  "queued",
  "running",
  "success",
  "failed",
  "resumable",
  "cancelled",
  "partial",
];

const PER_PAGE_OPTIONS = [10, 20, 50];

export interface PipelineRunsListPageProps {
  workspaceId: string;
  injectFetchClient?: Partial<InjectPipelineRunClient>;
  onNavigateToDetail: (run_id: string) => void;
  onNavigateToCompare: (aId: string, bId: string) => void;
}

function statusStyle(status: PipelineRunStatus): {
  bg: string;
  color: string;
  label: string;
  italic?: boolean;
  cls: string;
} {
  switch (status) {
    case "success":
      return { bg: "#d1fae5", color: "#065f46", label: "✓ success", cls: "status-success" };
    case "running":
      return { bg: "#dbeafe", color: "#1e40af", label: "● running", cls: "status-running" };
    case "failed":
      return { bg: "#fee2e2", color: "#991b1b", label: "✗ failed", cls: "status-failed" };
    case "queued":
      return { bg: "#f3f4f6", color: "#4b5563", label: "⏳ queued", cls: "status-queued" };
    case "cancelled":
      return { bg: "#f3f4f6", color: "#6b7280", label: "⊘ cancelled", italic: true, cls: "status-cancelled" };
    case "partial":
      return { bg: "#fef3c7", color: "#92400e", label: "⚠ partial", cls: "status-partial" };
    case "resumable":
      return { bg: "#ede9fe", color: "#5b21b6", label: "↻ resumable", cls: "status-resumable" };
    case "paused":
      return { bg: "#fef9c3", color: "#854d0e", label: "⏸ paused", cls: "status-paused" };
  }
}

function formatDuration(ms: number | null): string {
  if (ms === null || typeof ms !== "number") return "—";
  const totalSec = Math.floor(ms / 1000);
  const m = Math.floor(totalSec / 60);
  const s = totalSec % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

function formatCreated(iso: string): string {
  try {
    const d = new Date(iso);
    const mm = (d.getMonth() + 1).toString().padStart(2, "0");
    const dd = d.getDate().toString().padStart(2, "0");
    const hh = d.getHours().toString().padStart(2, "0");
    const mi = d.getMinutes().toString().padStart(2, "0");
    return `${mm}-${dd} ${hh}:${mi}`;
  } catch {
    return iso;
  }
}

function computeDurationFromTimestamps(summary: PipelineRunSummary): number | null {
  if (summary.duration_ms !== null && summary.duration_ms !== undefined) {
    return summary.duration_ms;
  }
  if (summary.finished_at && summary.created_at) {
    try {
      return new Date(summary.finished_at).getTime() - new Date(summary.created_at).getTime();
    } catch {
      return null;
    }
  }
  return null;
}

function build8Dots(summary: PipelineRunSummary): Array<{ color: string; label: string }> {
  const current = summary.current_step_index ?? 0;
  const status = summary.status;
  const dots: Array<{ color: string; label: string }> = [];
  for (let i = 0; i < 8; i++) {
    let color = "#d1d5db";
    let label = "pending";
    if (status === "success") {
      color = "#10b981";
      label = "success";
    } else if (status === "failed" && i <= current) {
      color = i === current ? "#ef4444" : "#10b981";
      label = i === current ? "failed" : "success";
    } else if (status === "partial") {
      if (i < current) {
        color = "#10b981";
        label = "success";
      } else if (i === current) {
        color = "#f59e0b";
        label = "partial";
      }
    } else if (i < current) {
      color = "#10b981";
      label = "success";
    } else if (i === current && (status === "running" || status === "queued" || status === "resumable")) {
      color = "#3b82f6";
      label = "running";
    }
    dots.push({ color, label });
  }
  return dots;
}

export function PipelineRunsListPage(props: PipelineRunsListPageProps): JSX.Element {
  const { workspaceId, injectFetchClient, onNavigateToDetail, onNavigateToCompare } = props;
  const pipeline = usePipelineRun({ workspaceId, injectFetchClient });

  const [presetFilter, setPresetFilter] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<PipelineRunStatus | "all">("all");
  const [page, setPage] = useState<number>(1);
  const [perPage, setPerPage] = useState<number>(20);
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [rerunPreset, setRerunPreset] = useState<string | undefined>(undefined);
  const [rerunMax, setRerunMax] = useState<number | undefined>(undefined);

  useEffect(() => {
    const params: any = { page, per_page: perPage, sort: "created_at DESC" };
    if (presetFilter) params.preset = presetFilter;
    if (statusFilter !== "all") params.status = statusFilter;
    pipeline.listRuns(params);
  }, [presetFilter, statusFilter, page, perPage]);

  const allRuns = useMemo(() => {
    const runs = [...(pipeline.state.runs || [])];
    runs.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    return runs;
  }, [pipeline.state.runs]);

  const totalPages = Math.max(1, Math.ceil(allRuns.length / perPage));
  const currentPageRuns = allRuns.slice((page - 1) * perPage, page * perPage);

  const handleNewRun = () => {
    setRerunPreset(undefined);
    setRerunMax(undefined);
    setModalOpen(true);
  };

  const handleRerun = (run: PipelineRunSummary) => {
    setRerunPreset(run.preset);
    setRerunMax(run.max_records);
    setModalOpen(true);
  };

  const handleConfirm = async (payload: {
    preset: string;
    mode: "snapshot" | "live";
    max_records: number;
  }) => {
    setModalOpen(false);
    await pipeline.startRun(payload.preset, payload.mode, payload.max_records);
    const params: any = { page, per_page: perPage, sort: "created_at DESC" };
    if (presetFilter) params.preset = presetFilter;
    if (statusFilter !== "all") params.status = statusFilter;
    pipeline.listRuns(params);
  };

  return (
    <div data-testid="pipeline-runs-list-page" style={{ padding: 24, background: "#f9fafb", minHeight: "100vh" }}>
      <NewRunModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onConfirm={handleConfirm}
        initialPreset={rerunPreset}
        initialMaxRecords={rerunMax}
      />

      <div
        data-testid="top-bar"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 16,
          marginBottom: 20,
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: 1, minWidth: 0 }}>
          <div
            data-testid="filter-preset-chips"
            style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}
          >
            <button
              data-testid="preset-filter-all"
              onClick={() => setPresetFilter(null)}
              style={{
                padding: "6px 14px",
                borderRadius: 999,
                border: `1px solid ${presetFilter === null ? "#2563eb" : "#d1d5db"}`,
                background: presetFilter === null ? "#dbeafe" : "#ffffff",
                color: presetFilter === null ? "#1e40af" : "#374151",
                fontSize: 12,
                fontWeight: presetFilter === null ? 700 : 500,
                cursor: "pointer",
              }}
            >
              All
            </button>
            {PRESETS.map((p) => (
              <button
                key={p}
                data-testid={`preset-filter-${p}`}
                onClick={() => setPresetFilter(presetFilter === p ? null : p)}
                style={{
                  padding: "6px 14px",
                  borderRadius: 999,
                  border: `1px solid ${presetFilter === p ? "#2563eb" : "#d1d5db"}`,
                  background: presetFilter === p ? "#dbeafe" : "#ffffff",
                  color: presetFilter === p ? "#1e40af" : "#374151",
                  fontSize: 12,
                  fontWeight: presetFilter === p ? 700 : 500,
                  cursor: "pointer",
                }}
              >
                {p}
              </button>
            ))}
          </div>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <label style={{ fontSize: 13, color: "#4b5563", fontWeight: 500 }}>Status:</label>
            <select
              data-testid="status-select"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value as PipelineRunStatus | "all");
                setPage(1);
              }}
              style={{
                padding: "6px 10px",
                borderRadius: 6,
                border: "1px solid #d1d5db",
                fontSize: 13,
                background: "#ffffff",
              }}
            >
              {STATUS_OPTIONS.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          data-testid="btn-new-run"
          onClick={handleNewRun}
          style={{
            padding: "10px 20px",
            borderRadius: 8,
            border: "none",
            background: "#2563eb",
            color: "#ffffff",
            fontSize: 14,
            fontWeight: 700,
            cursor: "pointer",
            whiteSpace: "nowrap",
          }}
        >
          🔘 + 启动新 Run
        </button>
      </div>

      {pipeline.state.loading && allRuns.length === 0 ? (
        <div
          data-testid="loading-spinner"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: 60,
            fontSize: 14,
            color: "#6b7280",
          }}
        >
          <span style={{ display: "inline-block", animation: "spin 1s linear infinite", marginRight: 8 }}>⏳</span>
          Loading pipeline runs...
        </div>
      ) : allRuns.length === 0 ? (
        <div
          data-testid="empty-state"
          style={{
            padding: 80,
            textAlign: "center",
            background: "#ffffff",
            borderRadius: 12,
            border: "1px dashed #d1d5db",
            color: "#6b7280",
            fontSize: 15,
          }}
        >
          暂无 Pipeline Run — 点右上 🔘 启动新 Run
        </div>
      ) : (
        <>
          <div
            style={{
              background: "#ffffff",
              borderRadius: 12,
              border: "1px solid #e5e7eb",
              overflow: "hidden",
            }}
          >
            <div
              data-testid="runs-table"
              style={{ width: "100%", overflowX: "auto" }}
            >
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead>
                  <tr style={{ background: "#f9fafb", borderBottom: "1px solid #e5e7eb" }}>
                    <th style={TH_STYLE}>🔗 ID</th>
                    <th style={TH_STYLE}>Preset</th>
                    <th style={TH_STYLE}>Mode</th>
                    <th style={TH_STYLE}>N Rec</th>
                    <th style={TH_STYLE}>Status</th>
                    <th style={TH_STYLE}>Progress</th>
                    <th style={TH_STYLE}>Created</th>
                    <th style={TH_STYLE}>Duration</th>
                    <th style={TH_STYLE}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {currentPageRuns.map((run) => {
                    const sStyle = statusStyle(run.status);
                    const durationMs = computeDurationFromTimestamps(run);
                    const dots = build8Dots(run);
                    return (
                      <tr
                        key={run.run_id}
                        data-testid={`table-row-${run.run_id}`}
                        style={{ borderBottom: "1px solid #f3f4f6" }}
                      >
                        <td style={TD_STYLE}>
                          <span style={{ fontFamily: "monospace", color: "#2563eb", fontWeight: 600 }}>
                            🔗 {run.run_id}
                          </span>
                        </td>
                        <td style={TD_STYLE}>
                          <code style={{ background: "#f3f4f6", padding: "2px 6px", borderRadius: 4, fontSize: 12 }}>
                            {run.preset}
                          </code>
                        </td>
                        <td style={TD_STYLE}>
                          {run.mode === "snapshot" ? (
                            <span
                              data-testid={`mode-badge-snapshot-${run.run_id}`}
                              className="mode-snapshot-badge"
                              style={{
                                display: "inline-block",
                                padding: "3px 10px",
                                borderRadius: 999,
                                fontSize: 11,
                                fontWeight: 700,
                                background: "#dbeafe",
                                color: "#1e40af",
                                border: "1px solid #93c5fd",
                              }}
                            >
                              🔵 snapshot
                            </span>
                          ) : (
                            <span
                              data-testid={`mode-badge-live-${run.run_id}`}
                              className="mode-live-badge"
                              style={{
                                display: "inline-block",
                                padding: "3px 10px",
                                borderRadius: 999,
                                fontSize: 11,
                                fontWeight: 700,
                                background: "#dcfce7",
                                color: "#166534",
                                border: "1px solid #86efac",
                              }}
                            >
                              🟢 live
                            </span>
                          )}
                        </td>
                        <td style={TD_STYLE}>{run.max_records}</td>
                        <td style={TD_STYLE}>
                          <span
                            data-testid={`status-badge-${run.run_id}`}
                            className={sStyle.cls}
                            style={{
                              display: "inline-block",
                              padding: "3px 10px",
                              borderRadius: 999,
                              fontSize: 11,
                              fontWeight: 700,
                              background: sStyle.bg,
                              color: sStyle.color,
                              fontStyle: sStyle.italic ? "italic" : "normal",
                            }}
                          >
                            {sStyle.label}
                          </span>
                        </td>
                        <td style={TD_STYLE}>
                          <div
                            data-testid={`progress-dots-${run.run_id}`}
                            style={{ display: "flex", gap: 4 }}
                          >
                            {dots.map((d, i) => (
                              <span
                                key={i}
                                data-testid={`progress-dot-${run.run_id}-${i}`}
                                title={d.label}
                                style={{
                                  display: "inline-block",
                                  width: 10,
                                  height: 10,
                                  borderRadius: "50%",
                                  background: d.color,
                                  border: d.color === "#d1d5db" ? "1px solid #9ca3af" : "none",
                                }}
                              />
                            ))}
                          </div>
                        </td>
                        <td style={TD_STYLE}>
                          <span style={{ color: "#6b7280", fontSize: 12 }}>{formatCreated(run.created_at)}</span>
                        </td>
                        <td style={TD_STYLE}>
                          <span
                            data-testid={`duration-${run.run_id}`}
                            style={{ fontFamily: "monospace", color: "#374151" }}
                          >
                            {formatDuration(durationMs)}
                          </span>
                        </td>
                        <td style={{ ...TD_STYLE, whiteSpace: "nowrap" }}>
                          <button
                            data-testid={`btn-detail-${run.run_id}`}
                            onClick={() => onNavigateToDetail(run.run_id)}
                            style={BTN_LINK_STYLE}
                          >
                            详情 →
                          </button>
                          <button
                            data-testid={`btn-rerun-${run.run_id}`}
                            onClick={() => handleRerun(run)}
                            style={{ ...BTN_LINK_STYLE, color: "#2563eb" }}
                          >
                            ⟲ 重跑
                          </button>
                          <button
                            data-testid={`btn-csv-${run.run_id}`}
                            disabled={run.status !== "success"}
                            style={{
                              ...BTN_LINK_STYLE,
                              color: run.status === "success" ? "#059669" : "#9ca3af",
                              cursor: run.status === "success" ? "pointer" : "not-allowed",
                              opacity: run.status === "success" ? 1 : 0.5,
                            }}
                          >
                            ⬇ CSV
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>

          <div
            data-testid="pagination"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginTop: 16,
              padding: "0 4px",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <label style={{ fontSize: 12, color: "#6b7280" }}>Per page:</label>
              <select
                data-testid="per-page-select"
                value={perPage}
                onChange={(e) => {
                  setPerPage(Number(e.target.value));
                  setPage(1);
                }}
                style={{
                  padding: "4px 8px",
                  borderRadius: 6,
                  border: "1px solid #d1d5db",
                  fontSize: 12,
                }}
              >
                {PER_PAGE_OPTIONS.map((n) => (
                  <option key={n} value={n}>
                    {n}
                  </option>
                ))}
              </select>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <button
                data-testid="btn-prev-page"
                disabled={page <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid #d1d5db",
                  background: page <= 1 ? "#f3f4f6" : "#ffffff",
                  color: page <= 1 ? "#9ca3af" : "#374151",
                  cursor: page <= 1 ? "not-allowed" : "pointer",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                ◀
              </button>
              <span
                data-testid="page-indicator"
                style={{ fontSize: 13, color: "#374151", fontWeight: 600, minWidth: 50, textAlign: "center" }}
              >
                {page}/{totalPages}
              </span>
              <button
                data-testid="btn-next-page"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid #d1d5db",
                  background: page >= totalPages ? "#f3f4f6" : "#ffffff",
                  color: page >= totalPages ? "#9ca3af" : "#374151",
                  cursor: page >= totalPages ? "not-allowed" : "pointer",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                ▶
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

const TH_STYLE: React.CSSProperties = {
  padding: "10px 14px",
  textAlign: "left",
  fontSize: 11,
  fontWeight: 700,
  color: "#4b5563",
  textTransform: "uppercase",
  letterSpacing: "0.02em",
  whiteSpace: "nowrap",
};

const TD_STYLE: React.CSSProperties = {
  padding: "12px 14px",
  fontSize: 13,
  color: "#111827",
  verticalAlign: "middle",
};

const BTN_LINK_STYLE: React.CSSProperties = {
  padding: "4px 8px",
  border: "none",
  background: "transparent",
  fontSize: 12,
  fontWeight: 600,
  cursor: "pointer",
  marginRight: 4,
};
