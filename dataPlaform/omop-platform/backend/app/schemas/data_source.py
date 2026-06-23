from pydantic import BaseModel
from typing import Dict, Any, Optional

class DataSourceBase(BaseModel):
    name: str
    type: str
    connection_params: Dict[str, Any]
    frequency: str

class DataSourceCreate(DataSourceBase):
    pass

class DataSource(DataSourceBase):
    id: str

    class Config:
        from_attributes = True
