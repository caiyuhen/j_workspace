import type { SearchQueryEditorSummary } from "@meda/shared-sdk";

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

export function SearchQueryBuilderScreen({
  editor,
  onBackToStageEntry,
  onSaveDraft,
  onSaveVersion,
}: {
  editor: SearchQueryEditorSummary;
  onBackToStageEntry: () => void;
  onSaveDraft: () => void;
  onSaveVersion: () => void;
}) {
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
          <h2 style={{ margin: "16px 0 8px", fontSize: "30px" }}>检索式管理</h2>
          <div>当前检索式：{editor.query_name}</div>
          <div style={{ marginTop: "4px" }}>当前版本：{editor.query_version}</div>
          <div style={{ display: "flex", gap: "12px", marginTop: "16px" }}>
            <button
              style={{
                border: "1px solid #d0d7e2",
                background: "#ffffff",
                borderRadius: "999px",
                padding: "10px 16px",
                cursor: "pointer",
              }}
              onClick={onSaveDraft}
            >
              保存
            </button>
            <button
              style={{
                border: "none",
                background: "#111827",
                color: "#f9fafb",
                borderRadius: "999px",
                padding: "10px 16px",
                cursor: "pointer",
              }}
              onClick={onSaveVersion}
            >
              另存为新版本
            </button>
          </div>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>预览 + 助手</h3>
          <div>{editor.preview_summary.database_scope_summary}</div>
          <div style={{ marginTop: "8px" }}>{editor.preview_summary.coverage_hint}</div>
        </section>
      </aside>
    </>
  );
}
