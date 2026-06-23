from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os
import shutil
import tempfile
import traceback
import uuid
import json
from datetime import datetime

from app.services.dicom_parser import DicomParser
from app.services.raw_persistence import RawPersistenceService
from app.db.database import get_db, SessionLocal
from app.models.raw import SourceBatch, RawRecord
from app.models.staging import StagingObservation

router = APIRouter()

# Mock Object Storage path
MINIO_MOCK_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "minio_mock", "dicom")

def process_dicom_task(tmp_path: str, filename: str, batch_id: str):
    """Background task to process DICOM dual-stream ingestion."""
    db = SessionLocal()
    persistence_svc = RawPersistenceService(db)
    try:
        parser = DicomParser(tmp_path)
        
        # 1. Metadata Stream
        metadata = parser.extract_metadata()
        
        # Determine paths
        patient_id = metadata.get("patient_id", "UNKNOWN")
        study_uid = metadata.get("study_instance_uid", "UNKNOWN_STUDY")
        new_filename = f"{uuid.uuid4().hex[:8]}.dcm"
        target_path = os.path.join(MINIO_MOCK_DIR, patient_id, study_uid, new_filename)
        
        # 2. File Stream (De-identification & Storage)
        saved_path = parser.deidentify_dicom(target_path, new_patient_id=f"hash_{patient_id}")
        
        # 3. Store Raw Metadata in DB
        raw_record = RawRecord(
            batch_id=batch_id,
            row_data=metadata
        )
        db.add(raw_record)
        db.commit()
        db.refresh(raw_record)
        
        # 4. Map to Staging Observation
        # Extract dates
        obs_date = None
        obs_dt = None
        if metadata.get("study_date"):
            try:
                obs_date = datetime.strptime(metadata["study_date"], "%Y%m%d").date()
                if metadata.get("study_time"):
                    dt_str = metadata["study_date"] + metadata["study_time"].split('.')[0]
                    obs_dt = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
            except Exception:
                pass
                
        staging_obs = StagingObservation(
            source_batch_id=batch_id,
            raw_record_id=raw_record.id,
            person_source_value=metadata.get("patient_id"),
            observation_source_value=metadata.get("modality", "Imaging"),
            observation_date=obs_date,
            observation_datetime=obs_dt,
            value_as_string=json.dumps(metadata),
            observation_concept_id=4052536, # Example OMOP concept for 'Medical imaging'
            file_storage_path=saved_path
        )
        db.add(staging_obs)
        db.commit()
        
        # Complete batch
        persistence_svc.complete_batch(batch_id, total_rows=1, error_rows=0, status="completed")
        
    except Exception as e:
        traceback.print_exc()
        # Mark batch as failed
        persistence_svc.complete_batch(batch_id, total_rows=0, error_rows=1, status="failed")
    finally:
        db.close()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/upload")
async def upload_dicom(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a DICOM file for dual-stream processing."""
    if not file.filename.lower().endswith('.dcm'):
        raise HTTPException(status_code=400, detail="Only DICOM (.dcm) files are supported")
        
    try:
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        persistence_svc = RawPersistenceService(db)
        batch = persistence_svc.create_batch(file.filename)
        
        # Dispatch to background task
        background_tasks.add_task(process_dicom_task, tmp_path, file.filename, batch.id)
        
        return {
            "batch_id": batch.id,
            "filename": file.filename,
            "message": "DICOM file accepted. Dual-stream processing started."
        }
    except Exception as e:
        traceback.print_exc()
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))
