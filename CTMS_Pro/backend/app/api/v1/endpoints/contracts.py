"""
经费管理 API（合同 + 付款）
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel
from typing import Optional
from datetime import date
from uuid import UUID
from decimal import Decimal

from app.db.session import get_db
from app.models.models import Contract, Payment, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class ContractCreate(BaseModel):
    contract_no: str
    trial_id: Optional[UUID] = None
    site_id: Optional[UUID] = None
    title: str
    contract_type: Optional[str] = None
    party_name: Optional[str] = None
    total_amount: Optional[float] = None
    currency: str = "CNY"
    sign_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    payment_terms: Optional[str] = None


class PaymentCreate(BaseModel):
    contract_id: UUID
    trial_id: UUID
    payment_type: Optional[str] = None
    description: Optional[str] = None
    planned_amount: float
    planned_date: Optional[date] = None
    notes: Optional[str] = None


class PaymentUpdate(BaseModel):
    actual_amount: Optional[float] = None
    actual_date: Optional[date] = None
    status: Optional[str] = None
    invoice_no: Optional[str] = None
    invoice_date: Optional[date] = None
    invoice_amount: Optional[float] = None
    notes: Optional[str] = None


def contract_to_dict(c: Contract) -> dict:
    return {
        "id": str(c.id),
        "contract_no": c.contract_no,
        "trial_id": str(c.trial_id) if c.trial_id else None,
        "site_id": str(c.site_id) if c.site_id else None,
        "title": c.title,
        "contract_type": c.contract_type,
        "party_name": c.party_name,
        "total_amount": float(c.total_amount) if c.total_amount else None,
        "currency": c.currency,
        "sign_date": c.sign_date.isoformat() if c.sign_date else None,
        "start_date": c.start_date.isoformat() if c.start_date else None,
        "end_date": c.end_date.isoformat() if c.end_date else None,
        "status": c.status,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }


def payment_to_dict(p: Payment) -> dict:
    return {
        "id": str(p.id),
        "contract_id": str(p.contract_id) if p.contract_id else None,
        "trial_id": str(p.trial_id) if p.trial_id else None,
        "payment_type": p.payment_type,
        "description": p.description,
        "planned_amount": float(p.planned_amount) if p.planned_amount else None,
        "actual_amount": float(p.actual_amount) if p.actual_amount else None,
        "planned_date": p.planned_date.isoformat() if p.planned_date else None,
        "actual_date": p.actual_date.isoformat() if p.actual_date else None,
        "status": p.status,
        "invoice_no": p.invoice_no,
        "invoice_date": p.invoice_date.isoformat() if p.invoice_date else None,
        "invoice_amount": float(p.invoice_amount) if p.invoice_amount else None,
        "notes": p.notes,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }


# ─── 合同 ─────────────────────────────────────────────────────────

@router.get("/contracts", summary="合同列表")
async def list_contracts(
    trial_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Contract)
    filters = []
    if trial_id:
        filters.append(Contract.trial_id == trial_id)
    if status:
        filters.append(Contract.status == status)
    if filters:
        query = query.where(and_(*filters))

    # 数据隔离：非管理员只能看到自己创建的合同
    if not current_user.is_superuser:
        query = query.where(Contract.created_by == current_user.id)

    result = await db.execute(query.order_by(desc(Contract.created_at)))
    contracts = result.scalars().all()
    return {"total": len(contracts), "items": [contract_to_dict(c) for c in contracts]}


@router.post("/contracts", summary="创建合同", status_code=201)
async def create_contract(
    body: ContractCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("finance:write")),
):
    exists = await db.execute(select(Contract).where(Contract.contract_no == body.contract_no))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="合同编号已存在")

    contract = Contract(**body.model_dump(exclude_none=True), created_by=current_user.id)
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return {"message": "合同创建成功", "data": contract_to_dict(contract)}


# ─── 付款 ─────────────────────────────────────────────────────────

@router.get("/payments", summary="付款记录列表")
async def list_payments(
    trial_id: Optional[UUID] = Query(None),
    contract_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Payment)
    filters = []
    if trial_id:
        filters.append(Payment.trial_id == trial_id)
    if contract_id:
        filters.append(Payment.contract_id == contract_id)
    if status:
        filters.append(Payment.status == status)
    if filters:
        query = query.where(and_(*filters))

    # 数据隔离：非管理员只能看自己负责的试验或所属中心相关的付款
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq2 = select(TrialSite.trial_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        cond = (Payment.trial_id.in_(subq)) | (Payment.trial_id.in_(subq2))
        query = query.where(cond)

    result = await db.execute(query.order_by(Payment.planned_date))
    payments = result.scalars().all()
    return {"total": len(payments), "items": [payment_to_dict(p) for p in payments]}


@router.post("/payments", summary="添加付款计划", status_code=201)
async def create_payment(
    body: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("budget:write")),
):
    payment = Payment(**body.model_dump(exclude_none=True), status="PENDING", created_by=current_user.id)
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return {"message": "付款计划添加成功", "data": payment_to_dict(payment)}


@router.put("/payments/{payment_id}", summary="更新付款状态")
async def update_payment(
    payment_id: UUID,
    body: PaymentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("budget:write")),
):
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="付款记录不存在")

    for key, val in body.model_dump(exclude_none=True).items():
        setattr(payment, key, val)
    await db.commit()
    return {"message": "更新成功", "data": payment_to_dict(payment)}


@router.get("/budget-summary", summary="预算汇总")
async def budget_summary(
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """按试验汇总预算执行情况"""
    from app.models.models import Trial
    query = select(
        Trial.id, Trial.short_name, Trial.total_budget, Trial.spent_amount, Trial.currency
    )
    if trial_id:
        query = query.where(Trial.id == trial_id)

    # 数据隔离：非管理员只能看自己负责的试验或所属中心相关的预算
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Site
        cond = (Trial.pm_user_id == current_user.id) | (Trial.created_by == current_user.id)
        subq2 = select(TrialSite.trial_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        cond = cond | Trial.id.in_(subq2)
        query = query.where(cond)

    result = await db.execute(query)
    rows = result.all()
    return {
        "data": [{
            "trial_id": str(row[0]),
            "trial_name": row[1],
            "total_budget": float(row[2]) if row[2] else 0,
            "spent_amount": float(row[3]) if row[3] else 0,
            "remaining": float(row[2] or 0) - float(row[3] or 0),
            "usage_rate": round(float(row[3] or 0) / float(row[2] or 1) * 100, 2),
            "currency": row[4],
        } for row in rows]
    }
