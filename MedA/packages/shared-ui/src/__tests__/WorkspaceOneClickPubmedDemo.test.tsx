import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { WorkspaceOneClickPubmedDemo } from "../WorkspaceOneClickPubmedDemo";
import type { MedaClient, SessionContext } from "@meda/shared-sdk";
import { DEMO_PRESETS } from "@meda/shared-sdk";

function makeSession(): SessionContext {
  return {
    token: "test-token",
    user: { user_id: "u-test-001", display_name: "Dr. Chen" },
    organization: { slug: "demo-hospital", name: "Demo Hospital" },
    role: "org_admin",
    client_type: "web",
  };
}

function makeClient(overrides: Partial<MedaClient> = {} as any): MedaClient {
  return {
    listProjects: vi.fn().mockResolvedValue([]),
    createProject: vi.fn().mockResolvedValue({ id: 11, organization_slug: "demo-hospital", owner_user_id: "u-test-001", name: "MedA-Demo-Diabetes-CKD-2026", description: "x", workspace_key: "demo-hospital/MedA-Demo-Diabetes-CKD-2026" }),
    getSearchQueryEditor: vi.fn().mockResolvedValue({ query_id: 3, query_name: "old name", query_version: "v0", query_dirty: false, query_mode: "pico_builder", selected_sources: ["pubmed"], grouped_terms: [], expression_blocks: [], validation_messages: [], preview_summary: { status: "ok", coverage_hint: "", database_scope_summary: "", estimated_hit_band: "", last_generated_from: "" }, project: { id: 11, name: "", workspace_key: "", stage_key: "search" } }),
    saveSearchQueryVersion: vi.fn().mockImplementation(async (_pid, p) => ({ query_id: p.query_id, query_name: p.query_name, query_version: "v1", query_dirty: false, query_mode: "pico_builder", selected_sources: p.selected_sources, grouped_terms: p.grouped_terms, expression_blocks: p.expression_blocks, validation_messages: [], preview_summary: { status: "ok", coverage_hint: "", database_scope_summary: "", estimated_hit_band: "", last_generated_from: "" }, project: { id: 11, name: "", workspace_key: "", stage_key: "search" } })),
    createSearchRun: vi.fn().mockResolvedValue({ id: 99, status: "pending" }),
    ...overrides,
  } as unknown as MedaClient;
}

describe("WorkspaceOneClickPubmedDemo", () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it("test1 renders 6 preset chips with correct labels", () => {
    render(
      <WorkspaceOneClickPubmedDemo
        client={makeClient()}
        session={makeSession()}
        workspaceHomeProjectId={7}
        onRunCreated={vi.fn()}
      />,
    );
    DEMO_PRESETS.forEach((p) => {
      const button = screen.getByRole("button", {
        name: `${p.label} preset button`,
      });
      expect(button).toBeInTheDocument();
      expect(button).toHaveTextContent(p.label);
    });
  });

  it("test2 zero projects → clicks chip → calls createProject + saveSearchQueryVersion + createSearchRun with pubmed source", async () => {
    const client = makeClient();
    const onRunCreated = vi.fn();
    render(
      <WorkspaceOneClickPubmedDemo
        client={client}
        session={makeSession()}
        onRunCreated={onRunCreated}
      />,
    );
    const preset = DEMO_PRESETS[0];
    const keyword = preset.label.split(" ").slice(1).join(" ").slice(0, 4);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(keyword) }));
    await waitFor(() => expect(client.createProject).toHaveBeenCalledTimes(1));
    expect(client.createProject).toHaveBeenCalledWith(
      expect.objectContaining({ name: preset.project_name }),
    );
    await waitFor(() => expect(client.saveSearchQueryVersion).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(client.createSearchRun).toHaveBeenCalledTimes(1));
    const payload = (client.createSearchRun as any).mock.calls[0][1];
    expect(payload.selected_sources).toEqual(["pubmed"]);
    expect(onRunCreated).toHaveBeenCalledWith(99, expect.any(Number));
  });

  it("test3 existing matching project → does NOT create new project", async () => {
    const preset = DEMO_PRESETS[0];
    const client = makeClient({
      listProjects: vi.fn().mockResolvedValue([
        {
          id: 77,
          name: preset.project_name,
          workspace_key: "x/y",
          current_stage: "search",
          updated_at_label: "刚刚",
        },
      ]),
    } as any);
    render(
      <WorkspaceOneClickPubmedDemo
        client={client}
        session={makeSession()}
        onRunCreated={vi.fn()}
      />,
    );
    const keyword = preset.label.split(" ").slice(1).join(" ").slice(0, 4);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(keyword) }));
    await waitFor(() => expect(client.createSearchRun).toHaveBeenCalled());
    expect(client.createProject).not.toHaveBeenCalled();
  });

  it("test4 saveSearchQueryVersion 422 → toast error 显示", async () => {
    const client = makeClient({
      saveSearchQueryVersion: vi
        .fn()
        .mockRejectedValue(new Error("422 grouped_terms empty")),
    } as any);
    render(
      <WorkspaceOneClickPubmedDemo
        client={client}
        session={makeSession()}
        onRunCreated={vi.fn()}
      />,
    );
    const p = DEMO_PRESETS[1];
    const keyword = p.label.split(" ").slice(1).join(" ").slice(0, 4);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(keyword) }));
    await waitFor(() =>
      expect(screen.queryByText(/Demo 启动失败/)).toBeInTheDocument(),
    );
  });

  it("test5 expression block 是 LiteralBoolean 包含 preset boolean_text", async () => {
    const client = makeClient();
    render(
      <WorkspaceOneClickPubmedDemo
        client={client}
        session={makeSession()}
        workspaceHomeProjectId={5}
        onRunCreated={vi.fn()}
      />,
    );
    const p = DEMO_PRESETS[2];
    const keyword = p.label.split(" ").slice(1).join(" ").slice(0, 4);
    fireEvent.click(screen.getByRole("button", { name: new RegExp(keyword) }));
    await waitFor(() => expect(client.saveSearchQueryVersion).toHaveBeenCalled());
    const payload = (client.saveSearchQueryVersion as any).mock.calls[0][1] as any;
    expect(payload.expression_blocks[0].block_type).toEqual("LiteralBoolean");
    expect(payload.grouped_terms.length).toBeGreaterThanOrEqual(4);
    expect(
      payload.grouped_terms.every((g: any) => g.terms.length >= 1),
    ).toBe(true);
  });
});
