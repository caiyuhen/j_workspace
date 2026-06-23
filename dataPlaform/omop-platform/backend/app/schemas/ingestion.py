from pydantic import BaseModel
from datetime import datetime

class BatchResponse(BaseModel):
    id: str
    filename: str
    total_rows: int
    error_rows: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
