import React, { useMemo, useState } from "react";
import type { HistoryPayload } from "./BenchDashboardSummary";

export const BenchDashboardCommitCompare: React.FC<{ history: HistoryPayload }> = ({ history }) => {
  const entries = history.entries || [];
  const [a, setA] = useState(Math.max(0, entries.length - 2));
  const [b, setB] = useState(Math.max(0, entries.length - 1));
  const ea = entries[a], eb = entries[b];
  const sizes = ["n500","n1000","n2000","n10000","n50000"];
  const diffs = useMemo(() => sizes.map(sz => {
    const av = ea?.slo[sz]?.median_s ?? 0, bv = eb?.slo[sz]?.median_s ?? 0;
    const pct = av > 0 ? (bv - av) / av * 100 : 0;
    return { sz, av, bv, pct };
  }), [ea, eb]);
  const anyHard = (ea?.alerts ?? []).concat(eb?.alerts ?? []).some(x => x.severity === "HARD_BLOCK");
  return (
    <div className="w-full p-4">
      {anyHard && (
        <div className="mb-3 p-3 rounded bg-red-50 border border-red-200 text-red-700 text-sm font-semibold">⚠ HARD_BLOCK detected in selected commits</div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-3">
        <label className="block text-sm">
          <span className="text-slate-500">Base commit (A): </span>
          <select className="mt-1 w-full border border-slate-200 rounded p-2 bg-white" value={a} onChange={e=>setA(Number(e.target.value))}>
            {entries.map((e,i)=><option key={i} value={i}>[{i}] {e.sha} — {e.commit_msg.slice(0,60)}</option>)}
          </select>
        </label>
        <label className="block text-sm">
          <span className="text-slate-500">Head commit (B): </span>
          <select className="mt-1 w-full border border-slate-200 rounded p-2 bg-white" value={b} onChange={e=>setB(Number(e.target.value))}>
            {entries.map((e,i)=><option key={i} value={i}>[{i}] {e.sha} — {e.commit_msg.slice(0,60)}</option>)}
          </select>
        </label>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
        {diffs.map(d => {
          const color = d.pct > 0 ? "#dc2626" : d.pct < 0 ? "#10b981" : "#334155";
          const barW = Math.min(Math.abs(d.pct), 50);
          return (
            <div key={d.sz} className="flex items-center gap-3 text-sm">
              <div className="w-20 font-medium text-slate-600">{d.sz}</div>
              <div className="w-32 text-right tabular-nums text-slate-500">{d.av.toFixed(2)}s → {d.bv.toFixed(2)}s</div>
              <div className="flex-1 h-5 bg-slate-100 rounded relative overflow-hidden">
                <div className="h-full" style={{ width: `${barW}%`, backgroundColor: color, marginLeft: d.pct >= 0 ? "50%" : `${50 - barW}%` }} />
              </div>
              <div className="w-20 text-right font-semibold tabular-nums" style={{ color }}>{d.pct >= 0 ? "+" : ""}{d.pct.toFixed(1)}%</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
export default BenchDashboardCommitCompare;
