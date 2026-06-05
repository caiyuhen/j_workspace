import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.models import Role, User

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Role))
        roles = res.scalars().all()
        
        all_modules = [
            'trial', 'site', 'patient', 'visit', 'document', 'drug', 
            'report', 'timesheet', 'milestone', 'meeting', 'iwrs', 
            'icf', 'ae', 'finance', 'user', 'qc', 'monitoring', 'econsent', 'budget'
        ]
        
        for r in roles:
            if r.code == 'SUPER_ADMIN':
                r.permissions = ['*:*']
            elif r.code == 'PM':
                # PM 有自己管理项目的所有权限
                r.permissions = ['*:*']
            elif r.code == 'CRA' or r.code == 'CRC':
                # CRA/CRC 有指定模块的权限
                # 文件、受试者、物资与药品、统计报表、填写工时、里程碑流浏览、会议安排、随机化系统、电子知情同意、访视管理、SAE管理、发票进度
                # 加上 trial:read, site:read 保证基础页面可访问
                r.permissions = [
                    'trial:read', 'site:read', 'user:read',
                    'document:*', 'patient:*', 'drug:*', 'report:*', 
                    'timesheet:*', 'milestone:read', 'meeting:*', 
                    'iwrs:*', 'icf:*', 'econsent:*', 'visit:*', 'ae:*', 'finance:*'
                ]
            elif r.code == 'PI':
                # PI 所有数据查看权限
                r.permissions = [f"{m}:read" for m in all_modules]
            elif r.code == 'SUB_I':
                # SUB_I 所有数据查看权限
                r.permissions = [f"{m}:read" for m in all_modules]
        
        # 将 SUPER_ADMIN 角色的所有用户的 is_superuser 设置为 True
        super_admin_role = await db.execute(select(Role).where(Role.code == 'SUPER_ADMIN'))
        super_role = super_admin_role.scalar_one_or_none()
        if super_role:
            await db.execute(
                update(User).where(User.role_id == super_role.id).values(is_superuser=True)
            )

        await db.commit()
        print("Role permissions updated.")

if __name__ == '__main__':
    asyncio.run(run())
