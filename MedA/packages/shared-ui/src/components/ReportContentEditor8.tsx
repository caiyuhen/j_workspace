import React, { useState, useEffect, useCallback, useMemo } from "react";
import type { Report8ChaptersDraft } from "@meda/shared-sdk";

export type ChapterTag = "auto" | "auto_editable" | "manual";

export interface ChapterMetaItem {
  ch: number;
  title: string;
  tag: ChapterTag;
  key: keyof Omit<Report8ChaptersDraft, "source_snapshot_id">;
}

export const CHAPTER_META: ChapterMetaItem[] = [
  { ch: 1, title: "1. Background / 研究背景", tag: "auto_editable", key: "ch1_background" },
  { ch: 2, title: "2. Methods / 方法学", tag: "auto", key: "ch2_methods" },
  { ch: 3, title: "3. PICO Selection / PICO 选择", tag: "auto", key: "ch3_pico" },
  { ch: 4, title: "4. Results / 结果", tag: "auto_editable", key: "ch4_results" },
  { ch: 5, title: "5. GRADE Assessment / GRADE 评估", tag: "auto", key: "ch5_grade_assessment" },
  { ch: 6, title: "6. Summary of Findings / 发现总结", tag: "auto", key: "ch6_summary_of_findings" },
  { ch: 7, title: "7. Discussion / 讨论", tag: "manual", key: "ch7_discussion" },
  { ch: 8, title: "8. Appendices / 附录", tag: "auto_editable", key: "ch8_appendices" },
];

export const TAG_COLOR: Record<ChapterTag, { className: string; label: string }> = {
  auto: { className: "bg-green-100 text-green-800", label: "自动生成 / Auto" },
  auto_editable: { className: "bg-blue-100 text-blue-800", label: "自动可编辑 / Auto-Editable" },
  manual: { className: "bg-amber-100 text-amber-900", label: "人工撰写 / Manual" },
};

const EMPTY_DRAFT: Report8ChaptersDraft = {
  ch1_background: "",
  ch2_methods: "",
  ch3_pico: "",
  ch4_results: "",
  ch5_grade_assessment: "",
  ch6_summary_of_findings: "",
  ch7_discussion: "",
  ch8_appendices: "",
  source_snapshot_id: null,
};

type _ChapterKey = keyof Omit<Report8ChaptersDraft, "source_snapshot_id">;

const _CH_RE_MAP: Record<_ChapterKey, RegExp[]> = {
  ch1_background: [
    /##[^#\n]*\b1\b[^#\n]*Background/i,
    /##[^#\n]*研究背景/i,
  ],
  ch2_methods: [
    /##[^#\n]*\b2\b[^#\n]*Methods/i,
    /##[^#\n]*方法学/i,
  ],
  ch3_pico: [
    /##[^#\n]*\b3\b[^#\n]*PICO/i,
    /##[^#\n]*PICO[^#\n]*选择/i,
  ],
  ch4_results: [
    /##[^#\n]*\b4\b[^#\n]*Results/i,
    /##[^#\n]*结果/i,
  ],
  ch5_grade_assessment: [
    /##[^#\n]*\b5\b[^#\n]*GRADE/i,
    /##[^#\n]*GRADE[^#\n]*评估/i,
  ],
  ch6_summary_of_findings: [
    /##[^#\n]*\b6\b[^#\n]*Summary\s*of\s*Findings/i,
    /##[^#\n]*发现总结/i,
  ],
  ch7_discussion: [
    /##[^#\n]*\b7\b[^#\n]*Discussion/i,
    /##[^#\n]*讨论/i,
  ],
  ch8_appendices: [
    /##[^#\n]*\b8\b[^#\n]*Appendices/i,
    /##[^#\n]*附录/i,
  ],
};

const _CHAPTER_ORDER: _ChapterKey[] = [
  "ch1_background",
  "ch2_methods",
  "ch3_pico",
  "ch4_results",
  "ch5_grade_assessment",
  "ch6_summary_of_findings",
  "ch7_discussion",
  "ch8_appendices",
];

function _matchChapter(line: string): _ChapterKey | null {
  for (const key of _CHAPTER_ORDER) {
    for (const re of _CH_RE_MAP[key]) {
      if (re.test(line)) return key;
    }
  }
  return null;
}

export function parseSnapshotInto8Chapters(snapshot_md: string): Report8ChaptersDraft {
  const result: Report8ChaptersDraft = { ...EMPTY_DRAFT };
  const lines = snapshot_md.split(/\r?\n/);
  let current: _ChapterKey | null = null;
  const buffer: Partial<Record<_ChapterKey, string[]>> = {};

  for (const line of lines) {
    const matched = _matchChapter(line);
    if (matched) {
      current = matched;
      if (!buffer[current]) buffer[current] = [];
      continue;
    }
    if (current) {
      if (!buffer[current]) buffer[current] = [];
      buffer[current]!.push(line);
    }
  }

  for (const key of _CHAPTER_ORDER) {
    const arr = buffer[key];
    result[key] = arr ? arr.join("\n").trim() : "";
  }

  return result;
}

export interface UpstreamDataInput {
  background?: string;
  methods?: string;
  pico?: string;
  results?: string;
  grade?: string;
  sof?: string;
  discussion?: string;
  appendices?: string;
}

export function generateDraftFromUpstream(input: UpstreamDataInput): Report8ChaptersDraft {
  const draft: Report8ChaptersDraft = { ...EMPTY_DRAFT };

  draft.ch1_background = input.background ?? "";
  draft.ch2_methods = input.methods ?? "";
  draft.ch3_pico = input.pico ?? "";
  draft.ch4_results = input.results ?? "";

  let ch5Content = "";
  if (input.grade) ch5Content += input.grade;
  if (ch5Content && input.sof) ch5Content += "\n\n";
  if (input.sof) ch5Content += input.sof;
  draft.ch5_grade_assessment = ch5Content;

  draft.ch6_summary_of_findings = input.sof ?? "";

  let ch7Content = "";
  if (input.discussion) {
    ch7Content += input.discussion;
  } else {
    if (input.grade) {
      if (ch7Content) ch7Content += "\n\n";
      ch7Content += "### GRADE 评估要点\n" + input.grade;
    }
    if (input.sof) {
      if (ch7Content) ch7Content += "\n\n";
      ch7Content += "### 发现总结要点\n" + input.sof;
    }
  }
  draft.ch7_discussion = ch7Content;

  draft.ch8_appendices = input.appendices ?? "";

  return draft;
}

export type Editor8Props = {
  initialValue?: Partial<Report8ChaptersDraft>;
  onValueChange?: (
    next: Report8ChaptersDraft,
    dirtyFields: Set<keyof Report8ChaptersDraft>,
  ) => void;
  upstreamSnapshotMd?: string;
  upstreamData?: UpstreamDataInput;
  onImportUpstream?: () => void;
  onRestoreSnapshot?: () => void;
  sourceSnapshotId?: number | null;
  enableImportButton?: boolean;
  enableRestoreButton?: boolean;
  readOnly?: boolean;
};

export const ReportContentEditor8: React.FC<Editor8Props> = ({
  initialValue,
  onValueChange,
  upstreamSnapshotMd,
  upstreamData,
  onImportUpstream,
  onRestoreSnapshot,
  sourceSnapshotId,
  enableImportButton = true,
  enableRestoreButton = true,
  readOnly = false,
}) => {
  const [draft, setDraft] = useState<Report8ChaptersDraft>(() => {
    const base: Report8ChaptersDraft = { ...EMPTY_DRAFT };

    if (initialValue) {
      Object.assign(base, initialValue);
    } else if (upstreamSnapshotMd) {
      const parsed = parseSnapshotInto8Chapters(upstreamSnapshotMd);
      Object.assign(base, parsed);
    }

    if (sourceSnapshotId !== undefined) {
      base.source_snapshot_id = sourceSnapshotId;
    }

    return base;
  });

  const [dirtyFields, setDirtyFields] = useState<Set<keyof Report8ChaptersDraft>>(
    new Set(),
  );

  useEffect(() => {
    const nextDirty = new Set<keyof Report8ChaptersDraft>();
    const base: Report8ChaptersDraft = { ...EMPTY_DRAFT };

    if (initialValue) {
      Object.assign(base, initialValue);
    } else if (upstreamSnapshotMd) {
      const parsed = parseSnapshotInto8Chapters(upstreamSnapshotMd);
      Object.assign(base, parsed);
    }

    if (sourceSnapshotId !== undefined) {
      base.source_snapshot_id = sourceSnapshotId;
    }

    (Object.keys(base) as Array<keyof Report8ChaptersDraft>).forEach((k) => {
      const v = draft[k];
      const b = base[k];
      if (v !== b) {
        nextDirty.add(k);
      }
    });

    setDirtyFields(nextDirty);
  }, [initialValue, upstreamSnapshotMd, sourceSnapshotId]);

  const handleChange = useCallback(
    (key: keyof Omit<Report8ChaptersDraft, "source_snapshot_id">, value: string) => {
      setDraft((prev) => {
        const next: Report8ChaptersDraft = { ...prev, [key]: value };
        const nextDirty = new Set(dirtyFields);
        nextDirty.add(key);
        setDirtyFields(nextDirty);
        if (onValueChange) {
          onValueChange(next, nextDirty);
        }
        return next;
      });
    },
    [dirtyFields, onValueChange],
  );

  const handleImportClick = useCallback(() => {
    if (onImportUpstream) {
      onImportUpstream();
    }
    if (upstreamData) {
      const merged = generateDraftFromUpstream(upstreamData);
      setDraft((prev) => {
        const next: Report8ChaptersDraft = { ...prev, ...merged };
        if (sourceSnapshotId !== undefined) {
          next.source_snapshot_id = sourceSnapshotId;
        }
        const nextDirty = new Set(dirtyFields);
        Object.keys(merged).forEach((k) => {
          nextDirty.add(k as keyof Report8ChaptersDraft);
        });
        setDirtyFields(nextDirty);
        if (onValueChange) {
          onValueChange(next, nextDirty);
        }
        return next;
      });
    }
  }, [onImportUpstream, upstreamData, sourceSnapshotId, dirtyFields, onValueChange]);

  const handleRestoreClick = useCallback(() => {
    if (onRestoreSnapshot) {
      onRestoreSnapshot();
    }
    if (upstreamSnapshotMd) {
      const restored = parseSnapshotInto8Chapters(upstreamSnapshotMd);
      if (sourceSnapshotId !== undefined) {
        restored.source_snapshot_id = sourceSnapshotId;
      }
      setDraft(restored);
      setDirtyFields(new Set());
      if (onValueChange) {
        onValueChange(restored, new Set());
      }
    }
  }, [onRestoreSnapshot, upstreamSnapshotMd, sourceSnapshotId, onValueChange]);

  const leftColumns = useMemo(() => CHAPTER_META.slice(0, 4), []);
  const rightColumns = useMemo(() => CHAPTER_META.slice(4, 8), []);

  const renderCard = (meta: ChapterMetaItem) => {
    const value = draft[meta.key] ?? "";
    const colorInfo = TAG_COLOR[meta.tag];
    return (
      <div
        key={meta.ch}
        data-testid={`rce8-card-ch${meta.ch}`}
        style={{
          border: "1px solid #e5e7eb",
          borderRadius: "12px",
          padding: "16px",
          background: "#ffffff",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "8px",
            flexWrap: "wrap",
          }}
        >
          <h3
            data-testid={`rce8-title-ch${meta.ch}`}
            style={{
              margin: 0,
              fontSize: "15px",
              fontWeight: 600,
              color: "#111827",
            }}
          >
            {meta.title}
          </h3>
          <span
            data-testid={`rce8-badge-ch${meta.ch}`}
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "2px 10px",
              borderRadius: "999px",
              fontSize: "11px",
              fontWeight: 500,
              background:
                meta.tag === "auto"
                  ? "#dcfce7"
                  : meta.tag === "auto_editable"
                  ? "#dbeafe"
                  : "#fef3c7",
              color:
                meta.tag === "auto"
                  ? "#166534"
                  : meta.tag === "auto_editable"
                  ? "#1e40af"
                  : "#92400e",
            }}
            className={colorInfo.className}
          >
            {colorInfo.label}
          </span>
        </div>
        <textarea
          data-testid={`ch${meta.ch}_textarea`}
          value={value}
          readOnly={readOnly}
          disabled={readOnly}
          onChange={(e) => handleChange(meta.key, e.target.value)}
          style={{
            width: "100%",
            minHeight: "120px",
            resize: "vertical",
            border: "1px solid #d1d5db",
            borderRadius: "8px",
            padding: "10px 12px",
            fontSize: "13px",
            lineHeight: 1.5,
            fontFamily:
              "ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, sans-serif",
            background: readOnly ? "#f9fafb" : "#ffffff",
            boxSizing: "border-box",
          }}
          placeholder={`在此输入 ${meta.title} ...`}
        />
        <div style={{ display: "flex", justifyContent: "flex-end" }}>
          <span
            data-testid={`rce8-count-ch${meta.ch}`}
            style={{
              fontSize: "11px",
              color: "#6b7280",
            }}
          >
            {value.length} 字符 / chars
          </span>
        </div>
      </div>
    );
  };

  return (
    <div
      data-testid="rce8-editor"
      style={{
        width: "100%",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      <div
        data-testid="rce8-header"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
          padding: "12px 16px",
          background: "#f8fafc",
          border: "1px solid #e2e8f0",
          borderRadius: "12px",
        }}
      >
        <div>
          <h2
            data-testid="rce8-title"
            style={{ margin: 0, fontSize: "18px", fontWeight: 700, color: "#0f172a" }}
          >
            报告内容编辑器 · 八章结构 / Report Content Editor 8
          </h2>
          {sourceSnapshotId !== null && sourceSnapshotId !== undefined ? (
            <div
              data-testid="rce8-snapshot-id"
              style={{ marginTop: "4px", fontSize: "12px", color: "#64748b" }}
            >
              来源快照 ID / Source Snapshot ID: #{sourceSnapshotId}
            </div>
          ) : null}
        </div>
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {enableImportButton ? (
            <button
              data-testid="btn-import-upstream"
              onClick={handleImportClick}
              style={{
                padding: "8px 16px",
                border: "1px solid #2563eb",
                background: "#2563eb",
                color: "#ffffff",
                borderRadius: "8px",
                fontSize: "13px",
                fontWeight: 500,
                cursor: readOnly ? "not-allowed" : "pointer",
                opacity: readOnly ? 0.5 : 1,
              }}
              disabled={readOnly}
            >
              从上游数据导入 / Import From Upstream
            </button>
          ) : null}
          {enableRestoreButton ? (
            <button
              data-testid="btn-restore-snapshot"
              onClick={handleRestoreClick}
              style={{
                padding: "8px 16px",
                border: "1px solid #64748b",
                background: "#ffffff",
                color: "#334155",
                borderRadius: "8px",
                fontSize: "13px",
                fontWeight: 500,
                cursor: readOnly ? "not-allowed" : "pointer",
                opacity: readOnly ? 0.5 : 1,
              }}
              disabled={readOnly}
            >
              恢复快照 / Restore Snapshot
            </button>
          ) : null}
        </div>
      </div>

      <div
        className="grid grid-cols-1 md:grid-cols-2 gap-4"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(380px, 1fr))",
          gap: "16px",
        }}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {leftColumns.map(renderCard)}
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {rightColumns.map(renderCard)}
        </div>
      </div>
    </div>
  );
};

export { ReportContentEditor8 as default };
