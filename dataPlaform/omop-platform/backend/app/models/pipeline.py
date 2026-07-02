import uuid
from sqlalchemy import Column, String, Integer, DateTime, JSON
from datetime import datetime
from app.db.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class PipelineRun(Base):
    __tablename__ = "pipeline_run"

    id = Column(String, primary_key=True, default=generate_uuid)
    status = Column(String, default="running")  # running, success, failed, cancelled
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    total_processed = Column(Integer, default=0)
    passed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    logs = Column(JSON, nullable=True)
