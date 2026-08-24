import React, { useState, useEffect } from "react";

const PRESETS: string[] = [
  "sglt2i_ckd",
  "empagliflozin_hf",
  "glp1_weightloss",
  "liraglutide_nafld",
  "pkd_tolvaptan",
  "ckd_blood_pressure_control",
];

export interface NewRunModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (payload: {
    preset: string;
    mode: "snapshot" | "live";
    max_records: number;
  }) => void | Promise<void>;
  initialPreset?: string;
  initialMaxRecords?: number;
}

export function NewRunModal(props: NewRunModalProps): JSX.Element | null {
  const { open, onClose, onConfirm, initialPreset, initialMaxRecords } = props;
  const [preset, setPreset] = useState<string | null>(initialPreset ?? null);
  const [mode, setMode] = useState<"snapshot" | "live">("snapshot");
  const [maxRecordsStr, setMaxRecordsStr] = useState<string>(
    String(initialMaxRecords ?? 200),
  );

  useEffect(() => {
    if (open) {
      setPreset(initialPreset ?? null);
      setMaxRecordsStr(String(initialMaxRecords ?? 200));
      setMode("snapshot");
    }
  }, [open, initialPreset, initialMaxRecords]);

  const maxRecordsNum = Number(maxRecordsStr);
  const maxRecordsValid =
    maxRecordsStr !== "" &&
    !Number.isNaN(maxRecordsNum) &&
    maxRecordsNum >= 1 &&
    maxRecordsNum <= 2500;
  const over2500 =
    maxRecordsStr !== "" && !Number.isNaN(maxRecordsNum) && maxRecordsNum > 2500;
  const valid = preset !== null && maxRecordsValid;

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-label="启动新 Pipeline Run dialog"
      data-testid="new-run-modal"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") onClose();
      }}
    >
      <div
        data-testid="modal-content"
        style={{
          background: "#fff",
          borderRadius: 12,
          padding: 24,
          minWidth: 520,
          maxWidth: 640,
          boxShadow: "0 20px 25px -5px rgba(0,0,0,0.1)",
        }}
      >
        <h2
          data-testid="modal-title"
          style={{
            margin: "0 0 20px 0",
            fontSize: 20,
            fontWeight: 700,
            color: "#111827",
          }}
        >
          🔬 启动新 Pipeline Run
        </h2>

        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: "#374151",
              marginBottom: 8,
            }}
          >
            1. 选择 Preset
          </div>
          <div
            data-testid="preset-chips-grid"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(2, 1fr)",
              gap: 8,
            }}
          >
            {PRESETS.map((p) => {
              const selected = preset === p;
              return (
                <button
                  key={p}
                  data-testid={`preset-chip-${p}`}
                  onClick={() => setPreset(p)}
                  style={{
                    padding: "10px 12px",
                    borderRadius: 8,
                    border: `1px solid ${selected ? "#2563eb" : "#d1d5db"}`,
                    background: selected ? "#dbeafe" : "#f9fafb",
                    color: selected ? "#1e40af" : "#374151",
                    fontSize: 12,
                    fontWeight: selected ? 700 : 500,
                    cursor: "pointer",
                    textAlign: "left",
                    transition: "all 0.15s",
                  }}
                >
                  {selected && "✓ "}
                  {p}
                </button>
              );
            })}
          </div>
        </div>

        <div style={{ marginBottom: 20 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: "#374151",
              marginBottom: 8,
            }}
          >
            2. 运行模式
          </div>
          <div
            data-testid="mode-toggle"
            style={{ display: "flex", gap: 0, border: "1px solid #d1d5db", borderRadius: 8, overflow: "hidden" }}
          >
            <button
              data-testid="mode-snapshot"
              onClick={() => setMode("snapshot")}
              style={{
                flex: 1,
                padding: "10px 12px",
                border: "none",
                background: mode === "snapshot" ? "#dbeafe" : "#f9fafb",
                color: mode === "snapshot" ? "#1e40af" : "#374151",
                fontSize: 13,
                fontWeight: mode === "snapshot" ? 700 : 500,
                cursor: "pointer",
              }}
            >
              🔵 Snapshot (离线 快 稳)
            </button>
            <button
              data-testid="mode-live"
              onClick={() => setMode("live")}
              style={{
                flex: 1,
                padding: "10px 12px",
                border: "none",
                background: mode === "live" ? "#dcfce7" : "#f9fafb",
                color: mode === "live" ? "#166534" : "#374151",
                fontSize: 13,
                fontWeight: mode === "live" ? 700 : 500,
                cursor: "pointer",
              }}
            >
              🟢 Live (需联网 PubMed NCBI)
            </button>
          </div>
        </div>

        <div style={{ marginBottom: 24 }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 600,
              color: "#374151",
              marginBottom: 8,
            }}
          >
            3. Max Records (1-2000)
          </div>
          <input
            type="number"
            data-testid="input-max-records"
            value={maxRecordsStr}
            onChange={(e) => setMaxRecordsStr(e.target.value)}
            min={1}
            max={2000}
            step={50}
            disabled={preset === null}
            style={{
              width: "100%",
              padding: "10px 12px",
              borderRadius: 8,
              border: `1px solid ${over2500 ? "#ef4444" : "#d1d5db"}`,
              fontSize: 14,
              boxSizing: "border-box",
            }}
          />
          {over2500 && (
            <div
              data-testid="error-max-records"
              style={{
                marginTop: 6,
                fontSize: 12,
                color: "#dc2626",
                fontWeight: 600,
              }}
            >
              超过最大上限 2500 篇（含 buffer）
            </div>
          )}
          {mode === "live" && maxRecordsNum > 500 && (
            <div
              data-testid="banner-live-large"
              aria-label="warn_live_large"
              style={{
                marginTop: 10,
                padding: "10px 12px",
                borderRadius: 8,
                background: "#fffbeb",
                border: "1px solid #f59e0b",
                color: "#92400e",
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              ⚠️ Live PubMed 模式 N{'>'}500 篇易触发 NCBI 429 限流，建议先用 snapshot 试跑
            </div>
          )}
        </div>

        <div style={{ display: "flex", justifyContent: "flex-end", gap: 10 }}>
          <button
            data-testid="btn-cancel"
            onClick={onClose}
            style={{
              padding: "10px 20px",
              borderRadius: 8,
              border: "1px solid #d1d5db",
              background: "#ffffff",
              color: "#374151",
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            取消
          </button>
          <button
            data-testid="btn-confirm"
            disabled={!valid}
            onClick={() => {
              if (!valid || preset === null) return;
              onConfirm({
                preset,
                mode,
                max_records: maxRecordsNum,
              });
            }}
            style={{
              padding: "10px 20px",
              borderRadius: 8,
              border: "none",
              background: valid ? "#2563eb" : "#9ca3af",
              color: "#ffffff",
              fontSize: 14,
              fontWeight: 700,
              cursor: valid ? "pointer" : "not-allowed",
            }}
          >
            启动 Run ✅
          </button>
        </div>
      </div>
    </div>
  );
}
