import pytest
from datetime import datetime

from app.services.raw_persistence import RawPersistenceService
from app.models.raw import SourceBatch, RawRecord, ErrorRecord

def test_create_and_complete_batch(db_session):
    svc = RawPersistenceService(db_session)
    
    # 1. Create batch
    batch = svc.create_batch("test_upload.csv")
    assert batch.id is not None
    assert batch.filename == "test_upload.csv"
    assert batch.status == "processing"
    
    # 2. Complete batch
    completed = svc.complete_batch(batch.id, total_rows=100, error_rows=5)
    assert completed.status == "completed"
    assert completed.total_rows == 100
    assert completed.error_rows == 5

def test_save_chunk(db_session):
    svc = RawPersistenceService(db_session)
    batch = svc.create_batch("data.csv")
    
    valid_rows = [
        {"name": "Alice", "age": "30"},
        {"name": "Bob", "age": "25"}
    ]
    error_rows = [
        {"line_number": 3, "raw_data": ["Charlie"], "error": "Missing columns"}
    ]
    
    svc.save_chunk(batch.id, valid_rows, error_rows)
    
    # Verify RawRecords in DB
    raws = db_session.query(RawRecord).filter(RawRecord.batch_id == batch.id).all()
    assert len(raws) == 2
    # Ensure JSON data is saved correctly
    names = [r.row_data["name"] for r in raws]
    assert "Alice" in names
    assert "Bob" in names
    
    # Verify ErrorRecords in DB
    errs = db_session.query(ErrorRecord).filter(ErrorRecord.batch_id == batch.id).all()
    assert len(errs) == 1
    assert errs[0].line_number == 3
    assert errs[0].error_message == "Missing columns"
    assert errs[0].raw_data == ["Charlie"]


def test_save_chunk_persists_incremental_metadata(db_session):
    svc = RawPersistenceService(db_session)

    first_batch = svc.create_batch("delta-1.csv")
    svc.save_chunk(
        first_batch.id,
        valid_rows=[
            {
                "patient_id": "P001",
                "updated_at": "2026-07-15T10:00:00",
                "version": 1,
                "name": "Alice",
            }
        ],
        error_rows=[],
        dataset_name="patient_delta",
        window_start=datetime(2026, 7, 15, 9, 0, 0),
        window_end=datetime(2026, 7, 15, 11, 0, 0),
    )

    second_batch = svc.create_batch("delta-2.csv")
    svc.save_chunk(
        second_batch.id,
        valid_rows=[
            {
                "patient_id": "P001",
                "updated_at": "2026-07-15T10:30:00",
                "version": 2,
                "name": "Alice Smith",
            }
        ],
        error_rows=[],
        dataset_name="patient_delta",
        window_start=datetime(2026, 7, 15, 9, 0, 0),
        window_end=datetime(2026, 7, 15, 11, 0, 0),
    )

    rows = (
        db_session.query(RawRecord)
        .filter(RawRecord.dataset_name == "patient_delta")
        .order_by(RawRecord.source_updated_at.asc())
        .all()
    )

    assert len(rows) == 2

    first, second = rows
    assert first.dataset_name == "patient_delta"
    assert first.business_key == "P001"
    assert first.record_hash
    assert first.source_updated_at == datetime(2026, 7, 15, 10, 0, 0)
    assert first.source_version == "1"
    assert first.op_flag == "snapshot"
    assert first.change_type == "insert"

    assert second.dataset_name == "patient_delta"
    assert second.business_key == "P001"
    assert second.record_hash
    assert second.record_hash != first.record_hash
    assert second.source_updated_at == datetime(2026, 7, 15, 10, 30, 0)
    assert second.source_version == "2"
    assert second.op_flag == "snapshot"
    assert second.change_type == "update"
