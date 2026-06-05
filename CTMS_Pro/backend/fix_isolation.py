import os
import re

files = [
    "drugs.py", "adverse_events.py", "reports.py", "documents.py",
    "iwrs.py", "contracts.py", "visits.py", "patients.py", "sites.py", "trials.py"
]

for file in files:
    path = os.path.join("app/api/v1/endpoints", file)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # For sites.py: Site.id == current_user.organization_id -> Site.organization_id == current_user.organization_id
    content = content.replace("Site.id == current_user.organization_id", "Site.organization_id == current_user.organization_id")
    
    # For others like TrialSite.site_id == current_user.organization_id -> TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))
    # We need to make sure `Site` is imported.
    
    # Let's replace TrialSite.site_id == current_user.organization_id
    content = content.replace(
        "TrialSite.site_id == current_user.organization_id", 
        "TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))"
    )
    
    # For Patient.site_id == current_user.organization_id
    content = content.replace(
        "Patient.site_id == current_user.organization_id",
        "Patient.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))"
    )
    
    # For PatientVisit.site_id == current_user.organization_id
    content = content.replace(
        "PatientVisit.site_id == current_user.organization_id",
        "PatientVisit.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))"
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"Processed {file}")
