import type { StageEntryCardSummary, StageEntrySummary, WorkspaceItemSummary } from "@meda/shared-sdk";

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

const buttonStyle = {
  width: "100%",
  border: "1px solid #d0d7e2",
  background: "#ffffff",
  borderRadius: "14px",
  padding: "12px 14px",
  textAlign: "left" as const,
  cursor: "pointer",
};

function StageButton({
  title,
  subtitle,
  onClick,
}: {
  title: string;
  subtitle: string;
  onClick: () => void;
}) {
  return (
    <button aria-label={title} style={buttonStyle} onClick={onClick}>
      <div style={{ fontWeight: 600 }}>{title}</div>
      <div style={{ marginTop: "4px", color: "#4b5563", fontSize: "14px" }}>
        {subtitle}
      </div>
    </button>
  );
}

function cardSubtitle(card: StageEntryCardSummary) {
  return `${card.description} · ${card.status}`;
}

function itemSubtitle(item: WorkspaceItemSummary) {
  return item.subtitle;
}

export function StageEntryScreen({
  stageEntry,
  onOpenPrimaryAction,
  onOpenTaskPage,
  onOpenArtifactPage,
  onOpenAssistantAction,
  onOpenEntryCard,
}: {
  stageEntry: StageEntrySummary;
  onOpenPrimaryAction: () => void;
  onOpenTaskPage: () => void;
  onOpenArtifactPage: () => void;
  onOpenAssistantAction: () => void;
  onOpenEntryCard: (entryKey: string) => void;
}) {
  return (
    <>
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>{stageEntry.project.name}</div>
          <h2 style={{ margin: "8px 0 12px", fontSize: "30px" }}>
            {stageEntry.stage_label}阶段
          </h2>
          <p style={{ margin: "0 0 8px" }}>当前状态：{stageEntry.stage_status}</p>
          <p style={{ margin: 0 }}>{stageEntry.stage_goal}</p>
          <button
            style={{
              marginTop: "16px",
              border: "none",
              borderRadius: "999px",
              background: "#111827",
              color: "#f9fafb",
              padding: "10px 16px",
              cursor: "pointer",
              fontWeight: 600,
            }}
            onClick={onOpenPrimaryAction}
          >
            {stageEntry.primary_action.label}
          </button>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>子入口导航</h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
              gap: "12px",
            }}
          >
            {stageEntry.entry_cards.map((card) => (
              <StageButton
                key={card.key}
                title={card.title}
                subtitle={cardSubtitle(card)}
                onClick={() => onOpenEntryCard(card.key)}
              />
            ))}
          </div>
        </section>

        <section
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: "20px",
          }}
        >
          <div style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>最近任务</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {stageEntry.recent_tasks.map((task) => (
                <StageButton
                  key={task.title}
                  title={task.title}
                  subtitle={itemSubtitle(task)}
                  onClick={onOpenTaskPage}
                />
              ))}
            </div>
          </div>

          <div style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>最近产物</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {stageEntry.recent_artifacts.map((artifact) => (
                <StageButton
                  key={artifact.title}
                  title={artifact.title}
                  subtitle={itemSubtitle(artifact)}
                  onClick={onOpenArtifactPage}
                />
              ))}
            </div>
          </div>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>阶段助手 + 下一步建议</h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            {stageEntry.assistant_suggestions.map((item) => (
              <StageButton
                key={item.title}
                title={item.title}
                subtitle={itemSubtitle(item)}
                onClick={onOpenAssistantAction}
              />
            ))}
          </div>
        </section>

        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>阶段提示</h2>
          <ul style={{ margin: 0, paddingLeft: "20px", color: "#374151" }}>
            {stageEntry.guidance_notes.map((note) => (
              <li key={note.title} style={{ marginBottom: "10px" }}>
                <strong>{note.title}</strong>：{note.detail}
              </li>
            ))}
          </ul>
        </section>
      </aside>
    </>
  );
}
