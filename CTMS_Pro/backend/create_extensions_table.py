import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.models import Base
from app.db.session import engine

async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Created tables")

if __name__ == "__main__":
    asyncio.run(main())
