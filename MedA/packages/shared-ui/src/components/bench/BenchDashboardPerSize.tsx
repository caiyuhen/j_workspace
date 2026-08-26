import React, { useState } from "react";
import type { HistoryPayload } from "./BenchDashboardSummary";

export const BenchDashboardPerSize: React.FC<{ history: HistoryPayload }> = ({ history }) => {
  const [size, setSize] = useState<"n500"|"n1000"|"n2000"|"n10000"|"n50000">("n10000");
  const [window, setWindow] = useState<7|30|60>(7);
  const entries = (history.entries || []).slice(-(window * 10));
  const w = 860, h = 260, padL = 40, padR = 16, padT = 16, padB = 28;
  const iw = w - padL - padR, ih = h - padT - padB;
  const target_s = { n500: 1.0, n1000: 1.5, n2000: 3.0, n10000: 9.6, n50000: 45.0 }[size];
  const maxY = target_s * 1.5;
  const n = Math.max(entries.length, 1);
  const xFor = (i: number) => padL + (iw * i) / Math.max(n - 1, 1);
  const yFor = (v: number) => padT + ih * (1 - Math.min(v, maxY) / maxY);
  return (
    <div className="w-full p-4">
      <div className="flex flex-wrap gap-2 mb-3">
        {(["n500","n1000","n2000","n10000","n50000"] as const).map(s => (
          <button key={s} onClick={() => setSize(s)}
            className={`px-3 py-1.5 text-sm rounded-md border ${size===s?"bg-slate-800 text-white border-slate-800":"bg-white text-slate-600 border-slate-200"}`}>{s}</button>
        ))}
        <div className="flex-1"/>
        {([7,30,60] as const).map(wd => (
          <button key={wd} onClick={() => setWindow(wd)}
            className={`px-3 py-1.5 text-sm rounded-md border ${window===wd?"bg-indigo-600 text-white border-indigo-600":"bg-white text-slate-600 border-slate-200"}`}>{wd}d</button>
        ))}
      </div>
      <div className="rounded-lg border border-slate-200 bg-white p-3">
        <div className="text-sm text-slate-600 mb-2">{size} · p50 median (blue) / p95 (orange dashed) / target (red dashed)</div>
        <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto">
          <line x1={padL} y1={padT} x2={padL} y2={padT+ih} stroke="#94a3b8"/>
          <line x1={padL} y1={padT+ih} x2={padL+iw} y2={padT+ih} stroke="#94a3b8"/>
          <line x1={padL} y1={yFor(target_s)} x2={padL+iw} y2={yFor(target_s)} stroke="#dc2626" strokeDasharray="5 5"/>
          <polyline points={entries.map((e,i)=>`${xFor(i)},${yFor(e.slo?.[size]?.median_s ?? 0)}`).join(" ")} fill="none" stroke="#2563eb" strokeWidth={2}/>
          <polyline points={entries.map((e,i)=>`${xFor(i)},${yFor(e.slo?.[size]?.p95_s ?? 0)}`).join(" ")} fill="none" stroke="#f97316" strokeDasharray="6 3" strokeWidth={2}/>
        </svg>
      </div>
    </div>
  );
};
export default BenchDashboardPerSize;
