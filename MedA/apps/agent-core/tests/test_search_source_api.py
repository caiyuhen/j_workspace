from app.services.source_catalog import (
    LANGUAGE_OPTIONS,
    SEARCH_FIELD_OPTIONS,
    SOURCE_CATALOG,
    source_labels_for_keys,
)


def test_source_catalog_contains_six_medical_databases() -> None:
    keys = [item.key for item in SOURCE_CATALOG]

    assert keys == ["pubmed", "embase", "cochrane", "wos", "cnki", "wanfang"]
    assert all(item.label for item in SOURCE_CATALOG)
    assert all(item.description for item in SOURCE_CATALOG)


def test_source_catalog_marks_full_text_support() -> None:
    support = {item.key: item.supports_full_text for item in SOURCE_CATALOG}

    assert support["pubmed"] is False
    assert support["cochrane"] is True
    assert support["cnki"] is True


def test_search_field_and_language_options_are_defined() -> None:
    assert [item.key for item in SEARCH_FIELD_OPTIONS] == [
        "title",
        "abstract",
        "keyword",
        "mesh",
        "full_text",
    ]
    assert [item.key for item in LANGUAGE_OPTIONS] == ["en", "zh"]


def test_source_labels_for_keys_maps_keys_to_display_labels() -> None:
    assert source_labels_for_keys(["pubmed", "embase"]) == ["PubMed", "Embase"]


def test_source_labels_for_keys_preserves_catalog_order() -> None:
    assert source_labels_for_keys(["cnki", "pubmed"]) == ["PubMed", "中国知网 CNKI"]


def test_source_labels_for_keys_ignores_unknown_keys() -> None:
    assert source_labels_for_keys(["pubmed", "nope"]) == ["PubMed"]
