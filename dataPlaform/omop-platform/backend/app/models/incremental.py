import uuid
from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String

from app.db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class IncrementalSyncRun(Base):
    __tablename__ = "incremental_sync_run"

    id = Column(String, primary_key=True, default=generate_uuid)
    dataset_name = Column(String, default="ingestion", index=True)
    batch_id = Column(String, ForeignKey("source_batch.id"), index=True)
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)
    cursor_start = Column(DateTime, nullable=True)
    cursor_end = Column(DateTime, nullable=True)
    status = Column(String, default="running", index=True)
    scan_count = Column(Integer, default=0)
    change_count = Column(Integer, default=0)
    insert_count = Column(Integer, default=0)
    update_count = Column(Integer, default=0)
    delete_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    error_log = Column(JSON, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)


class BatchAnalysisSummary(Base):
    __tablename__ = "batch_analysis_summary"

    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("source_batch.id"), index=True)
    dataset_name = Column(String, default="ingestion", index=True)
    processed_at = Column(DateTime, default=datetime.utcnow, index=True)
    total_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    inserted_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    deleted_rows = Column(Integer, default=0)
    success_rate = Column(Integer, default=0)
    processing_duration_ms = Column(Integer, default=0)
    core_metrics = Column(JSON, nullable=True)
    detail_stats = Column(JSON, nullable=True)
