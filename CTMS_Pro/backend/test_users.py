import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import User, Role

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User, Role).outerjoin(Role, User.role_id == Role.id))
        rows = res.all()
        for u, r in rows:
            print(u.id, u.username, u.full_name, r.name if r else None)

asyncio.run(main())