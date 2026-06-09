<<<<<<< HEAD
"""检查本地PostgreSQL数据库状态"""
import asyncio
import asyncpg
import sys
sys.stdout.reconfigure(encoding='utf-8')

async def check_db():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='ctms_user',
            password='ctms2026',
            database='ctms_pro'
        )
        
        tables = await conn.fetch("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        count = tables[0]['count']
        print('=== 本地PostgreSQL数据库状态 ===')
        print('数据库: ctms_pro')
        print('用户: ctms_user') 
        print('端口: 5432')
        print('表数量:', count)
        
        # 检查是否有数据
        trials = await conn.fetch("SELECT COUNT(*) FROM trials")
        print('试验数量:', trials[0]['count'])
        
        await conn.close()
        print('状态: 已连接到本地PostgreSQL ✓')
    except Exception as e:
        print('连接失败:', e)

asyncio.run(check_db())
=======
"""检查本地PostgreSQL数据库状态"""
import asyncio
import asyncpg
import sys
sys.stdout.reconfigure(encoding='utf-8')

async def check_db():
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='ctms_user',
            password='ctms2026',
            database='ctms_pro'
        )
        
        tables = await conn.fetch("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public'")
        count = tables[0]['count']
        print('=== 本地PostgreSQL数据库状态 ===')
        print('数据库: ctms_pro')
        print('用户: ctms_user') 
        print('端口: 5432')
        print('表数量:', count)
        
        # 检查是否有数据
        trials = await conn.fetch("SELECT COUNT(*) FROM trials")
        print('试验数量:', trials[0]['count'])
        
        await conn.close()
        print('状态: 已连接到本地PostgreSQL ✓')
    except Exception as e:
        print('连接失败:', e)

asyncio.run(check_db())
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
