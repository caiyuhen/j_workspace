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
    total_rows = Column(Integer, default=0)
    error_rows = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    raw_records = relationship("RawRecord", back_populates="batch", cascade="all, delete-orphan")
    error_records = relationship("ErrorRecord", back_populates="batch", cascade="all, delete-orphan")

class RawRecord(Base):
    __tablename__ = "raw_record"
    
    id = Column(String, primary_key=True, default=generate_uuid)
    batch_id = Column(String, ForeignKey("source_batch.id"))
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
