import { useEffect, useState } from "react";

import type { SearchSourceConfigSummary } from "@meda/shared-sdk";

type SearchSourceConfigScreenProps = {
  config: SearchSourceConfigSummary;
  onBackToStageEntry: () => void;
  onSave: (payload: {
    enabled_source_keys: string[];
    search_fields: string[];
    year_from: number | null;
    year_to: number | null;
    languages: string[];
  }) => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

export function SearchSourceConfigScreen({
  config,
  onBackToStageEntry,
  onSave,
}: SearchSourceConfigScreenProps) {
  const [enabledKeys, setEnabledKeys] = useState<string[]>(
    config.enabled_source_keys,
  );

  useEffect(() => {
    setEnabledKeys(config.enabled_source_keys);
  }, [config.enabled_source_keys]);

  const toggleSource = (key: string) => {
    setEnabledKeys((current) =>
      current.includes(key)
        ? current.filter((item) => item !== key)
        : config.available_sources
            .map((item) => item.key)
            .filter((item) => current.includes(item) || item === key),
    );
  };

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
            <label
              key={source.key}
              style={{
                display: "flex",
                gap: "12px",
                alignItems: "flex-start",
                marginBottom: "12px",
                border: "1px solid #e5e7eb",
                borderRadius: "12px",
                padding: "12px 14px",
              }}
            >
              <input
                type="checkbox"
                aria-label={`启用 ${source.label}`}
                checked={enabledKeys.includes(source.key)}
                onChange={() => toggleSource(source.key)}
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
          <div>检索字段：{config.search_fields.join(", ")}</div>
          <div style={{ marginTop: "8px" }}>
            年份区间：{config.year_from ?? "不限"} — {config.year_to ?? "不限"}
          </div>
          <div style={{ marginTop: "8px" }}>
            语种：{config.languages.join(", ")}
          </div>
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
                search_fields: config.search_fields,
                year_from: config.year_from,
                year_to: config.year_to,
                languages: config.languages,
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
