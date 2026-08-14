from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from scripts.demo_pubmed_end2end import DEMO_PRESETS_PY

ROOT = Path(__file__).resolve().parent.parent.parent.parent
TS_PRESETS_FILE = ROOT / "packages" / "shared-sdk" / "src" / "presets.ts"


def _whitespace_norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _extract_ts_string(text: str, start: int) -> tuple[str, int]:
    assert text[start] == '"' or text[start] == "'", f"Expected quote at {start}: {text[start:start+20]!r}"
    quote = text[start]
    i = start + 1
    out_chars = []
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            out_chars.append(text[i + 1])
            i += 2
            continue
        if ch == quote:
            return "".join(out_chars), i + 1
        out_chars.append(ch)
        i += 1
    raise ValueError("Unterminated string")


def _parse_demo_presets_from_ts(ts_content: str) -> list[dict]:
    results = []
    marker = "export const DEMO_PRESETS: DemoPreset[] = ["
    idx = ts_content.find(marker)
    assert idx != -1, "DEMO_PRESETS array not found in TS file"
    i = idx + len(marker)
    depth = 1
    while i < len(ts_content) and depth > 0:
        ch = ts_content[i]
        if ch == "[":
            depth += 1
            i += 1
        elif ch == "]":
            depth -= 1
            i += 1
        elif ch == "{":
            entry, i = _parse_one_ts_preset_obj(ts_content, i)
            results.append(entry)
        else:
            i += 1
    return results


def _parse_one_ts_preset_obj(text: str, start: int) -> tuple[dict, int]:
    assert text[start] == "{"
    i = start + 1
    entry: dict = {"pico": {}}
    depth = 1
    while i < len(text) and depth > 0:
        key_match = re.match(r"\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", text[i:])
        if key_match:
            key_name = key_match.group(1)
            i += key_match.end()
            if key_name == "key":
                m = re.match(r"\s*", text[i:])
                i += m.end()
                s, i = _extract_ts_string(text, i)
                entry["key"] = s
            elif key_name == "boolean_text":
                m = re.match(r"\s*", text[i:])
                i += m.end()
                if text[i:i+1] == ":\n" or text[i:i+1] == ": ":
                    i += 1 if text[i] == ":" else 0
                    m2 = re.match(r"\s*", text[i:])
                    i += m2.end()
                s, i = _extract_ts_string(text, i)
                entry["boolean_text"] = s
            elif key_name == "pico":
                m = re.match(r"\s*\{\s*", text[i:])
                i += m.end()
                pico_depth = 1
                while i < len(text) and pico_depth > 0:
                    dom_match = re.match(r"\s*([pico])\s*:\s*", text[i:])
                    if dom_match:
                        dom = dom_match.group(1)
                        i += dom_match.end()
                        s, i = _extract_ts_string(text, i)
                        entry["pico"][dom] = s
                    else:
                            ch = text[i]
                            if ch == "}":
                                pico_depth -= 1
                                i += 1
                            elif ch == "{":
                                pico_depth += 1
                                i += 1
                            else:
                                i += 1
            else:
                while i < len(text):
                    ch = text[i]
                    if ch == "{":
                        inner_depth = 1
                        i += 1
                        while i < len(text) and inner_depth > 0:
                            c2 = text[i]
                            if c2 == "{":
                                inner_depth += 1
                            elif c2 == "}":
                                inner_depth -= 1
                            i += 1
                        break
                    elif ch == "," or ch == "}":
                        break
                    else:
                        i += 1
        else:
            ch = text[i]
            if ch == "{":
                depth += 1
                i += 1
            elif ch == "}":
                depth -= 1
                i += 1
            elif ch == '"' or ch == "'":
                _, i = _extract_ts_string(text, i)
            else:
                i += 1
    return entry, i


def test_shared_sdk_demo_presets_vs_python_have_same_key_boolean_text_pico():
    assert TS_PRESETS_FILE.exists(), f"TS presets file not found: {TS_PRESETS_FILE}"
    ts_content = TS_PRESETS_FILE.read_text(encoding="utf-8")
    ts_list = _parse_demo_presets_from_ts(ts_content)

    assert len(ts_list) == 6, f"Expected 6 DEMO_PRESETS in TS, got {len(ts_list)}"

    ts_keys = sorted([x["key"] for x in ts_list])
    py_keys = sorted(DEMO_PRESETS_PY.keys())
    assert ts_keys == py_keys, f"preset keys mismatch: TS={ts_keys}, PY={py_keys}"

    for ts_entry in ts_list:
        key = ts_entry["key"]
        py_entry = DEMO_PRESETS_PY[key]
        ts_bool = _whitespace_norm(ts_entry["boolean_text"])
        py_bool = _whitespace_norm(py_entry["boolean_text"])
        assert ts_bool == py_bool, f"[{key}] boolean_text mismatch\nTS={ts_bool!r}\nPY={py_bool!r}"
        for dom in ("p", "i", "c", "o"):
            ts_p = _whitespace_norm(ts_entry["pico"].get(dom, ""))
            py_p = _whitespace_norm(py_entry["pico"].get(dom, ""))
            assert ts_p == py_p, f"[{key}] pico.{dom} mismatch\nTS={ts_p!r}\nPY={py_p!r}"
