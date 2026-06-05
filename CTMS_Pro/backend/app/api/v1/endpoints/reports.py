"""
统计报表 API - Dashboard 数据聚合
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import Optional
from uuid import UUID
from datetime import date, timedelta

from app.db.session import get_db
from app.models.models import Trial, Patient, AdverseEvent, DrugBatch, Payment, User, AuditLog
from app.core.dependencies import get_current_active_user

router = APIRouter()


@router.get("/dashboard", summary="Dashboard 数据汇总")
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取系统全局统计数据用于首页 Dashboard"""
    from app.models.models import TrialSite, Site

    # 基础过滤条件
    trial_cond = []
    patient_cond = []
    
    if not current_user.is_superuser:
        subq_trial = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq_site_trial = select(TrialSite.trial_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        trial_cond.append((Trial.id.in_(subq_trial)) | (Trial.id.in_(subq_site_trial)))
        
        subq_site = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        patient_cond.append((Patient.trial_id.in_(subq_trial)) | (Patient.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) | (Patient.site_id.in_(subq_site)))

    def build_query(model, conds, *extra_conds):
        q = select(func.count(model.id))
        all_conds = conds + list(extra_conds)
        if all_conds:
            q = q.where(and_(*all_conds))
        return q

    # 试验统计
    trial_total = (await db.execute(build_query(Trial, trial_cond))).scalar()
    trial_ongoing = (await db.execute(build_query(Trial, trial_cond, Trial.status == "ONGOING"))).scalar()

    # 患者统计
    patient_total = (await db.execute(build_query(Patient, patient_cond))).scalar()
    patient_enrolled = (await db.execute(build_query(Patient, patient_cond, Patient.status == "ENROLLED"))).scalar()
    patient_screening = (await db.execute(build_query(Patient, patient_cond, Patient.status == "SCREENING"))).scalar()
    patient_completed = (await db.execute(build_query(Patient, patient_cond, Patient.status == "COMPLETED"))).scalar()

    # SAE 统计 (通过试验隔离)
    sae_cond = [(AdverseEvent.trial_id.in_(subq_trial)) | (AdverseEvent.trial_id.in_(subq_site_trial))] if not current_user.is_superuser else []
    sae_total = (await db.execute(build_query(AdverseEvent, sae_cond, AdverseEvent.is_serious == True))).scalar()
    sae_pending = (await db.execute(build_query(AdverseEvent, sae_cond, AdverseEvent.is_serious == True, AdverseEvent.report_status == "INITIAL"))).scalar()

    # 药品近效期预警
    warn_date = date.today() + timedelta(days=30)
    drug_cond = [(DrugBatch.trial_id.in_(subq_trial)) | (DrugBatch.trial_id.in_(subq_site_trial))] if not current_user.is_superuser else []
    drug_expiry_warning = (await db.execute(build_query(DrugBatch, drug_cond, DrugBatch.expiry_date <= warn_date, DrugBatch.status == "ACTIVE"))).scalar()

    # 待付款
    payment_cond = [(Payment.trial_id.in_(subq_trial)) | (Payment.trial_id.in_(subq_site_trial))] if not current_user.is_superuser else []
    payment_pending = (await db.execute(build_query(Payment, payment_cond, Payment.status == "PENDING"))).scalar()

    return {
        "trials": {
            "total": trial_total,
            "ongoing": trial_ongoing,
        },
        "patients": {
            "total": patient_total,
            "enrolled": patient_enrolled,
            "screening": patient_screening,
            "completed": patient_completed,
        },
        "sae": {
            "total": sae_total,
            "pending_report": sae_pending,
        },
        "alerts": {
            "drug_expiry_warning": drug_expiry_warning,
            "payment_pending": payment_pending,
        }
    }


@router.get("/enrollment-trend", summary="入组趋势（月度）")
async def enrollment_trend(
    months: int = Query(12, ge=3, le=24),
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取近N月入组趋势数据，用于折线图"""
    from sqlalchemy import extract
    from datetime import datetime

    result = []
    today = date.today()
    for i in range(months - 1, -1, -1):
        # 计算每个月
        month_date = today.replace(day=1) - timedelta(days=i * 28)
        year, month = month_date.year, month_date.month

        query = select(func.count(Patient.id)).where(
            and_(
                extract("year", Patient.enrollment_date) == year,
                extract("month", Patient.enrollment_date) == month,
            )
        )
        if trial_id:
            query = query.where(Patient.trial_id == trial_id)

    # 添加数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Site
        cond = (Patient.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | Patient.trial_id.in_(subq)
        
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | Patient.site_id.in_(subq2)
        query = query.where(cond)

        count = (await db.execute(query)).scalar() or 0
        result.append({
            "period": f"{year}-{month:02d}",
            "enrolled": count,
        })

    return {"data": result}


@router.get("/site-enrollment", summary="各中心入组对比")
async def site_enrollment(
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """各研究中心入组数量对比，用于柱状图"""
    from app.models.models import Site

    query = select(
        Site.name,
        func.count(Patient.id).label("enrolled"),
    ).outerjoin(Patient, and_(
        Patient.site_id == Site.id,
        Patient.status.in_(["ENROLLED", "ACTIVE", "COMPLETED"]),
    ))
    if trial_id:
        query = query.where(Patient.trial_id == trial_id)

    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        cond = (Patient.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | Patient.trial_id.in_(subq)
        
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | Patient.site_id.in_(subq2)
        query = query.where(cond)


    query = query.group_by(Site.id, Site.name).order_by(desc("enrolled")).limit(10)
    result = await db.execute(query)
    rows = result.all()

    return {
        "data": [{"site_name": row[0], "enrolled": row[1] or 0} for row in rows]
    }


@router.get("/ae-summary", summary="AE 统计报表")
async def ae_summary(
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """不良事件统计汇总"""
    filters = []
    if trial_id:
        filters.append(AdverseEvent.trial_id == trial_id)

    base = and_(*filters) if filters else True

    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site, Patient
        subq_trial = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq_site = select(TrialSite.site_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        subq_patient = select(Patient.id).where(Patient.site_id.in_(subq_site))
        
        base = and_(base, (AdverseEvent.trial_id.in_(subq_trial)) | (AdverseEvent.patient_id.in_(subq_patient)))


    # 按严重程度分组
    severity_q = select(
        AdverseEvent.severity, func.count(AdverseEvent.id)
    ).where(base).group_by(AdverseEvent.severity)
    severity_result = await db.execute(severity_q)
    by_severity = {row[0]: row[1] for row in severity_result if row[0]}

    # 按因果关系分组
    relatedness_q = select(
        AdverseEvent.relatedness, func.count(AdverseEvent.id)
    ).where(base).group_by(AdverseEvent.relatedness)
    relatedness_result = await db.execute(relatedness_q)
    by_relatedness = {row[0]: row[1] for row in relatedness_result if row[0]}

    # SAE vs non-SAE
    total_ae = (await db.execute(select(func.count(AdverseEvent.id)).where(base))).scalar() or 0
    total_sae = (await db.execute(
        select(func.count(AdverseEvent.id)).where(and_(base, AdverseEvent.is_serious == True))
    )).scalar() or 0

    return {
        "total_ae": total_ae,
        "total_sae": total_sae,
        "total_non_sae": total_ae - total_sae,
        "by_severity": by_severity,
        "by_relatedness": by_relatedness,
    }


@router.get("/audit-logs", summary="稽查轨迹查询")
async def get_audit_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    user_id: Optional[UUID] = Query(None),
    action: Optional[str] = Query(None),
    module: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """查询稽查轨迹（21 CFR Part 11 合规要求）"""
    query = select(AuditLog)
    count_query = select(func.count(AuditLog.id))
    filters = []

    if user_id:
        filters.append(AuditLog.user_id == user_id)
    if action:
        filters.append(AuditLog.action == action)
    if module:
        filters.append(AuditLog.module == module)
    if start_date:
        from datetime import datetime, timezone
        filters.append(AuditLog.created_at >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        from datetime import datetime
        filters.append(AuditLog.created_at <= datetime.combine(end_date, datetime.max.time()))

    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(desc(AuditLog.created_at)).offset(offset).limit(page_size))
    logs = result.scalars().all()

    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [{
            "id": log.id,
            "event_id": str(log.event_id),
            "username": log.username,
            "user_role": log.user_role,
            "action": log.action,
            "module": log.module,
            "resource_type": log.resource_type,
            "resource_id": log.resource_id,
            "ip_address": str(log.ip_address) if log.ip_address else None,
            "success": log.success,
            "error_message": log.error_message,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        } for log in logs]
    }
