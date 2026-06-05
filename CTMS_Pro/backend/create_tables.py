import asyncio
from app.db.session import engine, Base
import app.models.models

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created")

asyncio.run(main())