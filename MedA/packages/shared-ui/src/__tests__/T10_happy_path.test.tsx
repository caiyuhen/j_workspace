import React from "react";
import { describe, it, expect, vi } from "vitest";
import { renderHook, render, act, screen } from "@testing-library/react";
import {
  useReportEditorController,
  type FetchClient,
} from "../hooks/useReportEditorController";
import { ReportGeneratorPanel } from "../components/ReportGeneratorPanel";
import { ReportContentEditor8 } from "../components/ReportContentEditor8";

describe("Wave 8.4 T10 Happy Path Integration", () => {
  const UPSTREAM_MD = `## 1. Background
上游背景 ch1 内容

## 2. Methods
上游方法学 ch2 内容

## 3. PICO Selection
pico

## 4. Results
results

## 5. GRADE Assessment
grade

## 6. Summary of Findings
sof

## 7. Discussion
upstream discussion

## 8. Appendices
appendices
`;

  const MOCK_SHA = "sha256_happypath_abcd1234ef56";
  const MOCK_VERSION = "manual-123456";
  const MOCK_GENERATED_AT = "2026-08-18T10:20:30Z";
  const CH7_MANUAL = "## 讨论人工精修\n要点 1：需要补充异质性来源分析\n要点 2：GRADE 降级依据需明确";

  const makeFetchClient = () => ({
    post: vi.fn().mockResolvedValue({
      sha: MOCK_SHA,
      version_label: MOCK_VERSION,
      generated_at: MOCK_GENERATED_AT,
    }),
  } as FetchClient & { post: ReturnType<typeof vi.fn> });

  it("T10 Happy Path: generateFromUpstream → manual edits → generateReport → Panel render tabs", async () => {
    const fetchClient = makeFetchClient();
    const { result } = renderHook(() =>
      useReportEditorController({ projectId: 77, fetchClient }),
    );

    act(() => {
      result.current.generateFromUpstream(UPSTREAM_MD);
    });
    expect(result.current.state.draft.ch1_background).toContain("上游背景 ch1");
    expect(result.current.state.draft.ch2_methods).toContain("上游方法学 ch2");

    act(() => {
      result.current.onFieldChange("ch7_discussion", CH7_MANUAL);
    });
    expect(result.current.state.dirty.has("ch7_discussion")).toBe(true);
    expect(result.current.state.draft.ch7_discussion).toBe(CH7_MANUAL);

    act(() => {
      result.current.onFieldChange("ch1_background", "");
    });
    expect(result.current.state.dirty.has("ch1_background")).toBe(true);
    expect(result.current.state.draft.ch1_background).toBe("");

    let genResult: { ok: boolean; sha?: string | null };
    await act(async () => {
      genResult = await result.current.generateReport();
    });

    expect(genResult!.ok).toBe(true);
    expect(fetchClient.post).toHaveBeenCalledTimes(1);

    const [url, payload] = fetchClient.post.mock.lastCall as [string, Record<string, string>];
    expect(url).toBe("/api/v1/workspaces/projects/77/report/generate");
    expect(payload.override_ch7_discussion).toBe(CH7_MANUAL);
    expect(Object.prototype.hasOwnProperty.call(payload, "override_ch1_background")).toBe(false);
    expect(payload.version_label).toMatch(/^manual-\d{6}$/);
    expect(result.current.state.snapshot.sha).toBe(MOCK_SHA);

    const ui = (
      <ReportGeneratorPanel
        projectId={77}
        sha256={result.current.state.snapshot.sha}
        versionLabel={result.current.state.snapshot.versionLabel}
        activeTab={result.current.state.activeTab}
        onActiveTabChange={(t) => result.current.dispatch({ type: "tab_change", next: t })}
        editorSlot={<ReportContentEditor8 />}
        mdPreviewSlot={result.current.state.snapshot.mdContent}
        htmlPreviewSlot={result.current.state.snapshot.htmlContent}
        onGenerateClick={() => result.current.generateReport()}
        isGenerating={result.current.state.generating}
        errorDetailLiteral={result.current.state.errorDetail}
        generatedAt={result.current.state.snapshot.generatedAt}
      />
    );
    render(ui);
    expect(screen.getByTestId("tab-editor")).toBeInTheDocument();
    expect(screen.getByTestId("tab-md")).toBeInTheDocument();
    expect(screen.getByTestId("tab-html")).toBeInTheDocument();
  });
});
