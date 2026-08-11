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

  it("fetches the source catalog", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        available_sources: [
          {
            key: "pubmed",
            label: "PubMed",
            description: "美国国立医学图书馆生物医学文献库",
            supports_full_text: false,
          },
        ],
        search_field_options: [{ key: "title", label: "标题" }],
        language_options: [{ key: "en", label: "英文" }],
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const catalog = await client.getSourceCatalog();

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/sources/catalog",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(catalog.available_sources[0].key).toBe("pubmed");
    expect(catalog.search_field_options[0].label).toBe("标题");
  });

  it("fetches the search source config", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 1,
          name: "糖尿病真实世界研究",
          workspace_key: "demo-hospital/糖尿病真实世界研究",
          current_stage: "检索",
          updated_at_label: "刚刚更新",
        },
        stage_key: "search",
        available_sources: [],
        enabled_source_keys: ["pubmed", "embase"],
        search_fields: ["title", "abstract"],
        year_from: null,
        year_to: null,
        languages: ["en"],
        config_dirty: false,
        impact_summary: {
          enabled_count: 2,
          coverage_hint: "已启用 2 个数据库：PubMed, Embase",
          query_impact_hint: "当前检索式的预览将基于这 2 个库重新计算",
        },
        validation_messages: [],
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const config = await client.getSearchSourceConfig(1);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/sources",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(config.enabled_source_keys).toEqual(["pubmed", "embase"]);
    expect(config.impact_summary.enabled_count).toBe(2);
  });

  it("saves the search source config", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        project: {
          id: 1,
          name: "糖尿病真实世界研究",
          workspace_key: "demo-hospital/糖尿病真实世界研究",
          current_stage: "检索",
          updated_at_label: "刚刚更新",
        },
        stage_key: "search",
        available_sources: [],
        enabled_source_keys: ["pubmed", "cochrane"],
        search_fields: ["title"],
        year_from: 2015,
        year_to: 2025,
        languages: ["en"],
        config_dirty: false,
        impact_summary: {
          enabled_count: 2,
          coverage_hint: "已启用 2 个数据库：PubMed, Cochrane Library",
          query_impact_hint: "当前检索式的预览将基于这 2 个库重新计算",
        },
        validation_messages: [],
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const config = await client.saveSearchSourceConfig(1, {
      enabled_source_keys: ["pubmed", "cochrane"],
      search_fields: ["title"],
      year_from: 2015,
      year_to: 2025,
      languages: ["en"],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/sources",
      expect.objectContaining({ method: "PUT" }),
    );
    expect(config.enabled_source_keys).toEqual(["pubmed", "cochrane"]);
    expect(config.year_from).toBe(2015);
  });

  const libraryResponse = {
    project: {
      id: 1,
      name: "糖尿病真实世界研究",
      workspace_key: "demo-hospital/糖尿病真实世界研究",
      current_stage: "检索",
      updated_at_label: "刚刚更新",
    },
    stage_key: "search",
    records: [
      {
        id: 11,
        title: "Metformin and cardiovascular outcomes",
        authors: "Chen L",
        journal: "Lancet",
        year: 2023,
        doi: "10.1016/S2213-8587",
        pmid: "37123456",
        source_key: "pubmed",
        source_label: "PubMed",
        dedupe_status: "unique",
        duplicate_of_id: null,
      },
    ],
    stats: {
      total_count: 1,
      unique_count: 1,
      duplicate_count: 0,
      by_source: [{ source_key: "pubmed", source_label: "PubMed", count: 1 }],
    },
    recent_batches: [],
    available_sources: [
      {
        key: "pubmed",
        label: "PubMed",
        description: "美国国立医学图书馆生物医学文献库",
        supports_full_text: false,
      },
    ],
    last_import_result: null,
  };

  it("fetches the literature library", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => libraryResponse,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const library = await client.getLiteratureLibrary(1);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/literature",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(library.records[0].title).toBe(
      "Metformin and cardiovascular outcomes",
    );
    expect(library.stats.total_count).toBe(1);
  });

  it("imports literature from pasted text", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        ...libraryResponse,
        last_import_result: {
          imported_count: 2,
          duplicate_count: 1,
          skipped_count: 0,
        },
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const library = await client.importLiterature(1, {
      source_key: "pubmed",
      raw_text: "title: A paper",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/literature/import",
      expect.objectContaining({ method: "POST" }),
    );
    expect(library.last_import_result?.imported_count).toBe(2);
    expect(library.last_import_result?.duplicate_count).toBe(1);
  });

  it("creates a literature record manually", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => libraryResponse,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    await client.createLiteratureRecord(1, {
      title: "Hand entered",
      authors: "",
      journal: "",
      year: null,
      doi: "",
      pmid: "",
      abstract: "",
      source_key: "cochrane",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/literature/records",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("confirms a flagged record as unique", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => libraryResponse,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    await client.confirmLiteratureUnique(1, 11);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/1/stages/search/literature/records/11/confirm-unique",
      expect.objectContaining({ method: "POST" }),
    );
  });
});
