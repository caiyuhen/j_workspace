from app.models.raw import ErrorRecord, RawRecord, SourceBatch
from app.services.batch_analytics import BatchAnalyticsService


def test_batch_analytics_summary_aggregates_incremental_counts(db_session):
    batch = SourceBatch(
        id="batch_summary",
        filename="summary.csv",
        dataset_name="patient_delta",
        total_rows=10,
        error_rows=1,
        inserted_rows=3,
        updated_rows=2,
        deleted_rows=1,
    )
    db_session.add(batch)
    db_session.add_all(
        [
            RawRecord(batch_id=batch.id, row_data={"patient_id": "P1"}, change_type="insert"),
            RawRecord(batch_id=batch.id, row_data={"patient_id": "P2"}, change_type="update"),
            ErrorRecord(batch_id=batch.id, line_number=2, raw_data={"patient_id": "PX"}, error_message="bad row"),
        ]
    )
    db_session.commit()

    summary = BatchAnalyticsService(db_session).build_summary_for_batch(batch.id)

    assert summary.batch_id == batch.id
    assert summary.dataset_name == "patient_delta"
    assert summary.total_rows == 10
    assert summary.error_rows == 1
    assert summary.inserted_rows == 3
    assert summary.updated_rows == 2
    assert summary.deleted_rows == 1
    assert summary.core_metrics == {"raw_records": 2, "error_records": 1}
