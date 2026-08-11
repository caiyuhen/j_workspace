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

  it("creates a search run via POST /search-runs with snake_case body and maps camelCase response", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 201,
      json: async () => ({
        id: 42,
        project_id: 7,
        search_query_version_id: 3,
        selected_sources: ["pubmed", "cnki"],
        status: "pending",
        created_at: "2026-08-11T09:00:00Z",
        started_at: null,
        finished_at: null,
        total_hits_raw: 0,
        total_after_dedupe: 0,
        prisma: {
          identification: 0,
          screening: 0,
          eligibility: 0,
          included: 0,
          by_source: [
            {
              source_key: "pubmed",
              source_label: "PubMed",
              records_retrieved: 0,
              records_imported: 0,
            },
          ],
        },
        eta_seconds: null,
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.createSearchRun(7, {
      searchQueryVersionId: 3,
      querySnapshot: { p: "T2DM" },
      sources: ["pubmed", "cnki"],
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          search_query_version_id: 3,
          query_snapshot: { p: "T2DM" },
          sources: ["pubmed", "cnki"],
        }),
      },
    );
    expect(result.id).toBe(42);
    expect(result.projectId).toBe(7);
    expect(result.searchQueryVersionId).toBe(3);
    expect(result.selectedSources).toEqual(["pubmed", "cnki"]);
    expect(result.totalHitsRaw).toBe(0);
    expect(result.prisma.identification).toBe(0);
    expect(result.prisma.bySource[0].sourceKey).toBe("pubmed");
    expect(result.prisma.bySource[0].recordsRetrieved).toBe(0);
  });

  it("lists search runs with page and pageSize query params", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        items: [
          {
            id: 1,
            project_id: 7,
            search_query_version_id: null,
            selected_sources: ["pubmed"],
            status: "completed",
            created_at: "2026-08-11T08:00:00Z",
            started_at: "2026-08-11T08:00:05Z",
            finished_at: "2026-08-11T08:01:00Z",
            total_hits_raw: 120,
            total_after_dedupe: 100,
            prisma: {
              identification: 120,
              screening: 100,
              eligibility: 80,
              included: 50,
              by_source: [],
            },
            eta_seconds: null,
          },
        ],
        total: 15,
        page: 2,
        page_size: 5,
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.listSearchRuns(7, { page: 2, pageSize: 5 });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs?page=2&page_size=5",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(result.items).toHaveLength(1);
    expect(result.items[0].totalAfterDedupe).toBe(100);
    expect(result.total).toBe(15);
    expect(result.page).toBe(2);
    expect(result.pageSize).toBe(5);
  });

  it("gets a search run detail with run and sources mapping", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        run: {
          id: 42,
          project_id: 7,
          search_query_version_id: null,
          selected_sources: ["pubmed", "cnki"],
          status: "running",
          created_at: "2026-08-11T09:00:00Z",
          started_at: "2026-08-11T09:00:05Z",
          finished_at: null,
          total_hits_raw: 50,
          total_after_dedupe: 40,
          prisma: {
            identification: 50,
            screening: 40,
            eligibility: 0,
            included: 0,
            by_source: [],
          },
          eta_seconds: 12.5,
        },
        sources: [
          {
            id: 1,
            search_run_id: 42,
            source_key: "pubmed",
            source_label: "PubMed",
            status: "completed",
            hits_on_source: 30,
            records_retrieved: 30,
            records_imported: 25,
            started_at: "2026-08-11T09:00:05Z",
            finished_at: "2026-08-11T09:00:20Z",
            error_message: null,
          },
          {
            id: 2,
            search_run_id: 42,
            source_key: "cnki",
            source_label: "CNKI",
            status: "failed",
            hits_on_source: null,
            records_retrieved: 0,
            records_imported: 0,
            started_at: "2026-08-11T09:00:05Z",
            finished_at: "2026-08-11T09:00:07Z",
            error_message: "timeout",
          },
        ],
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.getSearchRun(7, 42);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs/42",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(result.run.status).toBe("running");
    expect(result.run.etaSeconds).toBe(12.5);
    expect(result.sources).toHaveLength(2);
    expect(result.sources[0].searchRunId).toBe(42);
    expect(result.sources[0].sourceKey).toBe("pubmed");
    expect(result.sources[0].hitsOnSource).toBe(30);
    expect(result.sources[0].recordsImported).toBe(25);
    expect(result.sources[1].status).toBe("failed");
    expect(result.sources[1].errorMessage).toBe("timeout");
  });

  it("cancels a search run via POST cancel endpoint", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({ status: "cancelled" }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.cancelSearchRun(7, 42);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs/42/cancel",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      },
    );
    expect(result.status).toBe("cancelled");
  });

  it("retries a search run via POST retry endpoint and maps restartedSources", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({ restarted_sources: 2 }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.retrySearchRun(7, 42);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs/42/retry",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      },
    );
    expect(result.restartedSources).toBe(2);
  });

  it("returns a CSV URL string (without calling fetch) via getSearchRunCsvUrl", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const url = client.getSearchRunCsvUrl(7, 42);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(url).toBe(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs/42/export.csv",
    );
  });

  it("polls a search run status and maps snake_case to camelCase", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        status: "running",
        finished_sources: 1,
        total_sources: 3,
        eta_seconds: 45.2,
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.pollSearchRunStatus(7, 42);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs/42/status",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(result.status).toBe("running");
    expect(result.finishedSources).toBe(1);
    expect(result.totalSources).toBe(3);
    expect(result.etaSeconds).toBe(45.2);
  });

  it("recomputes BM25 for a search run via POST recompute-bm25", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({ queued: true }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.recomputeBm25(7, 42);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs/42/recompute-bm25",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      },
    );
    expect(result.queued).toBe(true);
  });

  it("fetches extended literature library with searchRunId, sort, and minScore QS params", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => libraryResponse,
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    await client.getLiteratureLibraryExt(7, {
      searchRunId: 42,
      sort: "relevance",
      minScore: 0.75,
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/literature?search_run_id=42&sort=relevance&min_score=0.75",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
  });

  it("batch extracts PICO via POST with snake_case body and maps response", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        processed: 8,
        already_had: 2,
        failed: 1,
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.batchExtractPico(7, {
      recordIds: [101, 102, 103],
      method: "rule_baseline",
    });

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/literature/records/pico:batch-extract",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          record_ids: [101, 102, 103],
          method: "rule_baseline",
        }),
      },
    );
    expect(result.processed).toBe(8);
    expect(result.alreadyHad).toBe(2);
    expect(result.failed).toBe(1);
  });

  it("gets a single record PICO via GET with optional method QS and maps fields", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        record_id: 101,
        population: "成人T2DM患者",
        intervention: "SGLT2抑制剂",
        comparison: "安慰剂",
        outcome: "3P-MACE",
        study_type: "rct",
        extraction_method: "rule_baseline",
        confidence: 0.82,
        extracted_at: "2026-08-11T10:00:00Z",
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.getRecordPico(7, 101, "llm");

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/literature/records/101/pico?method=llm",
      expect.objectContaining({ headers: expect.any(Object) }),
    );
    expect(result.recordId).toBe(101);
    expect(result.population).toBe("成人T2DM患者");
    expect(result.intervention).toBe("SGLT2抑制剂");
    expect(result.comparison).toBe("安慰剂");
    expect(result.outcome).toBe("3P-MACE");
    expect(result.studyType).toBe("rct");
    expect(result.extractionMethod).toBe("rule_baseline");
    expect(result.confidence).toBe(0.82);
    expect(result.extractedAt).toBe("2026-08-11T10:00:00Z");
  });

  it("autofills PICO query draft from a search run via POST and maps supportingRecordIds", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      json: async () => ({
        p: "成人2型糖尿病合并慢性肾病",
        i: "SGLT2抑制剂联合二甲双胍",
        c: "二甲双胍单药",
        o: "肾脏复合终点及心血管事件发生率",
        supporting_record_ids: [101, 102, 105, 110],
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient("http://localhost:8000");
    const result = await client.autofillPicoFromRun(7, 42);

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/workspace/projects/7/stages/search/search-runs/42/pico:autofill-query",
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
      },
    );
    expect(result.p).toBe("成人2型糖尿病合并慢性肾病");
    expect(result.i).toBe("SGLT2抑制剂联合二甲双胍");
    expect(result.c).toBe("二甲双胍单药");
    expect(result.o).toBe("肾脏复合终点及心血管事件发生率");
    expect(result.supportingRecordIds).toEqual([101, 102, 105, 110]);
  });

  it("sends the bearer token when calling createSearchRun", async () => {
    const fetchMock = vi.fn(async () => ({
      ok: true,
      status: 201,
      json: async () => ({
        id: 42,
        project_id: 7,
        search_query_version_id: null,
        selected_sources: ["pubmed"],
        status: "pending",
        created_at: "2026-08-11T09:00:00Z",
        started_at: null,
        finished_at: null,
        total_hits_raw: 0,
        total_after_dedupe: 0,
        prisma: {
          identification: 0,
          screening: 0,
          eligibility: 0,
          included: 0,
          by_source: [],
        },
        eta_seconds: null,
      }),
    }));
    vi.stubGlobal("fetch", fetchMock);

    const client = createClient(
      "http://localhost:8000",
      createMemorySessionStore("meda_token"),
    );
    await client.createSearchRun(7, { sources: ["pubmed"] });

    expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining("/search-runs"),
      expect.objectContaining({
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer meda_token",
        },
      }),
    );
  });
});
