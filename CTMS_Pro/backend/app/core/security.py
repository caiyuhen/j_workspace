<<<<<<< HEAD
"""
安全工具：密码哈希、JWT令牌、加密/解密
符合 FDA 21 CFR Part 11 / FIDO2 标准
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
import hashlib
from app.core.config import settings

# ─── 密码哈希 ──────────────────────────────────────────────────────
def _prepare_password_bytes(password: str) -> bytes:
    """将密码转换为 bcrypt 可接受的字节串（<=72 bytes）"""
    pwd_bytes = (password or "").encode("utf-8")
    if len(pwd_bytes) > 72:
        # 对超长密码先做 sha256，规避 bcrypt 72 字节限制
        pwd_bytes = hashlib.sha256(pwd_bytes).hexdigest().encode("utf-8")
    return pwd_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        plain = _prepare_password_bytes(plain_password)
        hashed = (hashed_password or "").encode("utf-8")
        return bcrypt.checkpw(plain, hashed)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    plain = _prepare_password_bytes(password)
    return bcrypt.hashpw(plain, bcrypt.gensalt(rounds=12)).decode("utf-8")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    校验密码强度
    要求：至少8位，包含大小写字母、数字和特殊字符
    """
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not any(c.isupper() for c in password):
        return False, "密码必须包含至少一个大写字母"
    if not any(c.islower() for c in password):
        return False, "密码必须包含至少一个小写字母"
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含至少一个数字"
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        return False, "密码必须包含至少一个特殊字符"
    return True, "密码强度合格"


# ─── JWT 令牌 ──────────────────────────────────────────────────────

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_data: Optional[dict] = None
) -> str:
    """创建 Access Token (JWT)"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(subject),
        "type": "access",
        "jti": secrets.token_urlsafe(16),  # JWT ID，用于吊销
    }
    if extra_data:
        to_encode.update(extra_data)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, Any]) -> str:
    """创建 Refresh Token"""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(subject),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并验证 JWT"""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    return payload


# ─── 数据加密（GDPR/HIPAA PII 保护）──────────────────────────────

def _get_fernet_key() -> bytes:
    """从 SECRET_KEY 派生 Fernet 加密密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ctms_pro_pii_salt",  # 生产环境应从配置读取
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return key


_fernet = Fernet(_get_fernet_key())


def encrypt_pii(data: str) -> bytes:
    """加密 PII 数据（AES-256 via Fernet）"""
    if not data:
        return b""
    return _fernet.encrypt(data.encode("utf-8"))


def decrypt_pii(encrypted: bytes) -> str:
    """解密 PII 数据"""
    if not encrypted:
        return ""
    try:
        return _fernet.decrypt(encrypted).decode("utf-8")
    except Exception:
        return "[解密失败]"


def mask_phone(phone: str) -> str:
    """手机号脱敏：138****1234"""
    if len(phone) == 11:
        return phone[:3] + "****" + phone[-4:]
    return phone[:3] + "****"


def mask_id_card(id_card: str) -> str:
    """身份证脱敏：310***********1234"""
    if len(id_card) == 18:
        return id_card[:3] + "*" * 11 + id_card[-4:]
    return id_card[:3] + "****"


def mask_name(name: str) -> str:
    """姓名脱敏：张*明"""
    if len(name) <= 1:
        return name
    if len(name) == 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]


def sha256_hash(data: str) -> str:
    """SHA-256 哈希（用于文件完整性校验）"""
    return hashlib.sha256(data.encode()).hexdigest()
=======
"""
安全工具：密码哈希、JWT令牌、加密/解密
符合 FDA 21 CFR Part 11 / FIDO2 标准
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Union, Any
from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import secrets
import hashlib
from app.core.config import settings

# ─── 密码哈希 ──────────────────────────────────────────────────────
def _prepare_password_bytes(password: str) -> bytes:
    """将密码转换为 bcrypt 可接受的字节串（<=72 bytes）"""
    pwd_bytes = (password or "").encode("utf-8")
    if len(pwd_bytes) > 72:
        # 对超长密码先做 sha256，规避 bcrypt 72 字节限制
        pwd_bytes = hashlib.sha256(pwd_bytes).hexdigest().encode("utf-8")
    return pwd_bytes


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    try:
        plain = _prepare_password_bytes(plain_password)
        hashed = (hashed_password or "").encode("utf-8")
        return bcrypt.checkpw(plain, hashed)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    plain = _prepare_password_bytes(password)
    return bcrypt.hashpw(plain, bcrypt.gensalt(rounds=12)).decode("utf-8")


def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    校验密码强度
    要求：至少8位，包含大小写字母、数字和特殊字符
    """
    if len(password) < 8:
        return False, "密码长度至少8位"
    if not any(c.isupper() for c in password):
        return False, "密码必须包含至少一个大写字母"
    if not any(c.islower() for c in password):
        return False, "密码必须包含至少一个小写字母"
    if not any(c.isdigit() for c in password):
        return False, "密码必须包含至少一个数字"
    if not any(c in "!@#$%^&*()_+-=[]{}|;':\",./<>?" for c in password):
        return False, "密码必须包含至少一个特殊字符"
    return True, "密码强度合格"


# ─── JWT 令牌 ──────────────────────────────────────────────────────

def create_access_token(
    subject: Union[str, Any],
    expires_delta: Optional[timedelta] = None,
    extra_data: Optional[dict] = None
) -> str:
    """创建 Access Token (JWT)"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(subject),
        "type": "access",
        "jti": secrets.token_urlsafe(16),  # JWT ID，用于吊销
    }
    if extra_data:
        to_encode.update(extra_data)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: Union[str, Any]) -> str:
    """创建 Refresh Token"""
    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "sub": str(subject),
        "type": "refresh",
        "jti": secrets.token_urlsafe(16),
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict:
    """解码并验证 JWT"""
    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM]
    )
    return payload


# ─── 数据加密（GDPR/HIPAA PII 保护）──────────────────────────────

def _get_fernet_key() -> bytes:
    """从 SECRET_KEY 派生 Fernet 加密密钥"""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"ctms_pro_pii_salt",  # 生产环境应从配置读取
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return key


_fernet = Fernet(_get_fernet_key())


def encrypt_pii(data: str) -> bytes:
    """加密 PII 数据（AES-256 via Fernet）"""
    if not data:
        return b""
    return _fernet.encrypt(data.encode("utf-8"))


def decrypt_pii(encrypted: bytes) -> str:
    """解密 PII 数据"""
    if not encrypted:
        return ""
    try:
        return _fernet.decrypt(encrypted).decode("utf-8")
    except Exception:
        return "[解密失败]"


def mask_phone(phone: str) -> str:
    """手机号脱敏：138****1234"""
    if len(phone) == 11:
        return phone[:3] + "****" + phone[-4:]
    return phone[:3] + "****"


def mask_id_card(id_card: str) -> str:
    """身份证脱敏：310***********1234"""
    if len(id_card) == 18:
        return id_card[:3] + "*" * 11 + id_card[-4:]
    return id_card[:3] + "****"


def mask_name(name: str) -> str:
    """姓名脱敏：张*明"""
    if len(name) <= 1:
        return name
    if len(name) == 2:
        return name[0] + "*"
    return name[0] + "*" * (len(name) - 2) + name[-1]


def sha256_hash(data: str) -> str:
    """SHA-256 哈希（用于文件完整性校验）"""
    return hashlib.sha256(data.encode()).hexdigest()
>>>>>>> origin/main
