from __future__ import annotations
from dataclasses import dataclass

INTERNAL_CSS = """<style>
body { font-family: Georgia, 'Times New Roman', serif; color:#111; line-height:1.55; max-width:900px; margin:2rem auto; padding:0 1rem; }
h1,h2,h3 { font-family: system-ui, -apple-system, sans-serif; }
h1 { font-size:1.9rem; } h2 { font-size:1.3rem; border-bottom: 1px solid #e5e7eb; padding-bottom:.3rem; margin-top:2rem;}
table.sof-table { border-collapse: collapse; width: 100%; font-size: 0.92rem; margin: 1rem 0; }
table.sof-table th, table.sof-table td { border:1px solid #d1d5db; padding: 0.5rem 0.6rem; vertical-align: top; }
table.sof-table th { background-color: #f9fafb; text-align: left; font-family: system-ui; }
.grade-certainty { font-weight: 600; padding: .15rem .5rem; border-radius: .3rem; color: #fff; font-family: system-ui; }
.grade-color-High { background-color: #166534; }
.grade-color-Moderate { background-color: #1d4ed8; }
.grade-color-Low { background-color: #b45309; }
.grade-color-VeryLow { background-color: #7f1d1d; }
.prisma-27-item { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: 0.86rem; }
.section-rule-box { border: 1px solid #e5e7eb; padding: 1rem; border-radius: .5rem; background: #fafafa; margin: 1rem 0; }
</style>
"""

@dataclass(frozen=True, slots=True)
class GradeAssRow:
    outcome_label: str
    certainty: str
    participants_n: int
    studies_k: int
    effect_label: str
    ar_control: str
    ar_intervention: str
    comments: str = ""

@dataclass(frozen=True, slots=True)
class ProjectReportInput:
    project_name: str
    project_id: int
    owner_display: str
    abstract_summary: str
    prisma_checklist_masked_count: int
    prisma_checklist_total_items: int
    grade_rows: list[GradeAssRow]
    forest_svg_content: str = ""

def _render_md(pi: ProjectReportInput) -> str:
    rows_md = []
    rows_md.append(f"| Outcome | Certainty | N (Participants) | k (Studies) | Effect Measure | Absolute Risk (Control) | Absolute Risk (Intervention) | Comments |")
    rows_md.append(f"| --- | --- | ---: | ---: | --- | --- | --- | --- |")
    for r in pi.grade_rows:
        rows_md.append(f"| {r.outcome_label} | {r.certainty} | {r.participants_n} | {r.studies_k} | {r.effect_label} | {r.ar_control} | {r.ar_intervention} | {r.comments} |")
    table_md = "\n".join(rows_md)
    return f"""# {pi.project_name} (SR GRADE Report)

## Summary
- Owner: {pi.owner_display}
- PRISMA 2020 Checklist: {pi.prisma_checklist_masked_count}/{pi.prisma_checklist_total_items} items marked
- Abstract / Background Summary: {pi.abstract_summary}

## Grade Summary of Findings (SoF)

{table_md}

### Forest Plot
{pi.forest_svg_content if pi.forest_svg_content else "_Forest plot not generated yet_"}

## References
- Cochrane GRADE 5 domains + 3 upgrades; 4 levels High / Moderate / Low / VeryLow
- PRISMA 2020 27 items checklist; see attachments for complete items 1-27 mask
"""

def _render_html(pi: ProjectReportInput) -> str:
    trs = "".join(
        f'<tr><td>{r.outcome_label}</td>'
        f'<td><span class="grade-certainty grade-color-{r.certainty}">{r.certainty}</span></td>'
        f'<td style="text-align:right">{r.participants_n}</td>'
        f'<td style="text-align:right">{r.studies_k}</td>'
        f'<td>{r.effect_label}</td><td>{r.ar_control}</td><td>{r.ar_intervention}</td>'
        f'<td>{r.comments or ""}</td></tr>' for r in pi.grade_rows
    )
    body = f"""
<h1>{pi.project_name}</h1>
<div class="section-rule-box">
  <strong>Owner:</strong> {pi.owner_display}<br>
  <strong>PRISMA 2020 Checklist:</strong> {pi.prisma_checklist_masked_count}/{pi.prisma_checklist_total_items} items marked
</div>
<h2>Abstract / Background Summary</h2>
<p>{pi.abstract_summary}</p>
<h2>SoF Table: Summary of Findings (GRADE)</h2>
<table class="sof-table">
<thead><tr><th>Outcome</th><th>Certainty</th><th>N (Participants)</th><th>k (Studies)</th><th>Effect Measure</th><th>AR Control</th><th>AR Intervention</th><th>Comments</th></tr></thead>
<tbody>
{trs}
</tbody></table>
<h2>Forest Plot</h2>
<div class="section-rule-box">{pi.forest_svg_content if pi.forest_svg_content else '<p><em>Forest plot not generated yet.</em></p>'}</div>
<h2>Legend — 4档 GRADE 颜色</h2>
<p>
  <span class="grade-certainty grade-color-High">High (#166534 绿)</span>&nbsp;
  <span class="grade-certainty grade-color-Moderate">Moderate (#1d4ed8 蓝)</span>&nbsp;
  <span class="grade-certainty grade-color-Low">Low (#b45309 橙)</span>&nbsp;
  <span class="grade-certainty grade-color-VeryLow">VeryLow (#7f1d1d 深红)</span>
</p>
"""
    return f"<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">{INTERNAL_CSS}</head><body>{body}</body></html>"

def _render_txt(pi: ProjectReportInput) -> str:
    lines = []
    lines.append(pi.project_name)
    lines.append("=" * len(pi.project_name))
    lines.append("")
    lines.append(f"Owner: {pi.owner_display}")
    lines.append(f"PRISMA 2020 Checklist: {pi.prisma_checklist_masked_count}/{pi.prisma_checklist_total_items} items marked")
    lines.append(f"Abstract: {pi.abstract_summary}")
    lines.append("")
    lines.append("SoF (Summary of Findings)")
    lines.append("-" * 60)
    lines.append(f"  {'Outcome':<30} {'Certainty':<10} {'N':>8} {'k':>4} {'Effect'}")
    for r in pi.grade_rows:
        lines.append(f"  {r.outcome_label:<30} {r.certainty:<10} {r.participants_n:>8} {r.studies_k:>4} {r.effect_label}")
    if pi.forest_svg_content:
        lines.append("")
        lines.append("[Forest Plot SVG embedded — preview HTML or MD for render]")
    return "\n".join(lines)

def generate_report_three_formats(pi: ProjectReportInput) -> tuple[str, str, str]:
    return _render_md(pi), _render_html(pi), _render_txt(pi)
