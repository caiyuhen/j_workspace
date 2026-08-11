from app.services.literature_parser import (
    ParsedLiteratureEntry,
    normalize_title,
    parse_literature_text,
)


def test_parse_multiple_entries_separated_by_dashes() -> None:
    raw = """title: Metformin and cardiovascular outcomes
authors: Chen L, Wang H
journal: Lancet
year: 2023
doi: 10.1016/S2213-8587
pmid: 37123456
abstract: This study evaluates outcomes.
---
title: SGLT2 inhibitors in heart failure
authors: Zhang Y
journal: NEJM
year: 2022
"""

    result = parse_literature_text(raw)

    assert len(result.entries) == 2
    assert result.skipped_count == 0

    first = result.entries[0]
    assert first.title == "Metformin and cardiovascular outcomes"
    assert first.authors == "Chen L, Wang H"
    assert first.journal == "Lancet"
    assert first.year == 2023
    assert first.doi == "10.1016/S2213-8587"
    assert first.pmid == "37123456"
    assert first.abstract == "This study evaluates outcomes."

    second = result.entries[1]
    assert second.title == "SGLT2 inhibitors in heart failure"
    assert second.year == 2022
    assert second.doi == ""
    assert second.pmid == ""


def test_parse_single_entry_without_separator() -> None:
    result = parse_literature_text("title: Only one paper")

    assert len(result.entries) == 1
    assert result.entries[0] == ParsedLiteratureEntry(
        title="Only one paper",
        authors="",
        journal="",
        year=None,
        doi="",
        pmid="",
        abstract="",
    )


def test_parse_ignores_unknown_keys_and_blank_lines() -> None:
    raw = """title: A paper

publisher: Some Press
volume: 12
authors: Li Q
"""

    result = parse_literature_text(raw)

    assert len(result.entries) == 1
    assert result.entries[0].title == "A paper"
    assert result.entries[0].authors == "Li Q"


def test_parse_is_case_insensitive_for_keys() -> None:
    result = parse_literature_text("Title: Mixed case key\nYEAR: 2021")

    assert result.entries[0].title == "Mixed case key"
    assert result.entries[0].year == 2021


def test_parse_sets_year_to_none_when_not_an_integer() -> None:
    result = parse_literature_text("title: Bad year\nyear: in press")

    assert result.entries[0].year is None


def test_parse_skips_blocks_without_title() -> None:
    raw = """title: Good entry
year: 2020
---
authors: No Title Here
year: 2021
---
title: Another good entry
"""

    result = parse_literature_text(raw)

    assert [entry.title for entry in result.entries] == [
        "Good entry",
        "Another good entry",
    ]
    assert result.skipped_count == 1


def test_parse_returns_no_entries_for_unparseable_text() -> None:
    result = parse_literature_text("this text has no recognizable fields at all")

    assert result.entries == []
    assert result.skipped_count == 0


def test_parse_trims_whitespace_around_values() -> None:
    result = parse_literature_text("title:    Padded title   \nauthors:  Wang H  ")

    assert result.entries[0].title == "Padded title"
    assert result.entries[0].authors == "Wang H"


def test_normalize_title_strips_case_and_punctuation() -> None:
    assert normalize_title("Metformin in T2DM.") == normalize_title("metformin in t2dm")
    assert normalize_title("A  Study,  Revisited!") == "astudyrevisited"


def test_normalize_title_handles_empty_string() -> None:
    assert normalize_title("") == ""
    assert normalize_title("   ") == ""


def test_normalize_title_preserves_chinese_characters() -> None:
    t1 = normalize_title("二甲双胍心血管研究")
    t2 = normalize_title("SGLT2抑制剂心衰研究")
    assert t1 != t2, "不同中文标题归一化后不应相等"
    assert t1 == "二甲双胍心血管研究"
    assert normalize_title("二甲双胍 心血管 研究!") == t1, "中文空格和标点应被剥除"


def test_normalize_title_casefold_matches_mixed_case() -> None:
    assert normalize_title("Metformin") == normalize_title("METFORMIN")
    assert normalize_title("Straße") == normalize_title("strasse"), "Unicode casefold 处理 ß"


def test_parse_multiline_abstract_appends_continuation_lines() -> None:
    text = (
        "title: 多中心随机对照试验\n"
        "abstract: 这是摘要的第一行，介绍背景。\n"
        "这是摘要的第二行，不含冒号。\n"
        "这是第三行。\n"
        "year: 2023\n"
        "doi: 10.1/test\n"
    )
    result = parse_literature_text(text)
    assert len(result.entries) == 1
    abstract = result.entries[0].abstract
    assert "第一行" in abstract
    assert "第二行" in abstract, "不含冒号的续行应被追加到 abstract"
    assert "第三行" in abstract


def test_parse_continuation_lines_only_attach_to_last_known_key() -> None:
    preamble_text = (
        "junk line at the top, before any known key\n"
        "another junk without colon\n"
        "title: Valid Title\n"
        "authors: Alice\n"
        "continue authors line here\n"
        "year: 2020\n"
    )
    result = parse_literature_text(preamble_text)
    assert len(result.entries) == 1
    entry = result.entries[0]
    assert (
        entry.title == "Valid Title"
    ), "title 出现之前的 junk 行（last_key=None）应被丢弃，不应污染 title"
    assert "continue authors line here" in entry.authors, "authors 后的续行应追加到 authors"
    assert entry.year == 2020
