import React, { useMemo, useState, useEffect, useRef } from "react";

/**
 * Wave82B T9 ScreeningTrio: 3 components (ProgressHeader + Toolbar + ExcludeReasonDialog)
 * + Cochrane PRISMA 9 类排除理由预设。0 新增 npm 包。
 */

// Inline shared-sdk types (peer only, avoid path alias issue in shared-ui)
type _ScreeningStage = "ta" | "fulltext";
type _ScreeningDecision = "include" | "exclude";
type _PresetClass = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;

export interface CochranePreset {
  class: _PresetClass;
  label: string;
  hint?: string;
  allowedStages: Array<_ScreeningStage>;
}

/**
 * 9 Cochrane-PRISMA 标准排除理由（Spec 5.3 精确对应）：
 * 1=重复文献（仅系统自动，用户禁用）；2=研究类型；3=人群 P；4=干预/对照 I/C；
 * 5=结局 O；6=无法获取全文；7=只有摘要；8=语言/年份不符；9=其他（备注必填）。
 */
export const COCHRANE_PRESET_REASONS_9: CochranePreset[] = [
  { class: 1, label: "重复文献（Auto Dedup）", hint: "系统自动填，用户不可手动", allowedStages: [] },
  { class: 2, label: "研究类型不符", hint: "Review/letter/非RCT/非对照研究", allowedStages: ["ta"] },
  { class: 3, label: "人群 P 不符", hint: "年龄/性别/疾病/基线不匹配", allowedStages: ["ta"] },
  { class: 4, label: "干预/对照 I/C 不符", hint: "暴露或对照组与 PICO 入排不符", allowedStages: ["ta"] },
  { class: 5, label: "结局指标 O 不符", hint: "终点缺失 / 数据不可用", allowedStages: ["ta"] },
  { class: 6, label: "无法获取全文", hint: "图书馆 / 开放获取无全文", allowedStages: ["ta", "fulltext"] },
  { class: 7, label: "只有摘要 / 无正文", hint: "仅摘要 poster / conference abstract", allowedStages: ["ta", "fulltext"] },
  { class: 8, label: "语言 / 发表年份不符", hint: "排除语种或年限外的文献", allowedStages: ["ta", "fulltext"] },
  { class: 9, label: "其他（备注必填）", hint: "请在 note 中说明原因", allowedStages: ["ta", "fulltext"] },
];

export interface StatsWithPrisma {
  total_count: number;
  unique_count?: number;
  duplicate_count?: number;
  prisma_identification: number;
  prisma_screening?: number | null;
  prisma_eligibility: number;
  prisma_included: number;
  prisma_ta_excluded?: number | null;
  prisma_duplicate_excluded?: number | null;
  prisma_fulltext_excluded?: number | null;
  prisma_eligibility_unknown?: number | null;
  prisma_override_applied?: boolean | null;
  prisma_diff_percent?: number | null;
}

// ---------------------------------------------------------------------------
// 1. ScreeningProgressHeader (6 tests)
// ---------------------------------------------------------------------------
export interface ScreeningProgressHeaderProps {
  stats: StatsWithPrisma;
  overrideApplied?: boolean | null;
  className?: string;
}

function _pct(num: number, den: number): number {
  return den > 0 ? Math.max(0, Math.min(100, (num / den) * 100)) : 0;
}

export const ScreeningProgressHeader: React.FC<ScreeningProgressHeaderProps> = ({
  stats,
  overrideApplied = false,
}) => {
  const N = stats.prisma_identification || 0;
  const P = (label: string, testid: string, n: number, max: number, color: string) => {
    const pct = _pct(n, max);
    return (
      <div data-testid={testid} style={{ flex: 1, minWidth: 140 }}>
        <div style={{ fontSize: 12, marginBottom: 4, color: "#374151" }}>
          <strong>{label}</strong> — n = {n}/{max} ({Math.round(pct)}%)
        </div>
        <div style={{ height: 8, background: "#f3f4f6", borderRadius: 4, overflow: "hidden" }}>
          <div style={{ width: `${pct}%`, height: "100%", background: color }} />
        </div>
      </div>
    );
  };

  const diffPct = typeof stats.prisma_diff_percent === "number" ? stats.prisma_diff_percent : null;
  const diffClass =
    diffPct === null ? "diff-none" : diffPct >= 30 ? "diff-high" : diffPct >= 10 ? "diff-mid" : "diff-low";
  const diffStyle = {
    color: diffPct === null ? "#9ca3af" : diffPct >= 30 ? "#b91c1c" : diffPct >= 10 ? "#92400e" : "#065f46",
    fontWeight: 600,
    fontSize: 12,
  };

  return (
    <div style={{ padding: 16, background: "#fafafa", borderBottom: "1px solid #e5e7eb" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 }}>
        <strong style={{ fontSize: 14 }}>PRISMA 2020 四格进度</strong>
        <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
          <span
            data-testid="override-badge"
            className={overrideApplied ? "override-on" : "override-off"}
            style={{
              padding: "3px 8px",
              borderRadius: 999,
              fontSize: 12,
              fontWeight: 600,
              background: overrideApplied ? "#fecaca" : "#d1fae5",
              color: overrideApplied ? "#991b1b" : "#065f46",
              border: overrideApplied ? "1px solid #f87171" : "1px solid #6ee7b7",
            }}
          >
            {overrideApplied ? "⚙ Manual Override ON" : "✓ Auto (Live SQL 聚合)"}
          </span>
          <span data-testid="diff-percent" className={diffClass} style={diffStyle}>
            {diffPct === null ? "Δ: OFF" : `Δ: ${diffPct}%`}
          </span>
        </div>
      </div>
      <div style={{ display: "flex", gap: 16, flexWrap: "wrap" }}>
        {P("Identification (N1)", "bar-identification", N, N, "#1d4ed8")}
        {P("Screening (N2)", "bar-screening", stats.prisma_screening ?? N, N, "#2563eb")}
        {P("Eligibility (N3)", "bar-eligibility", stats.prisma_eligibility || 0, N, "#7c3aed")}
        {P("Included (N4)", "bar-included", stats.prisma_included || 0, N, "#059669")}
        {P("T/A 排除 + 去重", "bar-excl-ta-dup",
          ((stats.prisma_ta_excluded ?? 0) + (stats.prisma_duplicate_excluded ?? 0)) || 0, N,
          "#dc2626")}
        {P("全文排除", "bar-excl-fulltext", stats.prisma_fulltext_excluded ?? 0,
          Math.max(1, stats.prisma_eligibility || 0), "#b45309")}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// 2. ScreeningToolbar (14 tests)
// ---------------------------------------------------------------------------
export interface FilterState {
  run?: string;
  source?: string;
  year?: string;
  decision?: string;
}

export interface ScreeningToolbarProps {
  selectedCount: number;
  totalRows: number;
  duplicateInSelectionCount?: number;
  stage?: _ScreeningStage | null;
  availableRuns?: Array<{ id: number | string; label: string }>;
  availableSources?: Array<{ key: string; label: string }>;
  availableYears?: number[];
  onBatchInclude: () => void;
  onBatchExclude: () => void;
  onBatchRevoke: () => void;
  onFilterChange: (f: FilterState) => void;
}

export const ScreeningToolbar: React.FC<ScreeningToolbarProps> = ({
  selectedCount, totalRows, duplicateInSelectionCount = 0,
  stage, availableRuns = [], availableSources = [], availableYears = [],
  onBatchInclude, onBatchExclude, onBatchRevoke, onFilterChange,
}) => {
  const anySel = selectedCount > 0;
  const titleText =
    stage === "ta" ? "标题/摘要筛选 (Title/Abstract Screening)" :
    stage === "fulltext" ? "全文筛选 (Fulltext Screening)" :
    "文献筛选工作台 (Screening)";
  return (
    <div style={{ padding: 12, borderBottom: "1px solid #e5e7eb", display: "flex", flexWrap: "wrap", gap: 12, alignItems: "center", background: "#fff" }}>
      <div style={{ fontWeight: 600 }} data-testid="stage-title">{titleText}</div>
      <div style={{ fontSize: 13, color: "#4b5563" }} data-testid="sel-counter">
        已选 <strong>{selectedCount}</strong> / {totalRows} 条
      </div>

      {duplicateInSelectionCount > 0 ? (
        <span
          data-testid="dup-skip-warn"
          style={{ padding: "2px 8px", fontSize: 12, background: "#fef3c7", color: "#92400e", borderRadius: 999 }}
        >
          ⚠ {duplicateInSelectionCount} 条 duplicate 将被 batch 跳过（不参与人工筛选）
        </span>
      ) : null}

      <div style={{ flex: 1 }} />

      {/* filter dropdowns */}
      <div style={{ display: "flex", gap: 8 }}>
        <select
          data-testid="filter-run"
          defaultValue=""
          onChange={(e) => onFilterChange({ run: e.target.value })}
        >
          <option value="">全部 Run</option>
          {availableRuns.map((r) => (
            <option key={String(r.id)} value={String(r.id)}>{r.label}</option>
          ))}
        </select>
        <select
          data-testid="filter-source"
          defaultValue=""
          onChange={(e) => onFilterChange({ source: e.target.value })}
        >
          <option value="">全部来源</option>
          {availableSources.map((s) => (
            <option key={s.key} value={s.key}>{s.label}</option>
          ))}
        </select>
        <select
          data-testid="filter-year"
          defaultValue=""
          onChange={(e) => onFilterChange({ year: e.target.value })}
        >
          <option value="">全部年份</option>
          {availableYears.map((y) => (
            <option key={String(y)} value={String(y)}>{y}</option>
          ))}
        </select>
        <select
          data-testid="filter-decision"
          defaultValue=""
          onChange={(e) => onFilterChange({ decision: e.target.value })}
        >
          <option value="">全部决策状态</option>
          <option value="undecided">未决策</option>
          <option value="include">✓ 纳入</option>
          <option value="exclude">✗ 排除</option>
          <option value="duplicate">⊙ 重复（auto）</option>
        </select>
      </div>

      {/* 3 batch buttons */}
      <div style={{ display: "flex", gap: 6 }}>
        <button
          type="button"
          data-testid="btn-batch-include"
          disabled={!anySel}
          onClick={onBatchInclude}
          style={{ padding: "6px 12px", background: anySel ? "#059669" : "#9ca3af", color: "#fff", border: "none", borderRadius: 4, cursor: anySel ? "pointer" : "not-allowed" }}
        >
          ✓ 批量纳入 (N={selectedCount})
        </button>
        <button
          type="button"
          data-testid="btn-batch-exclude"
          disabled={!anySel}
          onClick={onBatchExclude}
          style={{ padding: "6px 12px", background: anySel ? "#dc2626" : "#9ca3af", color: "#fff", border: "none", borderRadius: 4, cursor: anySel ? "pointer" : "not-allowed" }}
        >
          ✗ 批量排除…
        </button>
        <button
          type="button"
          data-testid="btn-batch-revoke"
          disabled={!anySel}
          onClick={onBatchRevoke}
          style={{ padding: "6px 12px", background: anySel ? "#e5e7eb" : "#f3f4f6", color: anySel ? "#111827" : "#9ca3af", border: "1px solid #d1d5db", borderRadius: 4, cursor: anySel ? "pointer" : "not-allowed" }}
        >
          ↺ 撤销决策
        </button>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// 3. ExcludeReasonDialog (10 tests)
// ---------------------------------------------------------------------------
export interface ExcludeReasonDialogProps {
  open: boolean;
  recordCount: number;
  stage: _ScreeningStage;
  initialPreset: _PresetClass | null;
  initialNote?: string | null;
  onApply: (result: { preset_class: _PresetClass; note: string | null }) => void;
  onClose: () => void;
}

export const ExcludeReasonDialog: React.FC<ExcludeReasonDialogProps> = ({
  open, recordCount, stage, initialPreset, initialNote = "",
  onApply, onClose,
}) => {
  const [preset, setPreset] = useState<_PresetClass | null>(initialPreset);
  const [note, setNote] = useState<string | null>(initialNote ?? "");

  useEffect(() => {
    if (open) {
      setPreset(initialPreset);
      setNote(initialNote ?? "");
    }
  }, [open, initialPreset, initialNote]);

  if (!open) return null;

  const presetDisabled = (idx: number): boolean => {
    if (idx === 1) return true;  // 1 reserved auto dedupe
    const allowed = COCHRANE_PRESET_REASONS_9[idx - 1].allowedStages;
    return !allowed.includes(stage);
  };

  const needNote = preset === 9;
  const noteOk = !needNote || (typeof note === "string" && note.trim().length > 0);
  const applyEnabled = preset !== null && noteOk;

  return (
    <div role="dialog" aria-modal="true" data-testid="exclude-reason-dialog"
      style={{
        position: "fixed", inset: 0, background: "rgba(0,0,0,.3)",
        display: "flex", alignItems: "center", justifyContent: "center", zIndex: 999,
      }}
    >
      <div style={{ background: "#fff", minWidth: 520, maxWidth: "90%", borderRadius: 6, padding: 20, boxShadow: "0 8px 30px rgba(0,0,0,.25)" }}>
        <h3 data-testid="dlg-title" style={{ margin: 0, marginBottom: 8, fontSize: 16 }}>
          批量排除 {recordCount} 条文献 — 选择 Cochrane PRISMA 排除理由（单选）
        </h3>
        <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 12 }}>
          Stage: <strong>{stage === "ta" ? "标题/摘要" : "全文"}</strong>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
          {COCHRANE_PRESET_REASONS_9.map((p) => {
            const disabled = presetDisabled(p.class);
            const checked = preset === p.class;
            return (
              <label
                key={p.class}
                data-testid={`preset-${p.class}-row`}
                style={{
                  display: "flex", gap: 8, padding: "6px 8px",
                  borderRadius: 4,
                  background: checked ? "#eff6ff" : "transparent",
                  opacity: disabled ? 0.45 : 1,
                  cursor: disabled ? "not-allowed" : "pointer",
                }}
              >
                <input
                  type="radio"
                  name="preset_class"
                  value={p.class}
                  data-testid={`preset-${p.class}`}
                  disabled={disabled}
                  checked={checked}
                  onChange={() => !disabled && setPreset(p.class)}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: p.class === 1 ? 500 : 600 }}>
                    #{p.class} {p.label}
                  </div>
                  {p.hint ? <div style={{ fontSize: 12, color: "#6b7280" }}>{p.hint}</div> : null}
                </div>
              </label>
            );
          })}
        </div>

        <label style={{ display: "block", fontSize: 13, marginBottom: 4 }}>
          备注 note {needNote ? <span style={{ color: "#dc2626" }}>(预设 9 其他 必填)</span> : "（可选）"}
        </label>
        <textarea
          data-testid="note-input"
          value={note ?? ""}
          onChange={(e) => setNote(e.target.value)}
          placeholder={needNote ? "请详细说明「其他」排除理由…" : "补充说明（可空）"}
          rows={3}
          style={{ width: "100%", padding: 8, border: "1px solid #d1d5db", borderRadius: 4, resize: "vertical", fontFamily: "inherit", fontSize: 13 }}
        />
        {(needNote && !(typeof note === "string" && note.trim())) ? (
          <div style={{ color: "#dc2626", fontSize: 12, marginTop: 4 }}>⚠ 备注不能为空</div>
        ) : null}

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
          <button
            type="button"
            data-testid="btn-cancel"
            onClick={onClose}
            style={{ padding: "6px 14px", border: "1px solid #d1d5db", background: "#fff", borderRadius: 4, cursor: "pointer" }}
          >
            取消
          </button>
          <button
            type="button"
            data-testid="btn-apply"
            disabled={!applyEnabled}
            onClick={() => applyEnabled && onApply({
              preset_class: preset!,
              note: (typeof note === "string" && note.trim()) ? note.trim() : null,
            })}
            style={{
              padding: "6px 14px",
              background: applyEnabled ? "#dc2626" : "#9ca3af",
              color: "#fff",
              border: "none",
              borderRadius: 4,
              cursor: applyEnabled ? "pointer" : "not-allowed",
            }}
          >
            确认排除 {recordCount} 条
          </button>
        </div>
      </div>
    </div>
  );
};

export default {
  COCHRANE_PRESET_REASONS_9,
  ScreeningProgressHeader,
  ScreeningToolbar,
  ExcludeReasonDialog,
};

export type StatsWithPrismaT9 = StatsWithPrisma;
