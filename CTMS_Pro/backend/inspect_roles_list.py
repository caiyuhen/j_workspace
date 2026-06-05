import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import Role

async def main():
    async with AsyncSessionLocal() as db:
        print((await db.execute(select(Role.code, Role.name))).all())

asyncio.run(main())