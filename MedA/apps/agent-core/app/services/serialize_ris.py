import re
from typing import Any

WIN_RESERVED = re.compile(r'[\\/:*?"<>|]')
CTRL = re.compile(r'[\x00-\x1f]')


def makeEmptyPrismaSvg(*, runId: int | str, reason: str) -> str:
    rid = str(runId)
    r = str(reason or "").replace("&", "&amp;").replace("<", "&lt;").replace('"', "&quot;")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<svg xmlns="http://www.w3.org/2000/svg" width="800" height="600" '
        'viewBox="0 0 800 600">\n'
        f'  <title>Empty PRISMA runId={rid}</title>\n'
        f'  <desc>{r}</desc>\n'
        '  <rect x="1" y="1" width="798" height="598" fill="#ffffff" stroke="#cccccc"/>\n'
        f'  <text x="400" y="300" font-family="sans-serif" font-size="16" '
        'text-anchor="middle" fill="#999999">Empty PRISMA flow diagram</text>\n'
        '</svg>\n'
    )


def _sanitize_filename_py(raw: str, fallback: str = "meda_export") -> str:
    s = str(raw or "").strip()
    s = CTRL.sub("", s)
    s = WIN_RESERVED.sub("_", s)
    s = s.strip()
    dot_idx = s.rfind(".")
    if dot_idx > 0:
        base = s[:dot_idx]
        ext = s[dot_idx:]
    else:
        base = s
        ext = ""
    while base.endswith(".") or base.endswith(" "):
        base = base[:-1]
    s = base + ext if ext else base
    while s.endswith(".") or s.endswith(" "):
        s = s[:-1]
    if len(s) == 0:
        return fallback
    if len(s) > 200:
        dot_idx2 = s.rfind(".")
        ext2 = s[dot_idx2:] if dot_idx2 > 160 else ""
        base2 = s[:dot_idx2] if ext2 else s
        max_base = max(1, 200 - len(ext2))
        s = base2[:max_base] + ext2
    return s or fallback


def _truncate_field_py(value: Any, max_bytes: int, suffix: str = "...[truncated]") -> str:
    if value is None:
        return ""
    s = str(value)
    suf_bytes = len(suffix.encode("utf-8"))
    b = s.encode("utf-8")
    if len(b) <= max_bytes:
        return s
    hard_max = max(10, max_bytes)
    target = max(20, hard_max - suf_bytes)
    while len(s.encode("utf-8")) > target and len(s) > 0:
        m = re.match(r'^(.*)[。.!?！？；;,\s]', s)
        if m and len(m.group(1)) > 0:
            s = m.group(1)
        else:
            s = s[:-1]
    return s + suffix


def _escape_ris_value(value: Any) -> str:
    if value is None:
        return ""
    s = str(value)
    s = s.replace("\\", "\\\\")
    s = s.replace("`", "\\`")
    return s


def _split_pages(pages: str) -> tuple[str, str]:
    if not pages:
        return "", ""
    p = str(pages).strip()
    if not p:
        return "", ""
    if "-" in p:
        parts = p.split("-", 1)
        return parts[0].strip(), parts[1].strip()
    return p, ""


def serialize_ris_py(records: list[dict], ris_utf8_bom: bool = True) -> str:
    ris_lines: list[str] = []
    for rec in records:
        ris_lines.append("TY  - JOUR")
        title = _truncate_field_py(rec.get("title"), 6144)
        ris_lines.append(f"TI  - {_escape_ris_value(title)}")
        authors = rec.get("authors") or []
        if len(authors) > 25:
            authors = authors[:25]
            authors[-1] = authors[-1] + " et al."
        for au in authors:
            ris_lines.append(f"AU  - {_escape_ris_value(au)}")
        journal = rec.get("journal")
        if journal:
            ris_lines.append(f"JO  - {_escape_ris_value(journal)}")
        year = rec.get("year")
        if year:
            ris_lines.append(f"PY  - {year}")
        volume = rec.get("volume")
        if volume:
            ris_lines.append(f"VL  - {_escape_ris_value(volume)}")
        issue = rec.get("issue")
        if issue:
            ris_lines.append(f"IS  - {_escape_ris_value(issue)}")
        pages = rec.get("pages") or ""
        sp, ep = _split_pages(pages)
        if sp:
            ris_lines.append(f"SP  - {sp}")
        if ep:
            ris_lines.append(f"EP  - {ep}")
        abstract = _truncate_field_py(rec.get("abstract"), 6144)
        if abstract:
            ris_lines.append(f"AB  - {_escape_ris_value(abstract)}")
        doi = rec.get("doi")
        if doi:
            ris_lines.append(f"DO  - {_escape_ris_value(doi)}")
        pmid = rec.get("pmid")
        if pmid:
            ris_lines.append(f"PM  - {_escape_ris_value(pmid)}")
        url = rec.get("url")
        if url:
            ris_lines.append(f"UR  - {_escape_ris_value(url)}")
        keywords = rec.get("keywords") or []
        for kw in keywords:
            ris_lines.append(f"KW  - {_escape_ris_value(kw)}")
        source = rec.get("source") or ""
        rec_id = rec.get("id") or ""
        n1_parts = []
        if source:
            n1_parts.append(f"source:{source}")
        if rec_id:
            n1_parts.append(f"id:{rec_id}")
        if n1_parts:
            ris_lines.append(f"N1  - {';'.join(n1_parts)}")
        ris_lines.append("ER  - ")
        ris_lines.append("")
    result = "\r\n".join(ris_lines) + "\r\n"
    if ris_utf8_bom:
        result = "\ufeff" + result
    return result
