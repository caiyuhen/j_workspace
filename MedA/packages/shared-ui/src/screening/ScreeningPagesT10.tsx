import React, { useMemo, useState } from "react";
import { ScreeningTable, type ScreeningTableRow, type DedupeStatus } from "./ScreeningTable";
import {
  ScreeningProgressHeader,
  type ScreeningProgressHeaderProps,
  type StatsWithPrismaT9,
  ScreeningToolbar,
  type ScreeningToolbarProps,
  type FilterState,
  ExcludeReasonDialog,
  type ExcludeReasonDialogProps,
  COCHRANE_PRESET_REASONS_9,
  type CochranePreset,
} from "./ScreeningTrio";

/** T10: 3 routing page containers (Dashboard / TA Screening / Fulltext Screening) +
 *  computeNavigation route helper. 0 npm 新增，仅组合 T8/T9 现有组件。
 */

// Re-export types shared with caller
export type ScreeningPageStats = StatsWithPrismaT9;

export interface ScreeningRouteKey {
  key: "dashboard" | "ta" | "fulltext";
  label: string;
  active: boolean;
  locked: boolean;
}

export interface NavResult {
  currentKey: "dashboard" | "ta" | "fulltext";
  tabs: ScreeningRouteKey[];
}

/**
 * Compute nav tabs. eligibility=0 → fulltext is locked (no records passed T/A yet).
 */
export function computeNavigation(
  current: "dashboard" | "ta" | "fulltext",
  eligibilityCount: number = 1,
): NavResult {
  const tabs: ScreeningRouteKey[] = [
    { key: "dashboard", label: "总览 Dashboard", active: current === "dashboard", locked: false },
    { key: "ta", label: "标题/摘要筛选 (T/A)", active: current === "ta", locked: false },
    { key: "fulltext", label: "全文筛选 Fulltext", active: current === "fulltext", locked: eligibilityCount <= 0 },
  ];
  return { currentKey: current, tabs };
}

// ---------------------------------------------------------------------------
// Shared page types
// ---------------------------------------------------------------------------
export type _ExportFormat = "ris" | "bib" | "csv" | "jsonl";

export interface _BasePageProps {
  stats: ScreeningPageStats;
  records: ScreeningTableRow[];
  currentRoute?: "dashboard" | "ta" | "fulltext";
  onNavigate: (next: "dashboard" | "ta" | "fulltext") => void;
  onRunDedupe?: () => void;
  onApplyOverride?: (val: {
    identification: number; screening: number; eligibility: number; included: number;
  }) => void;
  onClearOverride?: () => void;
  onExport?: (format: _ExportFormat) => void;
  onBatchDecision?: (op: {
    operation: "include" | "exclude" | "revoke_fulltext";
    stage?: "ta" | "fulltext" | null;
    exclude_reason?: { preset_class: number; note: string | null } | null;
    record_ids?: number[];
  }) => void;
  onBatchRevoke?: (op: any) => void;
  onFilterChange?: (f: FilterState) => void;
  onPageChange?: (nextPageZeroIdx: number) => void;
  onSelectionChange?: (sel: Set<number>) => void;
  initialSelectedIds?: Set<number>;
  availableRuns?: Array<{ id: number | string; label: string }>;
  availableSources?: Array<{ key: string; label: string }>;
  availableYears?: number[];
  initialPage?: number;
  pageSize?: number;
}

// ---------------------------------------------------------------------------
// Nav Tabs strip (shared)
// ---------------------------------------------------------------------------
function NavTabs({ tabs, onNavigate }: { tabs: ScreeningRouteKey[]; onNavigate: (k: any) => void }) {
  return (
    <div data-testid="nav-tabs" style={{ display: "flex", gap: 6, padding: "8px 16px", background: "#fff", borderBottom: "1px solid #e5e7eb" }}>
      {tabs.map((t) => (
        <button
          key={t.key}
          data-testid={`nav-tab-${t.key}`}
          className={t.active ? "nav-tab active" : "nav-tab"}
          disabled={t.locked}
          onClick={() => !t.locked && onNavigate(t.key)}
          style={{
            padding: "6px 12px", borderRadius: 4,
            background: t.active ? "#1d4ed8" : t.locked ? "#f3f4f6" : "#fff",
            color: t.active ? "#fff" : t.locked ? "#9ca3af" : "#111827",
            border: t.locked ? "1px dashed #d1d5db" : "1px solid #e5e7eb",
            cursor: t.locked ? "not-allowed" : "pointer",
            fontWeight: t.active ? 700 : 500,
          }}
          title={t.locked ? "尚未有通过 T/A 的文献" : undefined}
        >
          {t.label}{t.locked ? " 🔒" : ""}
        </button>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pagination strip (shared)
// ---------------------------------------------------------------------------
function _Pagination({
  currentPage, pageSize, total, onPageChange,
}: {
  currentPage: number; pageSize: number; total: number;
  onPageChange: (next: number) => void;
}) {
  const maxPage = Math.max(0, Math.ceil(total / pageSize) - 1);
  const label = `${currentPage + 1} / ${maxPage + 1}`;
  return (
    <div style={{ padding: "8px 16px", display: "flex", justifyContent: "flex-end", gap: 8, alignItems: "center", borderTop: "1px solid #e5e7eb" }}>
      <button
        type="button"
        data-testid="btn-page-prev"
        disabled={currentPage <= 0}
        onClick={() => onPageChange(Math.max(0, currentPage - 1))}
        style={{ padding: "4px 10px" }}
      >← Prev</button>
      <span data-testid="page-label" style={{ fontSize: 13, minWidth: 56, textAlign: "center" }}>{label}</span>
      <button
        type="button"
        data-testid="btn-page-next"
        disabled={currentPage >= maxPage}
        onClick={() => onPageChange(Math.min(maxPage, currentPage + 1))}
        style={{ padding: "4px 10px" }}
      >Next →</button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard Page (14 tests)
// ---------------------------------------------------------------------------
export interface DashboardScreeningPageProps extends _BasePageProps {}

export const DashboardScreeningPage: React.FC<DashboardScreeningPageProps> = ({
  stats, records, currentRoute = "dashboard", onNavigate,
  onRunDedupe, onApplyOverride, onClearOverride, onExport,
}) => {
  const eligibility = stats.prisma_eligibility || 0;
  const nav = computeNavigation(currentRoute, eligibility);
  const tabs = nav.tabs;
  const [overrideOpen, setOverrideOpen] = useState(false);
  const [identification, setIdentification] = useState<string>(
    `${stats.prisma_identification ?? ""}`,
  );
  const [screening, setScreening] = useState<string>(`${stats.prisma_screening ?? stats.prisma_identification ?? ""}`);
  const [eligibilityOv, setEligibilityOv] = useState<string>(`${stats.prisma_eligibility ?? ""}`);
  const [included, setIncluded] = useState<string>(`${stats.prisma_included ?? ""}`);

  const apply = () => {
    onApplyOverride?.({
      identification: parseInt(identification || "0", 10) || 0,
      screening: parseInt(screening || "0", 10) || 0,
      eligibility: parseInt(eligibilityOv || "0", 10) || 0,
      included: parseInt(included || "0", 10) || 0,
    });
    setOverrideOpen(false);
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <div data-testid="page-title" style={{ padding: "12px 16px", fontSize: 18, fontWeight: 700, background: "#fff", borderBottom: "1px solid #e5e7eb" }}>
        📊 PRISMA 2020 工作台总览 Dashboard
      </div>
      <NavTabs tabs={tabs} onNavigate={onNavigate} />
      <ScreeningProgressHeader stats={stats} overrideApplied={!!stats.prisma_override_applied} />

      <div style={{ padding: 16, display: "flex", gap: 16, flexWrap: "wrap" }}>
        {[
          ["N1 鉴定 Identification", stats.prisma_identification, "card-N1"],
          ["N2 筛选 Screening", stats.prisma_screening ?? stats.prisma_identification, "card-N2"],
          ["N3 合格 Eligibility", stats.prisma_eligibility, "card-N3"],
          ["N4 最终纳入 Included", stats.prisma_included, "card-N4"],
        ].map(([label, n, tid]) => (
          <div key={tid as string} data-testid={tid as string}
            style={{ minWidth: 180, padding: 16, borderRadius: 8, background: "#fff", border: "1px solid #e5e7eb", flex: "1 1 180px" }}>
            <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 4 }}>{label}</div>
            <div style={{ fontSize: 26, fontWeight: 700 }}>{n ?? 0}</div>
          </div>
        ))}
      </div>

      <div style={{ padding: "0 16px 16px", display: "flex", gap: 12, flexWrap: "wrap" }}>
        <button
          type="button" data-testid="nav-go-ta"
          onClick={() => onNavigate("ta")}
          style={{ padding: "8px 14px", background: "#2563eb", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}
        >→ 进入 T/A 标题/摘要筛选</button>
        <button
          type="button" data-testid="nav-go-fulltext"
          disabled={eligibility <= 0}
          onClick={() => eligibility > 0 && onNavigate("fulltext")}
          style={{ padding: "8px 14px",
            background: eligibility > 0 ? "#7c3aed" : "#9ca3af",
            color: "#fff", border: "none", borderRadius: 4,
            cursor: eligibility > 0 ? "pointer" : "not-allowed" }}
        >→ 进入 全文筛选{eligibility <= 0 ? " (Locked)" : ""}</button>

        <div style={{ flex: 1 }} />

        <button type="button" data-testid="btn-run-dedupe" onClick={onRunDedupe}
          style={{ padding: "6px 12px", border: "1px solid #f59e0b", background: "#fff7ed", color: "#92400e", borderRadius: 4, cursor: "pointer" }}>
          🔄 重新跑项目去重 (Full Dedupe)
        </button>

        <button type="button" data-testid="btn-override-open" onClick={() => setOverrideOpen(true)}
          style={{ padding: "6px 12px", border: "1px solid #dc2626", background: "#fef2f2", color: "#991b1b", borderRadius: 4, cursor: "pointer" }}>
          ⚙ PRISMA 手动覆盖 Override
        </button>

        {(["ris", "bib", "csv", "jsonl"] as _ExportFormat[]).map((f) => (
          <button key={f} type="button" data-testid={`btn-export-${f}`} onClick={() => onExport?.(f)}
            style={{ padding: "6px 12px", border: "1px solid #d1d5db", background: "#fff", borderRadius: 4, cursor: "pointer" }}>
            导出 {f.toUpperCase()}
          </button>
        ))}
      </div>

      <div style={{ flex: 1, padding: "0 16px 16px" }} data-testid="screener-table">
        <ScreeningTable
          rows={records.slice(0, 10)}
          onSelectionChange={() => {}}
          selection={new Set<number>()}
          onJumpDuplicate={() => {}}
        />
      </div>

      {overrideOpen ? (
        <div role="dialog" aria-modal="true" data-testid="dlg-prisma-override"
          style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.3)", zIndex: 999, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <div style={{ background: "#fff", padding: 20, borderRadius: 8, minWidth: 480 }}>
            <h3 style={{ margin: 0, marginBottom: 12 }}>PRISMA 2020 四格手动覆盖 Manual Override</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              {[
                ["Identification N1", "ov-identification", identification, setIdentification],
                ["Screening N2", "ov-screening", screening, setScreening],
                ["Eligibility N3", "ov-eligibility", eligibilityOv, setEligibilityOv],
                ["Included N4", "ov-included", included, setIncluded],
              ].map(([label, tid, val, setter]) => (
                <label key={tid as string} style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
                  <span>{label}</span>
                  <input
                    data-testid={tid as string}
                    type="number"
                    value={val as string}
                    onChange={(e) => (setter as (x: string) => void)(e.target.value)}
                    style={{ padding: "6px 8px", border: "1px solid #d1d5db", borderRadius: 4 }}
                  />
                </label>
              ))}
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
              <button type="button" data-testid="btn-override-clear" onClick={onClearOverride}
                style={{ padding: "6px 12px", background: "#fef2f2", color: "#991b1b", border: "1px solid #fecaca", borderRadius: 4, cursor: "pointer" }}>
                恢复 Auto（清空 override）
              </button>
              <button type="button" onClick={() => setOverrideOpen(false)}
                style={{ padding: "6px 12px", border: "1px solid #d1d5db", background: "#fff", borderRadius: 4, cursor: "pointer" }}>
                取消
              </button>
              <button type="button" data-testid="btn-override-apply" onClick={apply}
                style={{ padding: "6px 14px", background: "#dc2626", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
                应用 override
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
};

// ---------------------------------------------------------------------------
// T/A Screening Page (13 tests)
// ---------------------------------------------------------------------------
export interface TAScreeningPageProps extends _BasePageProps {}

export const TAScreeningPage: React.FC<TAScreeningPageProps> = ({
  stats, records, currentRoute = "ta", onNavigate,
  onBatchDecision, onBatchRevoke, onFilterChange, onPageChange,
  onSelectionChange, availableRuns, availableSources, availableYears,
  initialSelectedIds, initialPage = 0, pageSize = 200,
}) => {
  const eligibility = stats.prisma_eligibility || (records.filter((r) => r.dedupe_status !== "duplicate").length);
  const nav = computeNavigation(currentRoute, eligibility);
  const [selection, setSelection] = useState<Set<number>>(initialSelectedIds ?? new Set());
  const [page, setPage] = useState<number>(initialPage);
  const [excludeOpen, setExcludeOpen] = useState<boolean>(false);

  const duplicateCountInSel = useMemo(
    () => [...selection].filter((id) => records.find((r) => r.id === id)?.dedupe_status === "duplicate").length,
    [selection, records],
  );
  const start = page * pageSize;
  const slice = records.slice(start, start + pageSize);

  const onInclude: ScreeningToolbarProps["onBatchInclude"] = () => {
    onBatchDecision?.({
      operation: "include", stage: "ta", record_ids: [...selection],
    });
  };
  const onExcludeClick = () => setExcludeOpen(true);
  const onRevoke = () => {
    // revoke: flip any decision. include stage ta to clear? operation=include stage ta
    onBatchRevoke?.({ operation: "revoke", stage: "ta", record_ids: [...selection] });
  };

  const handleExcludeApply: ExcludeReasonDialogProps["onApply"] = (val) => {
    setExcludeOpen(false);
    onBatchDecision?.({
      operation: "exclude", stage: "ta", exclude_reason: val as any, record_ids: [...selection],
    });
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "10px 16px", fontSize: 16, fontWeight: 700, borderBottom: "1px solid #e5e7eb", background: "#fff" }} data-testid="ta-header">
        T/A 标题/摘要筛选
      </div>
      <NavTabs tabs={nav.tabs} onNavigate={onNavigate} />
      <ScreeningToolbar
        selectedCount={selection.size}
        totalRows={records.length}
        duplicateInSelectionCount={duplicateCountInSel}
        stage="ta"
        availableRuns={availableRuns}
        availableSources={availableSources}
        availableYears={availableYears}
        onBatchInclude={onInclude}
        onBatchExclude={onExcludeClick}
        onBatchRevoke={onRevoke}
        onFilterChange={(f) => onFilterChange?.(f)}
      />
      <div style={{ flex: 1 }} data-testid="screener-table">
        <ScreeningTable
          rows={slice}
          selection={selection}
          onSelectionChange={(s) => { setSelection(s); onSelectionChange?.(s); }}
          onJumpDuplicate={() => {}}
        />
      </div>
      <_Pagination
        currentPage={page} pageSize={pageSize} total={records.length}
        onPageChange={(np) => { setPage(np); onPageChange?.(np); }}
      />
      {excludeOpen ? (
        <ExcludeReasonDialog
          open={true} recordCount={selection.size} stage="ta"
          initialPreset={null} initialNote=""
          onApply={handleExcludeApply} onClose={() => setExcludeOpen(false)}
        />
      ) : null}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Fulltext Screening Page (10 tests)
// ---------------------------------------------------------------------------
export interface FulltextScreeningPageProps extends _BasePageProps {}

export const FulltextScreeningPage: React.FC<FulltextScreeningPageProps> = ({
  stats, records, currentRoute = "fulltext", onNavigate,
  onBatchDecision, onBatchRevoke, onFilterChange, onPageChange,
  onSelectionChange, onExport,
  initialSelectedIds, initialPage = 0, pageSize = 200,
}) => {
  const eligibility = stats.prisma_eligibility || 0;
  const includedN = stats.prisma_included || 0;
  const nav = computeNavigation(currentRoute, eligibility);
  const [selection, setSelection] = useState<Set<number>>(initialSelectedIds ?? new Set());
  const [page, setPage] = useState<number>(initialPage);
  const [excludeOpen, setExcludeOpen] = useState(false);

  const start = page * pageSize;
  const slice = records.slice(start, start + pageSize);

  if (eligibility <= 0) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
        <div style={{ padding: "10px 16px", fontSize: 16, fontWeight: 700, borderBottom: "1px solid #e5e7eb", background: "#fff" }}>
          全文筛选
        </div>
        <NavTabs tabs={nav.tabs} onNavigate={onNavigate} />
        <div data-testid="empty-fulltext-state"
          style={{ padding: 48, textAlign: "center", color: "#6b7280" }}>
          🏗️ 还没有通过 T/A 的文献可以进入全文筛选。
          <br />
          <button type="button" data-testid="nav-back-ta" onClick={() => onNavigate("ta")}
            style={{ marginTop: 16, padding: "8px 14px", background: "#2563eb", color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>
            → 回到 T/A 筛选
          </button>
        </div>
      </div>
    );
  }

  const onInclude = () => onBatchDecision?.({
    operation: "include", stage: "fulltext", record_ids: [...selection],
  });
  const onExcludeClick = () => setExcludeOpen(true);
  const onRevoke = () => onBatchRevoke?.({ operation: "revoke_fulltext", record_ids: [...selection] });
  const handleExcludeApply: ExcludeReasonDialogProps["onApply"] = (val) => {
    setExcludeOpen(false);
    onBatchDecision?.({
      operation: "exclude", stage: "fulltext", exclude_reason: val as any, record_ids: [...selection],
    });
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <div style={{ padding: "10px 16px", fontSize: 16, fontWeight: 700, borderBottom: "1px solid #e5e7eb",
        background: "#fff", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>Fulltext 全文筛选</div>
        <div data-testid="ft-progress" style={{ fontSize: 13, color: "#065f46", fontWeight: 600 }}>
          进度: 已纳入 Included {includedN} / Eligibility {eligibility}
        </div>
      </div>
      <NavTabs tabs={nav.tabs} onNavigate={onNavigate} />
      <div style={{ padding: "8px 16px", background: "#f9fafb", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <button type="button" data-testid="nav-back-ta" onClick={() => onNavigate("ta")}
          style={{ padding: "4px 10px", border: "1px solid #d1d5db", background: "#fff", borderRadius: 4, cursor: "pointer" }}>
          ← 回到 T/A 筛选
        </button>
        <div style={{ display: "flex", gap: 8 }}>
          {(["ris", "bib", "csv", "jsonl"] as _ExportFormat[]).map((f) => (
            <button key={f} type="button" data-testid={`btn-export-${f}`} onClick={() => onExport?.(f)}
              style={{ padding: "4px 10px", border: "1px solid #e5e7eb", background: "#fff", borderRadius: 4, cursor: "pointer" }}>
              {f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>
      <ScreeningToolbar
        selectedCount={selection.size}
        totalRows={records.length}
        stage="fulltext"
        onBatchInclude={onInclude}
        onBatchExclude={onExcludeClick}
        onBatchRevoke={onRevoke}
        onFilterChange={(f) => onFilterChange?.(f)}
      />
      <div style={{ flex: 1 }} data-testid="screener-table">
        <ScreeningTable
          rows={slice}
          selection={selection}
          onSelectionChange={(s) => { setSelection(s); onSelectionChange?.(s); }}
          onJumpDuplicate={() => {}}
        />
      </div>
      <_Pagination
        currentPage={page} pageSize={pageSize} total={records.length}
        onPageChange={(np) => { setPage(np); onPageChange?.(np); }}
      />
      {excludeOpen ? (
        <ExcludeReasonDialog
          open={true} recordCount={selection.size} stage="fulltext"
          initialPreset={null} initialNote=""
          onApply={handleExcludeApply} onClose={() => setExcludeOpen(false)}
        />
      ) : null}
    </div>
  );
};

export default {
  computeNavigation,
  DashboardScreeningPage,
  TAScreeningPage,
  FulltextScreeningPage,
  COCHRANE_PRESET_REASONS_9,
};
