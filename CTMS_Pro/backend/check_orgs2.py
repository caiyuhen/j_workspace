import asyncio
from app.db.session import AsyncSessionLocal
from sqlalchemy import select, update
from app.models.models import Organization, Site

async def main():
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(Organization.id, Organization.name, Organization.type))
        orgs = res.all()
        for r in orgs: 
            print(f"Org: {r}")
        
        res = await db.execute(select(Site.id, Site.name, Site.organization_id))
        sites = res.all()
        for s in sites:
            print(f"Site: {s}")

asyncio.run(main())