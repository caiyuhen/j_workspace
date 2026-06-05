import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import Site, Organization, User, Role

async def main():
    async with AsyncSessionLocal() as db:
        print("Users:", (await db.execute(select(User.username, User.organization_id, Role.name).outerjoin(Role, User.role_id == Role.id))).all())
        print("Sites:", (await db.execute(select(Site.id, Site.organization_id))).all())
        print("Orgs:", (await db.execute(select(Organization.id, Organization.name))).all())

asyncio.run(main())