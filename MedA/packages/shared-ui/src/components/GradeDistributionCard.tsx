import React from "react";

export interface GradeDistributionCardProps {
  distribution: { H: number; M: number; L: number } | null;
  title?: string;
}

const BAR_COLORS = {
  H: "#10b981",
  M: "#f59e0b",
  L: "#ef4444",
};

const BAR_TOOLTIPS = {
  H: "No RoB2 high downgrade",
  M: "1域 Some concerns → -1",
  L: "RoB2 Overall High → -2 + 间接性",
};

function _pct(n: number, total: number): string {
  if (total === 0) return "0.0";
  return ((n / total) * 100).toFixed(1);
}

export function GradeDistributionCard(props: GradeDistributionCardProps): JSX.Element {
  const { distribution, title = "🎓 GRADE 分布" } = props;

  if (distribution === null) {
    return (
      <div
        data-testid="grade-distribution-card"
        aria-label="GRADE evidence distribution loading"
        style={{
          padding: 16,
          background: "#fff",
          borderRadius: 8,
          border: "1px solid #e5e7eb",
        }}
      >
        <div
          data-testid="gdc-title"
          style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}
        >
          {title}
        </div>
        <div
          data-testid="gdc-bars-row"
          style={{
            display: "flex",
            width: "100%",
            height: 32,
            borderRadius: 4,
            overflow: "hidden",
            marginBottom: 12,
          }}
        >
          <div
            data-testid="gdc-skeleton-bar-H"
            className="gdc-skeleton-bar"
            style={{ flex: 1, background: "#d1d5db" }}
          />
          <div
            data-testid="gdc-skeleton-bar-M"
            className="gdc-skeleton-bar"
            style={{ flex: 1, background: "#d1d5db", marginLeft: 2 }}
          />
          <div
            data-testid="gdc-skeleton-bar-L"
            className="gdc-skeleton-bar"
            style={{ flex: 1, background: "#d1d5db", marginLeft: 2 }}
          />
        </div>
        <div
          data-testid="gdc-labels"
          style={{
            display: "flex",
            gap: 16,
            flexWrap: "wrap",
            fontSize: 12,
            color: "#9ca3af",
          }}
        >
          <span data-testid="gdc-label-H">● High —</span>
          <span data-testid="gdc-label-M">● Moderate —</span>
          <span data-testid="gdc-label-L">● Low —</span>
        </div>
      </div>
    );
  }

  const { H, M, L } = distribution;
  const total = H + M + L;
  const pctH = _pct(H, total);
  const pctM = _pct(M, total);
  const pctL = _pct(L, total);

  const ariaLabel = `GRADE evidence distribution: High ${H}, Moderate ${M}, Low ${L}`;

  return (
    <div
      data-testid="grade-distribution-card"
      aria-label={ariaLabel}
      style={{
        padding: 16,
        background: "#fff",
        borderRadius: 8,
        border: "1px solid #e5e7eb",
      }}
    >
      <div
        data-testid="gdc-title"
        style={{ fontSize: 14, fontWeight: 700, marginBottom: 12 }}
      >
        {title}
      </div>
      <div
        data-testid="gdc-bars-row"
        style={{
          display: "flex",
          width: "100%",
          height: 32,
          borderRadius: 4,
          overflow: "hidden",
          marginBottom: 12,
        }}
      >
        <div
          data-testid="gdc-bar-H"
          className="gdc-bar-H"
          title={`High: ${H} — ${BAR_TOOLTIPS.H}`}
          style={{
            width: `${pctH}%`,
            background: BAR_COLORS.H,
            minWidth: H > 0 ? 2 : 0,
          }}
        />
        <div
          data-testid="gdc-bar-M"
          className="gdc-bar-M"
          title={`Moderate: ${M} — ${BAR_TOOLTIPS.M}`}
          style={{
            width: `${pctM}%`,
            background: BAR_COLORS.M,
            minWidth: M > 0 ? 2 : 0,
          }}
        />
        <div
          data-testid="gdc-bar-L"
          className="gdc-bar-L"
          title={`Low: ${L} — ${BAR_TOOLTIPS.L}`}
          style={{
            width: `${pctL}%`,
            background: BAR_COLORS.L,
            minWidth: L > 0 ? 2 : 0,
          }}
        />
      </div>
      <div
        data-testid="gdc-labels"
        style={{
          display: "flex",
          gap: 16,
          flexWrap: "wrap",
          fontSize: 12,
          color: "#374151",
        }}
      >
        <span data-testid="gdc-label-H" style={{ color: BAR_COLORS.H, fontWeight: 600 }}>
          ● High {H} ({pctH}%)
        </span>
        <span data-testid="gdc-label-M" style={{ color: BAR_COLORS.M, fontWeight: 600 }}>
          ● Moderate {M} ({pctM}%)
        </span>
        <span data-testid="gdc-label-L" style={{ color: BAR_COLORS.L, fontWeight: 600 }}>
          ● Low {L} ({pctL}%)
        </span>
      </div>
    </div>
  );
}

export default GradeDistributionCard;
