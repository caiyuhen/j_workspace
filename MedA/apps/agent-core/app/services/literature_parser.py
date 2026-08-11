import re

from pydantic import BaseModel

ENTRY_SEPARATOR = "---"
KNOWN_KEYS = {"title", "authors", "journal", "year", "doi", "pmid", "abstract"}


class ParsedLiteratureEntry(BaseModel):
    title: str
    authors: str = ""
    journal: str = ""
    year: int | None = None
    doi: str = ""
    pmid: str = ""
    abstract: str = ""


class ParseResult(BaseModel):
    entries: list[ParsedLiteratureEntry]
    skipped_count: int


def normalize_title(title: str) -> str:
    """转小写并去除所有非字母数字字符，用于标题级去重比较。"""
    return re.sub(r"[^a-z0-9]", "", title.lower())


def _parse_block(lines: list[str]) -> dict[str, str]:
    fields: dict[str, str] = {}

    for line in lines:
        if ":" not in line:
            continue

        raw_key, raw_value = line.split(":", 1)
        key = raw_key.strip().lower()
        if key in KNOWN_KEYS:
            fields[key] = raw_value.strip()

    return fields


def _to_year(raw: str) -> int | None:
    try:
        return int(raw)
    except ValueError:
        return None


def parse_literature_text(raw_text: str) -> ParseResult:
    blocks: list[list[str]] = [[]]

    for line in raw_text.splitlines():
        if line.strip() == ENTRY_SEPARATOR:
            blocks.append([])
            continue

        if line.strip() == "":
            continue

        blocks[-1].append(line)

    entries: list[ParsedLiteratureEntry] = []
    skipped_count = 0

    for block in blocks:
        fields = _parse_block(block)
        if not fields:
            continue

        title = fields.get("title", "")
        if title == "":
            skipped_count += 1
            continue

        entries.append(
            ParsedLiteratureEntry(
                title=title,
                authors=fields.get("authors", ""),
                journal=fields.get("journal", ""),
                year=_to_year(fields.get("year", "")),
                doi=fields.get("doi", ""),
                pmid=fields.get("pmid", ""),
                abstract=fields.get("abstract", ""),
            )
        )

    return ParseResult(entries=entries, skipped_count=skipped_count)
