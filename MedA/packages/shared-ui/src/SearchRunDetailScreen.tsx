import type { SearchRunDetail } from "@meda/shared-sdk";

type SearchRunDetailScreenProps = {
  detail: SearchRunDetail | null;
  onBackToRunList: () => void;
  onRetrySource: (sourceKey: string) => Promise<void> | void;
  onCancelRun: () => Promise<void> | void;
  onCsvExport: () => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

const STATUS_CHIP_STYLES: Record<
  string,
  { background: string; color: string; label: string }
> = {
  pending: { background: "#f3f4f6", color: "#4b5563", label: "等待中" },
  running: { background: "#dbeafe", color: "#1d4ed8", label: "运行中" },
  completed: { background: "#dcfce7", color: "#047857", label: "已完成" },
  partial_failed: { background: "#ffedd5", color: "#c2410c", label: "部分失败" },
  failed: { background: "#fee2e2", color: "#b91c1c", label: "失败" },
  cancelled: { background: "#e5e7eb", color: "#6b7280", label: "已取消" },
};

export function SearchRunDetailScreen({
  detail,
  onBackToRunList,
  onRetrySource,
  onCancelRun,
  onCsvExport,
}: SearchRunDetailScreenProps) {
  if (detail === null) {
    return (
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <button
            style={{
              border: "1px solid #d0d7e2",
              background: "#ffffff",
              borderRadius: "999px",
              padding: "8px 14px",
              cursor: "pointer",
              fontSize: "13px",
            }}
            onClick={onBackToRunList}
          >
            ← 返回运行列表
          </button>
          <div
            style={{
              marginTop: "20px",
              padding: "40px 0",
              textAlign: "center",
              color: "#6b7280",
            }}
          >
            加载中…
          </div>
        </section>
      </section>
    );
  }

  const run = detail.run;
  const sources = detail.sources;
  const statusChip = STATUS_CHIP_STYLES[run.status] ?? STATUS_CHIP_STYLES.pending;
  const canCancel = run.status === "pending" || run.status === "running";
  const prisma = run.prisma ?? {
    identification: 0,
    screening: 0,
    eligibility: 0,
    included: 0,
    by_source: [],
  };

  return (
    <section
      style={{ display: "flex", flexDirection: "column", gap: "20px" }}
      data-testid="search-run-detail-screen"
    >
      <section style={panelStyle}>
        <button
          style={{
            border: "1px solid #d0d7e2",
            background: "#ffffff",
            borderRadius: "999px",
            padding: "8px 14px",
            cursor: "pointer",
            fontSize: "13px",
          }}
          onClick={onBackToRunList}
        >
          ← 返回运行列表
        </button>

        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
            marginTop: "16px",
            flexWrap: "wrap",
            gap: "16px",
          }}
        >
          <div>
            <h2 style={{ margin: "0 0 8px", fontSize: "28px" }}>
              检索运行详情 #{run.id}
            </h2>
            <div
              style={{
                display: "flex",
                gap: "10px",
                alignItems: "center",
                flexWrap: "wrap",
              }}
            >
              <span
                style={{
                  background: statusChip.background,
                  color: statusChip.color,
                  borderRadius: "999px",
                  padding: "4px 12px",
                  fontSize: "12px",
                  fontWeight: 600,
                }}
              >
                {statusChip.label}
              </span>
              <span style={{ color: "#6b7280", fontSize: "13px" }}>
                创建于 {run.created_at ?? "—"}
              </span>
              {run.eta_seconds != null && (
                <span
                  style={{
                    background: "#f8fafc",
                    color: "#334155",
                    borderRadius: "6px",
                    padding: "3px 10px",
                    fontSize: "12px",
                  }}
                >
                  预计耗时 {run.eta_seconds}s
                </span>
              )}
            </div>
          </div>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {canCancel && (
              <button
                style={{
                  border: "1px solid #d0d7e2",
                  background: "#ffffff",
                  color: "#374151",
                  borderRadius: "999px",
                  padding: "8px 16px",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: 600,
                }}
                onClick={() => void onCancelRun()}
              >
                取消运行
              </button>
            )}
            <button
              style={{
                border: "none",
                background: "#111827",
                color: "#f9fafb",
                borderRadius: "999px",
                padding: "8px 16px",
                cursor: "pointer",
                fontSize: "13px",
                fontWeight: 600,
              }}
              onClick={onCsvExport}
            >
              导出 CSV
            </button>
          </div>
        </div>

        <div
          style={{
            marginTop: "20px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
            gap: "16px",
          }}
        >
          <div
            style={{
              padding: "16px",
              background: "#f8fafc",
              borderRadius: "14px",
              border: "1px solid #e5e7eb",
            }}
          >
            <div style={{ fontSize: "12px", color: "#64748b" }}>原始命中</div>
            <div style={{ marginTop: "6px", fontSize: "22px", fontWeight: 700 }}>
              {run.total_hits_raw?.toLocaleString() ?? 0}
            </div>
          </div>
          <div
            style={{
              padding: "16px",
              background: "#f8fafc",
              borderRadius: "14px",
              border: "1px solid #e5e7eb",
            }}
          >
            <div style={{ fontSize: "12px", color: "#64748b" }}>去重后</div>
            <div style={{ marginTop: "6px", fontSize: "22px", fontWeight: 700 }}>
              {run.total_after_dedupe?.toLocaleString() ?? 0}
            </div>
          </div>
          <div
            style={{
              padding: "16px",
              background: "#dbeafe",
              borderRadius: "14px",
              border: "1px solid #bfdbfe",
            }}
          >
            <div style={{ fontSize: "12px", color: "#1e40af" }}>PRISMA 识别</div>
            <div style={{ marginTop: "6px", fontSize: "22px", fontWeight: 700, color: "#1e3a8a" }}>
              {prisma.identification ?? 0}
            </div>
          </div>
          <div
            style={{
              padding: "16px",
              background: "#dcfce7",
              borderRadius: "14px",
              border: "1px solid #bbf7d0",
            }}
          >
            <div style={{ fontSize: "12px", color: "#166534" }}>PRISMA 纳入</div>
            <div style={{ marginTop: "6px", fontSize: "22px", fontWeight: 700, color: "#14532d" }}>
              {prisma.included ?? 0}
            </div>
          </div>
        </div>
      </section>

      <section style={panelStyle}>
        <h3 style={{ marginTop: 0, marginBottom: "16px" }}>各数据源明细</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {sources.map((src) => {
            const sStyle = STATUS_CHIP_STYLES[src.status] ?? STATUS_CHIP_STYLES.pending;
            const showRetry = src.status === "failed" || src.status === "partial_failed";
            return (
              <div
                key={src.source_key}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "12px",
                  padding: "14px 16px",
                }}
              >
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    flexWrap: "wrap",
                    gap: "12px",
                  }}
                >
                  <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
                    <span style={{ fontSize: "15px", fontWeight: 700 }}>
                      {src.source_label}
                    </span>
                    <span
                      style={{
                        background: sStyle.background,
                        color: sStyle.color,
                        borderRadius: "999px",
                        padding: "3px 10px",
                        fontSize: "12px",
                        fontWeight: 600,
                      }}
                    >
                      {sStyle.label}
                    </span>
                    <span style={{ fontSize: "13px", color: "#4b5563" }}>
                      检索 {src.records_retrieved ?? 0} / 入库{" "}
                      {src.records_imported ?? 0}
                    </span>
                  </div>
                  {showRetry && (
                    <button
                      style={{
                        border: "1px solid #2563eb",
                        background: "#eff6ff",
                        color: "#1d4ed8",
                        borderRadius: "999px",
                        padding: "6px 14px",
                        cursor: "pointer",
                        fontSize: "12px",
                        fontWeight: 600,
                      }}
                      onClick={() => void onRetrySource(src.source_key)}
                    >
                      重试该源
                    </button>
                  )}
                </div>

                {src.error_message && (
                  <div
                    style={{
                      marginTop: "10px",
                      padding: "10px 12px",
                      background: "#fef2f2",
                      color: "#b91c1c",
                      borderRadius: "8px",
                      fontSize: "13px",
                    }}
                  >
                    错误：{src.error_message}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </section>
    </section>
  );
}

export type { SearchRunDetailScreenProps };
