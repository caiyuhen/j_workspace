import React from "react";

export type SearchRunStatus =
  | "pending"
  | "running"
  | "completed"
  | "partial_failed"
  | "failed"
  | "cancelled";

export type SearchRunSourceBadge = {
  source_key: string;
  source_label: string;
  records_retrieved: number;
  records_imported: number;
};

export type SearchRunMiniPrisma = {
  identification: number;
  screening: number;
};

export type SearchRunListItem = {
  id: number;
  status: SearchRunStatus;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  progress_percent?: number | null;
  sources: SearchRunSourceBadge[];
  prisma: SearchRunMiniPrisma;
};

export type SearchRunListScreenProps = {
  runs: SearchRunListItem[];
  onCreateRun: () => void;
  onSelectRun?: (runId: number) => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

export const STATUS_CHIP_STYLES: Record<
  SearchRunStatus,
  { background: string; color: string; label: string; className?: string }
> = {
  pending: {
    background: "#f3f4f6",
    color: "#4b5563",
    label: "等待中",
    className: "status-pending-grey",
  },
  running: {
    background: "#dbeafe",
    color: "#1d4ed8",
    label: "运行中",
    className: "status-running-blue",
  },
  completed: {
    background: "#dcfce7",
    color: "#047857",
    label: "已完成",
    className: "status-completed-green",
  },
  partial_failed: {
    background: "#ffedd5",
    color: "#c2410c",
    label: "部分失败",
    className: "status-partial_orange",
  },
  failed: {
    background: "#fee2e2",
    color: "#b91c1c",
    label: "失败",
    className: "status-failed-red",
  },
  cancelled: {
    background: "#e5e7eb",
    color: "#6b7280",
    label: "已取消",
    className: "status-cancelled-grey",
  },
};

export function formatRelativeTime(isoString: string): string {
  const now = new Date().getTime();
  const then = new Date(isoString).getTime();
  const diffMs = now - then;
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec <= 0) return "刚刚";

  if (diffSec < 60) return diffSec === 1 ? "1 秒前" : `${diffSec} 秒前`;

  const diffMin = Math.floor(diffSec / 60);
  if (diffMin < 60) return diffMin === 1 ? "1 分钟前" : `${diffMin} 分钟前`;

  const diffHour = Math.floor(diffMin / 60);
  if (diffHour < 24) return diffHour === 1 ? "1 小时前" : `${diffHour} 小时前`;

  const diffDay = Math.floor(diffHour / 24);
  if (diffDay <= 90) return diffDay === 1 ? "昨天" : `${diffDay} 天前`;

  const date = new Date(isoString);
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function StatusChip({
  status,
  progressPercent,
}: {
  status: SearchRunStatus;
  progressPercent?: number | null;
}) {
  const style = STATUS_CHIP_STYLES[status];
  const showPulse = status === "running";
  return (
    <span
      data-testid={`status-chip-${status}`}
      className={style.className}
      style={{
        background: style.background,
        color: style.color,
        borderRadius: "999px",
        padding: "4px 12px",
        fontSize: "12px",
        fontWeight: 600,
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
      }}
    >
      {showPulse && (
        <span
          data-testid="running-pulse-dot"
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            background: style.color,
          }}
        />
      )}
      {style.label}
      {progressPercent != null && status === "running"
        ? ` ${progressPercent}%`
        : ""}
    </span>
  );
}

export function SearchRunListScreen({
  runs,
  onCreateRun,
  onSelectRun,
}: SearchRunListScreenProps) {
  return (
    <section
      style={{ display: "flex", flexDirection: "column", gap: "20px" }}
      data-testid="search-run-list-screen"
    >
      <section style={panelStyle}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "30px" }}>检索运行记录</h2>
          <button
            data-testid="btn-create-run"
            style={{
              border: "none",
              background: "#111827",
              color: "#f9fafb",
              borderRadius: "999px",
              padding: "10px 20px",
              cursor: "pointer",
              fontWeight: 600,
              fontSize: "14px",
            }}
            onClick={onCreateRun}
          >
            运行当前检索
          </button>
        </div>
      </section>

      <section style={panelStyle}>
        {runs.length === 0 ? (
          <div style={{ color: "#6b7280", padding: "40px 0", textAlign: "center" }}>
            暂无检索运行记录。点击右上角「运行当前检索」开始第一次检索。
          </div>
        ) : (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr",
              gap: "12px",
            }}
          >
            {runs.map((run) => (
              <div
                key={run.id}
                data-testid={`run-row-${run.id}`}
                onClick={() => onSelectRun?.(run.id)}
                style={{
                  display: "grid",
                  gridTemplateColumns: "140px 140px 1fr auto",
                  gap: "16px",
                  alignItems: "center",
                  padding: "14px 16px",
                  border: "1px solid #e5e7eb",
                  borderRadius: "12px",
                  cursor: onSelectRun ? "pointer" : "default",
                  background: onSelectRun ? "#ffffff" : "transparent",
                }}
              >
                <div
                  style={{
                    color: "#6b7280",
                    fontSize: "13px",
                  }}
                  data-testid={`run-created-${run.id}`}
                >
                  {formatRelativeTime(run.created_at)}
                </div>

                <StatusChip
                  status={run.status}
                  progressPercent={run.progress_percent}
                />

                <div
                  style={{
                    display: "flex",
                    gap: "6px",
                    flexWrap: "wrap",
                  }}
                >
                  {run.sources.slice(0, 3).map((src) => (
                    <span
                      key={src.source_key}
                      data-testid={`src-badge-${run.id}-${src.source_key}`}
                      style={{
                        background: "#f1f5f9",
                        color: "#334155",
                        borderRadius: "6px",
                        padding: "3px 8px",
                        fontSize: "11px",
                        fontWeight: 500,
                      }}
                    >
                      {src.source_label} {src.records_retrieved}/
                      {src.records_imported}
                    </span>
                  ))}
                </div>

                <div
                  style={{
                    display: "flex",
                    gap: "16px",
                    fontSize: "12px",
                    color: "#374151",
                  }}
                  data-testid={`prisma-mini-${run.id}`}
                >
                  <span>
                    <span style={{ color: "#6b7280" }}>识别→</span>
                    <b style={{ color: "#2563eb" }}>
                      {run.prisma.identification}
                    </b>
                  </span>
                  <span>
                    <span style={{ color: "#6b7280" }}>筛选→</span>
                    <b style={{ color: "#3b82f6" }}>{run.prisma.screening}</b>
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </section>
  );
}
