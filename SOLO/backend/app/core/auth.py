"""
用户认证模块

提供JWT认证、用户登录注册等功能
"""
from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr

from app.config import settings


# 密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Token(BaseModel):
    """Token响应模型"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token数据模型"""
    user_id: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class UserLogin(BaseModel):
    """用户登录请求"""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """用户注册请求"""
    email: EmailStr
    password: str
    name: Optional[str] = None


class UserResponse(BaseModel):
    """用户响应模型"""
    id: str
    email: str
    name: Optional[str]
    role: str
    created_at: datetime


# ============== 密码处理 ==============

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return pwd_context.hash(password)


# ============== JWT Token ==============

def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    创建访问令牌
    
    Args:
        data: 要编码的数据
        expires_delta: 过期时间增量
        
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    解码访问令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        TokenData: 解码后的数据，失败返回None
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None:
            return None
        
        return TokenData(user_id=user_id, email=email, role=role)
        
    except JWTError:
        return None


# ============== 用户服务 ==============

# 模拟用户数据库（实际应使用数据库）
fake_users_db = {
    "admin@medical.ai": {
        "id": "user_001",
        "email": "admin@medical.ai",
        "name": "管理员",
        "hashed_password": get_password_hash("admin123"),
        "role": "admin",
        "created_at": datetime.utcnow()
    },
    "doctor@medical.ai": {
        "id": "user_002",
        "email": "doctor@medical.ai",
        "name": "张医生",
        "hashed_password": get_password_hash("doctor123"),
        "role": "doctor",
        "created_at": datetime.utcnow()
    }
}


class UserService:
    """用户服务"""
    
    @staticmethod
    async def get_user_by_email(email: str) -> Optional[dict]:
        """根据邮箱获取用户"""
        return fake_users_db.get(email)
    
    @staticmethod
    async def get_user_by_id(user_id: str) -> Optional[dict]:
        """根据ID获取用户"""
        for user in fake_users_db.values():
            if user["id"] == user_id:
                return user
        return None
    
    @staticmethod
    async def create_user(email: str, password: str, name: str = None) -> dict:
        """创建用户"""
        if email in fake_users_db:
            raise ValueError("邮箱已注册")
        
        user_id = f"user_{len(fake_users_db) + 1:03d}"
        
        user = {
            "id": user_id,
            "email": email,
            "name": name or email.split("@")[0],
            "hashed_password": get_password_hash(password),
            "role": "user",
            "created_at": datetime.utcnow()
        }
        
        fake_users_db[email] = user
        return user
    
    @staticmethod
    async def authenticate_user(email: str, password: str) -> Optional[dict]:
        """认证用户"""
        user = await UserService.get_user_by_email(email)
        
        if not user:
            return None
        
        if not verify_password(password, user["hashed_password"]):
            return None
        
        return user
    
    @staticmethod
    async def login(email: str, password: str) -> Optional[Token]:
        """用户登录"""
        user = await UserService.authenticate_user(email, password)
        
        if not user:
            return None
        
        access_token = create_access_token(
            data={
                "sub": user["id"],
                "email": user["email"],
                "role": user["role"]
            }
        )
        
        return Token(
            access_token=access_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    
    @staticmethod
    async def register(email: str, password: str, name: str = None) -> UserResponse:
        """用户注册"""
        user = await UserService.create_user(email, password, name)
        
        return UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            role=user["role"],
            created_at=user["created_at"]
        )


# 全局用户服务实例
user_service = UserService()
