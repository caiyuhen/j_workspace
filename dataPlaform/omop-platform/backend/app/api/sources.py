import time
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.database import get_db
from app.models.models import DataSourceModel

router = APIRouter()

class DataSourceBase(BaseModel):
    name: str
    type: str
    connection_string: str = "" # 可选，实际中可能需要加密

class DataSourceCreate(DataSourceBase):
    pass

class DataSourceTestRequest(BaseModel):
    type: str
    connection_string: str

class DataSourceResponse(DataSourceBase):
    id: str
    status: str

    model_config = {
        "from_attributes": True
    }

@router.get("/", response_model=List[DataSourceResponse])
def get_sources(db: Session = Depends(get_db)):
    """获取所有配置的数据源列表"""
    return db.query(DataSourceModel).all()

@router.post("/test")
def test_connection(req: DataSourceTestRequest):
    """测试数据库连接是否畅通"""
    if not req.connection_string:
        raise HTTPException(status_code=400, detail="连接字符串不能为空")
        
    try:
        # 使用 SQLAlchemy 尝试连接数据库，设置较短的超时时间
        engine = create_engine(
            req.connection_string, 
            connect_args={"connect_timeout": 5} if req.connection_string.startswith("mysql") else {"connect_timeout": 5} if req.connection_string.startswith("postgresql") else {}
        )
        with engine.connect() as conn:
            pass # 连接成功
        return {"status": "success", "message": "连接测试通过！"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=400, detail=f"数据库连接失败: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"连接格式错误或无法连接: {str(e)}")

@router.post("/", response_model=DataSourceResponse)
def create_source(source: DataSourceCreate, db: Session = Depends(get_db)):
    """添加一个新的医院系统数据源"""
    db_source = DataSourceModel(
        name=source.name,
        type=source.type,
        connection_string=source.connection_string,
        status="active"
    )
    db.add(db_source)
    db.commit()
    db.refresh(db_source)
    return db_source

@router.delete("/{source_id}")
def delete_source(source_id: str, db: Session = Depends(get_db)):
    """删除一个数据源"""
    db_source = db.query(DataSourceModel).filter(DataSourceModel.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    db.delete(db_source)
    db.commit()
    return {"status": "success", "message": "删除成功"}

@router.put("/{source_id}", response_model=DataSourceResponse)
def update_source(source_id: str, source: DataSourceCreate, db: Session = Depends(get_db)):
    """更新一个数据源"""
    db_source = db.query(DataSourceModel).filter(DataSourceModel.id == source_id).first()
    if not db_source:
        raise HTTPException(status_code=404, detail="数据源不存在")
    
    db_source.name = source.name
    db_source.type = source.type
    db_source.connection_string = source.connection_string
    db.commit()
    db.refresh(db_source)
    return db_source
