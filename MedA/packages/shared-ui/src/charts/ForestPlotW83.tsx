import React from "react";

export interface ForestStudyRow {
  study_id: string;
  study_label: string;
  effect: number;
  ci_low: number;
  ci_high: number;
  weight: number;
}

export interface ForestMetaResult {
  pooled: {
    effect: number;
    ci_low: number;
    ci_high: number;
  };
  heterogeneity: {
    I2_pct: number;
  };
}

export interface ForestPlotW83Props {
  studies: ForestStudyRow[];
  result?: ForestMetaResult | undefined;
  width?: number;
  height?: number;
}

const NO_DATA = (
  <div data-testid="no-data-forest" style={{
    padding: "24px",
    textAlign: "center",
    color: "#6b7280",
    fontSize: "14px",
    border: "1px dashed #d1d5db",
    borderRadius: "8px",
    background: "#f9fafb",
  }}>
    📊 暂无数据：尚无研究数据可绘制森林图
  </div>
);

export const ForestPlotW83: React.FC<ForestPlotW83Props> = ({
  studies,
  result,
  width = 800,
  height = 500,
}) => {
  const hasData = studies.length > 0;

  if (!hasData) {
    return NO_DATA;
  }

  const K = studies.length;
  const padding = { left: 120, right: 120, top: 40, bottom: 80 };
  const plotW = width - padding.left - padding.right;
  const plotH = height - padding.top - padding.bottom;
  const rowH = plotH / Math.max(K + 2, 4);

  let minX = Infinity;
  let maxX = -Infinity;
  for (const s of studies) {
    if (s.ci_low < minX) minX = s.ci_low;
    if (s.ci_high > maxX) maxX = s.ci_high;
  }
  if (result) {
    if (result.pooled.ci_low < minX) minX = result.pooled.ci_low;
    if (result.pooled.ci_high > maxX) maxX = result.pooled.ci_high;
  }
  if (minX > 1) minX = 0.5;
  if (maxX < 1) maxX = 2;
  minX = Math.min(minX, 0.5);
  maxX = Math.max(maxX, 1.5);
  const padX = (maxX - minX) * 0.08;
  minX -= padX;
  maxX += padX;

  const xToPx = (x: number): number => {
    return padding.left + ((x - minX) / (maxX - minX)) * plotW;
  };
  const yToPxRow = (rowIdx: number): number => {
    return padding.top + rowH * 0.5 + rowIdx * rowH;
  };

  const viewBox = `0 0 ${width} ${height}`;
  const x0 = xToPx(1);

  const i2Pct = result?.heterogeneity?.I2_pct ?? 0;
  const pooledEffect = result?.pooled;

  return (
    <svg
      data-testid="forest-svg-root"
      className="forest-svg"
      width={width}
      height={height}
      viewBox={viewBox}
      xmlns="http://www.w3.org/2000/svg"
      style={{ display: "block", background: "#fff" }}
    >
      <line
        x1={x0}
        y1={padding.top - 10}
        x2={x0}
        y2={padding.top + K * rowH + 10}
        stroke="#9ca3af"
        strokeWidth={1}
        strokeDasharray="4 3"
      />

      <line
        x1={padding.left}
        y1={padding.top + K * rowH + 12}
        x2={padding.left + plotW}
        y2={padding.top + K * rowH + 12}
        stroke="#374151"
        strokeWidth={1.2}
      />

      {Array.from({ length: 5 }).map((_, i) => {
        const xVal = minX + ((maxX - minX) * i) / 4;
        const px = xToPx(xVal);
        return (
          <g key={`axis-tick-${i}`}>
            <line
              x1={px}
              y1={padding.top + K * rowH + 12}
              x2={px}
              y2={padding.top + K * rowH + 18}
              stroke="#374151"
              strokeWidth={1}
            />
            <text
              x={px}
              y={padding.top + K * rowH + 32}
              textAnchor="middle"
              fontSize="11"
              fill="#4b5563"
              fontFamily="sans-serif"
            >
              {xVal.toFixed(2)}
            </text>
          </g>
        );
      })}

      {studies.map((s, i) => {
        const y = yToPxRow(i);
        const cx = xToPx(s.effect);
        const x1 = xToPx(s.ci_low);
        const x2 = xToPx(s.ci_high);
        const size = 6 + Math.sqrt(s.weight) * 1.2;
        return (
          <g data-testid={`forest-row-${i}`} key={`row-${i}`}>
            <text
              x={padding.left - 8}
              y={y + 4}
              textAnchor="end"
              fontSize="12"
              fill="#1f2937"
              fontFamily="sans-serif"
            >
              {s.study_label}
            </text>
            <line
              data-testid={`forest-hline-${i}`}
              x1={x1}
              y1={y}
              x2={x2}
              y2={y}
              stroke="#2563eb"
              strokeWidth={1.8}
            />
            <line x1={x1} y1={y - 4} x2={x1} y2={y + 4} stroke="#2563eb" strokeWidth={1.8} />
            <line x1={x2} y1={y - 4} x2={x2} y2={y + 4} stroke="#2563eb" strokeWidth={1.8} />
            <rect
              data-testid={`forest-square-${i}`}
              x={cx - size / 2}
              y={y - size / 2}
              width={size}
              height={size}
              fill="#1e3a8a"
              stroke="#0f172a"
              strokeWidth={0.5}
            />
            <text
              x={padding.left + plotW + 8}
              y={y + 4}
              fontSize="12"
              fill="#1f2937"
              fontFamily="sans-serif"
            >
              {s.effect.toFixed(2)} [{s.ci_low.toFixed(2)}, {s.ci_high.toFixed(2)}]
            </text>
          </g>
        );
      })}

      {pooledEffect && (() => {
        const y = yToPxRow(K);
        const cx = xToPx(pooledEffect.effect);
        const lx = xToPx(pooledEffect.ci_low);
        const hx = xToPx(pooledEffect.ci_high);
        const w = 14;
        const h = 18;
        const pts = [
          `${cx},${y - h / 2}`,
          `${hx},${y}`,
          `${cx},${y + h / 2}`,
          `${lx},${y}`,
        ].join(" ");
        return (
          <g key="pooled-group">
            <line
              x1={lx}
              y1={y}
              x2={hx}
              y2={y}
              stroke="#15803d"
              strokeWidth={2.2}
            />
            <polygon
              data-testid="diamond-pooled"
              points={pts}
              fill="#16a34a"
              stroke="#14532d"
              strokeWidth={1.2}
            />
            <text
              x={padding.left - 8}
              y={y + 4}
              textAnchor="end"
              fontSize="12"
              fontWeight="700"
              fill="#15803d"
              fontFamily="sans-serif"
            >
              Pooled
            </text>
            <text
              x={padding.left + plotW + 8}
              y={y + 4}
              fontSize="12"
              fontWeight="700"
              fill="#15803d"
              fontFamily="sans-serif"
            >
              {pooledEffect.effect.toFixed(2)} [{pooledEffect.ci_low.toFixed(2)}, {pooledEffect.ci_high.toFixed(2)}]
            </text>
          </g>
        );
      })()}

      <text
        data-testid="i2-text"
        x={padding.left}
        y={height - 22}
        fontSize="13"
        fontWeight="700"
        fill="#b45309"
        fontFamily="sans-serif"
      >
        {`I\u00b2 = ${i2Pct.toFixed(1)}%`}
      </text>
    </svg>
  );
};
