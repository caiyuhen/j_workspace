import asyncio
import asyncpg

async def run():
    conn = await asyncpg.connect(user='ctms_user', password='ctms2026', database='ctms_pro', host='127.0.0.1', port=5432)
    val = await conn.fetchval("SELECT rolsuper FROM pg_roles WHERE rolname = 'ctms_user'")
    print('Superuser:', val)
    
    # Also check if ctms_user has CREATEROLE or something to become owner
    val2 = await conn.fetchval("SELECT rolcreaterole FROM pg_roles WHERE rolname = 'ctms_user'")
    print('Createrole:', val2)
    
    # Try to become owner of trials table
    try:
        await conn.execute("ALTER TABLE trials OWNER TO ctms_user;")
        print("Successfully changed owner to ctms_user!")
    except Exception as e:
        print("Failed to change owner:", e)
        
    await conn.close()

asyncio.run(run())