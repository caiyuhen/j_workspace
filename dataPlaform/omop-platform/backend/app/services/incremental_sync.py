import hashlib
import json
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy.orm import Session

from app.models.raw import RawRecord


class IncrementalSyncService:
    def __init__(self, db: Optional[Session]):
        self.db = db

    def build_business_key(self, row: Dict[str, Any]) -> str:
        for field in ("business_key", "person_id", "patient_id", "person_source_value", "id"):
            value = row.get(field)
            if value is not None and value != "":
                return str(value)
        return ""

    def build_record_hash(self, row: Dict[str, Any]) -> str:
        normalized = json.dumps(row, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def get_current_snapshot(self, dataset_name: str, business_key: str) -> Optional[Dict[str, Any]]:
        if self.db is None or not business_key:
            return None

        record = (
            self.db.query(RawRecord)
            .filter(
                RawRecord.dataset_name == dataset_name,
                RawRecord.business_key == business_key,
            )
            .order_by(RawRecord.source_updated_at.desc(), RawRecord.created_at.desc())
            .first()
        )
        if record is None:
            return None

        return {
            "business_key": record.business_key,
            "record_hash": record.record_hash,
            "source_updated_at": record.source_updated_at,
            "source_version": record.source_version,
            "op_flag": record.op_flag,
            "change_type": record.change_type,
        }

    def classify_change(
        self,
        incoming: Dict[str, Any],
        current_snapshot: Optional[Dict[str, Any]],
        window_start: Optional[datetime],
        window_end: Optional[datetime],
    ) -> str:
        op_flag = str(incoming.get("op_flag") or "").lower()
        if op_flag == "delete":
            return "delete"

        incoming_version = self._normalize_scalar(incoming.get("source_version"))
        current_version = self._normalize_scalar(self._snapshot_value(current_snapshot, "source_version"))
        if current_snapshot and incoming_version and current_version and incoming_version != current_version:
            return "update"

        source_updated_at = incoming.get("source_updated_at")
        in_window = source_updated_at is None or (
            (window_start is None or source_updated_at >= window_start)
            and (window_end is None or source_updated_at <= window_end)
        )
        if not current_snapshot and in_window:
            return "insert"

        incoming_hash = self._normalize_scalar(incoming.get("record_hash"))
        current_hash = self._normalize_scalar(self._snapshot_value(current_snapshot, "record_hash"))
        if current_snapshot and in_window and incoming_hash != current_hash:
            return "update"

        return "unchanged"

    @staticmethod
    def _snapshot_value(snapshot: Optional[Dict[str, Any]], key: str) -> Any:
        if snapshot is None:
            return None
        return snapshot.get(key)

    @staticmethod
    def _normalize_scalar(value: Any) -> str:
        if value is None:
            return ""
        return str(value)
