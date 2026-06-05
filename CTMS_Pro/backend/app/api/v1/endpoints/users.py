"""
用户管理 API
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, desc, delete
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from uuid import UUID

from app.db.session import get_db
from app.models.models import User, Role
from app.core.security import get_password_hash, validate_password_strength
from app.core.dependencies import get_current_active_user, require_permissions, require_superuser

router = APIRouter()


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str
    password: str
    role_id: Optional[UUID] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    organization_id: Optional[UUID] = None


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    title: Optional[str] = None
    role_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


def user_to_dict(u: User, role: Role = None) -> dict:
    return {
        "id": str(u.id),
        "employee_id": u.employee_id,
        "username": u.username,
        "email": u.email,
        "full_name": u.full_name,
        "phone": u.phone,
        "department": u.department,
        "title": u.title,
        "organization_id": str(u.organization_id) if u.organization_id else None,
        "role_id": str(u.role_id) if u.role_id else None,
        "role_code": role.code if role else None,
        "role_name": role.name if role else None,
        "is_active": u.is_active,
        "is_superuser": u.is_superuser,
        "mfa_enabled": u.mfa_enabled,
        "last_login_at": u.last_login_at.isoformat() if u.last_login_at else None,
        "created_at": u.created_at.isoformat() if u.created_at else None,
    }


@router.get("", summary="用户列表")
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    role_id: Optional[UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:read")),
):
    query = select(User, Role).outerjoin(Role, User.role_id == Role.id)
    count_query = select(func.count(User.id))

    if keyword:
        kw = f"%{keyword}%"
        cond = User.username.ilike(kw) | User.full_name.ilike(kw) | User.email.ilike(kw)
        query = query.where(cond)
        count_query = count_query.where(cond)
    if role_id:
        query = query.where(User.role_id == role_id)
        count_query = count_query.where(User.role_id == role_id)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
        count_query = count_query.where(User.is_active == is_active)

    # 数据隔离：检查是否具有全局人员查看权限
    if not current_user.is_superuser:
        role_result = await db.execute(select(Role).where(Role.id == current_user.role_id))
        user_role = role_result.scalar_one_or_none()
        has_global_user_access = False
        
        if user_role and user_role.permissions:
            if "*:*" in user_role.permissions or "user:*" in user_role.permissions or "user:read" in user_role.permissions:
                has_global_user_access = True
                
        if not has_global_user_access:
            # 如果没有全局权限，只能看到自己中心的人员
            query = query.where(User.organization_id == current_user.organization_id)
            count_query = count_query.where(User.organization_id == current_user.organization_id)

    total = (await db.execute(count_query)).scalar()
    offset = (page - 1) * page_size
    result = await db.execute(query.order_by(desc(User.created_at)).offset(offset).limit(page_size))
    rows = result.all()

    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [user_to_dict(u, r) for u, r in rows]
    }


@router.post("", summary="创建用户", status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:write")),
):
    # 密码强度校验
    valid, msg = validate_password_strength(body.password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    # 检查用户名/邮箱唯一性
    exists = await db.execute(
        select(User).where((User.username == body.username) | (User.email == body.email))
    )
    if exists.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名或邮箱已存在")

    user = User(
        username=body.username,
        email=body.email,
        full_name=body.full_name,
        hashed_password=get_password_hash(body.password),
        phone=body.phone,
        department=body.department,
        title=body.title,
        role_id=body.role_id,
        organization_id=body.organization_id,
    )
    
    if body.role_id:
        role_res = await db.execute(select(Role).where(Role.id == body.role_id))
        r = role_res.scalar_one_or_none()
        if r and r.code == 'SUPER_ADMIN':
            user.is_superuser = True

    db.add(user)
    await db.commit()
    await db.refresh(user)
    return {"message": "用户创建成功", "data": user_to_dict(user)}


@router.get("/roles", summary="获取角色列表")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(select(Role).order_by(Role.name))
    roles = result.scalars().all()
    return {
        "data": [{
            "id": str(r.id), "code": r.code, "name": r.name,
            "description": r.description, "permissions": r.permissions,
        } for r in roles]
    }


@router.get("/{user_id}", summary="用户详情")
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(User, Role).outerjoin(Role, User.role_id == Role.id).where(User.id == user_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="用户不存在")
    u, r = row
    return {"data": user_to_dict(u, r)}


@router.put("/{user_id}", summary="更新用户")
async def update_user(
    user_id: UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:write")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = body.model_dump(exclude_unset=True)
    if "password" in update_data:
        pwd = update_data.pop("password")
        valid, msg = validate_password_strength(pwd)
        if not valid:
            raise HTTPException(status_code=400, detail=msg)
        user.hashed_password = get_password_hash(pwd)
        
    if "role_id" in update_data:
        role_res = await db.execute(select(Role).where(Role.id == update_data["role_id"]))
        r = role_res.scalar_one_or_none()
        if r and r.code == 'SUPER_ADMIN':
            update_data["is_superuser"] = True
        else:
            update_data["is_superuser"] = False

    for k, v in update_data.items():
        setattr(user, k, v)

    await db.commit()
    return {"message": "更新成功"}

@router.delete("/{user_id}", summary="删除用户")
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:write")),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.is_superuser:
        raise HTTPException(status_code=400, detail="不能删除系统超级管理员")
        
    try:
        # 为了能够删除没有其他硬关联的测试用户，先清理其自己产生的关联数据
        from app.models.models import Timesheet
        await db.execute(delete(Timesheet).where(Timesheet.user_id == user_id))
        
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()
        return {"message": "删除成功"}
    except Exception as e:
        await db.rollback()
        # 捕获外键约束错误
        if "ForeignKeyViolationError" in str(e) or "foreign key constraint" in str(e):
            raise HTTPException(status_code=400, detail="无法删除：该用户已关联工时、试验或其他业务数据")
        raise HTTPException(status_code=500, detail=f"删除失败：{str(e)}")
