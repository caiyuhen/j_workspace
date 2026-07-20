<<<<<<< HEAD
"""修改数据库用户密码为不含特殊字符的版本"""
import asyncio
import asyncpg
import sys
sys.stdout.reconfigure(encoding='utf-8')

async def fix():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='root@123',
        database='postgres'
    )
    
    # 修改密码为不含特殊字符的版本
    await conn.execute("ALTER USER ctms_user WITH PASSWORD 'ctms2026'")
    print('密码已修改为 ctms2026')
    
    await conn.close()

asyncio.run(fix())
=======
"""修改数据库用户密码为不含特殊字符的版本"""
import asyncio
import asyncpg
import sys
sys.stdout.reconfigure(encoding='utf-8')

async def fix():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='root@123',
        database='postgres'
    )
    
    # 修改密码为不含特殊字符的版本
    await conn.execute("ALTER USER ctms_user WITH PASSWORD 'ctms2026'")
    print('密码已修改为 ctms2026')
    
    await conn.close()

asyncio.run(fix())
>>>>>>> origin/main
