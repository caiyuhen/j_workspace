import React from "react";
import type { TrafficLightRating } from "@meda/shared-sdk";

const TRAFFIC_LIGHT_COLORS: Record<TrafficLightRating, { bg: string; text: string; emoji: string }> = {
  low: { bg: "#10b981", text: "#ffffff", emoji: "🟢" },
  some_concerns: { bg: "#fbbf24", text: "#78350f", emoji: "🟡" },
  high: { bg: "#ef4444", text: "#ffffff", emoji: "🔴" },
  critical: { bg: "#dc2626", text: "#ffffff", emoji: "🔥" },
  ni: { bg: "#f1f5f9", text: "#64748b", emoji: "➖" },
};

const SIZE_STYLES: Record<'sm' | 'md' | 'lg', { padding: string; fontSize: string; minWidth: string }> = {
  sm: { padding: "0.125rem 0.375rem", fontSize: "0.75rem", minWidth: "32px" },
  md: { padding: "0.25rem 0.625rem", fontSize: "0.875rem", minWidth: "40px" },
  lg: { padding: "0.375rem 0.875rem", fontSize: "1rem", minWidth: "48px" },
};

export function TrafficLightCell({
  rating,
  size = "sm",
  onClick,
  style,
}: {
  rating: TrafficLightRating;
  size?: "sm" | "md" | "lg";
  onClick?: () => void;
  style?: React.CSSProperties;
}): JSX.Element {
  const c = TRAFFIC_LIGHT_COLORS[rating];
  const s = SIZE_STYLES[size];
  return (
    <span
      data-testid={`tlc-${rating}`}
      onClick={onClick}
      style={{
        display: "inline-flex",
        alignItems: "center",
        justifyContent: "center",
        gap: "0.25rem",
        backgroundColor: c.bg,
        color: c.text,
        padding: s.padding,
        fontSize: s.fontSize,
        minWidth: s.minWidth,
        borderRadius: "0.25rem",
        fontWeight: 600,
        fontFamily: "system-ui",
        cursor: onClick ? "pointer" : "default",
        userSelect: "none",
        ...style,
      }}
    >
      <span>{c.emoji}</span>
    </span>
  );
}

export { TRAFFIC_LIGHT_COLORS };
