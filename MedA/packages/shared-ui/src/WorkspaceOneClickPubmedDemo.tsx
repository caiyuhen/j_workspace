import React, { useState, type PropsWithChildren } from "react";
import {
  DEMO_PRESETS,
  ensureDemoProjectAndQuery,
  type DemoPreset,
  type EnsureDemoResult,
  type MedaClient,
  type SessionContext,
} from "@meda/shared-sdk";

export type WorkspaceOneClickPubmedDemoProps = {
  client: MedaClient;
  session: SessionContext;
  workspaceHomeProjectId?: number;
  onRunCreated: (searchRunId: number, projectId: number) => void;
  onProjectCreatedToast?: (projectName: string) => void;
  onErrorToast?: (msg: string) => void;
};

export function WorkspaceOneClickPubmedDemo(
  props: PropsWithChildren<WorkspaceOneClickPubmedDemoProps>,
) {
  const {
    client,
    session,
    workspaceHomeProjectId,
    onRunCreated,
    onProjectCreatedToast,
    onErrorToast,
  } = props;

  const [pendingKey, setPendingKey] = useState<DemoPreset["key"] | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleClick = async (preset: DemoPreset) => {
    if (pendingKey !== null) return;
    setPendingKey(preset.key);
    setErrorMsg(null);
    try {
      const ensured: EnsureDemoResult = await ensureDemoProjectAndQuery(
        client,
        session,
        preset,
        { workspaceHomeProjectId },
      );
      if (ensured.project_created_this_call && onProjectCreatedToast) {
        onProjectCreatedToast(preset.project_name);
      }
      const created = await props.client.createSearchRun(ensured.project_id, {
        query_id: ensured.query_id,
        query_version: ensured.query_version,
        selected_sources: preset.selected_sources,
        filters: preset.filters ?? {},
        adapter_modes: { pubmed: "prefer_real" } as any,
      } as any);
      onRunCreated(created.id, ensured.project_id);
    } catch (err: any) {
      const msg = `Demo 启动失败：${err?.message ?? String(err)}`;
      setErrorMsg(msg);
      if (onErrorToast) onErrorToast(msg);
    } finally {
      setPendingKey(null);
    }
  };

  const accent = "#6366F1";
  const panelStyle: React.CSSProperties = {
    background:
      "linear-gradient(135deg, rgba(99,102,241,0.12), rgba(34,211,238,0.05))",
    border: `1.5px solid ${accent}`,
    borderRadius: 14,
    padding: "16px 16px 14px",
  };
  const pill = (bg: string, fg: string, txt: string) => (
    <span
      style={{
        display: "inline-block",
        padding: "2px 9px",
        borderRadius: 999,
        background: bg,
        color: fg,
        fontSize: 11,
        fontWeight: 600,
        marginRight: 8,
      }}
    >
      {txt}
    </span>
  );
  return (
    <section
      aria-label="PubMed one-click demo section"
      style={{ marginTop: 20 }}
    >
      <div style={panelStyle}>
        <div
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: 6,
            background: accent,
            color: "white",
            fontSize: 11,
            fontWeight: 700,
            padding: "2px 8px",
            borderRadius: 999,
            marginBottom: 6,
            letterSpacing: 0.5,
          }}
        >
          NEW · 一键真实数据 Demo
        </div>
        <div style={{ fontWeight: 600, fontSize: 15 }}>
          🧪 用 PubMed 真实文献跑通完整检索流水线（仅 PubMed，约 2~6 秒）
        </div>
        <div style={{ fontSize: 12, color: "#94a3b8", marginTop: 4 }}>
          选一个主题 → 自动创建项目/检索式（若不存在）→ 发起 SearchRun →
          自动跳到运行详情页，展示 PRISMA、BM25 文献列表、PICO 批量提取。
        </div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
            marginTop: 12,
          }}
        >
          {DEMO_PRESETS.map((preset) => {
            const disabled = pendingKey !== null && pendingKey !== preset.key;
            const active = pendingKey === preset.key;
            const chipBg = active ? accent : "rgba(255,255,255,0.06)";
            const chipBorder = active ? accent : "rgba(255,255,255,0.08)";
            return (
              <button
                type="button"
                role="button"
                key={preset.key}
                onClick={() => handleClick(preset)}
                aria-label={`${preset.label} preset button`}
                disabled={disabled}
                style={{
                  fontSize: 12,
                  padding: "6px 10px",
                  borderRadius: 999,
                  background: chipBg,
                  border: `1px solid ${chipBorder}`,
                  color: "#cbd5ff",
                  cursor: disabled ? "not-allowed" : "pointer",
                  opacity: disabled ? 0.55 : 1,
                  transition: "all 0.15s ease",
                }}
                onMouseEnter={(e) => {
                  if (!disabled) {
                    (e.currentTarget as HTMLButtonElement).style.background =
                      accent;
                  }
                }}
                onMouseLeave={(e) => {
                  if (!disabled && !active) {
                    (e.currentTarget as HTMLButtonElement).style.background =
                      "rgba(255,255,255,0.06)";
                  }
                }}
              >
                {preset.label}
                <span style={{ opacity: 0.6, marginLeft: 4, fontSize: 10 }}>
                  {preset.expected_hits_hint}
                </span>
              </button>
            );
          })}
        </div>
        <div style={{ marginTop: 10, fontSize: 12 }}>
          {pill("rgba(34,197,94,0.15)", "#86efac", "已连网 prefer_real")}
          {pill(
            "rgba(245,158,11,0.15)",
            "#fcd34d",
            "无网络时自动 fallback 注入 demo 集",
          )}
          {pill(
            "rgba(34,211,238,0.15)",
            "#67e8f9",
            "仅 PubMed 单源 · 不触发机构反爬",
          )}
        </div>
        {errorMsg ? (
          <div
            role="alert"
            style={{
              marginTop: 10,
              padding: "8px 10px",
              borderRadius: 8,
              background: "rgba(239,68,68,0.1)",
              border: "1px solid rgba(239,68,68,0.3)",
              color: "#fecaca",
              fontSize: 12,
            }}
          >
            {errorMsg}
          </div>
        ) : null}
      </div>
    </section>
  );
}
