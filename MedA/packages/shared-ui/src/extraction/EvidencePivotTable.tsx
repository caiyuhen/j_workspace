import React, { useMemo, useState } from "react";

export type ExtractionFieldType = "text" | "select" | "number" | "boolean";

export type PicoBinding =
  | null
  | "P"
  | "I"
  | "C"
  | "O"
  | "S"
  | "StudyType"
  | "OutcomeMeasure"
  | "Other";

export interface ExtractionTemplateField {
  key: string;
  label: string;
  type: ExtractionFieldType;
  pico_binding: PicoBinding;
  required: boolean;
  options: string[];
}

export interface EvidenceWideRow {
  record_id: number | string;
  study_label: string;
  values: Record<string, unknown>;
}

export interface EvidencePivotTableProps {
  rows: EvidenceWideRow[];
  columns: ExtractionTemplateField[];
  pageSize?: number;
  onExportCsv?: () => void;
  onPageChange?: (page: number) => void;
  onRowClick?: (record_id: number | string) => void;
}

const PICO_BG_COLORS: Record<string, string> = {
  P: "#ede9fe",
  I: "#dbeafe",
  C: "#cffafe",
  O: "#dcfce7",
};

const PICO_LABEL: Record<string, string> = {
  P: "P - 人群",
  I: "I - 干预",
  C: "C - 对照",
  O: "O - 结局",
  S: "S - 研究设计",
  StudyType: "StudyType - 研究类型",
  OutcomeMeasure: "OutcomeMeasure - 结局指标",
  Other: "Other - 其他",
};

const LONG_TEXT_CUTOFF = 60;

function formatCellValue(v: unknown, type: ExtractionFieldType): string {
  if (v === null || v === undefined) return "-";
  if (type === "number") {
    if (typeof v === "number") return String(v);
    const s = String(v).trim();
    if (s === "") return "-";
    return s;
  }
  if (type === "boolean") {
    if (typeof v === "boolean") return v ? "是" : "否";
    return String(v);
  }
  const s = String(v);
  if (s.length > LONG_TEXT_CUTOFF) {
    return s.slice(0, LONG_TEXT_CUTOFF) + "...";
  }
  return s;
}

export const EvidencePivotTable: React.FC<EvidencePivotTableProps> = ({
  rows,
  columns,
  pageSize: pageSizeProp,
  onExportCsv,
  onPageChange,
  onRowClick,
}) => {
  const pageSize = pageSizeProp ?? 200;
  const [page, setPage] = useState<number>(1);

  const totalPages = rows.length === 0 ? 1 : Math.max(1, Math.ceil(rows.length / pageSize));

  const currentPage = Math.min(Math.max(1, page), totalPages);

  const pagedRows = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return rows.slice(start, start + pageSize);
  }, [rows, currentPage, pageSize]);

  const goNext = () => {
    if (currentPage < totalPages) {
      const next = currentPage + 1;
      setPage(next);
      if (onPageChange) onPageChange(next);
    }
  };

  const goPrev = () => {
    if (currentPage > 1) {
      const next = currentPage - 1;
      setPage(next);
      if (onPageChange) onPageChange(next);
    }
  };

  const headerBg = (c: ExtractionTemplateField): string => {
    if (c.pico_binding && PICO_BG_COLORS[c.pico_binding]) {
      return PICO_BG_COLORS[c.pico_binding];
    }
    return "#f3f4f6";
  };

  const headerTitle = (c: ExtractionTemplateField): string => {
    if (c.pico_binding && PICO_LABEL[c.pico_binding]) {
      return `${c.label} (${PICO_LABEL[c.pico_binding]})`;
    }
    return c.label;
  };

  const isNumberCol = (k: string): boolean => {
    const col = columns.find((c) => c.key === k);
    return !!col && col.type === "number";
  };

  const thStyle: React.CSSProperties = {
    padding: "8px 12px",
    borderBottom: "2px solid #e5e7eb",
    textAlign: "left",
    fontSize: "13px",
    fontWeight: 700,
    color: "#1f2937",
    whiteSpace: "nowrap",
  };

  const tdStyle: React.CSSProperties = {
    padding: "6px 12px",
    borderBottom: "1px solid #f3f4f6",
    fontSize: "13px",
    color: "#111827",
    verticalAlign: "top",
  };

  const emptyRows = rows.length === 0;

  return (
    <div data-testid="evidence-pivot-wrapper" style={{ fontFamily: "sans-serif" }}>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "8px 4px",
          marginBottom: "8px",
        }}
      >
        <div style={{ fontSize: "13px", color: "#4b5563", fontWeight: 600 }}>
          证据提取表 · 共 {rows.length} 行 · {columns.length} 个字段
        </div>
        <button
          data-testid="btn-export-csv"
          onClick={() => onExportCsv && onExportCsv()}
          disabled={emptyRows}
          style={{
            padding: "6px 14px",
            background: emptyRows ? "#f3f4f6" : "#0891b2",
            color: emptyRows ? "#9ca3af" : "#fff",
            border: "none",
            borderRadius: "4px",
            fontSize: "12px",
            fontWeight: 600,
            cursor: emptyRows ? "not-allowed" : "pointer",
          }}
        >
          导出 CSV
        </button>
      </div>

      {emptyRows ? (
        <div
          data-testid="no-rows-state"
          style={{
            padding: "40px 20px",
            textAlign: "center",
            color: "#6b7280",
            fontSize: "14px",
            border: "2px dashed #e5e7eb",
            borderRadius: "6px",
            background: "#fafafa",
          }}
        >
          <div style={{ fontSize: "28px", marginBottom: "10px" }}>📋</div>
          暂无提取数据
        </div>
      ) : (
        <>
          <div style={{ overflowX: "auto" }}>
            <table
              data-testid="evidence-table"
              style={{
                width: "100%",
                borderCollapse: "collapse",
                background: "#fff",
                minWidth: "600px",
              }}
            >
              <thead>
                <tr>
                  <th
                    data-testid="evidence-colheader-study_label"
                    title="研究标签"
                    style={{
                      ...thStyle,
                      background: "#e5e7eb",
                      minWidth: "200px",
                    }}
                  >
                    研究标签
                  </th>
                  {columns.map((c) => {
                    const thAlign: React.CSSProperties = c.type === "number" ? { textAlign: "right" } : {};
                    return (
                      <th
                        key={c.key}
                        data-testid={`evidence-colheader-${c.key}`}
                        title={headerTitle(c)}
                        style={{
                          ...thStyle,
                          background: headerBg(c),
                          ...thAlign,
                        }}
                      >
                        {c.label || c.key}
                      </th>
                    );
                  })}
                </tr>
              </thead>
              <tbody>
                {pagedRows.map((row, i) => (
                  <tr
                    key={String(row.record_id) + "-" + i}
                    data-testid={`evidence-row-${i}`}
                    onClick={() => onRowClick && onRowClick(row.record_id)}
                    style={{
                      cursor: onRowClick ? "pointer" : "default",
                      background: onRowClick ? "#fff" : "transparent",
                    }}
                  >
                    <td
                      style={{
                        ...tdStyle,
                        fontWeight: 600,
                        color: "#1d4ed8",
                      }}
                    >
                      {row.study_label}
                    </td>
                    {columns.map((c) => {
                      const raw = row.values[c.key];
                      const display = formatCellValue(raw, c.type);
                      const cellAlign: React.CSSProperties = c.type === "number" ? { textAlign: "right" } : {};
                      return (
                        <td
                          key={c.key}
                          data-testid={`evidence-cell-${i}-${c.key}`}
                          style={{ ...tdStyle, ...cellAlign }}
                        >
                          {display}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "10px 4px",
              marginTop: "6px",
              borderTop: "1px solid #e5e7eb",
              fontSize: "13px",
            }}
          >
            <div
              data-testid="evidence-page-info"
              style={{ color: "#4b5563", fontWeight: 600 }}
            >
              {currentPage} of {totalPages}
            </div>
            <div style={{ display: "flex", gap: "8px" }}>
              <button
                data-testid="evidence-btn-prev"
                onClick={goPrev}
                disabled={currentPage <= 1}
                style={{
                  padding: "5px 12px",
                  background: currentPage <= 1 ? "#f3f4f6" : "#ffffff",
                  color: currentPage <= 1 ? "#9ca3af" : "#1f2937",
                  border: "1px solid #d1d5db",
                  borderRadius: "4px",
                  fontSize: "12px",
                  cursor: currentPage <= 1 ? "not-allowed" : "pointer",
                  fontWeight: 600,
                }}
              >
                上一页
              </button>
              <button
                data-testid="evidence-btn-next"
                onClick={goNext}
                disabled={currentPage >= totalPages}
                style={{
                  padding: "5px 12px",
                  background: currentPage >= totalPages ? "#f3f4f6" : "#ffffff",
                  color: currentPage >= totalPages ? "#9ca3af" : "#1f2937",
                  border: "1px solid #d1d5db",
                  borderRadius: "4px",
                  fontSize: "12px",
                  cursor: currentPage >= totalPages ? "not-allowed" : "pointer",
                  fontWeight: 600,
                }}
              >
                下一页
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
