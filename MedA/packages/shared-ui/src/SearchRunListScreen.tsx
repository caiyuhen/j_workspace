import type {
  ProjectSummary,
  SearchQueryEditorSummary,
  SearchRunListItem,
  SearchRunListResponse,
} from "@meda/shared-sdk";

type SearchRunListScreenProps = {
  runs: SearchRunListResponse | null;
  editor: SearchQueryEditorSummary | null;
  onBackToStageEntry?: () => void;
  onCreateRun?: () => Promise<void> | void;
  onOpenRunDetail?: (runId: number) => void;
  // lightweight standalone mode: render just the list (no project/editor UI)
  standaloneRuns?: SearchRunListItem[];
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

export type SearchRunStatus =
  | "pending"
  | "running"
  | "completed"
  | "partial_failed"
  | "failed"
  | "cancelled";

export const STATUS_CHIP_STYLES: Record<
  SearchRunStatus,
  {
    background: string;
    color: string;
    label: string;
    className: string;
  }
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
    className: "status-partial-orange",
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

export type SearchRunListItem = {
  id: number;
  status: SearchRunStatus;
  created_at: string;
  sources: Array<{
    key: string;
    retrieved: number;
    imported: number;
  }>;
  prisma: {
    identification: number;
    screening: number;
  };
  progress_percent: number | null;
};

export function formatRelativeTime(isoOrDate: string | Date): string {
  const now = new Date();
  const t =
    typeof isoOrDate === "string" ? new Date(isoOrDate) : isoOrDate;
  const ms = now.getTime() - t.getTime();
  const sec = Math.floor(ms / 1000);
  if (sec < 1) return "刚刚";
  if (sec < 60) return sec === 1 ? "1 秒前" : `${sec} 秒前`;
  const min = Math.floor(sec / 60);
  if (min < 60) return min === 1 ? "1 分钟前" : `${min} 分钟前`;
  const hr = Math.floor(min / 60);
  if (hr < 24) return hr === 1 ? "1 小时前" : `${hr} 小时前`;
  const day = Math.floor(hr / 24);
  if (day === 1) return "昨天";
  if (day < 90) return `${day} 天前`;
  const y = t.getFullYear();
  const m = String(t.getMonth() + 1).padStart(2, "0");
  const d = String(t.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

function resolveProject(
  runs: SearchRunListResponse | null,
  editor: SearchQueryEditorSummary | null,
): ProjectSummary | null {
  return runs?.project ?? editor?.project ?? null;
}

export function SearchRunListScreen({
  runs,
  editor,
  onBackToStageEntry,
  onCreateRun,
  onOpenRunDetail,
  standaloneRuns,
}: SearchRunListScreenProps) {
  const project = resolveProject(runs, editor);
  const runList: SearchRunListItem[] =
    standaloneRuns && standaloneRuns.length > 0
      ? standaloneRuns
      : runs?.runs ?? [];
  const standaloneMode = standaloneRuns !== undefined;

  return (
    <section
      style={{ display: "flex", flexDirection: "column", gap: "20px" }}
      data-testid="search-run-list-screen"
    >
      <section style={panelStyle}>
        {!standaloneMode && (
          <>
            <button
              style={{
                border: "1px solid #d0d7e2",
                background: "#ffffff",
                borderRadius: "999px",
                padding: "8px 14px",
                cursor: "pointer",
                fontSize: "13px",
              }}
              onClick={onBackToStageEntry}
            >
              ← 返回检索阶段
            </button>
            {project !== null && (
              <div style={{ color: "#6b7280", fontSize: "13px", marginTop: "16px" }}>
                {project.name}
              </div>
            )}
          </>
        )}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: standaloneMode ? "0px" : "12px",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "30px" }}>🆕 检索运行记录</h2>
          {!standaloneMode && (
            <button
              data-testid="btn-create-run"
              aria-label="运行当前检索"
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
              onClick={() => void onCreateRun?.()}
            >
              ▶ 运行当前检索
            </button>
          )}
        </div>
        {!standaloneMode && editor !== null && (
          <div
            style={{
              marginTop: "16px",
              padding: "12px 14px",
              borderRadius: "14px",
              background: "#f8fafc",
              border: "1px solid #e5e7eb",
              color: "#475569",
              fontSize: "14px",
            }}
          >
            当前检索式：{editor.query_name}（{editor.query_version}），已选来源：
            {editor.selected_sources.join(", ")}
          </div>
        )}
      </section>

      <section style={panelStyle}>
        {runList.length === 0 ? (
          <div
            style={{
              color: "#6b7280",
              padding: "40px 0",
              textAlign: "center",
              fontSize: "14px",
            }}
          >
            暂无检索运行记录。点击右上角「▶ 运行当前检索」开始第一次检索。
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: "12px" }}>
            {runList.map((run) => {
              const statusChip = STATUS_CHIP_STYLES[run.status] ??
                STATUS_CHIP_STYLES.pending;
              return (
                <div
                  key={run.id}
                  data-testid={`run-row-${run.id}`}
                  onClick={() => onOpenRunDetail(run.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onOpenRunDetail(run.id);
                    }
                  }}
                  role="button"
                  tabIndex={0}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "auto 1fr auto",
                    gap: "16px",
                    alignItems: "center",
                    padding: "14px 16px",
                    border: "1px solid #e5e7eb",
                    borderRadius: "12px",
                    cursor: "pointer",
                    background: "#ffffff",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: "4px",
                      fontSize: "13px",
                    }}
                  >
                    <span style={{ fontWeight: 600 }}>运行 #{run.id}</span>
                    <span style={{ color: "#6b7280" }}>
                      {formatRelativeTime(run.created_at)}
                    </span>
                  </div>

                  <span
                    data-testid={`status-chip-${run.status}`}
                    className={statusChip.className}
                    style={{
                      background: statusChip.background,
                      color: statusChip.color,
                      borderRadius: "999px",
                      padding: "4px 12px",
                      fontSize: "12px",
                      fontWeight: 600,
                      justifySelf: "start",
                    }}
                  >
                    {statusChip.label}
                  </span>

                  <div style={{ fontSize: "12px", color: "#374151" }}>
                    <span style={{ color: "#6b7280" }}>PRISMA 识别→</span>
                    <b style={{ color: "#2563eb" }}>
                      {run.prisma?.identification ?? 0}
                    </b>
                    <span style={{ margin: "0 6px", color: "#94a3b8" }}>/</span>
                    <span style={{ color: "#6b7280" }}>纳入→</span>
                    <b style={{ color: "#15803d" }}>{run.prisma?.screening ?? 0}</b>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>
    </section>
  );
}

export type { SearchRunListScreenProps };
