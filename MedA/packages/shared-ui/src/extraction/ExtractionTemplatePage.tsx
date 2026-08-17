import React from "react";
import type {
  ExtractionTemplate as T7Template,
  ExtractionTemplateField as T7Field,
} from "@meda/shared-sdk";
import {
  ExtractionTemplateFieldsEditor,
  type ExtractionTemplateField as T8Field,
  type ExtractionFieldType as T8FieldType,
  type PicoBinding as T8Pico,
} from "./ExtractionTemplateFieldsEditor";

export interface ExtractionTemplatePageProps {
  template: T7Template | undefined;
  fields: T7Field[];
  onChange: (newFields: T7Field[]) => void;
  onSave: () => void;
  onLock: () => void;
  locked: boolean;
}

function t7ToT8Field(f: T7Field): T8Field {
  const t8Type: T8FieldType = (f.field_type && ["text", "select", "number", "boolean"].includes(f.field_type))
    ? (f.field_type as T8FieldType)
    : "text";
  const t8Pico: T8Pico = f.pico_binding ? (f.pico_binding as T8Pico) : null;
  return {
    key: f.key,
    label: f.label,
    type: t8Type,
    pico_binding: t8Pico,
    required: f.required,
    options: f.options ?? [],
  };
}

function t8ToT7Field(f: T8Field, original: T7Field | undefined): T7Field {
  return {
    key: f.key,
    label: f.label,
    pico_binding: f.pico_binding ?? (original?.pico_binding ?? "Other"),
    required: f.required,
    field_type: original?.field_type ?? f.type,
    options: f.options,
    description: original?.description,
  };
}

export const ExtractionTemplatePage: React.FC<ExtractionTemplatePageProps> = ({
  template,
  fields,
  onChange,
  onSave,
  onLock,
  locked,
}) => {
  const t8Fields: T8Field[] = fields.map((f) => t7ToT8Field(f));

  const handleEditorChange = (newT8: T8Field[]) => {
    const nextT7 = newT8.map((f8, idx) => t8ToT7Field(f8, fields[idx]));
    onChange(nextT7);
  };

  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const nextT7 = fields.map((f, idx) => t8ToT7Field(t7ToT8Field(f), fields[idx]));
    onChange(nextT7);
  };

  const templateDefined = template !== undefined;
  const nameValue = template?.name ?? "";
  const description = template?.description;

  return (
    <div style={{ fontFamily: "sans-serif", padding: "16px", maxWidth: "1100px", margin: "0 auto" }}>
      <div data-testid="page-title-extraction-template" style={{ marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "6px" }}>
          <h2 style={{ margin: 0, fontSize: "20px", color: "#111827" }}>提取模板编辑</h2>
          {locked && (
            <span
              data-testid="template-locked-badge"
              style={{
                padding: "3px 10px",
                background: "#e0e7ff",
                color: "#3730a3",
                borderRadius: "12px",
                fontSize: "12px",
                fontWeight: 600,
              }}
            >
              🔒 已锁定
            </span>
          )}
        </div>
        {description && (
          <div style={{ fontSize: "13px", color: "#6b7280", marginTop: "4px" }}>{description}</div>
        )}
      </div>

      <div
        style={{
          padding: "14px",
          border: "1px solid #e5e7eb",
          borderRadius: "8px",
          background: "#fff",
          marginBottom: "14px",
        }}
      >
        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ display: "flex", flexDirection: "column", gap: "4px", minWidth: "260px" }}>
            <label style={{ fontSize: "12px", color: "#374151", fontWeight: 600 }}>模板名称</label>
            <input
              data-testid="tpl-name-input"
              value={nameValue}
              disabled={locked}
              onChange={handleNameChange}
              placeholder="请输入模板名称"
              style={{
                padding: "6px 10px",
                border: "1px solid #d1d5db",
                borderRadius: "5px",
                fontSize: "13px",
                background: locked ? "#f9fafb" : "#fff",
                color: locked ? "#9ca3af" : "#111827",
              }}
            />
          </div>

          <div style={{ flex: 1 }} />

          <button
            data-testid="btn-save-template"
            onClick={onSave}
            disabled={locked}
            style={{
              padding: "7px 16px",
              background: locked ? "#f3f4f6" : "#16a34a",
              color: locked ? "#9ca3af" : "#fff",
              border: "none",
              borderRadius: "5px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: locked ? "not-allowed" : "pointer",
            }}
          >
            💾 保存模板
          </button>
          <button
            data-testid="btn-lock-template"
            onClick={onLock}
            disabled={locked || !templateDefined}
            style={{
              padding: "7px 16px",
              background: locked || !templateDefined ? "#f3f4f6" : "#2563eb",
              color: locked || !templateDefined ? "#9ca3af" : "#fff",
              border: "none",
              borderRadius: "5px",
              fontSize: "13px",
              fontWeight: 600,
              cursor: locked || !templateDefined ? "not-allowed" : "pointer",
            }}
          >
            🔒 {locked ? "已锁定" : "锁定模板"}
          </button>
        </div>
      </div>

      <ExtractionTemplateFieldsEditor
        fields={t8Fields}
        onChange={handleEditorChange}
        locked={locked}
      />
    </div>
  );
};
