"""
数据库初始化脚本

创建所有表并插入初始数据
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import engine, async_engine, Base
from app.models import User, UserRole, Skill
from app.core.auth import get_password_hash
from app.config import settings


async def create_tables():
    """创建所有数据库表"""
    print("📦 正在创建数据库表...")
    
    async with async_engine.begin() as conn:
        # 创建所有表
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ 数据库表创建完成")


async def create_initial_data():
    """创建初始数据"""
    print("📝 正在创建初始数据...")
    
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as session:
        # 检查是否已有用户
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()
        
        if count > 0:
            print("ℹ️  数据库已有数据，跳过初始化")
            return
        
        # 创建默认管理员用户
        admin_user = User(
            email="admin@medical.ai",
            hashed_password=get_password_hash("admin123"),
            name="系统管理员",
            role=UserRole.ADMIN,
            is_active=True,
            department="信息科"
        )
        session.add(admin_user)
        
        # 创建示例医生用户
        doctor_user = User(
            email="doctor@medical.ai",
            hashed_password=get_password_hash("doctor123"),
            name="张医生",
            role=UserRole.DOCTOR,
            is_active=True,
            department="内科"
        )
        session.add(doctor_user)
        
        # 创建示例研究员用户
        researcher_user = User(
            email="researcher@medical.ai",
            hashed_password=get_password_hash("researcher123"),
            name="李研究员",
            role=UserRole.RESEARCHER,
            is_active=True,
            department="研究中心"
        )
        session.add(researcher_user)
        
        # 创建内置技能
        skills = [
            Skill(
                name="medical_diagnosis",
                display_name="医学诊断",
                description="基于症状进行疾病诊断分析",
                category="diagnosis",
                protocol="builtin",
                is_active=True,
                is_builtin=True
            ),
            Skill(
                name="drug_interaction",
                display_name="药物相互作用检查",
                description="检查多种药物之间的相互作用",
                category="pharmacy",
                protocol="builtin",
                is_active=True,
                is_builtin=True
            ),
            Skill(
                name="literature_search",
                display_name="医学文献检索",
                description="检索医学文献和研究报告",
                category="research",
                protocol="skillhub",
                is_active=True,
                is_builtin=False
            ),
            Skill(
                name="clinical_guideline",
                display_name="临床指南查询",
                description="查询临床诊疗指南",
                category="reference",
                protocol="skillhub",
                is_active=True,
                is_builtin=False
            ),
            Skill(
                name="lab_interpretation",
                display_name="检验结果解读",
                description="解读临床检验结果",
                category="diagnosis",
                protocol="builtin",
                is_active=True,
                is_builtin=True
            ),
            Skill(
                name="image_analysis",
                display_name="医学影像分析",
                description="分析医学影像（X光、CT、MRI等）",
                category="imaging",
                protocol="mcp",
                is_active=True,
                is_builtin=False
            )
        ]
        
        for skill in skills:
            session.add(skill)
        
        await session.commit()
    
    print("✅ 初始数据创建完成")


async def init_database():
    """初始化数据库"""
    print("=" * 50)
    print("🏥 医学智能体系统 - 数据库初始化")
    print("=" * 50)
    print(f"📍 数据库: {settings.DATABASE_URL}")
    print()
    
    try:
        # 创建表
        await create_tables()
        
        # 创建初始数据
        await create_initial_data()
        
        print()
        print("=" * 50)
        print("✨ 数据库初始化完成！")
        print()
        print("默认用户账户:")
        print("  - admin@medical.ai / admin123 (管理员)")
        print("  - doctor@medical.ai / doctor123 (医生)")
        print("  - researcher@medical.ai / researcher123 (研究员)")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        raise


def main():
    """主函数"""
    asyncio.run(init_database())


if __name__ == "__main__":
    main()
