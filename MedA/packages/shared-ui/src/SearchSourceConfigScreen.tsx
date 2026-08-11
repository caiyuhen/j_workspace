import { useEffect, useState } from "react";

import type {
  CatalogOption,
  SaveSearchSourceConfigPayload,
  SearchSourceConfigSummary,
} from "@meda/shared-sdk";

export type SearchSourceConfigScreenProps = {
  config: SearchSourceConfigSummary;
  searchFieldOptions: CatalogOption[];
  languageOptions: CatalogOption[];
  onBackToStageEntry: () => void;
  onSave: (payload: SaveSearchSourceConfigPayload) => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

const optionRowStyle = {
  display: "flex",
  gap: "12px",
  alignItems: "flex-start",
  marginBottom: "12px",
  border: "1px solid #e5e7eb",
  borderRadius: "12px",
  padding: "12px 14px",
};

const yearInputStyle = {
  width: "104px",
  border: "1px solid #d0d7e2",
  borderRadius: "10px",
  padding: "8px 10px",
};

export function toggleKey(current: string[], ordered: string[], key: string): string[] {
  if (!ordered.includes(key)) {
    return current.filter((item) => ordered.includes(item));
  }
  if (current.includes(key)) {
    return current.filter((item) => item !== key);
  }

  return ordered.filter((item) => current.includes(item) || item === key);
}

const YEAR_RE = /^\d{4}$/;
const MIN_YEAR = 1800;
const MAX_YEAR = 2100;

export function parseYear(raw: string): number | null {
  const trimmed = raw.trim();
  if (trimmed === "") {
    return null;
  }
  if (!YEAR_RE.test(trimmed)) {
    return null;
  }

  const parsed = Number.parseInt(trimmed, 10);
  if (Number.isNaN(parsed)) {
    return null;
  }
  if (parsed < MIN_YEAR || parsed > MAX_YEAR) {
    return null;
  }
  return parsed;
}

export function SearchSourceConfigScreen({
  config,
  searchFieldOptions,
  languageOptions,
  onBackToStageEntry,
  onSave,
}: SearchSourceConfigScreenProps) {
  const [enabledKeys, setEnabledKeys] = useState(config.enabled_source_keys);
  const [searchFields, setSearchFields] = useState(config.search_fields);
  const [languages, setLanguages] = useState(config.languages);
  const [yearFrom, setYearFrom] = useState(config.year_from);
  const [yearTo, setYearTo] = useState(config.year_to);

  useEffect(() => {
    setEnabledKeys(config.enabled_source_keys);
    setSearchFields(config.search_fields);
    setLanguages(config.languages);
    setYearFrom(config.year_from);
    setYearTo(config.year_to);
  }, [config]);

  const sourceOrder = config.available_sources.map((item) => item.key);
  const fieldOrder = searchFieldOptions.map((item) => item.key);
  const languageOrder = languageOptions.map((item) => item.key);

  return (
    <>
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <button
            style={{
              border: "1px solid #d0d7e2",
              background: "#ffffff",
              borderRadius: "999px",
              padding: "8px 14px",
              cursor: "pointer",
            }}
            onClick={onBackToStageEntry}
          >
            返回检索阶段入口页
          </button>
          <h2 style={{ margin: "16px 0 8px", fontSize: "30px" }}>数据库来源</h2>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>
            {config.project.name}
          </div>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>来源清单</h3>
          {config.available_sources.map((source) => (
            <label key={source.key} style={optionRowStyle}>
              <input
                type="checkbox"
                aria-label={`启用 ${source.label}`}
                checked={enabledKeys.includes(source.key)}
                onChange={() =>
                  setEnabledKeys((current) =>
                    toggleKey(current, sourceOrder, source.key),
                  )
                }
              />
              <span>
                <span style={{ fontWeight: 600 }}>{source.label}</span>
                <span
                  style={{
                    display: "block",
                    marginTop: "4px",
                    color: "#6b7280",
                    fontSize: "13px",
                  }}
                >
                  {source.description}
                  {source.supports_full_text ? " · 支持全文" : ""}
                </span>
              </span>
            </label>
          ))}
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>检索参数</h3>

          <fieldset style={{ border: "none", padding: 0, margin: "0 0 16px" }}>
            <legend style={{ fontWeight: 600, padding: 0 }}>检索字段范围</legend>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "8px" }}>
              {searchFieldOptions.map((option) => (
                <span key={option.key} style={{ display: "flex", gap: "6px" }}>
                  <input
                    type="checkbox"
                    id={`search-field-${option.key}`}
                    checked={searchFields.includes(option.key)}
                    onChange={() =>
                      setSearchFields((current) =>
                        toggleKey(current, fieldOrder, option.key),
                      )
                    }
                  />
                  <label htmlFor={`search-field-${option.key}`}>
                    {option.label}
                  </label>
                </span>
              ))}
            </div>
          </fieldset>

          <fieldset style={{ border: "none", padding: 0, margin: "0 0 16px" }}>
            <legend style={{ fontWeight: 600, padding: 0 }}>年份区间</legend>
            <div style={{ display: "flex", gap: "12px", alignItems: "center", marginTop: "8px" }}>
              <input
                type="number"
                aria-label="起始年份"
                placeholder="不限"
                style={yearInputStyle}
                value={yearFrom ?? ""}
                onChange={(event) => setYearFrom(parseYear(event.target.value))}
              />
              <span>—</span>
              <input
                type="number"
                aria-label="结束年份"
                placeholder="不限"
                style={yearInputStyle}
                value={yearTo ?? ""}
                onChange={(event) => setYearTo(parseYear(event.target.value))}
              />
            </div>
          </fieldset>

          <fieldset style={{ border: "none", padding: 0, margin: 0 }}>
            <legend style={{ fontWeight: 600, padding: 0 }}>语种限定</legend>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "12px", marginTop: "8px" }}>
              {languageOptions.map((option) => (
                <span key={option.key} style={{ display: "flex", gap: "6px" }}>
                  <input
                    type="checkbox"
                    id={`language-${option.key}`}
                    checked={languages.includes(option.key)}
                    onChange={() =>
                      setLanguages((current) =>
                        toggleKey(current, languageOrder, option.key),
                      )
                    }
                  />
                  <label htmlFor={`language-${option.key}`}>{option.label}</label>
                </span>
              ))}
            </div>
          </fieldset>
        </section>

        <section style={panelStyle}>
          <button
            style={{
              border: "none",
              background: "#111827",
              color: "#f9fafb",
              borderRadius: "999px",
              padding: "10px 16px",
              cursor: "pointer",
            }}
            onClick={() =>
              onSave({
                enabled_source_keys: enabledKeys,
                search_fields: searchFields,
                year_from: yearFrom,
                year_to: yearTo,
                languages,
              })
            }
          >
            保存配置
          </button>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>配置影响</h3>
          <div>{config.impact_summary.coverage_hint}</div>
          <div style={{ marginTop: "8px", color: "#4b5563" }}>
            {config.impact_summary.query_impact_hint}
          </div>
          {config.validation_messages.map((message) => (
            <div
              key={message.code}
              style={{
                marginTop: "12px",
                color: message.level === "error" ? "#b91c1c" : "#6b7280",
              }}
            >
              {message.message}
            </div>
          ))}
        </section>
      </aside>
    </>
  );
}
