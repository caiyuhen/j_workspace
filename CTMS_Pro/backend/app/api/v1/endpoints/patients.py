"""
患者管理 API
支持 GDPR/HIPAA 合规的 PII 加密存储与访问
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, and_
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from uuid import UUID
import uuid

from app.db.session import get_db
from app.models.models import Patient, EConsent, ScreeningRecord, User
from app.core.security import encrypt_pii, decrypt_pii, mask_phone, mask_name, mask_id_card
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────

class PatientCreate(BaseModel):
    trial_id: UUID
    site_id: Optional[UUID] = None
    patient_no: str = Field(..., description="受试者编号，如 P-001")
    screening_no: Optional[str] = None
    # PII（将被加密）
    full_name: Optional[str] = None
    id_card: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    # 非敏感
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    age: Optional[int] = None
    blood_type: Optional[str] = None
    diagnosis: Optional[str] = None
    icd_code: Optional[str] = None
    disease_stage: Optional[str] = None
    comorbidities: Optional[List[str]] = []
    emr_patient_id: Optional[str] = None
    arm: Optional[str] = None


class PatientUpdate(BaseModel):
    status: Optional[str] = None
    diagnosis: Optional[str] = None
    disease_stage: Optional[str] = None
    assigned_to: Optional[UUID] = None
    site_id: Optional[UUID] = None
    screening_date: Optional[date] = None
    enrollment_date: Optional[date] = None
    completion_date: Optional[date] = None
    arm: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None
    consent_given: Optional[bool] = None


class EConsentCreate(BaseModel):
    trial_id: UUID
    version: str
    language: str = "zh-CN"


def patient_to_dict(p: Patient, include_pii: bool = False) -> dict:
    """转换患者对象为字典，默认脱敏"""
    d = {
        "id": str(p.id),
        "patient_no": p.patient_no,
        "screening_no": p.screening_no,
        "gender": p.gender,
        "birth_year": p.birth_year,
        "age": p.age,
        "blood_type": p.blood_type,
        "diagnosis": p.diagnosis,
        "icd_code": p.icd_code,
        "disease_stage": p.disease_stage,
        "comorbidities": p.comorbidities or [],
        "status": p.status,
        "trial_id": str(p.trial_id) if p.trial_id else None,
        "site_id": str(p.site_id) if p.site_id else None,
        "consent_given": p.consent_given,
        "consent_date": p.consent_date.isoformat() if p.consent_date else None,
        "screening_date": p.screening_date.isoformat() if p.screening_date else None,
        "enrollment_date": p.enrollment_date.isoformat() if p.enrollment_date else None,
        "completion_date": p.completion_date.isoformat() if p.completion_date else None,
        "emr_patient_id": p.emr_patient_id,
        "arm": p.arm,
        "created_at": p.created_at.isoformat() if p.created_at else None,
    }

    # PII 处理
    if include_pii:
        d["full_name"] = decrypt_pii(p.full_name_enc) if p.full_name_enc else None
        d["phone"] = decrypt_pii(p.phone_enc) if p.phone_enc else None
        d["id_card"] = decrypt_pii(p.id_card_enc) if p.id_card_enc else None
    else:
        # 脱敏显示
        name = decrypt_pii(p.full_name_enc) if p.full_name_enc else None
        phone = decrypt_pii(p.phone_enc) if p.phone_enc else None
        d["full_name"] = mask_name(name) if name else None
        d["phone"] = mask_phone(phone) if phone else None
        d["id_card"] = None  # 列表页不显示

    return d


# ─── 端点 ─────────────────────────────────────────────────────────

@router.get("", summary="获取患者列表")
async def list_patients(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    trial_id: Optional[UUID] = Query(None),
    site_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    keyword: Optional[str] = Query(None, description="患者编号或诊断关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取受试者列表，支持分页和多维筛选"""
    query = select(Patient)
    count_query = select(func.count(Patient.id))

    if trial_id:
        query = query.where(Patient.trial_id == trial_id)
        count_query = count_query.where(Patient.trial_id == trial_id)
    if site_id:
        query = query.where(Patient.site_id == site_id)
        count_query = count_query.where(Patient.site_id == site_id)
    if status:
        query = query.where(Patient.status == status)
        count_query = count_query.where(Patient.status == status)
    if keyword:
        kw = f"%{keyword}%"
        cond = Patient.patient_no.ilike(kw) | Patient.diagnosis.ilike(kw)
        query = query.where(cond)
        count_query = count_query.where(cond)

    # 数据隔离：非管理员只能看自己所属中心的患者，或者自己负责的试验项目下的患者
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        cond = (Patient.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | Patient.trial_id.in_(subq)
        
        # 用户作为PI时也可以看该中心的患者
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | Patient.site_id.in_(subq2)
        
        query = query.where(cond)
        count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(
        query.order_by(desc(Patient.created_at)).offset(offset).limit(page_size)
    )
    patients = result.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": [patient_to_dict(p) for p in patients]
    }


@router.post("", summary="新增受试者", status_code=201)
async def create_patient(
    body: PatientCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("patient:write")),
):
    """
    新增受试者
    PII（姓名、手机、身份证）将使用 AES-256 加密存储，符合 GDPR/HIPAA 要求
    """
    # 检查编号唯一性
    exists = await db.execute(
        select(Patient).where(Patient.patient_no == body.patient_no)
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"受试者编号 {body.patient_no} 已存在")

    # 加密 PII
    patient = Patient(
        patient_no=body.patient_no,
        screening_no=body.screening_no,
        trial_id=body.trial_id,
        site_id=body.site_id,
        full_name_enc=encrypt_pii(body.full_name) if body.full_name else None,
        id_card_enc=encrypt_pii(body.id_card) if body.id_card else None,
        phone_enc=encrypt_pii(body.phone) if body.phone else None,
        email_enc=encrypt_pii(body.email) if body.email else None,
        gender=body.gender,
        birth_year=body.birth_year,
        age=body.age,
        blood_type=body.blood_type,
        diagnosis=body.diagnosis,
        icd_code=body.icd_code,
        disease_stage=body.disease_stage,
        comorbidities=body.comorbidities or [],
        emr_patient_id=body.emr_patient_id,
        status="SCREENING",
        created_by=current_user.id,
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)

    # GDPR 日志
    gdpr_entry = {
        "action": "DATA_CREATED",
        "user": current_user.username,
        "timestamp": patient.created_at.isoformat() if patient.created_at else None,
        "purpose": "临床试验受试者管理"
    }
    patient.gdpr_log = [gdpr_entry]
    await db.commit()

    return {"message": "受试者创建成功", "data": patient_to_dict(patient)}


@router.get("/statistics", summary="患者统计")
async def patient_statistics(
    trial_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取患者各状态统计"""
    query = select(Patient.status, func.count(Patient.id)).group_by(Patient.status)
    if trial_id:
        query = query.where(Patient.trial_id == trial_id)

    result = await db.execute(query)
    status_counts = {row[0]: row[1] for row in result}

    total = sum(status_counts.values())
    return {
        "total": total,
        "by_status": status_counts,
        "screening": status_counts.get("SCREENING", 0),
        "enrolled": status_counts.get("ENROLLED", 0),
        "completed": status_counts.get("COMPLETED", 0),
        "withdrawn": status_counts.get("WITHDRAWN", 0),
        "screen_fail": status_counts.get("SCREEN_FAIL", 0),
    }


@router.get("/{patient_id}", summary="获取受试者详情")
async def get_patient(
    patient_id: UUID,
    include_pii: bool = Query(False, description="是否返回明文 PII（需特殊权限）"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """获取受试者详情，PII 数据默认脱敏"""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="受试者不存在")

    # 查看明文 PII 需要管理员权限
    can_view_pii = current_user.is_superuser or include_pii
    return {"data": patient_to_dict(patient, include_pii=can_view_pii)}


@router.put("/{patient_id}", summary="更新受试者信息")
async def update_patient(
    patient_id: UUID,
    body: PatientUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("patient:write")),
):
    """更新受试者信息，PII 字段自动重新加密"""
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    patient = result.scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="受试者不存在")

    update_data = body.model_dump(exclude_unset=True)

    # 处理 PII 字段
    if "full_name" in update_data:
        patient.full_name_enc = encrypt_pii(update_data.pop("full_name"))
    if "phone" in update_data:
        patient.phone_enc = encrypt_pii(update_data.pop("phone"))

    for key, value in update_data.items():
        if hasattr(patient, key):
            # 处理字符串转日期
            if key in ["screening_date", "enrollment_date", "completion_date"] and isinstance(value, str):
                try:
                    from datetime import datetime
                    value = datetime.strptime(value, "%Y-%m-%d").date()
                except ValueError:
                    pass
            setattr(patient, key, value)

    # 追加 GDPR 日志
    from datetime import datetime, timezone
    gdpr_log = patient.gdpr_log or []
    gdpr_log.append({
        "action": "DATA_UPDATED",
        "user": current_user.username,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fields": list(update_data.keys()),
    })
    patient.gdpr_log = gdpr_log

    await db.commit()
    return {"message": "更新成功", "data": patient_to_dict(patient)}


@router.post("/{patient_id}/econsent", summary="发起电子知情同意", status_code=201)
async def create_econsent(
    patient_id: UUID,
    body: EConsentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("econsent:write")),
):
    """创建知情同意书，等待患者签署"""
    patient = (await db.execute(select(Patient).where(Patient.id == patient_id))).scalar_one_or_none()
    if not patient:
        raise HTTPException(status_code=404, detail="受试者不存在")

    econsent = EConsent(
        patient_id=patient_id,
        trial_id=body.trial_id,
        version=body.version,
        language=body.language,
        status="PENDING",
        witness_user_id=current_user.id,
    )
    db.add(econsent)
    await db.commit()

    return {"message": "知情同意书已创建，等待受试者签署", "data": {"id": str(econsent.id)}}


@router.post("/{patient_id}/econsent/{consent_id}/sign", summary="患者签署知情同意")
async def sign_econsent(
    patient_id: UUID,
    consent_id: UUID,
    body: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    处理电子知情同意书签署
    符合 FDA 21 CFR Part 11 PKI 电子签名要求
    """
    from datetime import datetime, timezone
    result = await db.execute(
        select(EConsent).where(
            and_(EConsent.id == consent_id, EConsent.patient_id == patient_id)
        )
    )
    econsent = result.scalar_one_or_none()
    if not econsent:
        raise HTTPException(status_code=404, detail="知情同意书不存在")

    if econsent.status == "SIGNED":
        raise HTTPException(status_code=400, detail="该知情同意书已签署")

    # 记录签名信息（21 CFR Part 11）
    econsent.patient_signature = body.get("signature")
    econsent.patient_signed_at = datetime.now(timezone.utc)
    econsent.patient_ip = body.get("ip_address")
    econsent.patient_cert_fingerprint = body.get("cert_fingerprint")
    econsent.status = "SIGNED"

    # 更新患者同意状态
    patient = (await db.execute(select(Patient).where(Patient.id == patient_id))).scalar_one_or_none()
    if patient:
        patient.consent_given = True
        patient.consent_date = datetime.now(timezone.utc)
        patient.consent_doc_id = consent_id

    await db.commit()
    return {"message": "知情同意书签署成功"}
