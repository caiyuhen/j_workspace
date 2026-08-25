import React, { useMemo, useState } from "react";
import type { HistoryPayload } from "./BenchDashboardSummary";

export const BenchDashboardAlertLog: React.FC<{ history: HistoryPayload }> = ({ history }) => {
  const [filter, setFilter] = useState<"ALL"|"HARD_BLOCK"|"WARN"|"PASS">("ALL");
  const rows = useMemo(() => {
    const r: Array<{ date: string; sha: string; severity: string; size: string; message: string }> = [];
    (history.entries || []).forEach(e => {
      (e.alerts || []).forEach(a => {
        if (filter === "ALL" || a.severity === filter) {
          r.push({ date: e.date.slice(0,10), sha: e.sha, severity: a.severity, size: a.size, message: a.message });
        }
      });
    });
    return r.sort((a,b) => (b.date > a.date ? 1 : -1));
  }, [history, filter]);
  const sevColor: Record<string,string> = { HARD_BLOCK: "#ef4444", WARN: "#f59e0b", PASS: "#10b981" };
  return (
    <div className="w-full p-4">
      <div className="flex flex-wrap gap-2 mb-3">
        {(["ALL","HARD_BLOCK","WARN","PASS"] as const).map(f => (
          <button key={f} onClick={() => setFilter(f)}
            className={`px-3 py-1.5 text-sm rounded-md border ${filter===f?"bg-slate-800 text-white border-slate-800":"bg-white text-slate-600 border-slate-200"}`}>{f}</button>
        ))}
        <div className="flex-1 text-right text-sm text-slate-500 self-center">{rows.length} entries</div>
      </div>
      <div className="rounded-lg border border-slate-200 bg-white divide-y divide-slate-100">
        {rows.length === 0 && <div className="p-8 text-center text-slate-400 italic">No alerts — all green ✨</div>}
        {rows.map((r, i) => (
          <div key={i} className="p-3 flex items-center gap-3 text-sm">
            <span className="px-2 py-0.5 rounded text-white text-xs font-semibold" style={{ backgroundColor: sevColor[r.severity] }}>{r.severity}</span>
            <span className="text-slate-400 tabular-nums w-24">{r.date}</span>
            <code className="bg-slate-100 px-2 py-0.5 rounded text-xs w-20 overflow-hidden">{r.sha}</code>
            <span className="font-mono w-20">{r.size}</span>
            <span className="text-slate-700 flex-1 truncate">{r.message}</span>
          </div>
        ))}
      </div>
    </div>
  );
};
export default BenchDashboardAlertLog;
