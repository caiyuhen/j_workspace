from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, desc, and_
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
import uuid

from app.db.session import get_db
from app.models.models import Site, User
from app.core.dependencies import get_current_active_user, require_permissions

router = APIRouter()

class SiteCreate(BaseModel):
    code: str = Field(..., description="中心编号")
    name: str = Field(..., description="中心名称")
    address: Optional[str] = None
    pi_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    status: Optional[str] = "ACTIVE"

class SiteUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    pi_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    status: Optional[str] = None

def site_to_dict(s: Site):
    return {
        "id": str(s.id),
        "code": s.code,
        "name": s.name,
        "address": s.address,
        "pi_name": s.pi_name,
        "contact_phone": s.contact_phone,
        "contact_email": s.contact_email,
        "status": s.status,
        "organization_id": str(s.organization_id) if s.organization_id else None,
    }

@router.get("", summary="获取中心列表")
async def list_sites(
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    keyword: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    query = select(Site)
    count_query = select(func.count(Site.id))

    if keyword:
        kw = f"%{keyword}%"
        cond = Site.name.ilike(kw) | Site.code.ilike(kw)
        query = query.where(cond)
        count_query = count_query.where(cond)

    # 数据隔离：非管理员只能看自己所属的中心，或者自己负责的试验项目所关联的中心
    if not current_user.is_superuser:
        from app.models.models import Role
        # Check if user has global site read permission (like PM)
        role_result = await db.execute(select(Role).where(Role.id == current_user.role_id))
        role = role_result.scalar_one_or_none()
        has_global_site_access = False
        
        if role and role.permissions:
            if "*:*" in role.permissions or "site:*" in role.permissions or "site:read" in role.permissions:
                has_global_site_access = True
                
        if not has_global_site_access:
            from app.models.models import TrialSite, Trial
            cond = (Site.organization_id == current_user.organization_id)
            
            subq = select(TrialSite.site_id).join(Trial, TrialSite.trial_id == Trial.id).where(
                (Trial.pm_user_id == current_user.id) | 
                (Trial.created_by == current_user.id) |
                (TrialSite.pi_user_id == current_user.id)
            )
            cond = cond | Site.id.in_(subq)
            
            query = query.where(cond)
            count_query = count_query.where(cond)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(Site.created_at.desc()).offset(offset).limit(page_size))
    rows = result.scalars().all()

    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [site_to_dict(s) for s in rows]
    }

@router.post("", summary="创建中心", status_code=201)
async def create_site(
    body: SiteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:write")), # Assuming user:write or similar
):
    exists = await db.execute(select(Site).where(Site.code == body.code))
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="中心编号已存在")

    from app.models.models import Organization
    import uuid
    # Create an associated organization
    org = Organization(
        id=uuid.uuid4(),
        code=body.code,
        name=body.name,
        type="HOSPITAL"
    )
    db.add(org)
    await db.flush()

    site_data = body.model_dump(exclude_none=True)
    site_data["organization_id"] = org.id
    site = Site(**site_data)
    db.add(site)
    await db.commit()
    await db.refresh(site)
    return {"message": "中心创建成功", "data": site_to_dict(site)}

@router.put("/{site_id}", summary="更新中心")
async def update_site(
    site_id: UUID,
    body: SiteUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:write")),
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="中心不存在")

    update_data = body.model_dump(exclude_none=True)
    if "code" in update_data and update_data["code"] != site.code:
        exists = await db.execute(select(Site).where(Site.code == update_data["code"]))
        if exists.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="中心编号已存在")

    for key, val in update_data.items():
        setattr(site, key, val)
        
    if site.organization_id and ("name" in update_data or "code" in update_data):
        from app.models.models import Organization
        org_result = await db.execute(select(Organization).where(Organization.id == site.organization_id))
        org = org_result.scalar_one_or_none()
        if org:
            if "name" in update_data: org.name = update_data["name"]
            if "code" in update_data: org.code = update_data["code"]
    
    await db.commit()
    await db.refresh(site)
    return {"message": "更新成功", "data": site_to_dict(site)}

@router.delete("/{site_id}", summary="删除中心")
async def delete_site(
    site_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:write")),
):
    result = await db.execute(select(Site).where(Site.id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="中心不存在")
        
    try:
        await db.execute(delete(Site).where(Site.id == site_id))
        await db.commit()
        return {"message": "删除成功"}
    except Exception as e:
        await db.rollback()
        # 捕获外键约束等错误
        if "ForeignKeyViolationError" in str(e) or "foreign key constraint" in str(e):
            raise HTTPException(status_code=400, detail="无法删除：该中心已被试验或其他数据关联")
        raise HTTPException(status_code=500, detail=f"删除失败：{str(e)}")