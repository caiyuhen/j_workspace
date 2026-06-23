from sqlalchemy import Column, String, DateTime, func, Integer
from app.db.database import Base
import uuid

def generate_uuid():
    return f"src-{uuid.uuid4().hex[:6]}"

class DataSourceModel(Base):
    __tablename__ = "data_sources"

    id = Column(String, primary_key=True, default=generate_uuid, index=True)
    name = Column(String, index=True)
    type = Column(String)
    status = Column(String, default="active")
    connection_string = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class IngestionBatchModel(Base):
    __tablename__ = "ingestion_batches"

    id = Column(String, primary_key=True, index=True)
    source_id = Column(String, index=True)
    source_name = Column(String)
    status = Column(String, default="pending")
    records_processed = Column(Integer, default=0)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
