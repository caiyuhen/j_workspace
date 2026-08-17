import React, { useMemo, useState } from "react";
import {
  OutcomeArmInputs,
  type OutcomeType,
  type BinaryMeasure,
  type ContinuousMeasure,
  type ArmInputsValue,
} from "./OutcomeArmInputs";
import {
  ForestPlotW83,
  type ForestStudyRow,
} from "../charts/ForestPlotW83";

export interface OutcomeDefinition {
  id: string;
  name: string;
  outcome_type: OutcomeType;
  measure: BinaryMeasure | ContinuousMeasure;
  description?: string;
  time_point?: string;
}

export interface MetaRunResult {
  outcome_id: string;
  analysis_model: string;
  pooled: {
    effect: number;
    ci_low: number;
    ci_high: number;
    p_value?: number;
  };
  heterogeneity: {
    I2_pct: number;
    Q?: number;
    df?: number;
    p_value?: number;
  };
  studies: ForestStudyRow[];
}

interface StudyItem {
  study_id: string;
  study_label: string;
}

export type AnalysisModel = "fixed_iv" | "fixed_mh" | "random_dl";

export interface AnalysisMetaPageProps {
  outcomes: OutcomeDefinition[];
  selectedOutcomeId: string | undefined;
  onSelectOutcome: (id: string) => void;
  onDefineOutcome: (payload: Omit<OutcomeDefinition, "id">) => void;
  studiesByOutcome: Record<string, StudyItem[]>;
  onAddStudy: (outcomeId: string) => void;
  onDeleteStudy: (outcomeId: string, studyId: string) => void;
  armsByOutcome: Record<string, ArmInputsValue>;
  onArmsChange: (outcomeId: string, v: ArmInputsValue) => void;
  analysisModel: AnalysisModel;
  onAnalysisModelChange: (m: AnalysisModel) => void;
  runResultByOutcome: Record<string, MetaRunResult>;
  onRunMeta: (payload: { outcome_id: string; analysis_model: string }) => void;
  onExportForestSvg: () => void;
  clearRuns: () => void;
}

const cardStyle = (selected: boolean): React.CSSProperties => ({
  padding: "10px 12px",
  border: selected ? "2px solid #2563eb" : "1px solid #e5e7eb",
  borderRadius: "8px",
  background: selected ? "#eff6ff" : "#fff",
  marginBottom: "8px",
  cursor: "pointer",
});

const sectionHeader: React.CSSProperties = {
  fontSize: "14px",
  fontWeight: 700,
  color: "#111827",
  marginBottom: "10px",
};

const btnPrimary = (disabled = false): React.CSSProperties => ({
  padding: "7px 14px",
  background: disabled ? "#d1d5db" : "#2563eb",
  color: "#fff",
  border: "none",
  borderRadius: "6px",
  fontSize: "13px",
  fontWeight: 600,
  cursor: disabled ? "not-allowed" : "pointer",
});

const btnGhost = (disabled = false): React.CSSProperties => ({
  padding: "5px 10px",
  background: disabled ? "#f3f4f6" : "#fff",
  color: disabled ? "#9ca3af" : "#374151",
  border: "1px solid #d1d5db",
  borderRadius: "5px",
  fontSize: "12px",
  cursor: disabled ? "not-allowed" : "pointer",
});

export const AnalysisMetaPage: React.FC<AnalysisMetaPageProps> = ({
  outcomes,
  selectedOutcomeId,
  onSelectOutcome,
  onDefineOutcome,
  studiesByOutcome,
  onAddStudy,
  onDeleteStudy,
  armsByOutcome,
  onArmsChange,
  analysisModel,
  onAnalysisModelChange,
  runResultByOutcome,
  onRunMeta,
  onExportForestSvg,
  clearRuns,
}) => {
  const [dialogOpen, setDialogOpen] = useState<boolean>(false);
  const [dlgName, setDlgName] = useState<string>("");
  const [dlgType, setDlgType] = useState<OutcomeType>("binary");
  const [dlgMeasureBin, setDlgMeasureBin] = useState<BinaryMeasure>("RR");
  const [dlgMeasureCont, setDlgMeasureCont] = useState<ContinuousMeasure>("MD");
  const [dlgDesc, setDlgDesc] = useState<string>("");
  const [dlgTp, setDlgTp] = useState<string>("");

  const selectedOutcome = useMemo(
    () => outcomes.find((o) => o.id === selectedOutcomeId),
    [outcomes, selectedOutcomeId]
  );
  const selStudies = selectedOutcome
    ? studiesByOutcome[selectedOutcome.id] ?? []
    : [];
  const selArms = selectedOutcome ? armsByOutcome[selectedOutcome.id] : undefined;
  const selResult = selectedOutcome
    ? runResultByOutcome[selectedOutcome.id]
    : undefined;

  const K = selStudies.length;
  const canRunMeta = K >= 2 && !!selArms;

  const openDialog = () => {
    setDlgName("");
    setDlgType("binary");
    setDlgMeasureBin("RR");
    setDlgMeasureCont("MD");
    setDlgDesc("");
    setDlgTp("");
    setDialogOpen(true);
  };

  const saveDialog = () => {
    const measure =
      dlgType === "binary" ? dlgMeasureBin : dlgMeasureCont;
    const payload: Omit<OutcomeDefinition, "id"> = {
      name: dlgName,
      outcome_type: dlgType,
      measure,
      description: dlgDesc || undefined,
      time_point: dlgTp || undefined,
    };
    onDefineOutcome(payload);
    setDialogOpen(false);
  };

  const measureOptions = dlgType === "binary"
    ? (["RR", "OR", "RD"] as BinaryMeasure[])
    : (["MD", "SMD"] as ContinuousMeasure[]);

  return (
    <div
      style={{
        fontFamily: "sans-serif",
        padding: "16px",
        maxWidth: "1200px",
        margin: "0 auto",
      }}
    >
      <div
        data-testid="page-title-analysis-rendering"
        style={{ marginBottom: "16px" }}
      >
        <h2 style={{ margin: 0, fontSize: "20px", color: "#111827" }}>
          元分析 (Meta-Analysis) 模块
        </h2>
        <div style={{ fontSize: "13px", color: "#6b7280", marginTop: "4px" }}>
          结局定义 → 研究数据 → 分析模型 → 森林图
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "320px 1fr", gap: "16px" }}>
        <div>
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "10px",
            }}
          >
            <div style={sectionHeader}>结局 Outcomes</div>
            <button
              data-testid="btn-add-outcome"
              onClick={openDialog}
              style={btnGhost(false)}
            >
              + 新增结局
            </button>
          </div>

          {outcomes.length === 0 && (
            <div
              data-testid="no-outcomes-yet"
              style={{
                padding: "16px",
                textAlign: "center",
                color: "#6b7280",
                fontSize: "13px",
                border: "1px dashed #d1d5db",
                borderRadius: "8px",
                background: "#f9fafb",
              }}
            >
              📋 尚未定义任何结局，点击右上角 "新增结局" 开始
            </div>
          )}

          {outcomes.map((o, idx) => {
            const selected = o.id === selectedOutcomeId;
            return (
              <div
                key={o.id}
                data-testid={`outcome-card-${o.id}`}
                data-order={idx}
                onClick={() => onSelectOutcome(o.id)}
                className={selected ? "outcome-card-selected" : "outcome-card"}
                style={cardStyle(selected)}
              >
                <div style={{ fontSize: "14px", fontWeight: 700, color: "#111827" }}>
                  {o.name}
                </div>
                <div style={{ fontSize: "12px", color: "#6b7280", marginTop: "3px" }}>
                  {o.outcome_type === "binary" ? "二分类" : "连续型"} ·{" "}
                  {String(o.measure)}
                  {o.time_point ? ` · ${o.time_point}` : ""}
                </div>
                {o.description && (
                  <div
                    style={{
                      fontSize: "12px",
                      color: "#4b5563",
                      marginTop: "4px",
                      lineHeight: 1.4,
                    }}
                  >
                    {o.description}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
          {selectedOutcome ? (
            <>
              <div
                style={{
                  padding: "14px",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  background: "#fff",
                }}
              >
                <div style={sectionHeader}>
                  研究列表 Studies（K = {K}）
                </div>

                <div
                  data-testid="studies-list"
                  style={{
                    border: "1px solid #f3f4f6",
                    borderRadius: "6px",
                    minHeight: "60px",
                    padding: "6px",
                    marginBottom: "8px",
                    background: "#fafafa",
                  }}
                >
                  {selStudies.length === 0 ? (
                    <div
                      style={{
                        padding: "10px",
                        textAlign: "center",
                        color: "#9ca3af",
                        fontSize: "12px",
                      }}
                    >
                      尚未添加研究
                    </div>
                  ) : (
                    selStudies.map((s) => (
                      <div
                        key={s.study_id}
                        data-testid={`study-row-${s.study_id}`}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "space-between",
                          padding: "6px 8px",
                          borderBottom: "1px solid #f3f4f6",
                        }}
                      >
                        <span style={{ fontSize: "13px", color: "#111827" }}>
                          📄 {s.study_label}
                        </span>
                        <button
                          data-testid={`btn-delete-study-${s.study_id}`}
                          onClick={() => onDeleteStudy(selectedOutcome.id, s.study_id)}
                          style={{ ...btnGhost(false), color: "#dc2626", borderColor: "#fecaca" }}
                        >
                          删除
                        </button>
                      </div>
                    ))
                  )}
                </div>

                <button
                  data-testid="btn-add-study"
                  onClick={() => onAddStudy(selectedOutcome.id)}
                  style={btnGhost(false)}
                >
                  + 添加研究
                </button>
              </div>

              <div
                style={{
                  padding: "14px",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  background: "#fff",
                }}
              >
                <div style={sectionHeader}>
                  效应量数据 Arms ({selectedOutcome.outcome_type === "binary" ? "Binary" : "Continuous"})
                </div>
                {selArms ? (
                  <OutcomeArmInputs
                    value={selArms}
                    onChange={(v) => onArmsChange(selectedOutcome.id, v)}
                  />
                ) : (
                  <div
                    style={{
                      padding: "10px",
                      color: "#6b7280",
                      fontSize: "13px",
                    }}
                  >
                    请先设置效应量初始数据
                  </div>
                )}
              </div>

              <div
                style={{
                  padding: "14px",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  background: "#fff",
                }}
              >
                <div style={sectionHeader}>分析模型 Analysis Model</div>
                <div style={{ display: "flex", flexWrap: "wrap", gap: "14px" }}>
                  {(["fixed_iv", "fixed_mh", "random_dl"] as AnalysisModel[]).map((m) => {
                    const label =
                      m === "fixed_iv"
                        ? "Fixed Effect (IV)"
                        : m === "fixed_mh"
                        ? "Fixed Effect (MH)"
                        : "Random Effect (DL)";
                    return (
                      <label
                        key={m}
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "5px",
                          fontSize: "13px",
                          color: "#374151",
                          cursor: "pointer",
                        }}
                      >
                        <input
                          data-testid={`model-radio-${m}`}
                          type="radio"
                          value={m}
                          checked={analysisModel === m}
                          onChange={() => onAnalysisModelChange(m)}
                        />
                        {label}
                      </label>
                    );
                  })}
                </div>

                <div
                  style={{
                    marginTop: "12px",
                    display: "flex",
                    gap: "10px",
                    alignItems: "center",
                    flexWrap: "wrap",
                  }}
                >
                  <button
                    data-testid="btn-run-meta"
                    onClick={() =>
                      onRunMeta({
                        outcome_id: selectedOutcome.id,
                        analysis_model: analysisModel,
                      })
                    }
                    disabled={!canRunMeta}
                    title={
                      canRunMeta
                        ? "运行元分析"
                        : "need_at_least_2_studies: 至少需要 2 条研究数据和效应量输入"
                    }
                    style={btnPrimary(!canRunMeta)}
                  >
                    🔬 运行元分析 Run Meta
                  </button>

                  <button
                    data-testid="btn-clear-runs"
                    onClick={clearRuns}
                    style={btnGhost(false)}
                  >
                    🗑 清空结果
                  </button>

                  <button
                    data-testid="btn-export-forest-svg"
                    onClick={onExportForestSvg}
                    disabled={!selResult}
                    style={btnGhost(!selResult)}
                  >
                    💾 导出森林图 SVG
                  </button>
                </div>
              </div>

              <div
                data-testid="forest-result-wrapper"
                style={{
                  padding: "14px",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                  background: "#fff",
                }}
              >
                <div style={sectionHeader}>森林图 Forest Plot</div>

                {selResult ? (
                  <>
                    <div
                      style={{
                        display: "flex",
                        gap: "20px",
                        marginBottom: "10px",
                        flexWrap: "wrap",
                      }}
                    >
                      <div
                        data-testid="pooled-effect-text"
                        style={{
                          padding: "8px 12px",
                          background: "#ecfdf5",
                          border: "1px solid #a7f3d0",
                          borderRadius: "6px",
                          fontSize: "13px",
                          color: "#065f46",
                          fontWeight: 600,
                        }}
                      >
                        Pooled Effect = {selResult.pooled.effect.toFixed(3)} (95%CI{" "}
                        {selResult.pooled.ci_low.toFixed(3)}-
                        {selResult.pooled.ci_high.toFixed(3)})
                      </div>
                      <div
                        data-testid="heterogeneity-i2"
                        style={{
                          padding: "8px 12px",
                          background: "#fff7ed",
                          border: "1px solid #fed7aa",
                          borderRadius: "6px",
                          fontSize: "13px",
                          color: "#9a3412",
                          fontWeight: 600,
                        }}
                      >
                        Heterogeneity: I² = {selResult.heterogeneity.I2_pct.toFixed(1)}%
                      </div>
                    </div>
                    <ForestPlotW83
                      studies={selResult.studies}
                      result={{
                        pooled: selResult.pooled,
                        heterogeneity: selResult.heterogeneity,
                      }}
                      width={800}
                      height={Math.max(360, 120 + selResult.studies.length * 40)}
                    />
                  </>
                ) : (
                  <ForestPlotW83 studies={[]} result={undefined} />
                )}
              </div>
            </>
          ) : (
            <div
              style={{
                padding: "40px 20px",
                textAlign: "center",
                color: "#6b7280",
                fontSize: "14px",
                border: "1px dashed #d1d5db",
                borderRadius: "8px",
                background: "#f9fafb",
              }}
            >
              ← 请从左侧选择或创建一个结局以开始分析
            </div>
          )}
        </div>
      </div>

      {dialogOpen && (
        <div
          data-testid="dialog-outcome-define"
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 9999,
          }}
          onClick={(e) => {
            if (e.target === e.currentTarget) setDialogOpen(false);
          }}
        >
          <div
            style={{
              background: "#fff",
              borderRadius: "10px",
              padding: "20px",
              width: "480px",
              maxWidth: "92vw",
              boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
            }}
          >
            <div
              style={{
                fontSize: "16px",
                fontWeight: 700,
                marginBottom: "14px",
                color: "#111827",
              }}
            >
              定义新结局 Define Outcome
            </div>

            <div style={{ marginBottom: "10px" }}>
              <label style={sectionHeader}>结局名称 Name *</label>
              <input
                data-testid="dialog-outcome-name"
                value={dlgName}
                onChange={(e) => setDlgName(e.target.value)}
                placeholder="例如：全因死亡率"
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  fontSize: "13px",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ marginBottom: "10px" }}>
              <label style={sectionHeader}>数据类型 Type</label>
              <select
                data-testid="dialog-outcome-type"
                value={dlgType}
                onChange={(e) =>
                  setDlgType(e.target.value as OutcomeType)
                }
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  fontSize: "13px",
                }}
              >
                <option value="binary">二分类 Binary (Events/N)</option>
                <option value="continuous">连续型 Continuous (Mean, SD, N)</option>
              </select>
            </div>

            <div style={{ marginBottom: "10px" }}>
              <label style={sectionHeader}>效应量指标 Measure</label>
              <select
                data-testid="dialog-outcome-measure"
                value={dlgType === "binary" ? dlgMeasureBin : dlgMeasureCont}
                onChange={(e) => {
                  if (dlgType === "binary") {
                    setDlgMeasureBin(e.target.value as BinaryMeasure);
                  } else {
                    setDlgMeasureCont(e.target.value as ContinuousMeasure);
                  }
                }}
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  fontSize: "13px",
                }}
              >
                {measureOptions.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            </div>

            <div style={{ marginBottom: "10px" }}>
              <label style={sectionHeader}>时间点 Time Point (可选)</label>
              <input
                data-testid="dialog-outcome-time_point"
                value={dlgTp}
                onChange={(e) => setDlgTp(e.target.value)}
                placeholder="例如：Week 12, Month 6"
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  fontSize: "13px",
                  boxSizing: "border-box",
                }}
              />
            </div>

            <div style={{ marginBottom: "16px" }}>
              <label style={sectionHeader}>描述 Description</label>
              <textarea
                data-testid="dialog-outcome-description"
                value={dlgDesc}
                onChange={(e) => setDlgDesc(e.target.value)}
                placeholder="结局的详细说明"
                rows={3}
                style={{
                  width: "100%",
                  padding: "7px 10px",
                  border: "1px solid #d1d5db",
                  borderRadius: "6px",
                  fontSize: "13px",
                  boxSizing: "border-box",
                  resize: "vertical",
                  fontFamily: "sans-serif",
                }}
              />
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "flex-end",
                gap: "10px",
              }}
            >
              <button
                data-testid="btn-cancel-outcome"
                onClick={() => setDialogOpen(false)}
                style={btnGhost(false)}
              >
                取消
              </button>
              <button
                data-testid="btn-save-outcome"
                onClick={saveDialog}
                style={btnPrimary(false)}
              >
                💾 保存
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
