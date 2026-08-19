import React from "react";

export interface ConfidenceBarProps {
  value: number;
  label?: string;
  "data-testid"?: string;
}

function _getGradient(value: number): string {
  if (value >= 0.85) {
    return "linear-gradient(90deg, #10b981 0%, #059669 100%)";
  }
  if (value >= 0.45) {
    return "linear-gradient(90deg, #f59e0b 0%, #d97706 100%)";
  }
  return "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)";
}

function _clamp(v: number): number {
  return Math.max(0, Math.min(1, v));
}

export default function ConfidenceBar(props: ConfidenceBarProps): JSX.Element {
  const { value, label } = props;
  const clamped = _clamp(value);
  const pct = Math.round(clamped * 100);
  const testIdKey = label ?? "default";
  const gradient = _getGradient(clamped);

  return (
    <div
      data-testid={`confidence-bar-${testIdKey}`}
      style={{
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      {label && (
        <span
          style={{
            fontSize: 12,
            color: "#374151",
            fontWeight: 500,
            whiteSpace: "nowrap",
          }}
        >
          {label}
        </span>
      )}
      <div
        style={{
          flex: 1,
          height: 8,
          backgroundColor: "#e5e7eb",
          borderRadius: 4,
          overflow: "hidden",
          minWidth: 40,
        }}
      >
        <div
          data-testid={`confidence-bar-inner-${testIdKey}`}
          style={{
            width: `${clamped * 100}%`,
            height: "100%",
            background: gradient,
            transition: "width 0.3s ease",
          }}
        />
      </div>
      <span
        data-testid={`confidence-bar-pct-${testIdKey}`}
        style={{
          fontSize: 12,
          fontWeight: 600,
          color: "#111827",
          minWidth: 32,
          textAlign: "right",
          whiteSpace: "nowrap",
        }}
      >
        {pct}%
      </span>
    </div>
  );
}

export { ConfidenceBar };
