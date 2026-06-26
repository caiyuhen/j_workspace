from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any

class BatchResponse(BaseModel):
    id: str
    filename: str
    total_rows: int
    error_rows: int
    status: str
    profiling_data: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True
