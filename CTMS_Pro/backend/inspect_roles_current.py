import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import Role

async def run():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Role))
        for r in res.scalars().all():
            print(f'{r.code}: {r.permissions}')

if __name__ == '__main__':
    asyncio.run(run())
