import re
from typing import Any

WIN_RESERVED = re.compile(r'[\\/:*?"<>|]')
CTRL = re.compile(r'[\x00-\x1f]')


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
