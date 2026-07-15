import app.models.incremental as incremental
from app.models.raw import RawRecord, SourceBatch


def test_source_batch_and_raw_record_expose_incremental_columns():
    source_batch_columns = SourceBatch.__table__.columns.keys()
    raw_record_columns = RawRecord.__table__.columns.keys()

    assert "batch_type" in source_batch_columns
    assert "window_start" in source_batch_columns
    assert "deleted_rows" in source_batch_columns

    assert "business_key" in raw_record_columns
    assert "record_hash" in raw_record_columns
    assert "change_type" in raw_record_columns


def test_incremental_models_define_run_and_summary_tables():
    metadata_tables = set(incremental.Base.metadata.tables.keys())

    assert incremental.IncrementalSyncRun.__tablename__ == "incremental_sync_run"
    assert incremental.BatchAnalysisSummary.__tablename__ == "batch_analysis_summary"
    assert {"incremental_sync_run", "batch_analysis_summary"}.issubset(metadata_tables)
