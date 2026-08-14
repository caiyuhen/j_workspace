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

const literatureResponse = {
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
    {
      id: 12,
      title: "Duplicated paper",
      authors: "Zhang Y",
      journal: "NEJM",
      year: 2023,
      doi: "10.1016/S2213-8587",
      pmid: "",
      source_key: "embase",
      source_label: "Embase",
      dedupe_status: "duplicate",
      duplicate_of_id: 11,
    },
  ],
  stats: {
    total_count: 2,
    unique_count: 1,
    duplicate_count: 1,
    by_source: [
      { source_key: "pubmed", source_label: "PubMed", count: 1 },
      { source_key: "embase", source_label: "Embase", count: 1 },
    ],
  },
  recent_batches: [],
  available_sources: [
    {
      key: "pubmed",
      label: "PubMed",
      description: "美国国立医学图书馆生物医学文献库",
      supports_full_text: false,
    },
    {
      key: "embase",
      label: "Embase",
      description: "爱思唯尔生物医学与药理学文献库",
      supports_full_text: false,
    },
  ],
  last_import_result: null,
};

const getLiteratureLibrary = vi.fn(async () => literatureResponse);

const importLiterature = vi.fn(async () => ({
  ...literatureResponse,
  last_import_result: {
    imported_count: 2,
    duplicate_count: 1,
    skipped_count: 0,
  },
}));

const confirmLiteratureUnique = vi.fn(async () => ({
  ...literatureResponse,
  records: [
    literatureResponse.records[0],
    {
      ...literatureResponse.records[1],
      dedupe_status: "confirmed_unique",
      duplicate_of_id: null,
    },
  ],
  stats: { ...literatureResponse.stats, unique_count: 2, duplicate_count: 0 },
}));

vi.mock("@meda/shared-sdk", () => {
  const DEMO_PRESETS_MOCK = [
    {
      key: "sglt2i_ckd",
      label: "💧 糖尿病肾病 SGLT2i",
      badge: "经典适应症",
      expected_hits_hint: "预计 1.5k+ hits",
      project_name: "MedA-Demo-Diabetes-CKD-2026",
      query_name: "SGLT2i in CKD (PubMed real-data demo)",
      boolean_text:
        "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR canagliflozin[Title/Abstract]) AND (chronic kidney disease[Title/Abstract] OR CKD[Title/Abstract] OR diabetic nephropathies[MeSH Major Topic]) AND randomised controlled trial[pt]",
      selected_sources: ["pubmed"] as const,
      pico: {
        p: "adult with type 2 diabetes mellitus and CKD stage 2-4 or macroalbuminuria",
        i: "SGLT2 inhibitor add-on to RAAS blockade",
        c: "placebo or standard of care without SGLT2i",
        o: "composite renal endpoint (eGFR decline ≥50% / ESRD / renal death) ; change in eGFR slope ; 3P-MACE ; AE of genital mycotic infection / DKA / hypovolemia",
      },
      filters: { study_type: ["rct"] as const },
    },
    {
      key: "sglt2i_hfredef",
      label: "❤️ 达格列净 HFrEF DAPA-HF / DAPA-CKD",
      badge: "标杆研究",
      expected_hits_hint: "含 DAPA-HF、DAPA-CKD 原始 + follow-up",
      project_name: "MedA-Demo-HF-2026",
      query_name: "Dapagliflozin landmark HFrEF/CKD trials",
      boolean_text:
        "(DAPA-HF[Title/Abstract] OR DAPA-CKD[Title/Abstract] OR (dapagliflozin[Title/Abstract] AND (heart failure with reduced ejection fraction[Title/Abstract] OR HFrEF[Title/Abstract] OR chronic kidney disease[Title/Abstract]))) AND randomised controlled trial[pt]",
      selected_sources: ["pubmed"] as const,
      pico: {
        p: "HFrEF LVEF ≤40% with/without T2DM; CKD eGFR 25-75 + uACR >200",
        i: "dapagliflozin 10 mg once daily",
        c: "matching placebo",
        o: "CV death or worsening HF composite; renal composite; change in NT-proBNP / KCCQ",
      },
      filters: { study_type: ["rct"] as const },
    },
    {
      key: "met_cv_presto",
      label: "💊 二甲双胍 CV PRESTO",
      badge: "RCT 重分析",
      expected_hits_hint: "RCT + pooled subgroup",
      project_name: "MedA-Demo-Metformin-CV-2026",
      query_name: "Metformin PRESTO CV outcomes reanalysis",
      boolean_text:
        "(PRESTO[Title/Abstract] OR (metformin[Title/Abstract] AND cardiovascular[Title/Abstract] AND (prediabetes[Title/Abstract] OR insulin resistance[Title/Abstract]))) AND randomized controlled trial[pt]",
      selected_sources: ["pubmed"] as const,
      pico: {
        p: "prediabetes / insulin resistance with CV risk factors but no established ASCVD",
        i: "metformin extended-release +/- lifestyle intervention",
        c: "placebo or lifestyle-only",
        o: "MACE (CV death / MI / stroke) ; change in LDL-C / SBP / Hba1c",
      },
      filters: { study_type: ["rct"] as const },
    },
    {
      key: "glp1_mace_rws",
      label: "📈 GLP-1 RA MACE 真实世界",
      badge: "RCT vs RWS 对照",
      expected_hits_hint: "RCT + RWS 双队列",
      project_name: "MedA-Demo-GLP1-RA-2026",
      query_name: "GLP-1 RA MACE: RCT vs real-world comparison",
      boolean_text:
        "(glucagon-like peptide-1 receptor agonist[Title/Abstract] OR GLP-1 RA[Title/Abstract] OR liraglutide[Title/Abstract] OR semaglutide[Title/Abstract] OR dulaglutide[Title/Abstract] OR tirzepatide[Title/Abstract]) AND (major adverse cardiovascular events[Title/Abstract] OR MACE[Title/Abstract] OR cardiovascular outcomes[Title/Abstract]) AND ((randomized controlled trial[pt]) OR (real-world[Title/Abstract] OR retrospective[Title/Abstract] OR cohort[Title/Abstract]))",
      selected_sources: ["pubmed"] as const,
      pico: {
        p: "T2DM with established ASCVD or high CV risk",
        i: "GLP-1 RA (injectable or oral) as add-on",
        c: "DPP-4 inhibitor / sulfonylurea / basal insulin / placebo",
        o: "3P-MACE (CV death, non-fatal MI, non-fatal stroke) ; all-cause mortality ; severe hypoglycaemia",
      },
      filters: { study_type: ["rct_and_sr"] as const },
    },
    {
      key: "sglt2i_dka_safety",
      label: "⚠️ SGLT2i 酮症酸中毒 Safety",
      badge: "风险点",
      expected_hits_hint: "RCT post-hoc + RWS + case series",
      project_name: "MedA-Demo-SGLT2i-Safety-2026",
      query_name: "SGLT2i DKA euglycemic safety signal",
      boolean_text:
        "(sodium glucose cotransporter 2 inhibitor[Title/Abstract] OR SGLT2i[Title/Abstract] OR empagliflozin[Title/Abstract] OR dapagliflozin[Title/Abstract] OR ertugliflozin[Title/Abstract]) AND (diabetic ketoacidosis[Title/Abstract] OR DKA[Title/Abstract] OR euglycemic ketoacidosis[Title/Abstract] OR ketosis[Title/Abstract])",
      selected_sources: ["pubmed"] as const,
      pico: {
        p: "T2DM or T1DM on SGLT2i around peri-operative / fasting / severe illness periods",
        i: "SGLT2i continued or paused peri-event window",
        c: "same population without SGLT2i exposure",
        o: "event rate of DKA / euglycemic DKA ; median bicarbonate / gap / anion gap at diagnosis",
      },
    },
    {
      key: "met_lifestyle_predm",
      label: "🏃 Metformin + Lifestyle Prediabetes",
      badge: "一级预防",
      expected_hits_hint: "DPP + follow-up + meta-analysis",
      project_name: "MedA-Demo-Prediabetes-Prevention-2026",
      query_name: "Metformin vs lifestyle in prediabetes: prevention of T2DM",
      boolean_text:
        "(diabetes prevention program[Title/Abstract] OR DPP[Title/Abstract] OR prediabetes[Title/Abstract]) AND (metformin[Title/Abstract] AND (lifestyle[Title/Abstract] OR diet AND exercise[Title/Abstract])) AND (progression to type 2 diabetes[Title/Abstract] OR incidence of type 2 diabetes[Title/Abstract])",
      selected_sources: ["pubmed"] as const,
      pico: {
        p: "adult with prediabetes (IFG / IGT / elevated HbA1c 5.7-6.4%) without prior CV event",
        i: "metformin 850 mg BID + intensive lifestyle (≥7% weight loss, 150 min/wk exercise)",
        c: "placebo + standard lifestyle brochure",
        o: "time to T2DM diagnosis (primary) ; regression to normoglycaemia ; change in weight / Hba1c at 3y",
      },
      filters: { pubmed_mindate: "1996/01/01" },
    },
  ];
  const DEMO_PRESET_BY_KEY_MOCK = Object.fromEntries(
    DEMO_PRESETS_MOCK.map((p) => [p.key, p]),
  );
  const build_grouped_terms_from_pico_mock = (pico: {
    p: string;
    i: string;
    c: string;
    o: string;
  }) => {
    const split = (s: string) =>
      s
        .split(/[\s,;，；/]+/)
        .filter(Boolean)
        .map((t, idx) => ({
          term_id: `t-${idx}-${t.slice(0, 6)}`,
          label: t,
          source_type: "user_entry" as const,
          selected: true,
        }));
    return [
      { group_key: "p", group_label: "Population", terms: split(pico.p) },
      { group_key: "i", group_label: "Intervention", terms: split(pico.i) },
      { group_key: "c", group_label: "Comparison", terms: split(pico.c) },
      { group_key: "o", group_label: "Outcome", terms: split(pico.o) },
    ];
  };
  const build_expression_from_boolean_text_mock = (_bt: string) => [
    {
      block_id: "demo-boolean-block-0",
      block_type: "LiteralBoolean" as const,
      operator: null,
      term_ref: null,
      children: [],
      position: 0,
    },
  ];
  const ensureDemoProjectAndQueryMock = vi.fn(async () => ({
    project_id: 42,
    project_created_this_call: true,
    query_id: 7,
    query_version: "v1",
  }));

  return {
    createMemorySessionStore: () => ({ getToken: () => "meda_token" }),
    DEMO_PRESETS: DEMO_PRESETS_MOCK,
    DEMO_PRESET_BY_KEY: DEMO_PRESET_BY_KEY_MOCK,
    build_grouped_terms_from_pico: build_grouped_terms_from_pico_mock,
    build_expression_from_boolean_text: build_expression_from_boolean_text_mock,
    ensureDemoProjectAndQuery: ensureDemoProjectAndQueryMock,
    createClient: () => ({
      getMe: async () => ({
        token: "meda_token",
        user: { user_id: "u-001", display_name: "Dr. Chen" },
        organization: { slug: "demo-hospital", name: "Demo Hospital" },
        role: "researcher",
        client_type: "desktop",
      }),
      devLogin: vi.fn(async () => ({
        token: "meda_token",
        user: { user_id: "u-001", display_name: "Dr. Chen" },
        organization: { slug: "demo-hospital", name: "Demo Hospital" },
        role: "org_admin",
        client_type: "desktop",
      })),
      createProject: vi.fn(
        async (payload: { name: string; organization_slug: string }) => ({
          id: 99,
          name: payload.name,
          workspace_key: payload.organization_slug + "/" + payload.name,
        }),
      ),
      getSearchRunCsvUrl: (
        _: unknown,
        pid: number | string,
        rid: number | string,
      ) => `/api/projects/${pid}/search-runs/${rid}/csv`,
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
          {
            key: "literature",
            title: "文献条目库",
            description: "导入与去重项目文献集合",
            status: "ready",
            target: "/workspace/projects/1/stages/search/literature",
          },
          {
            key: "search-runs",
            title: "检索运行记录",
            description: "查看检索任务运行进度与结果",
            status: "ready",
            target: "/workspace/projects/1/stages/search/runs",
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
      getLiteratureLibrary,
      importLiterature,
      confirmLiteratureUnique,
      listSearchRuns: vi.fn(async () => ({
        project: {
          id: 1,
          name: "糖尿病真实世界研究",
        },
        runs: [],
        items: [],
        stage_key: "search",
        page: 1,
        page_size: 20,
        pageSize: 20,
        total: 0,
      })),
      createSearchRun: vi.fn(async () => ({
        id: 1,
        project_id: 1,
        projectId: 1,
        status: "pending",
        created_at: "2026-08-11T10:00:00Z",
        createdAt: "2026-08-11T10:00:00Z",
        progress_percent: null,
        sources: [],
        prisma: {
          identification: 0,
          screening: 0,
          eligibility: 0,
          included: 0,
          by_source: [],
        },
      })),
      getSearchRunDetail: vi.fn(async () => ({
        id: 1,
        status: "running",
        project: { id: 1, name: "糖尿病真实世界研究" },
        created_at_label: "刚刚",
        sources: [],
      })),
      getSearchRun: vi.fn(async () => ({
        id: 1,
        status: "running",
        project: { id: 1, name: "糖尿病真实世界研究" },
        created_at_label: "刚刚",
        sources: [],
      })),
      retrySearchRun: vi.fn(async () => ({ ok: true })),
      cancelSearchRun: vi.fn(async () => ({ ok: true })),
    }),
  };
});

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
  fireEvent.click(await screen.findByRole("button", { name: "检索式编辑器" }));

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

test("desktop workspace imports literature and confirms a duplicate", async () => {
  render(<App />);

  fireEvent.click(await screen.findByRole("button", { name: "检索" }));
  fireEvent.click(await screen.findByRole("button", { name: "文献条目库" }));

  expect(getLiteratureLibrary).toHaveBeenCalledWith(1);
  expect(
    await screen.findByRole("heading", { name: "文献条目库" }),
  ).toBeInTheDocument();
  expect(screen.getByText("共 2 条 · 唯一 1 条 · 重复 1 条")).toBeInTheDocument();

  fireEvent.change(screen.getByLabelText("粘贴文献条目"), {
    target: { value: "title: A pasted paper" },
  });
  fireEvent.click(screen.getByRole("button", { name: "导入" }));

  expect(importLiterature).toHaveBeenCalledWith(1, {
    source_key: "pubmed",
    raw_text: "title: A pasted paper",
  });

  fireEvent.click(await screen.findByRole("button", { name: "标记为独立文献" }));

  expect(confirmLiteratureUnique).toHaveBeenCalledWith(1, 12);
  expect(
    await screen.findByText("共 2 条 · 唯一 2 条 · 重复 0 条"),
  ).toBeInTheDocument();
});
