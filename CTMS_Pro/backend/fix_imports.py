import os

files = [
    "drugs.py", "adverse_events.py", "reports.py", "documents.py",
    "iwrs.py", "contracts.py", "visits.py", "patients.py", "trials.py"
]

for file in files:
    path = os.path.join("app/api/v1/endpoints", file)
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace "from app.models.models import TrialSite" with "from app.models.models import TrialSite, Site"
    # Replace "from app.models.models import TrialSite, Trial" with "from app.models.models import TrialSite, Trial, Site"
    # Replace "from app.models.models import TrialSite, Trial, Patient" with "from app.models.models import TrialSite, Trial, Patient, Site"
    # Replace "from app.models.models import Patient, TrialSite, Trial" with "from app.models.models import Patient, TrialSite, Trial, Site"
    
    content = content.replace("from app.models.models import TrialSite, Trial, Patient", "from app.models.models import TrialSite, Trial, Patient, Site")
    content = content.replace("from app.models.models import Patient, TrialSite, Trial", "from app.models.models import Patient, TrialSite, Trial, Site")
    content = content.replace("from app.models.models import TrialSite, Trial", "from app.models.models import TrialSite, Trial, Site")
    content = content.replace("from app.models.models import TrialSite\n", "from app.models.models import TrialSite, Site\n")
    
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
