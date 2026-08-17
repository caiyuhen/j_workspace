import React from "react";
import type {
  KappaFieldSummary as T7Kappa,
  ExtractionTemplateField as T7Field,
} from "@meda/shared-sdk";
import {
  EvidencePivotTable,
  type EvidenceWideRow as T8Row,
  type ExtractionTemplateField as T8Field,
  type ExtractionFieldType as T8FieldType,
  type PicoBinding as T8Pico,
} from "./EvidencePivotTable";

export interface ReviewerOption {
  id: number | string;
  name: string;
}

export interface EvidenceTablePageProps {
  rows: T8Row[];
  columns: T7Field[];
  reviewerOptions: ReviewerOption[];
  selectedReviewerIds: (number | string)[];
  onReviewerFilterChange: (ids: (number | string)[]) => void;
  onExportCsv: () => void;
  kappaSummaryList: T7Kappa[];
}

function t7ToT8Col(f: T7Field): T8Field {
  const t8Type: T8FieldType = (f.field_type && ["text", "select", "number", "boolean"].includes(f.field_type))
    ? (f.field_type as T8FieldType)
    : "text";
  const t8Pico: T8Pico = f.pico_binding ? (f.pico_binding as T8Pico) : null;
  return {
    key: f.key,
    label: f.label,
    type: t8Type,
    pico_binding: t8Pico,
    required: f.required,
    options: f.options ?? [],
  };
}

// ============================================================
// inner KappaSummary component
// ============================================================
export interface KappaSummaryProps {
  kappaSummaryList: T7Kappa[];
}

const KappaSummary: React.FC<KappaSummaryProps> = ({ kappaSummaryList }) => {
  const empty = kappaSummaryList.length === 0;

  const thStyle: React.CSSProperties = {
    padding: "8px 12px",
    borderBottom: "2px solid #e5e7eb",
    textAlign: "left",
    fontSize: "13px",
    fontWeight: 700,
    color: "#1f2937",
    whiteSpace: "nowrap",
    background: "#f3f4f6",
  };

  const tdStyle: React.CSSProperties = {
    padding: "6px 12px",
    borderBottom: "1px solid #f3f4f6",
    fontSize: "13px",
    color: "#111827",
    verticalAlign: "top",
  };

  if (empty) {
    return (
      <div
        data-testid="no-kappa-data"
        style={{
          padding: "30px 20px",
          textAlign: "center",
          color: "#6b7280",
          fontSize: "13px",
          border: "2px dashed #e5e7eb",
          borderRadius: "6px",
          background: "#fafafa",
        }}
      >
        <div style={{ fontSize: "24px", marginBottom: "8px" }}>📊</div>
        暂无 Kappa 一致性数据
      </div>
    );
  }

  return (
    <div style={{ fontFamily: "sans-serif" }}>
      <div
        style={{
          fontSize: "13px",
          color: "#4b5563",
          fontWeight: 700,
          marginBottom: "8px",
        }}
      >
        Kappa 一致性统计 · 共 {kappaSummaryList.length} 个字段
      </div>
      <div style={{ overflowX: "auto" }}>
        <table
          data-testid="kappa-table"
          style={{
            width: "100%",
            borderCollapse: "collapse",
            background: "#fff",
            minWidth: "500px",
          }}
        >
          <thead>
            <tr>
              <th style={thStyle}>字段 Key</th>
              <th style={{ ...thStyle, textAlign: "right" }}>Kappa</th>
              <th style={{ ...thStyle, textAlign: "right" }}>一致率 %</th>
              <th style={{ ...thStyle, textAlign: "right" }}>配对数</th>
              <th style={thStyle}>状态</th>
            </tr>
          </thead>
          <tbody>
            {kappaSummaryList.map((k) => {
              const isLow = k.warning_level === "low_agreement";
              return (
                <tr key={k.field_key} data-testid={`kappa-row-${k.field_key}`}>
                  <td style={tdStyle}>{k.field_key}</td>
                  <td style={{ ...tdStyle, textAlign: "right", fontFamily: "monospace" }}>
                    {k.kappa === null ? "N/A" : k.kappa.toFixed(3)}
                  </td>
                  <td style={{ ...tdStyle, textAlign: "right" }}>
                    {k.pct_agree === null || k.pct_agree === undefined
                      ? "-"
                      : `${k.pct_agree.toFixed(1)}%`}
                  </td>
                  <td style={{ ...tdStyle, textAlign: "right" }}>{k.n_pairs}</td>
                  <td style={tdStyle}>
                    {isLow ? (
                      <span
                        data-testid={`kappa-warning-${k.field_key}`}
                        style={{
                          display: "inline-block",
                          padding: "3px 10px",
                          background: "#fee2e2",
                          color: "#b91c1c",
                          borderRadius: "10px",
                          fontSize: "11px",
                          fontWeight: 700,
                        }}
                      >
                        ⚠ 低一致性
                      </span>
                    ) : (
                      <span
                        style={{
                          display: "inline-block",
                          padding: "3px 10px",
                          background: "#dcfce7",
                          color: "#166534",
                          borderRadius: "10px",
                          fontSize: "11px",
                          fontWeight: 700,
                        }}
                      >
                        ✓ 一致
                      </span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ============================================================
// EvidenceTablePage
// ============================================================
export const EvidenceTablePage: React.FC<EvidenceTablePageProps> = ({
  rows,
  columns,
  reviewerOptions,
  selectedReviewerIds,
  onReviewerFilterChange,
  onExportCsv,
  kappaSummaryList,
}) => {
  const t8Columns: T8Field[] = columns.map((c) => t7ToT8Col(c));

  const toggleReviewer = (id: number | string) => {
    const exists = selectedReviewerIds.includes(id);
    const next = exists
      ? selectedReviewerIds.filter((x) => x !== id)
      : [...selectedReviewerIds, id];
    onReviewerFilterChange(next);
  };

  const emptyRows = rows.length === 0;

  return (
    <div style={{ fontFamily: "sans-serif", padding: "16px", maxWidth: "1200px", margin: "0 auto" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "12px",
          marginBottom: "14px",
          flexWrap: "wrap",
        }}
      >
        <div>
          <h2 style={{ margin: 0, fontSize: "20px", color: "#111827" }}>证据提取表</h2>
          <div style={{ fontSize: "13px", color: "#6b7280", marginTop: "4px" }}>
            浏览、筛选、审阅已提取的证据字段
          </div>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "6px",
            minWidth: "320px",
          }}
        >
          <div
            data-testid="reviewer-filter-label"
            style={{ fontSize: "12px", fontWeight: 600, color: "#374151" }}
          >
            评审者筛选：
          </div>
          <div
            data-testid="reviewer-filter-options"
            style={{
              display: "flex",
              flexWrap: "wrap",
              gap: "8px",
              padding: "8px",
              border: "1px solid #e5e7eb",
              borderRadius: "6px",
              background: "#fafafa",
            }}
          >
            {reviewerOptions.length === 0 ? (
              <span style={{ fontSize: "12px", color: "#9ca3af" }}>暂无评审者</span>
            ) : (
              reviewerOptions.map((r) => {
                const checked = selectedReviewerIds.includes(r.id);
                return (
                  <label
                    key={String(r.id)}
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: "4px",
                      padding: "3px 8px",
                      background: checked ? "#dbeafe" : "#fff",
                      border: `1px solid ${checked ? "#3b82f6" : "#d1d5db"}`,
                      borderRadius: "12px",
                      fontSize: "12px",
                      color: "#374151",
                      cursor: "pointer",
                    }}
                  >
                    <input
                      type="checkbox"
                      data-testid={`reviewer-checkbox-${r.id}`}
                      checked={checked}
                      onChange={() => toggleReviewer(r.id)}
                      style={{ margin: 0 }}
                    />
                    {r.name}
                  </label>
                );
              })
            )}
          </div>
        </div>
      </div>

      <div
        style={{
          marginBottom: "18px",
          padding: emptyRows ? "0" : "0",
        }}
        data-testid={emptyRows ? "empty-evidence-table" : "evidence-section"}
      >
        <EvidencePivotTable
          rows={rows}
          columns={t8Columns}
          onExportCsv={onExportCsv}
        />
      </div>

      <div
        style={{
          padding: "14px",
          border: "1px solid #e5e7eb",
          borderRadius: "8px",
          background: "#fff",
        }}
      >
        <KappaSummary kappaSummaryList={kappaSummaryList} />
      </div>
    </div>
  );
};

export { KappaSummary };
