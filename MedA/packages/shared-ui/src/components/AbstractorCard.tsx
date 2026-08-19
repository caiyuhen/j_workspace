import React from "react";
import ConfidenceBar from "./ConfidenceBar";

export interface AbstractorRecord {
  id: string;
  title: string;
  year?: number;
  journal?: string;
  hamming_distance?: number;
  jaccard_similarity?: number;
}

export interface AbstractorTriage {
  decision: "include" | "exclude" | "review";
  confidence: number;
  reasons?: string[];
  exclude_reason_ids?: number[];
  failed_steps?: string[];
  override_by_user_id?: string;
  pico?: {
    p?: { text?: string; n?: number; age_min?: number; age_max?: number; condition?: string };
    i?: { drug?: string; dose?: string; duration?: string; n?: number };
    c?: { comparator?: string; type?: "active" | "placebo" | "other" };
    o?: Array<{
      name?: string;
      mean_diff?: number;
      rr?: number;
      ci_low?: number;
      ci_high?: number;
      p_value?: number;
    }>;
  };
  pipeline_steps?: Array<{ key: string; label: string; active: boolean }>;
}

export interface AbstractorCardProps {
  record: AbstractorRecord;
  triage: AbstractorTriage;
  onDecide?: (decision: string, options?: { reason_ids?: number[]; override_by_user_id?: string }) => void;
  dashboard_stats?: {
    include_percent?: number;
    review_percent?: number;
    exclude_percent?: number;
  };
}

function _decisionBadge(decision: string): { bg: string; color: string; label: string; border: string } {
  switch (decision) {
    case "include":
      return { bg: "#d1fae5", color: "#065f46", label: "✓ Include", border: "#6ee7b7" };
    case "exclude":
      return { bg: "#fee2e2", color: "#991b1b", label: "✗ Exclude", border: "#fca5a5" };
    case "review":
    default:
      return { bg: "#fef3c7", color: "#92400e", label: "⚠ Review", border: "#fcd34d" };
  }
}

export default function AbstractorCard(props: AbstractorCardProps): JSX.Element {
  const { record, triage, onDecide } = props;
  const recordId = record.id;
  const decisionBadge = _decisionBadge(triage.decision);
  const hasFailed = Array.isArray(triage.failed_steps) && triage.failed_steps.length > 0;
  const hasDupeHints =
    typeof record.hamming_distance === "number" || typeof record.jaccard_similarity === "number";

  const p = triage.pico?.p ?? {};
  const i = triage.pico?.i ?? {};
  const c = triage.pico?.c ?? {};
  const oList = triage.pico?.o ?? [];
  const steps = triage.pipeline_steps ?? [];

  return (
    <div
      data-testid={`abstractor-card-${recordId}`}
      style={{
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        padding: 16,
        background: "#ffffff",
        boxShadow: "0 1px 2px rgba(0,0,0,0.04)",
        position: "relative",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: 12,
          marginBottom: 12,
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: 1, minWidth: 220 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap", marginBottom: 8 }}>
            <span
              data-testid={`badge-decision-${recordId}`}
              style={{
                padding: "3px 10px",
                borderRadius: 999,
                fontSize: 12,
                fontWeight: 600,
                background: decisionBadge.bg,
                color: decisionBadge.color,
                border: `1px solid ${decisionBadge.border}`,
              }}
            >
              {decisionBadge.label}
            </span>

            {typeof record.year === "number" && (
              <span
                data-testid={`badge-year-${recordId}`}
                style={{
                  padding: "3px 10px",
                  borderRadius: 999,
                  fontSize: 12,
                  fontWeight: 500,
                  background: "#e0e7ff",
                  color: "#3730a3",
                  border: "1px solid #a5b4fc",
                }}
              >
                📅 {record.year}
              </span>
            )}

            {hasDupeHints && (
              <span
                data-testid={`badge-duplicate-${recordId}`}
                style={{
                  padding: "3px 10px",
                  borderRadius: 999,
                  fontSize: 12,
                  fontWeight: 500,
                  background: "#f3e8ff",
                  color: "#6b21a8",
                  border: "1px solid #c4b5fd",
                }}
                title={
                  [
                    typeof record.hamming_distance === "number"
                      ? `Hamming=${record.hamming_distance}`
                      : "",
                    typeof record.jaccard_similarity === "number"
                      ? `Jaccard=${record.jaccard_similarity}`
                      : "",
                  ]
                    .filter(Boolean)
                    .join(" / ") || undefined
                }
              >
                🔁 Duplicate
                {typeof record.hamming_distance === "number" ? ` H=${record.hamming_distance}` : ""}
                {typeof record.jaccard_similarity === "number"
                  ? ` J=${record.jaccard_similarity}`
                  : ""}
              </span>
            )}
          </div>

          <h3
            data-testid={`card-title-${recordId}`}
            style={{
              fontSize: 15,
              fontWeight: 600,
              margin: "0 0 4px 0",
              color: "#111827",
              lineHeight: 1.4,
            }}
          >
            {record.title}
          </h3>

          {record.journal && (
            <div
              style={{
                fontSize: 12,
                color: "#6b7280",
                marginBottom: 2,
              }}
            >
              {record.journal}
            </div>
          )}
        </div>

        <div style={{ minWidth: 200, flex: "0 0 260px" }}>
          <ConfidenceBar value={triage.confidence} label="Confidence" />
        </div>
      </div>

      {steps.length > 0 && (
        <div
          data-testid={`pipeline-steps-${recordId}`}
          style={{
            display: "flex",
            gap: 8,
            marginBottom: 12,
            flexWrap: "wrap",
          }}
        >
          {steps.map((s) => (
            <span
              key={s.key}
              data-testid={`pipeline-step-${s.key}-${recordId}`}
              style={{
                padding: "3px 10px",
                borderRadius: 6,
                fontSize: 11,
                fontWeight: 600,
                background: s.active ? "#dbeafe" : "#f3f4f6",
                color: s.active ? "#1e40af" : "#6b7280",
                border: `1px solid ${s.active ? "#93c5fd" : "#e5e7eb"}`,
              }}
            >
              {s.active ? "●" : "○"} {s.label}
            </span>
          ))}
        </div>
      )}

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(4, minmax(0, 1fr))",
          gap: 12,
          marginBottom: 12,
        }}
      >
        <div
          data-testid={`pico-p-${recordId}`}
          style={{
            padding: 10,
            background: "#f9fafb",
            borderRadius: 6,
            border: "1px solid #e5e7eb",
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: "#4b5563", marginBottom: 6 }}>
            P · Population
          </div>
          {p.text && <div style={{ fontSize: 12, color: "#111827", marginBottom: 4 }}>{p.text}</div>}
          <div style={{ fontSize: 11, color: "#6b7280", display: "flex", gap: 8, flexWrap: "wrap" }}>
            {typeof p.n === "number" && <span>n={p.n}</span>}
            {(typeof p.age_min === "number" || typeof p.age_max === "number") && (
              <span>
                age {p.age_min ?? "?"}–{p.age_max ?? "?"}
              </span>
            )}
            {p.condition && !p.text && <span>{p.condition}</span>}
          </div>
        </div>

        <div
          data-testid={`pico-i-${recordId}`}
          style={{
            padding: 10,
            background: "#f9fafb",
            borderRadius: 6,
            border: "1px solid #e5e7eb",
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: "#4b5563", marginBottom: 6 }}>
            I · Intervention
          </div>
          {i.drug && <div style={{ fontSize: 12, color: "#111827", marginBottom: 4 }}>{i.drug}</div>}
          <div style={{ fontSize: 11, color: "#6b7280", display: "flex", gap: 8, flexWrap: "wrap" }}>
            {i.dose && <span>dose: {i.dose}</span>}
            {i.duration && <span>×{i.duration}</span>}
            {typeof i.n === "number" && <span>n={i.n}</span>}
          </div>
        </div>

        <div
          data-testid={`pico-c-${recordId}`}
          style={{
            padding: 10,
            background: "#f9fafb",
            borderRadius: 6,
            border: "1px solid #e5e7eb",
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: "#4b5563", marginBottom: 6 }}>
            C · Comparator
          </div>
          {c.comparator && (
            <div style={{ fontSize: 12, color: "#111827", marginBottom: 4 }}>{c.comparator}</div>
          )}
          <div style={{ fontSize: 11, color: "#6b7280" }}>
            {c.type && <span>type: {c.type}</span>}
          </div>
        </div>

        <div
          data-testid={`pico-o-${recordId}`}
          style={{
            padding: 10,
            background: "#f9fafb",
            borderRadius: 6,
            border: "1px solid #e5e7eb",
          }}
        >
          <div style={{ fontSize: 11, fontWeight: 700, color: "#4b5563", marginBottom: 6 }}>
            O · Outcomes
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            {oList.length === 0 && (
              <div style={{ fontSize: 11, color: "#9ca3af", fontStyle: "italic" }}>—</div>
            )}
            {oList.map((o, idx) => (
              <div
                key={idx}
                data-testid={`outcome-${idx}-${recordId}`}
                style={{
                  fontSize: 11,
                  padding: "4px 6px",
                  background: "#ffffff",
                  borderRadius: 4,
                  border: "1px solid #f3f4f6",
                }}
              >
                <div style={{ fontWeight: 600, color: "#111827", marginBottom: 2 }}>
                  {o.name ?? `Outcome ${idx + 1}`}
                </div>
                <div
                  style={{
                    color: "#4b5563",
                    display: "flex",
                    gap: 6,
                    flexWrap: "wrap",
                    lineHeight: 1.5,
                  }}
                >
                  {typeof o.mean_diff === "number" && <span>MD={o.mean_diff}</span>}
                  {typeof o.rr === "number" && <span>RR={o.rr}</span>}
                  {(typeof o.ci_low === "number" || typeof o.ci_high === "number") && (
                    <span>
                      CI: [{o.ci_low ?? "?"}, {o.ci_high ?? "?"}]
                    </span>
                  )}
                  {typeof o.p_value === "number" && (
                    <span style={{ color: o.p_value < 0.05 ? "#059669" : "#6b7280" }}>
                      p={o.p_value}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {Array.isArray(triage.reasons) && triage.reasons.length > 0 && (
        <div
          style={{
            padding: 8,
            background: "#f8fafc",
            borderRadius: 6,
            marginBottom: 12,
            fontSize: 12,
            color: "#475569",
            border: "1px solid #e2e8f0",
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4, fontSize: 11 }}>Triage Reasons:</div>
          <ul style={{ margin: 0, paddingLeft: 20 }}>
            {triage.reasons.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
          flexWrap: "wrap",
        }}
      >
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <button
            data-testid="btn-accept-include"
            onClick={() => {
              if (onDecide) onDecide("include");
            }}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "1px solid #10b981",
              background: "#10b981",
              color: "#ffffff",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            ✓ 接受 Include
          </button>
          <button
            data-testid="btn-modify-review"
            onClick={() => {
              if (onDecide)
                onDecide("review", {
                  override_by_user_id: "current-user",
                });
            }}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "1px solid #f59e0b",
              background: "#f59e0b",
              color: "#ffffff",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            ✎ 修改 → Review
          </button>
          <button
            data-testid="btn-accept-exclude"
            onClick={() => {
              const reasonIds = Array.isArray(triage.exclude_reason_ids)
                ? triage.exclude_reason_ids
                : undefined;
              if (onDecide) onDecide("exclude", { reason_ids: reasonIds });
            }}
            style={{
              padding: "8px 16px",
              borderRadius: 6,
              border: "1px solid #ef4444",
              background: "#ef4444",
              color: "#ffffff",
              fontSize: 13,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            ✗ 接受 Exclude
          </button>
        </div>

        {hasFailed && (
          <div
            data-testid={`llm-degrade-warning-${recordId}`}
            style={{
              padding: "6px 10px",
              borderRadius: 6,
              background: "#fef3c7",
              color: "#92400e",
              border: "1px solid #fcd34d",
              fontSize: 12,
              fontWeight: 600,
            }}
            title={`Failed steps: ${triage.failed_steps?.join(", ")}`}
          >
            ⚠️ LLM降级 规则
          </div>
        )}
      </div>
    </div>
  );
}

export { AbstractorCard };
export { ConfidenceBar } from "./ConfidenceBar";
export type { ConfidenceBarProps } from "./ConfidenceBar";
