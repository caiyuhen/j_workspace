import asyncio
import asyncpg

async def test_pass(pwd):
    try:
        conn = await asyncpg.connect(user='postgres', password=pwd, database='ctms_pro', host='127.0.0.1', port=5432)
        print(f"Success with password: {pwd}")
        await conn.execute("ALTER TABLE trials ADD COLUMN IF NOT EXISTS trial_code VARCHAR(100);")
        print("Column added!")
        await conn.close()
        return True
    except Exception as e:
        print(f"Failed with {pwd}: {e}")
        return False

async def main():
    passwords = ["postgres", "123456", "admin", "root", "", "password", "ctms2026", "12345678"]
    for pwd in passwords:
        if await test_pass(pwd):
            break

asyncio.run(main())