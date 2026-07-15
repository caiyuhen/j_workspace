from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.raw import ErrorRecord, RawRecord, SourceBatch
from app.services.incremental_sync import IncrementalSyncService

class RawPersistenceService:
    def __init__(self, db: Session):
        self.db = db

    def create_batch(self, filename: str) -> SourceBatch:
        batch = SourceBatch(filename=filename, status="processing")
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def save_chunk(
        self,
        batch_id: str,
        valid_rows: List[Dict[str, Any]],
        error_rows: List[Dict[str, Any]],
        dataset_name: str = "ingestion",
        window_start: Optional[datetime] = None,
        window_end: Optional[datetime] = None,
    ):
        # Bulk insert for performance
        if valid_rows:
            sync_service = IncrementalSyncService(self.db)
            snapshot_cache: Dict[Tuple[str, str], Optional[Dict[str, Any]]] = {}
            raw_records = []
            for row in valid_rows:
                business_key = sync_service.build_business_key(row)
                record_hash = sync_service.build_record_hash(row)
                source_updated_at = self._parse_datetime(
                    row.get("updated_at", row.get("source_updated_at"))
                )
                source_version = self._stringify_optional(
                    row.get("version", row.get("source_version"))
                )
                op_flag = self._stringify_optional(row.get("op_flag")) or "snapshot"

                cache_key = (dataset_name, business_key)
                current_snapshot = snapshot_cache.get(cache_key)
                if cache_key not in snapshot_cache:
                    current_snapshot = sync_service.get_current_snapshot(dataset_name, business_key)
                    snapshot_cache[cache_key] = current_snapshot

                incoming = {
                    "business_key": business_key,
                    "record_hash": record_hash,
                    "source_updated_at": source_updated_at,
                    "source_version": source_version,
                    "op_flag": op_flag,
                }
                change_type = sync_service.classify_change(
                    incoming=incoming,
                    current_snapshot=current_snapshot,
                    window_start=window_start,
                    window_end=window_end,
                )

                raw_records.append(
                    RawRecord(
                        batch_id=batch_id,
                        dataset_name=dataset_name,
                        business_key=business_key,
                        record_hash=record_hash,
                        source_updated_at=source_updated_at,
                        source_version=source_version,
                        op_flag=op_flag,
                        change_type=change_type,
                        row_data=row,
                    )
                )
                snapshot_cache[cache_key] = incoming

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

    @staticmethod
    def _parse_datetime(value: Any) -> Optional[datetime]:
        if value is None or value == "":
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            normalized = value.replace("Z", "+00:00")
            return datetime.fromisoformat(normalized)
        return None

    @staticmethod
    def _stringify_optional(value: Any) -> Optional[str]:
        if value is None or value == "":
            return None
        return str(value)

    def update_batch_progress(self, batch_id: str, current_valid: int, current_error: int):
        batch = self.db.query(SourceBatch).filter(SourceBatch.id == batch_id).first()
        if batch:
            batch.total_rows = current_valid
            batch.error_rows = current_error
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
