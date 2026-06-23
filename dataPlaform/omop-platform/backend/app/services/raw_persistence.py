from sqlalchemy.orm import Session
from app.models.raw import SourceBatch, RawRecord, ErrorRecord
from typing import List, Dict, Any

class RawPersistenceService:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, filename: str) -> SourceBatch:
        batch = SourceBatch(filename=filename, status="processing")
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def save_chunk(self, batch_id: str, valid_rows: List[Dict[str, Any]], error_rows: List[Dict[str, Any]]):
        # Bulk insert for performance
        if valid_rows:
            raw_records = [RawRecord(batch_id=batch_id, row_data=row) for row in valid_rows]
            self.db.bulk_save_objects(raw_records)
        
        if error_rows:
            err_records = [
                ErrorRecord(
                    batch_id=batch_id, 
                    line_number=err.get("line_number"),
                    raw_data=err.get("raw_data"),
                    error_message=err.get("error")
                ) 
                for err in error_rows
            ]
            self.db.bulk_save_objects(err_records)
        
        self.db.commit()

    def complete_batch(self, batch_id: str, total_rows: int, error_rows: int, status: str = "completed"):
        batch = self.db.query(SourceBatch).filter(SourceBatch.id == batch_id).first()
        if batch:
            batch.total_rows = total_rows
            batch.error_rows = error_rows
            batch.status = status
            self.db.commit()
            self.db.refresh(batch)
        return batch
