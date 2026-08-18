import React, { useState, useEffect } from "react";

export type PrismaOverrideEditorProps = {
  open: boolean;
  initialStats?: { identification?: number; screening?: number; eligibility?: number; included?: number } | null;
  onApply: (v: { identification?: number; screening?: number; eligibility?: number; included?: number }) => void;
  onClear: () => void;
  onCancel: () => void;
  diffRatio?: number | null;
};

export const PrismaOverrideEditor: React.FC<PrismaOverrideEditorProps> = ({
  open,
  initialStats,
  onApply,
  onClear,
  onCancel,
  diffRatio,
}) => {
  const [identification, setIdentification] = useState<string>(
    `${initialStats?.identification ?? ""}`,
  );
  const [screening, setScreening] = useState<string>(
    `${initialStats?.screening ?? initialStats?.identification ?? ""}`,
  );
  const [eligibility, setEligibility] = useState<string>(
    `${initialStats?.eligibility ?? ""}`,
  );
  const [included, setIncluded] = useState<string>(
    `${initialStats?.included ?? ""}`,
  );

  useEffect(() => {
    if (open) {
      setIdentification(`${initialStats?.identification ?? ""}`);
      setScreening(`${initialStats?.screening ?? initialStats?.identification ?? ""}`);
      setEligibility(`${initialStats?.eligibility ?? ""}`);
      setIncluded(`${initialStats?.included ?? ""}`);
    }
  }, [open, initialStats]);

  const idVal = parseInt(identification || "0", 10);
  const scVal = parseInt(screening || "0", 10);
  const elVal = parseInt(eligibility || "0", 10);
  const inVal = parseInt(included || "0", 10);
  const anyNaN = isNaN(idVal) || isNaN(scVal) || isNaN(elVal) || isNaN(inVal);
  const applyDisabled = inVal > elVal || anyNaN;

  const apply = () => {
    onApply({
      identification: idVal || 0,
      screening: scVal || 0,
      eligibility: elVal || 0,
      included: inVal || 0,
    });
    onCancel();
  };

  if (!open) return null;

  const showBadge30 = diffRatio != null && diffRatio > 0.2;

  return (
    <div
      role="dialog"
      aria-modal="true"
      data-testid="prisma-override-editor"
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,.3)", zIndex: 999, display: "flex", alignItems: "center", justifyContent: "center" }}
    >
      <div style={{ background: "#fff", padding: 20, borderRadius: 8, minWidth: 480 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <h3 style={{ margin: 0 }}>Manual PRISMA Override 四格手动覆盖</h3>
          {showBadge30 ? (
            <span
              data-testid="override-badge-30"
              style={{ padding: "2px 8px", background: "#fee2e2", color: "#991b1b", borderRadius: 999, fontSize: 12, fontWeight: 600 }}
            >
              Override Applied {Math.round((diffRatio as number) * 100)}%
            </span>
          ) : null}
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
          {(
            [
              ["Identification N1", "ov-identification", identification, setIdentification],
              ["Screening N2", "ov-screening", screening, setScreening],
              ["Eligibility N3", "ov-eligibility", eligibility, setEligibility],
              ["Included N4", "ov-included", included, setIncluded],
            ] as Array<[string, string, string, React.Dispatch<React.SetStateAction<string>>]>
          ).map(([label, tid, val, setter]) => (
            <label key={tid} style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 13 }}>
              <span>{label}</span>
              <input
                data-testid={tid}
                type="number"
                value={val}
                onChange={(e) => setter(e.target.value)}
                style={{ padding: "6px 8px", border: "1px solid #d1d5db", borderRadius: 4 }}
              />
            </label>
          ))}
        </div>
        {inVal > elVal ? (
          <div data-testid="ov-error-hint" style={{ marginTop: 8, color: "#dc2626", fontSize: 12 }}>
            ⚠ Included ({inVal}) must be ≤ Eligibility ({elVal})
          </div>
        ) : null}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: 8, marginTop: 16 }}>
          <button
            type="button"
            data-testid="btn-override-clear"
            onClick={onClear}
            style={{ padding: "6px 12px", background: "#fef2f2", color: "#991b1b", border: "1px solid #fecaca", borderRadius: 4, cursor: "pointer" }}
          >
            恢复 Auto（清空 override）
          </button>
          <button
            type="button"
            data-testid="btn-override-cancel"
            onClick={onCancel}
            style={{ padding: "6px 12px", border: "1px solid #d1d5db", background: "#fff", borderRadius: 4, cursor: "pointer" }}
          >
            取消
          </button>
          <button
            type="button"
            data-testid="btn-override-apply"
            onClick={apply}
            disabled={applyDisabled}
            style={{
              padding: "6px 14px",
              background: applyDisabled ? "#9ca3af" : "#dc2626",
              color: "#fff",
              border: "none",
              borderRadius: 4,
              cursor: applyDisabled ? "not-allowed" : "pointer",
            }}
          >
            应用 override
          </button>
        </div>
      </div>
    </div>
  );
};

export type { PrismaOverrideEditorProps as PrismaOverrideEditorT11Props };
