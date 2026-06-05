import asyncio
import uuid
from app.db.session import AsyncSessionLocal
from sqlalchemy import select, update, delete
from app.models.models import Organization, Site, User

async def fix_db():
    async with AsyncSessionLocal() as db:
        # 1. Get all sites
        res = await db.execute(select(Site))
        sites = res.scalars().all()
        
        for site in sites:
            # 2. Check if there's already an organization with the same name
            res_org = await db.execute(select(Organization).where(Organization.name == site.name))
            org = res_org.scalar_one_or_none()
            
            if not org:
                org = Organization(
                    id=uuid.uuid4(),
                    code=site.code,
                    name=site.name,
                    type="HOSPITAL"
                )
                db.add(org)
                await db.flush()
                
            # 3. Link site to this unique organization
            site.organization_id = org.id
            
        await db.commit()
        print("Database sites and organizations fixed.")

asyncio.run(fix_db())