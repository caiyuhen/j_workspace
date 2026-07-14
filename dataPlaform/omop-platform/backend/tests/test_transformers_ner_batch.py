from app.services.transformers_ner import TransformersNERMapper


def test_extract_entities_batch_uses_ner_pipeline_batch_mode():
    mapper = object.__new__(TransformersNERMapper)

    def fake_pipeline(texts, **kwargs):
        assert isinstance(texts, list), "NER pipeline should receive a batch list"
        assert kwargs.get("batch_size") == 2
        return [
            [{"entity_group": "DIS", "word": "冠心病", "score": 0.99}],
            [{"entity_group": "PROCEDURE", "word": "支架植入术", "score": 0.99}],
        ]

    mapper.ner_pipeline = fake_pipeline

    texts = ["患者冠心病。", "既往支架植入术史。"]
    results = mapper.extract_entities_batch(texts, batch_size=2)

    assert results[0]["conditions"] == ["冠心病"]
    assert results[1]["procedures"] == ["支架植入术"]
