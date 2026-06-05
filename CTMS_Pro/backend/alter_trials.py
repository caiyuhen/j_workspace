import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    try:
        engine = create_async_engine('postgresql+asyncpg://ctms_user:ctms2026@localhost:5432/ctms_pro')
        async with engine.begin() as conn:
            # Drop constraint if exists and recreate column
            try:
                await conn.execute(text('ALTER TABLE trials ADD COLUMN IF NOT EXISTS trial_code VARCHAR(100);'))
            except Exception as e:
                print("Column may already exist or cannot be added directly", e)
        print('Done')
        await engine.dispose()
    except Exception as e:
        print("Error:", e)

asyncio.run(main())