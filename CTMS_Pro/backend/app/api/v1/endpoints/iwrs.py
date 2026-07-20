<<<<<<< HEAD
"""
IWRS 随机化系统 API 端点
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import random
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.models.models import RandomizationScheme, SubjectRandomization, RandomizationCode, Patient
from app.services.randomization import randomization_service
from app.core.dependencies import get_current_active_user
from app.models.models import User


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class RandomizationSchemeCreate(BaseModel):
    scheme_name: str
    scheme_type: str  # RANDOM/BLOCK/STRATIFIED
    trial_id: Optional[UUID] = None
    block_sizes: Optional[List[int]] = [4]
    ratio: Optional[str] = "1:1"
    strata_factors: Optional[List[str]] = []
    arms: Optional[List[dict]] = [
        {"code": "A", "name": "试验组"},
        {"code": "B", "name": "对照组"}
    ]
    total_subjects: int
    is_blinded: Optional[bool] = True
    blinding_method: Optional[str] = "DOUBLE"


class RandomizationSchemeUpdate(BaseModel):
    scheme_name: Optional[str] = None
    status: Optional[str] = None
    block_sizes: Optional[List[int]] = None
    ratio: Optional[str] = None
    arms: Optional[List[dict]] = None


class RandomizationSchemeResponse(BaseModel):
    id: str
    scheme_code: str
    scheme_name: str
    scheme_type: str
    trial_id: Optional[str] = None
    block_sizes: List[int]
    ratio: str
    strata_factors: List[str]
    arms: List[dict]
    total_subjects: int
    is_blinded: bool
    blinding_method: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    activated_at: Optional[str] = None
    completed_at: Optional[str] = None


class SubjectRandomizationCreate(BaseModel):
    patient_id: UUID
    scheme_id: UUID


class RandomizationAssignRequest(BaseModel):
    scheme_id: UUID
    patient_id: UUID
    strata_values: Optional[dict] = {}


class RandomizationAssignResponse(BaseModel):
    id: str
    scheme_id: str
    scheme_name: str
    patient_id: str
    subject_code: str
    randomization_code: str
    treatment_arm: str
    treatment_name: str
    strata_values: dict
    is_blinded: bool
    drug_code: Optional[str] = None
    kit_number: Optional[str] = None
    assigned_at: Optional[str] = None


class SubjectRandomizationResponse(BaseModel):
    id: str
    scheme_id: str
    patient_id: str
    subject_code: str
    randomization_code: str
    treatment_arm: str
    treatment_name: str
    strata_values: dict
    is_blinded: bool
    unblinded_at: Optional[str] = None
    status: str
    drug_code: Optional[str] = None
    kit_number: Optional[str] = None
    assigned_at: Optional[str] = None


class UnblindRequest(BaseModel):
    reason: str

router = APIRouter(prefix="/iwrs", tags=["IWRS 随机化系统"])


# ═══════════════════════════════════════════════════════════════════════════
# 随机化方案管理
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/schemes", response_model=List[RandomizationSchemeResponse])
async def list_schemes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    trial_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取随机化方案列表"""
    query = select(RandomizationScheme)
    
    if status:
        query = query.where(RandomizationScheme.status == status)
    if trial_id:
        query = query.where(RandomizationScheme.trial_id == trial_id)
        
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
        cond = (RandomizationScheme.trial_id.in_(subq)) | (RandomizationScheme.trial_id.in_(subq2))
        query = query.where(cond)
    
    query = query.order_by(RandomizationScheme.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    schemes = result.scalars().all()
    
    return [
        RandomizationSchemeResponse(
            id=str(s.id),
            scheme_code=s.scheme_code,
            scheme_name=s.scheme_name,
            scheme_type=s.scheme_type,
            trial_id=str(s.trial_id) if s.trial_id else None,
            block_sizes=s.block_sizes,
            ratio=s.ratio,
            strata_factors=s.strata_factors,
            arms=s.arms,
            total_subjects=s.total_subjects,
            is_blinded=s.is_blinded,
            blinding_method=s.blinding_method,
            status=s.status,
            created_at=s.created_at.isoformat() if s.created_at else None,
            updated_at=s.updated_at.isoformat() if s.updated_at else None,
            activated_at=s.activated_at.isoformat() if s.activated_at else None,
            completed_at=s.completed_at.isoformat() if s.completed_at else None
        ) for s in schemes
    ]


@router.post("/schemes", response_model=RandomizationSchemeResponse, status_code=status.HTTP_201_CREATED)
async def create_scheme(
    scheme_in: RandomizationSchemeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建随机化方案"""
    # 生成方案编号
    scheme_code = f"RS-{datetime.now().strftime('%Y%m')}-{random.randint(100, 999)}"
    
    scheme = RandomizationScheme(
        scheme_code=scheme_code,
        scheme_name=scheme_in.scheme_name,
        scheme_type=scheme_in.scheme_type,
        trial_id=scheme_in.trial_id,
        block_sizes=scheme_in.block_sizes or [4],
        ratio=scheme_in.ratio or "1:1",
        strata_factors=scheme_in.strata_factors or [],
        arms=scheme_in.arms or [{"code": "A", "name": "试验组"}, {"code": "B", "name": "对照组"}],
        total_subjects=scheme_in.total_subjects,
        is_blinded=scheme_in.is_blinded,
        blinding_method=scheme_in.blinding_method or "DOUBLE",
        status="DRAFT",
        created_by=current_user.id
    )
    
    db.add(scheme)
    await db.commit()
    await db.refresh(scheme)
    
    return RandomizationSchemeResponse(
        id=str(scheme.id),
        scheme_code=scheme.scheme_code,
        scheme_name=scheme.scheme_name,
        scheme_type=scheme.scheme_type,
        trial_id=str(scheme.trial_id) if scheme.trial_id else None,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms,
        total_subjects=scheme.total_subjects,
        is_blinded=scheme.is_blinded,
        blinding_method=scheme.blinding_method,
        status=scheme.status,
        created_at=scheme.created_at.isoformat() if scheme.created_at else None,
        updated_at=scheme.updated_at.isoformat() if scheme.updated_at else None,
        activated_at=scheme.activated_at.isoformat() if scheme.activated_at else None,
        completed_at=scheme.completed_at.isoformat() if scheme.completed_at else None
    )


@router.get("/schemes/{scheme_id}", response_model=RandomizationSchemeResponse)
async def get_scheme(
    scheme_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取随机化方案详情"""
    result = await db.execute(select(RandomizationScheme).where(RandomizationScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    
    if not scheme:
        raise HTTPException(status_code=404, detail="随机化方案不存在")
    
    return RandomizationSchemeResponse(
        id=str(scheme.id),
        scheme_code=scheme.scheme_code,
        scheme_name=scheme.scheme_name,
        scheme_type=scheme.scheme_type,
        trial_id=str(scheme.trial_id) if scheme.trial_id else None,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms,
        total_subjects=scheme.total_subjects,
        is_blinded=scheme.is_blinded,
        blinding_method=scheme.blinding_method,
        status=scheme.status,
        created_at=scheme.created_at.isoformat() if scheme.created_at else None,
        updated_at=scheme.updated_at.isoformat() if scheme.updated_at else None,
        activated_at=scheme.activated_at.isoformat() if scheme.activated_at else None,
        completed_at=scheme.completed_at.isoformat() if scheme.completed_at else None
    )


@router.patch("/schemes/{scheme_id}", response_model=RandomizationSchemeResponse)
async def update_scheme(
    scheme_id: UUID,
    scheme_in: RandomizationSchemeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新随机化方案"""
    result = await db.execute(select(RandomizationScheme).where(RandomizationScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    
    if not scheme:
        raise HTTPException(status_code=404, detail="随机化方案不存在")
    
    # 更新字段
    update_data = scheme_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scheme, field, value)
    
    await db.commit()
    await db.refresh(scheme)
    
    return RandomizationSchemeResponse(
        id=str(scheme.id),
        scheme_code=scheme.scheme_code,
        scheme_name=scheme.scheme_name,
        scheme_type=scheme.scheme_type,
        trial_id=str(scheme.trial_id) if scheme.trial_id else None,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms,
        total_subjects=scheme.total_subjects,
        is_blinded=scheme.is_blinded,
        blinding_method=scheme.blinding_method,
        status=scheme.status,
        created_at=scheme.created_at.isoformat() if scheme.created_at else None,
        updated_at=scheme.updated_at.isoformat() if scheme.updated_at else None,
        activated_at=scheme.activated_at.isoformat() if scheme.activated_at else None,
        completed_at=scheme.completed_at.isoformat() if scheme.completed_at else None
    )


@router.post("/schemes/{scheme_id}/activate", response_model=RandomizationSchemeResponse)
async def activate_scheme(
    scheme_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """激活随机化方案，生成编码池"""
    from datetime import datetime
    import random as random_module
    
    result = await db.execute(select(RandomizationScheme).where(RandomizationScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    
    if not scheme:
        raise HTTPException(status_code=404, detail="随机化方案不存在")
    
    if scheme.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能激活草稿状态的方案")
    
    # 生成编码池
    codes = randomization_service.generate_code_pool(
        scheme_type=scheme.scheme_type,
        total_subjects=scheme.total_subjects,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms
    )
    
    # 保存编码到数据库
    db_codes = []
    for code in codes:
        random_code = RandomizationCode(
            scheme_id=scheme.id,
            block_id=code["block_id"],
            sequence=code["sequence"],
            randomization_code=f"R{scheme.scheme_code.replace('RS-', '')}{random_module.randint(10000, 99999)}",
            treatment_arm=code["treatment_arm"],
            treatment_name=code["treatment_name"],
            strata_values=code["strata_values"]
        )
        db_codes.append(random_code)
    
    db.add_all(db_codes)
    
    # 更新方案状态
    scheme.status = "ACTIVE"
    scheme.activated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(scheme)
    
    return RandomizationSchemeResponse(
        id=str(scheme.id),
        scheme_code=scheme.scheme_code,
        scheme_name=scheme.scheme_name,
        scheme_type=scheme.scheme_type,
        trial_id=str(scheme.trial_id) if scheme.trial_id else None,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms,
        total_subjects=scheme.total_subjects,
        is_blinded=scheme.is_blinded,
        blinding_method=scheme.blinding_method,
        status=scheme.status,
        created_at=scheme.created_at.isoformat() if scheme.created_at else None,
        updated_at=scheme.updated_at.isoformat() if scheme.updated_at else None,
        activated_at=scheme.activated_at.isoformat() if scheme.activated_at else None,
        completed_at=scheme.completed_at.isoformat() if scheme.completed_at else None
    )


# ═══════════════════════════════════════════════════════════════════════════
# 受试者随机化分配
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/assign", response_model=RandomizationAssignResponse)
async def assign_randomization(
    request: RandomizationAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """为受试者分配随机号"""
    logger.info(f"开始为受试者 {request.patient_id} 分配方案 {request.scheme_id} 的随机号")
    # 获取方案
    result = await db.execute(select(RandomizationScheme).where(RandomizationScheme.id == request.scheme_id))
    scheme = result.scalar_one_or_none()
    
    if not scheme:
        raise HTTPException(status_code=404, detail="随机化方案不存在")
    
    if scheme.status not in ["ACTIVE", "DRAFT"]:
        raise HTTPException(status_code=400, detail="只能对激活状态或草稿状态的方案进行随机分配")
    
    # 检查是否还有可用编码
    result = await db.execute(
        select(func.count(RandomizationCode.id))
        .where(and_(RandomizationCode.scheme_id == scheme.id, RandomizationCode.is_used == False))
    )
    available_count = result.scalar()
    
    if available_count <= 0:
        raise HTTPException(status_code=400, detail="该方案已无剩余随机号")
    
    # 获取一个可用编码
    result = await db.execute(
        select(RandomizationCode)
        .where(and_(RandomizationCode.scheme_id == scheme.id, RandomizationCode.is_used == False))
        .limit(1)
    )
    code = result.scalar_one_or_none()
    
    if not code:
        raise HTTPException(status_code=400, detail="无法获取可用随机号")
    
    # 标记编码为已使用
    code.is_used = True
    code.used_at = datetime.utcnow()
    
    # 生成受试者编号
    result = await db.execute(
        select(func.count(SubjectRandomization.id)).where(SubjectRandomization.scheme_id == scheme.id)
    )
    subject_count = result.scalar()
    # 为保证全局唯一性，加上方案编号前缀
    subject_code = f"{scheme.scheme_code}-P{str(subject_count + 1).zfill(3)}"
    
    # 创建随机化记录
    randomization = SubjectRandomization(
        scheme_id=scheme.id,
        patient_id=request.patient_id,
        subject_code=subject_code,
        randomization_code=code.randomization_code,
        block_id=code.block_id,
        block_sequence=code.sequence,
        treatment_arm=code.treatment_arm,
        treatment_name=code.treatment_name,
        strata_values=request.strata_values or {},
        is_blinded=scheme.is_blinded,
        status="ASSIGNED",
        drug_code=code.randomization_code,
        kit_number=f"KIT-{code.randomization_code}",
        assigned_by=current_user.id
    )
    
    db.add(randomization)
    
    # 同步更新 Patient 的分组状态
    patient_result = await db.execute(select(Patient).where(Patient.id == request.patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient:
        patient.arm = "盲态" if scheme.is_blinded else code.treatment_name
        logger.info(f"更新受试者 {patient.id} 的状态 arm 为: {patient.arm}")

    try:
        await db.commit()
        logger.info("数据库事务提交成功")
        await db.refresh(randomization)
    except Exception as e:
        await db.rollback()
        logger.error(f"数据库写入失败，已回滚: {str(e)}")
        raise HTTPException(status_code=500, detail="分配随机号失败，请稍后重试")
    
    return RandomizationAssignResponse(
        id=str(randomization.id),
        scheme_id=str(scheme.id),
        scheme_name=scheme.scheme_name,
        patient_id=str(request.patient_id),
        subject_code=randomization.subject_code,
        randomization_code=randomization.randomization_code,
        treatment_arm=randomization.treatment_arm,
        treatment_name=randomization.treatment_name,
        strata_values=randomization.strata_values,
        is_blinded=randomization.is_blinded,
        drug_code=randomization.drug_code,
        kit_number=randomization.kit_number,
        assigned_at=randomization.created_at.isoformat() if randomization.created_at else None
    )


@router.get("/subjects", response_model=List[SubjectRandomizationResponse])
async def list_randomizations(
    scheme_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取随机化分配记录列表"""
    query = select(SubjectRandomization)
    
    if scheme_id:
        query = query.where(SubjectRandomization.scheme_id == scheme_id)
    if patient_id:
        query = query.where(SubjectRandomization.patient_id == patient_id)
        
    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import Patient, TrialSite, Trial, Site
        subq_trial = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq_site = select(TrialSite.site_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        
        # 只能看到自己负责的试验或所属中心相关的患者的随机化记录
        subq_patient = select(Patient.id).where(
            Patient.trial_id.in_(subq_trial) | Patient.site_id.in_(subq_site)
        )
        query = query.where(SubjectRandomization.patient_id.in_(subq_patient))
    
    query = query.order_by(SubjectRandomization.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()
    
    return [
        SubjectRandomizationResponse(
            id=str(r.id),
            scheme_id=str(r.scheme_id),
            patient_id=str(r.patient_id),
            subject_code=r.subject_code,
            randomization_code=r.randomization_code,
            treatment_arm=r.treatment_arm,
            treatment_name=r.treatment_name,
            strata_values=r.strata_values,
            is_blinded=r.is_blinded,
            unblinded_at=r.unblinded_at.isoformat() if r.unblinded_at else None,
            status=r.status,
            drug_code=r.drug_code,
            kit_number=r.kit_number,
            assigned_at=r.created_at.isoformat() if r.created_at else None
        ) for r in records
    ]


@router.post("/subjects/{randomization_id}/unblind", response_model=SubjectRandomizationResponse)
async def unblind_subject(
    randomization_id: UUID,
    request: UnblindRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """解盲操作"""
    from datetime import datetime
    
    result = await db.execute(select(SubjectRandomization).where(SubjectRandomization.id == randomization_id))
    randomization = result.scalar_one_or_none()
    
    if not randomization:
        raise HTTPException(status_code=404, detail="随机化记录不存在")
    
    # 执行解盲
    randomization.is_blinded = False
    randomization.unblinded_at = datetime.utcnow()
    randomization.unblinded_by = current_user.id
    randomization.unblind_reason = request.reason
    randomization.status = "UNBLINDED"
    
    await db.commit()
    await db.refresh(randomization)
    
    return SubjectRandomizationResponse(
        id=str(randomization.id),
        scheme_id=str(randomization.scheme_id),
        patient_id=str(randomization.patient_id),
        subject_code=randomization.subject_code,
        randomization_code=randomization.randomization_code,
        treatment_arm=randomization.treatment_arm,
        treatment_name=randomization.treatment_name,
        strata_values=randomization.strata_values,
        is_blinded=randomization.is_blinded,
        unblinded_at=randomization.unblinded_at.isoformat() if randomization.unblinded_at else None,
        status=randomization.status,
        drug_code=randomization.drug_code,
        kit_number=randomization.kit_number,
        assigned_at=randomization.created_at.isoformat() if randomization.created_at else None
    )


# ═══════════════════════════════════════════════════════════════════════════
# 统计与导出
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/schemes/{scheme_id}/stats")
async def get_scheme_stats(
    scheme_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取方案统计信息"""
    # 总随机号
    result = await db.execute(
        select(func.count(RandomizationCode.id)).where(RandomizationCode.scheme_id == scheme_id)
    )
    total_codes = result.scalar()
    
    # 已使用
    result = await db.execute(
        select(func.count(RandomizationCode.id))
        .where(and_(RandomizationCode.scheme_id == scheme_id, RandomizationCode.is_used == True))
    )
    used_codes = result.scalar()
    
    # 已分配受试者数
    result = await db.execute(
        select(func.count(SubjectRandomization.id))
        .where(SubjectRandomization.scheme_id == scheme_id)
    )
    assigned_subjects = result.scalar()
    
    return {
        "scheme_id": str(scheme_id),
        "total_codes": total_codes or 0,
        "used_codes": used_codes or 0,
        "available_codes": (total_codes or 0) - (used_codes or 0),
        "assigned_subjects": assigned_subjects or 0,
        "usage_rate": round(used_codes / total_codes * 100, 1) if total_codes else 0
    }


# 导入需要的模块
from datetime import datetime
import random
=======
"""
IWRS 随机化系统 API 端点
"""
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import random
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

logger = logging.getLogger(__name__)

from app.db.session import get_db
from app.models.models import RandomizationScheme, SubjectRandomization, RandomizationCode, Patient
from app.services.randomization import randomization_service
from app.core.dependencies import get_current_active_user
from app.models.models import User


# ═══════════════════════════════════════════════════════════════════════════
# Schemas
# ═══════════════════════════════════════════════════════════════════════════

class RandomizationSchemeCreate(BaseModel):
    scheme_name: str
    scheme_type: str  # RANDOM/BLOCK/STRATIFIED
    trial_id: Optional[UUID] = None
    block_sizes: Optional[List[int]] = [4]
    ratio: Optional[str] = "1:1"
    strata_factors: Optional[List[str]] = []
    arms: Optional[List[dict]] = [
        {"code": "A", "name": "试验组"},
        {"code": "B", "name": "对照组"}
    ]
    total_subjects: int
    is_blinded: Optional[bool] = True
    blinding_method: Optional[str] = "DOUBLE"


class RandomizationSchemeUpdate(BaseModel):
    scheme_name: Optional[str] = None
    status: Optional[str] = None
    block_sizes: Optional[List[int]] = None
    ratio: Optional[str] = None
    arms: Optional[List[dict]] = None


class RandomizationSchemeResponse(BaseModel):
    id: str
    scheme_code: str
    scheme_name: str
    scheme_type: str
    trial_id: Optional[str] = None
    block_sizes: List[int]
    ratio: str
    strata_factors: List[str]
    arms: List[dict]
    total_subjects: int
    is_blinded: bool
    blinding_method: str
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    activated_at: Optional[str] = None
    completed_at: Optional[str] = None


class SubjectRandomizationCreate(BaseModel):
    patient_id: UUID
    scheme_id: UUID


class RandomizationAssignRequest(BaseModel):
    scheme_id: UUID
    patient_id: UUID
    strata_values: Optional[dict] = {}


class RandomizationAssignResponse(BaseModel):
    id: str
    scheme_id: str
    scheme_name: str
    patient_id: str
    subject_code: str
    randomization_code: str
    treatment_arm: str
    treatment_name: str
    strata_values: dict
    is_blinded: bool
    drug_code: Optional[str] = None
    kit_number: Optional[str] = None
    assigned_at: Optional[str] = None


class SubjectRandomizationResponse(BaseModel):
    id: str
    scheme_id: str
    patient_id: str
    subject_code: str
    randomization_code: str
    treatment_arm: str
    treatment_name: str
    strata_values: dict
    is_blinded: bool
    unblinded_at: Optional[str] = None
    status: str
    drug_code: Optional[str] = None
    kit_number: Optional[str] = None
    assigned_at: Optional[str] = None


class UnblindRequest(BaseModel):
    reason: str

router = APIRouter(prefix="/iwrs", tags=["IWRS 随机化系统"])


# ═══════════════════════════════════════════════════════════════════════════
# 随机化方案管理
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/schemes", response_model=List[RandomizationSchemeResponse])
async def list_schemes(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = None,
    trial_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取随机化方案列表"""
    query = select(RandomizationScheme)
    
    if status:
        query = query.where(RandomizationScheme.status == status)
    if trial_id:
        query = query.where(RandomizationScheme.trial_id == trial_id)
        
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
        cond = (RandomizationScheme.trial_id.in_(subq)) | (RandomizationScheme.trial_id.in_(subq2))
        query = query.where(cond)
    
    query = query.order_by(RandomizationScheme.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    schemes = result.scalars().all()
    
    return [
        RandomizationSchemeResponse(
            id=str(s.id),
            scheme_code=s.scheme_code,
            scheme_name=s.scheme_name,
            scheme_type=s.scheme_type,
            trial_id=str(s.trial_id) if s.trial_id else None,
            block_sizes=s.block_sizes,
            ratio=s.ratio,
            strata_factors=s.strata_factors,
            arms=s.arms,
            total_subjects=s.total_subjects,
            is_blinded=s.is_blinded,
            blinding_method=s.blinding_method,
            status=s.status,
            created_at=s.created_at.isoformat() if s.created_at else None,
            updated_at=s.updated_at.isoformat() if s.updated_at else None,
            activated_at=s.activated_at.isoformat() if s.activated_at else None,
            completed_at=s.completed_at.isoformat() if s.completed_at else None
        ) for s in schemes
    ]


@router.post("/schemes", response_model=RandomizationSchemeResponse, status_code=status.HTTP_201_CREATED)
async def create_scheme(
    scheme_in: RandomizationSchemeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建随机化方案"""
    # 生成方案编号
    scheme_code = f"RS-{datetime.now().strftime('%Y%m')}-{random.randint(100, 999)}"
    
    scheme = RandomizationScheme(
        scheme_code=scheme_code,
        scheme_name=scheme_in.scheme_name,
        scheme_type=scheme_in.scheme_type,
        trial_id=scheme_in.trial_id,
        block_sizes=scheme_in.block_sizes or [4],
        ratio=scheme_in.ratio or "1:1",
        strata_factors=scheme_in.strata_factors or [],
        arms=scheme_in.arms or [{"code": "A", "name": "试验组"}, {"code": "B", "name": "对照组"}],
        total_subjects=scheme_in.total_subjects,
        is_blinded=scheme_in.is_blinded,
        blinding_method=scheme_in.blinding_method or "DOUBLE",
        status="DRAFT",
        created_by=current_user.id
    )
    
    db.add(scheme)
    await db.commit()
    await db.refresh(scheme)
    
    return RandomizationSchemeResponse(
        id=str(scheme.id),
        scheme_code=scheme.scheme_code,
        scheme_name=scheme.scheme_name,
        scheme_type=scheme.scheme_type,
        trial_id=str(scheme.trial_id) if scheme.trial_id else None,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms,
        total_subjects=scheme.total_subjects,
        is_blinded=scheme.is_blinded,
        blinding_method=scheme.blinding_method,
        status=scheme.status,
        created_at=scheme.created_at.isoformat() if scheme.created_at else None,
        updated_at=scheme.updated_at.isoformat() if scheme.updated_at else None,
        activated_at=scheme.activated_at.isoformat() if scheme.activated_at else None,
        completed_at=scheme.completed_at.isoformat() if scheme.completed_at else None
    )


@router.get("/schemes/{scheme_id}", response_model=RandomizationSchemeResponse)
async def get_scheme(
    scheme_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取随机化方案详情"""
    result = await db.execute(select(RandomizationScheme).where(RandomizationScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    
    if not scheme:
        raise HTTPException(status_code=404, detail="随机化方案不存在")
    
    return RandomizationSchemeResponse(
        id=str(scheme.id),
        scheme_code=scheme.scheme_code,
        scheme_name=scheme.scheme_name,
        scheme_type=scheme.scheme_type,
        trial_id=str(scheme.trial_id) if scheme.trial_id else None,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms,
        total_subjects=scheme.total_subjects,
        is_blinded=scheme.is_blinded,
        blinding_method=scheme.blinding_method,
        status=scheme.status,
        created_at=scheme.created_at.isoformat() if scheme.created_at else None,
        updated_at=scheme.updated_at.isoformat() if scheme.updated_at else None,
        activated_at=scheme.activated_at.isoformat() if scheme.activated_at else None,
        completed_at=scheme.completed_at.isoformat() if scheme.completed_at else None
    )


@router.patch("/schemes/{scheme_id}", response_model=RandomizationSchemeResponse)
async def update_scheme(
    scheme_id: UUID,
    scheme_in: RandomizationSchemeUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新随机化方案"""
    result = await db.execute(select(RandomizationScheme).where(RandomizationScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    
    if not scheme:
        raise HTTPException(status_code=404, detail="随机化方案不存在")
    
    # 更新字段
    update_data = scheme_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(scheme, field, value)
    
    await db.commit()
    await db.refresh(scheme)
    
    return RandomizationSchemeResponse(
        id=str(scheme.id),
        scheme_code=scheme.scheme_code,
        scheme_name=scheme.scheme_name,
        scheme_type=scheme.scheme_type,
        trial_id=str(scheme.trial_id) if scheme.trial_id else None,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms,
        total_subjects=scheme.total_subjects,
        is_blinded=scheme.is_blinded,
        blinding_method=scheme.blinding_method,
        status=scheme.status,
        created_at=scheme.created_at.isoformat() if scheme.created_at else None,
        updated_at=scheme.updated_at.isoformat() if scheme.updated_at else None,
        activated_at=scheme.activated_at.isoformat() if scheme.activated_at else None,
        completed_at=scheme.completed_at.isoformat() if scheme.completed_at else None
    )


@router.post("/schemes/{scheme_id}/activate", response_model=RandomizationSchemeResponse)
async def activate_scheme(
    scheme_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """激活随机化方案，生成编码池"""
    from datetime import datetime
    import random as random_module
    
    result = await db.execute(select(RandomizationScheme).where(RandomizationScheme.id == scheme_id))
    scheme = result.scalar_one_or_none()
    
    if not scheme:
        raise HTTPException(status_code=404, detail="随机化方案不存在")
    
    if scheme.status != "DRAFT":
        raise HTTPException(status_code=400, detail="只能激活草稿状态的方案")
    
    # 生成编码池
    codes = randomization_service.generate_code_pool(
        scheme_type=scheme.scheme_type,
        total_subjects=scheme.total_subjects,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms
    )
    
    # 保存编码到数据库
    db_codes = []
    for code in codes:
        random_code = RandomizationCode(
            scheme_id=scheme.id,
            block_id=code["block_id"],
            sequence=code["sequence"],
            randomization_code=f"R{scheme.scheme_code.replace('RS-', '')}{random_module.randint(10000, 99999)}",
            treatment_arm=code["treatment_arm"],
            treatment_name=code["treatment_name"],
            strata_values=code["strata_values"]
        )
        db_codes.append(random_code)
    
    db.add_all(db_codes)
    
    # 更新方案状态
    scheme.status = "ACTIVE"
    scheme.activated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(scheme)
    
    return RandomizationSchemeResponse(
        id=str(scheme.id),
        scheme_code=scheme.scheme_code,
        scheme_name=scheme.scheme_name,
        scheme_type=scheme.scheme_type,
        trial_id=str(scheme.trial_id) if scheme.trial_id else None,
        block_sizes=scheme.block_sizes,
        ratio=scheme.ratio,
        strata_factors=scheme.strata_factors,
        arms=scheme.arms,
        total_subjects=scheme.total_subjects,
        is_blinded=scheme.is_blinded,
        blinding_method=scheme.blinding_method,
        status=scheme.status,
        created_at=scheme.created_at.isoformat() if scheme.created_at else None,
        updated_at=scheme.updated_at.isoformat() if scheme.updated_at else None,
        activated_at=scheme.activated_at.isoformat() if scheme.activated_at else None,
        completed_at=scheme.completed_at.isoformat() if scheme.completed_at else None
    )


# ═══════════════════════════════════════════════════════════════════════════
# 受试者随机化分配
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/assign", response_model=RandomizationAssignResponse)
async def assign_randomization(
    request: RandomizationAssignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """为受试者分配随机号"""
    logger.info(f"开始为受试者 {request.patient_id} 分配方案 {request.scheme_id} 的随机号")
    # 获取方案
    result = await db.execute(select(RandomizationScheme).where(RandomizationScheme.id == request.scheme_id))
    scheme = result.scalar_one_or_none()
    
    if not scheme:
        raise HTTPException(status_code=404, detail="随机化方案不存在")
    
    if scheme.status not in ["ACTIVE", "DRAFT"]:
        raise HTTPException(status_code=400, detail="只能对激活状态或草稿状态的方案进行随机分配")
    
    # 检查是否还有可用编码
    result = await db.execute(
        select(func.count(RandomizationCode.id))
        .where(and_(RandomizationCode.scheme_id == scheme.id, RandomizationCode.is_used == False))
    )
    available_count = result.scalar()
    
    if available_count <= 0:
        raise HTTPException(status_code=400, detail="该方案已无剩余随机号")
    
    # 获取一个可用编码
    result = await db.execute(
        select(RandomizationCode)
        .where(and_(RandomizationCode.scheme_id == scheme.id, RandomizationCode.is_used == False))
        .limit(1)
    )
    code = result.scalar_one_or_none()
    
    if not code:
        raise HTTPException(status_code=400, detail="无法获取可用随机号")
    
    # 标记编码为已使用
    code.is_used = True
    code.used_at = datetime.utcnow()
    
    # 生成受试者编号
    result = await db.execute(
        select(func.count(SubjectRandomization.id)).where(SubjectRandomization.scheme_id == scheme.id)
    )
    subject_count = result.scalar()
    # 为保证全局唯一性，加上方案编号前缀
    subject_code = f"{scheme.scheme_code}-P{str(subject_count + 1).zfill(3)}"
    
    # 创建随机化记录
    randomization = SubjectRandomization(
        scheme_id=scheme.id,
        patient_id=request.patient_id,
        subject_code=subject_code,
        randomization_code=code.randomization_code,
        block_id=code.block_id,
        block_sequence=code.sequence,
        treatment_arm=code.treatment_arm,
        treatment_name=code.treatment_name,
        strata_values=request.strata_values or {},
        is_blinded=scheme.is_blinded,
        status="ASSIGNED",
        drug_code=code.randomization_code,
        kit_number=f"KIT-{code.randomization_code}",
        assigned_by=current_user.id
    )
    
    db.add(randomization)
    
    # 同步更新 Patient 的分组状态
    patient_result = await db.execute(select(Patient).where(Patient.id == request.patient_id))
    patient = patient_result.scalar_one_or_none()
    if patient:
        patient.arm = "盲态" if scheme.is_blinded else code.treatment_name
        logger.info(f"更新受试者 {patient.id} 的状态 arm 为: {patient.arm}")

    try:
        await db.commit()
        logger.info("数据库事务提交成功")
        await db.refresh(randomization)
    except Exception as e:
        await db.rollback()
        logger.error(f"数据库写入失败，已回滚: {str(e)}")
        raise HTTPException(status_code=500, detail="分配随机号失败，请稍后重试")
    
    return RandomizationAssignResponse(
        id=str(randomization.id),
        scheme_id=str(scheme.id),
        scheme_name=scheme.scheme_name,
        patient_id=str(request.patient_id),
        subject_code=randomization.subject_code,
        randomization_code=randomization.randomization_code,
        treatment_arm=randomization.treatment_arm,
        treatment_name=randomization.treatment_name,
        strata_values=randomization.strata_values,
        is_blinded=randomization.is_blinded,
        drug_code=randomization.drug_code,
        kit_number=randomization.kit_number,
        assigned_at=randomization.created_at.isoformat() if randomization.created_at else None
    )


@router.get("/subjects", response_model=List[SubjectRandomizationResponse])
async def list_randomizations(
    scheme_id: Optional[UUID] = None,
    patient_id: Optional[UUID] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取随机化分配记录列表"""
    query = select(SubjectRandomization)
    
    if scheme_id:
        query = query.where(SubjectRandomization.scheme_id == scheme_id)
    if patient_id:
        query = query.where(SubjectRandomization.patient_id == patient_id)
        
    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import Patient, TrialSite, Trial, Site
        subq_trial = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq_site = select(TrialSite.site_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        
        # 只能看到自己负责的试验或所属中心相关的患者的随机化记录
        subq_patient = select(Patient.id).where(
            Patient.trial_id.in_(subq_trial) | Patient.site_id.in_(subq_site)
        )
        query = query.where(SubjectRandomization.patient_id.in_(subq_patient))
    
    query = query.order_by(SubjectRandomization.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    records = result.scalars().all()
    
    return [
        SubjectRandomizationResponse(
            id=str(r.id),
            scheme_id=str(r.scheme_id),
            patient_id=str(r.patient_id),
            subject_code=r.subject_code,
            randomization_code=r.randomization_code,
            treatment_arm=r.treatment_arm,
            treatment_name=r.treatment_name,
            strata_values=r.strata_values,
            is_blinded=r.is_blinded,
            unblinded_at=r.unblinded_at.isoformat() if r.unblinded_at else None,
            status=r.status,
            drug_code=r.drug_code,
            kit_number=r.kit_number,
            assigned_at=r.created_at.isoformat() if r.created_at else None
        ) for r in records
    ]


@router.post("/subjects/{randomization_id}/unblind", response_model=SubjectRandomizationResponse)
async def unblind_subject(
    randomization_id: UUID,
    request: UnblindRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """解盲操作"""
    from datetime import datetime
    
    result = await db.execute(select(SubjectRandomization).where(SubjectRandomization.id == randomization_id))
    randomization = result.scalar_one_or_none()
    
    if not randomization:
        raise HTTPException(status_code=404, detail="随机化记录不存在")
    
    # 执行解盲
    randomization.is_blinded = False
    randomization.unblinded_at = datetime.utcnow()
    randomization.unblinded_by = current_user.id
    randomization.unblind_reason = request.reason
    randomization.status = "UNBLINDED"
    
    await db.commit()
    await db.refresh(randomization)
    
    return SubjectRandomizationResponse(
        id=str(randomization.id),
        scheme_id=str(randomization.scheme_id),
        patient_id=str(randomization.patient_id),
        subject_code=randomization.subject_code,
        randomization_code=randomization.randomization_code,
        treatment_arm=randomization.treatment_arm,
        treatment_name=randomization.treatment_name,
        strata_values=randomization.strata_values,
        is_blinded=randomization.is_blinded,
        unblinded_at=randomization.unblinded_at.isoformat() if randomization.unblinded_at else None,
        status=randomization.status,
        drug_code=randomization.drug_code,
        kit_number=randomization.kit_number,
        assigned_at=randomization.created_at.isoformat() if randomization.created_at else None
    )


# ═══════════════════════════════════════════════════════════════════════════
# 统计与导出
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/schemes/{scheme_id}/stats")
async def get_scheme_stats(
    scheme_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取方案统计信息"""
    # 总随机号
    result = await db.execute(
        select(func.count(RandomizationCode.id)).where(RandomizationCode.scheme_id == scheme_id)
    )
    total_codes = result.scalar()
    
    # 已使用
    result = await db.execute(
        select(func.count(RandomizationCode.id))
        .where(and_(RandomizationCode.scheme_id == scheme_id, RandomizationCode.is_used == True))
    )
    used_codes = result.scalar()
    
    # 已分配受试者数
    result = await db.execute(
        select(func.count(SubjectRandomization.id))
        .where(SubjectRandomization.scheme_id == scheme_id)
    )
    assigned_subjects = result.scalar()
    
    return {
        "scheme_id": str(scheme_id),
        "total_codes": total_codes or 0,
        "used_codes": used_codes or 0,
        "available_codes": (total_codes or 0) - (used_codes or 0),
        "assigned_subjects": assigned_subjects or 0,
        "usage_rate": round(used_codes / total_codes * 100, 1) if total_codes else 0
    }


# 导入需要的模块
from datetime import datetime
import random
>>>>>>> origin/main
