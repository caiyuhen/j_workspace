import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import Role

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Role))
        roles = res.scalars().all()
        for r in roles:
            print(f"Role: code={r.code}, name={r.name}")

asyncio.run(run())
