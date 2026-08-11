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
