import { useMemo, useState } from "react";

import type {
  ImportLiteraturePayload,
  LiteratureLibrarySummary,
  LiteratureRecordSummary,
} from "@meda/shared-sdk";

import { PicoPanel, type PicoFieldValues } from "./PicoPanel";

export type LiteratureLibrarySortKey =
  | "default"
  | "relevance"
  | "year_desc"
  | "journal";

export type LiteratureLibraryInitialFilter = {
  searchRunId?: number | null;
};

export type LiteratureLibraryScreenProps = {
  library: LiteratureLibrarySummary;
  onBackToStageEntry: () => void;
  onImport: (payload: ImportLiteraturePayload) => void;
  onConfirmUnique: (recordId: number) => void;
  initialFilter?: LiteratureLibraryInitialFilter;
  onClearFilter?: () => void;
  sort?: LiteratureLibrarySortKey;
  onSortChange?: (sort: LiteratureLibrarySortKey) => void;
  recordPico?: Record<number, PicoFieldValues | undefined>;
};

export const SORT_OPTIONS: Array<{
  key: LiteratureLibrarySortKey;
  label: string;
}> = [
  { key: "default", label: "入库顺序 默认" },
  { key: "relevance", label: "BM25 相关性(高→低)" },
  { key: "year_desc", label: "最新发表" },
  { key: "journal", label: "期刊" },
];

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

const badgeStyles: Record<string, { background: string; color: string; label: string }> = {
  unique: { background: "#ecfdf5", color: "#047857", label: "唯一" },
  duplicate: { background: "#fef2f2", color: "#b91c1c", label: "重复" },
  confirmed_unique: { background: "#eff6ff", color: "#1d4ed8", label: "已确认独立" },
  unknown: { background: "#f3f4f6", color: "#4b5563", label: "未知状态" },
};

type ExtendedRecord = LiteratureRecordSummary & {
  relevance_score?: number | null;
  pico_status?: string | null;
};

function sortRecords(
  records: LiteratureRecordSummary[],
  sort: LiteratureLibrarySortKey,
): LiteratureRecordSummary[] {
  const arr = records.slice();
  switch (sort) {
    case "relevance":
      return arr.sort((a, b) => {
        const as = (a as ExtendedRecord).relevance_score ?? 0;
        const bs = (b as ExtendedRecord).relevance_score ?? 0;
        return bs - as;
      });
    case "year_desc":
      return arr.sort((a, b) => (b.year ?? 0) - (a.year ?? 0));
    case "journal":
      return arr.sort((a, b) => a.journal.localeCompare(b.journal));
    default:
      return arr;
  }
}

export function LiteratureLibraryScreen({
  library,
  onBackToStageEntry,
  onImport,
  onConfirmUnique,
  initialFilter,
  onClearFilter,
  sort: propSort,
  onSortChange,
  recordPico,
}: LiteratureLibraryScreenProps) {
  const defaultSource = library.available_sources.find(
    (s) => s.key === "pubmed",
  )?.key ?? library.available_sources[0]?.key ?? "";
  const [sourceKey, setSourceKey] = useState(defaultSource);
  const [rawText, setRawText] = useState("");
  const [pendingConfirmId, setPendingConfirmId] = useState<number | null>(null);
  const [emptyHint, setEmptyHint] = useState(false);
  const [internalSort, setInternalSort] =
    useState<LiteratureLibrarySortKey>("default");
  const [openPicoRecordId, setOpenPicoRecordId] = useState<number | null>(null);
  const [hoveredRecordId, setHoveredRecordId] = useState<number | null>(null);

  const sort: LiteratureLibrarySortKey = propSort ?? internalSort;

  const { stats, last_import_result: importResult } = library;

  const handleSortChange = (next: LiteratureLibrarySortKey) => {
    setInternalSort(next);
    onSortChange?.(next);
  };

  const handleImportClick = () => {
    if (rawText.trim() === "") {
      setEmptyHint(true);
      setTimeout(() => setEmptyHint(false), 2500);
      return;
    }
    setEmptyHint(false);
    onImport({ source_key: sourceKey, raw_text: rawText });
  };

  const handleConfirmUnique = (recordId: number) => {
    setPendingConfirmId(recordId);
    try {
      onConfirmUnique(recordId);
    } finally {
      setTimeout(() => setPendingConfirmId(null), 1200);
    }
  };

  const displayedRecords = useMemo(
    () => sortRecords(library.records, sort),
    [library.records, sort],
  );

  const searchRunId = initialFilter?.searchRunId ?? null;

  return (
    <>
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <button
            style={{
              border: "1px solid #d0d7e2",
              background: "#ffffff",
              borderRadius: "999px",
              padding: "8px 14px",
              cursor: "pointer",
            }}
            onClick={onBackToStageEntry}
          >
            返回检索阶段入口页
          </button>
          <h2 style={{ margin: "16px 0 8px", fontSize: "30px" }}>文献条目库</h2>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>
            {library.project.name}
          </div>

          {searchRunId != null && (
            <div
              data-testid="breadcrumb-search-run"
              style={{
                marginTop: "14px",
                display: "inline-flex",
                alignItems: "center",
                gap: "10px",
                background: "#eef2ff",
                color: "#3730a3",
                borderRadius: "999px",
                padding: "6px 12px",
                fontSize: "13px",
                fontWeight: 500,
              }}
            >
              <span>范围：检索运行 #{searchRunId}</span>
              {onClearFilter && (
                <button
                  data-testid="btn-clear-filter"
                  onClick={onClearFilter}
                  style={{
                    border: "none",
                    background: "#ffffff",
                    color: "#4338ca",
                    borderRadius: "999px",
                    padding: "2px 10px",
                    cursor: "pointer",
                    fontSize: "12px",
                    fontWeight: 600,
                  }}
                >
                  清除筛选
                </button>
              )}
            </div>
          )}
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>导入条目</h3>
          <div style={{ display: "flex", gap: "12px", alignItems: "center" }}>
            <label htmlFor="literature-source">来源</label>
            <select
              id="literature-source"
              value={sourceKey}
              onChange={(event) => setSourceKey(event.target.value)}
              style={{
                border: "1px solid #d0d7e2",
                borderRadius: "10px",
                padding: "8px 10px",
              }}
            >
              {library.available_sources.map((source) => (
                <option key={source.key} value={source.key}>
                  {source.label}
                </option>
              ))}
            </select>
          </div>

          <textarea
            aria-label="粘贴文献条目"
            value={rawText}
            onChange={(event) => setRawText(event.target.value)}
            rows={6}
            style={{
              width: "100%",
              marginTop: "12px",
              border: "1px solid #d0d7e2",
              borderRadius: "12px",
              padding: "10px 12px",
              fontFamily: "inherit",
              boxSizing: "border-box",
            }}
          />

          <button
            style={{
              marginTop: "12px",
              border: "none",
              background: "#111827",
              color: "#f9fafb",
              borderRadius: "999px",
              padding: "10px 16px",
              cursor: rawText.trim() === "" ? "not-allowed" : "pointer",
              opacity: rawText.trim() === "" ? 0.6 : 1,
            }}
            onClick={handleImportClick}
          >
            导入
          </button>

          {emptyHint ? (
            <div style={{ marginTop: "12px", color: "#b91c1c" }}>
              请先粘贴要导入的文献条目
            </div>
          ) : null}

          {importResult === null ? null : (
            <div style={{ marginTop: "12px", color: "#4b5563" }}>
              本次导入 {importResult.imported_count} 条 · 重复{" "}
              {importResult.duplicate_count} 条 · 跳过{" "}
              {importResult.skipped_count} 条
            </div>
          )}
        </section>

        <section style={panelStyle}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              flexWrap: "wrap",
              gap: "10px",
              marginBottom: "12px",
            }}
          >
            <h3 style={{ marginTop: 0, marginBottom: 0 }}>条目列表</h3>
            <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
              <label
                htmlFor="library-sort"
                style={{ fontSize: "13px", color: "#4b5563" }}
              >
                排序：
              </label>
              <select
                id="library-sort"
                data-testid="library-sort-dropdown"
                value={sort}
                onChange={(e) =>
                  handleSortChange(e.target.value as LiteratureLibrarySortKey)
                }
                style={{
                  border: "1px solid #d0d7e2",
                  borderRadius: "10px",
                  padding: "6px 10px",
                  fontSize: "13px",
                }}
              >
                {SORT_OPTIONS.map((opt) => (
                  <option
                    key={opt.key}
                    data-testid={`sort-option-${opt.key}`}
                    value={opt.key}
                  >
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {displayedRecords.length === 0 ? (
            <div style={{ color: "#6b7280" }}>尚未导入任何文献条目</div>
          ) : (
            <div
              style={{
                maxHeight: "640px",
                overflowY: "auto",
                paddingRight: "4px",
              }}
            >
              {displayedRecords.map((rawRecord) => {
                const record = rawRecord as ExtendedRecord;
                const badge =
                  badgeStyles[record.dedupe_status] ?? badgeStyles.unknown;
                const isConfirming = pendingConfirmId === record.id;
                const isHovered = hoveredRecordId === record.id;
                const picoOpen = openPicoRecordId === record.id;
                const picoValues = recordPico?.[record.id];

                return (
                  <div
                    key={record.id}
                    data-testid={`record-card-${record.id}`}
                    onMouseEnter={() => setHoveredRecordId(record.id)}
                    onMouseLeave={() => setHoveredRecordId(null)}
                    style={{
                      marginBottom: "12px",
                      border: "1px solid #e5e7eb",
                      borderRadius: "12px",
                      padding: "12px 14px",
                      position: "relative",
                    }}
                  >
                    <div
                      style={{
                        display: "flex",
                        gap: "10px",
                        alignItems: "baseline",
                      }}
                    >
                      <span style={{ fontWeight: 600 }}>{record.title}</span>
                      {record.relevance_score != null && (
                        <span
                          data-testid={`bm25-badge-${record.id}`}
                          style={{
                            background: "#fffbeb",
                            color: "#b45309",
                            borderRadius: "6px",
                            padding: "2px 7px",
                            fontSize: "11px",
                            fontWeight: 700,
                          }}
                        >
                          ⭐ {record.relevance_score.toFixed(2)}
                        </span>
                      )}
                      <span
                        style={{
                          background: badge.background,
                          color: badge.color,
                          borderRadius: "999px",
                          padding: "2px 10px",
                          fontSize: "12px",
                        }}
                      >
                        {badge.label}
                      </span>
                      {isHovered && (
                        <button
                          data-testid={`pico-toggle-btn-${record.id}`}
                          onClick={() =>
                            setOpenPicoRecordId(picoOpen ? null : record.id)
                          }
                          style={{
                            border: "1px solid #d0d7e2",
                            background: "#ffffff",
                            borderRadius: "999px",
                            padding: "2px 8px",
                            cursor: "pointer",
                            fontSize: "12px",
                            marginLeft: "auto",
                          }}
                          aria-label="查看 PICO"
                        >
                          🏷️
                        </button>
                      )}
                    </div>
                    <div
                      style={{
                        marginTop: "4px",
                        color: "#6b7280",
                        fontSize: "13px",
                      }}
                    >
                      {record.authors} · {record.journal} ·{" "}
                      {record.year ?? "年份未知"} · {record.source_label}
                    </div>
                    <div
                      style={{
                        marginTop: "4px",
                        color: "#6b7280",
                        fontSize: "13px",
                      }}
                    >
                      {record.doi === "" ? "" : `DOI ${record.doi}`}
                      {record.pmid === "" ? "" : ` · PMID ${record.pmid}`}
                    </div>

                    {picoOpen && (
                      <div
                        data-testid={`pico-inline-drawer-${record.id}`}
                        style={{
                          marginTop: "12px",
                          padding: "12px",
                          background: "#f8fafc",
                          borderRadius: "10px",
                          border: "1px solid #e2e8f0",
                        }}
                      >
                        <PicoPanel pico={picoValues} compact />
                      </div>
                    )}

                    {record.dedupe_status === "duplicate" ? (
                      <button
                        disabled={isConfirming}
                        style={{
                          marginTop: "10px",
                          border: "1px solid #d0d7e2",
                          background: isConfirming ? "#f9fafb" : "#ffffff",
                          borderRadius: "999px",
                          padding: "6px 12px",
                          cursor: isConfirming ? "progress" : "pointer",
                          opacity: isConfirming ? 0.7 : 1,
                        }}
                        onClick={() => handleConfirmUnique(record.id)}
                      >
                        {isConfirming ? "处理中..." : "标记为独立文献"}
                      </button>
                    ) : null}
                  </div>
                );
              })}
            </div>
          )}
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>集合统计</h3>
          <div>
            共 {stats.total_count} 条 · 唯一 {stats.unique_count} 条 · 重复{" "}
            {stats.duplicate_count} 条
          </div>
          <div style={{ marginTop: "12px" }}>
            {stats.by_source.map((item) => (
              <div key={item.source_key} style={{ marginTop: "6px", color: "#4b5563" }}>
                {item.source_label}：{item.count} 条
              </div>
            ))}
          </div>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>最近导入</h3>
          {library.recent_batches.length === 0 ? (
            <div style={{ color: "#6b7280" }}>暂无导入记录</div>
          ) : (
            library.recent_batches.map((batch) => (
              <div key={batch.id} style={{ marginTop: "8px", color: "#4b5563" }}>
                {batch.source_label} · 解析 {batch.parsed_count} 条 · 重复{" "}
                {batch.duplicate_count} 条 · 跳过 {batch.skipped_count} 条
              </div>
            ))
          )}
        </section>
      </aside>
    </>
  );
}
