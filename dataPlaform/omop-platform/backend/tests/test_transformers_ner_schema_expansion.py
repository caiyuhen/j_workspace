from app.services.transformers_ner import TransformersNERMapper


def test_empty_result_contains_new_domain_buckets():
    mapper = object.__new__(TransformersNERMapper)

    result = mapper._empty_result()

    assert "devices" in result
    assert "specimens" in result
    assert "death" in result
    assert "providers" in result
    assert "care_sites" in result
    assert "note_nlp_items" in result
