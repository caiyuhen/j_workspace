"""
药品管理 API - 入库/发放/回收/库存
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime, timezone
from uuid import UUID

from app.db.session import get_db
from app.models.models import DrugBatch, DrugDispensing, User, AuditLog
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


class DrugBatchCreate(BaseModel):
    trial_id: UUID
    batch_no: str
    drug_name: str
    drug_code: Optional[str] = None
    drug_form: Optional[str] = None
    dosage: Optional[str] = None
    manufacturer: Optional[str] = None
    manufacture_date: Optional[date] = None
    expiry_date: date
    received_qty: int = Field(..., gt=0)
    unit: str = "片/粒"
    storage_condition: Optional[str] = None
    storage_site: Optional[UUID] = None
    is_blinded: bool = False


class DrugDispenseCreate(BaseModel):
    batch_id: UUID
    patient_id: UUID
    visit_id: Optional[UUID] = None
    trial_id: UUID
    dispense_qty: int = Field(..., gt=0)
    randomization_no: Optional[str] = None
    kit_no: Optional[str] = None
    notes: Optional[str] = None


class DrugReturnCreate(BaseModel):
    dispense_id: str
    returned_qty: int = Field(..., gt=0)
    notes: Optional[str] = None


def batch_to_dict(b: DrugBatch) -> dict:
    from datetime import date as d
    today = d.today()
    days_to_expiry = (b.expiry_date - today).days if b.expiry_date else None
    return {
        "id": str(b.id),
        "trial_id": str(b.trial_id) if b.trial_id else None,
        "batch_no": b.batch_no,
        "drug_name": b.drug_name,
        "drug_code": b.drug_code,
        "drug_form": b.drug_form,
        "dosage": b.dosage,
        "manufacturer": b.manufacturer,
        "manufacture_date": b.manufacture_date.isoformat() if b.manufacture_date else None,
        "expiry_date": b.expiry_date.isoformat() if b.expiry_date else None,
        "days_to_expiry": days_to_expiry,
        "expiry_warning": days_to_expiry is not None and days_to_expiry <= 30,
        "received_qty": b.received_qty,
        "current_qty": b.current_qty,
        "dispensed_qty": b.dispensed_qty,
        "returned_qty": b.returned_qty,
        "destroyed_qty": b.destroyed_qty,
        "unit": b.unit,
        "storage_condition": b.storage_condition,
        "current_temp": float(b.current_temp) if b.current_temp else None,
        "is_blinded": b.is_blinded,
        "status": b.status,
        "received_at": b.received_at.isoformat() if b.received_at else None,
    }


@router.get("/batches", summary="药品批次列表")
async def list_batches(
    trial_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    expiry_warning: bool = Query(False, description="只显示近效期（≤30天）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(DrugBatch)
    filters = []
    if trial_id:
        filters.append(DrugBatch.trial_id == trial_id)
    if status:
        filters.append(DrugBatch.status == status)
    if expiry_warning:
        from datetime import date, timedelta
        warn_date = date.today() + timedelta(days=30)
        filters.append(DrugBatch.expiry_date <= warn_date)
        filters.append(DrugBatch.status == "ACTIVE")
    if filters:
        query = query.where(and_(*filters))

    # 数据隔离：非管理员只能看自己负责的试验或所属中心相关的试验的药品
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
        cond = (DrugBatch.trial_id.in_(subq)) | (DrugBatch.trial_id.in_(subq2))
        query = query.where(cond)

    result = await db.execute(query.order_by(DrugBatch.expiry_date))
    batches = result.scalars().all()
    return {"total": len(batches), "items": [batch_to_dict(b) for b in batches]}


@router.post("/batches", summary="药品入库", status_code=201)
async def create_batch(
    body: DrugBatchCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("drug:write")),
):
    exists = await db.execute(select(DrugBatch).where(DrugBatch.batch_no == body.batch_no))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"批号 {body.batch_no} 已存在")

    batch = DrugBatch(
        **body.model_dump(exclude_none=True),
        current_qty=body.received_qty,
        dispensed_qty=0,
        returned_qty=0,
        destroyed_qty=0,
        status="ACTIVE",
        received_by=current_user.id,
        received_at=datetime.now(timezone.utc),
    )
    db.add(batch)
    await db.commit()
    await db.refresh(batch)
    
    # 补充记录详细参数到 audit_log
    request.state.audit_new_values = body.model_dump(mode='json')
    
    return {"message": "药品入库成功", "data": batch_to_dict(batch)}


@router.post("/dispense", summary="药品发放", status_code=201)
async def dispense_drug(
    body: DrugDispenseCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("drug:write")),
):
    """发放药品给受试者，自动扣减库存"""
    batch = (await db.execute(select(DrugBatch).where(DrugBatch.id == body.batch_id))).scalar_one_or_none()
    if not batch:
        raise HTTPException(status_code=404, detail="药品批次不存在")
    if batch.current_qty < body.dispense_qty:
        raise HTTPException(status_code=400, detail=f"库存不足，当前库存 {batch.current_qty} {batch.unit}")
    if batch.status != "ACTIVE":
        raise HTTPException(status_code=400, detail="该批次药品已不可用")

    # 更新库存
    batch.current_qty -= body.dispense_qty
    batch.dispensed_qty += body.dispense_qty
    if batch.current_qty == 0:
        batch.status = "DEPLETED"

    dispense = DrugDispensing(
        batch_id=body.batch_id,
        patient_id=body.patient_id,
        visit_id=body.visit_id,
        trial_id=body.trial_id,
        dispense_qty=body.dispense_qty,
        randomization_no=body.randomization_no,
        kit_no=body.kit_no,
        dispensed_by=current_user.id,
        dispensed_at=datetime.now(timezone.utc),
        notes=body.notes,
    )
    db.add(dispense)
    await db.commit()
    
    request.state.audit_new_values = body.model_dump(mode='json')
    
    return {"message": "药品发放成功", "data": {"dispense_id": str(dispense.id), "remaining_qty": batch.current_qty}}


@router.post("/return", summary="药品回收")
async def return_drug(
    body: DrugReturnCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("drug:write")),
):
    """回收已发放的药品，记录回收数量（不加回库存，进入待销毁状态）"""
    # 由于前端传来的 dispense_id 可能是 AuditLog 的 id (出于我们复用稽查日志作为流水的原因)
    # 我们需要先看看它是不是真的 dispense_id，如果是 audit_log_id 就先找到对应的 dispense_id
    dispense_id = body.dispense_id
    
    # 尝试判断是否是 AuditLog
    # 如果前端传来的 id 是数字形式的字符串（如 "129"），这代表它是 AuditLog 的 BigInteger 主键
    if dispense_id.isdigit():
        log_query = await db.execute(select(AuditLog).where(AuditLog.id == int(dispense_id)))
        audit_log = log_query.scalar_one_or_none()
        if audit_log and audit_log.new_values and "batch_id" in audit_log.new_values:
            # 如果这是一个发药审计日志，我们要去找到真实的 dispense 记录
            real_dispense_id = audit_log.new_values.get("id")
            if real_dispense_id:
                dispense_id = real_dispense_id
            else:
                # 根据 batch_id 和 patient_id 去查最近一条
                batch_id = audit_log.new_values.get("batch_id")
                patient_id = audit_log.new_values.get("patient_id")
                d_query = await db.execute(
                    select(DrugDispensing)
                    .where(DrugDispensing.batch_id == batch_id, DrugDispensing.patient_id == patient_id)
                    .order_by(DrugDispensing.dispensed_at.desc())
                )
                real_d = d_query.scalars().first()
                if real_d:
                    dispense_id = str(real_d.id)
                    
    # 确保最终查发药表时 dispense_id 可以被转为 UUID
    try:
        query_id = UUID(dispense_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="无效的发药记录ID格式")

    dispense = (await db.execute(select(DrugDispensing).where(DrugDispensing.id == query_id))).scalar_one_or_none()
    if not dispense:
        raise HTTPException(status_code=404, detail="发药记录不存在或无法关联")

    # 校验数量
    current_returned = dispense.returned_qty or 0
    max_returnable = dispense.dispense_qty - current_returned
    if body.returned_qty > max_returnable:
        raise HTTPException(status_code=400, detail=f"回收数量不能大于可回收数量 ({max_returnable})")

    # 更新 dispense
    dispense.returned_qty = current_returned + body.returned_qty
    dispense.returned_at = datetime.now(timezone.utc)
    if body.notes:
        dispense.notes = f"{dispense.notes or ''} [回收备注]: {body.notes}"

    # 更新 batch
    batch = (await db.execute(select(DrugBatch).where(DrugBatch.id == dispense.batch_id))).scalar_one_or_none()
    if batch:
        batch.returned_qty = (batch.returned_qty or 0) + body.returned_qty

    await db.commit()
    
    # 补充审计参数
    request.state.audit_new_values = body.model_dump(mode='json')
    request.state.audit_new_values["dispense_id"] = str(dispense_id) # 确保覆盖为真实的

    return {"message": "药品回收成功", "data": {"dispense_id": str(dispense.id), "total_returned": dispense.returned_qty}}


class DrugDestructionUpdate(BaseModel):
    status: str
    proofUrl: Optional[str] = None
    proofName: Optional[str] = None

@router.put("/logs/{log_id}/destruction", summary="更新药品销毁状态")
async def update_destruction_status(
    log_id: str,
    body: DrugDestructionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("drug:write")),
):
    if not log_id.isdigit():
        raise HTTPException(status_code=400, detail="无效的日志ID")
    
    log_query = await db.execute(select(AuditLog).where(AuditLog.id == int(log_id)))
    audit_log = log_query.scalar_one_or_none()
    if not audit_log:
        raise HTTPException(status_code=404, detail="回收记录不存在")
        
    new_vals = audit_log.new_values or {}
    # 由于 new_values 是 JSONB 且可能受 SQLAlchemy 检测不到原地修改的影响
    # 需创建新 dict 并重新赋值
    updated_vals = dict(new_vals)
    updated_vals["destruction_status"] = body.status
    if body.proofUrl:
        updated_vals["proofUrl"] = body.proofUrl
    if body.proofName:
        updated_vals["proofName"] = body.proofName
        
    audit_log.new_values = updated_vals
    
    await db.commit()
    return {"message": "销毁状态更新成功"}

@router.get("/logs", summary="药品操作流水日志")
async def list_drug_logs(
    trial_id: Optional[UUID] = Query(None),
    limit: int = Query(500, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取药品的入库、发放、回收流水日志（基于审计轨迹表）"""
    query = select(AuditLog).where(AuditLog.module.like("%/api/v1/drugs%"))
    
    # 粗略地把 POST /batches 算作入库(inbound)，POST /dispense 算作发放(dispatch)，POST /return 算作回收(return)
    result = await db.execute(query.order_by(desc(AuditLog.created_at)).limit(limit))
    logs = result.scalars().all()
    
    parsed_logs = []
    for log in logs:
        action_path = log.resource_type or ""
        op_type = "unknown"
        qty = 0
        drug_id = None
        patient_id = None
        remark = log.error_message or "正常"
        req_body = log.new_values or {}
        
        # 尝试从请求体/响应体解析明细
        try:
            if "batches" in action_path or (log.action == "CREATE" and "batch_no" in req_body):
                op_type = "inbound"
                qty = req_body.get("received_qty", 0)
                drug_id = req_body.get("drug_name", req_body.get("batch_no", "未知批次"))
            elif "dispense" in action_path or (log.action == "CREATE" and "dispense_qty" in req_body):
                op_type = "dispatch"
                qty = req_body.get("dispense_qty", 0)
                drug_id = req_body.get("batch_id", "未知批次")
                patient_id = req_body.get("patient_id", "未知受试者")
            elif "return" in action_path or (log.action == "CREATE" and "returned_qty" in req_body) or "destruction_status" in req_body:
                op_type = "return"
                qty = req_body.get("returned_qty", 0)
                drug_id = req_body.get("dispense_id", "未知发放记录")
        except:
            pass

        parsed_logs.append({
            "id": str(log.id),
            "date": log.created_at.isoformat() if log.created_at else "",
            "type": op_type,
            "drugId": drug_id,
            "qty": qty,
            "operator": log.username,
            "remark": remark,
            "patientId": patient_id,
            "destruction_status": req_body.get("destruction_status") if op_type == "return" else None,
            "proofUrl": req_body.get("proofUrl"),
            "proofName": req_body.get("proofName")
        })
        
    return parsed_logs

@router.get("/inventory-summary", summary="库存汇总")
async def inventory_summary(
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """按药品汇总库存情况"""
    query = select(
        DrugBatch.drug_name,
        func.sum(DrugBatch.current_qty).label("total_current"),
        func.sum(DrugBatch.received_qty).label("total_received"),
        func.sum(DrugBatch.dispensed_qty).label("total_dispensed"),
        func.count(DrugBatch.id).label("batch_count"),
    ).group_by(DrugBatch.drug_name)

    if trial_id:
        query = query.where(DrugBatch.trial_id == trial_id)

    # 数据隔离
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
        cond = (DrugBatch.trial_id.in_(subq)) | (DrugBatch.trial_id.in_(subq2))
        query = query.where(cond)

    result = await db.execute(query)
    rows = result.all()
    return {
        "data": [{
            "drug_name": row[0],
            "total_current": int(row[1] or 0),
            "total_received": int(row[2] or 0),
            "total_dispensed": int(row[3] or 0),
            "batch_count": int(row[4] or 0),
        } for row in rows]
    }
