import type { SearchQueryEditorSummary } from "@meda/shared-sdk";

type SearchQueryBuilderScreenProps = {
  editor: SearchQueryEditorSummary;
  onBackToStageEntry: () => void;
  onSaveDraft: () => void;
  onSaveVersion: () => void;
  onDeriveDraft: () => void;
};

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
  onDeriveDraft,
}: SearchQueryBuilderScreenProps) {
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
          <div style={{ color: "#6b7280", fontSize: "13px" }}>{editor.project.name}</div>
          <div style={{ marginTop: "8px" }}>当前检索式：{editor.query_name}</div>
          <div style={{ marginTop: "4px" }}>当前版本：{editor.query_version}</div>
          <div style={{ marginTop: "4px" }}>模式：{editor.query_mode}</div>
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
            {editor.query_mode === "snapshot" ? (
              <button
                style={{
                  border: "1px solid #d0d7e2",
                  background: "#ffffff",
                  borderRadius: "999px",
                  padding: "10px 16px",
                  cursor: "pointer",
                }}
                onClick={onDeriveDraft}
              >
                派生为草稿
              </button>
            ) : null}
          </div>
        </section>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "280px minmax(0, 1fr)",
            gap: "20px",
          }}
        >
          <section style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>词组与字段区</h3>
            {editor.grouped_terms.map((group) => (
              <div key={group.group_key} style={{ marginBottom: "16px" }}>
                <div style={{ fontWeight: 600 }}>{group.group_label}</div>
                {group.terms.map((term) => (
                  <div
                    key={term.term_id}
                    style={{
                      marginTop: "8px",
                      border: "1px solid #e5e7eb",
                      borderRadius: "12px",
                      padding: "10px 12px",
                    }}
                  >
                    {term.label} · {term.source_type}
                  </div>
                ))}
              </div>
            ))}
          </section>

          <section style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>块式编辑器</h3>
            {editor.expression_blocks.map((block) => (
              <div
                key={block.block_id}
                style={{
                  marginBottom: "10px",
                  border: "1px solid #e5e7eb",
                  borderRadius: "12px",
                  padding: "10px 12px",
                }}
              >
                {block.block_type === "term"
                  ? `TERM · ${block.term_ref ?? ""}`
                  : `${block.block_type} · ${block.operator ?? ""}`}
              </div>
            ))}
            <div style={{ marginTop: "16px", color: "#4b5563" }}>
              {editor.validation_messages.map((message) => message.message).join(" / ")}
            </div>
          </section>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>预览 + 助手</h3>
          <div>{editor.preview_summary.coverage_hint}</div>
          <div style={{ marginTop: "8px" }}>
            {editor.preview_summary.database_scope_summary}
          </div>
          <div style={{ marginTop: "8px" }}>
            预计命中：{editor.preview_summary.estimated_hit_band}
          </div>
          <div style={{ marginTop: "8px", color: "#6b7280", fontSize: "13px" }}>
            来源：{editor.preview_summary.last_generated_from}
          </div>
        </section>
      </aside>
    </>
  );
}
