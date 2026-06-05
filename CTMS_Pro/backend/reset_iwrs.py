import asyncio
from sqlalchemy import update
from app.db.session import AsyncSessionLocal
from app.models.models import RandomizationScheme

async def reset_schemes():
    async with AsyncSessionLocal() as session:
        await session.execute(update(RandomizationScheme).values(status='DRAFT'))
        await session.commit()
        print("All IWRS schemes have been reset to DRAFT status in the database.")

if __name__ == "__main__":
    asyncio.run(reset_schemes())