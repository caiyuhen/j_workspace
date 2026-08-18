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

def _original_w83_generate_report_three_formats(pi: ProjectReportInput) -> tuple[str, str, str]:
    return _render_md(pi), _render_html(pi), _render_txt(pi)


CH_OVERRIDE_MAP: dict[str, tuple[int, str, str]] = {
    "override_ch1_background": (1, "## 1. Background", "## 1. 研究背景"),
    "override_ch2_methods": (2, "## 2. Methods", "## 2. 研究方法"),
    "override_ch3_pico": (3, "## 3. PICO", "## 3. PICO问题"),
    "override_ch4_results": (4, "## 4. Results", "## 4. 研究结果"),
    "override_ch5_grade_assessment": (5, "## 5. GRADE Assessment", "## 5. 证据质量评价"),
    "override_ch6_summary_of_findings": (6, "## 6. Summary of Findings", "## 6. 主要发现总结"),
    "override_ch7_discussion": (7, "## 7. Discussion", "## 7. 讨论"),
    "override_ch8_appendices": (8, "## 8. Appendices", "## 8. 附录"),
}


def _md_strip_section_body(md: str, heading_en: str, heading_zh: str) -> tuple[int, int] | None:
    lines = md.splitlines(keepends=True)
    anchor_idx = -1
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n")
        if stripped == heading_en or stripped == heading_zh:
            anchor_idx = i
            break
    if anchor_idx == -1:
        return None
    start_pos = 0
    for i in range(anchor_idx + 1):
        start_pos += len(lines[i])
    end_pos = start_pos
    for i in range(anchor_idx + 1, len(lines)):
        line = lines[i]
        stripped = line.lstrip()
        if stripped.startswith("## ") and not stripped.startswith("### "):
            break
        end_pos += len(line)
    return start_pos, end_pos


def _replace_section_body(md: str, heading_en: str, heading_zh: str, new_body: str) -> str:
    span = _md_strip_section_body(md, heading_en, heading_zh)
    if span is None:
        appendix = "\n" + heading_en + "\n" + new_body
        if not md.endswith("\n"):
            appendix = "\n" + appendix
        return md + appendix
    s, e = span
    return md[:s] + new_body + ("\n" if not new_body.endswith("\n") else "") + md[e:]


def _replace_section_body_html(html: str, ch_num: int, heading_en: str, new_body_html: str) -> str:
    section_id = f"ch{ch_num}"
    open_tag = f'<section id="{section_id}">'
    close_tag = "</section>"
    if open_tag in html:
        s = html.find(open_tag) + len(open_tag)
        e = html.find(close_tag, s)
        if e != -1:
            h2_text = heading_en.replace("## ", "")
            new_inner = f"<h2>{h2_text}</h2>\n{new_body_html}"
            return html[:s] + new_inner + html[e:]
    append_anchor = "</body>"
    if append_anchor in html:
        idx = html.find(append_anchor)
        h2_text = heading_en.replace("## ", "")
        new_section = f'<section id="{section_id}"><h2>{h2_text}</h2>\n{new_body_html}</section>\n'
        return html[:idx] + new_section + html[idx:]
    return html


def _md_to_minimal_html(md: str) -> str:
    out_lines: list[str] = []
    in_paragraph = False
    para_buf: list[str] = []

    def flush_para():
        nonlocal in_paragraph, para_buf
        if in_paragraph:
            text = " ".join(s.rstrip() for s in para_buf)
            text = text.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            while "**" in text:
                text = text.replace("**", "<strong>", 1).replace("**", "</strong>", 1)
            text = text.replace("*", "<em>", 1).replace("*", "</em>", 1)
            while "*" in text:
                text = text.replace("*", "<em>", 1).replace("*", "</em>", 1)
            out_lines.append(f"<p>{text}</p>")
            in_paragraph = False
            para_buf = []

    for raw_line in md.splitlines():
        line = raw_line.rstrip()
        if line.startswith("### "):
            flush_para()
            out_lines.append(f"<h3>{line[4:]}</h3>")
        elif line.startswith("## "):
            flush_para()
            out_lines.append(f"<h2>{line[3:]}</h2>")
        elif line.startswith("# "):
            flush_para()
            out_lines.append(f"<h1>{line[2:]}</h1>")
        elif line.startswith("|"):
            flush_para()
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            out_lines.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
        elif line == "":
            flush_para()
        else:
            if not in_paragraph:
                in_paragraph = True
            para_buf.append(line)
    flush_para()
    return "\n".join(out_lines)


def generate_report_three_formats(pi: ProjectReportInput, overrides: dict | None = None) -> tuple[str, str, str]:
    md, html, txt = _original_w83_generate_report_three_formats(pi)
    if not overrides:
        return md, html, txt
    non_empty_items = [(k, v) for k, v in overrides.items() if isinstance(v, str) and v.strip()]
    if not non_empty_items:
        return md, html, txt
    sorted_items = sorted(
        non_empty_items,
        key=lambda kv: CH_OVERRIDE_MAP.get(kv[0], (999, "", ""))[0],
    )
    for key, new_body in sorted_items:
        cfg = CH_OVERRIDE_MAP.get(key)
        if cfg is None:
            continue
        ch_num, heading_en, heading_zh = cfg
        md = _replace_section_body(md, heading_en, heading_zh, new_body)
        body_html = _md_to_minimal_html(new_body)
        html = _replace_section_body_html(html, ch_num, heading_en, body_html)
        txt_heading = heading_en.replace("## ", "")
        txt_heading_zh = heading_zh.replace("## ", "")
        txt_anchor = txt_heading + "\n" + "-" * len(txt_heading)
        txt_anchor_zh = txt_heading_zh + "\n" + "-" * len(txt_heading_zh)
        if txt_anchor in txt:
            start = txt.find(txt_anchor) + len(txt_anchor)
            next_idx = txt.find("\n\n", start)
            end = next_idx if next_idx != -1 else len(txt)
            txt = txt[:start] + "\n" + new_body + ("\n" if end < len(txt) else "") + txt[end:]
        elif txt_anchor_zh in txt:
            start = txt.find(txt_anchor_zh) + len(txt_anchor_zh)
            next_idx = txt.find("\n\n", start)
            end = next_idx if next_idx != -1 else len(txt)
            txt = txt[:start] + "\n" + new_body + ("\n" if end < len(txt) else "") + txt[end:]
        else:
            appendix = "\n\n" + txt_anchor + "\n" + new_body
            txt += appendix
    return md, html, txt
