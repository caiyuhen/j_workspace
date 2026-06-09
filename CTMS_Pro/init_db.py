<<<<<<< HEAD
"""初始化CTMS_Pro数据库"""
import asyncio
import asyncpg
import sys
sys.stdout.reconfigure(encoding='utf-8')

async def init_database():
    # 连接到postgres默认数据库（创建用户和数据库需要）
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        database='postgres',
        password='root@123'
    )
    
    # 检查并创建用户
    user_exists = await conn.fetchval(
        "SELECT 1 FROM pg_roles WHERE rolname='ctms_user'"
    )
    if not user_exists:
        await conn.execute("CREATE USER ctms_user WITH PASSWORD 'ctms2026'")
        print("✓ 创建用户 ctms_user")
    else:
        print("✓ 用户 ctms_user 已存在")
        await conn.execute("ALTER USER ctms_user WITH PASSWORD 'ctms2026'")
        print("✓ 已统一用户 ctms_user 密码")
    
    # 检查并创建数据库
    db_exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname='ctms_pro'"
    )
    if not db_exists:
        await conn.execute('CREATE DATABASE ctms_pro OWNER ctms_user')
        print("✓ 创建数据库 ctms_pro")
    else:
        print("✓ 数据库 ctms_pro 已存在")
    
    # 授予权限
    await conn.execute('GRANT ALL PRIVILEGES ON DATABASE ctms_pro TO ctms_user')
    
    await conn.close()
    print("\n数据库初始化完成！")

if __name__ == "__main__":
    asyncio.run(init_database())
=======
"""初始化CTMS_Pro数据库"""
import asyncio
import asyncpg
import sys
sys.stdout.reconfigure(encoding='utf-8')

async def init_database():
    # 连接到postgres默认数据库（创建用户和数据库需要）
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        database='postgres',
        password='root@123'
    )
    
    # 检查并创建用户
    user_exists = await conn.fetchval(
        "SELECT 1 FROM pg_roles WHERE rolname='ctms_user'"
    )
    if not user_exists:
        await conn.execute("CREATE USER ctms_user WITH PASSWORD 'ctms2026'")
        print("✓ 创建用户 ctms_user")
    else:
        print("✓ 用户 ctms_user 已存在")
        await conn.execute("ALTER USER ctms_user WITH PASSWORD 'ctms2026'")
        print("✓ 已统一用户 ctms_user 密码")
    
    # 检查并创建数据库
    db_exists = await conn.fetchval(
        "SELECT 1 FROM pg_database WHERE datname='ctms_pro'"
    )
    if not db_exists:
        await conn.execute('CREATE DATABASE ctms_pro OWNER ctms_user')
        print("✓ 创建数据库 ctms_pro")
    else:
        print("✓ 数据库 ctms_pro 已存在")
    
    # 授予权限
    await conn.execute('GRANT ALL PRIVILEGES ON DATABASE ctms_pro TO ctms_user')
    
    await conn.close()
    print("\n数据库初始化完成！")

if __name__ == "__main__":
    asyncio.run(init_database())
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
