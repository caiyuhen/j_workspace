from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Any

class BatchResponse(BaseModel):
    id: str
    filename: str
    batch_type: Optional[str] = None
    dataset_name: Optional[str] = None
    trigger_mode: Optional[str] = None
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    total_rows: int
    error_rows: int
    inserted_rows: int = 0
    updated_rows: int = 0
    deleted_rows: int = 0
    unchanged_rows: int = 0
    status: str
    profiling_data: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ReplayRequest(BaseModel):
    dataset_name: str = "ingestion"
    trigger_mode: str = "manual"
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    batch_id: Optional[str] = None
    business_keys: list[str] = Field(default_factory=list)


class ReplayResponse(BaseModel):
    batch_id: str
    batch_type: str
    dataset_name: str
    trigger_mode: str
    window_start: Optional[datetime] = None
    window_end: Optional[datetime] = None
    status: str
