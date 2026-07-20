<<<<<<< HEAD
"""
访视管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.db.session import get_db
from app.models.models import PatientVisit, VisitSchedule, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class VisitCreate(BaseModel):
    patient_id: UUID
    trial_id: UUID
    schedule_id: Optional[UUID] = None
    visit_name: str
    visit_type: Optional[str] = None
    planned_date: Optional[date] = None
    site_id: Optional[UUID] = None
    investigator_id: Optional[UUID] = None


class VisitUpdate(BaseModel):
    actual_date: Optional[date] = None
    status: Optional[str] = None
    is_protocol_deviation: Optional[bool] = None
    deviation_type: Optional[str] = None
    deviation_notes: Optional[str] = None
    assessments: Optional[dict] = None
    notes: Optional[str] = None


def visit_to_dict(v: PatientVisit) -> dict:
    return {
        "id": str(v.id),
        "patient_id": str(v.patient_id) if v.patient_id else None,
        "trial_id": str(v.trial_id) if v.trial_id else None,
        "visit_name": v.visit_name,
        "visit_type": v.visit_type,
        "planned_date": v.planned_date.isoformat() if v.planned_date else None,
        "actual_date": v.actual_date.isoformat() if v.actual_date else None,
        "status": v.status,
        "site_id": str(v.site_id) if v.site_id else None,
        "is_protocol_deviation": v.is_protocol_deviation,
        "deviation_type": v.deviation_type,
        "deviation_notes": v.deviation_notes,
        "assessments": v.assessments or {},
        "notes": v.notes,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


@router.get("", summary="访视列表")
async def list_visits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    patient_id: Optional[UUID] = Query(None),
    trial_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(PatientVisit)
    count_query = select(func.count(PatientVisit.id))
    filters = []
    if patient_id:
        filters.append(PatientVisit.patient_id == patient_id)
    if trial_id:
        filters.append(PatientVisit.trial_id == trial_id)
    if status:
        filters.append(PatientVisit.status == status)
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # 数据隔离：非管理员只能看自己所属中心的访视，或者自己负责的试验项目下的访视
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        cond = (PatientVisit.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | PatientVisit.trial_id.in_(subq)
        
        # 用户作为PI时也可以看该中心的访视
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | PatientVisit.site_id.in_(subq2)
        
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(PatientVisit.planned_date).offset(offset).limit(page_size)
    )
    visits = result.scalars().all()
    return {"total": total, "page": page, "page_size": page_size,
            "items": [visit_to_dict(v) for v in visits]}


@router.post("", summary="创建访视", status_code=201)
async def create_visit(
    body: VisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("visit:write")),
):
    visit = PatientVisit(
        patient_id=body.patient_id,
        trial_id=body.trial_id,
        schedule_id=body.schedule_id,
        visit_name=body.visit_name,
        visit_type=body.visit_type,
        planned_date=body.planned_date,
        site_id=body.site_id,
        investigator_id=body.investigator_id or current_user.id,
        status="SCHEDULED",
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return {"message": "访视创建成功", "data": visit_to_dict(visit)}


@router.get("/upcoming", summary="即将到来的访视")
async def upcoming_visits(
    days: int = Query(7, ge=1, le=30),
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取未来N天内的计划访视"""
    from datetime import datetime, timedelta
    now = datetime.now().date()
    future = now + timedelta(days=days)

    query = select(PatientVisit).where(
        and_(
            PatientVisit.status == "SCHEDULED",
            PatientVisit.planned_date >= now,
            PatientVisit.planned_date <= future,
        )
    )
    if trial_id:
        query = query.where(PatientVisit.trial_id == trial_id)

    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        cond = (PatientVisit.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | PatientVisit.trial_id.in_(subq)
        
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | PatientVisit.site_id.in_(subq2)
        query = query.where(cond)


    result = await db.execute(query.order_by(PatientVisit.planned_date))
    visits = result.scalars().all()
    return {"data": [visit_to_dict(v) for v in visits]}


@router.put("/{visit_id}", summary="更新访视")
async def update_visit(
    visit_id: UUID,
    body: VisitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("visit:write")),
):
    result = await db.execute(select(PatientVisit).where(PatientVisit.id == visit_id))
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="访视记录不存在")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(visit, key, val)
    await db.commit()
    return {"message": "更新成功", "data": visit_to_dict(visit)}
=======
"""
访视管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.db.session import get_db
from app.models.models import PatientVisit, VisitSchedule, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class VisitCreate(BaseModel):
    patient_id: UUID
    trial_id: UUID
    schedule_id: Optional[UUID] = None
    visit_name: str
    visit_type: Optional[str] = None
    planned_date: Optional[date] = None
    site_id: Optional[UUID] = None
    investigator_id: Optional[UUID] = None


class VisitUpdate(BaseModel):
    actual_date: Optional[date] = None
    status: Optional[str] = None
    is_protocol_deviation: Optional[bool] = None
    deviation_type: Optional[str] = None
    deviation_notes: Optional[str] = None
    assessments: Optional[dict] = None
    notes: Optional[str] = None


def visit_to_dict(v: PatientVisit) -> dict:
    return {
        "id": str(v.id),
        "patient_id": str(v.patient_id) if v.patient_id else None,
        "trial_id": str(v.trial_id) if v.trial_id else None,
        "visit_name": v.visit_name,
        "visit_type": v.visit_type,
        "planned_date": v.planned_date.isoformat() if v.planned_date else None,
        "actual_date": v.actual_date.isoformat() if v.actual_date else None,
        "status": v.status,
        "site_id": str(v.site_id) if v.site_id else None,
        "is_protocol_deviation": v.is_protocol_deviation,
        "deviation_type": v.deviation_type,
        "deviation_notes": v.deviation_notes,
        "assessments": v.assessments or {},
        "notes": v.notes,
        "created_at": v.created_at.isoformat() if v.created_at else None,
    }


@router.get("", summary="访视列表")
async def list_visits(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    patient_id: Optional[UUID] = Query(None),
    trial_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(PatientVisit)
    count_query = select(func.count(PatientVisit.id))
    filters = []
    if patient_id:
        filters.append(PatientVisit.patient_id == patient_id)
    if trial_id:
        filters.append(PatientVisit.trial_id == trial_id)
    if status:
        filters.append(PatientVisit.status == status)
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # 数据隔离：非管理员只能看自己所属中心的访视，或者自己负责的试验项目下的访视
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        cond = (PatientVisit.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | PatientVisit.trial_id.in_(subq)
        
        # 用户作为PI时也可以看该中心的访视
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | PatientVisit.site_id.in_(subq2)
        
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(PatientVisit.planned_date).offset(offset).limit(page_size)
    )
    visits = result.scalars().all()
    return {"total": total, "page": page, "page_size": page_size,
            "items": [visit_to_dict(v) for v in visits]}


@router.post("", summary="创建访视", status_code=201)
async def create_visit(
    body: VisitCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("visit:write")),
):
    visit = PatientVisit(
        patient_id=body.patient_id,
        trial_id=body.trial_id,
        schedule_id=body.schedule_id,
        visit_name=body.visit_name,
        visit_type=body.visit_type,
        planned_date=body.planned_date,
        site_id=body.site_id,
        investigator_id=body.investigator_id or current_user.id,
        status="SCHEDULED",
    )
    db.add(visit)
    await db.commit()
    await db.refresh(visit)
    return {"message": "访视创建成功", "data": visit_to_dict(visit)}


@router.get("/upcoming", summary="即将到来的访视")
async def upcoming_visits(
    days: int = Query(7, ge=1, le=30),
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取未来N天内的计划访视"""
    from datetime import datetime, timedelta
    now = datetime.now().date()
    future = now + timedelta(days=days)

    query = select(PatientVisit).where(
        and_(
            PatientVisit.status == "SCHEDULED",
            PatientVisit.planned_date >= now,
            PatientVisit.planned_date <= future,
        )
    )
    if trial_id:
        query = query.where(PatientVisit.trial_id == trial_id)

    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        cond = (PatientVisit.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | PatientVisit.trial_id.in_(subq)
        
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | PatientVisit.site_id.in_(subq2)
        query = query.where(cond)


    result = await db.execute(query.order_by(PatientVisit.planned_date))
    visits = result.scalars().all()
    return {"data": [visit_to_dict(v) for v in visits]}


@router.put("/{visit_id}", summary="更新访视")
async def update_visit(
    visit_id: UUID,
    body: VisitUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("visit:write")),
):
    result = await db.execute(select(PatientVisit).where(PatientVisit.id == visit_id))
    visit = result.scalar_one_or_none()
    if not visit:
        raise HTTPException(status_code=404, detail="访视记录不存在")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(visit, key, val)
    await db.commit()
    return {"message": "更新成功", "data": visit_to_dict(visit)}
>>>>>>> origin/main
