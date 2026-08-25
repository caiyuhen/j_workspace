import React from "react";

export interface DedupPerf {
  nodes: number;
  build_ms: number;
  query_avg_us: number;
  step1_total_ms: number;
  speedup_x: number;
  parallel_eff_x: number;
  slo_2000: number;
  ratio: number;
  stage_ms?: {
    minhash_ms?: number;
    lsh_ms?: number;
    oversample_ms?: number;
    bk_ms?: number;
    union_ms?: number;
    total_ms?: number;
  };
  lsh_candidates?: number;
  lsh_candidate_filter_ratio?: number;
  oversample_prefix?: boolean;
}

export interface DedupDiag {
  sizes_hist: Record<string, number>;
  hamming_hist: Record<string, number>;
  perf?: DedupPerf;
}

export interface DedupDiagCardsProps {
  diag: DedupDiag;
  diagLoading?: boolean;
  diagError?: string | null;
}

function _cardContainer(children: React.ReactNode, testid: string, ariaLabel: string) {
  return (
    <div
      data-testid={testid}
      aria-label={ariaLabel}
      style={{
        padding: 16,
        background: "#fff",
        borderRadius: 8,
        border: "1px solid #e5e7eb",
      }}
    >
      {children}
    </div>
  );
}

export function DedupSizesCard({ sizes_hist }: { sizes_hist: Record<string, number> }): JSX.Element {
  const entries = Object.entries(sizes_hist);
  let n_total_fixed = 0;
  for (const [size, count] of entries) {
    const s = parseInt(size, 10);
    n_total_fixed += s * count;
  }
  const n_kept = entries.reduce((sum, [, count]) => sum + count, 0);
  const dropRate = n_total_fixed === 0 ? 0 : ((n_total_fixed - n_kept) / n_total_fixed) * 100;

  const chips: { text: string; bg: string; color: string; border: string; testid: string }[] = [];

  const entriesBySize = entries.map(([size, count]) => ({ size: parseInt(size, 10), count }));

  const size1Entry = entriesBySize.find((e) => e.size === 1);
  if (size1Entry) {
    const pct = n_total_fixed === 0 ? 0 : ((size1Entry.count * 1) / n_total_fixed) * 100;
    chips.push({
      text: `1 · ${size1Entry.count} (${pct.toFixed(1)}% unique)`,
      bg: "#d1fae5",
      color: "#065f46",
      border: "#6ee7b7",
      testid: "sizes-chip-1",
    });
  }

  const size2Entry = entriesBySize.find((e) => e.size === 2);
  if (size2Entry) {
    chips.push({
      text: `2 · ${size2Entry.count} 对`,
      bg: "#fef3c7",
      color: "#92400e",
      border: "#fcd34d",
      testid: "sizes-chip-2",
    });
  }

  const size3Entry = entriesBySize.find((e) => e.size === 3);
  if (size3Entry) {
    chips.push({
      text: `3 · ${size3Entry.count} 组`,
      bg: "#ffedd5",
      color: "#9a3412",
      border: "#fdba74",
      testid: "sizes-chip-3",
    });
  }

  const size4PlusCount = entriesBySize
    .filter((e) => e.size >= 4)
    .reduce((sum, e) => sum + e.count, 0);
  const size4PlusPapers = entriesBySize
    .filter((e) => e.size >= 4)
    .reduce((sum, e) => sum + e.count * e.size, 0);
  if (size4PlusCount > 0) {
    chips.push({
      text: `4+ · ${size4PlusCount} 组 (${size4PlusPapers} 篇)`,
      bg: "#fee2e2",
      color: "#991b1b",
      border: "#fca5a5",
      testid: "sizes-chip-4plus",
    });
  }

  const bottomText = `丢弃率 ${dropRate.toFixed(1)}% · 保留 ${n_kept} 篇`;
  const ariaLabel = `Dedup sizes card: 丢弃率 ${dropRate.toFixed(1)}%`;

  return _cardContainer(
    <>
      <h4 data-testid="dedup-sizes-title" style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, margin: 0 }}>重复组大小分布</h4>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12, marginTop: 12 }}>
        {chips.map((c) => (
          <span
            key={c.testid}
            data-testid={c.testid}
            style={{
              padding: "3px 10px",
              borderRadius: 999,
              fontSize: 12,
              fontWeight: 600,
              background: c.bg,
              color: c.color,
              border: `1px solid ${c.border}`,
            }}
          >
            {c.text}
          </span>
        ))}
      </div>
      <div
        data-testid="sizes-bottom-row"
        aria-label={ariaLabel}
        style={{ fontSize: 12, color: "#4b5563", fontWeight: 500 }}
      >
        {bottomText}
      </div>
    </>,
    "dedup-sizes-card",
    ariaLabel
  );
}

export function DedupHammingCard({
  hamming_hist,
  threshold = 6,
}: {
  hamming_hist: Record<string, number>;
  threshold?: number;
}): JSX.Element {
  const histEntries = Object.entries(hamming_hist).map(([h, c]) => ({ h: parseInt(h, 10), count: c }));
  const paircount_total = histEntries.reduce((sum, e) => sum + e.count, 0);

  function _countFor(cond: (h: number) => boolean): number {
    return histEntries.filter((e) => cond(e.h)).reduce((sum, e) => sum + e.count, 0);
  }

  const rows = [
    {
      label: "h≤3",
      minWidth: 32,
      key: "le3",
      count: _countFor((h) => h <= 3),
      gradient: "linear-gradient(90deg, #10b981, #34d399)",
      testid: "hamming-row-le3",
    },
    {
      label: "h=4",
      minWidth: 32,
      key: "eq4",
      count: _countFor((h) => h === 4),
      gradient: "linear-gradient(90deg, #34d399, #6ee7b7)",
      testid: "hamming-row-eq4",
    },
    {
      label: "h=5",
      minWidth: 32,
      key: "eq5",
      count: _countFor((h) => h === 5),
      gradient: "linear-gradient(90deg, #6ee7b7, #fcd34d)",
      testid: "hamming-row-eq5",
    },
    {
      label: "h=6",
      minWidth: 32,
      key: "eq6",
      count: _countFor((h) => h === 6),
      gradient: "linear-gradient(90deg, #f59e0b, #fbbf24)",
      testid: "hamming-row-eq6",
    },
    {
      label: "h≥7",
      minWidth: 32,
      key: "ge7",
      count: _countFor((h) => h >= 7),
      gradient: "linear-gradient(90deg, #ef4444, #f87171)",
      testid: "hamming-row-ge7",
    },
  ];

  return _cardContainer(
    <>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
        <h4 data-testid="dedup-hamming-title" style={{ fontSize: 14, fontWeight: 700, margin: 0 }}>汉明距命中分布</h4>
        <span
          data-testid="hamming-thr-badge"
          aria-label="阈值锁定"
          style={{
            padding: "3px 10px",
            borderRadius: 999,
            fontSize: 12,
            fontWeight: 600,
            background: "#e0e7ff",
            color: "#3730a3",
            border: "1px solid #a5b4fc",
          }}
        >
          THR={threshold} 🔒locked
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
        {rows.map((r) => {
          const pct = paircount_total === 0 ? 0 : (r.count / paircount_total) * 100;
          const pctText = paircount_total === 0 ? "0.0" : pct.toFixed(1);
          return (
            <div
              key={r.key}
              data-testid={r.testid}
              style={{ display: "flex", alignItems: "center", gap: 8, width: "100%" }}
            >
              <span
                data-testid={`${r.testid}-label`}
                style={{
                  minWidth: r.minWidth,
                  width: 32,
                  fontSize: 12,
                  fontWeight: 600,
                  color: "#374151",
                }}
              >
                {r.label}
              </span>
              <div
                data-testid={`${r.testid}-barcontainer`}
                style={{
                  flex: 1,
                  background: "#f3f4f6",
                  borderRadius: 4,
                  height: 20,
                  overflow: "hidden",
                  position: "relative",
                }}
              >
                <div
                  data-testid={`${r.testid}-bar`}
                  style={{
                    width: `${pct}%`,
                    height: "100%",
                    background: r.gradient,
                    borderRadius: 4,
                  }}
                />
              </div>
              <span
                data-testid={`${r.testid}-count`}
                style={{
                  minWidth: 90,
                  textAlign: "right",
                  fontSize: 12,
                  color: "#4b5563",
                  fontWeight: 500,
                }}
              >
                {r.count} ({pctText}%)
              </span>
            </div>
          );
        })}
      </div>
    </>,
    "dedup-hamming-card",
    `Dedup hamming card, THR=${threshold} 锁定`
  );
}

export function DedupPerfCard({ perf }: { perf: DedupPerf }): JSX.Element {
  const {
    nodes,
    build_ms,
    query_avg_us,
    step1_total_ms,
    speedup_x,
    parallel_eff_x,
    slo_2000 = 3000,
    ratio,
  } = perf;

  const parallelPct = Math.round((parallel_eff_x / 8) * 100);
  const sloMs = slo_2000;
  const headroomPct = Math.max(0, 100 - ratio * 100);

  const rows: {
    key: string;
    label: string;
    valueNode: React.ReactNode;
    testid: string;
  }[] = [
    {
      key: "nodes",
      label: "节点数",
      testid: "perf-row-nodes",
      valueNode: (
        <span data-testid="perf-value-nodes" style={{ fontSize: 13, color: "#111827", fontWeight: 500 }}>
          {nodes.toLocaleString()}
        </span>
      ),
    },
    {
      key: "build_ms",
      label: "Build ms",
      testid: "perf-row-build",
      valueNode: (
        <span data-testid="perf-value-build" style={{ fontSize: 13, color: "#111827", fontWeight: 500 }}>
          {build_ms.toFixed(2)} ms
        </span>
      ),
    },
    {
      key: "query_avg_us",
      label: "Query avg",
      testid: "perf-row-query",
      valueNode: (
        <span data-testid="perf-value-query" style={{ fontSize: 13, color: "#111827", fontWeight: 500 }}>
          {query_avg_us.toFixed(1)} µs / 次
        </span>
      ),
    },
    {
      key: "step1_total_ms",
      label: "STEP1 total",
      testid: "perf-row-step1",
      valueNode: (
        <span
          data-testid="perf-value-step1"
          style={{ fontSize: 13, color: "#10b981", fontWeight: 700 }}
        >
          {step1_total_ms.toFixed(0)} ms
        </span>
      ),
    },
    {
      key: "speedup_x",
      label: "加速比",
      testid: "perf-row-speedup",
      valueNode: (
        <span data-testid="perf-value-speedup" style={{ fontSize: 13, color: "#111827", fontWeight: 500 }}>
          🚀 {speedup_x.toFixed(1)}×
        </span>
      ),
    },
    {
      key: "parallel_eff_x",
      label: "并行效率 理想8×",
      testid: "perf-row-parallel",
      valueNode: (
        <span data-testid="perf-value-parallel" style={{ fontSize: 13, color: "#111827", fontWeight: 500 }}>
          {parallel_eff_x.toFixed(2)}× 实际 {parallelPct}%
        </span>
      ),
    },
    {
      key: "slo_headroom",
      label: "SLO headroom",
      testid: "perf-row-slo",
      valueNode: (
        <span data-testid="perf-value-slo" style={{ fontSize: 13, color: "#111827", fontWeight: 500 }}>
          SLO {sloMs}ms × {ratio.toFixed(1)} headroom {headroomPct}%
        </span>
      ),
    },
  ];

  const minhashMs = perf.stage_ms?.minhash_ms ?? 0;
  const lshCandidates = perf.lsh_candidates ?? 0;
  const lshFilterRatio = perf.lsh_candidate_filter_ratio ?? 0;
  const oversampleEnabled = perf.oversample_prefix ? 1 : 0;

  return _cardContainer(
    <>
      <h4 data-testid="dedup-perf-title" style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, margin: 0 }}>BK-Tree 性能</h4>
      <div data-testid="hybrid-chips-row" style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 12 }}>
        <span
          data-testid="chip-minhash"
          title="MinHash"
          style={{
            padding: "3px 10px",
            borderRadius: 999,
            fontSize: 12,
            fontWeight: 600,
            background: "#dbeafe",
            color: "#1e40af",
            border: "1px solid #93c5fd",
          }}
        >
          MinHash · {minhashMs.toFixed(1)} ms
        </span>
        <span
          data-testid="chip-lsh-filter"
          title="LSH Filter"
          style={{
            padding: "3px 10px",
            borderRadius: 999,
            fontSize: 12,
            fontWeight: 600,
            background: "#fae8ff",
            color: "#86198f",
            border: "1px solid #f0abfc",
          }}
        >
          LSH Filter · {lshCandidates.toLocaleString()} cand ({(lshFilterRatio * 100).toFixed(1)}%)
        </span>
        <span
          data-testid="chip-oversample"
          title="Oversample"
          style={{
            padding: "3px 10px",
            borderRadius: 999,
            fontSize: 12,
            fontWeight: 600,
            background: "#fef3c7",
            color: "#92400e",
            border: "1px solid #fcd34d",
          }}
        >
          Oversample · prefix {oversampleEnabled}
        </span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {rows.map((r) => (
          <div
            key={r.key}
            data-testid={r.testid}
            style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 0" }}
          >
            <span style={{ fontSize: 12, color: "#6b7280", fontWeight: 500 }}>{r.label}</span>
            {r.valueNode}
          </div>
        ))}
      </div>
    </>,
    "dedup-perf-card",
    "Dedup performance diagnostic card"
  );
}

export default function DedupDiagCards(props: DedupDiagCardsProps): JSX.Element {
  const { diag, diagLoading = false, diagError = null } = props;

  if (diagLoading) {
    return (
      <div
        data-testid="dedup-diag-cards"
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
          gap: 16,
        }}
      >
        {["sizes", "hamming", "perf"].map((k) => (
          <div
            key={k}
            data-testid={`dedup-${k}-skeleton`}
            style={{
              padding: 16,
              background: "#fff",
              borderRadius: 8,
              border: "1px solid #e5e7eb",
              height: 180,
              backgroundImage:
                "linear-gradient(90deg, #f3f4f6 0px, #e5e7eb 40px, #f3f4f6 80px)",
              backgroundSize: "800px 100%",
            }}
          />
        ))}
      </div>
    );
  }

  if (diagError) {
    return (
      <div
        data-testid="dedup-diag-cards"
        aria-label={`Dedup diag error: ${diagError}`}
        style={{
          padding: 16,
          background: "#fef2f2",
          borderRadius: 8,
          border: "1px solid #fecaca",
          color: "#991b1b",
          fontWeight: 600,
        }}
      >
        ⚠️ {diagError}
      </div>
    );
  }

  return (
    <div
      data-testid="dedup-diag-cards"
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
        gap: 16,
      }}
    >
      <DedupSizesCard sizes_hist={diag.sizes_hist} />
      <DedupHammingCard hamming_hist={diag.hamming_hist} threshold={6} />
      {diag.perf && <DedupPerfCard perf={diag.perf} />}
      {!diag.perf && (
        <div
          data-testid="dedup-perf-empty"
          style={{
            padding: 16,
            background: "#fff",
            borderRadius: 8,
            border: "1px solid #e5e7eb",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#9ca3af",
            fontSize: 12,
          }}
        >
          — 无性能数据 —
        </div>
      )}
    </div>
  );
}

export { DedupDiagCards };
