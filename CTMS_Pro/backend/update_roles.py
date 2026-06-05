import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import Role

async def run():
    roles_data = [
        {"code": "SUPER_ADMIN", "name": "系统管理员"},
        {"code": "PM", "name": "项目经理"},
        {"code": "PI", "name": "主要研究者"},
        {"code": "SUB_I", "name": "研究者"},
        {"code": "CRA", "name": "临床监查员(CRA)"},
        {"code": "CRC", "name": "临床协调员(CRC)"},
        {"code": "PHARMACIST", "name": "药品管理员"},
        {"code": "INVESTIGATOR", "name": "研究者"}
    ]
    
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Role))
        existing_roles = res.scalars().all()
        existing_codes = {r.code: r for r in existing_roles}
        
        for data in roles_data:
            if data["code"] in existing_codes:
                r = existing_codes[data["code"]]
                r.name = data["name"]
            else:
                r = Role(code=data["code"], name=data["name"], description=data["name"], permissions=["*:*"] if data["code"]=="SUPER_ADMIN" else [])
                db.add(r)
                
        await db.commit()
        print("Roles updated.")

asyncio.run(run())
