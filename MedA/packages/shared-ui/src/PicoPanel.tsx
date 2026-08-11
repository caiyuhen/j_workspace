import React, { useState } from "react";

export type PicoFieldValues = {
  population?: string | null;
  intervention?: string | null;
  comparison?: string | null;
  outcome?: string | null;
};

export type PicoPanelProps = {
  pico?: PicoFieldValues;
  recordCount?: number;
  batchExtractThreshold?: number;
  onBatchExtract?: () => void;
  autofillSuggestion?: PicoFieldValues | null;
  onConfirmAutofill?: () => void;
  compact?: boolean;
};

const PILL_KEYS: Array<{
  key: keyof Required<PicoFieldValues>;
  zh: string;
  en: string;
  accent: string;
}> = [
  { key: "population", zh: "人群", en: "P", accent: "#7c3aed" },
  { key: "intervention", zh: "干预", en: "I", accent: "#2563eb" },
  { key: "comparison", zh: "对照", en: "C", accent: "#0891b2" },
  { key: "outcome", zh: "结局", en: "O", accent: "#047857" },
];

function PicoPill({
  labelEn,
  labelZh,
  value,
  accent,
  compact,
}: {
  labelEn: string;
  labelZh: string;
  value?: string | null;
  accent: string;
  compact?: boolean;
}) {
  const hasValue = value != null && value.trim() !== "";
  const padding = compact ? "6px 10px" : "10px 14px";
  const fontSize = compact ? "12px" : "13px";
  return (
    <div
      data-testid={`pico-pill-${labelEn.toLowerCase()}`}
      style={{
        border: `1px solid ${hasValue ? accent : "#e5e7eb"}`,
        background: hasValue ? "#ffffff" : "#f9fafb",
        borderRadius: "999px",
        padding,
        display: "inline-flex",
        alignItems: "center",
        gap: "8px",
        minWidth: compact ? "160px" : "220px",
      }}
    >
      <span
        style={{
          background: hasValue ? accent : "#9ca3af",
          color: "#ffffff",
          fontSize: compact ? "10px" : "11px",
          fontWeight: 800,
          borderRadius: "999px",
          width: compact ? "20px" : "24px",
          height: compact ? "20px" : "24px",
          display: "inline-flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {labelEn}
      </span>
      <span style={{ fontSize, fontWeight: 600, color: "#111827" }}>
        {labelZh}
      </span>
      <span
        style={{
          fontSize,
          color: hasValue ? "#374151" : "#9ca3af",
          marginLeft: "auto",
          maxWidth: compact ? "100px" : "180px",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
        }}
        title={hasValue ? value ?? undefined : undefined}
      >
        {hasValue ? value : "待抽取…"}
      </span>
    </div>
  );
}

export function PicoPanel({
  pico,
  recordCount = 0,
  batchExtractThreshold = 20,
  onBatchExtract,
  autofillSuggestion = null,
  onConfirmAutofill,
  compact = false,
}: PicoPanelProps) {
  const [confirmOpen, setConfirmOpen] = useState(false);
  const shouldShowBatch =
    !compact && recordCount > batchExtractThreshold && !!onBatchExtract;
  const shouldShowAutofill = !compact && !!autofillSuggestion && !!onConfirmAutofill;

  const handleConfirmYes = () => {
    setConfirmOpen(false);
    onConfirmAutofill?.();
  };

  return (
    <div
      data-testid="pico-panel"
      style={{
        display: "flex",
        flexDirection: "column",
        gap: compact ? "8px" : "16px",
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          gap: compact ? "8px" : "12px",
        }}
      >
        {PILL_KEYS.map(({ key, zh, en, accent }) => (
          <PicoPill
            key={key}
            labelEn={en}
            labelZh={zh}
            value={pico?.[key] ?? null}
            accent={accent}
            compact={compact}
          />
        ))}
      </div>

      {(shouldShowBatch || shouldShowAutofill) && (
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            gap: "10px",
            flexWrap: "wrap",
          }}
        >
          {shouldShowBatch && (
            <button
              data-testid="btn-batch-extract-pico"
              onClick={onBatchExtract}
              style={{
                border: "1px solid #2563eb",
                background: "#eff6ff",
                color: "#1d4ed8",
                borderRadius: "999px",
                padding: "8px 16px",
                cursor: "pointer",
                fontSize: "13px",
                fontWeight: 600,
              }}
            >
              批量抽取 PICO ({recordCount})
            </button>
          )}
          {shouldShowAutofill && (
            <button
              data-testid="btn-autofill-suggest"
              onClick={() => setConfirmOpen(true)}
              style={{
                border: "none",
                background: "#111827",
                color: "#f9fafb",
                borderRadius: "999px",
                padding: "8px 16px",
                cursor: "pointer",
                fontSize: "13px",
                fontWeight: 600,
              }}
            >
              高频 PICO 回写到检索式
            </button>
          )}
        </div>
      )}

      {confirmOpen && autofillSuggestion && (
        <div
          data-testid="autofill-confirm-dialog"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(15, 23, 42, 0.45)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 50,
          }}
          onClick={() => setConfirmOpen(false)}
        >
          <div
            onClick={(e) => e.stopPropagation()}
            style={{
              background: "#ffffff",
              borderRadius: "16px",
              padding: "24px",
              width: "min(520px, 92vw)",
              boxShadow: "0 20px 60px rgba(15, 23, 42, 0.2)",
            }}
          >
            <h3
              style={{
                margin: "0 0 12px",
                fontSize: "18px",
                fontWeight: 700,
              }}
            >
              确认回填检索式
            </h3>
            <p style={{ margin: "0 0 16px", color: "#4b5563", fontSize: "14px" }}>
              将以下建议回填为检索式草稿，是否继续？
            </p>
            <div
              style={{
                display: "grid",
                gap: "8px",
                padding: "12px",
                background: "#f8fafc",
                borderRadius: "10px",
                marginBottom: "20px",
              }}
            >
              {PILL_KEYS.map(({ key, zh, en, accent }) => {
                const v = autofillSuggestion[key];
                return (
                  <div
                    key={key}
                    style={{
                      display: "flex",
                      gap: "10px",
                      alignItems: "flex-start",
                      fontSize: "13px",
                    }}
                  >
                    <span
                      style={{
                        background: accent,
                        color: "#fff",
                        borderRadius: "999px",
                        width: "22px",
                        height: "22px",
                        display: "inline-flex",
                        alignItems: "center",
                        justifyContent: "center",
                        fontSize: "11px",
                        fontWeight: 800,
                        flexShrink: 0,
                      }}
                    >
                      {en}
                    </span>
                    <span style={{ fontWeight: 600, color: "#374151" }}>
                      {zh}：
                    </span>
                    <span style={{ color: "#111827" }}>
                      {v && v.trim() !== "" ? v : "（空）"}
                    </span>
                  </div>
                );
              })}
            </div>
            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "10px",
              }}
            >
              <button
                data-testid="autofill-cancel"
                onClick={() => setConfirmOpen(false)}
                style={{
                  border: "1px solid #d0d7e2",
                  background: "#ffffff",
                  color: "#374151",
                  borderRadius: "999px",
                  padding: "8px 18px",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: 600,
                }}
              >
                No
              </button>
              <button
                data-testid="autofill-yes"
                onClick={handleConfirmYes}
                style={{
                  border: "none",
                  background: "#111827",
                  color: "#f9fafb",
                  borderRadius: "999px",
                  padding: "8px 18px",
                  cursor: "pointer",
                  fontSize: "13px",
                  fontWeight: 600,
                }}
              >
                Yes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
