import pytest
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
