from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, desc, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from uuid import UUID
import uuid

from app.db.session import get_db
from app.models.models import Timesheet, User
from app.core.dependencies import get_current_active_user

router = APIRouter()

class TimesheetCreate(BaseModel):
    date: date
    project: str
    task: str
    hours: float
    notes: Optional[str] = None

class TimesheetUpdate(BaseModel):
    date: Optional[date] = None
    project: Optional[str] = None
    task: Optional[str] = None
    hours: Optional[float] = None
    notes: Optional[str] = None

def timesheet_to_dict(t: Timesheet):
    return {
        "id": str(t.id),
        "date": t.date.isoformat() if t.date else None,
        "project": t.project,
        "task": t.task,
        "hours": float(t.hours),
        "notes": t.notes,
        "user_name": t.user.full_name if t.user and t.user.full_name else (t.user.username if t.user else "-")
    }

@router.get("", summary="获取当前用户的工时列表")
async def list_timesheets(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Timesheet).where(Timesheet.user_id == current_user.id).order_by(desc(Timesheet.date))
    count_query = select(func.count(Timesheet.id)).where(Timesheet.user_id == current_user.id)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    rows = result.scalars().all()
    
    # 填充 User 关系，手动查询或者使用 selectinload
    for t in rows:
        t.user = current_user

    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [timesheet_to_dict(t) for t in rows]
    }

@router.post("", summary="填报工时", status_code=201)
async def create_timesheet(
    body: TimesheetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if body.hours < 0 or body.hours > 24:
        raise HTTPException(status_code=400, detail="工时必须在0-24小时之间")

    t = Timesheet(
        user_id=current_user.id,
        **body.model_dump(exclude_none=True)
    )
    db.add(t)
    await db.commit()
    await db.refresh(t)
    t.user = current_user
    return {"message": "工时填报成功", "data": timesheet_to_dict(t)}

@router.put("/{ts_id}", summary="修改工时")
async def update_timesheet(
    ts_id: UUID,
    body: TimesheetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Timesheet).where(Timesheet.id == ts_id, Timesheet.user_id == current_user.id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    update_data = body.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(t, key, val)
    
    await db.commit()
    await db.refresh(t)
    t.user = current_user
    return {"message": "更新成功", "data": timesheet_to_dict(t)}

@router.delete("/{ts_id}", summary="删除工时")
async def delete_timesheet(
    ts_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Timesheet).where(Timesheet.id == ts_id, Timesheet.user_id == current_user.id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="工时记录不存在")

    await db.execute(delete(Timesheet).where(Timesheet.id == ts_id))
    await db.commit()
    return {"message": "删除成功"}