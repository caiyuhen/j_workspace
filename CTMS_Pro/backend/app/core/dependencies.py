<<<<<<< HEAD
"""
FastAPI 依赖注入：当前用户认证 & RBAC 权限控制
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from typing import Optional
from loguru import logger

from app.db.session import get_db
from app.models.models import User, TokenBlacklist
from app.core.security import decode_token

# Bearer Token 安全方案
security = HTTPBearer(auto_error=True)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从 JWT Token 获取当前登录用户
    支持 Token 黑名单检查（用户登出后 Token 立即失效）
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份凭证，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

        # 检查 Token 是否已被吊销（登出黑名单）
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已失效，请重新登录",
            )

    except JWTError as e:
        logger.warning(f"JWT 验证失败: {e}")
        raise credentials_exception

    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    # 更新请求上下文（用于审计日志）
    request.state.current_user = user
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """确保用户账号处于激活状态"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员"
        )
    return current_user


def require_permissions(*permissions: str):
    """
    RBAC 权限装饰器工厂
    用法：Depends(require_permissions("trial:read", "patient:write"))
    支持通配符：如 role ADMIN 有 "*:*" 则拥有所有权限
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # 超级管理员跳过权限检查
        if current_user.is_superuser:
            return current_user

        # 加载角色权限
        from app.models.models import Role
        result = await db.execute(
            select(Role).where(Role.id == current_user.role_id)
        )
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="未分配角色，无权访问"
            )

        user_perms: list = role.permissions or []

        # 检查通配符权限
        if "*:*" in user_perms:
            return current_user

        # 检查具体权限
        for perm in permissions:
            module, action = perm.split(":", 1)
            # 支持模块通配符：如 "trial:*" 包含 "trial:read"
            if f"{module}:*" in user_perms or perm in user_perms:
                continue
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 [{perm}] 权限"
            )

        return current_user

    return permission_checker


async def require_superuser(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """要求超级管理员权限"""
    if current_user.is_superuser:
        return current_user
        
    # 如果不是数据库字段 is_superuser=True，检查角色是否为 SUPER_ADMIN 或有所有权限
    from app.models.models import Role
    result = await db.execute(
        select(Role).where(Role.id == current_user.role_id)
    )
    role = result.scalar_one_or_none()
    if role and (role.code == 'SUPER_ADMIN' or '*:*' in (role.permissions or [])):
        return current_user
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="此操作需要超级管理员权限"
    )
=======
"""
FastAPI 依赖注入：当前用户认证 & RBAC 权限控制
"""
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from typing import Optional
from loguru import logger

from app.db.session import get_db
from app.models.models import User, TokenBlacklist
from app.core.security import decode_token

# Bearer Token 安全方案
security = HTTPBearer(auto_error=True)


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    从 JWT Token 获取当前登录用户
    支持 Token 黑名单检查（用户登出后 Token 立即失效）
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证身份凭证，请重新登录",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        token_type: str = payload.get("type")

        if user_id is None or token_type != "access":
            raise credentials_exception

        # 检查 Token 是否已被吊销（登出黑名单）
        result = await db.execute(
            select(TokenBlacklist).where(TokenBlacklist.jti == jti)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 已失效，请重新登录",
            )

    except JWTError as e:
        logger.warning(f"JWT 验证失败: {e}")
        raise credentials_exception

    # 查询用户
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active == True)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception

    # 更新请求上下文（用于审计日志）
    request.state.current_user = user
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """确保用户账号处于激活状态"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员"
        )
    return current_user


def require_permissions(*permissions: str):
    """
    RBAC 权限装饰器工厂
    用法：Depends(require_permissions("trial:read", "patient:write"))
    支持通配符：如 role ADMIN 有 "*:*" 则拥有所有权限
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
        db: AsyncSession = Depends(get_db),
    ) -> User:
        # 超级管理员跳过权限检查
        if current_user.is_superuser:
            return current_user

        # 加载角色权限
        from app.models.models import Role
        result = await db.execute(
            select(Role).where(Role.id == current_user.role_id)
        )
        role = result.scalar_one_or_none()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="未分配角色，无权访问"
            )

        user_perms: list = role.permissions or []

        # 检查通配符权限
        if "*:*" in user_perms:
            return current_user

        # 检查具体权限
        for perm in permissions:
            module, action = perm.split(":", 1)
            # 支持模块通配符：如 "trial:*" 包含 "trial:read"
            if f"{module}:*" in user_perms or perm in user_perms:
                continue
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要 [{perm}] 权限"
            )

        return current_user

    return permission_checker


async def require_superuser(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """要求超级管理员权限"""
    if current_user.is_superuser:
        return current_user
        
    # 如果不是数据库字段 is_superuser=True，检查角色是否为 SUPER_ADMIN 或有所有权限
    from app.models.models import Role
    result = await db.execute(
        select(Role).where(Role.id == current_user.role_id)
    )
    role = result.scalar_one_or_none()
    if role and (role.code == 'SUPER_ADMIN' or '*:*' in (role.permissions or [])):
        return current_user
        
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="此操作需要超级管理员权限"
    )
>>>>>>> origin/main
