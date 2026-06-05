"""修改数据库密码"""
import asyncio
import asyncpg

async def fix_password():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='root@123',
        database='postgres'
    )
    await conn.execute("ALTER USER ctms_user WITH PASSWORD 'root@123'")
    print('密码已修改为 root@123')
    await conn.close()

asyncio.run(fix_password())
