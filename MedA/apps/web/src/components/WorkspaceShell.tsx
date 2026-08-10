import { useMemo, useState } from "react";

import type {
  ProjectSummary,
  SaveSearchSourceConfigPayload,
  SearchQueryEditorSummary,
  SearchSourceCatalog,
  SearchSourceConfigSummary,
  SessionContext,
  StageEntrySummary,
  WorkspaceHomeSummary,
} from "@meda/shared-sdk";

import { SearchSourceConfigScreen } from "@meda/shared-ui";

import { SearchQueryBuilderScreen } from "./workspace/SearchQueryBuilderScreen";
import { StageEntryScreen } from "./workspace/StageEntryScreen";
import { SummaryButton } from "./workspace/SummaryButton";

type WorkspaceShellProps = {
  session: SessionContext;
  projects: ProjectSummary[];
  workspaceHome: WorkspaceHomeSummary;
  stageEntry: StageEntrySummary | null;
  searchQueryEditor: SearchQueryEditorSummary | null;
  onOpenStage: (projectId: number, stageKey: string) => Promise<void>;
  onOpenSearchQueryBuilder: (
    projectId: number,
    options?: { queryId?: number; version?: string },
  ) => Promise<void>;
  onSaveSearchQueryDraft: (projectId: number) => Promise<void>;
  onSaveSearchQueryVersion: (projectId: number) => Promise<void>;
  onDeriveSearchQueryDraft: (
    projectId: number,
    queryId: number,
    version: string,
  ) => Promise<void>;
  sourceConfig: SearchSourceConfigSummary | null;
  sourceCatalog: SearchSourceCatalog | null;
  onOpenSourceConfig: (projectId: number) => Promise<void>;
  onSaveSourceConfig: (
    projectId: number,
    payload: SaveSearchSourceConfigPayload,
  ) => Promise<void>;
};

type Screen =
  | "home"
  | "recent-tasks"
  | "recent-artifacts"
  | "assistant"
  | "stage-entry"
  | "query-builder"
  | "source-config"
  | "stage-subentry";

const shellStyle = {
  minHeight: "100vh",
  display: "grid",
  gridTemplateColumns: "220px minmax(0, 1fr) 320px",
  gap: "24px",
  padding: "24px",
  boxSizing: "border-box" as const,
  background: "#f3f4f8",
  color: "#111827",
  fontFamily: "Inter, Arial, sans-serif",
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

const buttonStyle = {
  width: "100%",
  border: "1px solid #d0d7e2",
  background: "#ffffff",
  borderRadius: "14px",
  padding: "12px 14px",
  textAlign: "left" as const,
  cursor: "pointer",
};

function LeftRail({
  projects,
  workspaceHome,
}: {
  projects: ProjectSummary[];
  workspaceHome: WorkspaceHomeSummary;
}) {
  return (
    <section
      style={{ ...panelStyle, display: "flex", flexDirection: "column", gap: "20px" }}
    >
      <div>
        <div
          style={{ fontSize: "12px", color: "#6b7280", letterSpacing: "0.08em" }}
        >
          MEDA WORKSPACE
        </div>
        <h1 style={{ margin: "8px 0 0", fontSize: "24px" }}>工作台</h1>
      </div>

      <nav aria-label="主导航">
        <ul
          style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
        >
          {["工作台", "项目", "数据 / 资料", "Agent", "产物", "管理"].map((item) => (
            <li key={item}>
              <div
                style={{
                  borderRadius: "12px",
                  padding: "10px 12px",
                  background: item === "工作台" ? "#eef2ff" : "#f8fafc",
                  color: item === "工作台" ? "#3730a3" : "#334155",
                  fontWeight: item === "工作台" ? 600 : 500,
                }}
              >
                {item}
              </div>
            </li>
          ))}
        </ul>
      </nav>

      <section>
        <h2 style={{ margin: "0 0 12px", fontSize: "16px" }}>项目上下文</h2>
        <ul
          style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "10px" }}
        >
          {projects.map((project) => (
            <li key={project.id}>
              <div
                style={{
                  border:
                    project.id === workspaceHome.project.id
                      ? "1px solid #c7d2fe"
                      : "1px solid #e5e7eb",
                  background:
                    project.id === workspaceHome.project.id ? "#f8faff" : "#ffffff",
                  borderRadius: "14px",
                  padding: "12px 14px",
                }}
              >
                <div style={{ fontWeight: 600 }}>{project.name}</div>
                <div
                  style={{ marginTop: "4px", color: "#6b7280", fontSize: "13px" }}
                >
                  {project.workspace_key}
                </div>
              </div>
            </li>
          ))}
        </ul>
      </section>
    </section>
  );
}

export function WorkspaceShell({
  session,
  projects,
  workspaceHome,
  stageEntry,
  searchQueryEditor,
  onOpenStage,
  onOpenSearchQueryBuilder,
  onSaveSearchQueryDraft,
  onSaveSearchQueryVersion,
  onDeriveSearchQueryDraft,
  sourceConfig,
  sourceCatalog,
  onOpenSourceConfig,
  onSaveSourceConfig,
}: WorkspaceShellProps) {
  const [screen, setScreen] = useState<Screen>("home");

  const projectWorkspaceKey = useMemo(
    () => workspaceHome.project.workspace_key,
    [workspaceHome.project.workspace_key],
  );

  if (screen === "recent-tasks") {
    return <main style={{ padding: "24px" }}>最近任务承接页</main>;
  }

  if (screen === "recent-artifacts") {
    return <main style={{ padding: "24px" }}>最近产物承接页</main>;
  }

  if (screen === "assistant") {
    return <main style={{ padding: "24px" }}>右侧助手触发面板</main>;
  }

  if (screen === "stage-subentry") {
    return <main style={{ padding: "24px" }}>阶段子入口承接页</main>;
  }

  if (screen === "query-builder" && searchQueryEditor !== null) {
    return (
      <main style={shellStyle}>
        <LeftRail projects={projects} workspaceHome={workspaceHome} />
        <SearchQueryBuilderScreen
          editor={searchQueryEditor}
          onBackToStageEntry={() => setScreen("stage-entry")}
          onSaveDraft={() => onSaveSearchQueryDraft(workspaceHome.project.id)}
          onSaveVersion={() => onSaveSearchQueryVersion(workspaceHome.project.id)}
          onDeriveDraft={() =>
            onDeriveSearchQueryDraft(
              workspaceHome.project.id,
              searchQueryEditor.query_id,
              searchQueryEditor.query_version,
            )
          }
        />
      </main>
    );
  }

  if (screen === "source-config" && sourceConfig !== null) {
    return (
      <main style={shellStyle}>
        <LeftRail projects={projects} workspaceHome={workspaceHome} />
        <SearchSourceConfigScreen
          config={sourceConfig}
          searchFieldOptions={sourceCatalog?.search_field_options ?? []}
          languageOptions={sourceCatalog?.language_options ?? []}
          onBackToStageEntry={() => setScreen("stage-entry")}
          onSave={(payload) =>
            onSaveSourceConfig(workspaceHome.project.id, payload)
          }
        />
      </main>
    );
  }

  if (screen === "stage-entry" && stageEntry !== null) {
    return (
      <main style={shellStyle}>
        <LeftRail projects={projects} workspaceHome={workspaceHome} />
        <StageEntryScreen
          stageEntry={stageEntry}
          onOpenPrimaryAction={async () => {
            await onOpenSearchQueryBuilder(workspaceHome.project.id);
            setScreen("query-builder");
          }}
          onOpenTaskPage={() => setScreen("recent-tasks")}
          onOpenArtifactPage={() => setScreen("recent-artifacts")}
          onOpenAssistantAction={() => setScreen("assistant")}
          onOpenEntryCard={async (entryKey) => {
            if (entryKey === "query-builder") {
              await onOpenSearchQueryBuilder(workspaceHome.project.id);
              setScreen("query-builder");
              return;
            }

            if (entryKey === "sources") {
              await onOpenSourceConfig(workspaceHome.project.id);
              setScreen("source-config");
              return;
            }

            setScreen("stage-subentry");
          }}
        />
      </main>
    );
  }

  return (
    <main style={shellStyle}>
      <LeftRail projects={projects} workspaceHome={workspaceHome} />

      <section style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              gap: "16px",
              alignItems: "flex-start",
            }}
          >
            <div>
              <div style={{ color: "#6b7280", fontSize: "13px" }}>项目工作台首页</div>
              <h2 style={{ margin: "8px 0 12px", fontSize: "30px" }}>
                {workspaceHome.project.name}
              </h2>
              <p style={{ margin: "0 0 8px" }}>当前机构：{session.organization.name}</p>
              <p style={{ margin: 0 }}>当前阶段：{workspaceHome.project.current_stage}</p>
            </div>
            <div style={{ minWidth: "180px", textAlign: "right" }}>
              <div style={{ color: "#6b7280", fontSize: "13px" }}>
                欢迎，{session.user.display_name}
              </div>
              <div style={{ marginTop: "8px", fontSize: "13px", color: "#4b5563" }}>
                {workspaceHome.project.updated_at_label}
              </div>
            </div>
          </div>

          <div
            style={{
              marginTop: "20px",
              padding: "16px",
              borderRadius: "18px",
              background: "linear-gradient(135deg, #111827 0%, #1f2937 100%)",
              color: "#f9fafb",
            }}
          >
            <div style={{ fontSize: "13px", opacity: 0.84 }}>当前项目空间</div>
            <div style={{ marginTop: "6px", fontSize: "15px" }}>
              {projectWorkspaceKey}
            </div>
            <button
              style={{
                marginTop: "16px",
                border: "none",
                borderRadius: "999px",
                background: "#f9fafb",
                color: "#111827",
                padding: "10px 16px",
                cursor: "pointer",
                fontWeight: 600,
              }}
              onClick={() => setScreen("recent-tasks")}
            >
              {workspaceHome.hero_cta.label}
            </button>
          </div>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>研究阶段</h3>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
              gap: "12px",
            }}
          >
            {workspaceHome.stages.map((stage) => (
              <SummaryButton
                key={stage.key}
                item={stage}
                onClick={async () => {
                  await onOpenStage(workspaceHome.project.id, stage.key);
                  setScreen("stage-entry");
                }}
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
              {workspaceHome.recent_tasks.map((task) => (
                <SummaryButton
                  key={task.title}
                  item={task}
                  onClick={() => setScreen("recent-tasks")}
                />
              ))}
            </div>
          </div>

          <div style={panelStyle}>
            <h3 style={{ marginTop: 0 }}>最近产物</h3>
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              {workspaceHome.recent_artifacts.map((artifact) => (
                <SummaryButton
                  key={artifact.title}
                  item={artifact}
                  onClick={() => setScreen("recent-artifacts")}
                />
              ))}
            </div>
          </div>
        </section>

        <section style={panelStyle}>
          <h3 style={{ marginTop: 0 }}>协作动态</h3>
          <ul
            style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {workspaceHome.activity.map((activity) => (
              <li
                key={activity.title}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "14px",
                  padding: "12px 14px",
                }}
              >
                <div style={{ fontWeight: 600 }}>{activity.title}</div>
                <div
                  style={{ marginTop: "4px", color: "#6b7280", fontSize: "14px" }}
                >
                  {activity.subtitle}
                </div>
              </li>
            ))}
          </ul>
        </section>
      </section>

      <aside style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>{workspaceHome.assistant.headline}</h2>
          <p style={{ margin: "0 0 16px", color: "#4b5563" }}>
            基于当前研究阶段与最近产物，继续推进下一步任务。
          </p>
          <button
            style={{
              ...buttonStyle,
              background: "#111827",
              border: "none",
              color: "#f9fafb",
              textAlign: "center",
            }}
            onClick={() => setScreen("assistant")}
          >
            {workspaceHome.assistant.primary_action_label}
          </button>
        </section>

        <section style={panelStyle}>
          <h2 style={{ marginTop: 0 }}>待办与提醒</h2>
          <ul
            style={{ ...listStyle, display: "flex", flexDirection: "column", gap: "12px" }}
          >
            {workspaceHome.todos.map((todo) => (
              <li key={todo.title}>
                <SummaryButton item={todo} onClick={() => setScreen("recent-tasks")} />
              </li>
            ))}
          </ul>
        </section>
      </aside>
    </main>
  );
}
