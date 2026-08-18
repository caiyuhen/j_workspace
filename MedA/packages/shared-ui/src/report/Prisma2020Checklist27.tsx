import React from "react";
import type { Prisma2020Checklist } from "@meda/shared-sdk";

const PRISMA_27_LABELS: { idx: 1|2|3|4|5|6|7|8|9|10|11|12|13|14|15|16|17|18|19|20|21|22|23|24|25|26|27; title: string }[] = [
  { idx: 1, title: "Title" },
  { idx: 2, title: "Abstract" },
  { idx: 3, title: "Rationale" },
  { idx: 4, title: "Objectives" },
  { idx: 5, title: "Protocol registration" },
  { idx: 6, title: "Eligibility criteria" },
  { idx: 7, title: "Information sources" },
  { idx: 8, title: "Search strategy" },
  { idx: 9, title: "Selection process" },
  { idx: 10, title: "Data collection process" },
  { idx: 11, title: "Data items" },
  { idx: 12, title: "Risk of bias" },
  { idx: 13, title: "Effect measures" },
  { idx: 14, title: "Synthesis methods" },
  { idx: 15, title: "Certainty assessment" },
  { idx: 16, title: "Study selection" },
  { idx: 17, title: "Study characteristics" },
  { idx: 18, title: "Risk of bias results" },
  { idx: 19, title: "Results individual studies" },
  { idx: 20, title: "Synthesis results" },
  { idx: 21, title: "Certainty of evidence" },
  { idx: 22, title: "Registration" },
  { idx: 23, title: "Protocol amendments" },
  { idx: 24, title: "Support" },
  { idx: 25, title: "Conflicts" },
  { idx: 26, title: "Data availability" },
  { idx: 27, title: "Ethics" },
] as unknown as typeof PRISMA_27_LABELS;

export function Prisma2020Checklist27({
  value,
  onChange,
}: {
  value: Prisma2020Checklist;
  onChange: (next: Prisma2020Checklist) => void;
}): JSX.Element {
  const checkedCount = PRISMA_27_LABELS.reduce((acc, l) => acc + ((value as any)[`item_${l.idx}`] ? 1 : 0), 0);
  const pct = (checkedCount / 27) * 100;
  return (
    <div className="prisma-2020-checklist" aria-label="PRISMA 2020 Checklist 27">
      <style>{`
        .prisma-2020-checklist .pcl-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem; font-family: system-ui; }
        .prisma-2020-checklist .pcl-progress { width: 100%; height: .5rem; background:#eef2f7; border-radius: .25rem; overflow:hidden; margin: .25rem 0 .8rem; }
        .prisma-2020-checklist .pcl-bar { background:#0ea5e9; height:100%; }
        .prisma-2020-checklist .pcl-grid { display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap: .3rem .7rem; }
        .prisma-2020-checklist .pcl-item { display: flex; align-items: flex-start; gap: .35rem; font-size: .85rem; }
      `}</style>
      <div className="pcl-header">
        <strong>PRISMA 2020 Checklist</strong>
        <span style={{ fontSize: ".8rem", color: "#475569" }}>{checkedCount}/27 ({pct.toFixed(1)}%)</span>
      </div>
      <div className="pcl-progress"><div className="pcl-bar" style={{ width: `${pct}%` }} /></div>
      <div className="pcl-grid">
        {PRISMA_27_LABELS.map(l => {
          const key = `item_${l.idx}` as const;
          const chk = !!(value as any)[key];
          return (
            <label className="pcl-item" key={l.idx} title={l.title}>
              <input
                type="checkbox"
                checked={chk}
                disabled={!!value.locked}
                onChange={() => {
                  const next: Prisma2020Checklist = { ...value, [key]: !chk } as Prisma2020Checklist;
                  onChange(next);
                }}
              />
              <span>{String(l.idx).padStart(2,"0")}. {l.title}</span>
            </label>
          );
        })}
      </div>
    </div>
  );
}
