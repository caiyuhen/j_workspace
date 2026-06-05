import asyncio
from sqlalchemy import text
from app.db.session import engine

async def main():
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE trials ADD COLUMN extra_data JSONB DEFAULT '{}';"))
            print("Successfully added extra_data to trials table.")
        except Exception as e:
            print(f"Error or already exists: {e}")

if __name__ == "__main__":
    asyncio.run(main())
