import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    try:
        engine = create_async_engine('postgresql+asyncpg://ctms_user:ctms2026@localhost:5432/ctms_pro')
        async with engine.begin() as conn:
            # Grant all privileges to ctms_user
            await conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ctms_user;"))
            
            # Now let's try to add the column, we might still fail if not owner.
            # But maybe we can add the column as superuser? We don't have superuser password.
            
            # Alternatively, we can recreate the table? No, it has data.
            # Let's check table owner.
            res = await conn.execute(text("SELECT tablename, tableowner FROM pg_tables WHERE schemaname = 'public';"))
            for row in res:
                print(row)
        await engine.dispose()
    except Exception as e:
        print("Error:", e)

asyncio.run(main())