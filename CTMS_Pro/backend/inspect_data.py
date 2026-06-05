import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.models import User, Site, TrialSite, Trial

async def main():
    async with AsyncSessionLocal() as db:
        users = (await db.execute(select(User.id, User.username, User.organization_id, User.role_id, User.title))).all()
        sites = (await db.execute(select(Site.id, Site.name))).all()
        trials = (await db.execute(select(Trial.id, Trial.trial_no, Trial.pm_user_id, Trial.created_by))).all()
        trial_sites = (await db.execute(select(TrialSite.trial_id, TrialSite.site_id, TrialSite.pi_user_id))).all()
        
        print("Users:")
        for u in users: print(f" - {u.username}: org={u.organization_id}, role={u.role_id}, title={u.title}")
        print("\nSites:")
        for s in sites: print(f" - {s.name}: {s.id}")
        print("\nTrials:")
        for t in trials: print(f" - {t.trial_no}: pm={t.pm_user_id}, created_by={t.created_by}")
        print("\nTrialSites:")
        for ts in trial_sites: print(f" - Trial {ts.trial_id} <-> Site {ts.site_id} (PI: {ts.pi_user_id})")

asyncio.run(main())