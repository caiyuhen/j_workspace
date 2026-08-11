import { useState } from "react";

import type {
  ImportLiteraturePayload,
  LiteratureLibrarySummary,
} from "@meda/shared-sdk";

export type LiteratureLibraryScreenProps = {
  library: LiteratureLibrarySummary;
  onBackToStageEntry: () => void;
  onImport: (payload: ImportLiteraturePayload) => void;
  onConfirmUnique: (recordId: number) => void;
};

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

export function LiteratureLibraryScreen({
  library,
  onBackToStageEntry,
  onImport,
  onConfirmUnique,
}: LiteratureLibraryScreenProps) {
  const defaultSource = library.available_sources.find(
    (s) => s.key === "pubmed",
  )?.key ?? library.available_sources[0]?.key ?? "";
  const [sourceKey, setSourceKey] = useState(defaultSource);
  const [rawText, setRawText] = useState("");
  const [pendingConfirmId, setPendingConfirmId] = useState<number | null>(null);
  const [emptyHint, setEmptyHint] = useState(false);

  const { stats, last_import_result: importResult } = library;

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
          <h3 style={{ marginTop: 0 }}>条目列表</h3>
          {library.records.length === 0 ? (
            <div style={{ color: "#6b7280" }}>尚未导入任何文献条目</div>
          ) : (
            <div
              style={{
                maxHeight: "640px",
                overflowY: "auto",
                paddingRight: "4px",
              }}
            >
              {library.records.map((record) => {
                const badge =
                  badgeStyles[record.dedupe_status] ?? badgeStyles.unknown;
                const isConfirming = pendingConfirmId === record.id;

                return (
                  <div
                    key={record.id}
                    style={{
                      marginBottom: "12px",
                      border: "1px solid #e5e7eb",
                      borderRadius: "12px",
                      padding: "12px 14px",
                    }}
                  >
                    <div style={{ display: "flex", gap: "10px", alignItems: "baseline" }}>
                      <span style={{ fontWeight: 600 }}>{record.title}</span>
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
                    </div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {record.authors} · {record.journal} · {record.year ?? "年份未知"} ·{" "}
                      {record.source_label}
                    </div>
                    <div
                      style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                    >
                      {record.doi === "" ? "" : `DOI ${record.doi}`}
                      {record.pmid === "" ? "" : ` · PMID ${record.pmid}`}
                    </div>
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
