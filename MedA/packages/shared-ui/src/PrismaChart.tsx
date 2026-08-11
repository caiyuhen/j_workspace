import React from "react";

export type PrismaSourceBreakdown = {
  source_key: string;
  source_label: string;
  records_retrieved: number;
  records_imported: number;
};

export type PrismaChartProps = {
  identification: number;
  screening: number;
  eligibility: number;
  included: number;
  by_source?: PrismaSourceBreakdown[];
  maxWidth?: number;
  barHeight?: number;
};

const PRISMA_LABELS = [
  { key: "identification", zh: "识别", en: "Identification" },
  { key: "screening", zh: "筛选", en: "Screening" },
  { key: "eligibility", zh: "合格", en: "Eligibility" },
  { key: "included", zh: "纳入", en: "Included" },
] as const;

const PRISMA_COLORS = ["#2563eb", "#3b82f6", "#60a5fa", "#93c5fd"];

export function calculatePrismaWidths(
  values: number[],
  maxWidth: number,
): number[] {
  if (values.length === 0) return [];
  const maxVal = Math.max(...values, 1);
  return values.map((v) => Math.max(1, Math.round((v / maxVal) * maxWidth)));
}

export function PrismaChart({
  identification,
  screening,
  eligibility,
  included,
  by_source = [],
  maxWidth = 600,
  barHeight = 52,
}: PrismaChartProps) {
  const values = [identification, screening, eligibility, included];
  const widths = calculatePrismaWidths(values, maxWidth);
  const labelWidth = 110;
  const numberWidth = 70;
  const barGap = 16;
  const totalBarAreaHeight = 4 * barHeight + 3 * barGap;
  const sourceSectionStart = totalBarAreaHeight + 48;
  const sourceBarHeight = 20;
  const sourceGap = 12;
  const sourceRowHeight = 2 * sourceBarHeight + sourceGap + 28;
  const sourceSectionHeight = by_source.length > 0 ? by_source.length * sourceRowHeight + 20 : 0;
  const svgWidth = labelWidth + maxWidth + numberWidth + 20;
  const svgHeight = sourceSectionStart + sourceSectionHeight + 20;

  return (
    <svg
      width={svgWidth}
      height={svgHeight}
      viewBox={`0 0 ${svgWidth} ${svgHeight}`}
      xmlns="http://www.w3.org/2000/svg"
      data-testid="prisma-chart"
    >
      {PRISMA_LABELS.map((label, idx) => {
        const y = idx * (barHeight + barGap);
        const width = widths[idx];
        const xStart = labelWidth + (maxWidth - width) / 2;
        return (
          <g key={label.key}>
            <text
              x={labelWidth - 12}
              y={y + barHeight / 2}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize="13"
              fontWeight="600"
              fill="#111827"
            >
              {label.zh}
            </text>
            <text
              x={labelWidth - 12}
              y={y + barHeight / 2 + 16}
              textAnchor="end"
              dominantBaseline="middle"
              fontSize="11"
              fill="#6b7280"
            >
              {label.en}
            </text>
            <rect
              data-testid={`prisma-bar-${label.key}`}
              x={xStart}
              y={y}
              width={width}
              height={barHeight}
              rx={8}
              fill={PRISMA_COLORS[idx]}
            />
            <text
              x={xStart + width / 2}
              y={y + barHeight / 2}
              textAnchor="middle"
              dominantBaseline="middle"
              fontSize="15"
              fontWeight="700"
              fill="#ffffff"
            >
              {values[idx].toLocaleString()}
            </text>
          </g>
        );
      })}

      {by_source.length > 0 && (
        <>
          <text
            x={labelWidth}
            y={sourceSectionStart - 12}
            fontSize="13"
            fontWeight="600"
            fill="#374151"
          >
            各来源明细（检索命中 / 成功入库）
          </text>
          {by_source.map((src, sIdx) => {
            const rowY = sourceSectionStart + sIdx * sourceRowHeight;
            const srcMax = Math.max(src.records_retrieved, src.records_imported, 1);
            const retrievedWidth = Math.max(
              2,
              Math.round((src.records_retrieved / srcMax) * (maxWidth * 0.7)),
            );
            const importedWidth = Math.max(
              2,
              Math.round((src.records_imported / srcMax) * (maxWidth * 0.7)),
            );
            return (
              <g key={src.source_key} data-testid={`source-group-${src.source_key}`}>
                <text
                  x={labelWidth}
                  y={rowY + 14}
                  fontSize="12"
                  fontWeight="600"
                  fill="#374151"
                >
                  {src.source_label}
                </text>
                <rect
                  data-testid={`source-bar-retrieved-${src.source_key}`}
                  x={labelWidth}
                  y={rowY + 24}
                  width={retrievedWidth}
                  height={sourceBarHeight}
                  rx={4}
                  fill="#60a5fa"
                />
                <text
                  x={labelWidth + retrievedWidth + 8}
                  y={rowY + 24 + sourceBarHeight / 2}
                  dominantBaseline="middle"
                  fontSize="11"
                  fill="#4b5563"
                >
                  检索 {src.records_retrieved}
                </text>
                <rect
                  data-testid={`source-bar-imported-${src.source_key}`}
                  x={labelWidth}
                  y={rowY + 24 + sourceBarHeight + 4}
                  width={importedWidth}
                  height={sourceBarHeight}
                  rx={4}
                  fill="#10b981"
                />
                <text
                  x={labelWidth + importedWidth + 8}
                  y={rowY + 24 + sourceBarHeight + 4 + sourceBarHeight / 2}
                  dominantBaseline="middle"
                  fontSize="11"
                  fill="#4b5563"
                >
                  入库 {src.records_imported}
                </text>
              </g>
            );
          })}
        </>
      )}
    </svg>
  );
}
