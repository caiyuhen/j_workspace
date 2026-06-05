"""
认证API端点
"""
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from app.core.auth import (
    Token,
    UserLogin,
    UserRegister,
    UserResponse,
    UserService,
    decode_access_token,
    TokenData
)


router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    获取当前用户
    
    从JWT令牌中解析用户信息
    """
    token = credentials.credentials
    token_data = decode_access_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token_data


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """获取当前活跃用户"""
    return current_user


@router.post("/login", response_model=Token, summary="用户登录")
async def login(user_login: UserLogin):
    """
    用户登录
    
    - **email**: 用户邮箱
    - **password**: 用户密码
    """
    token = await UserService.login(user_login.email, user_login.password)
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="邮箱或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


@router.post("/register", response_model=UserResponse, summary="用户注册")
async def register(user_register: UserRegister):
    """
    用户注册
    
    - **email**: 用户邮箱
    - **password**: 用户密码
    - **name**: 用户名称（可选）
    """
    try:
        user = await UserService.register(
            email=user_register.email,
            password=user_register.password,
            name=user_register.name
        )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user: TokenData = Depends(get_current_active_user)):
    """获取当前登录用户的信息"""
    user = await UserService.get_user_by_id(current_user.user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )
    
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"]
    )


@router.post("/refresh", response_model=Token, summary="刷新令牌")
async def refresh_token(current_user: TokenData = Depends(get_current_active_user)):
    """刷新访问令牌"""
    from app.core.auth import create_access_token
    from app.config import settings
    
    access_token = create_access_token(
        data={
            "sub": current_user.user_id,
            "email": current_user.email,
            "role": current_user.role
        }
    )
    
    return Token(
        access_token=access_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/logout", summary="用户登出")
async def logout(current_user: TokenData = Depends(get_current_active_user)):
    """
    用户登出
    
    注意：由于使用JWT无状态认证，服务端不维护会话状态。
    客户端需要自行删除存储的令牌。
    """
    return {"message": "登出成功", "user_id": current_user.user_id}
