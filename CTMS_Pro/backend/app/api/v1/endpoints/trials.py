"""
试验管理 API
完整的 CRUD + 中心管理 + 里程碑 + 统计
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, desc, and_
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
import uuid
import httpx
from loguru import logger

from app.core.config import settings
from app.db.session import get_db
from app.models.models import (
    Trial,
    TrialSite,
    TrialMilestone,
    Site,
    User,
    Patient,
    EConsent,
    VisitSchedule,
    PatientVisit,
    AdverseEvent,
    DrugBatch,
    DrugDispensing,
    Contract,
    Payment,
    MonitoringReport,
    QCIssue,
    Document,
    ETMFFolder,
    ScreeningRecord,
    Notification,
    RandomizationScheme,
    SubjectRandomization,
    RandomizationCode,
)
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────

class TrialCenterCreate(BaseModel):
    id: str
    code: str
    name: str
    pi: str
    target: int

class TrialUserCreate(BaseModel):
    id: str
    name: str
    role: str
    scope: str
    email: str

class TrialCreate(BaseModel):
    trial_no: str = Field(..., description="试验编号，如 CTMS-2026-001")
    short_name: str
    full_name: str
    phase: Optional[str] = None
    type: Optional[str] = None
    indication: Optional[str] = None
    drug_name: Optional[str] = None
    drug_code: Optional[str] = None
    sponsor: Optional[str] = None
    cro: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    target_enrollment: int = 0
    total_budget: Optional[float] = None
    protocol_version: Optional[str] = None
    ctgov_id: Optional[str] = None
    cde_id: Optional[str] = None
    pm_user_id: Optional[UUID] = None
    centers: Optional[List[TrialCenterCreate]] = None
    users: Optional[List[TrialUserCreate]] = None
    user_token: Optional[str] = None
    extra_data: Optional[dict] = None


class TrialUpdate(BaseModel):
    short_name: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    indication: Optional[str] = None
    planned_start: Optional[date] = None
    planned_end: Optional[date] = None
    actual_start: Optional[date] = None
    actual_end: Optional[date] = None
    target_enrollment: Optional[int] = None
    total_budget: Optional[float] = None
    protocol_version: Optional[str] = None
    ctgov_id: Optional[str] = None
    cde_id: Optional[str] = None
    ethics_approval_no: Optional[str] = None
    pm_user_id: Optional[UUID] = None
    extra_data: Optional[dict] = None


class MilestoneCreate(BaseModel):
    name: str
    milestone_type: Optional[str] = None
    planned_date: Optional[date] = None
    owner_user_id: Optional[UUID] = None
    notes: Optional[str] = None


def trial_to_dict(t: Trial) -> dict:
    from sqlalchemy import inspect
    d = {
        "id": str(t.id),
        "trial_no": t.trial_no,
        "short_name": t.short_name,
        "full_name": t.full_name,
        "phase": t.phase,
        "status": t.status,
        "type": t.type,
        "indication": t.indication,
        "drug_name": t.drug_name,
        "sponsor": t.sponsor,
        "cro": t.cro,
        "planned_start": t.planned_start.isoformat() if t.planned_start else None,
        "planned_end": t.planned_end.isoformat() if t.planned_end else None,
        "actual_start": t.actual_start.isoformat() if t.actual_start else None,
        "target_enrollment": t.target_enrollment,
        "enrolled_count": t.enrolled_count,
        "screened_count": t.screened_count,
        "completed_count": t.completed_count,
        "total_budget": float(t.total_budget) if t.total_budget else None,
        "spent_amount": float(t.spent_amount) if t.spent_amount else 0,
        "currency": t.currency,
        "protocol_version": t.protocol_version,
        "ctgov_id": t.ctgov_id,
        "cde_id": t.cde_id,
        "ethics_approval_no": t.ethics_approval_no,
        "pm_user_id": str(t.pm_user_id) if t.pm_user_id else None,
        "trial_code": t.trial_code,
        "created_at": t.created_at.isoformat() if t.created_at else None,
        "updated_at": t.updated_at.isoformat() if t.updated_at else None,
    }
    insp = inspect(t)
    if "extension" not in insp.unloaded and t.extension:
        d["extra_data"] = t.extension.extra_data
    return d


# ─── 试验列表 ─────────────────────────────────────────────────────

@router.get("", summary="获取试验列表")
async def list_trials(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="状态筛选"),
    phase: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="关键词搜索（编号/名称/药物）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取临床试验列表，支持分页、筛选、搜索"""
    query = select(Trial)
    count_query = select(func.count(Trial.id))

    if status:
        query = query.where(Trial.status == status)
        count_query = count_query.where(Trial.status == status)
    if phase:
        query = query.where(Trial.phase == phase)
        count_query = count_query.where(Trial.phase == phase)
    if keyword:
        kw = f"%{keyword}%"
        condition = (
            Trial.trial_no.ilike(kw) |
            Trial.short_name.ilike(kw) |
            Trial.drug_name.ilike(kw) |
            Trial.sponsor.ilike(kw)
        )
        query = query.where(condition)
        count_query = count_query.where(condition)

    # 数据隔离：非管理员只能看自己参与或管理的试验，或者所属中心的试验
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Site
        # 用户作为PM、创建者
        cond = (Trial.pm_user_id == current_user.id) | (Trial.created_by == current_user.id)
        
        # 用户作为中心人员或PI
        subq = select(TrialSite.trial_id).where(
            (TrialSite.pi_user_id == current_user.id) | 
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        )
        cond = cond | Trial.id.in_(subq)
        
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.options(selectinload(Trial.extension)).order_by(desc(Trial.created_at)).offset(offset).limit(page_size)
    )
    trials = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [trial_to_dict(t) for t in trials]
    }


@router.post("", summary="创建试验", status_code=201)
async def create_trial(
    body: TrialCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trial:write")),
):
    """创建新临床试验"""
    # 检查编号唯一性
    exists = await db.execute(select(Trial).where(Trial.trial_no == body.trial_no))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"试验编号 {body.trial_no} 已存在")

    body_data = body.model_dump(exclude_none=True)
    centers = body_data.pop("centers", [])
    users = body_data.pop("users", [])
    user_token = body_data.pop("user_token", None)
    extra_data = body_data.pop("extra_data", None)

    trial = Trial(
        **body_data,
        status="PLANNING",
        created_by=current_user.id,
    )
    db.add(trial)
    
    if extra_data:
        from app.models.models import TrialExtension
        extension = TrialExtension(trial=trial, extra_data=extra_data)
        db.add(extension)

    await db.commit()
    await db.refresh(trial)

    # 同步外部系统
    hospital_list = []
    for c in centers:
        hospital_list.append({
            "hospitalName": c.get("name"),
            "hospitalCode": c.get("code"),
            "projectLeader": c.get("pi")
        })

    personnel_list = []
    if users:
        user_ids = []
        for u in users:
            try:
                user_ids.append(uuid.UUID(u.get("id")))
            except:
                pass
        
        user_map = {}
        if user_ids:
            user_res = await db.execute(select(User).where(User.id.in_(user_ids)))
            for u in user_res.scalars().all():
                user_map[str(u.id)] = u
                
        for u in users:
            db_user = user_map.get(u.get("id"))
            if db_user:
                personnel_list.append({
                    "keyword": db_user.phone or "",
                    "userName": db_user.full_name or db_user.username,
                    "hospitalCode": "",
                    "userTag": u.get("role")
                })

    payload = {
        "project": {
            "ctmsProjectId": str(trial.id),
            "projectNumber": trial.trial_no,
            "projectName": trial.full_name,
            "projectStatus": trial.status,
            "projectType": trial.phase,
            "bidCompany": trial.sponsor,
            "projectSystem": "5"
        },
        "projectHospitalList": hospital_list,
        "projectUserInfoList": personnel_list
    }

    import json
    logger.info(f"Prepared external API payload: {json.dumps(payload, ensure_ascii=False)}")
    logger.info(f"User token present: {bool(user_token)}")
    logger.info(f"User token value: {user_token}")

    if user_token:
        try:
            logger.info(f"Calling external API saveRwsProjectAll with payload: {json.dumps(payload, ensure_ascii=False)}")
            async with httpx.AsyncClient() as client:
                headers = {"Authorization": user_token}
                response = await client.post(
                    settings.IWRS_SAVE_PROJECT_ALL_URL,
                    json=payload,
                    headers=headers,
                    timeout=10.0
                )
                res_data = response.json()
                logger.info(f"External API response: {res_data}")
                
                if str(res_data.get("code")) == "1":
                    rws_project_id = str(res_data.get("data", ""))
                    if rws_project_id and rws_project_id != "None":
                        trial.trial_code = rws_project_id
                        # 在异步代码中执行属性更新后，如果不显式刷新可能触发隐式 IO
                        db.add(trial)
                        await db.commit()
                        await db.refresh(trial)
        except Exception as e:
            logger.error(f"Failed to call external API saveRwsProjectAll: {e}")

    return {"message": "试验创建成功", "data": trial_to_dict(trial)}


@router.get("/statistics", summary="试验统计概览")
async def get_trial_statistics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取全局统计数据（用于 Dashboard）"""
    # 各状态数量
    status_counts = await db.execute(
        select(Trial.status, func.count(Trial.id)).group_by(Trial.status)
    )
    status_map = {row[0]: row[1] for row in status_counts}

    # 总试验数
    total_result = await db.execute(select(func.count(Trial.id)))
    total = total_result.scalar()

    # 总患者数
    patient_result = await db.execute(select(func.count(Patient.id)))
    total_patients = patient_result.scalar()

    # 入组中患者数
    enrolled_result = await db.execute(
        select(func.count(Patient.id)).where(Patient.status == "ENROLLED")
    )
    enrolled_patients = enrolled_result.scalar()

    # 总预算
    budget_result = await db.execute(
        select(func.sum(Trial.total_budget))
    )
    total_budget = budget_result.scalar() or 0

    return {
        "total_trials": total,
        "by_status": status_map,
        "ongoing": status_map.get("ONGOING", 0),
        "planning": status_map.get("PLANNING", 0),
        "completed": status_map.get("COMPLETED", 0),
        "total_patients": total_patients,
        "enrolled_patients": enrolled_patients,
        "total_budget": float(total_budget),
    }


@router.get("/{trial_id}", summary="获取试验详情")
async def get_trial(
    trial_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取单个试验详情"""
    result = await db.execute(select(Trial).options(selectinload(Trial.extension)).where(Trial.id == trial_id))
    trial = result.scalar_one_or_none()
    if not trial:
        raise HTTPException(status_code=404, detail="试验不存在")
    return {"data": trial_to_dict(trial)}


@router.put("/{trial_id}", summary="更新试验信息")
async def update_trial(
    trial_id: UUID,
    body: TrialUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trial:write")),
):
    """更新试验基本信息"""
    result = await db.execute(select(Trial).options(selectinload(Trial.extension)).where(Trial.id == trial_id))
    trial = result.scalar_one_or_none()
    if not trial:
        raise HTTPException(status_code=404, detail="试验不存在")

    update_data = body.model_dump(exclude_unset=True)
    extra_data = update_data.pop("extra_data", None)

    for key, value in update_data.items():
        setattr(trial, key, value)

    if extra_data is not None:
        from app.models.models import TrialExtension
        if trial.extension:
            trial.extension.extra_data = extra_data
        else:
            extension = TrialExtension(trial=trial, extra_data=extra_data)
            db.add(extension)

    await db.commit()
    await db.refresh(trial)
    return {"message": "更新成功", "data": trial_to_dict(trial)}


@router.delete("/{trial_id}", summary="删除试验（物理删除）")
async def delete_trial(
    trial_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trial:delete")),
):
    """物理删除试验及其关联数据"""
    result = await db.execute(select(Trial).where(Trial.id == trial_id))
    trial = result.scalar_one_or_none()
    if not trial:
        raise HTTPException(status_code=404, detail="试验不存在")

    await db.execute(delete(Notification).where(Notification.trial_id == trial_id))
    await db.execute(delete(ScreeningRecord).where(ScreeningRecord.trial_id == trial_id))
    await db.execute(delete(Document).where(Document.trial_id == trial_id))
    await db.execute(delete(ETMFFolder).where(ETMFFolder.trial_id == trial_id))
    await db.execute(delete(QCIssue).where(QCIssue.trial_id == trial_id))
    await db.execute(delete(MonitoringReport).where(MonitoringReport.trial_id == trial_id))
    await db.execute(delete(Payment).where(Payment.trial_id == trial_id))
    await db.execute(delete(Contract).where(Contract.trial_id == trial_id))

    await db.execute(delete(DrugDispensing).where(DrugDispensing.trial_id == trial_id))
    await db.execute(delete(DrugBatch).where(DrugBatch.trial_id == trial_id))

    schemes_result = await db.execute(select(RandomizationScheme.id).where(RandomizationScheme.trial_id == trial_id))
    scheme_ids = schemes_result.scalars().all()
    if scheme_ids:
        await db.execute(delete(SubjectRandomization).where(SubjectRandomization.scheme_id.in_(scheme_ids)))
        await db.execute(delete(RandomizationCode).where(RandomizationCode.scheme_id.in_(scheme_ids)))
    await db.execute(delete(RandomizationScheme).where(RandomizationScheme.trial_id == trial_id))

    await db.execute(delete(AdverseEvent).where(AdverseEvent.trial_id == trial_id))
    await db.execute(delete(PatientVisit).where(PatientVisit.trial_id == trial_id))
    await db.execute(delete(EConsent).where(EConsent.trial_id == trial_id))
    await db.execute(delete(Patient).where(Patient.trial_id == trial_id))
    await db.execute(delete(VisitSchedule).where(VisitSchedule.trial_id == trial_id))
    await db.execute(delete(TrialMilestone).where(TrialMilestone.trial_id == trial_id))
    await db.execute(delete(TrialSite).where(TrialSite.trial_id == trial_id))
    await db.execute(delete(Trial).where(Trial.id == trial_id))

    await db.commit()
    return {"message": "试验已删除"}


# ─── 里程碑 ───────────────────────────────────────────────────────

@router.get("/{trial_id}/milestones", summary="获取里程碑列表")
async def get_milestones(
    trial_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(TrialMilestone)
        .where(TrialMilestone.trial_id == trial_id)
        .order_by(TrialMilestone.planned_date)
    )
    milestones = result.scalars().all()
    return {
        "data": [{
            "id": str(m.id),
            "name": m.name,
            "milestone_type": m.milestone_type,
            "planned_date": m.planned_date.isoformat() if m.planned_date else None,
            "actual_date": m.actual_date.isoformat() if m.actual_date else None,
            "status": m.status,
            "notes": m.notes,
        } for m in milestones]
    }


@router.post("/{trial_id}/milestones", summary="添加里程碑", status_code=201)
async def create_milestone(
    trial_id: UUID,
    body: MilestoneCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trial:write")),
):
    milestone = TrialMilestone(
        trial_id=trial_id,
        **body.model_dump(exclude_none=True)
    )
    db.add(milestone)
    await db.commit()
    return {"message": "里程碑添加成功", "data": {"id": str(milestone.id)}}


@router.put("/{trial_id}/milestones/{milestone_id}", summary="更新里程碑")
async def update_milestone(
    trial_id: UUID,
    milestone_id: UUID,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("trial:write")),
):
    result = await db.execute(
        select(TrialMilestone).where(
            and_(TrialMilestone.id == milestone_id, TrialMilestone.trial_id == trial_id)
        )
    )
    m = result.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="里程碑不存在")
    for key, val in body.items():
        if hasattr(m, key):
            # Convert string dates to python date objects if necessary
            if key in ["planned_date", "actual_date"] and isinstance(val, str):
                try:
                    val = datetime.strptime(val, "%Y-%m-%d").date()
                except ValueError:
                    pass
            setattr(m, key, val)
    await db.commit()
    return {"message": "更新成功"}
