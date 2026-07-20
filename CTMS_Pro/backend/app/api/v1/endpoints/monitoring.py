<<<<<<< HEAD
"""
质控监查 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.db.session import get_db
from app.models.models import MonitoringReport, QCIssue, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class MonitoringReportCreate(BaseModel):
    trial_id: UUID
    site_id: Optional[UUID] = None
    visit_type: str
    visit_date: date
    overall_rating: str = "GREEN"
    findings: Optional[List[dict]] = []
    actions: Optional[List[dict]] = []


class QCIssueCreate(BaseModel):
    trial_id: UUID
    site_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    category: str
    severity: str
    description: str
    due_date: Optional[date] = None
    assigned_to: Optional[UUID] = None


class QCIssueUpdate(BaseModel):
    status: Optional[str] = None
    resolution: Optional[str] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None


def report_to_dict(r: MonitoringReport) -> dict:
    return {
        "id": str(r.id),
        "report_no": r.report_no,
        "trial_id": str(r.trial_id) if r.trial_id else None,
        "site_id": str(r.site_id) if r.site_id else None,
        "visit_type": r.visit_type,
        "visit_date": r.visit_date.isoformat() if r.visit_date else None,
        "overall_rating": r.overall_rating,
        "findings": r.findings or [],
        "actions": r.actions or [],
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def issue_to_dict(i: QCIssue) -> dict:
    return {
        "id": str(i.id),
        "issue_no": i.issue_no,
        "trial_id": str(i.trial_id) if i.trial_id else None,
        "category": i.category,
        "severity": i.severity,
        "description": i.description,
        "due_date": i.due_date.isoformat() if i.due_date else None,
        "status": i.status,
        "assigned_to": str(i.assigned_to) if i.assigned_to else None,
        "resolution": i.resolution,
        "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
        "created_at": i.created_at.isoformat() if i.created_at else None,
    }


def generate_report_no() -> str:
    from datetime import datetime
    import random, string
    ts = datetime.now().strftime("%Y%m%d")
    rand = "".join(random.choices(string.digits, k=4))
    return f"MR-{ts}-{rand}"


def generate_issue_no() -> str:
    from datetime import datetime
    import random, string
    ts = datetime.now().strftime("%Y%m%d")
    rand = "".join(random.choices(string.digits, k=4))
    return f"QC-{ts}-{rand}"


@router.get("/reports", summary="监查报告列表")
async def list_monitoring_reports(
    trial_id: Optional[UUID] = Query(None),
    site_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(MonitoringReport)
    filters = []
    if trial_id:
        filters.append(MonitoringReport.trial_id == trial_id)
    if site_id:
        filters.append(MonitoringReport.site_id == site_id)
    if status:
        filters.append(MonitoringReport.status == status)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query.order_by(desc(MonitoringReport.visit_date)))
    reports = result.scalars().all()
    return {"total": len(reports), "items": [report_to_dict(r) for r in reports]}


@router.post("/reports", summary="提交监查报告", status_code=201)
async def create_monitoring_report(
    body: MonitoringReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("monitoring:write")),
):
    report = MonitoringReport(
        report_no=generate_report_no(),
        trial_id=body.trial_id,
        site_id=body.site_id,
        monitor_user_id=current_user.id,
        visit_type=body.visit_type,
        visit_date=body.visit_date,
        report_date=date.today(),
        overall_rating=body.overall_rating,
        findings=body.findings or [],
        actions=body.actions or [],
        status="SUBMITTED",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return {"message": "监查报告提交成功", "data": report_to_dict(report)}


@router.delete("/reports/{report_id}", summary="删除监查报告")
async def delete_monitoring_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("monitoring:write")),
):
    result = await db.execute(select(MonitoringReport).where(MonitoringReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="监查报告不存在")
        
    await db.delete(report)
    await db.commit()
    return {"message": "监查报告删除成功"}


@router.get("/issues", summary="质控问题列表")
async def list_qc_issues(
    trial_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(QCIssue)
    filters = []
    if trial_id:
        filters.append(QCIssue.trial_id == trial_id)
    if status:
        filters.append(QCIssue.status == status)
    if severity:
        filters.append(QCIssue.severity == severity)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query.order_by(desc(QCIssue.created_at)))
    issues = result.scalars().all()
    return {"total": len(issues), "items": [issue_to_dict(i) for i in issues]}


@router.post("/issues", summary="新增质控问题", status_code=201)
async def create_qc_issue(
    body: QCIssueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("qc:write")),
):
    issue = QCIssue(
        issue_no=generate_issue_no(),
        **body.model_dump(exclude_none=True),
        status="OPEN",
    )
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
    return {"message": "质控问题记录成功", "data": issue_to_dict(issue)}


@router.put("/issues/{issue_id}", summary="更新质控问题")
async def update_qc_issue(
    issue_id: UUID,
    body: QCIssueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("qc:write")),
):
    result = await db.execute(select(QCIssue).where(QCIssue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="质控问题不存在")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(issue, key, val)

    # 自动记录解决时间
    if body.status in ("RESOLVED", "CLOSED") and not issue.resolved_at:
        from datetime import datetime, timezone
        issue.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    return {"message": "更新成功", "data": issue_to_dict(issue)}
=======
"""
质控监查 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import Optional, List
from datetime import date
from uuid import UUID

from app.db.session import get_db
from app.models.models import MonitoringReport, QCIssue, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class MonitoringReportCreate(BaseModel):
    trial_id: UUID
    site_id: Optional[UUID] = None
    visit_type: str
    visit_date: date
    overall_rating: str = "GREEN"
    findings: Optional[List[dict]] = []
    actions: Optional[List[dict]] = []


class QCIssueCreate(BaseModel):
    trial_id: UUID
    site_id: Optional[UUID] = None
    report_id: Optional[UUID] = None
    category: str
    severity: str
    description: str
    due_date: Optional[date] = None
    assigned_to: Optional[UUID] = None


class QCIssueUpdate(BaseModel):
    status: Optional[str] = None
    resolution: Optional[str] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None


def report_to_dict(r: MonitoringReport) -> dict:
    return {
        "id": str(r.id),
        "report_no": r.report_no,
        "trial_id": str(r.trial_id) if r.trial_id else None,
        "site_id": str(r.site_id) if r.site_id else None,
        "visit_type": r.visit_type,
        "visit_date": r.visit_date.isoformat() if r.visit_date else None,
        "overall_rating": r.overall_rating,
        "findings": r.findings or [],
        "actions": r.actions or [],
        "status": r.status,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def issue_to_dict(i: QCIssue) -> dict:
    return {
        "id": str(i.id),
        "issue_no": i.issue_no,
        "trial_id": str(i.trial_id) if i.trial_id else None,
        "category": i.category,
        "severity": i.severity,
        "description": i.description,
        "due_date": i.due_date.isoformat() if i.due_date else None,
        "status": i.status,
        "assigned_to": str(i.assigned_to) if i.assigned_to else None,
        "resolution": i.resolution,
        "resolved_at": i.resolved_at.isoformat() if i.resolved_at else None,
        "created_at": i.created_at.isoformat() if i.created_at else None,
    }


def generate_report_no() -> str:
    from datetime import datetime
    import random, string
    ts = datetime.now().strftime("%Y%m%d")
    rand = "".join(random.choices(string.digits, k=4))
    return f"MR-{ts}-{rand}"


def generate_issue_no() -> str:
    from datetime import datetime
    import random, string
    ts = datetime.now().strftime("%Y%m%d")
    rand = "".join(random.choices(string.digits, k=4))
    return f"QC-{ts}-{rand}"


@router.get("/reports", summary="监查报告列表")
async def list_monitoring_reports(
    trial_id: Optional[UUID] = Query(None),
    site_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(MonitoringReport)
    filters = []
    if trial_id:
        filters.append(MonitoringReport.trial_id == trial_id)
    if site_id:
        filters.append(MonitoringReport.site_id == site_id)
    if status:
        filters.append(MonitoringReport.status == status)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query.order_by(desc(MonitoringReport.visit_date)))
    reports = result.scalars().all()
    return {"total": len(reports), "items": [report_to_dict(r) for r in reports]}


@router.post("/reports", summary="提交监查报告", status_code=201)
async def create_monitoring_report(
    body: MonitoringReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("monitoring:write")),
):
    report = MonitoringReport(
        report_no=generate_report_no(),
        trial_id=body.trial_id,
        site_id=body.site_id,
        monitor_user_id=current_user.id,
        visit_type=body.visit_type,
        visit_date=body.visit_date,
        report_date=date.today(),
        overall_rating=body.overall_rating,
        findings=body.findings or [],
        actions=body.actions or [],
        status="SUBMITTED",
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    return {"message": "监查报告提交成功", "data": report_to_dict(report)}


@router.delete("/reports/{report_id}", summary="删除监查报告")
async def delete_monitoring_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("monitoring:write")),
):
    result = await db.execute(select(MonitoringReport).where(MonitoringReport.id == report_id))
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="监查报告不存在")
        
    await db.delete(report)
    await db.commit()
    return {"message": "监查报告删除成功"}


@router.get("/issues", summary="质控问题列表")
async def list_qc_issues(
    trial_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(QCIssue)
    filters = []
    if trial_id:
        filters.append(QCIssue.trial_id == trial_id)
    if status:
        filters.append(QCIssue.status == status)
    if severity:
        filters.append(QCIssue.severity == severity)
    if filters:
        query = query.where(and_(*filters))

    result = await db.execute(query.order_by(desc(QCIssue.created_at)))
    issues = result.scalars().all()
    return {"total": len(issues), "items": [issue_to_dict(i) for i in issues]}


@router.post("/issues", summary="新增质控问题", status_code=201)
async def create_qc_issue(
    body: QCIssueCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("qc:write")),
):
    issue = QCIssue(
        issue_no=generate_issue_no(),
        **body.model_dump(exclude_none=True),
        status="OPEN",
    )
    db.add(issue)
    await db.commit()
    await db.refresh(issue)
    return {"message": "质控问题记录成功", "data": issue_to_dict(issue)}


@router.put("/issues/{issue_id}", summary="更新质控问题")
async def update_qc_issue(
    issue_id: UUID,
    body: QCIssueUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("qc:write")),
):
    result = await db.execute(select(QCIssue).where(QCIssue.id == issue_id))
    issue = result.scalar_one_or_none()
    if not issue:
        raise HTTPException(status_code=404, detail="质控问题不存在")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(issue, key, val)

    # 自动记录解决时间
    if body.status in ("RESOLVED", "CLOSED") and not issue.resolved_at:
        from datetime import datetime, timezone
        issue.resolved_at = datetime.now(timezone.utc)

    await db.commit()
    return {"message": "更新成功", "data": issue_to_dict(issue)}
>>>>>>> origin/main
