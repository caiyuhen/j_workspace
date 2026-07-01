from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os
import shutil
import tempfile
import traceback
import uuid
import json
from datetime import datetime
from minio import Minio

from app.core.logger import data_logger
from app.services.dicom_parser import DicomParser
from app.services.raw_persistence import RawPersistenceService
from app.db.database import get_db, SessionLocal
from app.models.raw import SourceBatch, RawRecord
from app.models.staging import StagingObservation

router = APIRouter()

# MinIO Client Setup
MINIO_URL = os.getenv("MINIO_URL", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = "dicom-images"

def get_minio_client():
    client = Minio(
        MINIO_URL,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False
    )
    try:
        if not client.bucket_exists(MINIO_BUCKET):
            client.make_bucket(MINIO_BUCKET)
    except Exception as e:
        if "积极拒绝" in str(e) or "ConnectionRefusedError" in str(e) or "MaxRetryError" in str(e) or "WinError 10061" in str(e):
            raise Exception(f"Failed to connect to MinIO object storage at {MINIO_URL}. Please ensure the MinIO service is running. Details: {e}")
        raise
    return client

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
        object_name = f"{patient_id}/{study_uid}/{new_filename}"

        # 2. File Stream (De-identification & Storage)
        # First save to a temp de-identified file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dcm") as scrubbed_tmp:
            scrubbed_path = scrubbed_tmp.name
            
        parser.deidentify_dicom(scrubbed_path, new_patient_id=f"hash_{patient_id}")
        
        # Upload to MinIO
        minio_client = get_minio_client()
        minio_client.fput_object(
            MINIO_BUCKET, 
            object_name, 
            scrubbed_path,
            content_type="application/dicom"
        )
        saved_path = f"s3://{MINIO_BUCKET}/{object_name}"
        
        # Get presigned URL for frontend viewing
        presigned_url = minio_client.get_presigned_url(
            "GET",
            MINIO_BUCKET,
            object_name
        )
        
        # Cleanup scrubbed file
        if os.path.exists(scrubbed_path):
            os.remove(scrubbed_path)

        # 3. Store Raw Metadata in DB
        # Add the DICOM URL into metadata to allow frontend to generate a download link
        metadata["_dicom_url"] = presigned_url
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
                
        # To make the _dicom_url accessible to the frontend when it queries batch profiling data,
        # we persist it in value_as_string.
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
        
        # Update batch with a synthetic profiling data list containing the metadata so frontend can render the URL
        batch = db.query(SourceBatch).filter(SourceBatch.id == batch_id).first()
        if batch:
            batch.profiling_data = [json.dumps(metadata)]
            db.commit()

        # Complete batch
        persistence_svc.complete_batch(batch_id, total_rows=1, error_rows=0, status="completed")
        
    except Exception as e:
        error_msg = f"{str(e)}\n{traceback.format_exc()}"
        data_logger.error(f"DICOM processing failed: {error_msg}")
        # Mark batch as failed
        # Assuming you have a way to log this error in the database.
        # Since persistence_svc doesn't have an error log method in this snippet, we will update the batch status.
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
        data_logger.error(f"Upload DICOM failed: {traceback.format_exc()}")
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))
