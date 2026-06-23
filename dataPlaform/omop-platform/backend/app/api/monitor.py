from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.monitor import MonitoringService

router = APIRouter()

@router.get("/health")
def check_health(db: Session = Depends(get_db)):
    """
    Returns the comprehensive system health report.
    Checks Staging layer processing latency, Storage Capacity, and Error Rates.
    """
    monitor_svc = MonitoringService(db)
    return monitor_svc.get_system_health_report()
