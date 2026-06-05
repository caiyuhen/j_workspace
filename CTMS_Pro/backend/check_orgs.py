import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select
from app.models.models import Site, Organization

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Site.id, Site.name, Site.organization_id))
        print("Sites:", res.all())
        
        res = await db.execute(select(Organization.id, Organization.name))
        print("Orgs:", res.all())

asyncio.run(main())
