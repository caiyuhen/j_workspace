import { createClient } from "../client";
import type {
  CreateProjectRequest,
  ProjectSummary,
  SaveSearchQueryDraftPayload,
  SearchExpressionBlock,
  SearchTermGroupSummary,
  SearchTermSummary,
  SessionContext,
} from "../client";
import { DEMO_PRESET_BY_KEY, type DemoPreset, type DemoPresetKey } from "../presets";

export type MedaClient = ReturnType<typeof createClient>;

export type EnsureDemoResult = {
  project_id: number;
  project_created_this_call: boolean;
  query_id: number;
  query_version: string;
};

export type EnsureDemoOptions = {
  workspaceHomeProjectId?: number;
  forceNewProject?: boolean;
};

const SPLIT_RE = /[\s,;，；/]+/;

export function build_grouped_terms_from_pico(pico: DemoPreset["pico"]): SearchTermGroupSummary[] {
  const groups: Array<{ key: "p" | "i" | "c" | "o"; label: string }> = [
    { key: "p", label: "P - Population" },
    { key: "i", label: "I - Intervention" },
    { key: "c", label: "C - Comparator" },
    { key: "o", label: "O - Outcome" },
  ];
  return groups.map(({ key, label }, gi) => {
    const raw = pico[key];
    const chunks = raw
      .split(SPLIT_RE)
      .map((s) => s.trim())
      .filter(Boolean);
    const terms: SearchTermSummary[] = (chunks.length > 0 ? chunks : [pico[key].slice(0, 24)]).map((t, ti) => ({
      term_id: `demo-${key}-${gi}-${ti}`,
      label: t,
      source_type: "user_entry",
      selected: true,
    }));
    return {
      group_key: `demo-group-${key}`,
      group_label: label,
      terms,
    };
  });
}

export function build_expression_from_boolean_text(boolean_text: string): SearchExpressionBlock[] {
  return [
    {
      block_id: "demo-boolean-block-0",
      block_type: "LiteralBoolean",
      operator: null,
      term_ref: null,
      children: [],
      position: 0,
    },
  ];
}

export async function ensureDemoProjectAndQuery(
  client: MedaClient,
  session: SessionContext,
  preset: DemoPreset,
  options: EnsureDemoOptions = {},
): Promise<EnsureDemoResult> {
  let project_id: number | null = null;
  let project_created_this_call = false;

  if (!options.forceNewProject) {
    if (options.workspaceHomeProjectId) {
      project_id = options.workspaceHomeProjectId;
    } else {
      const projects = await client.listProjects();
      const match = projects.find((p: ProjectSummary) => p.name === preset.project_name);
      if (match) project_id = match.id;
      else if (projects.length > 0) project_id = projects[0].id;
    }
  }

  if (project_id == null) {
    const payload: CreateProjectRequest = {
      organization_slug: session.organization.slug,
      owner_user_id: session.user.user_id,
      name: preset.project_name,
      description: "Auto-created by PubMed one-click demo.",
    };
    const created = await client.createProject(payload);
    project_id = created.id;
    project_created_this_call = true;
  }

  const final_project_id = project_id;
  const editor = await client.getSearchQueryEditor(final_project_id);
  if (editor.query_name !== preset.query_name) {
    const savePayload: SaveSearchQueryDraftPayload = {
      query_id: editor.query_id,
      query_name: preset.query_name,
      selected_sources: preset.selected_sources,
      grouped_terms: build_grouped_terms_from_pico(preset.pico),
      expression_blocks: build_expression_from_boolean_text(preset.boolean_text),
      max_pages_cn: 1 as const,
    };
    const saved = await client.saveSearchQueryVersion(final_project_id, savePayload);
    return {
      project_id: final_project_id,
      project_created_this_call,
      query_id: saved.query_id,
      query_version: saved.query_version,
    };
  }

  return {
    project_id: final_project_id,
    project_created_this_call,
    query_id: editor.query_id,
    query_version: editor.query_version,
  };
}
