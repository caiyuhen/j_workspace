import asyncio
import asyncpg

async def run():
    conn = await asyncpg.connect(user='ctms_user', password='ctms2026', database='ctms_pro', host='127.0.0.1', port=5432)
    val = await conn.fetch("SELECT tablename, tableowner FROM pg_tables WHERE schemaname = 'public'")
    for row in val:
        print(f"Table: {row['tablename']}, Owner: {row['tableowner']}")
    await conn.close()

asyncio.run(run())