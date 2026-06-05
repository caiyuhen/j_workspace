"""
不良事件 / SAE 管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.db.session import get_db
from app.models.models import AdverseEvent, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class AECreate(BaseModel):
    patient_id: UUID
    trial_id: UUID
    visit_id: Optional[UUID] = None
    description: str
    meddra_pt: Optional[str] = None
    meddra_soc: Optional[str] = None
    severity: str = Field(..., description="GRADE_1~GRADE_5 / MILD / MODERATE / SEVERE")
    is_serious: bool = False
    sae_criteria: Optional[List[str]] = []
    relatedness: Optional[str] = None
    onset_date: Optional[date] = None
    action_taken: Optional[str] = None
    treatment: Optional[str] = None


class AEUpdate(BaseModel):
    severity: Optional[str] = None
    is_serious: Optional[bool] = None
    relatedness: Optional[str] = None
    resolution_date: Optional[date] = None
    outcome: Optional[str] = None
    action_taken: Optional[str] = None
    treatment: Optional[str] = None
    report_status: Optional[str] = None
    reported_to_sponsor: Optional[bool] = None
    sponsor_report_date: Optional[date] = None
    reported_to_ethics: Optional[bool] = None


def ae_to_dict(ae: AdverseEvent) -> dict:
    return {
        "id": str(ae.id),
        "ae_no": ae.ae_no,
        "patient_id": str(ae.patient_id) if ae.patient_id else None,
        "trial_id": str(ae.trial_id) if ae.trial_id else None,
        "description": ae.description,
        "meddra_pt": ae.meddra_pt,
        "meddra_soc": ae.meddra_soc,
        "severity": ae.severity,
        "is_serious": ae.is_serious,
        "sae_criteria": ae.sae_criteria or [],
        "relatedness": ae.relatedness,
        "onset_date": ae.onset_date.isoformat() if ae.onset_date else None,
        "resolution_date": ae.resolution_date.isoformat() if ae.resolution_date else None,
        "outcome": ae.outcome,
        "action_taken": ae.action_taken,
        "treatment": ae.treatment,
        "report_status": ae.report_status,
        "reported_to_sponsor": ae.reported_to_sponsor,
        "sponsor_report_date": ae.sponsor_report_date.isoformat() if ae.sponsor_report_date else None,
        "reported_to_ethics": ae.reported_to_ethics,
        "expedited_report": ae.expedited_report,
        "created_at": ae.created_at.isoformat() if ae.created_at else None,
    }


def generate_ae_no() -> str:
    """生成 AE 编号"""
    import random, string
    from datetime import datetime
    ts = datetime.now().strftime("%Y%m%d%H%M%S")
    rand = "".join(random.choices(string.digits, k=4))
    return f"AE-{ts}-{rand}"


@router.get("", summary="不良事件列表")
async def list_adverse_events(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trial_id: Optional[UUID] = Query(None),
    patient_id: Optional[UUID] = Query(None),
    is_serious: Optional[bool] = Query(None),
    severity: Optional[str] = Query(None),
    report_status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(AdverseEvent)
    count_query = select(func.count(AdverseEvent.id))

    filters = []
    if trial_id:
        filters.append(AdverseEvent.trial_id == trial_id)
    if patient_id:
        filters.append(AdverseEvent.patient_id == patient_id)
    if is_serious is not None:
        filters.append(AdverseEvent.is_serious == is_serious)
    if severity:
        filters.append(AdverseEvent.severity == severity)
    if report_status:
        filters.append(AdverseEvent.report_status == report_status)

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site, Patient, Site
        subq_trial = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq_site = select(TrialSite.site_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        
        # 用户可以看到自己负责试验的AE，或者所属中心患者的AE
        subq_patient = select(Patient.id).where(Patient.site_id.in_(subq_site))
        
        cond = (AdverseEvent.trial_id.in_(subq_trial)) | (AdverseEvent.patient_id.in_(subq_patient))
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(AdverseEvent.created_at)).offset(offset).limit(page_size)
    )
    aes = result.scalars().all()

    return {"total": total, "page": page, "page_size": page_size, "items": [ae_to_dict(a) for a in aes]}


@router.post("", summary="上报不良事件", status_code=201)
async def create_adverse_event(
    body: AECreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("ae:write")),
):
    from datetime import datetime, timezone

    ae = AdverseEvent(
        ae_no=generate_ae_no(),
        patient_id=body.patient_id,
        trial_id=body.trial_id,
        visit_id=body.visit_id,
        description=body.description,
        meddra_pt=body.meddra_pt,
        meddra_soc=body.meddra_soc,
        severity=body.severity,
        is_serious=body.is_serious,
        sae_criteria=body.sae_criteria or [],
        relatedness=body.relatedness,
        onset_date=body.onset_date,
        action_taken=body.action_taken,
        treatment=body.treatment,
        report_status="INITIAL",
        # 自动判断是否需要快速报告（SAE 需要7天/15天报告）
        expedited_report=body.is_serious,
        reported_by=current_user.id,
    )
    db.add(ae)
    await db.commit()
    await db.refresh(ae)

    return {"message": "不良事件上报成功", "data": ae_to_dict(ae)}


@router.get("/statistics", summary="AE 统计")
async def ae_statistics(
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    q = select(AdverseEvent)
    if trial_id:
        q = q.where(AdverseEvent.trial_id == trial_id)

    # 总数
    total_q = select(func.count(AdverseEvent.id))
    if trial_id:
        total_q = total_q.where(AdverseEvent.trial_id == trial_id)
    total = (await db.execute(total_q)).scalar()

    # SAE 数
    sae_q = select(func.count(AdverseEvent.id)).where(AdverseEvent.is_serious == True)
    if trial_id:
        sae_q = sae_q.where(AdverseEvent.trial_id == trial_id)
    sae_count = (await db.execute(sae_q)).scalar()

    # 按严重程度分组
    severity_q = select(AdverseEvent.severity, func.count(AdverseEvent.id)).group_by(AdverseEvent.severity)
    if trial_id:
        severity_q = severity_q.where(AdverseEvent.trial_id == trial_id)
    severity_result = await db.execute(severity_q)
    by_severity = {row[0]: row[1] for row in severity_result if row[0]}

    return {"total": total, "sae_count": sae_count, "by_severity": by_severity}


@router.get("/{ae_id}", summary="AE 详情")
async def get_adverse_event(
    ae_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(AdverseEvent).where(AdverseEvent.id == ae_id))
    ae = result.scalar_one_or_none()
    if not ae:
        raise HTTPException(status_code=404, detail="不良事件记录不存在")
    return {"data": ae_to_dict(ae)}


@router.put("/{ae_id}", summary="更新 AE")
async def update_adverse_event(
    ae_id: UUID,
    body: AEUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("ae:write")),
):
    result = await db.execute(select(AdverseEvent).where(AdverseEvent.id == ae_id))
    ae = result.scalar_one_or_none()
    if not ae:
        raise HTTPException(status_code=404, detail="不良事件不存在")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(ae, key, val)
    await db.commit()
    return {"message": "更新成功", "data": ae_to_dict(ae)}
