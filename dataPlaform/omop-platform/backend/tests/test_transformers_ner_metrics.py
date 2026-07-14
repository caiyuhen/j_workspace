from app.services.transformers_ner import TransformersNERMapper


def test_format_timing_log_includes_all_stage_metrics():
    mapper = object.__new__(TransformersNERMapper)

    message = mapper._format_timing_log(
        prefix="[nlp]",
        metrics={
            "regex_ms": 1.2,
            "ner_ms": 3.4,
            "llm_ms": 5.6,
            "total_ms": 10.2,
        },
        extra={"texts": 8},
    )

    assert "[nlp]" in message
    assert "regex_ms=1.20" in message
    assert "ner_ms=3.40" in message
    assert "llm_ms=5.60" in message
    assert "total_ms=10.20" in message
    assert "texts=8" in message
