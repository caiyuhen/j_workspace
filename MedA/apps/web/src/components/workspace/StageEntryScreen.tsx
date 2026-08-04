import type { StageEntrySummary } from "@meda/shared-sdk";

import { SummaryButton } from "./SummaryButton";

type StageEntryScreenProps = {
  stageEntry: StageEntrySummary;
  onOpenPrimaryAction: () => void;
  onOpenTaskPage: () => void;
  onOpenArtifactPage: () => void;
  onOpenAssistantAction: () => void;
  onOpenEntryCard: (entryKey: string) => void;
};

const panelStyle = {
  background: "#ffffff",
  border: "1px solid #d7dce5",
  borderRadius: "20px",
  padding: "20px",
  boxShadow: "0 8px 24px rgba(15, 23, 42, 0.06)",
};

const listStyle = {
  listStyle: "none",
  padding: 0,
  margin: 0,
};

export function StageEntryScreen({
  stageEntry,
  onOpenPrimaryAction,
  onOpenTaskPage,
  onOpenArtifactPage,
  onOpenAssistantAction,
  onOpenEntryCard,
}: StageEntryScreenProps) {
  return (
    <>
      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <div style={{ color: "#6b7280", fontSize: "13px" }}>
            {stageEntry.project.name}
          </div>
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
              <SummaryButton
                key={card.key}
                item={card}
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
                <SummaryButton
                  key={task.title}
                  item={task}
                  onClick={onOpenTaskPage}
                />
              ))}
            </div>
          </div>

          <div style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>最近产物</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {stageEntry.recent_artifacts.map((artifact) => (
                <SummaryButton
                  key={artifact.title}
                  item={artifact}
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
              <SummaryButton
                key={item.title}
                item={item}
                onClick={onOpenAssistantAction}
              />
            ))}
          </div>
        </section>

        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>阶段提示</h2>
          <ul style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }}>
            {stageEntry.guidance_notes.map((note) => (
              <li
                key={note.title}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "14px",
                  padding: "12px 14px",
                }}
              >
                <div style={{ fontWeight: 600 }}>{note.title}</div>
                <div
                  style={{ marginTop: "4px", color: "#6b7280", fontSize: "14px" }}
                >
                  {note.detail}
                </div>
              </li>
            ))}
          </ul>
        </section>
      </aside>
    </>
  );
}
