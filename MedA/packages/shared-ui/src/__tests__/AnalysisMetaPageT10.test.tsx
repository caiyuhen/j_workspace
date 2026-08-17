import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import React from "react";
import {
  OutcomeArmInputs,
  type OutcomeArmInputsProps,
  type OutcomeType,
  type BinaryMeasure,
  type ContinuousMeasure,
  type ArmInputsValue,
} from "../analysis/OutcomeArmInputs";
import {
  ForestPlotW83,
  type ForestPlotW83Props,
  type ForestStudyRow,
  type ForestMetaResult,
} from "../charts/ForestPlotW83";
import {
  AnalysisMetaPage,
  type AnalysisMetaPageProps,
  type OutcomeDefinition,
  type MetaRunResult,
} from "../analysis/AnalysisMetaPage";

// ============================================================
// Helpers
// ============================================================
function makeBinaryArms(
  e1: number,
  n1: number,
  e2: number,
  n2: number
): ArmInputsValue {
  return {
    outcome_type: "binary",
    measure: "RR",
    events_1: e1,
    n_1: n1,
    events_2: e2,
    n_2: n2,
  };
}

function makeContinuousArms(
  m1: number,
  sd1: number,
  n1: number,
  m2: number,
  sd2: number,
  n2: number
): ArmInputsValue {
  return {
    outcome_type: "continuous",
    measure: "MD",
    mean_1: m1,
    sd_1: sd1,
    n_1: n1,
    mean_2: m2,
    sd_2: sd2,
    n_2: n2,
  };
}

function sampleForestStudies(n: number): ForestStudyRow[] {
  const arr: ForestStudyRow[] = [];
  for (let i = 0; i < n; i++) {
    arr.push({
      study_id: `s${i + 1}`,
      study_label: `Study ${i + 1}`,
      effect: 0.8 + i * 0.05,
      ci_low: 0.5 + i * 0.03,
      ci_high: 1.2 + i * 0.04,
      weight: 20,
    });
  }
  return arr;
}

function sampleMetaResult(): MetaRunResult {
  return {
    outcome_id: "o1",
    analysis_model: "random_dl",
    pooled: {
      effect: 0.8765,
      ci_low: 0.6123,
      ci_high: 1.2345,
      p_value: 0.345,
    },
    heterogeneity: {
      I2_pct: 62.34,
      Q: 12.34,
      df: 4,
      p_value: 0.015,
    },
    studies: sampleForestStudies(5),
  };
}

function sampleOutcomes(n: number): OutcomeDefinition[] {
  const arr: OutcomeDefinition[] = [];
  for (let i = 0; i < n; i++) {
    arr.push({
      id: `o${i + 1}`,
      name: `Outcome ${i + 1}`,
      outcome_type: i % 2 === 0 ? "binary" : "continuous",
      measure: i % 2 === 0 ? "RR" : "MD",
      description: `Desc ${i + 1}`,
      time_point: i === 0 ? "Week 12" : undefined,
    });
  }
  return arr;
}

// ============================================================
// A) OutcomeArmInputs (8 tests)
// ============================================================
describe("Wave83 T10 A) OutcomeArmInputs (8)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  function renderArms(overrides: Partial<OutcomeArmInputsProps> = {}) {
    const onChange = vi.fn();
    const value: ArmInputsValue = overrides.value ?? makeBinaryArms(10, 50, 15, 60);
    const props: OutcomeArmInputsProps = {
      value,
      onChange,
      ...overrides,
    };
    const r = render(<OutcomeArmInputs {...props} />);
    return { ...r, onChange };
  }

  it("A01: outcome_type=binary → renders 4 inputs: events-1, n-1, events-2, n-2", () => {
    renderArms({ value: makeBinaryArms(10, 50, 15, 60) });
    expect(screen.getByTestId("events-1")).toBeTruthy();
    expect(screen.getByTestId("n-1")).toBeTruthy();
    expect(screen.getByTestId("events-2")).toBeTruthy();
    expect(screen.getByTestId("n-2")).toBeTruthy();
  });

  it("A02: binary measure selector 显示 RR/OR/RD 三选项（binary measure only）", () => {
    renderArms({ value: makeBinaryArms(10, 50, 15, 60) });
    const sel = screen.getByTestId("measure-selector") as HTMLSelectElement;
    const opts = Array.from(sel.options).map((o) => o.value);
    expect(opts).toContain("RR");
    expect(opts).toContain("OR");
    expect(opts).toContain("RD");
  });

  it("A03: type=continuous → renders 6 inputs: mean-1,sd-1,n-1,mean-2,sd-2,n-2", () => {
    renderArms({ value: makeContinuousArms(10.5, 2.3, 50, 12.1, 3.2, 60) });
    expect(screen.getByTestId("mean-1")).toBeTruthy();
    expect(screen.getByTestId("sd-1")).toBeTruthy();
    expect(screen.getByTestId("n-1")).toBeTruthy();
    expect(screen.getByTestId("mean-2")).toBeTruthy();
    expect(screen.getByTestId("sd-2")).toBeTruthy();
    expect(screen.getByTestId("n-2")).toBeTruthy();
  });

  it("A04: continuous measure selector 显示 MD / SMD 两选项", () => {
    renderArms({ value: makeContinuousArms(10.5, 2.3, 50, 12.1, 3.2, 60) });
    const sel = screen.getByTestId("measure-selector") as HTMLSelectElement;
    const opts = Array.from(sel.options).map((o) => o.value);
    expect(opts).toContain("MD");
    expect(opts).toContain("SMD");
    expect(opts).not.toContain("RR");
  });

  it("A05: binary events > n → 显示 events-gt-n-warning data-testid", () => {
    renderArms({ value: makeBinaryArms(60, 50, 15, 60) });
    expect(screen.getByTestId("events-gt-n-warning")).toBeTruthy();
  });

  it("A06: continuous sd<=0 或 n<2 → sd-nonpositive-warning", () => {
    renderArms({ value: makeContinuousArms(10, 0, 50, 12, 3.2, 60) });
    expect(screen.getByTestId("sd-nonpositive-warning")).toBeTruthy();
  });

  it("A07: inputs 输入变更 → onChange callback 拿到正确 payload", () => {
    const { onChange } = renderArms({ value: makeBinaryArms(10, 50, 15, 60) });
    const ev1 = screen.getByTestId("events-1") as HTMLInputElement;
    fireEvent.change(ev1, { target: { value: "25" } });
    expect(onChange).toHaveBeenCalled();
    const last = onChange.mock.calls[onChange.mock.calls.length - 1][0];
    expect(last.events_1).toBe(25);
    expect(last.outcome_type).toBe("binary");
  });

  it("A08: 切换 type binary → continuous → 原 binary inputs 清空，continuous 渲染", () => {
    const initial = makeBinaryArms(10, 50, 15, 60);
    let current: ArmInputsValue = initial;
    const onChange = vi.fn((v) => {
      current = v;
    });
    const { rerender } = render(<OutcomeArmInputs value={current} onChange={onChange} />);
    expect(screen.getByTestId("events-1")).toBeTruthy();
    const cont: ArmInputsValue = {
      outcome_type: "continuous",
      measure: "MD",
      mean_1: 10.5,
      sd_1: 2.3,
      n_1: 50,
      mean_2: 12.1,
      sd_2: 3.2,
      n_2: 60,
    };
    rerender(<OutcomeArmInputs value={cont} onChange={onChange} />);
    expect(screen.queryByTestId("events-1")).toBeFalsy();
    expect(screen.getByTestId("mean-1")).toBeTruthy();
  });
});

// ============================================================
// B) ForestPlotW83 (7 tests)
// ============================================================
describe("Wave83 T10 B) ForestPlotW83 (7)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  function renderForest(overrides: Partial<ForestPlotW83Props> = {}) {
    const props: ForestPlotW83Props = {
      studies: [],
      result: undefined,
      width: 800,
      height: 500,
      ...overrides,
    };
    return render(<ForestPlotW83 {...props} />);
  }

  it("B01: render empty studies → 显示 no-data-forest", () => {
    renderForest({ studies: [], result: undefined });
    expect(screen.getByTestId("no-data-forest")).toBeTruthy();
  });

  it("B02: K=5 studies → renders 5 rows (forest-row-{i}, 每 row 有 square + horizontal-line)", () => {
    renderForest({ studies: sampleForestStudies(5), result: undefined });
    for (let i = 0; i < 5; i++) {
      const row = screen.getByTestId(`forest-row-${i}`);
      expect(row).toBeTruthy();
      const w = within(row as HTMLElement);
      expect(w.getByTestId(`forest-square-${i}`)).toBeTruthy();
      expect(w.getByTestId(`forest-hline-${i}`)).toBeTruthy();
    }
  });

  it("B03: pooled diamond polygon 存在（diamond-pooled 元素，polygon.points length=4）", () => {
    const result: ForestMetaResult = {
      pooled: { effect: 0.88, ci_low: 0.61, ci_high: 1.23 },
      heterogeneity: { I2_pct: 62 },
    };
    renderForest({ studies: sampleForestStudies(5), result });
    const diamond = screen.getByTestId("diamond-pooled");
    expect(diamond).toBeTruthy();
    const points = diamond.getAttribute("points")?.trim().split(/[\s,]+/).filter(Boolean) ?? [];
    expect(points.length).toBe(8);
  });

  it("B04: I² text 元素包含内容 I² = → 存在", () => {
    const result: ForestMetaResult = {
      pooled: { effect: 0.88, ci_low: 0.61, ci_high: 1.23 },
      heterogeneity: { I2_pct: 62.5 },
    };
    renderForest({ studies: sampleForestStudies(5), result });
    const i2 = screen.getByTestId("i2-text");
    expect(i2.textContent).toContain("I");
    expect(i2.textContent).toMatch(/I.*=|I\u00b2.*=/);
  });

  it("B05: svg 大小 viewBox 属性存在（not empty）", () => {
    renderForest({ studies: sampleForestStudies(3), result: undefined, width: 800, height: 500 });
    const svg = screen.getByTestId("forest-svg-root");
    const vb = svg.getAttribute("viewBox");
    expect(vb).toBeTruthy();
    expect(vb!.length).toBeGreaterThan(3);
  });

  it("B06: no script tag 检测（确保自包含 AC7-4）", () => {
    renderForest({ studies: sampleForestStudies(3), result: undefined });
    const svg = screen.getByTestId("forest-svg-root");
    const svgAny = svg as unknown as SVGElement;
    const scripts = svgAny.querySelectorAll("script");
    expect(scripts.length).toBe(0);
  });

  it("B07: svg element class=forest-svg + width not 0", () => {
    renderForest({ studies: sampleForestStudies(3), result: undefined, width: 800, height: 500 });
    const svg = screen.getByTestId("forest-svg-root");
    expect(svg.getAttribute("class")).toContain("forest-svg");
    const w = svg.getAttribute("width");
    const h = svg.getAttribute("height");
    const wNum = w ? Number(w) : 0;
    const hNum = h ? Number(h) : 0;
    expect(wNum).toBeGreaterThan(0);
    expect(hNum).toBeGreaterThan(0);
  });
});

// ============================================================
// C) AnalysisMetaPage (25 tests)
// ============================================================
describe("Wave83 T10 C) AnalysisMetaPage (25)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  function renderPage(overrides: Partial<AnalysisMetaPageProps> = {}) {
    const onDefineOutcome = vi.fn();
    const onRunMeta = vi.fn();
    const onExportForestSvg = vi.fn();
    const clearRuns = vi.fn();
    const onSelectOutcome = vi.fn();
    const onDeleteStudy = vi.fn();
    const onAddStudy = vi.fn();
    const onArmsChange = vi.fn();

    const props: AnalysisMetaPageProps = {
      outcomes: [],
      selectedOutcomeId: undefined,
      onSelectOutcome,
      onDefineOutcome,
      studiesByOutcome: {},
      onAddStudy,
      onDeleteStudy,
      armsByOutcome: {},
      onArmsChange,
      analysisModel: "random_dl",
      onAnalysisModelChange: vi.fn(),
      runResultByOutcome: {},
      onRunMeta,
      onExportForestSvg,
      clearRuns,
      ...overrides,
    };
    const r = render(<AnalysisMetaPage {...props} />);
    return {
      ...r,
      onDefineOutcome,
      onRunMeta,
      onExportForestSvg,
      clearRuns,
      onSelectOutcome,
      onDeleteStudy,
      onAddStudy,
      onArmsChange,
    };
  }

  it("C01: page-title-analysis-rendering 存在", () => {
    renderPage();
    expect(screen.getByTestId("page-title-analysis-rendering")).toBeTruthy();
  });

  it("C02: empty outcome list → shows no-outcomes-yet 状态", () => {
    renderPage({ outcomes: [] });
    expect(screen.getByTestId("no-outcomes-yet")).toBeTruthy();
  });

  it("C03: click btn-add-outcome → 显示 OutcomeDefineDialog（dialog-outcome-define）", () => {
    renderPage({ outcomes: [] });
    fireEvent.click(screen.getByTestId("btn-add-outcome"));
    expect(screen.getByTestId("dialog-outcome-define")).toBeTruthy();
  });

  it("C04: dialog 填入 name + select type=binary + RR → btn-save-outcome 触发 onDefineOutcome callback 1 次 with correct payload", () => {
    const { onDefineOutcome } = renderPage({ outcomes: [] });
    fireEvent.click(screen.getByTestId("btn-add-outcome"));
    const nameInput = screen.getByTestId("dialog-outcome-name") as HTMLInputElement;
    fireEvent.change(nameInput, { target: { value: "Mortality" } });
    const typeSel = screen.getByTestId("dialog-outcome-type") as HTMLSelectElement;
    fireEvent.change(typeSel, { target: { value: "binary" } });
    const measureSel = screen.getByTestId("dialog-outcome-measure") as HTMLSelectElement;
    fireEvent.change(measureSel, { target: { value: "RR" } });
    fireEvent.click(screen.getByTestId("btn-save-outcome"));
    expect(onDefineOutcome).toHaveBeenCalledTimes(1);
    const payload = onDefineOutcome.mock.calls[0][0];
    expect(payload.name).toBe("Mortality");
    expect(payload.outcome_type).toBe("binary");
    expect(payload.measure).toBe("RR");
  });

  it("C05: outcome list length=3 → renders 3 outcome cards", () => {
    renderPage({ outcomes: sampleOutcomes(3) });
    expect(screen.getByTestId("outcome-card-o1")).toBeTruthy();
    expect(screen.getByTestId("outcome-card-o2")).toBeTruthy();
    expect(screen.getByTestId("outcome-card-o3")).toBeTruthy();
  });

  it("C06: 选中某 outcome card → card has class outcome-card-selected", () => {
    renderPage({ outcomes: sampleOutcomes(3), selectedOutcomeId: "o2" });
    const card = screen.getByTestId("outcome-card-o2");
    expect(card.getAttribute("class")).toContain("outcome-card-selected");
  });

  it("C07: 选中 binary RR outcome → OutcomeArmInputs renders 4 binary inputs", () => {
    const outcomes = sampleOutcomes(3);
    renderPage({
      outcomes,
      selectedOutcomeId: "o1",
      armsByOutcome: {
        o1: makeBinaryArms(10, 50, 15, 60),
      },
    });
    expect(screen.getByTestId("events-1")).toBeTruthy();
    expect(screen.getByTestId("n-1")).toBeTruthy();
    expect(screen.getByTestId("events-2")).toBeTruthy();
    expect(screen.getByTestId("n-2")).toBeTruthy();
  });

  it("C08: 选中 continuous MD outcome → OutcomeArmInputs renders 6 continuous inputs", () => {
    const outcomes = sampleOutcomes(3);
    renderPage({
      outcomes,
      selectedOutcomeId: "o2",
      armsByOutcome: {
        o2: makeContinuousArms(10.5, 2.3, 50, 12.1, 3.2, 60),
      },
    });
    expect(screen.getByTestId("mean-1")).toBeTruthy();
    expect(screen.getByTestId("sd-1")).toBeTruthy();
    expect(screen.getByTestId("n-1")).toBeTruthy();
    expect(screen.getByTestId("mean-2")).toBeTruthy();
    expect(screen.getByTestId("sd-2")).toBeTruthy();
    expect(screen.getByTestId("n-2")).toBeTruthy();
  });

  it("C09: 添加 2 study 后 → studies-list 显示 2 条", () => {
    renderPage({
      outcomes: sampleOutcomes(1),
      selectedOutcomeId: "o1",
      studiesByOutcome: {
        o1: [
          { study_id: "s1", study_label: "Study A" },
          { study_id: "s2", study_label: "Study B" },
        ],
      },
    });
    const list = screen.getByTestId("studies-list");
    expect(list).toBeTruthy();
    expect(screen.getByTestId("study-row-s1")).toBeTruthy();
    expect(screen.getByTestId("study-row-s2")).toBeTruthy();
  });

  it("C10: 删除 1 study → 剩 1 条 + 删除按钮 enabled confirm fire", () => {
    const onDeleteStudy = vi.fn();
    const { rerender } = render(
      <AnalysisMetaPage
        outcomes={sampleOutcomes(1)}
        selectedOutcomeId="o1"
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{
          o1: [
            { study_id: "s1", study_label: "Study A" },
            { study_id: "s2", study_label: "Study B" },
          ],
        }}
        onAddStudy={vi.fn()}
        onDeleteStudy={onDeleteStudy}
        armsByOutcome={{ o1: makeBinaryArms(10, 50, 15, 60) }}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{}}
        onRunMeta={vi.fn()}
        onExportForestSvg={vi.fn()}
        clearRuns={vi.fn()}
      />
    );
    expect(screen.getByTestId("study-row-s1")).toBeTruthy();
    expect(screen.getByTestId("study-row-s2")).toBeTruthy();
    const delBtn = screen.getByTestId("btn-delete-study-s1") as HTMLButtonElement;
    expect(delBtn.disabled).toBe(false);
    fireEvent.click(delBtn);
    expect(onDeleteStudy).toHaveBeenCalledWith("o1", "s1");
  });

  it("C11: btn-run-meta enabled only when K>=2 studies（k=1 → disabled）", () => {
    renderPage({
      outcomes: sampleOutcomes(1),
      selectedOutcomeId: "o1",
      studiesByOutcome: {
        o1: [{ study_id: "s1", study_label: "Only" }],
      },
      armsByOutcome: { o1: makeBinaryArms(10, 50, 15, 60) },
    });
    expect((screen.getByTestId("btn-run-meta") as HTMLButtonElement).disabled).toBe(true);
  });

  it("C12: btn-run-meta click → onRunMeta callback fired 1 time with selected outcome.id + model=random_dl 默认", () => {
    const onRunMeta = vi.fn();
    render(
      <AnalysisMetaPage
        outcomes={sampleOutcomes(1)}
        selectedOutcomeId="o1"
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{
          o1: [
            { study_id: "s1", study_label: "A" },
            { study_id: "s2", study_label: "B" },
          ],
        }}
        onAddStudy={vi.fn()}
        onDeleteStudy={vi.fn()}
        armsByOutcome={{ o1: makeBinaryArms(10, 50, 15, 60) }}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{}}
        onRunMeta={onRunMeta}
        onExportForestSvg={vi.fn()}
        clearRuns={vi.fn()}
      />
    );
    fireEvent.click(screen.getByTestId("btn-run-meta"));
    expect(onRunMeta).toHaveBeenCalledTimes(1);
    const payload = onRunMeta.mock.calls[0][0];
    expect(payload.outcome_id).toBe("o1");
    expect(payload.analysis_model).toBe("random_dl");
  });

  it("C13: 分析模型 selector fixed_iv/fixed_mh/random_dl 三单选 UI 渲染", () => {
    renderPage({
      outcomes: sampleOutcomes(1),
      selectedOutcomeId: "o1",
      analysisModel: "random_dl",
    });
    const radios = screen.getAllByTestId(/model-radio-/);
    const values = radios.map((r) => (r as HTMLInputElement).value);
    expect(values).toContain("fixed_iv");
    expect(values).toContain("fixed_mh");
    expect(values).toContain("random_dl");
  });

  it("C14: 切换 random_dl → onRunMeta payload analysis_model=random_dl", () => {
    const onRunMeta = vi.fn();
    const { rerender } = render(
      <AnalysisMetaPage
        outcomes={sampleOutcomes(1)}
        selectedOutcomeId="o1"
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{
          o1: [
            { study_id: "s1", study_label: "A" },
            { study_id: "s2", study_label: "B" },
          ],
        }}
        onAddStudy={vi.fn()}
        onDeleteStudy={vi.fn()}
        armsByOutcome={{ o1: makeBinaryArms(10, 50, 15, 60) }}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{}}
        onRunMeta={onRunMeta}
        onExportForestSvg={vi.fn()}
        clearRuns={vi.fn()}
      />
    );
    const radio = screen.getByTestId("model-radio-random_dl") as HTMLInputElement;
    fireEvent.click(radio);
    fireEvent.click(screen.getByTestId("btn-run-meta"));
    const payload = onRunMeta.mock.calls[0][0];
    expect(payload.analysis_model).toBe("random_dl");
  });

  it("C15: run-meta 成功返回 result_json → 下方 ForestPlotW83 渲染 SVG（Forest wrapper 包含 result）", () => {
    renderPage({
      outcomes: sampleOutcomes(1),
      selectedOutcomeId: "o1",
      runResultByOutcome: { o1: sampleMetaResult() },
    });
    expect(screen.getByTestId("forest-result-wrapper")).toBeTruthy();
    expect(screen.getByTestId("forest-svg-root")).toBeTruthy();
  });

  it("C16: pooled effect 文本显示 Pooled Effect = xxx (95%CI xxx-xxx)（3 位小数）", () => {
    renderPage({
      outcomes: sampleOutcomes(1),
      selectedOutcomeId: "o1",
      runResultByOutcome: { o1: sampleMetaResult() },
    });
    const txt = screen.getByTestId("pooled-effect-text");
    expect(txt.textContent).toMatch(/Pooled/);
    expect(txt.textContent).toMatch(/0\.87[0-9]/);
    expect(txt.textContent).toMatch(/0\.61[0-9]/);
    expect(txt.textContent).toMatch(/1\.23[0-9]/);
  });

  it("C17: heterogeneity I² 显示（取 result.heterogeneity.I2_pct）", () => {
    renderPage({
      outcomes: sampleOutcomes(1),
      selectedOutcomeId: "o1",
      runResultByOutcome: { o1: sampleMetaResult() },
    });
    const i2 = screen.getByTestId("heterogeneity-i2");
    expect(i2.textContent).toMatch(/62/);
  });

  it("C18: 空 result → Forest 显示 no-data-forest", () => {
    renderPage({
      outcomes: sampleOutcomes(1),
      selectedOutcomeId: "o1",
      runResultByOutcome: {},
    });
    expect(screen.getByTestId("no-data-forest")).toBeTruthy();
  });

  it("C19: onExportForestSvg 按钮 → 1 次 click → onExport 回调", () => {
    const onExportForestSvg = vi.fn();
    render(
      <AnalysisMetaPage
        outcomes={sampleOutcomes(1)}
        selectedOutcomeId="o1"
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{ o1: [] }}
        onAddStudy={vi.fn()}
        onDeleteStudy={vi.fn()}
        armsByOutcome={{ o1: makeBinaryArms(10, 50, 15, 60) }}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{ o1: sampleMetaResult() }}
        onRunMeta={vi.fn()}
        onExportForestSvg={onExportForestSvg}
        clearRuns={vi.fn()}
      />
    );
    fireEvent.click(screen.getByTestId("btn-export-forest-svg"));
    expect(onExportForestSvg).toHaveBeenCalledTimes(1);
  });

  it("C20: outcome_selector 下拉切换 outcome → OutcomeArmInputs 重新渲染对应该 type", () => {
    const outcomes = sampleOutcomes(2);
    const initial: Partial<AnalysisMetaPageProps> = {
      outcomes,
      selectedOutcomeId: "o1",
      armsByOutcome: {
        o1: makeBinaryArms(10, 50, 15, 60),
        o2: makeContinuousArms(10.5, 2.3, 50, 12.1, 3.2, 60),
      },
    };
    const { rerender } = render(
      <AnalysisMetaPage
        outcomes={initial.outcomes!}
        selectedOutcomeId={initial.selectedOutcomeId}
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{}}
        onAddStudy={vi.fn()}
        onDeleteStudy={vi.fn()}
        armsByOutcome={initial.armsByOutcome!}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{}}
        onRunMeta={vi.fn()}
        onExportForestSvg={vi.fn()}
        clearRuns={vi.fn()}
      />
    );
    expect(screen.getByTestId("events-1")).toBeTruthy();
    rerender(
      <AnalysisMetaPage
        outcomes={initial.outcomes!}
        selectedOutcomeId="o2"
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{}}
        onAddStudy={vi.fn()}
        onDeleteStudy={vi.fn()}
        armsByOutcome={initial.armsByOutcome!}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{}}
        onRunMeta={vi.fn()}
        onExportForestSvg={vi.fn()}
        clearRuns={vi.fn()}
      />
    );
    expect(screen.queryByTestId("events-1")).toBeFalsy();
    expect(screen.getByTestId("mean-1")).toBeTruthy();
  });

  it("C21: btn-clear-runs → clearRuns callback 触发", () => {
    const clearRuns = vi.fn();
    render(
      <AnalysisMetaPage
        outcomes={sampleOutcomes(1)}
        selectedOutcomeId="o1"
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{}}
        onAddStudy={vi.fn()}
        onDeleteStudy={vi.fn()}
        armsByOutcome={{ o1: makeBinaryArms(10, 50, 15, 60) }}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{ o1: sampleMetaResult() }}
        onRunMeta={vi.fn()}
        onExportForestSvg={vi.fn()}
        clearRuns={clearRuns}
      />
    );
    fireEvent.click(screen.getByTestId("btn-clear-runs"));
    expect(clearRuns).toHaveBeenCalledTimes(1);
  });

  it("C22: 若 outcome 无 arms data → btn-run-meta disabled with tooltip need_at_least_2_studies", () => {
    renderPage({
      outcomes: sampleOutcomes(1),
      selectedOutcomeId: "o1",
      studiesByOutcome: {},
      armsByOutcome: {},
    });
    const btn = screen.getByTestId("btn-run-meta") as HTMLButtonElement;
    expect(btn.disabled).toBe(true);
    const tip = btn.getAttribute("title") ?? "";
    expect(tip.length).toBeGreaterThan(0);
  });

  it("C23: time_point optional 输入存在", () => {
    renderPage({ outcomes: [] });
    fireEvent.click(screen.getByTestId("btn-add-outcome"));
    expect(screen.getByTestId("dialog-outcome-time_point")).toBeTruthy();
  });

  it("C24: description textarea 存在", () => {
    renderPage({ outcomes: [] });
    fireEvent.click(screen.getByTestId("btn-add-outcome"));
    expect(screen.getByTestId("dialog-outcome-description")).toBeTruthy();
  });

  it("C25: outcome list keyed by id 稳定 not reorder on select（按 id 顺序 o1,o2,o3 不随 selected 变化）", () => {
    const { rerender } = render(
      <AnalysisMetaPage
        outcomes={sampleOutcomes(3)}
        selectedOutcomeId="o1"
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{}}
        onAddStudy={vi.fn()}
        onDeleteStudy={vi.fn()}
        armsByOutcome={{}}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{}}
        onRunMeta={vi.fn()}
        onExportForestSvg={vi.fn()}
        clearRuns={vi.fn()}
      />
    );
    const order1 = ["outcome-card-o1", "outcome-card-o2", "outcome-card-o3"].map((id) =>
      screen.getByTestId(id).getAttribute("data-order")
    );
    rerender(
      <AnalysisMetaPage
        outcomes={sampleOutcomes(3)}
        selectedOutcomeId="o3"
        onSelectOutcome={vi.fn()}
        onDefineOutcome={vi.fn()}
        studiesByOutcome={{}}
        onAddStudy={vi.fn()}
        onDeleteStudy={vi.fn()}
        armsByOutcome={{}}
        onArmsChange={vi.fn()}
        analysisModel="random_dl"
        onAnalysisModelChange={vi.fn()}
        runResultByOutcome={{}}
        onRunMeta={vi.fn()}
        onExportForestSvg={vi.fn()}
        clearRuns={vi.fn()}
      />
    );
    const order2 = ["outcome-card-o1", "outcome-card-o2", "outcome-card-o3"].map((id) =>
      screen.getByTestId(id).getAttribute("data-order")
    );
    expect(order1).toEqual(order2);
  });
});
