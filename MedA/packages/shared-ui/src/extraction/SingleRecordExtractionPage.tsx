import React, { useState, useEffect, useRef, useMemo } from "react";
import type {
  ExtractionTemplateField as T7Field,
} from "@meda/shared-sdk";

export interface SingleRecordCurrent {
  record_id: number | string;
  title: string;
  authors: string;
}

export interface SingleRecordExtractionPageProps {
  currentRecord: SingleRecordCurrent;
  templateFields: T7Field[];
  cellsByFieldKey: Record<string, unknown>;
  onUpsert: (field: string, value: unknown) => void;
  prevDisabled: boolean;
  nextDisabled: boolean;
  onPrevRecord: () => void;
  onNextRecord: () => void;
}

type FieldKey = string;

export const SingleRecordExtractionPage: React.FC<SingleRecordExtractionPageProps> = ({
  currentRecord,
  templateFields,
  cellsByFieldKey,
  onUpsert,
  prevDisabled,
  nextDisabled,
  onPrevRecord,
  onNextRecord,
}) => {
  const [localValues, setLocalValues] = useState<Record<FieldKey, unknown>>({});
  const dirtyRef = useRef<Set<FieldKey>>(new Set());
  const timersRef = useRef<Map<FieldKey, ReturnType<typeof setTimeout>>>(new Map());

  useEffect(() => {
    return () => {
      for (const t of timersRef.current.values()) {
        clearTimeout(t);
      }
      timersRef.current.clear();
    };
  }, []);

  const allValues = useMemo(() => {
    const merged: Record<FieldKey, unknown> = { ...cellsByFieldKey };
    for (const k of Object.keys(localValues)) {
      if (dirtyRef.current.has(k)) {
        merged[k] = localValues[k];
      }
    }
    return merged;
  }, [cellsByFieldKey, localValues]);

  const isDirty = dirtyRef.current.size > 0;

  const fireUpsertDebounced = (key: FieldKey, value: unknown) => {
    const existingTimer = timersRef.current.get(key);
    if (existingTimer) {
      clearTimeout(existingTimer);
    }
    const t = setTimeout(() => {
      onUpsert(key, value);
      dirtyRef.current.delete(key);
      setLocalValues((prev) => {
        const next = { ...prev };
        delete next[key];
        return next;
      });
    }, 500);
    timersRef.current.set(key, t);
  };

  const handleCellChange = (key: FieldKey, rawValue: string) => {
    const field = templateFields.find((f) => f.key === key);
    let typedVal: unknown = rawValue;
    if (field?.field_type === "number") {
      const trimmed = rawValue.trim();
      if (trimmed === "") typedVal = null;
      else {
        const n = Number(trimmed);
        typedVal = Number.isFinite(n) ? n : rawValue;
      }
    } else if (field?.field_type === "boolean") {
      typedVal = rawValue === "true" || rawValue === "1";
    }

    dirtyRef.current.add(key);
    setLocalValues((prev) => ({ ...prev, [key]: typedVal }));
    fireUpsertDebounced(key, typedVal);
  };

  const renderCellInput = (f: T7Field) => {
    const key = f.key;
    const val = allValues[key];
    const displayVal = val === null || val === undefined ? "" : String(val);

    if (f.field_type === "boolean") {
      return (
        <select
          data-testid={`cell-input-${key}`}
          value={displayVal}
          onChange={(e) => handleCellChange(key, e.target.value)}
          style={{
            padding: "6px 8px",
            border: "1px solid #d1d5db",
            borderRadius: "5px",
            fontSize: "13px",
            width: "100%",
            background: "#fff",
          }}
        >
          <option value="">未填写</option>
          <option value="true">是</option>
          <option value="false">否</option>
        </select>
      );
    }

    if (f.field_type === "select" && (f.options ?? []).length > 0) {
      return (
        <select
          data-testid={`cell-input-${key}`}
          value={displayVal}
          onChange={(e) => handleCellChange(key, e.target.value)}
          style={{
            padding: "6px 8px",
            border: "1px solid #d1d5db",
            borderRadius: "5px",
            fontSize: "13px",
            width: "100%",
            background: "#fff",
          }}
        >
          <option value="">请选择</option>
          {(f.options ?? []).map((opt, i) => (
            <option key={i} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      );
    }

    if (key === "confidence" || f.field_type === "number") {
      return (
        <input
          data-testid={`cell-input-${key}`}
          type="number"
          step={key === "confidence" ? "0.05" : "any"}
          min={key === "confidence" ? 0 : undefined}
          max={key === "confidence" ? 1 : undefined}
          value={displayVal}
          onChange={(e) => handleCellChange(key, e.target.value)}
          style={{
            padding: "6px 8px",
            border: "1px solid #d1d5db",
            borderRadius: "5px",
            fontSize: "13px",
            width: "100%",
            background: "#fff",
          }}
        />
      );
    }

    return (
      <input
        data-testid={`cell-input-${key}`}
        type="text"
        value={displayVal}
        onChange={(e) => handleCellChange(key, e.target.value)}
        style={{
          padding: "6px 8px",
          border: "1px solid #d1d5db",
          borderRadius: "5px",
          fontSize: "13px",
          width: "100%",
          background: "#fff",
        }}
      />
    );
  };

  return (
    <div style={{ fontFamily: "sans-serif", padding: "16px", maxWidth: "1000px", margin: "0 auto" }}>
      <div
        data-testid="page-title-single-record"
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "flex-start",
          gap: "12px",
          marginBottom: "16px",
          flexWrap: "wrap",
        }}
      >
        <div style={{ flex: 1, minWidth: "280px" }}>
          <div style={{ fontSize: "12px", color: "#6b7280", fontWeight: 600, marginBottom: "4px" }}>
            单条记录提取 · ID #{String(currentRecord.record_id)}
          </div>
          <div
            data-testid="record-title-label"
            style={{ fontSize: "17px", fontWeight: 700, color: "#111827", lineHeight: 1.4 }}
          >
            {currentRecord.title}
          </div>
          <div
            data-testid="author-label"
            style={{ fontSize: "13px", color: "#4b5563", marginTop: "6px" }}
          >
            作者：{currentRecord.authors}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span
            data-testid="auto-save-badge"
            style={{
              padding: "4px 10px",
              borderRadius: "12px",
              fontSize: "12px",
              fontWeight: 600,
              background: isDirty ? "#fef3c7" : "#dcfce7",
              color: isDirty ? "#92400e" : "#166534",
            }}
          >
            {isDirty ? "💾 Saving..." : "✅ Saved"}
          </span>
          <button
            data-testid="nav-prev"
            onClick={onPrevRecord}
            disabled={prevDisabled}
            style={{
              padding: "7px 14px",
              background: prevDisabled ? "#f3f4f6" : "#ffffff",
              color: prevDisabled ? "#9ca3af" : "#1f2937",
              border: "1px solid #d1d5db",
              borderRadius: "5px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: prevDisabled ? "not-allowed" : "pointer",
            }}
          >
            ← 上一条
          </button>
          <button
            data-testid="nav-next"
            onClick={onNextRecord}
            disabled={nextDisabled}
            style={{
              padding: "7px 14px",
              background: nextDisabled ? "#f3f4f6" : "#2563eb",
              color: nextDisabled ? "#9ca3af" : "#fff",
              border: "none",
              borderRadius: "5px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: nextDisabled ? "not-allowed" : "pointer",
            }}
          >
            下一条 →
          </button>
        </div>
      </div>

      <div
        style={{
          padding: "14px",
          border: "1px solid #e5e7eb",
          borderRadius: "8px",
          background: "#fff",
        }}
      >
        <div style={{ fontSize: "13px", color: "#374151", fontWeight: 700, marginBottom: "12px" }}>
          字段提取 · 共 {templateFields.length} 个字段
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
          {templateFields.map((f) => (
            <div
              key={f.key}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: "4px",
                padding: "8px",
                border: "1px solid #f3f4f6",
                borderRadius: "6px",
                background: "#fafafa",
              }}
            >
              <label
                style={{
                  fontSize: "12px",
                  fontWeight: 600,
                  color: "#374151",
                  display: "flex",
                  alignItems: "center",
                  gap: "4px",
                }}
              >
                {f.label || f.key}
                {f.required && (
                  <span style={{ color: "#dc2626", fontSize: "11px" }}>*</span>
                )}
              </label>
              {renderCellInput(f)}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
