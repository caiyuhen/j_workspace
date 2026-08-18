import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import type { Report8ChaptersDraft } from "@meda/shared-sdk";
import {
  useReportEditorController,
  type FetchClient,
} from "../hooks/useReportEditorController";

describe("Wave 8.4 T8 useReportEditorController C1-C10", () => {
  const makeEmptyDraft = (): Report8ChaptersDraft => ({
    ch1_background: "",
    ch2_methods: "",
    ch3_pico: "",
    ch4_results: "",
    ch5_grade_assessment: "",
    ch6_summary_of_findings: "",
    ch7_discussion: "",
    ch8_appendices: "",
    source_snapshot_id: null,
  });

  const makeMockFetchClient = (): FetchClient & {
    post: ReturnType<typeof vi.fn>;
    get: ReturnType<typeof vi.fn>;
  } => ({
    post: vi.fn(),
    get: vi.fn(),
  });

  const SAMPLE_UPSTREAM_MD = `## 1. Background
背景示例内容 ch1

## 2. Methods
方法学示例内容 ch2

## 3. PICO Selection
pico 内容

## 4. Results
results 内容

## 5. GRADE Assessment
grade 内容

## 6. Summary of Findings
sof 内容

## 7. Discussion
discussion 内容

## 8. Appendices
appendices 内容
`;

  it("C1 initial state 正确：dirty.size=0, activeTab=editor, generating=false", () => {
    const fetchClient = makeMockFetchClient();
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 1, fetchClient }),
    );
    expect(result.current.state.dirty.size).toBe(0);
    expect(result.current.state.activeTab).toBe("editor");
    expect(result.current.state.generating).toBe(false);
    expect(result.current.state.exporting).toBe(false);
    expect(result.current.state.errorDetail).toBeNull();
    expect(result.current.state.sourceSnapshotId).toBeNull();
    expect(result.current.dirtyFields.size).toBe(0);
  });

  it("C2 onFieldChange ch1_background Hello → dirty 含 ch1_background; draft.ch1=Hello", () => {
    const fetchClient = makeMockFetchClient();
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 1, fetchClient }),
    );
    act(() => {
      result.current.onFieldChange("ch1_background", "Hello");
    });
    expect(result.current.state.draft.ch1_background).toBe("Hello");
    expect(result.current.state.dirty.has("ch1_background")).toBe(true);
    expect(result.current.dirtyFields.has("ch1_background")).toBe(true);
  });

  it("C3 tab_change md → activeTab === md", () => {
    const fetchClient = makeMockFetchClient();
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 1, fetchClient }),
    );
    act(() => {
      result.current.dispatch({ type: "tab_change", next: "md" });
    });
    expect(result.current.state.activeTab).toBe("md");
  });

  it("C4 generateFromUpstream 上游 md ch1/ch2 → draft 正确 parse 填充", () => {
    const fetchClient = makeMockFetchClient();
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 1, fetchClient }),
    );
    act(() => {
      result.current.generateFromUpstream(SAMPLE_UPSTREAM_MD);
    });
    expect(result.current.state.draft.ch1_background).toContain("背景示例内容 ch1");
    expect(result.current.state.draft.ch2_methods).toContain("方法学示例内容 ch2");
    expect(result.current.state.errorDetail).toBeNull();
  });

  it("C5 restoreLatestSnapshot mdContent 存在 → draft = snapshot parse; sourceSnapshotId=null", () => {
    const fetchClient = makeMockFetchClient();
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 1, fetchClient, initialSnapshotId: 99 }),
    );
    act(() => {
      (result.current.state.snapshot as unknown as { mdContent: string }).mdContent =
        SAMPLE_UPSTREAM_MD;
      result.current.dispatch({ type: "source_snapshot_set", id: 99 });
    });
    expect(result.current.state.sourceSnapshotId).toBe(99);
    act(() => {
      result.current.restoreLatestSnapshot();
    });
    expect(result.current.state.draft.ch1_background).toContain("背景示例内容 ch1");
    expect(result.current.state.draft.ch2_methods).toContain("方法学示例内容 ch2");
    expect(result.current.state.sourceSnapshotId).toBeNull();
  });

  it("C6 generateReport → fetchClient.post 调用 payload dirty non-empty 作为 override；空串不进 payload (NOTOUCH-5)", () => {
    const fetchClient = makeMockFetchClient();
    fetchClient.post.mockResolvedValueOnce({
      sha: "sha256_test",
      version_label: "manual-123456",
      generated_at: "2026-08-18T00:00:00Z",
    });
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 42, fetchClient }),
    );
    act(() => {
      result.current.onFieldChange("ch1_background", "bg non-empty");
      result.current.onFieldChange("ch2_methods", "");
      result.current.onFieldChange("ch7_discussion", "discussion value");
    });
    expect(result.current.state.dirty.has("ch1_background")).toBe(true);
    expect(result.current.state.dirty.has("ch2_methods")).toBe(true);
    expect(result.current.state.dirty.has("ch7_discussion")).toBe(true);
    return act(async () => {
      const out = await result.current.generateReport();
      expect(out.ok).toBe(true);
      expect(fetchClient.post).toHaveBeenCalledTimes(1);
      const [url, payload] = fetchClient.post.mock.lastCall as [string, Record<string, string>];
      expect(url).toBe("/api/v1/workspaces/projects/42/report/generate");
      expect(payload.version_label).toBeTruthy();
      expect(payload.version_label.startsWith("manual-")).toBe(true);
      expect(payload.override_ch1_background).toBe("bg non-empty");
      expect(payload.override_ch7_discussion).toBe("discussion value");
      expect(Object.prototype.hasOwnProperty.call(payload, "override_ch2_methods")).toBe(false);
    });
  });

  it("C7 generateReport 422 detail prisma_less_than_five → state.errorDetail === prisma_less_than_five", async () => {
    const fetchClient = makeMockFetchClient();
    const err422 = {
      response: { detail: "prisma_less_than_five" },
      detail: "prisma_less_than_five",
    };
    fetchClient.post.mockRejectedValueOnce(err422);
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 1, fetchClient }),
    );
    act(() => {
      result.current.onFieldChange("ch1_background", "some value");
    });
    let reportResult: { ok: boolean; sha?: string | null; detail?: string | null };
    await act(async () => {
      reportResult = await result.current.generateReport();
    });
    expect(reportResult!).toBeDefined();
    expect(reportResult!.ok).toBe(false);
    expect(reportResult!.detail).toBe("prisma_less_than_five");
    expect(result.current.state.errorDetail).toBe("prisma_less_than_five");
    expect(result.current.state.generating).toBe(false);
  });

  it("C8 generateReport success sha256_abcdef1234567890 → state.snapshot.sha === sha; generating=false", async () => {
    const fetchClient = makeMockFetchClient();
    const TEST_SHA = "sha256_abcdef1234567890";
    fetchClient.post.mockResolvedValueOnce({
      sha: TEST_SHA,
      version_label: "manual-654321",
      generated_at: "2026-08-18T12:34:56Z",
    });
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 1, fetchClient }),
    );
    act(() => {
      result.current.onFieldChange("ch1_background", "some text");
    });
    let reportResult: { ok: boolean; sha?: string | null; detail?: string | null };
    await act(async () => {
      reportResult = await result.current.generateReport();
    });
    expect(reportResult!).toBeDefined();
    expect(reportResult!.ok).toBe(true);
    expect(reportResult!.sha).toBe(TEST_SHA);
    expect(result.current.state.snapshot.sha).toBe(TEST_SHA);
    expect(result.current.state.snapshot.versionLabel).toBe("manual-654321");
    expect(result.current.state.snapshot.generatedAt).toBe("2026-08-18T12:34:56Z");
    expect(result.current.state.generating).toBe(false);
  });

  it("C9 exportReport html → ok=true; content=html；exporting 先 true 再 false", async () => {
    const HTML_CONTENT = "<html><body>Report HTML</body></html>";
    let resolvePost!: (val: { content: string }) => void;
    const postPromise = new Promise<{ content: string }>((res) => {
      resolvePost = res;
    });
    const fetchClient = makeMockFetchClient();
    fetchClient.post.mockReturnValueOnce(postPromise);
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 7, fetchClient }),
    );
    let exportPromise!: Promise<{
      ok: boolean;
      content?: string | null;
      detail?: string | null;
    }>;
    act(() => {
      exportPromise = result.current.exportReport("html");
    });
    expect(result.current.state.exporting).toBe(true);
    expect(fetchClient.post).toHaveBeenCalledTimes(1);
    const [url, body] = fetchClient.post.mock.lastCall as [string, { format: string }];
    expect(url).toBe("/api/v1/workspaces/projects/7/report/export/html");
    expect(body.format).toBe("html");
    await act(async () => {
      resolvePost({ content: HTML_CONTENT });
      const out = await exportPromise;
      expect(out.ok).toBe(true);
      expect(out.content).toBe(HTML_CONTENT);
    });
    expect(result.current.state.exporting).toBe(false);
  });

  it("C10 reset → dirty=empty; errorDetail=null; activeTab=editor", () => {
    const fetchClient = makeMockFetchClient();
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 1, fetchClient }),
    );
    act(() => {
      result.current.onFieldChange("ch1_background", "Hello");
      result.current.onFieldChange("ch7_discussion", "Discussion");
      result.current.dispatch({ type: "tab_change", next: "md" });
      result.current.dispatch({ type: "error_set", detail: "some error" });
    });
    expect(result.current.state.dirty.size).toBe(2);
    expect(result.current.state.activeTab).toBe("md");
    expect(result.current.state.errorDetail).toBe("some error");
    act(() => {
      result.current.reset();
    });
    expect(result.current.state.dirty.size).toBe(0);
    expect(result.current.state.errorDetail).toBeNull();
    expect(result.current.state.activeTab).toBe("editor");
    expect(result.current.state.generating).toBe(false);
    expect(result.current.state.exporting).toBe(false);
  });
});
