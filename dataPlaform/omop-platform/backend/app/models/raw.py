import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class SourceBatch(Base):
    __tablename__ = "source_batch"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, index=True)
    batch_type = Column(String, default="full", index=True)
    dataset_name = Column(String, default="ingestion", index=True)
    window_start = Column(DateTime, nullable=True)
    window_end = Column(DateTime, nullable=True)
    trigger_mode = Column(String, default="auto")
    source_snapshot_at = Column(DateTime, nullable=True)
    total_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    inserted_rows = Column(Integer, default=0)
    updated_rows = Column(Integer, default=0)
    deleted_rows = Column(Integer, default=0)
    unchanged_rows = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing, completed, failed
    error_message = Column(String, nullable=True)
    profiling_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    raw_records = relationship("RawRecord", back_populates="batch", cascade="all, delete-orphan")
    error_records = relationship("ErrorRecord", back_populates="batch", cascade="all, delete-orphan")

class RawRecord(Base):
    __tablename__ = "raw_record"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("source_batch.id"))
    dataset_name = Column(String, default="ingestion", index=True)
    business_key = Column(String, nullable=True, index=True)
    record_hash = Column(String, nullable=True, index=True)
    source_updated_at = Column(DateTime, nullable=True)
    source_version = Column(String, nullable=True)
    op_flag = Column(String, nullable=True)
    change_type = Column(String, nullable=True, index=True)
    is_processed = Column(Integer, default=0)
    processed_at = Column(DateTime, nullable=True)
    row_data = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("SourceBatch", back_populates="raw_records")

class ErrorRecord(Base):
    __tablename__ = "error_record"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("source_batch.id"))
    line_number = Column(Integer)
    raw_data = Column(JSON)
    error_message = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    batch = relationship("SourceBatch", back_populates="error_records")


import app.models.incremental  # noqa: E402,F401
