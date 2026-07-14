from app.services.staging_transformer import StagingTransformer


def test_format_stage_timing_log_includes_metrics_and_extra_fields():
    message = StagingTransformer._format_stage_timing_log(
        prefix="[batch_1] [STAGING_ORM]",
        metrics={"orm_ms": 12.34, "nlp_infer_ms": 56.78},
        extra={"objects": 99},
    )

    assert "[batch_1] [STAGING_ORM]" in message
    assert "orm_ms=12.34" in message
    assert "nlp_infer_ms=56.78" in message
    assert "objects=99" in message
