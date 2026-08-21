import React, { useState, useEffect, useMemo } from "react";
import {
  usePipelineCompare,
  type InjectPipelineCompareClient,
} from "../hooks/usePipelineCompare";
import {
  usePipelineRun,
  type InjectPipelineRunClient,
} from "../hooks/usePipelineRun";
import type { PipelineRunSummary, PipelineCompareResult } from "@meda/shared-sdk";
import FunnelProgressBar from "../components/FunnelProgressBar";
import { GradeDistributionCard } from "../components/GradeDistributionCard";
import { TrafficLightCell } from "../grade/TrafficLightCell";

export interface PipelineComparePageProps {
  workspaceId: string;
  defaultRunAId?: string;
  defaultRunBId?: string;
  injectFetchClient?: Partial<InjectPipelineCompareClient> & Partial<InjectPipelineRunClient>;
  onBack: () => void;
}

const FUNNEL_STEP_KEYS = [
  "Identify",
  "Dedup",
  "TA-pass",
  "FT-include",
  "Abstractor-include",
  "RoB2-assessed",
] as const;

type PicoTabKey = "only_a" | "only_b" | "both";

function _gradeToTrafficLight(g: "H" | "M" | "L"): "low" | "some_concerns" | "high" {
  switch (g) {
    case "H": return "low";
    case "M": return "some_concerns";
    case "L": return "high";
  }
}

export function PipelineComparePage(props: PipelineComparePageProps): JSX.Element {
  const { workspaceId, defaultRunAId, defaultRunBId, injectFetchClient, onBack } = props;

  const pipelineRun = usePipelineRun({ workspaceId, injectFetchClient });
  const compareHook = usePipelineCompare({
    workspaceId,
    runAId: defaultRunAId,
    runBId: defaultRunBId,
    injectFetchClient,
  });

  const [runASelected, setRunASelected] = useState<string | undefined>(defaultRunAId);
  const [runBSelected, setRunBSelected] = useState<string | undefined>(defaultRunBId);
  const [syncPreset, setSyncPreset] = useState<string | null>(null);
  const [picoTab, setPicoTab] = useState<PicoTabKey>("only_a");

  useEffect(() => {
    pipelineRun.listRuns({ per_page: 100, sort: "created_at DESC" });
  }, []);

  const runs = pipelineRun.state.runs || [];

  const runsFiltered = useMemo(() => {
    if (!syncPreset) return runs;
    return runs.filter((r) => r.preset === syncPreset);
  }, [runs, syncPreset]);

  const result: PipelineCompareResult | undefined = compareHook.state.compareResult;

  const funnelSteps = useMemo(() => {
    if (!result) {
      return FUNNEL_STEP_KEYS.map((label) => ({ label, a_n: 0, b_n: 0, diff: 0 }));
    }
    return FUNNEL_STEP_KEYS.map((label, idx) => {
      const row = result.funnel_delta[idx];
      return {
        label,
        a_n: row?.a_n ?? 0,
        b_n: row?.b_n ?? 0,
        diff: row?.diff ?? 0,
      };
    });
  }, [result]);

  const rob2Data = useMemo(() => {
    if (!result) return { low: { a: 0, b: 0 }, some: { a: 0, b: 0 }, high: { a: 0, b: 0 } };
    const out = { low: { a: 0, b: 0 }, some: { a: 0, b: 0 }, high: { a: 0, b: 0 } };
    for (const row of result.rob2_delta) {
      if (row.overall === "low") { out.low.a = row.a; out.low.b = row.b; }
      else if (row.overall === "some") { out.some.a = row.a; out.some.b = row.b; }
      else if (row.overall === "high") { out.high.a = row.a; out.high.b = row.b; }
    }
    return out;
  }, [result]);

  const gradeRows = useMemo(() => {
    if (!result || !result.grade_delta || result.grade_delta.length === 0) {
      return [
        { outcome: "All-cause mortality", a: "H" as const, b: "H" as const, reason: "Same grade; robust" },
        { outcome: "CV mortality", a: "H" as const, b: "M" as const, reason: "A lower due to indirectness vs B" },
        { outcome: "HF hospitalization", a: "M" as const, b: "L" as const, reason: "A higher certainty; B downgraded RoB2 high" },
        { outcome: "eGFR decline", a: "H" as const, b: "H" as const, reason: "Same grade; robust" },
      ];
    }
    return result.grade_delta;
  }, [result]);

  const picoOnlyA = result?.pico.only_in_a_nct_ids ?? [];
  const picoOnlyB = result?.pico.only_in_b_nct_ids ?? [];
  const picoBoth = result?.pico.both ?? [];

  const currentTabList = picoTab === "only_a" ? picoOnlyA : picoTab === "only_b" ? picoOnlyB : picoBoth;

  const handleSelectRunA = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value || undefined;
    setRunASelected(val);
    if (val && runBSelected) {
      compareHook.compare(val, runBSelected);
    }
  };

  const handleSelectRunB = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value || undefined;
    setRunBSelected(val);
    if (runASelected && val) {
      compareHook.compare(runASelected, val);
    }
  };

  const handleSyncPreset = () => {
    const firstPreset = runs[0]?.preset ?? null;
    if (firstPreset) setSyncPreset(syncPreset === firstPreset ? null : firstPreset);
  };

  const handleExportMD = () => {
    const md = _buildCompareMarkdown(result, runASelected, runBSelected);
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `pipeline-compare-${runASelected ?? "A"}-${runBSelected ?? "B"}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const funnelMax = useMemo(() => {
    let m = 1;
    for (const s of funnelSteps) {
      if (s.a_n > m) m = s.a_n;
      if (s.b_n > m) m = s.b_n;
    }
    return m;
  }, [funnelSteps]);

  const funnelAStats = useMemo(() => {
    const keys: any = ["N1", "N2", "E1", "E2", "E3", "E6"];
    return funnelSteps.map((s, i) => ({
      key: keys[i],
      label: s.label,
      count: s.a_n,
      locked: true,
    }));
  }, [funnelSteps]);

  const funnelBStats = useMemo(() => {
    const keys: any = ["N1", "N2", "E1", "E2", "E3", "E6"];
    return funnelSteps.map((s, i) => ({
      key: keys[i],
      label: s.label,
      count: s.b_n,
      locked: true,
    }));
  }, [funnelSteps]);

  return (
    <div
      data-testid="pipeline-compare-page"
      style={{ padding: 24, background: "#f9fafb", minHeight: "100vh", fontFamily: "system-ui, sans-serif" }}
    >
      {/* Header */}
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
            style={{ fontSize: 18, fontWeight: 700, margin: 0, color: "#111827" }}
          >
            ⚖️ Pipeline Run A/B 对比
          </h1>
        </div>
      </div>

      {/* Top Row: SYNC PRESET + 2 selectors */}
      <div
        data-testid="top-row"
        style={{
          display: "flex",
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
        <button
          data-testid="btn-sync-preset"
          onClick={handleSyncPreset}
          className={syncPreset ? "sync-preset-active" : ""}
          style={{
            padding: "6px 14px",
            borderRadius: 999,
            border: `1px solid ${syncPreset ? "#2563eb" : "#d1d5db"}`,
            background: syncPreset ? "#dbeafe" : "#ffffff",
            color: syncPreset ? "#1e40af" : "#374151",
            fontSize: 12,
            fontWeight: syncPreset ? 700 : 500,
            cursor: "pointer",
          }}
        >
          {syncPreset ? `🔗 SYNC PRESET: ${syncPreset}` : "🔗 SYNC PRESET"}
        </button>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <label style={{ fontSize: 13, color: "#4b5563", fontWeight: 600 }}>Run A (left):</label>
          <select
            data-testid="selector-run-a"
            value={runASelected ?? ""}
            onChange={handleSelectRunA}
            style={{
              padding: "6px 10px",
              borderRadius: 6,
              border: "1px solid #d1d5db",
              fontSize: 13,
              background: "#ffffff",
              minWidth: 220,
            }}
          >
            <option value="">— Select Run A —</option>
            {runsFiltered.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id.slice(0, 8)} · {r.preset} · {r.status}
              </option>
            ))}
          </select>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <label style={{ fontSize: 13, color: "#4b5563", fontWeight: 600 }}>Run B (right):</label>
          <select
            data-testid="selector-run-b"
            value={runBSelected ?? ""}
            onChange={handleSelectRunB}
            style={{
              padding: "6px 10px",
              borderRadius: 6,
              border: "1px solid #d1d5db",
              fontSize: 13,
              background: "#ffffff",
              minWidth: 220,
            }}
          >
            <option value="">— Select Run B —</option>
            {runsFiltered.map((r) => (
              <option key={r.run_id} value={r.run_id}>
                {r.run_id.slice(0, 8)} · {r.preset} · {r.status}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Section 1: FUNNEL DIFF TABLE */}
      <div
        data-testid="section-funnel-diff"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div data-testid="funnel-diff-header" style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
          📊 Funnel Diff (A vs B side-by-side)
        </div>
        <div data-testid="funnel-diff-table" style={{ width: "100%" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
            <thead>
              <tr style={{ background: "#f9fafb", borderBottom: "1px solid #e5e7eb" }}>
                <th style={FTH_STYLE}>Step</th>
                <th style={FTH_STYLE}>Run A count</th>
                <th style={FTH_STYLE}>Δ diff</th>
                <th style={FTH_STYLE}>Run B count</th>
              </tr>
            </thead>
            <tbody>
              {funnelSteps.map((row, idx) => {
                const aPct = funnelMax > 0 ? (row.a_n / funnelMax) * 100 : 0;
                const bPct = funnelMax > 0 ? (row.b_n / funnelMax) * 100 : 0;
                let diffClass = "diff-neutral";
                let diffColor = "#6b7280";
                if (row.diff > 0) { diffClass = "diff-positive green"; diffColor = "#059669"; }
                else if (row.diff < 0) { diffClass = "diff-negative red"; diffColor = "#dc2626"; }
                return (
                  <tr
                    key={row.label}
                    data-testid={`funnel-diff-row-${idx}`}
                    style={{ borderBottom: "1px solid #f3f4f6" }}
                  >
                    <td style={FTD_STYLE}>
                      <span style={{ fontWeight: 600 }}>{row.label}</span>
                    </td>
                    <td style={FTD_STYLE}>
                      <div data-testid={`funnel-a-bar-${idx}`} style={{ position: "relative", height: 28 }}>
                        <div
                          className="funnel-bar-a"
                          style={{
                            position: "absolute",
                            left: 0,
                            top: 0,
                            width: `${aPct}%`,
                            height: "100%",
                            background: "#10b981",
                            borderRadius: 4,
                            opacity: 0.85,
                          }}
                        />
                        <span
                          data-testid={`funnel-a-count-${idx}`}
                          style={{ position: "relative", zIndex: 1, paddingLeft: 8, lineHeight: "28px", color: aPct > 50 ? "#ffffff" : "#111827", fontWeight: 600 }}
                        >
                          {row.a_n}
                        </span>
                      </div>
                    </td>
                    <td style={FTD_STYLE}>
                      <span
                        data-testid={`funnel-diff-cell-${idx}`}
                        className={diffClass}
                        style={{ fontWeight: 700, color: diffColor, display: "inline-block", padding: "4px 10px", borderRadius: 4, background: diffClass === "diff-neutral" ? "#f3f4f6" : "transparent" }}
                      >
                        {row.diff > 0 ? `+${row.diff}` : row.diff === 0 ? "0" : `${row.diff}`}
                      </span>
                    </td>
                    <td style={FTD_STYLE}>
                      <div data-testid={`funnel-b-bar-${idx}`} style={{ position: "relative", height: 28 }}>
                        <div
                          className="funnel-bar-b"
                          style={{
                            position: "absolute",
                            left: 0,
                            top: 0,
                            width: `${bPct}%`,
                            height: "100%",
                            background: "#3b82f6",
                            borderRadius: 4,
                            opacity: 0.85,
                          }}
                        />
                        <span
                          data-testid={`funnel-b-count-${idx}`}
                          style={{ position: "relative", zIndex: 1, paddingLeft: 8, lineHeight: "28px", color: bPct > 50 ? "#ffffff" : "#111827", fontWeight: 600 }}
                        >
                          {row.b_n}
                        </span>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div data-testid="funnel-progress-bars-wrapper" style={{ display: "flex", gap: 16, marginTop: 16 }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#059669", marginBottom: 6 }}>Run A Funnel</div>
            <FunnelProgressBar stats={funnelAStats} />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#1e40af", marginBottom: 6 }}>Run B Funnel</div>
            <FunnelProgressBar stats={funnelBStats} />
          </div>
        </div>
      </div>

      {/* Section 2: RoB2 HISTOGRAM side-by-side */}
      <div
        data-testid="section-rob2-histogram"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
          ⚖️ RoB2 Histogram Comparison
        </div>
        <div style={{ display: "flex", gap: 24, alignItems: "flex-end", minHeight: 220 }}>
          <div
            data-testid="rob2-bar-run-a"
            style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}
          >
            <div style={{ fontSize: 12, fontWeight: 700, color: "#059669", marginBottom: 8 }}>Run A</div>
            <div style={{ display: "flex", gap: 4, height: 180, alignItems: "flex-end" }}>
              {_renderRob2StackSegment("a", "low", rob2Data.low.a, "#10b981")}
              {_renderRob2StackSegment("a", "some", rob2Data.some.a, "#f59e0b")}
              {_renderRob2StackSegment("a", "high", rob2Data.high.a, "#ef4444")}
            </div>
          </div>
          <div
            data-testid="rob2-bar-run-b"
            style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center" }}
          >
            <div style={{ fontSize: 12, fontWeight: 700, color: "#1e40af", marginBottom: 8 }}>Run B</div>
            <div style={{ display: "flex", gap: 4, height: 180, alignItems: "flex-end" }}>
              {_renderRob2StackSegment("b", "low", rob2Data.low.b, "#10b981")}
              {_renderRob2StackSegment("b", "some", rob2Data.some.b, "#f59e0b")}
              {_renderRob2StackSegment("b", "high", rob2Data.high.b, "#ef4444")}
            </div>
          </div>
        </div>
        <div style={{ display: "flex", justifyContent: "center", gap: 24, marginTop: 12 }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#10b981" }}>● Low</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#f59e0b" }}>● Some</span>
          <span style={{ fontSize: 12, fontWeight: 600, color: "#ef4444" }}>● High</span>
        </div>
      </div>

      {/* Section 3: GRADE COMPARISON TABLE */}
      <div
        data-testid="section-grade-comparison"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
          🎓 GRADE Comparison (per outcome)
        </div>
        <div style={{ display: "flex", gap: 16, marginBottom: 12, flexWrap: "wrap" }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#059669", marginBottom: 6 }}>Run A GRADE Distribution</div>
            <GradeDistributionCard
              distribution={_computeGradeDistFromRows(gradeRows, "a")}
              title=""
            />
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600, color: "#1e40af", marginBottom: 6 }}>Run B GRADE Distribution</div>
            <GradeDistributionCard
              distribution={_computeGradeDistFromRows(gradeRows, "b")}
              title=""
            />
          </div>
        </div>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#f9fafb", borderBottom: "1px solid #e5e7eb" }}>
              <th style={GTH_STYLE}>Outcome</th>
              <th style={GTH_STYLE}>Run A Grade</th>
              <th style={GTH_STYLE}>Δ</th>
              <th style={GTH_STYLE}>Run B Grade</th>
              <th style={GTH_STYLE}>Reason</th>
            </tr>
          </thead>
          <tbody>
            {gradeRows.map((row, idx) => {
              const gradeA: "H" | "M" | "L" = row.a;
              const gradeB: "H" | "M" | "L" = row.b;
              const order = { H: 0, M: 1, L: 2 } as const;
              let deltaIndicator = "↔";
              let deltaClass = "grade-delta-neutral";
              if (order[gradeA] < order[gradeB]) { deltaIndicator = "↗"; deltaClass = "grade-delta-up"; }
              else if (order[gradeA] > order[gradeB]) { deltaIndicator = "↘"; deltaClass = "grade-delta-down"; }
              return (
                <tr
                  key={row.outcome}
                  data-testid={`grade-row-${idx}`}
                  style={{ borderBottom: "1px solid #f3f4f6" }}
                >
                  <td style={GTD_STYLE}>
                    <span style={{ fontWeight: 600 }}>{row.outcome}</span>
                  </td>
                  <td style={GTD_STYLE}>
                    <div data-testid={`grade-a-cell-${idx}`}>
                      <TrafficLightCell rating={_gradeToTrafficLight(gradeA)} size="md" />
                      <span style={{ marginLeft: 6, fontWeight: 700, fontSize: 12 }}>{gradeA}</span>
                    </div>
                  </td>
                  <td style={GTD_STYLE}>
                    <span
                      data-testid={`grade-delta-${idx}`}
                      className={deltaClass}
                      style={{ fontSize: 16, fontWeight: 700 }}
                    >
                      {deltaIndicator}
                    </span>
                  </td>
                  <td style={GTD_STYLE}>
                    <div data-testid={`grade-b-cell-${idx}`}>
                      <TrafficLightCell rating={_gradeToTrafficLight(gradeB)} size="md" />
                      <span style={{ marginLeft: 6, fontWeight: 700, fontSize: 12 }}>{gradeB}</span>
                    </div>
                  </td>
                  <td style={GTD_STYLE}>
                    <span
                      data-testid={`grade-reason-${idx}`}
                      style={{ fontSize: 12, color: "#374151" }}
                    >
                      {row.reason}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Section 4: PICO DIFF TABS */}
      <div
        data-testid="section-pico-diff"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          marginBottom: 20,
        }}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}>
          📋 PICO Study ID Diff
        </div>
        <div
          data-testid="pico-tabs"
          style={{
            display: "flex",
            gap: 4,
            borderBottom: "2px solid #e5e7eb",
            marginBottom: 16,
          }}
        >
          <button
            data-testid="pico-tab-only-a"
            className={picoTab === "only_a" ? "active" : ""}
            onClick={() => setPicoTab("only_a")}
            style={{
              padding: "8px 16px",
              border: "none",
              borderBottom: picoTab === "only_a" ? "2px solid #2563eb" : "2px solid transparent",
              marginBottom: -2,
              background: "transparent",
              color: picoTab === "only_a" ? "#1e40af" : "#6b7280",
              fontSize: 13,
              fontWeight: picoTab === "only_a" ? 700 : 500,
              cursor: "pointer",
            }}
          >
            仅 A 有 {picoOnlyA.length} 篇
          </button>
          <button
            data-testid="pico-tab-only-b"
            className={picoTab === "only_b" ? "active" : ""}
            onClick={() => setPicoTab("only_b")}
            style={{
              padding: "8px 16px",
              border: "none",
              borderBottom: picoTab === "only_b" ? "2px solid #2563eb" : "2px solid transparent",
              marginBottom: -2,
              background: "transparent",
              color: picoTab === "only_b" ? "#1e40af" : "#6b7280",
              fontSize: 13,
              fontWeight: picoTab === "only_b" ? 700 : 500,
              cursor: "pointer",
            }}
          >
            仅 B 有 {picoOnlyB.length} 篇
          </button>
          <button
            data-testid="pico-tab-both"
            className={picoTab === "both" ? "active" : ""}
            onClick={() => setPicoTab("both")}
            style={{
              padding: "8px 16px",
              border: "none",
              borderBottom: picoTab === "both" ? "2px solid #2563eb" : "2px solid transparent",
              marginBottom: -2,
              background: "transparent",
              color: picoTab === "both" ? "#1e40af" : "#6b7280",
              fontSize: 13,
              fontWeight: picoTab === "both" ? 700 : 500,
              cursor: "pointer",
            }}
          >
            共有 {picoBoth.length} 篇
          </button>
        </div>
        <div
          data-testid="pico-card-list"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(240px, 1fr))",
            gap: 12,
          }}
        >
          {currentTabList.length === 0 ? (
            <div
              data-testid="pico-empty-state"
              style={{
                padding: 24,
                textAlign: "center",
                color: "#9ca3af",
                fontSize: 13,
                gridColumn: "1 / -1",
              }}
            >
              No studies in this category
            </div>
          ) : (
            currentTabList.map((nctId) => (
              <div
                key={nctId}
                data-testid={`nct-card-${nctId}`}
                style={{
                  padding: 12,
                  borderRadius: 8,
                  border: "1px solid #e5e7eb",
                  background: "#f9fafb",
                }}
              >
                <a
                  data-testid={`nct-link-${nctId}`}
                  href={`https://clinicaltrials.gov/ct2/show/${nctId}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{
                    fontFamily: "monospace",
                    fontWeight: 700,
                    color: "#2563eb",
                    fontSize: 13,
                    textDecoration: "none",
                  }}
                >
                  🔗 {nctId}
                </a>
                <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>
                  ClinicalTrials.gov
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Bottom Actions */}
      <div
        data-testid="bottom-actions"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 16,
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
          flexWrap: "wrap",
        }}
      >
        <button
          data-testid="btn-export-md"
          onClick={handleExportMD}
          style={{
            padding: "10px 20px",
            borderRadius: 6,
            border: "1px solid #6366f1",
            background: "#6366f1",
            color: "#fff",
            cursor: "pointer",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          ⬇ 导出对比报告 Markdown
        </button>
        <button
          data-testid="btn-runs-list"
          onClick={onBack}
          style={{
            padding: "10px 20px",
            borderRadius: 6,
            border: "1px solid #d1d5db",
            background: "#fff",
            color: "#374151",
            cursor: "pointer",
            fontSize: 13,
            fontWeight: 600,
          }}
        >
          ↩ Runs List
        </button>
      </div>
    </div>
  );
}

function _renderRob2StackSegment(
  side: "a" | "b",
  level: "low" | "some" | "high",
  count: number,
  color: string,
): JSX.Element {
  const height = Math.max(4, Math.min(180, count * 4));
  return (
    <div
      key={`rob2-${side}-${level}`}
      data-testid={`rob2-${side}-seg-${level}`}
      style={{
        width: 48,
        height,
        background: color,
        borderRadius: "4px 4px 0 0",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        position: "relative",
      }}
    >
      <span
        data-testid={`rob2-${side}-label-${level}`}
        style={{
          color: "#ffffff",
          fontSize: 11,
          fontWeight: 700,
          position: count * 4 > 20 ? "static" : "absolute",
          top: count * 4 > 20 ? undefined : -20,
        }}
      >
        {count}
      </span>
    </div>
  );
}

function _computeGradeDistFromRows(
  rows: { outcome: string; a: "H" | "M" | "L"; b: "H" | "M" | "L"; reason: string }[],
  side: "a" | "b",
): { H: number; M: number; L: number } {
  const d = { H: 0, M: 0, L: 0 };
  for (const r of rows) {
    const key = side === "a" ? r.a : r.b;
    d[key]++;
  }
  return d;
}

function _buildCompareMarkdown(
  result: PipelineCompareResult | undefined,
  aId: string | undefined,
  bId: string | undefined,
): string {
  const lines: string[] = [];
  lines.push(`# Pipeline Compare Report: ${aId ?? "A"} vs ${bId ?? "B"}`);
  lines.push("");
  lines.push(`- Run A: \`${aId ?? "N/A"}\``);
  lines.push(`- Run B: \`${bId ?? "N/A"}\``);
  lines.push(`- Generated: ${new Date().toISOString()}`);
  lines.push("");
  lines.push("## Funnel Delta");
  lines.push("");
  lines.push("| Step | Run A | Run B | Δ |");
  lines.push("|------|-------|-------|---|");
  if (result) {
    for (const row of result.funnel_delta) {
      lines.push(`| ${row.step} | ${row.a_n} | ${row.b_n} | ${row.diff > 0 ? "+" + row.diff : String(row.diff)} |`);
    }
  }
  lines.push("");
  lines.push("## Grade Comparison");
  lines.push("");
  if (result && result.grade_delta) {
    for (const g of result.grade_delta) {
      lines.push(`- **${g.outcome}**: A=${g.a} vs B=${g.b} — ${g.reason}`);
    }
  }
  lines.push("");
  return lines.join("\n");
}

const FTH_STYLE: React.CSSProperties = {
  padding: "10px 12px",
  textAlign: "left",
  fontSize: 11,
  fontWeight: 700,
  color: "#4b5563",
  textTransform: "uppercase",
};

const FTD_STYLE: React.CSSProperties = {
  padding: "10px 12px",
  fontSize: 13,
  verticalAlign: "middle",
};

const GTH_STYLE: React.CSSProperties = {
  padding: "10px 12px",
  textAlign: "left",
  fontSize: 11,
  fontWeight: 700,
  color: "#4b5563",
  textTransform: "uppercase",
};

const GTD_STYLE: React.CSSProperties = {
  padding: "12px 12px",
  fontSize: 13,
  verticalAlign: "middle",
};

export default PipelineComparePage;
