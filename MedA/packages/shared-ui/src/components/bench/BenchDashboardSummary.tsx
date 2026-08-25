import React from "react";

export interface BenchEntry {
  sha: string; commit_msg: string; branch: string; date: string;
  python?: string; os?: string;
  slo: Record<string, { target_s: number; median_s: number; p95_s: number; status: string }>;
  vs_baseline_v0110_speedup_x: { n2000: number; n10000: number; n50000: number };
  alerts: Array<{ severity: string; size: string; message: string }>;
}
export interface HistoryPayload { generated_at: string; window_days: number; entries: BenchEntry[]; }

const SIZE_COLORS: Record<string, string> = {
  n500: "#2563eb", n1000: "#059669", n2000: "#d97706", n10000: "#7c3aed", n50000: "#dc2626",
};
const SIZE_LABELS: Record<string, string> = {
  n500: "N=500", n1000: "N=1k", n2000: "N=2k", n10000: "N=10k", n50000: "N=50k",
};

const SEVERITY_COLOR: Record<string, string> = { PASS: "#10b981", WARN: "#f59e0b", HARD_BLOCK: "#ef4444" };

export const BenchDashboardSummary: React.FC<{ history: HistoryPayload }> = ({ history }) => {
  const entries = history.entries || [];
  const latest = entries[entries.length - 1];
  const kpis = latest ? [
    { label: "Latest N=2k", value: `${latest.slo.n2000?.median_s.toFixed(2) ?? "—"}s`, target: "SLO 3.0s", color: SEVERITY_COLOR[latest.slo.n2000?.status || "PASS"] },
    { label: "N=10k (AC4)", value: `${latest.slo.n10000?.median_s.toFixed(2) ?? "—"}s`, target: "SLO 9.6s", color: SEVERITY_COLOR[latest.slo.n10000?.status || "PASS"] },
    { label: "N=50k (AC5)", value: `${latest.slo.n50000?.median_s.toFixed(2) ?? "—"}s`, target: "SLO 45.0s", color: SEVERITY_COLOR[latest.slo.n50000?.status || "PASS"] },
    { label: "Active Alerts", value: String(latest.alerts?.length ?? 0), target: `${entries.length} runs in window`, color: (latest.alerts?.length ?? 0) > 0 ? "#ef4444" : "#10b981" },
  ] : [];

  const width = 860, height = 260, padL = 40, padR = 16, padT = 16, padB = 28;
  const innerW = width - padL - padR, innerH = height - padT - padB;
  const sizes = ["n500","n1000","n2000","n10000","n50000"];
  const maxY = 55;
  const n = Math.max(entries.length, 1);
  const xFor = (i: number) => padL + (innerW * i) / Math.max(n - 1, 1);
  const yFor = (s: number) => padT + innerH * (1 - Math.min(s, maxY) / maxY);

  return (
    <div className="w-full p-4">
      <h2 className="text-xl font-semibold mb-3 text-slate-800">Summary · {entries.length} runs · window {history.window_days} days</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mb-4">
        {kpis.map((k, i) => (
          <div key={i} className="rounded-lg border border-slate-200 bg-white p-3 shadow-sm">
            <div className="text-xs text-slate-500">{k.label}</div>
            <div className="text-2xl font-bold" style={{ color: k.color }}>{k.value}</div>
            <div className="text-xs text-slate-400 mt-1">{k.target}</div>
          </div>
        ))}
        {kpis.length === 0 && <div className="col-span-4 text-slate-400 italic">No data yet — wait for CI bench runs.</div>}
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <div className="text-sm font-medium text-slate-600 mb-2">7d Median (s) by Size · inline SVG polyline</div>
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
          <line x1={padL} y1={padT} x2={padL} y2={padT + innerH} stroke="#94a3b8" />
          <line x1={padL} y1={padT + innerH} x2={padL + innerW} y2={padT + innerH} stroke="#94a3b8" />
          {[0, 15, 30, 45, 55].map(v => (
            <text key={v} x={padL - 6} y={yFor(v) + 4} textAnchor="end" fontSize={10} fill="#64748b">{v}s</text>
          ))}
          <line x1={padL} y1={yFor(9.6)} x2={padL + innerW} y2={yFor(9.6)} stroke="#7c3aed" strokeDasharray="4 4" strokeWidth={1} opacity={0.5}/>
          <line x1={padL} y1={yFor(45)} x2={padL + innerW} y2={yFor(45)} stroke="#dc2626" strokeDasharray="4 4" strokeWidth={1} opacity={0.5}/>
          {sizes.map(sz => {
            const pts = entries.map((e, i) => `${xFor(i)},${yFor(e.slo[sz]?.median_s ?? 0)}`).join(" ");
            return <polyline key={sz} points={pts} fill="none" stroke={SIZE_COLORS[sz]} strokeWidth={2}/>;
          })}
          {sizes.map((sz, i) => (
            <g key={sz}>
              <rect x={padL + 4 + i * 80} y={padT + 4} width={10} height={10} fill={SIZE_COLORS[sz]}/>
              <text x={padL + 18 + i * 80} y={padT + 13} fontSize={10} fill="#334155">{SIZE_LABELS[sz]}</text>
            </g>
          ))}
        </svg>
      </div>
    </div>
  );
};

export default BenchDashboardSummary;
