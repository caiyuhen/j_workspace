import asyncio
import asyncpg

async def run():
    conn = await asyncpg.connect(user='ctms_user', password='ctms2026', database='ctms_pro', host='127.0.0.1', port=5432)
    val = await conn.fetchval("SELECT schema_owner::regrole FROM information_schema.schemata WHERE schema_name = 'public'")
    print('Schema Owner:', val)
    
    try:
        await conn.execute("DROP TABLE IF EXISTS test_drop;")
        await conn.execute("CREATE TABLE test_drop (id INT);")
        await conn.execute("ALTER TABLE test_drop OWNER TO postgres;")
        print("Created test_drop and changed owner to postgres")
        await conn.execute("DROP TABLE test_drop;")
        print("Dropped test_drop successfully!")
    except Exception as e:
        print("Error:", e)
        
    await conn.close()

asyncio.run(run())