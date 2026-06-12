"""
数据库初始化：创建初始超管账号
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.models import User, Role
from app.core.security import get_password_hash
from app.core.config import settings


async def init_db(db: AsyncSession) -> None:
    """
    初始化数据库：
    1. 确保角色表有初始数据（已在SQL中插入）
    2. 创建超管账号
    """
    # 检查超管是否已存在
    result = await db.execute(
        select(User).where(User.email == settings.FIRST_SUPERUSER)
    )
    existing = result.scalar_one_or_none()
    if existing:
        logger.info(f"超管账号已存在: {settings.FIRST_SUPERUSER}")
        return

    # 再次检查是否有重复的尝试，捕获异常处理
    try:
        # 查找超管角色
        role_result = await db.execute(
            select(Role).where(Role.code == "SUPER_ADMIN")
        )
        role = role_result.scalar_one_or_none()

        superuser = User(
            username="admin",
            email=settings.FIRST_SUPERUSER,
            full_name="系统超级管理员",
            hashed_password=get_password_hash(settings.FIRST_SUPERUSER_PASSWORD),
            is_active=True,
            is_superuser=True,
            role_id=role.id if role else None,
            department="IT",
            title="系统管理员",
        )
        db.add(superuser)
        await db.commit()
        logger.info(f"✅ 超管账号初始化完成: {settings.FIRST_SUPERUSER}")
    except Exception as e:
        await db.rollback()
        logger.warning(f"超管账号可能已被其他进程创建或初始化失败: {str(e)}")
