from datetime import datetime

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


def test_batch_analytics_list_filters_by_batch_type_and_time_range(client, db_session):
    db_session.add_all(
        [
            SourceBatch(
                id="batch_incremental",
                filename="inc.csv",
                batch_type="incremental",
                dataset_name="ingestion",
                status="completed",
                total_rows=8,
                inserted_rows=3,
                updated_rows=1,
                deleted_rows=1,
                created_at=datetime(2026, 7, 15, 10, 0, 0),
            ),
            SourceBatch(
                id="batch_full",
                filename="full.csv",
                batch_type="full",
                dataset_name="ingestion",
                status="completed",
                total_rows=12,
                inserted_rows=12,
                updated_rows=0,
                deleted_rows=0,
                created_at=datetime(2026, 7, 14, 10, 0, 0),
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/v1/ingestion/batch-analytics",
        params={
            "batch_type": "incremental",
            "start_time": "2026-07-15T00:00:00",
            "end_time": "2026-07-15T23:59:59",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == ["batch_incremental"]
    assert payload["items"][0]["batch_type"] == "incremental"
    assert payload["items"][0]["total_rows"] == 8
    assert payload["items"][0]["inserted_rows"] == 3


def test_batch_analytics_export_returns_csv(client, db_session):
    db_session.add_all(
        [
            SourceBatch(
                id="batch_export_1",
                filename="inc-a.csv",
                batch_type="incremental",
                dataset_name="ingestion",
                status="completed",
                total_rows=5,
                inserted_rows=2,
                updated_rows=1,
                deleted_rows=0,
            ),
            SourceBatch(
                id="batch_export_2",
                filename="inc-b.csv",
                batch_type="incremental",
                dataset_name="ingestion",
                status="failed",
                total_rows=4,
                inserted_rows=0,
                updated_rows=1,
                deleted_rows=1,
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/v1/ingestion/batch-analytics/export",
        params={"batch_ids": "batch_export_1,batch_export_2"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    content = response.text
    assert "batch_id,filename,batch_type,status,total_rows,inserted_rows,updated_rows,deleted_rows,error_rows" in content
    assert "batch_export_1,inc-a.csv,incremental,completed,5,2,1,0,0" in content
    assert "batch_export_2,inc-b.csv,incremental,failed,4,0,1,1,0" in content


def test_batch_analytics_compare_returns_selected_batches(client, db_session):
    db_session.add_all(
        [
            SourceBatch(
                id="batch_compare_1",
                filename="compare-a.csv",
                batch_type="incremental",
                dataset_name="ingestion",
                status="completed",
                total_rows=10,
                inserted_rows=4,
                updated_rows=2,
                deleted_rows=1,
            ),
            SourceBatch(
                id="batch_compare_2",
                filename="compare-b.csv",
                batch_type="replay",
                dataset_name="ingestion",
                status="completed",
                total_rows=6,
                inserted_rows=1,
                updated_rows=3,
                deleted_rows=0,
            ),
        ]
    )
    db_session.commit()

    response = client.get(
        "/api/v1/ingestion/batch-analytics/compare",
        params={"batch_ids": "batch_compare_1,batch_compare_2"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert [item["id"] for item in payload["items"]] == ["batch_compare_1", "batch_compare_2"]
