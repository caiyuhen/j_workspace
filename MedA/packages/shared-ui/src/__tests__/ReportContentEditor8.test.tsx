import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import React from "react";
import type { Report8ChaptersDraft } from "@meda/shared-sdk";
import {
  ReportContentEditor8,
  parseSnapshotInto8Chapters,
  generateDraftFromUpstream,
  CHAPTER_META,
  TAG_COLOR,
} from "../components/ReportContentEditor8";

describe("Wave 8.4 T5 ReportContentEditor8 E1-E20", () => {
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

  it("E1 render 8 章 8 textarea 全部存在", () => {
    render(<ReportContentEditor8 />);
    for (let ch = 1; ch <= 8; ch++) {
      expect(screen.getByTestId(`ch${ch}_textarea`)).toBeTruthy();
    }
    expect(screen.getByTestId("rce8-editor")).toBeTruthy();
  });

  it("E2 所有章节 badge 正确颜色（auto_editable = 自动可编辑）", () => {
    render(<ReportContentEditor8 />);
    for (const meta of CHAPTER_META) {
      const badge = screen.getByTestId(`rce8-badge-ch${meta.ch}`);
      expect(badge.textContent).toBeTruthy();
      if (meta.tag === "auto") {
        expect(badge.textContent).toMatch(/Auto|自动/);
      } else if (meta.tag === "auto_editable") {
        expect(badge.textContent).toMatch(/Auto-Editable|自动可编辑/);
      } else if (meta.tag === "manual") {
        expect(badge.textContent).toMatch(/Manual|人工/);
      }
      expect(badge.style.background).toBeTruthy();
    }
    expect(CHAPTER_META[0].tag).toBe("auto_editable");
    expect(CHAPTER_META[6].tag).toBe("manual");
  });

  it("E3 rce8-count-ch1 显示实时字符 count", () => {
    const init: Partial<Report8ChaptersDraft> = { ch1_background: "Hello World" };
    render(<ReportContentEditor8 initialValue={init} />);
    const count = screen.getByTestId("rce8-count-ch1");
    expect(count.textContent).toContain("11");
    const ta = screen.getByTestId("ch1_textarea") as HTMLTextAreaElement;
    fireEvent.change(ta, { target: { value: "0123456789" } });
    expect(count.textContent).toContain("10");
  });

  it("E4 手动编辑 ch1 → onValueChange 回调值正确", () => {
    const onChange = vi.fn();
    render(<ReportContentEditor8 onValueChange={onChange} />);
    const ta = screen.getByTestId("ch1_textarea") as HTMLTextAreaElement;
    fireEvent.change(ta, { target: { value: "bg new text" } });
    expect(onChange).toHaveBeenCalled();
    const [newVal, dirty] = onChange.mock.lastCall as [
      Report8ChaptersDraft,
      Set<keyof Report8ChaptersDraft>,
    ];
    expect(newVal.ch1_background).toBe("bg new text");
    expect(dirty.has("ch1_background")).toBe(true);
  });

  it("E5 initialValue 初始化生效", () => {
    const init: Partial<Report8ChaptersDraft> = {
      ch1_background: "背景测试",
      ch7_discussion: "讨论测试",
    };
    render(<ReportContentEditor8 initialValue={init} />);
    expect((screen.getByTestId("ch1_textarea") as HTMLTextAreaElement).value).toBe(
      "背景测试",
    );
    expect((screen.getByTestId("ch7_textarea") as HTMLTextAreaElement).value).toBe(
      "讨论测试",
    );
  });

  it("E6 sourceSnapshotId 在 header 显示", () => {
    render(<ReportContentEditor8 sourceSnapshotId={42} />);
    const idEl = screen.getByTestId("rce8-snapshot-id");
    expect(idEl.textContent).toContain("42");
  });

  it("E7 readOnly=true 所有 8 textarea 是只读", () => {
    render(<ReportContentEditor8 readOnly={true} />);
    for (let ch = 1; ch <= 8; ch++) {
      const ta = screen.getByTestId(`ch${ch}_textarea`) as HTMLTextAreaElement;
      expect(ta.readOnly || ta.disabled).toBe(true);
    }
  });

  it("E8 parseSnapshotInto8Chapters 能解析带中文 H2 标题的 md", () => {
    const md = `# 报告
## 1. 研究背景
背景中文内容
## 2. 方法学
方法中文
## 3. PICO 选择
PICO 内容
## 4. 结果
结果数据
## 5. GRADE 评估
GRADE 中文
## 6. 发现总结
SOF 中文
## 7. 讨论
讨论中文
## 8. 附录
附录中文`;
    const result = parseSnapshotInto8Chapters(md);
    expect(result.ch1_background).toBe("背景中文内容");
    expect(result.ch2_methods).toBe("方法中文");
    expect(result.ch3_pico).toBe("PICO 内容");
    expect(result.ch4_results).toBe("结果数据");
    expect(result.ch5_grade_assessment).toBe("GRADE 中文");
    expect(result.ch6_summary_of_findings).toBe("SOF 中文");
    expect(result.ch7_discussion).toBe("讨论中文");
    expect(result.ch8_appendices).toBe("附录中文");
  });

  it("E9 parseSnapshotInto8Chapters 解析带英文 H2 的 md", () => {
    const md = `# Report
## 1. Background
bg en
## 2. Methods
methods en
## 3. PICO Selection
pico en
## 4. Results
results en
## 5. GRADE Assessment
grade en
## 6. Summary of Findings
sof en
## 7. Discussion
disc en
## 8. Appendices
app en`;
    const result = parseSnapshotInto8Chapters(md);
    expect(result.ch1_background).toBe("bg en");
    expect(result.ch2_methods).toBe("methods en");
    expect(result.ch3_pico).toBe("pico en");
    expect(result.ch4_results).toBe("results en");
    expect(result.ch5_grade_assessment).toBe("grade en");
    expect(result.ch6_summary_of_findings).toBe("sof en");
    expect(result.ch7_discussion).toBe("disc en");
    expect(result.ch8_appendices).toBe("app en");
  });

  it("E10 缺失章节返回空串（不抛错）", () => {
    const md = `# 报告\n## 1. 研究背景\n只有第一章`;
    expect(() => parseSnapshotInto8Chapters(md)).not.toThrow();
    const result = parseSnapshotInto8Chapters(md);
    expect(result.ch1_background).toBe("只有第一章");
    expect(result.ch2_methods).toBe("");
    expect(result.ch3_pico).toBe("");
    expect(result.ch4_results).toBe("");
    expect(result.ch5_grade_assessment).toBe("");
    expect(result.ch6_summary_of_findings).toBe("");
    expect(result.ch7_discussion).toBe("");
    expect(result.ch8_appendices).toBe("");
  });

  it("E11 generateDraftFromUpstream 全字段传入合并正确", () => {
    const result = generateDraftFromUpstream({
      background: "bg",
      methods: "mt",
      pico: "pc",
      results: "rs",
      grade: "gd",
      sof: "sf",
      discussion: "ds",
      appendices: "ap",
    });
    expect(result.ch1_background).toBe("bg");
    expect(result.ch2_methods).toBe("mt");
    expect(result.ch3_pico).toBe("pc");
    expect(result.ch4_results).toBe("rs");
    expect(result.ch5_grade_assessment).toContain("gd");
    expect(result.ch5_grade_assessment).toContain("sf");
    expect(result.ch6_summary_of_findings).toBe("sf");
    expect(result.ch7_discussion).toBe("ds");
    expect(result.ch8_appendices).toBe("ap");
  });

  it("E12 generateDraftFromUpstream 部分字段（缺 discussion) → ch7 包含 grade/sof 要点", () => {
    const result = generateDraftFromUpstream({
      grade: "grade-data",
      sof: "sof-data",
    });
    expect(result.ch1_background).toBe("");
    expect(result.ch7_discussion).toContain("grade-data");
    expect(result.ch7_discussion).toContain("sof-data");
    expect(result.source_snapshot_id).toBeNull();
  });

  it("E13 点击 btn-import-upstream 触发 onImportUpstream", () => {
    const onImport = vi.fn();
    render(<ReportContentEditor8 onImportUpstream={onImport} />);
    fireEvent.click(screen.getByTestId("btn-import-upstream"));
    expect(onImport).toHaveBeenCalledTimes(1);
  });

  it("E14 enableImportButton=false → 不渲染按钮", () => {
    render(<ReportContentEditor8 enableImportButton={false} />);
    expect(screen.queryByTestId("btn-import-upstream")).toBeNull();
  });

  it("E15 enableRestoreButton=false → 不渲染 restore 按钮", () => {
    render(<ReportContentEditor8 enableRestoreButton={false} />);
    expect(screen.queryByTestId("btn-restore-snapshot")).toBeNull();
  });

  it("E16 upstreamSnapshotMd 传入但 initialValue 不传 → 默认值为 parse 结果", () => {
    const md = `# 报告
## 1. Background
snapshot-bg
## 2. Methods
snapshot-mt
## 8. Appendices
snapshot-ap`;
    const onChange = vi.fn();
    render(
      <ReportContentEditor8 upstreamSnapshotMd={md} onValueChange={onChange} />,
    );
    expect((screen.getByTestId("ch1_textarea") as HTMLTextAreaElement).value).toBe(
      "snapshot-bg",
    );
    expect((screen.getByTestId("ch2_textarea") as HTMLTextAreaElement).value).toBe(
      "snapshot-mt",
    );
    expect((screen.getByTestId("ch8_textarea") as HTMLTextAreaElement).value).toBe(
      "snapshot-ap",
    );
    expect(onChange).not.toHaveBeenCalled();
  });

  it("E17 dirtyFields：改 ch1 → dirty size=1", () => {
    const onChange = vi.fn();
    render(<ReportContentEditor8 onValueChange={onChange} />);
    fireEvent.change(screen.getByTestId("ch1_textarea"), {
      target: { value: "a" },
    });
    const [, dirty1] = onChange.mock.lastCall as [
      Report8ChaptersDraft,
      Set<keyof Report8ChaptersDraft>,
    ];
    expect(dirty1.size).toBe(1);
  });

  it("E18 dirtyFields：改 ch1 和 ch7 → dirty size=2；字段包括 ch1_background, ch7_discussion", () => {
    const onChange = vi.fn();
    render(<ReportContentEditor8 onValueChange={onChange} />);
    fireEvent.change(screen.getByTestId("ch1_textarea"), {
      target: { value: "bg1" },
    });
    fireEvent.change(screen.getByTestId("ch7_textarea"), {
      target: { value: "disc1" },
    });
    const [val, dirty] = onChange.mock.lastCall as [
      Report8ChaptersDraft,
      Set<keyof Report8ChaptersDraft>,
    ];
    expect(dirty.size).toBe(2);
    expect(dirty.has("ch1_background")).toBe(true);
    expect(dirty.has("ch7_discussion")).toBe(true);
    expect(val.ch1_background).toBe("bg1");
    expect(val.ch7_discussion).toBe("disc1");
  });

  it("E19 parseSnapshotInto8Chapters 返回 source_snapshot_id 为 null", () => {
    const md = `# 报告\n## 1. Background\n内容`;
    const result = parseSnapshotInto8Chapters(md);
    expect(result.source_snapshot_id).toBeNull();
    expect("source_snapshot_id" in result).toBe(true);
  });

  it("E20 onRestoreSnapshot 触发 onValueChange 重置为上游快照（结合 upstreamSnapshotMd parse 结果）", () => {
    const md = `# 报告
## 1. Background
ORIGINAL_BG
## 7. Discussion
ORIGINAL_DISC`;
    const onChange = vi.fn();
    const onRestore = vi.fn();
    render(
      <ReportContentEditor8
        upstreamSnapshotMd={md}
        onValueChange={onChange}
        onRestoreSnapshot={onRestore}
      />,
    );
    fireEvent.change(screen.getByTestId("ch1_textarea"), {
      target: { value: "MODIFIED" },
    });
    expect(
      (screen.getByTestId("ch1_textarea") as HTMLTextAreaElement).value,
    ).toBe("MODIFIED");

    fireEvent.click(screen.getByTestId("btn-restore-snapshot"));
    expect(onRestore).toHaveBeenCalledTimes(1);

    const [restoredVal, restoredDirty] = onChange.mock.lastCall as [
      Report8ChaptersDraft,
      Set<keyof Report8ChaptersDraft>,
    ];
    expect(restoredVal.ch1_background).toBe("ORIGINAL_BG");
    expect(restoredVal.ch7_discussion).toBe("ORIGINAL_DISC");
    expect(restoredDirty.size).toBe(0);
  });
});

describe("T5 Constants checks CHAPTER_META + TAG_COLOR", () => {
  it("CHAPTER_META 顺序必须 ch1..ch8 共 8 项", () => {
    expect(CHAPTER_META.length).toBe(8);
    CHAPTER_META.forEach((m, idx) => {
      expect(m.ch).toBe(idx + 1);
    });
    expect(CHAPTER_META[0].key).toBe("ch1_background");
    expect(CHAPTER_META[1].key).toBe("ch2_methods");
    expect(CHAPTER_META[2].key).toBe("ch3_pico");
    expect(CHAPTER_META[3].key).toBe("ch4_results");
    expect(CHAPTER_META[4].key).toBe("ch5_grade_assessment");
    expect(CHAPTER_META[5].key).toBe("ch6_summary_of_findings");
    expect(CHAPTER_META[6].key).toBe("ch7_discussion");
    expect(CHAPTER_META[7].key).toBe("ch8_appendices");
  });

  it("TAG_COLOR 映射三类正确", () => {
    expect(TAG_COLOR.auto.className).toMatch(/green/i);
    expect(TAG_COLOR.auto_editable.className).toMatch(/blue/i);
    expect(TAG_COLOR.manual.className).toMatch(/amber/i);
  });
});
