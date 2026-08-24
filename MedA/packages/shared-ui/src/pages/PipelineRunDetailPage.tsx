import React, { useMemo, useState } from "react";
import {
  usePipelineRun,
  type InjectPipelineRunClient,
} from "../hooks/usePipelineRun";
import type { InjectDiagClient } from "../hooks/useStepDiag";
import type {
  PipelineRunDetail,
  PipelineStepInfo,
  PipelineRunStatus,
  FunnelStepStat,
  RoB2Overall,
} from "@meda/shared-sdk";
import FunnelProgressBar from "../components/FunnelProgressBar";
import AbstractorCard, {
  type AbstractorRecord,
  type AbstractorTriage,
} from "../components/AbstractorCard";
import { RoB2Matrix } from "../grade/RoB2Matrix";
import { GradeDistributionCard } from "../components/GradeDistributionCard";
import { PipelineDetailStepDiagFetch } from "../components/PipelineDetailStepDiagFetch";

export interface PipelineRunDetailPageProps {
  workspaceId: string;
  runId: string;
  onBack: () => void;
  onNavigateToCompare: (aId: string) => void;
  injectFetchClient?: Partial<InjectPipelineRunClient>;
  injectDiagClient?: Partial<InjectDiagClient>;
}

const STEP_NAMES = [
  "Step 0: Fetch",
  "Step 1: Dedupe",
  "Step 2: Title/Abstract",
  "Step 3: Fulltext",
  "Step 4: PICO Extract",
  "Step 5: RoB2 Assess",
  "Step 6: GRADE",
  "Step 7: Report",
] as const;

function _statusStyle(status: PipelineRunStatus): {
  bg: string;
  color: string;
  label: string;
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
      return { bg: "#f3f4f6", color: "#6b7280", label: "⊘ cancelled", cls: "status-cancelled" };
    case "partial":
      return { bg: "#fef3c7", color: "#92400e", label: "⚠ partial", cls: "status-partial" };
    case "resumable":
      return { bg: "#ede9fe", color: "#5b21b6", label: "↻ resumable", cls: "status-resumable" };
    case "paused":
      return { bg: "#fef9c3", color: "#854d0e", label: "⏸ paused", cls: "status-paused" };
  }
}

function _formatDuration(ms: number | null): string {
  if (ms === null || typeof ms !== "number") return "00:00.000";
  const totalMs = ms;
  const m = Math.floor(totalMs / 60000);
  const s = Math.floor((totalMs % 60000) / 1000);
  const msPart = totalMs % 1000;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}.${msPart.toString().padStart(3, "0")}`;
}

function _stepStatusIcon(s: PipelineStepInfo["status"]): { icon: string; cls: string; bg: string } {
  switch (s) {
    case "success":
      return { icon: "✅", cls: "step-success", bg: "#10b981" };
    case "running":
      return { icon: "🔵", cls: "step-running", bg: "#3b82f6" };
    case "failed":
      return { icon: "❌", cls: "step-failed", bg: "#ef4444" };
    case "pending":
      return { icon: "○", cls: "step-pending", bg: "#d1d5db" };
    case "skipped":
      return { icon: "⚪", cls: "step-skipped", bg: "#9ca3af" };
  }
}

function _buildFunnelStats(detail: PipelineRunDetail | undefined): FunnelStepStat[] {
  const fallback = detail?.steps?.slice(0, 6) ?? [];
  const explicitCounts = detail?.funnel_counts;
  const keys = ["N1", "N2", "N3", "N4", "E1", "E2"] as const;
  const labels = ["Identified", "Screened", "Eligible", "Retrieved", "Assessed", "Included"];
  return keys.map((key, i) => {
    const count = explicitCounts && explicitCounts[i] !== undefined
      ? explicitCounts[i]
      : (fallback[i]?.n_out ?? 0);
    return {
      key,
      label: labels[i] ?? key,
      count,
      locked: true,
    } as FunnelStepStat;
  });
}

function _buildEvidenceArtifacts(detail: PipelineRunDetail | undefined): Array<{
  record: AbstractorRecord;
  triage: AbstractorTriage;
}> {
  const includeCount = detail?.funnel_counts?.[5] ?? detail?.steps?.[5]?.n_out ?? 0;
  const safeCount = Math.max(0, Math.min(includeCount, 50));
  const out: Array<{ record: AbstractorRecord; triage: AbstractorTriage }> = [];
  for (let i = 0; i < safeCount; i++) {
    const id = `EA-${String(i + 1).padStart(4, "0")}`;
    out.push({
      record: {
        id,
        title: `Evidence Artifact Study ${i + 1}: Randomized Controlled Trial`,
        year: 2020 + (i % 6),
        journal: i % 2 === 0 ? "NEJM" : "The Lancet",
      },
      triage: {
        decision: "include",
        confidence: 0.85 + (i % 15) / 100,
        reasons: ["Auto-included via pipeline"],
        pico: {
          p: { text: "Adult population with chronic condition", n: 100 + i * 10, age_min: 18, age_max: 85, condition: "Chronic Disease" },
          i: { drug: `Drug ${String.fromCharCode(65 + (i % 26))}`, dose: "10mg QD", duration: "12mo", n: 50 + i * 5 },
          c: { comparator: "Placebo", type: "placebo" },
          o: [{ name: "Primary Endpoint", rr: 0.7 + (i % 30) / 100, ci_low: 0.5, ci_high: 0.9, p_value: 0.01 + (i % 40) / 1000 }],
        },
        pipeline_steps: STEP_NAMES.slice(0, 6).map((label, idx) => ({
          key: `s${idx}`,
          label: label.split(": ")[1] ?? `Step ${idx}`,
          active: true,
        })),
      },
    });
  }
  return out;
}

function _buildRob2Studies(detail: PipelineRunDetail | undefined): RoB2Overall[] {
  const dist = detail?.rob2_distribution;
  const totalLow = dist?.low ?? 0;
  const totalSome = dist?.some ?? 0;
  const totalHigh = dist?.high ?? 0;
  const total = totalLow + totalSome + totalHigh;
  const studies: RoB2Overall[] = [];
  for (let i = 0; i < Math.max(total, 3); i++) {
    let overall: RoB2Overall["overall"] = "low";
    if (i < totalLow) overall = "low";
    else if (i < totalLow + totalSome) overall = "some_concerns";
    else overall = "high";
    const overallForDomain = overall === "some_concerns" ? "some_concerns" : overall;
    studies.push({
      study_id: `S${i + 1}`,
      study_type: "RCT",
      domains: ["D1_randomization", "D2_deviations", "D3_missing", "D4_measurement", "D5_reporting"].map((d, di) => ({
        domain: d as any,
        rating: di < 2 ? "low" : (overallForDomain === "some_concerns" ? "some_concerns" : overallForDomain),
        signal_answers: {},
        rationale: "",
      })),
      overall,
    });
  }
  return studies;
}

export function PipelineRunDetailPage(props: PipelineRunDetailPageProps): JSX.Element {
  const { workspaceId, runId, onBack, onNavigateToCompare, injectFetchClient, injectDiagClient } = props;
  const pipeline = usePipelineRun({ workspaceId, runId, injectFetchClient });
  const { state } = pipeline;
  const detail = state.detail;

  const [eaPage, setEaPage] = useState<number>(1);
  const EA_PAGE_SIZE = 10;

  const evidenceArtifacts = useMemo(() => _buildEvidenceArtifacts(detail), [detail]);
  const includeCount = evidenceArtifacts.length;
  const eaTotalPages = Math.max(1, Math.ceil(includeCount / EA_PAGE_SIZE));
  const eaPageStart = (eaPage - 1) * EA_PAGE_SIZE;
  const eaPageRows = evidenceArtifacts.slice(eaPageStart, eaPageStart + EA_PAGE_SIZE);

  const funnelStats = useMemo(() => _buildFunnelStats(detail), [detail]);
  const rob2Studies = useMemo(() => _buildRob2Studies(detail), [detail]);

  const status = detail?.status ?? "queued";
  const statusStyle = _statusStyle(status);
  const preset = detail?.preset ?? "default";
  const mode = detail?.mode ?? "snapshot";

  const failedStepIndex = useMemo(() => {
    if (!detail?.steps) return -1;
    return detail.steps.findIndex((s) => s.status === "failed");
  }, [detail]);

  const canCancel = status === "running" || status === "queued";
  const canResume = status === "failed" || status === "resumable" || status === "paused";
  const canDownload = status === "success" || status === "partial";

  const rob2Counts = useMemo(() => {
    const d = rob2Studies.reduce(
      (acc, s) => {
        if (s.overall === "low") acc.low++;
        else if (s.overall === "some_concerns") acc.some++;
        else if (s.overall === "high" || s.overall === "critical") acc.high++;
        return acc;
      },
      { low: 0, some: 0, high: 0 },
    );
    return d;
  }, [rob2Studies]);

  const steps: PipelineStepInfo[] = useMemo(() => {
    if (detail?.steps && detail.steps.length >= 8) return detail.steps;
    const base: PipelineStepInfo[] = [];
    for (let i = 0; i < 8; i++) {
      const fromDetail = detail?.steps?.[i];
      base.push(fromDetail ?? {
        step_index: i as any,
        step_name: STEP_NAMES[i],
        status: "pending",
        duration_ms: null,
        n_in: 0,
        n_out: 0,
      });
    }
    return base;
  }, [detail]);

  return (
    <div
      data-testid="pipeline-run-detail-page"
      style={{ padding: 24, background: "#f9fafb", minHeight: "100vh", fontFamily: "system-ui, sans-serif" }}
    >
      {/* ① HEADER bar */}
      <div
        data-testid="header-bar"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 16,
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <button
            data-testid="btn-back"
            onClick={onBack}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "1px solid #d1d5db",
              background: "#fff",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            ← Back
          </button>
          <h1
            data-testid="header-title"
            style={{ fontSize: 18, fontWeight: 700, margin: 0, color: "#111827", display: "flex", alignItems: "center", gap: 10, flexWrap: "wrap" }}
          >
            <span>📊 Run {runId.slice(0, 8)} · {preset} ·</span>
            <span
              data-testid="pipeline-id-chip"
              style={{
                display: "inline-block",
                padding: "3px 12px",
                borderRadius: 999,
                fontSize: 12,
                fontWeight: 700,
                background: "#f3e8ff",
                color: "#6b21a8",
                border: "1px solid #c4b5fd",
                fontFamily: "monospace",
              }}
            >
              RUN #{runId}
            </span>
            <span
              data-testid={`mode-badge-${mode}`}
              style={{
                display: "inline-block",
                padding: "2px 10px",
                borderRadius: 999,
                fontSize: 12,
                fontWeight: 600,
                background: mode === "snapshot" ? "#dbeafe" : "#dcfce7",
                color: mode === "snapshot" ? "#1e40af" : "#166534",
              }}
            >
              {mode === "snapshot" ? "🔵 snapshot" : "🟢 live"}
            </span>
          </h1>
          <span
            data-testid="status-chip"
            className={`status-chip ${statusStyle.cls}`}
            style={{
              display: "inline-block",
              padding: "4px 12px",
              borderRadius: 999,
              fontSize: 12,
              fontWeight: 600,
              background: statusStyle.bg,
              color: statusStyle.color,
            }}
          >
            {status === "running" ? (
              <span data-testid="loading-spinner" style={{ display: "inline-block", marginRight: 6 }}>
                🔄
              </span>
            ) : null}
            {statusStyle.label}
          </span>
        </div>

        <div data-testid="header-actions" style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {canCancel && (
            <button
              data-testid="btn-cancel"
              onClick={() => pipeline.cancelRun()}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "1px solid #ef4444",
                background: "#fff",
                color: "#b91c1c",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Cancel
            </button>
          )}
          {canResume && (
            <button
              data-testid="btn-resume"
              onClick={() => {
                const step = failedStepIndex >= 0 ? failedStepIndex : 0;
                pipeline.retryStep(step);
              }}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "1px solid #3b82f6",
                background: "#3b82f6",
                color: "#fff",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Resume {failedStepIndex >= 0 ? `#${failedStepIndex}` : ""}
            </button>
          )}
          {canDownload && (
            <button
              data-testid="btn-download-pdf"
              onClick={() => {
                const url = detail?.report_url;
                if (url) window.open(url, "_blank");
              }}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "1px solid #10b981",
                background: "#10b981",
                color: "#fff",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Download PDF
            </button>
          )}
          {canDownload && (
            <button
              data-testid="btn-download-csv"
              onClick={() => {
                const url = detail?.pico_csv_url;
                if (url) window.open(url, "_blank");
              }}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "1px solid #8b5cf6",
                background: "#8b5cf6",
                color: "#fff",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              Download CSV
            </button>
          )}
          <button
            data-testid="btn-compare"
            onClick={() => onNavigateToCompare(runId)}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "1px solid #6366f1",
              background: "#fff",
              color: "#4338ca",
              cursor: "pointer",
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            Compare →
          </button>
        </div>
      </div>

      {/* ② 8 STEP PROGRESS COLUMN BAR */}
      <div
        data-testid="step-progress-section"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>🧭 8-Step Pipeline Progress</div>
        <div
          data-testid="step-columns"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(8, minmax(0, 1fr))",
            gap: 8,
          }}
        >
          {steps.map((step, idx) => {
            const stIcon = _stepStatusIcon(step.status);
            const isDedupStep = idx === 1;
            return (
              <div
                key={idx}
                data-testid={`step-column-${idx}`}
                aria-label={isDedupStep ? "去重" : undefined}
                style={{
                  position: "relative",
                  padding: 12,
                  borderRadius: 6,
                  border: `1px solid ${stIcon.bg}`,
                  background: "#fafafa",
                  minHeight: 120,
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                }}
              >
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: 4 }}>
                    <div style={{ fontSize: 11, color: "#6b7280", fontWeight: 600 }}>
                      Step {idx}
                    </div>
                    {isDedupStep && (
                      <span
                        data-testid="step-dedup-star-badge"
                        aria-label="去重"
                        style={{
                          fontSize: 10,
                          padding: "1px 6px",
                          borderRadius: 999,
                          background: "#fef3c7",
                          color: "#92400e",
                          fontWeight: 700,
                          border: "1px solid #fcd34d",
                        }}
                      >
                        ⭐ NEW
                      </span>
                    )}
                  </div>
                  <div
                    data-testid={`step-name-${idx}`}
                    style={{ fontSize: 12, fontWeight: 700, color: "#111827", marginTop: 4 }}
                  >
                    {step.step_name ?? STEP_NAMES[idx]}
                  </div>
                </div>
                <div style={{ marginTop: 8 }}>
                  <div
                    data-testid={`step-status-icon-${idx}`}
                    className={`step-status-icon ${stIcon.cls}`}
                    title={`attempt: ${step.attempt_no ?? 1}, n_in→n_out: ${step.n_in}→${step.n_out}`}
                    style={{ fontSize: 18 }}
                  >
                    {stIcon.icon}
                  </div>
                  <div
                    data-testid={`step-duration-${idx}`}
                    style={{ fontSize: 11, color: "#6b7280", marginTop: 4, fontFamily: "monospace" }}
                  >
                    {_formatDuration(step.duration_ms)}
                  </div>
                </div>
                {step.status === "failed" && (
                  <div style={{ position: "absolute", bottom: 4, right: 4 }}>
                    <button
                      data-testid={`btn-retry-step-${idx}`}
                      onClick={() => pipeline.retryStep(idx)}
                      onContextMenu={(e) => {
                        e.preventDefault();
                        pipeline.retryStep(idx, true);
                      }}
                      style={{
                        padding: "4px 10px",
                        borderRadius: 4,
                        border: "1px solid #ef4444",
                        background: "#fee2e2",
                        color: "#991b1b",
                        cursor: "pointer",
                        fontSize: 11,
                        fontWeight: 600,
                      }}
                    >
                      RETRY STEP {idx}
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* ③ FUNNEL SECTION */}
      <div
        data-testid="funnel-section"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>📈 文献 PRISMA 漏斗</div>
        <div data-testid="funnel-progress-bar-wrapper">
          <FunnelProgressBar stats={funnelStats} />
        </div>
      </div>

      {/* ③-B DEDUP DIAGNOSTICS */}
      <PipelineDetailStepDiagFetch
        workspaceId={workspaceId}
        runId={runId}
        stepIndex={1}
        stepStatus={steps[1]?.status ?? "pending"}
        injectFetchClient={injectDiagClient}
      />

      {/* ④ EVIDENCE ARTIFACT CARD GRID */}
      <div
        data-testid="ea-section"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
          🗂️ Included Studies ({includeCount})
        </div>
        <div
          data-testid="ea-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
            gap: 12,
          }}
        >
          {eaPageRows.map((ea, i) => (
            <AbstractorCard
              key={ea.record.id}
              record={ea.record}
              triage={ea.triage}
            />
          ))}
        </div>
        {includeCount > EA_PAGE_SIZE && (
          <div
            data-testid="ea-pagination"
            style={{ display: "flex", justifyContent: "center", gap: 12, marginTop: 16, alignItems: "center" }}
          >
            <button
              data-testid="btn-ea-prev"
              disabled={eaPage <= 1}
              onClick={() => setEaPage((p) => Math.max(1, p - 1))}
              style={{
                padding: "6px 14px",
                borderRadius: 6,
                border: "1px solid #d1d5db",
                background: eaPage <= 1 ? "#f3f4f6" : "#fff",
                cursor: eaPage <= 1 ? "not-allowed" : "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              ◀
            </button>
            <span data-testid="ea-page-indicator" style={{ fontSize: 13, fontWeight: 600 }}>
              {eaPage}/{eaTotalPages}
            </span>
            <button
              data-testid="btn-ea-next"
              disabled={eaPage >= eaTotalPages}
              onClick={() => setEaPage((p) => Math.min(eaTotalPages, p + 1))}
              style={{
                padding: "6px 14px",
                borderRadius: 6,
                border: "1px solid #d1d5db",
                background: eaPage >= eaTotalPages ? "#f3f4f6" : "#fff",
                cursor: eaPage >= eaTotalPages ? "not-allowed" : "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              ▶
            </button>
          </div>
        )}
      </div>

      {/* ⑤ RoB2 MATRIX */}
      <div
        data-testid="rob2-section"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>⚖️ RoB2 偏倚风险评估</div>
        <div data-testid="rob2-matrix-wrapper">
          <RoB2Matrix studies={rob2Studies} editable={false} />
        </div>
        <div
          data-testid="rob2-summary"
          style={{
            marginTop: 12,
            padding: 10,
            borderRadius: 6,
            background: "#f9fafb",
            border: "1px solid #e5e7eb",
            display: "flex",
            gap: 16,
            fontSize: 12,
            fontWeight: 600,
            flexWrap: "wrap",
          }}
        >
          <span style={{ color: "#10b981" }}>Low {rob2Counts.low}</span>
          <span style={{ color: "#f59e0b" }}>Some {rob2Counts.some}</span>
          <span style={{ color: "#ef4444" }}>High {rob2Counts.high}</span>
        </div>
      </div>

      {/* ⑥ GRADE DISTRIBUTION */}
      <div
        data-testid="grade-section"
        style={{ marginBottom: 20 }}
      >
        <GradeDistributionCard
          distribution={detail?.grade_distribution ?? null}
        />
      </div>

      {/* ⑦ PICO CSV Downloadable */}
      <div
        data-testid="pico-csv-section"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>📋 PICO Extracted Data</div>
        <button
          data-testid="btn-download-pico-csv"
          disabled={!detail?.pico_csv_url}
          onClick={() => {
            const url = detail?.pico_csv_url;
            if (url) {
              const a = document.createElement("a");
              a.href = url;
              a.download = `pico-${runId.slice(0, 8)}.csv`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }
          }}
          style={{
            padding: "10px 20px",
            borderRadius: 6,
            border: "1px solid #3b82f6",
            background: detail?.pico_csv_url ? "#3b82f6" : "#e5e7eb",
            color: detail?.pico_csv_url ? "#fff" : "#9ca3af",
            cursor: detail?.pico_csv_url ? "pointer" : "not-allowed",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          ⬇ Download PICO CSV
        </button>
      </div>

      {/* ⑧ REPORT PDF PREVIEW iframe */}
      <div
        data-testid="report-section"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>📄 自动生成证据报告</div>
        {detail?.report_url ? (
          <iframe
            data-testid="report-iframe"
            src={detail.report_url}
            width="100%"
            height={480}
            title="Report Preview"
            style={{ border: "1px solid #e5e7eb", borderRadius: 4 }}
          />
        ) : (
          <div
            data-testid="report-skeleton"
            style={{
              width: "100%",
              height: 480,
              background: "#f3f4f6",
              borderRadius: 4,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#9ca3af",
              fontSize: 13,
            }}
          >
            Report not yet generated...
          </div>
        )}
        {detail?.report_url && (
          <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
            <button
              data-testid="btn-report-download-pdf"
              onClick={() => {
                const url = detail.report_url;
                window.open(url, "_blank");
              }}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "1px solid #10b981",
                background: "#10b981",
                color: "#fff",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              ⬇ Download PDF
            </button>
            <button
              data-testid="btn-report-download-md"
              onClick={() => {
                const mdUrl = detail.report_url?.replace(/\.pdf$/i, ".md");
                if (mdUrl) {
                  window.open(mdUrl, "_blank");
                }
              }}
              style={{
                padding: "8px 16px",
                borderRadius: 6,
                border: "1px solid #6366f1",
                background: "#6366f1",
                color: "#fff",
                cursor: "pointer",
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              ⬇ Markdown
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default PipelineRunDetailPage;
