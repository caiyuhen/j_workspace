import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.models import PatientVisit

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(PatientVisit.id, PatientVisit.patient_id, PatientVisit.status, PatientVisit.planned_date).limit(5))
        for r in res.all():
            print(r)

asyncio.run(main())