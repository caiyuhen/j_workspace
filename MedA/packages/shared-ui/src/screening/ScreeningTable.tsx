import React, { useMemo, useState, useEffect, useRef } from "react";
// Note: shared-ui doesn't import shared-sdk via path alias (peer only).
// Inline the exact 3 types used here — bit-for-bit identical to T7 commit
// `@meda/shared-sdk/client.ts:357-366` so the consumer can pass SDK types in.
type _ScreeningStage = "ta" | "fulltext";
type _ScreeningDecision = "include" | "exclude";
type _ExcludeReasonJson = {
  preset_class: 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9;
  note: string | null;
  stage?: _ScreeningStage | null;
  auto_by?: string | null;
};

/**
 * Wave82B ScreeningTableRow: single row in Title/Abstract Screening + Fulltext Screening Library.
 * Align 100% with shared-sdk W82B_* types (from T7 commit) + schemas.py LiteratureRecordSummary 4 new fields.
 */
export type DedupeStatus = "unique" | "duplicate" | "confirmed_unique";

export interface ScreeningTableRow {
  id: number;
  title: string;
  authors: string;
  journal: string;
  year: number | null;
  doi: string;
  pmid: string;
  abstract: string | null;
  dedupe_status: DedupeStatus;
  duplicate_of_id: number | null;
  screening_stage: _ScreeningStage | null;
  screening_decision: _ScreeningDecision | null;
  exclude_reason_json: string | null; // JSON string of _ExcludeReasonJson (or null)
  screening_notes: string | null;
}

/**
 * 5 列像素级固定 CSS Grid（0 new npm 包，不用 react-window / tanstack）。
 * 列 1 = 48px checkbox; 列 2 = min320 metadata; 列 3 = min420 abstract; 列 4 = 140px dedupe; 列 5 = 220px decision.
 */
export const SCREENING_TABLE_COL_WIDTHS = {
  select: 48,
  metadata: 320,
  abstract: 420,
  dedupe: 140,
  decision: 220,
} as const;

const ABSTRACT_TRUNCATE_CHARS = 300;
const PAGE_SIZE = 200;

export interface ScreeningTableProps {
  rows: ScreeningTableRow[];
  selection?: Set<number>;
  onSelectionChange?: (next: Set<number>) => void;
}

function gridTemplate(): string {
  const W = SCREENING_TABLE_COL_WIDTHS;
  return `${W.select}px minmax(${W.metadata}px, 1fr) minmax(${W.abstract}px, 2fr) ${W.dedupe}px ${W.decision}px`;
}

export const ScreeningTable: React.FC<ScreeningTableProps> = ({
  rows,
  selection: externalSelection,
  onSelectionChange,
}) => {
  const [internal, setInternal] = useState<Set<number>>(new Set());
  const sel = externalSelection ?? internal;
  const [page, setPage] = useState<number>(1);
  const [expandedAbs, setExpandedAbs] = useState<Set<number>>(new Set());

  const totalPages = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const pagedRows = useMemo(() => {
    const start = (page - 1) * PAGE_SIZE;
    return rows.slice(start, start + PAGE_SIZE);
  }, [rows, page]);

  // ------ checkbox state helpers ------
  const visibleSelectable = pagedRows.filter(
    (r) => r.dedupe_status !== "duplicate",
  );
  const selectedCount = visibleSelectable.reduce(
    (n, r) => (sel.has(r.id) ? n + 1 : n),
    0,
  );
  const allChecked = visibleSelectable.length > 0 && selectedCount === visibleSelectable.length;
  const indeterminate = selectedCount > 0 && selectedCount < visibleSelectable.length;
  const allCbRef = useRef<HTMLInputElement | null>(null);
  useEffect(() => {
    if (allCbRef.current) allCbRef.current.indeterminate = indeterminate;
  }, [indeterminate]);

  const setSelection = (next: Set<number>) => {
    setInternal(next);
    onSelectionChange?.(next);
  };

  const toggleRow = (id: number) => {
    const next = new Set(sel);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    setSelection(next);
  };

  const toggleSelectAllVisible = () => {
    const next = new Set(sel);
    if (allChecked) {
      for (const r of visibleSelectable) next.delete(r.id);
    } else {
      for (const r of visibleSelectable) next.add(r.id);
    }
    setSelection(next);
  };

  // ------ abstract truncation ------
  const formatAbstract = (r: ScreeningTableRow) => {
    const text = r.abstract ?? "";
    if (text.length <= ABSTRACT_TRUNCATE_CHARS) return { text, needToggle: false };
    if (expandedAbs.has(r.id)) return { text, needToggle: true, expanded: true };
    return { text: text.slice(0, ABSTRACT_TRUNCATE_CHARS) + "…", needToggle: true, expanded: false };
  };

  const toggleExpand = (id: number) => {
    const n = new Set(expandedAbs);
    if (n.has(id)) n.delete(id);
    else n.add(id);
    setExpandedAbs(n);
  };

  // ------ duplicate → scroll to master record ------
  const scrollToMaster = (masterId: number) => {
    const el = document.querySelector<HTMLElement>(`[data-testid="row-${masterId}"]`);
    if (el) {
      el.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  };

  // ------ render ------
  const W = SCREENING_TABLE_COL_WIDTHS;
  void W;

  return (
    <div data-testid="screening-table-root">
      <div role="grid" data-testid="grid" style={{ display: "grid", gridTemplateColumns: gridTemplate() }}>
        {/* header row */}
        <div role="columnheader" style={{ padding: 8 }}>
          <input
            ref={allCbRef}
            type="checkbox"
            data-testid="select-all"
            checked={allChecked}
            onChange={toggleSelectAllVisible}
            aria-label="Select all records on page"
          />
        </div>
        <div role="columnheader" style={{ padding: 8, fontWeight: 600 }}>
          Metadata (Title / Authors / Journal / Year)
        </div>
        <div role="columnheader" style={{ padding: 8, fontWeight: 600 }}>
          Abstract
        </div>
        <div role="columnheader" style={{ padding: 8, fontWeight: 600 }}>
          Dedupe status
        </div>
        <div role="columnheader" style={{ padding: 8, fontWeight: 600 }}>
          Screening decision
        </div>

        {/* data rows */}
        {pagedRows.map((r) => {
          const classes: string[] = [`row-${r.dedupe_status}`];
          if (r.screening_decision === "include") classes.push("decision-include");
          if (r.screening_decision === "exclude") classes.push("decision-exclude");
          if (r.dedupe_status === "duplicate") classes.push("row-duplicate");

          const reason: _ExcludeReasonJson | null = r.exclude_reason_json
            ? (JSON.parse(r.exclude_reason_json) as _ExcludeReasonJson)
            : null;

          const abs = formatAbstract(r);

          return (
            <React.Fragment key={r.id}>
              <div
                role="row"
                data-testid={`row-${r.id}`}
                className={classes.join(" ")}
                style={{
                  display: "contents",
                  borderLeft:
                    r.dedupe_status === "duplicate"
                      ? "4px solid #d97706"
                      : r.screening_decision === "include"
                        ? "4px solid #059669"
                        : r.screening_decision === "exclude"
                          ? "4px solid #dc2626"
                          : undefined,
                }}
              >
                <div role="gridcell" style={{ padding: 8 }}>
                  <input
                    type="checkbox"
                    data-testid={`selrow-${r.id}`}
                    checked={sel.has(r.id)}
                    disabled={r.dedupe_status === "duplicate"}
                    onChange={() => toggleRow(r.id)}
                    aria-label={`Select record ${r.id}`}
                  />
                </div>
                <div role="gridcell" style={{ padding: 8 }}>
                  <div style={{ fontWeight: 600 }}>{r.title}</div>
                  <div style={{ fontSize: 12, color: "#4b5563", marginTop: 4 }}>
                    {r.authors}
                    {r.journal ? ` · ${r.journal}` : ""}
                    {r.year ? ` (${r.year})` : ""}
                  </div>
                  {r.doi ? (
                    <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>DOI: {r.doi}</div>
                  ) : null}
                  {r.pmid ? (
                    <div style={{ fontSize: 11, color: "#6b7280", marginTop: 2 }}>PMID: {r.pmid}</div>
                  ) : null}
                </div>
                <div role="gridcell" style={{ padding: 8 }}>
                  <div data-testid={`abstract-${r.id}`} style={{ whiteSpace: "pre-wrap", lineHeight: 1.5 }}>
                    {abs.text || <em style={{ color: "#9ca3af" }}>No abstract available.</em>}
                  </div>
                  {abs.needToggle ? (
                    <button
                      type="button"
                      data-testid={`abs-expand-${r.id}`}
                      onClick={() => toggleExpand(r.id)}
                      style={{ marginTop: 4, background: "none", border: "none", color: "#2563eb", cursor: "pointer", padding: 0 }}
                    >
                      {abs.expanded ? "收起 (Collapse)" : "展开 (Show full)"}
                    </button>
                  ) : null}
                </div>
                <div role="gridcell" style={{ padding: 8 }}>
                  {r.dedupe_status === "duplicate" ? (
                    <div>
                      <div style={{ color: "#b45309", fontWeight: 600 }}>Duplicate</div>
                      <div style={{ fontSize: 12, color: "#6b7280" }}>
                        of #{r.duplicate_of_id ?? "?"}
                      </div>
                      <button
                        type="button"
                        data-testid={`scroll-to-master-${r.id}`}
                        title={
                          document.querySelector(`[data-testid="row-${r.duplicate_of_id}"]`)
                            ? "Scroll to original record"
                            : "Original record on other page (not rendered)"
                        }
                        onClick={() => scrollToMaster(r.duplicate_of_id ?? 0)}
                        style={{ marginTop: 6, padding: "2px 6px", fontSize: 12, cursor: "pointer" }}
                      >
                        Jump →
                      </button>
                    </div>
                  ) : r.dedupe_status === "confirmed_unique" ? (
                    <div style={{ color: "#047857" }}>Confirmed unique</div>
                  ) : (
                    <div style={{ color: "#4b5563" }}>Unique</div>
                  )}
                </div>
                <div role="gridcell" style={{ padding: 8 }}>
                  {r.screening_decision === "include" ? (
                    <div style={{ color: "#059669", fontWeight: 600 }}>✓ Include</div>
                  ) : r.screening_decision === "exclude" ? (
                    <div>
                      <div style={{ color: "#dc2626", fontWeight: 600 }}>✗ Exclude</div>
                      {reason ? (
                        <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>
                          Reason #{reason.preset_class}
                          {reason.note ? ` · ${reason.note}` : ""}
                          {reason.auto_by ? ` (auto: ${reason.auto_by})` : ""}
                        </div>
                      ) : null}
                    </div>
                  ) : (
                    <div style={{ color: "#9ca3af" }}>Not decided</div>
                  )}
                  {r.screening_stage ? (
                    <div style={{ fontSize: 11, color: "#6b7280", marginTop: 4 }}>
                      Stage: {r.screening_stage === "ta" ? "Title/Abstract" : "Fulltext"}
                    </div>
                  ) : null}
                </div>
              </div>
            </React.Fragment>
          );
        })}
      </div>

      {/* pagination */}
      <div data-testid="pagination" style={{ padding: 12, display: "flex", gap: 8, alignItems: "center" }}>
        <span style={{ fontSize: 12, color: "#4b5563" }}>
          Showing {rows.length === 0 ? 0 : (page - 1) * PAGE_SIZE + 1}–{Math.min(page * PAGE_SIZE, rows.length)} of {rows.length}
        </span>
        <div style={{ display: "flex", gap: 4 }}>
          {Array.from({ length: totalPages }, (_, i) => i + 1).map((p) => (
            <button
              key={p}
              type="button"
              data-testid={`page-${p}`}
              onClick={() => setPage(p)}
              aria-label={`Go to page ${p}`}
              style={{
                padding: "4px 8px",
                minWidth: 28,
                background: p === page ? "#2563eb" : "#fff",
                color: p === page ? "#fff" : "#111827",
                border: "1px solid #d1d5db",
                borderRadius: 4,
                cursor: "pointer",
              }}
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ScreeningTable;
