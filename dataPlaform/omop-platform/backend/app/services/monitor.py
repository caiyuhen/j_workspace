import psutil
import os
import time
import logging
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app.models.raw import SourceBatch

logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Service to monitor Staging and Ingestion health.
    Includes capacity checking, latency tracking, and error threshold alerts.
    """
    
    def __init__(self, db: Session):
        self.db = db
        # Thresholds
        self.LATENCY_THRESHOLD_MINUTES = 5
        self.ERROR_RATE_THRESHOLD = 0.1 # 10%
        self.MINIO_MOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "minio_mock")

    def check_storage_capacity(self):
        """Check if the disk where MinIO/Mock storage is located has sufficient capacity."""
        # Ensure dir exists to check its partition
        os.makedirs(self.MINIO_MOCK_DIR, exist_ok=True)
        usage = psutil.disk_usage(self.MINIO_MOCK_DIR)
        
        # If less than 10% free space
        if usage.percent > 90.0:
            logger.warning(f"[ALERT] Storage capacity critical! Usage: {usage.percent}%. Free: {usage.free / (1024**3):.2f} GB")
            return False, f"Storage usage critical: {usage.percent}%"
        return True, "Storage capacity normal"

    def check_processing_latency(self):
        """Check for batches that are stuck in 'processing' state for longer than the threshold."""
        threshold_time = datetime.utcnow() - timedelta(minutes=self.LATENCY_THRESHOLD_MINUTES)
        stuck_batches = self.db.query(SourceBatch).filter(
            SourceBatch.status == "processing",
            SourceBatch.created_at < threshold_time
        ).all()
        
        if stuck_batches:
            logger.error(f"[ALERT] Found {len(stuck_batches)} batches stuck in processing for over {self.LATENCY_THRESHOLD_MINUTES} minutes.")
            for b in stuck_batches:
                logger.error(f"  - Batch {b.id} ({b.filename}) started at {b.created_at}")
            return False, f"{len(stuck_batches)} batches exceeded latency threshold"
            
        return True, "Processing latency normal"

    def check_error_rates(self):
        """Check if recent completed batches have an unusually high error rate."""
        # Look at batches from the last 24 hours
        recent_batches = self.db.query(SourceBatch).filter(
            SourceBatch.status == "completed",
            SourceBatch.created_at > datetime.utcnow() - timedelta(days=1)
        ).all()
        
        high_error_batches = []
        for b in recent_batches:
            if b.total_rows > 0:
                error_rate = b.error_rows / (b.total_rows + b.error_rows)
                if error_rate > self.ERROR_RATE_THRESHOLD:
                    high_error_batches.append((b.id, error_rate))
                    
        if high_error_batches:
            logger.warning(f"[ALERT] Found {len(high_error_batches)} recent batches with error rate > {self.ERROR_RATE_THRESHOLD*100}%")
            return False, "High error rate detected in recent batches"
            
        return True, "Error rates normal"

    def get_system_health_report(self):
        """Generate a comprehensive health report."""
        storage_ok, storage_msg = self.check_storage_capacity()
        latency_ok, latency_msg = self.check_processing_latency()
        error_ok, error_msg = self.check_error_rates()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "Healthy" if (storage_ok and latency_ok and error_ok) else "Warning",
            "checks": {
                "storage": {"status": "ok" if storage_ok else "alert", "message": storage_msg},
                "latency": {"status": "ok" if latency_ok else "alert", "message": latency_msg},
                "error_rates": {"status": "ok" if error_ok else "alert", "message": error_msg}
            }
        }
