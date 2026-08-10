import { fireEvent, render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";

import App from "../src/App";

const saveSearchQueryVersion = vi.fn(async () => ({
  project: {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
    current_stage: "检索",
    updated_at_label: "刚刚更新",
  },
  stage_key: "search",
  query_id: 11,
  query_name: "检索式 1",
  query_version: "v1",
  query_dirty: false,
  query_mode: "draft",
  selected_sources: ["PubMed", "Embase"],
  grouped_terms: [],
  expression_blocks: [],
  validation_messages: [],
  preview_summary: {
    status: "available",
    coverage_hint: "主题组覆盖 2 / 5",
    database_scope_summary: "PubMed, Embase",
    estimated_hit_band: "80-150",
    last_generated_from: "draft",
  },
}));

const sourceConfigResponse = {
  project: {
    id: 1,
    name: "糖尿病真实世界研究",
    workspace_key: "demo-hospital/糖尿病真实世界研究",
    current_stage: "检索",
    updated_at_label: "刚刚更新",
  },
  stage_key: "search",
  available_sources: [
    {
      key: "pubmed",
      label: "PubMed",
      description: "美国国立医学图书馆生物医学文献库",
      supports_full_text: false,
      enabled: true,
    },
    {
      key: "cochrane",
      label: "Cochrane Library",
      description: "系统评价与随机对照试验证据库",
      supports_full_text: true,
      enabled: false,
    },
  ],
  enabled_source_keys: ["pubmed"],
  search_fields: ["title", "abstract"],
  year_from: null,
  year_to: null,
  languages: ["en"],
  config_dirty: false,
  impact_summary: {
    enabled_count: 1,
    coverage_hint: "已启用 1 个数据库：PubMed",
    query_impact_hint: "当前检索式的预览将基于这 1 个库重新计算",
  },
  validation_messages: [],
};

const getSearchSourceConfig = vi.fn(async () => sourceConfigResponse);

const getSourceCatalog = vi.fn(async () => ({
  available_sources: sourceConfigResponse.available_sources.map(
    ({ enabled, ...item }) => item,
  ),
  search_field_options: [
    { key: "title", label: "标题" },
    { key: "abstract", label: "摘要" },
    { key: "mesh", label: "主题词" },
  ],
  language_options: [
    { key: "en", label: "英文" },
    { key: "zh", label: "中文" },
  ],
}));

const saveSearchSourceConfig = vi.fn(async () => ({
  ...sourceConfigResponse,
  enabled_source_keys: ["pubmed", "cochrane"],
  impact_summary: {
    enabled_count: 2,
    coverage_hint: "已启用 2 个数据库：PubMed, Cochrane Library",
    query_impact_hint: "当前检索式的预览将基于这 2 个库重新计算",
  },
}));

vi.mock("@meda/shared-sdk", () => ({
  createMemorySessionStore: () => ({ getToken: () => "meda_token" }),
  createClient: () => ({
    getMe: async () => ({
      token: "meda_token",
      user: { user_id: "u-001", display_name: "Dr. Chen" },
      organization: { slug: "demo-hospital", name: "Demo Hospital" },
      role: "researcher",
      client_type: "desktop",
    }),
    listProjects: async () => [
      {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
      },
    ],
    getWorkspaceHome: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "方案设计",
        updated_at_label: "刚刚更新",
      },
      hero_cta: { label: "继续上次研究", target: "/workspace/tasks/recent" },
      stages: [
        {
          key: "search",
          label: "检索",
          status: "done",
          task_count: 1,
          artifact_count: 1,
          target: "/workspace/stages/search",
        },
      ],
      recent_tasks: [
        {
          title: "完善纳排标准草案",
          subtitle: "继续完善当前任务",
          target: "/workspace/tasks/recent",
        },
      ],
      recent_artifacts: [
        {
          title: "方案初稿 v0.3",
          subtitle: "最近修改于 5 分钟前",
          target: "/workspace/artifacts/recent",
        },
      ],
      activity: [
        {
          title: "新增方案初稿版本",
          subtitle: "产物链路已更新",
          target: "/workspace/activity",
        },
      ],
      assistant: {
        headline: "MedA 助手建议",
        primary_action_label: "生成下一步建议",
        primary_action_target: "/workspace/assistant",
      },
      todos: [
        {
          title: "确认研究终点定义",
          subtitle: "今日到期",
          target: "/workspace/tasks/recent",
        },
      ],
    }),
    getStageEntry: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      stage_label: "检索",
      stage_status: "done",
      stage_goal: "完成检索式与来源配置",
      primary_action: {
        label: "进入检索式管理",
        target: "/workspace/stage/search/query-builder",
      },
      entry_cards: [
        {
          key: "query-builder",
          title: "检索式管理",
          description: "维护主题词、自由词和组合策略",
          status: "ready",
          target: "/workspace/stage/search/query-builder",
        },
        {
          key: "sources",
          title: "数据库来源",
          description: "配置检索覆盖的数据库范围",
          status: "ready",
          target: "/workspace/projects/1/stages/search/sources",
        },
      ],
      recent_tasks: [
        {
          title: "补充文献检索式",
          subtitle: "进入该阶段任务承接页",
          target: "/workspace/stage/search/tasks",
        },
      ],
      recent_artifacts: [
        {
          title: "文献检索式 v0.2",
          subtitle: "进入该阶段产物承接页",
          target: "/workspace/stage/search/artifacts",
        },
      ],
      assistant_suggestions: [
        {
          title: "补全数据库来源",
          subtitle: "优先确认核心医学数据库清单",
          target: "/workspace/stage/search/sources",
        },
      ],
      guidance_notes: [
        { title: "输入要求", detail: "需要主题词、自由词与数据库范围。" },
      ],
    }),
    getSearchQueryEditor: async () => ({
      project: {
        id: 1,
        name: "糖尿病真实世界研究",
        workspace_key: "demo-hospital/糖尿病真实世界研究",
        current_stage: "检索",
        updated_at_label: "刚刚更新",
      },
      stage_key: "search",
      query_id: 11,
      query_name: "检索式 1",
      query_version: "draft",
      query_dirty: false,
      query_mode: "draft",
      selected_sources: ["PubMed", "Embase"],
      grouped_terms: [],
      expression_blocks: [],
      validation_messages: [],
      preview_summary: {
        status: "available",
        coverage_hint: "主题组覆盖 2 / 5",
        database_scope_summary: "PubMed, Embase",
        estimated_hit_band: "80-150",
        last_generated_from: "draft",
      },
    }),
    saveSearchQueryDraft: vi.fn(),
    saveSearchQueryVersion,
    deriveSearchQueryDraft: vi.fn(),
    getSearchSourceConfig,
    getSourceCatalog,
    saveSearchSourceConfig,
  }),
}));

test("desktop workspace opens the stage-entry hub from a stage card", async () => {
  render(<App />);

  expect(await screen.findByText("MedA Desktop Workspace")).toBeInTheDocument();
  expect(screen.getByText("当前阶段：方案设计")).toBeInTheDocument();
  expect(screen.getByText("研究阶段")).toBeInTheDocument();
  expect(screen.getByText("MedA 助手建议")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "检索" }));

  expect(await screen.findByText("检索阶段")).toBeInTheDocument();
  expect(screen.getByText("完成检索式与来源配置")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "进入检索式管理" })).toBeInTheDocument();
  expect(screen.getByText("补全数据库来源")).toBeInTheDocument();
});

test("desktop workspace opens query builder and creates a version", async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "进入检索式管理" }));

  expect(
    await screen.findByRole("heading", { name: "检索式管理" }),
  ).toBeInTheDocument();
  expect(screen.getByText("PubMed, Embase")).toBeInTheDocument();

  fireEvent.click(screen.getByRole("button", { name: "另存为新版本" }));

  expect(saveSearchQueryVersion).toHaveBeenCalled();
  expect(await screen.findByText("当前版本：v1")).toBeInTheDocument();
});

test("desktop workspace opens source config and saves an extra database", async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "数据库来源" }));

  expect(getSearchSourceConfig).toHaveBeenCalledWith(1);
  expect(
    await screen.findByRole("heading", { name: "数据库来源" }),
  ).toBeInTheDocument();
  expect(screen.getByText("已启用 1 个数据库：PubMed")).toBeInTheDocument();

  fireEvent.click(screen.getByLabelText("启用 Cochrane Library"));
  fireEvent.click(screen.getByRole("button", { name: "保存配置" }));

  expect(saveSearchSourceConfig).toHaveBeenCalledWith(1, {
    enabled_source_keys: ["pubmed", "cochrane"],
    search_fields: ["title", "abstract"],
    year_from: null,
    year_to: null,
    languages: ["en"],
  });
  expect(
    await screen.findByText("已启用 2 个数据库：PubMed, Cochrane Library"),
  ).toBeInTheDocument();
});
