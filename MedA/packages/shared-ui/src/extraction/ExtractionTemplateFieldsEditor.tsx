import React, { useMemo } from "react";

export type ExtractionFieldType = "text" | "select" | "number" | "boolean";

export type PicoBinding =
  | null
  | "P"
  | "I"
  | "C"
  | "O"
  | "S"
  | "StudyType"
  | "OutcomeMeasure"
  | "Other";

export interface ExtractionTemplateField {
  key: string;
  label: string;
  type: ExtractionFieldType;
  pico_binding: PicoBinding;
  required: boolean;
  options: string[];
}

export interface ExtractionTemplateFieldsEditorProps {
  fields: ExtractionTemplateField[];
  onChange: (newFields: ExtractionTemplateField[]) => void;
  locked?: boolean;
}

const PICO_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "", label: "未绑定" },
  { value: "P", label: "P - 人群" },
  { value: "I", label: "I - 干预" },
  { value: "C", label: "C - 对照" },
  { value: "O", label: "O - 结局" },
  { value: "S", label: "S - 研究设计" },
  { value: "StudyType", label: "StudyType - 研究类型" },
  { value: "OutcomeMeasure", label: "OutcomeMeasure - 结局指标" },
  { value: "Other", label: "Other - 其他" },
];

const TYPE_OPTIONS: Array<{ value: string; label: string }> = [
  { value: "text", label: "文本" },
  { value: "number", label: "数字" },
  { value: "select", label: "下拉选择" },
  { value: "boolean", label: "布尔" },
];

function emptyField(): ExtractionTemplateField {
  return {
    key: "",
    label: "",
    type: "text",
    pico_binding: null,
    required: false,
    options: [],
  };
}

export const ExtractionTemplateFieldsEditor: React.FC<ExtractionTemplateFieldsEditorProps> = ({
  fields,
  onChange,
  locked = false,
}) => {
  const duplicateKeys = useMemo(() => {
    const counts = new Map<string, number>();
    for (const f of fields) {
      if (f.key) counts.set(f.key, (counts.get(f.key) ?? 0) + 1);
    }
    const dup = new Set<string>();
    for (const [k, v] of counts.entries()) {
      if (v > 1) dup.add(k);
    }
    return dup;
  }, [fields]);

  const hasDuplicateKeys = duplicateKeys.size > 0;
  const hasAnyEmptyKey = fields.some(f => !f.key);

  const updateField = (idx: number, patch: Partial<ExtractionTemplateField>) => {
    const next = fields.map((f, i) => (i === idx ? { ...f, ...patch } : f));
    onChange(next);
  };

  const addField = () => {
    onChange([...fields, emptyField()]);
  };

  const removeField = (idx: number) => {
    const next = fields.filter((_, i) => i !== idx);
    onChange(next);
  };

  const addOption = (idx: number) => {
    const next = fields.map((f, i) =>
      i === idx ? { ...f, options: [...f.options, ""] } : f,
    );
    onChange(next);
  };

  const updateOption = (idx: number, jdx: number, val: string) => {
    const next = fields.map((f, i) => {
      if (i !== idx) return f;
      const opts = f.options.map((o, j) => (j === jdx ? val : o));
      return { ...f, options: opts };
    });
    onChange(next);
  };

  const fieldStyle: React.CSSProperties = {
    display: "flex",
    flexWrap: "wrap",
    gap: "8px",
    alignItems: "center",
    padding: "10px",
    border: "1px solid #e5e7eb",
    borderRadius: "6px",
    marginBottom: "8px",
    background: "#fafafa",
  };

  const inputStyle: React.CSSProperties = {
    padding: "4px 8px",
    border: "1px solid #d1d5db",
    borderRadius: "4px",
    fontSize: "13px",
  };

  return (
    <div data-testid="extraction-fields-editor" style={{ padding: "12px" }}>
      <div style={{ marginBottom: "10px", display: "flex", gap: "8px", alignItems: "center" }}>
        <button
          data-testid="btn-add-field"
          onClick={addField}
          disabled={locked}
          style={{
            padding: "6px 12px",
            background: locked ? "#f3f4f6" : "#2563eb",
            color: locked ? "#9ca3af" : "#fff",
            border: "none",
            borderRadius: "4px",
            cursor: locked ? "not-allowed" : "pointer",
          }}
        >
          + 添加字段
        </button>
        <button
          data-testid="btn-save-fields"
          disabled={hasAnyEmptyKey || hasDuplicateKeys || locked}
          style={{
            padding: "6px 12px",
            background:
              hasAnyEmptyKey || hasDuplicateKeys || locked ? "#f3f4f6" : "#16a34a",
            color:
              hasAnyEmptyKey || hasDuplicateKeys || locked ? "#9ca3af" : "#fff",
            border: "none",
            borderRadius: "4px",
            cursor:
              hasAnyEmptyKey || hasDuplicateKeys || locked
                ? "not-allowed"
                : "pointer",
          }}
        >
          保存字段
        </button>
      </div>

      {hasDuplicateKeys && (
        <div
          data-testid="duplicate-key-warning"
          style={{
            padding: "8px 12px",
            background: "#fef2f2",
            color: "#b91c1c",
            border: "1px solid #fecaca",
            borderRadius: "4px",
            marginBottom: "10px",
            fontSize: "13px",
          }}
        >
          ⚠️ 警告：存在重复的字段 key，请修改为唯一值。
        </div>
      )}

      {fields.map((f, i) => (
        <div key={i} style={fieldStyle}>
          <div style={{ width: "36px", fontWeight: 700, color: "#6b7280", fontSize: "12px" }}>
            #{i + 1}
          </div>

          {!f.key && (
            <span
              data-testid={`empty-key-warning-${i}`}
              style={{
                background: "#fef3c7",
                color: "#92400e",
                padding: "2px 6px",
                borderRadius: "3px",
                fontSize: "11px",
                fontWeight: 600,
              }}
            >
              key为空
            </span>
          )}

          <input
            data-testid={`input-field-key-${i}`}
            value={f.key}
            disabled={locked}
            placeholder="key (唯一)"
            onChange={(e) => updateField(i, { key: e.target.value })}
            style={{ ...inputStyle, width: "120px" }}
          />
          <input
            data-testid={`input-field-label-${i}`}
            value={f.label}
            disabled={locked}
            placeholder="显示名称"
            onChange={(e) => updateField(i, { label: e.target.value })}
            style={{ ...inputStyle, width: "160px" }}
          />
          <select
            data-testid={`select-field-type-${i}`}
            value={f.type}
            disabled={locked}
            onChange={(e) =>
              updateField(i, { type: e.target.value as ExtractionFieldType })
            }
            style={{ ...inputStyle, minWidth: "100px" }}
          >
            {TYPE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <select
            data-testid={`select-pico-binding-${i}`}
            value={f.pico_binding ?? ""}
            disabled={locked}
            onChange={(e) =>
              updateField(i, {
                pico_binding: (e.target.value || null) as PicoBinding,
              })
            }
            style={{ ...inputStyle, minWidth: "140px" }}
          >
            {PICO_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <label
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
              fontSize: "12px",
              color: "#374151",
            }}
          >
            <input
              data-testid={`checkbox-required-${i}`}
              type="checkbox"
              checked={f.required}
              disabled={locked}
              onChange={(e) => updateField(i, { required: e.target.checked })}
            />
            必填
          </label>
          <button
            data-testid={`btn-remove-field-${i}`}
            onClick={() => removeField(i)}
            disabled={locked}
            style={{
              padding: "4px 10px",
              background: locked ? "#f3f4f6" : "#dc2626",
              color: locked ? "#9ca3af" : "#fff",
              border: "none",
              borderRadius: "4px",
              cursor: locked ? "not-allowed" : "pointer",
              fontSize: "12px",
            }}
          >
            删除
          </button>

          {f.type === "select" && (
            <div style={{ width: "100%", marginTop: "6px", paddingLeft: "44px" }}>
              <button
                data-testid={`btn-add-option-${i}`}
                onClick={() => addOption(i)}
                disabled={locked}
                style={{
                  padding: "4px 10px",
                  background: locked ? "#f3f4f6" : "#0891b2",
                  color: locked ? "#9ca3af" : "#fff",
                  border: "none",
                  borderRadius: "4px",
                  cursor: locked ? "not-allowed" : "pointer",
                  fontSize: "12px",
                  marginBottom: "6px",
                }}
              >
                + 添加选项
              </button>
              <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
                {f.options.map((opt, j) => (
                  <input
                    key={j}
                    data-testid={`input-option-${i}-${j}`}
                    value={opt}
                    disabled={locked}
                    placeholder={`选项 ${j + 1}`}
                    onChange={(e) => updateOption(i, j, e.target.value)}
                    style={{ ...inputStyle, width: "300px" }}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};
