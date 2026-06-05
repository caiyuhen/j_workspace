"""
应用配置管理 - 基于 pydantic-settings
支持从 .env 文件和环境变量读取配置
"""
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, validator
from typing import List, Optional, Union
import secrets


class Settings(BaseSettings):
    # ─── 基础配置 ─────────────────────────────────────────
    APP_NAME: str = "CTMS Pro"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    # 使用固定的 SECRET_KEY 防止重启后 token 失效
    SECRET_KEY: str = "d2b9a8f7c6e5d4c3b2a109876543210f_CTMS_PRO_SECRET_KEY"

    # ─── CORS ─────────────────────────────────────────────
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:8899",
        "http://127.0.0.1:8899",
        "http://localhost:3000",
        "*"
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ─── 数据库配置 ────────────────────────────────────────
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "ctms_user"
    POSTGRES_PASSWORD: str = "ctms2026"
    POSTGRES_DB: str = "ctms_pro"
    DATABASE_URL: Optional[str] = None

    @validator("DATABASE_URL", pre=True, always=True)
    def assemble_db_connection(cls, v, values):
        if v:
            return v
        return (
            f"postgresql+asyncpg://{values['POSTGRES_USER']}:"
            f"{values['POSTGRES_PASSWORD']}@{values['POSTGRES_SERVER']}:"
            f"{values['POSTGRES_PORT']}/{values['POSTGRES_DB']}"
        )

    # ─── Redis 配置 ────────────────────────────────────────
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    @validator("REDIS_URL", pre=True, always=True)
    def assemble_redis_url(cls, v, values):
        if v:
            return v
        password = values.get("REDIS_PASSWORD", "")
        auth = f":{password}@" if password else ""
        return f"redis://{auth}{values['REDIS_HOST']}:{values['REDIS_PORT']}/{values['REDIS_DB']}"

    # ─── JWT 配置 ──────────────────────────────────────────
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480    # 8小时
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── 邮件配置 ──────────────────────────────────────────
    SMTP_TLS: bool = True
    SMTP_PORT: int = 465
    SMTP_HOST: str = "smtp.qiye.aliyun.com"
    SMTP_USER: str = "jdjd@jdhhealth.com"
    SMTP_PASSWORD: str = "6eZCXj7OZ7EKzB0F"
    EMAILS_FROM_EMAIL: str = "jdjd@jdhhealth.com"
    EMAILS_FROM_NAME: str = "CTMS Pro"

    # ─── 文件存储 ──────────────────────────────────────────
    S3_ENDPOINT_URL: str = "http://localhost:9000"
    S3_ACCESS_KEY: str = "minioadmin"
    S3_SECRET_KEY: str = "minioadmin"
    S3_BUCKET_NAME: str = "ctms-documents"
    S3_REGION: str = "us-east-1"

    # ─── Celery ────────────────────────────────────────────
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # ─── 业务配置 ──────────────────────────────────────────
    AUDIT_LOG_RETENTION_DAYS: int = 180
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_FILE_TYPES: List[str] = [
        "pdf", "doc", "docx", "xls", "xlsx",
        "jpg", "jpeg", "png", "gif", "zip"
    ]

    # ─── 超管初始账号 ──────────────────────────────────────
    FIRST_SUPERUSER: str = "admin@ctms-pro.com"
    FIRST_SUPERUSER_PASSWORD: str = "Admin@CTMS2026!"

    # ─── 外部系统 IWRS API 配置 ────────────────────────────
    IWRS_SAVE_PROJECT_ALL_URL: str = "https://synctest-test.jdhhealth.cn//rws/rwsProject/saveRwsProjectAll"
    IWRS_SAVE_PROJECT_HOSPITAL_URL: str = "https://synctest-test.jdhhealth.cn//rws/rwsProject/saveProjectHospital"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
