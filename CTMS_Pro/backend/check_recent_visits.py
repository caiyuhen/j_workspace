import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import PatientVisit

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(PatientVisit.id, PatientVisit.status, PatientVisit.updated_at).order_by(PatientVisit.updated_at.desc().nulls_last()).limit(10))
        for r in res.all():
            print(r)

asyncio.run(main())