import re
from typing import Any

_BIBTEX_ESCAPE_DICT: dict[str, str] = {
    "\\": "\\\\textbackslash\\\\{\\\\}",
    "&": "\\\\&",
    "%": "\\\\%",
    "#": "\\\\#",
    "_": "\\\\_",
    "{": "\\\\{",
    "}": "\\\\}",
    "~": "\\\\textasciitilde{}",
    "^": "\\\\textasciicircum{}",
    "<": "\\\\textless{}",
    ">": "\\\\textgreater{}",
    "|": "\\\\textbar{}",
    '"': "\\\\textquotedbl{}",
    "'": "\\\\textquotesingle{}",
    "`": "\\\\textasciigrave{}",
}


def _escape_bibtex_value(value: Any) -> str:
    if value is None:
        return ""
    s = str(value)
    out: list[str] = []
    for ch in s:
        rep = _BIBTEX_ESCAPE_DICT.get(ch)
        if rep is not None:
            out.append(rep)
        else:
            out.append(ch)
    return "".join(out)


_CITEKEY_STRIP = re.compile(r"[^\u4e00-\u9fffA-Za-z0-9]")


def _sanitize_citekey_part(raw: str) -> str:
    s = str(raw or "").strip()
    return _CITEKEY_STRIP.sub("", s)


def _make_citekey(rec: dict, prefix: str, used_keys: set[str], global_idx: int) -> str:
    authors = rec.get("authors") or []
    first_author = authors[0] if authors else "anon"
    sa = _sanitize_citekey_part(first_author)
    year = rec.get("year") or "0000"
    base = f"{prefix}_{sa}{year}"
    key = f"{base}_{global_idx:02d}"
    dup = 1
    while key in used_keys:
        key = f"{base}_{global_idx:02d}_dup{dup}"
        dup += 1
    used_keys.add(key)
    return key


def _split_pages(pages: str) -> str:
    if not pages:
        return ""
    p = str(pages).strip()
    return p if p else ""


def serialize_bibtex_py(records: list[dict], cite_key_prefix: str = "meda") -> str:
    used_keys: set[str] = set()
    entries: list[str] = []
    for global_idx, rec in enumerate(records, start=1):
        key = _make_citekey(rec, cite_key_prefix, used_keys, global_idx)
        fields: list[tuple[str, str]] = []
        title = rec.get("title")
        if title:
            fields.append(("title", _escape_bibtex_value(title)))
        authors = rec.get("authors") or []
        if authors:
            esc_authors = [_escape_bibtex_value(a) for a in authors]
            fields.append(("author", " and ".join(esc_authors)))
        journal = rec.get("journal")
        if journal:
            fields.append(("journal", _escape_bibtex_value(journal)))
        year = rec.get("year")
        if year:
            fields.append(("year", str(year)))
        volume = rec.get("volume")
        if volume:
            fields.append(("volume", _escape_bibtex_value(volume)))
        issue = rec.get("issue")
        if issue:
            fields.append(("number", _escape_bibtex_value(issue)))
        pages = rec.get("pages")
        pages_str = _split_pages(pages)
        if pages_str:
            fields.append(("pages", pages_str))
        abstract = rec.get("abstract")
        if abstract:
            fields.append(("abstract", _escape_bibtex_value(abstract)))
        doi = rec.get("doi")
        if doi:
            fields.append(("doi", _escape_bibtex_value(doi)))
        pmid = rec.get("pmid")
        if pmid:
            fields.append(("pmid", _escape_bibtex_value(pmid)))
        url = rec.get("url")
        if url:
            fields.append(("url", _escape_bibtex_value(url)))
        keywords = rec.get("keywords") or []
        if keywords:
            esc_kws = [_escape_bibtex_value(k) for k in keywords]
            fields.append(("keywords", ", ".join(esc_kws)))
        source = rec.get("source")
        if source:
            fields.append(("source", _escape_bibtex_value(source)))
        rec_id = rec.get("id")
        if rec_id:
            fields.append(("meda_id", _escape_bibtex_value(rec_id)))
        lines: list[str] = []
        lines.append(f"@article{{{key},")
        for i, (fname, fval) in enumerate(fields):
            comma = "," if i < len(fields) - 1 else ""
            lines.append(f"  {fname} = {{{fval}}}{comma}")
        lines.append("}")
        entries.append("\n".join(lines))
    return "\n\n".join(entries) + "\n\n"
