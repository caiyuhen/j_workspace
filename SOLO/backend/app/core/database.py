"""
数据库配置和连接管理
"""
from typing import AsyncGenerator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def _sync_database_url(database_url: str) -> str:
    """生成同步 SQLAlchemy 引擎使用的数据库 URL。"""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if database_url.startswith("sqlite+aiosqlite://"):
        return database_url.replace("sqlite+aiosqlite://", "sqlite://", 1)
    return database_url


def _async_database_url(database_url: str) -> str:
    """生成异步 SQLAlchemy 引擎使用的数据库 URL。"""
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if database_url.startswith("sqlite://"):
        return database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    return database_url


def _engine_options(database_url: str) -> dict:
    """不同数据库使用不同连接池参数。"""
    if database_url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True, "pool_size": 10, "max_overflow": 20}


sync_url = _sync_database_url(settings.DATABASE_URL)
async_url = _async_database_url(settings.DATABASE_URL)

# 同步引擎（用于初始化）
engine = create_engine(
    sync_url,
    echo=settings.DEBUG,
    **_engine_options(sync_url),
)

# 异步引擎（用于API）
async_engine = create_async_engine(
    async_url,
    echo=settings.DEBUG,
    **_engine_options(async_url),
)

# 会话工厂
AsyncSessionLocal = sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# 模型基类
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    获取数据库会话
    
    用于FastAPI依赖注入
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
