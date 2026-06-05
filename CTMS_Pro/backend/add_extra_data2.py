import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine("postgresql+asyncpg://postgres:postgres@localhost:5432/ctms_pro")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE trials ADD COLUMN extra_data JSONB DEFAULT '{}';"))
            print("Successfully added extra_data to trials table.")
        except Exception as e:
            print(f"Error or already exists: {e}")
            
        try:
            await conn.execute(text("GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ctms_user;"))
            await conn.execute(text("ALTER TABLE trials OWNER TO ctms_user;"))
            print("Granted privileges to ctms_user")
        except Exception as e:
            print(f"Privilege error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
