import React, { useState } from "react";

import { PrismaChart, type PrismaSourceBreakdown } from "./PrismaChart";
import {
  STATUS_CHIP_STYLES,
  formatRelativeTime,
  type SearchRunStatus,
} from "./SearchRunListScreen";

export type SearchRunSourceStatus =
  | "pending"
  | "running"
  | "completed"
  | "failed";

export type SearchRunSourceDetail = {
  id: number;
  source_key: string;
  source_label: string;
  status: SearchRunSourceStatus;
  records_retrieved: number;
  records_imported: number;
  started_at?: string | null;
  finished_at?: string | null;
  error_message?: string | null;
  raw_response_excerpt?: string | null;
};

export type SearchRunPrismaReport = {
  identification: number;
  screening: number;
  eligibility: number;
  included: number;
  by_source: PrismaSourceBreakdown[];
};

export type SearchRunDetailShape = {
  id: number;
  project_id: number;
  search_query_version_id?: number | null;
  status: SearchRunStatus;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
  query_snapshot?: Record<string, unknown> | null;
  selected_sources: string[];
  total_hits_raw: number;
  total_after_dedupe: number;
  prisma: SearchRunPrismaReport;
  csv_url?: string | null;
  sources: SearchRunSourceDetail[];
  associated_records?: Array<{
    id: number;
    title: string;
    authors: string;
    journal: string;
    year?: number | null;
    source_label: string;
  }>;
};

export type SearchRunDetailScreenProps = {
  detail: SearchRunDetailShape;
  onBackToList: () => void;
  onRun?: (runId: number) => void;
  onCancel?: (runId: number) => void;
  onRetry?: (runId: number) => void;
  onRetrySource?: (runId: number, sourceKey: string) => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

const SOURCE_STATUS_STYLES: Record<
  SearchRunSourceStatus,
  { background: string; color: string; label: string }
> = {
  pending: { background: "#f3f4f6", color: "#4b5563", label: "等待中" },
  running: { background: "#dbeafe", color: "#1d4ed8", label: "运行中" },
  completed: { background: "#dcfce7", color: "#047857", label: "已完成" },
  failed: { background: "#fee2e2", color: "#b91c1c", label: "失败" },
};

function calculateElapsedSeconds(
  started_at?: string | null,
  finished_at?: string | null,
): number | null {
  if (!started_at) return null;
  const start = new Date(started_at).getTime();
  const end = finished_at ? new Date(finished_at).getTime() : Date.now();
  return Math.max(0, Math.floor((end - start) / 1000));
}

function LiteratureRecordLine({
  record,
}: {
  record: NonNullable<SearchRunDetailShape["associated_records"]>[number];
}) {
  return (
    <div
      key={record.id}
      data-testid={`record-line-${record.id}`}
      style={{
        padding: "10px 12px",
        borderBottom: "1px solid #f3f4f6",
      }}
    >
      <div style={{ fontSize: "14px", fontWeight: 600, color: "#111827" }}>
        {record.title}
      </div>
      <div style={{ fontSize: "12px", color: "#6b7280", marginTop: "3px" }}>
        {record.authors} · {record.journal}
        {record.year ? ` · ${record.year}` : ""} · {record.source_label}
      </div>
    </div>
  );
}

export function SearchRunDetailScreen({
  detail,
  onBackToList,
  onRun,
  onCancel,
  onRetry,
  onRetrySource,
}: SearchRunDetailScreenProps) {
  const [expandedSources, setExpandedSources] = useState<Record<string, boolean>>({});
  const elapsed = calculateElapsedSeconds(detail.started_at, detail.finished_at);
  const statusChip = STATUS_CHIP_STYLES[detail.status];

  const toggleSource = (key: string) => {
    setExpandedSources((cur) => ({ ...cur, [key]: !cur[key] }));
  };

  const topRecords = (detail.associated_records ?? []).slice(0, 200);

  return (
    <section
      style={{ display: "flex", flexDirection: "column", gap: "20px" }}
      data-testid="search-run-detail-screen"
    >
      <section style={panelStyle} data-testid="detail-overview-card">
        <button
          style={{
            border: "1px solid #d0d7e2",
            background: "#ffffff",
            borderRadius: "999px",
            padding: "8px 14px",
            cursor: "pointer",
            fontSize: "13px",
          }}
          onClick={onBackToList}
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
              检索运行 #{detail.id}
            </h2>
            <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
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
                创建于 {formatRelativeTime(detail.created_at)}
              </span>
              {detail.started_at && (
                <span style={{ color: "#6b7280", fontSize: "13px" }}>
                  启动于 {new Date(detail.started_at).toLocaleString()}
                </span>
              )}
              {detail.finished_at && (
                <span style={{ color: "#6b7280", fontSize: "13px" }}>
                  结束于 {new Date(detail.finished_at).toLocaleString()}
                </span>
              )}
              {elapsed != null && (
                <span
                  style={{
                    background: "#f8fafc",
                    color: "#334155",
                    borderRadius: "6px",
                    padding: "3px 10px",
                    fontSize: "12px",
                  }}
                >
                  耗时 {elapsed}s
                </span>
              )}
            </div>
          </div>

          <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
            {onRun &&
              (detail.status === "pending" ||
                detail.status === "cancelled" ||
                detail.status === "failed" ||
                detail.status === "partial_failed") && (
                <button
                  data-testid="btn-run"
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
                  onClick={() => onRun(detail.id)}
                >
                  运行
                </button>
              )}
            {onCancel && detail.status === "running" && (
              <button
                data-testid="btn-cancel"
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
                onClick={() => onCancel(detail.id)}
              >
                取消
              </button>
            )}
            {onRetry &&
              (detail.status === "failed" ||
                detail.status === "partial_failed" ||
                detail.status === "cancelled") && (
              <button
                data-testid="btn-retry"
                style={{
                  border: "1px solid #2563eb",
                  background: "#eff6ff",
                  color: "#1d4ed8",
                  borderRadius: "999px",
                  padding: "8px 16px",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: 600,
                }}
                onClick={() => onRetry(detail.id)}
              >
                重试
              </button>
            )}
            {detail.csv_url && (
              <a
                data-testid="csv-export-link"
                href={detail.csv_url}
                style={{
                  border: "1px solid #d0d7e2",
                  background: "#ffffff",
                  color: "#374151",
                  borderRadius: "999px",
                  padding: "8px 16px",
                  textDecoration: "none",
                  fontSize: "13px",
                  fontWeight: 600,
                }}
              >
                导出 CSV
              </a>
            )}
          </div>
        </div>

        <div
          style={{
            marginTop: "20px",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
            gap: "16px",
          }}
        >
          {detail.search_query_version_id != null && (
            <div
              style={{
                padding: "12px",
                background: "#f8fafc",
                borderRadius: "10px",
              }}
            >
              <div style={{ fontSize: "12px", color: "#64748b" }}>检索式版本</div>
              <div style={{ marginTop: "4px", fontSize: "14px", fontWeight: 600 }}>
                <a style={{ color: "#2563eb", textDecoration: "none" }} href="#">
                  版本 #{detail.search_query_version_id} →
                </a>
              </div>
            </div>
          )}
          <div
            style={{
              padding: "12px",
              background: "#f8fafc",
              borderRadius: "10px",
            }}
          >
            <div style={{ fontSize: "12px", color: "#64748b" }}>已选数据源</div>
            <div style={{ marginTop: "4px", fontSize: "14px", fontWeight: 600 }}>
              {detail.selected_sources.join(", ")}
            </div>
          </div>
          <div
            style={{
              padding: "12px",
              background: "#f8fafc",
              borderRadius: "10px",
            }}
          >
            <div style={{ fontSize: "12px", color: "#64748b" }}>原始命中</div>
            <div style={{ marginTop: "4px", fontSize: "14px", fontWeight: 600 }}>
              {detail.total_hits_raw.toLocaleString()} 条
            </div>
          </div>
          <div
            style={{
              padding: "12px",
              background: "#f8fafc",
              borderRadius: "10px",
            }}
          >
            <div style={{ fontSize: "12px", color: "#64748b" }}>去重后入库</div>
            <div style={{ marginTop: "4px", fontSize: "14px", fontWeight: 600 }}>
              {detail.total_after_dedupe.toLocaleString()} 条
            </div>
          </div>
        </div>
      </section>

      <section style={panelStyle} data-testid="detail-prisma-section">
        <h3 style={{ marginTop: 0, marginBottom: "16px" }}>PRISMA 文献筛选漏斗</h3>
        <PrismaChart
          identification={detail.prisma.identification}
          screening={detail.prisma.screening}
          eligibility={detail.prisma.eligibility}
          included={detail.prisma.included}
          by_source={detail.prisma.by_source}
        />
      </section>

      <section style={panelStyle} data-testid="detail-sources-section">
        <h3 style={{ marginTop: 0, marginBottom: "16px" }}>各数据源明细</h3>
        <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
          {detail.sources.map((src) => {
            const sStyle = SOURCE_STATUS_STYLES[src.status];
            const expanded = !!expandedSources[src.source_key];
            return (
              <div
                key={src.source_key}
                data-testid={`source-detail-${src.source_key}`}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "12px",
                  padding: "14px 16px",
                  cursor: "pointer",
                }}
                onClick={() => toggleSource(src.source_key)}
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
                      检索 {src.records_retrieved} / 入库 {src.records_imported}
                    </span>
                  </div>
                  {onRetrySource && src.status === "failed" && (
                    <button
                      data-testid={`btn-retry-src-${src.source_key}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        onRetrySource(detail.id, src.source_key);
                      }}
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
                    >
                      重跑该库
                    </button>
                  )}
                </div>

                {src.error_message && (
                  <div
                    data-testid={`src-error-${src.source_key}`}
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

                {expanded && src.raw_response_excerpt && (
                  <pre
                    data-testid={`src-raw-${src.source_key}`}
                    style={{
                      marginTop: "10px",
                      padding: "12px",
                      background: "#0f172a",
                      color: "#e2e8f0",
                      borderRadius: "8px",
                      fontSize: "11px",
                      overflowX: "auto",
                      whiteSpace: "pre-wrap",
                      maxHeight: "200px",
                      overflowY: "auto",
                    }}
                  >
                    {src.raw_response_excerpt}
                  </pre>
                )}
              </div>
            );
          })}
        </div>
      </section>

      {topRecords.length > 0 && (
        <section style={panelStyle} data-testid="detail-records-section">
          <h3 style={{ marginTop: 0, marginBottom: "8px" }}>
            入库文献条目（Top 200）
          </h3>
          <div style={{ color: "#6b7280", fontSize: "13px", marginBottom: "12px" }}>
            共 {topRecords.length} 条
          </div>
          <div
            style={{
              maxHeight: "480px",
              overflowY: "auto",
              border: "1px solid #e5e7eb",
              borderRadius: "10px",
            }}
          >
            {topRecords.map((r) => (
              <LiteratureRecordLine key={r.id} record={r} />
            ))}
          </div>
        </section>
      )}
    </section>
  );
}
