import React from "react";
import type { FunnelStepStat } from "@meda/shared-sdk";

export const FUNNEL_COLORS: Record<string, string> = {
  N1: "#6366f1",
  N2: "#8b5cf6",
  N3: "#ec4899",
  N4: "#f43f5e",
  E1: "#0ea5e9",
  E2: "#ef4444",
  E3: "#0284c7",
  E4: "#059669",
  E5: "#dc2626",
  E6: "#10b981",
};

export const FUNNEL_ORDER_KEYS = ["N1", "N2", "N3", "N4", "E1", "E2", "E3", "E4", "E5", "E6"] as const;

export type FunnelStudyType = "ALL" | "RCT" | "NRSI";

export interface FunnelProgressBarProps {
  stats: FunnelStepStat[];
  studyType?: FunnelStudyType;
  onStepClick?: (stepKey: string, event: React.MouseEvent<HTMLButtonElement>) => void;
  "data-testid"?: string;
}

const EXCLUDE_REASONS_MAP: Record<number, { ta_allowed: boolean; ft_allowed: boolean }> = {
  1: { ta_allowed: true, ft_allowed: false },
  2: { ta_allowed: true, ft_allowed: false },
  3: { ta_allowed: true, ft_allowed: false },
  4: { ta_allowed: true, ft_allowed: false },
  5: { ta_allowed: true, ft_allowed: false },
  6: { ta_allowed: false, ft_allowed: true },
  7: { ta_allowed: false, ft_allowed: true },
  8: { ta_allowed: false, ft_allowed: true },
  9: { ta_allowed: true, ft_allowed: true },
};

export function getExcludeReasonTaAllowed(reasonId: number): boolean {
  return EXCLUDE_REASONS_MAP[reasonId]?.ta_allowed ?? false;
}

function _filterStatsByStudyType(
  stats: FunnelStepStat[],
  studyType: FunnelStudyType | undefined,
): FunnelStepStat[] {
  if (!studyType || studyType === "ALL") return stats;
  return stats;
}

export default function FunnelProgressBar(
  props: FunnelProgressBarProps,
): JSX.Element {
  const { stats, studyType, onStepClick, "data-testid": rootTestId } = props;

  const filtered = _filterStatsByStudyType(stats, studyType);

  const maxCount = Math.max(
    1,
    ...filtered.map((s) => s.count).filter((n) => typeof n === "number"),
  );

  return (
    <div data-testid={rootTestId ?? "funnel-progress-bar"}>
      {filtered.map((step) => {
        const widthPct = maxCount > 0 ? (step.count / maxCount) * 100 : 0;
        const color = FUNNEL_COLORS[step.key] ?? "#9ca3af";
        const isLocked = step.locked === true;

        return (
          <button
            key={step.key}
            data-testid={`fpb-step-${step.key}`}
            disabled={isLocked}
            aria-disabled={isLocked ? true : undefined}
            onClick={(e) => {
              if (!isLocked && onStepClick) onStepClick(step.key, e);
            }}
            style={{
              display: "block",
              width: `${Math.max(0, widthPct)}%`,
              height: "32px",
              backgroundColor: color,
              opacity: isLocked ? 0.35 : 1,
              pointerEvents: isLocked ? "none" : "auto",
              border: "none",
              padding: 0,
              margin: "4px 0",
              textAlign: "left",
              cursor: isLocked ? "default" : "pointer",
            }}
          >
            <span data-testid={`fpb-label-${step.key}`} style={{ paddingLeft: "8px", color: "white", fontSize: "12px" }}>
              {step.label ?? step.key} ({step.count})
            </span>
          </button>
        );
      })}
    </div>
  );
}

export { FunnelProgressBar };
