from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os
import shutil
import tempfile
import traceback
from app.services.csv_parser import CSVParser
from app.services.raw_persistence import RawPersistenceService
from app.services.staging_transformer import StagingTransformer
from app.db.database import get_db, SessionLocal
from app.models.raw import SourceBatch
from app.schemas.ingestion import BatchResponse
from typing import List

router = APIRouter()

def process_csv_task(tmp_path: str, filename: str, batch_id: str):
    """Background task to process the CSV file."""
    db = SessionLocal()
    try:
        parser = CSVParser(tmp_path)
        persistence_svc = RawPersistenceService(db)
        
        total_chunks = 0
        total_valid = 0
        total_errors = 0
        
        for chunk in parser.parse_chunks(chunk_size=5000):
            total_chunks += 1
            total_valid += len(chunk["valid_rows"])
            total_errors += len(chunk["error_rows"])
            
            persistence_svc.save_chunk(
                batch_id=batch_id, 
                valid_rows=chunk["valid_rows"], 
                error_rows=chunk["error_rows"]
            )
            
        persistence_svc.complete_batch(batch_id, total_rows=total_valid, error_rows=total_errors)
        
        default_mapping = {
            "person_source_value": "id",
            "gender_source_value": "gender",
            "birth_datetime": "age"
        }
        
        if total_valid > 0:
            transformer = StagingTransformer(db)
            transformer.transform_batch_to_person(batch_id, default_mapping)
            
    except Exception as e:
        traceback.print_exc()
        # Mark batch as failed
        persistence_svc = RawPersistenceService(db)
        persistence_svc.complete_batch(batch_id, total_rows=0, error_rows=0, status="failed")
    finally:
        db.close()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

@router.get("/batches", response_model=List[BatchResponse])
def list_batches(db: Session = Depends(get_db)):
    from app.models.raw import Base as RawBase
    RawBase.metadata.create_all(bind=db.get_bind())
    
    batches = db.query(SourceBatch).order_by(SourceBatch.created_at.desc()).all()
    return batches

@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
        
    try:
        suffix = os.path.splitext(file.filename)[1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name
            
        # Ensure tables exist
        from app.models.raw import Base as RawBase
        from app.db.database import engine
        RawBase.metadata.create_all(bind=engine)

        persistence_svc = RawPersistenceService(db)
        batch = persistence_svc.create_batch(file.filename)
        
        # Dispatch background task
        background_tasks.add_task(process_csv_task, tmp_path, file.filename, batch.id)
        
        return {
            "batch_id": batch.id,
            "filename": file.filename,
            "message": "File uploaded successfully. Processing started in the background."
        }
    except Exception as e:
        traceback.print_exc()
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))
