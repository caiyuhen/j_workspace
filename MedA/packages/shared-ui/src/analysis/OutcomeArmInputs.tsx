import React from "react";

export type OutcomeType = "binary" | "continuous";
export type BinaryMeasure = "RR" | "OR" | "RD";
export type ContinuousMeasure = "MD" | "SMD";

export type ArmInputsValue =
  | {
      outcome_type: "binary";
      measure: BinaryMeasure;
      events_1: number;
      n_1: number;
      events_2: number;
      n_2: number;
    }
  | {
      outcome_type: "continuous";
      measure: ContinuousMeasure;
      mean_1: number;
      sd_1: number;
      n_1: number;
      mean_2: number;
      sd_2: number;
      n_2: number;
    };

export interface OutcomeArmInputsProps {
  value: ArmInputsValue;
  onChange: (next: ArmInputsValue) => void;
}

const inputStyle: React.CSSProperties = {
  padding: "5px 9px",
  border: "1px solid #d1d5db",
  borderRadius: "5px",
  fontSize: "13px",
  width: "110px",
};

const labelStyle: React.CSSProperties = {
  fontSize: "12px",
  color: "#374151",
  fontWeight: 600,
  marginBottom: "3px",
  display: "block",
};

const colStyle: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  gap: "2px",
};

const warnStyle: React.CSSProperties = {
  marginTop: "6px",
  padding: "6px 10px",
  background: "#fef2f2",
  color: "#b91c1c",
  border: "1px solid #fecaca",
  borderRadius: "5px",
  fontSize: "12px",
};

export const OutcomeArmInputs: React.FC<OutcomeArmInputsProps> = ({ value, onChange }) => {
  if (value.outcome_type === "binary") {
    const hasWarn =
      value.events_1 > value.n_1 || value.events_2 > value.n_2;
    const setNum = (key: "events_1" | "n_1" | "events_2" | "n_2", str: string) => {
      const num = Number(str);
      const safe = isNaN(num) ? 0 : num;
      onChange({ ...value, [key]: safe });
    };
    const setMeasure = (m: string) => {
      const mm = (m === "RR" || m === "OR" || m === "RD") ? m as BinaryMeasure : "RR";
      onChange({ ...value, measure: mm });
    };
    return (
      <div data-testid="arm-inputs-root" style={{ padding: "8px 0" }}>
        <div style={{ marginBottom: "10px" }}>
          <label style={labelStyle}>指标度量 Measure</label>
          <select
            data-testid="measure-selector"
            value={value.measure}
            onChange={(e) => setMeasure(e.target.value)}
            style={{ ...inputStyle, width: "140px" }}
          >
            <option value="RR">RR - 相对风险</option>
            <option value="OR">OR - 比值比</option>
            <option value="RD">RD - 风险差</option>
          </select>
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
          <div style={colStyle}>
            <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "4px", color: "#1f2937" }}>
              Arm 1 (干预组)
            </div>
            <label style={labelStyle}>Events 事件数</label>
            <input
              data-testid="events-1"
              type="number"
              value={value.events_1}
              onChange={(e) => setNum("events_1", e.target.value)}
              style={inputStyle}
            />
            <label style={{ ...labelStyle, marginTop: "6px" }}>N 总人数</label>
            <input
              data-testid="n-1"
              type="number"
              value={value.n_1}
              onChange={(e) => setNum("n_1", e.target.value)}
              style={inputStyle}
            />
          </div>
          <div style={colStyle}>
            <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "4px", color: "#1f2937" }}>
              Arm 2 (对照组)
            </div>
            <label style={labelStyle}>Events 事件数</label>
            <input
              data-testid="events-2"
              type="number"
              value={value.events_2}
              onChange={(e) => setNum("events_2", e.target.value)}
              style={inputStyle}
            />
            <label style={{ ...labelStyle, marginTop: "6px" }}>N 总人数</label>
            <input
              data-testid="n-2"
              type="number"
              value={value.n_2}
              onChange={(e) => setNum("n_2", e.target.value)}
              style={inputStyle}
            />
          </div>
        </div>
        {hasWarn && (
          <div data-testid="events-gt-n-warning" style={warnStyle}>
            ⚠ 事件数(Events)不能大于总人数(N)
          </div>
        )}
      </div>
    );
  }

  const hasSdWarn =
    value.sd_1 <= 0 || value.sd_2 <= 0 || value.n_1 < 2 || value.n_2 < 2;
  const setNum = (
    key: "mean_1" | "sd_1" | "n_1" | "mean_2" | "sd_2" | "n_2",
    str: string
  ) => {
    const num = Number(str);
    const safe = isNaN(num) ? 0 : num;
    onChange({ ...value, [key]: safe });
  };
  const setMeasure = (m: string) => {
    const mm = (m === "MD" || m === "SMD") ? m as ContinuousMeasure : "MD";
    onChange({ ...value, measure: mm });
  };
  return (
    <div data-testid="arm-inputs-root" style={{ padding: "8px 0" }}>
      <div style={{ marginBottom: "10px" }}>
        <label style={labelStyle}>指标度量 Measure</label>
        <select
          data-testid="measure-selector"
          value={value.measure}
          onChange={(e) => setMeasure(e.target.value)}
          style={{ ...inputStyle, width: "180px" }}
        >
          <option value="MD">MD - 均数差</option>
          <option value="SMD">SMD - 标准化均数差</option>
        </select>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "14px" }}>
        <div style={colStyle}>
          <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "4px", color: "#1f2937" }}>
            Arm 1 (干预组)
          </div>
          <label style={labelStyle}>Mean 均值</label>
          <input
            data-testid="mean-1"
            type="number"
            step="0.01"
            value={value.mean_1}
            onChange={(e) => setNum("mean_1", e.target.value)}
            style={inputStyle}
          />
          <label style={{ ...labelStyle, marginTop: "6px" }}>SD 标准差</label>
          <input
            data-testid="sd-1"
            type="number"
            step="0.01"
            value={value.sd_1}
            onChange={(e) => setNum("sd_1", e.target.value)}
            style={inputStyle}
          />
          <label style={{ ...labelStyle, marginTop: "6px" }}>N 样本量</label>
          <input
            data-testid="n-1"
            type="number"
            value={value.n_1}
            onChange={(e) => setNum("n_1", e.target.value)}
            style={inputStyle}
          />
        </div>
        <div style={colStyle}>
          <div style={{ fontSize: "13px", fontWeight: 700, marginBottom: "4px", color: "#1f2937" }}>
            Arm 2 (对照组)
          </div>
          <label style={labelStyle}>Mean 均值</label>
          <input
            data-testid="mean-2"
            type="number"
            step="0.01"
            value={value.mean_2}
            onChange={(e) => setNum("mean_2", e.target.value)}
            style={inputStyle}
          />
          <label style={{ ...labelStyle, marginTop: "6px" }}>SD 标准差</label>
          <input
            data-testid="sd-2"
            type="number"
            step="0.01"
            value={value.sd_2}
            onChange={(e) => setNum("sd_2", e.target.value)}
            style={inputStyle}
          />
          <label style={{ ...labelStyle, marginTop: "6px" }}>N 样本量</label>
          <input
            data-testid="n-2"
            type="number"
            value={value.n_2}
            onChange={(e) => setNum("n_2", e.target.value)}
            style={inputStyle}
          />
        </div>
      </div>
      {hasSdWarn && (
        <div data-testid="sd-nonpositive-warning" style={warnStyle}>
          ⚠ SD 必须大于 0，且样本量 N 必须 ≥ 2
        </div>
      )}
    </div>
  );
};
