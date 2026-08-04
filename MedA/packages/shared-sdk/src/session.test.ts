import { describe, expect, it, vi } from "vitest";

import { createClient } from "./client";
import { createMemorySessionStore } from "./session";

describe("session store", () => {
  it("persists and clears bearer tokens", () => {
    const store = createMemorySessionStore();

    expect(store.getToken()).toBeNull();

    store.setToken("meda_token");
    expect(store.getToken()).toBe("meda_token");

    store.clearToken();
    expect(store.getToken()).toBeNull();
  });
});

describe("workspace client", () => {
  it("sends the bearer token when fetching workspace home", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 7,
          name: "糖尿病真实世界研究",
          workspace_key: "demo-hospital/糖尿病真实世界研究",
          current_stage: "方案设计",
          updated_at_label: "刚刚更新",
        },
        hero_cta: { label: "继续上次研究", target: "/workspace/tasks/recent" },
        stages: [],
        recent_tasks: [],
        recent_artifacts: [],
        activity: [],
        assistant: {
          headline: "MedA 助手建议",
          primary_action_label: "生成下一步建议",
          primary_action_target: "/workspace/assistant",
        },
        todos: [],
      }),
    }));

    vi.stubGlobal("fetch", fetchMock);

    const client = createClient(
      "http://localhost:8000",
      createMemorySessionStore("meda_token"),
    );

    const data = await client.getWorkspaceHome(7);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/home",
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer meda_token",
        },
      },
    );
    expect(data.project.name).toBe("糖尿病真实世界研究");
  });

  it("fetches stage-entry data with the bearer token", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 7,
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
        ],
        recent_tasks: [],
        recent_artifacts: [],
        assistant_suggestions: [],
        guidance_notes: [
          { title: "输入要求", detail: "需要主题词、自由词与数据库范围。" },
        ],
      }),
    }));

    vi.stubGlobal("fetch", fetchMock);

    const client = createClient(
      "http://localhost:8000",
      createMemorySessionStore("meda_token"),
    );

    const data = await client.getStageEntry(7, "search");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search",
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer meda_token",
        },
      },
    );
    expect(data.stage_label).toBe("检索");
    expect(data.entry_cards[0].title).toBe("检索式管理");
  });

  it("fetches the search query editor with the bearer token", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 7,
          name: "糖尿病真实世界研究",
          workspace_key: "demo-hospital/糖尿病真实世界研究",
          current_stage: "检索",
          updated_at_label: "刚刚更新",
        },
        stage_key: "search",
        query_id: 12,
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
    }));

    vi.stubGlobal("fetch", fetchMock);

    const client = createClient(
      "http://localhost:8000",
      createMemorySessionStore("meda_token"),
    );

    const data = await client.getSearchQueryEditor(7);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/query-builder",
      {
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer meda_token",
        },
      },
    );
    expect(data.query_name).toBe("检索式 1");
    expect(data.preview_summary.status).toBe("available");
  });

  it("posts save draft with the bearer token", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 7,
          name: "糖尿病真实世界研究",
          workspace_key: "demo-hospital/糖尿病真实世界研究",
          current_stage: "检索",
          updated_at_label: "刚刚更新",
        },
        stage_key: "search",
        query_id: 12,
        query_name: "糖尿病检索式",
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
    }));

    vi.stubGlobal("fetch", fetchMock);

    const client = createClient(
      "http://localhost:8000",
      createMemorySessionStore("meda_token"),
    );

    const data = await client.saveSearchQueryDraft(7, {
      query_id: 12,
      query_name: "糖尿病检索式",
      selected_sources: ["PubMed", "Embase"],
      grouped_terms: [],
      expression_blocks: [],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/query-builder/save",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer meda_token",
        },
        body: JSON.stringify({
          query_id: 12,
          query_name: "糖尿病检索式",
          selected_sources: ["PubMed", "Embase"],
          grouped_terms: [],
          expression_blocks: [],
        }),
      },
    );
    expect(data.query_name).toBe("糖尿病检索式");
    expect(data.query_version).toBe("draft");
  });

  it("posts save-as-version with the bearer token", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 7,
          name: "糖尿病真实世界研究",
          workspace_key: "demo-hospital/糖尿病真实世界研究",
          current_stage: "检索",
          updated_at_label: "刚刚更新",
        },
        stage_key: "search",
        query_id: 12,
        query_name: "糖尿病检索式",
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
      }),
    }));

    vi.stubGlobal("fetch", fetchMock);

    const client = createClient(
      "http://localhost:8000",
      createMemorySessionStore("meda_token"),
    );

    const data = await client.saveSearchQueryVersion(7, {
      query_id: 12,
      query_name: "糖尿病检索式",
      selected_sources: ["PubMed", "Embase"],
      grouped_terms: [],
      expression_blocks: [],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/query-builder/save-as-version",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer meda_token",
        },
        body: JSON.stringify({
          query_id: 12,
          query_name: "糖尿病检索式",
          selected_sources: ["PubMed", "Embase"],
          grouped_terms: [],
          expression_blocks: [],
        }),
      },
    );
    expect(data.query_version).toBe("v1");
  });

  it("derives a draft from a saved version with the bearer token", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 7,
          name: "糖尿病真实世界研究",
          workspace_key: "demo-hospital/糖尿病真实世界研究",
          current_stage: "检索",
          updated_at_label: "刚刚更新",
        },
        stage_key: "search",
        query_id: 12,
        query_name: "糖尿病检索式",
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
          last_generated_from: "v1",
        },
      }),
    }));

    vi.stubGlobal("fetch", fetchMock);

    const client = createClient(
      "http://localhost:8000",
      createMemorySessionStore("meda_token"),
    );

    const data = await client.deriveSearchQueryDraft(7, 12, "v1");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/query-builder/derive-draft",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer meda_token",
        },
        body: JSON.stringify({
          query_id: 12,
          version_label: "v1",
        }),
      },
    );
    expect(data.query_mode).toBe("draft");
    expect(data.query_version).toBe("v1");
  });
});
