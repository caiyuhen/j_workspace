import os

# 1. visits.py -> upcoming_visits
with open("app/api/v1/endpoints/visits.py", "r", encoding="utf-8") as f:
    v_content = f.read()

v_isolation = """
    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        cond = (PatientVisit.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | PatientVisit.trial_id.in_(subq)
        
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | PatientVisit.site_id.in_(subq2)
        query = query.where(cond)
"""

if "from datetime import datetime, timedelta" in v_content and "# 数据隔离" not in v_content.split("def upcoming_visits")[1]:
    v_content = v_content.replace(
        "if trial_id:\n        query = query.where(PatientVisit.trial_id == trial_id)",
        "if trial_id:\n        query = query.where(PatientVisit.trial_id == trial_id)\n" + v_isolation
    )
    with open("app/api/v1/endpoints/visits.py", "w", encoding="utf-8") as f:
        f.write(v_content)

# 2. drugs.py -> list_drug_logs
with open("app/api/v1/endpoints/drugs.py", "r", encoding="utf-8") as f:
    d_content = f.read()

d_isolation = """
    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq2 = select(TrialSite.trial_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        cond = (DrugDispensing.trial_id.in_(subq)) | (DrugDispensing.trial_id.in_(subq2))
        query = query.where(cond)
        count_query = count_query.where(cond)
"""

if "def list_drug_logs" in d_content and "# 数据隔离" not in d_content.split("def list_drug_logs")[1]:
    d_content = d_content.replace(
        "count_query = count_query.where(and_(*filters))",
        "count_query = count_query.where(and_(*filters))\n" + d_isolation
    )
    with open("app/api/v1/endpoints/drugs.py", "w", encoding="utf-8") as f:
        f.write(d_content)

# 3. reports.py -> site_enrollment and ae_summary
with open("app/api/v1/endpoints/reports.py", "r", encoding="utf-8") as f:
    r_content = f.read()

r_isolation = """
    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site
        cond = (Patient.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id)))
        
        subq = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        cond = cond | Patient.trial_id.in_(subq)
        
        subq2 = select(TrialSite.site_id).where(TrialSite.pi_user_id == current_user.id)
        cond = cond | Patient.site_id.in_(subq2)
        query = query.where(cond)
"""

if "def site_enrollment" in r_content and "# 数据隔离" not in r_content.split("def site_enrollment")[1]:
    r_content = r_content.replace(
        "if trial_id:\n        query = query.where(Patient.trial_id == trial_id)",
        "if trial_id:\n        query = query.where(Patient.trial_id == trial_id)\n" + r_isolation
    )

r_isolation_ae = """
    # 数据隔离
    if not current_user.is_superuser:
        from app.models.models import TrialSite, Trial, Site, Patient
        subq_trial = select(Trial.id).where(
            (Trial.pm_user_id == current_user.id) | 
            (Trial.created_by == current_user.id)
        )
        subq_site = select(TrialSite.site_id).where(
            (TrialSite.site_id.in_(select(Site.id).where(Site.organization_id == current_user.organization_id))) |
            (TrialSite.pi_user_id == current_user.id)
        )
        subq_patient = select(Patient.id).where(Patient.site_id.in_(subq_site))
        
        base = and_(base, (AdverseEvent.trial_id.in_(subq_trial)) | (AdverseEvent.patient_id.in_(subq_patient)))
"""

if "def ae_summary" in r_content and "# 数据隔离" not in r_content.split("def ae_summary")[1]:
    r_content = r_content.replace(
        "base = and_(*filters) if filters else True",
        "base = and_(*filters) if filters else True\n" + r_isolation_ae
    )
    
    with open("app/api/v1/endpoints/reports.py", "w", encoding="utf-8") as f:
        f.write(r_content)
        
print("Fixed remaining isolated endpoints.")
