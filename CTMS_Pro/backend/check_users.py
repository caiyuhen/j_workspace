import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import User

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User.username, User.email, User.is_active))
        print(res.all())

asyncio.run(main())