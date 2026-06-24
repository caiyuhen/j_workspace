import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os
import shutil
import tempfile
import traceback
from app.services.csv_parser import CSVParser
from app.services.nlp_mapper import NLPMapper
from app.services.raw_persistence import RawPersistenceService
from app.services.staging_transformer import StagingTransformer
from app.db.database import get_db, SessionLocal
from app.models.raw import SourceBatch
from app.schemas.ingestion import BatchResponse
from typing import List

router = APIRouter()

def process_csv_task(tmp_path: str, filename: str, batch_id: str):
    """Background task to process the CSV file."""
    # We must create a new event loop for this thread because SQLAlchemy or AnyIO might need it
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    db = SessionLocal()
    try:
        parser = CSVParser(tmp_path)
        persistence_svc = RawPersistenceService(db)
        
        total_chunks = 0
        total_valid = 0
        total_errors = 0
        
        # We need to make sure the batch exists in THIS session before we can link foreign keys to it
        # Since it was created in a separate session, we just verify it's there
        batch_exists = db.query(SourceBatch).filter(SourceBatch.id == batch_id).first()
        if not batch_exists:
            print(f"ERROR: Batch {batch_id} not found in background task session!")
            # Recreate it just in case!
            batch = SourceBatch(id=batch_id, filename=filename, status="processing")
            db.add(batch)
            db.commit()
            
        # Optimize parsing chunk size for SQLite bulk insert performance
        for chunk in parser.parse_chunks(chunk_size=10000):
            total_chunks += 1
            total_valid += len(chunk["valid_rows"])
            total_errors += len(chunk["error_rows"])
            
            persistence_svc.save_chunk(
                batch_id=batch_id, 
                valid_rows=chunk["valid_rows"], 
                error_rows=chunk["error_rows"]
            )
            # Update batch progress periodically
            if total_chunks % 10 == 0:
                persistence_svc.update_batch_progress(batch_id, total_valid, total_errors)
            
        persistence_svc.complete_batch(batch_id, total_rows=total_valid, error_rows=total_errors)
        
        # Auto NLP Semantic Mapping Configuration
        auto_mapping = NLPMapper.generate_mapping(parser.headers)
        print(f"[{batch_id}] NLP Auto-Generated Mapping: {auto_mapping}")
        
        if total_valid > 0:
            transformer = StagingTransformer(db)
            transformer.transform_batch_to_person(batch_id, auto_mapping)
            
    except Exception as e:
        print("====== BACKGROUND TASK CRASHED ======")
        traceback.print_exc()
        print("=====================================")
        # Mark batch as failed
        persistence_svc = RawPersistenceService(db)
        persistence_svc.complete_batch(batch_id, total_rows=0, error_rows=0, status="failed")
    finally:
        db.close()
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        try:
            loop.close()
        except:
            pass

@router.post("/clear")
def clear_data(db: Session = Depends(get_db)):
    """Clear all local SQLite data including batches and staging tables"""
    from sqlalchemy import MetaData
    from sqlalchemy.sql import text
    try:
        engine = db.get_bind()
        meta = MetaData()
        meta.reflect(bind=engine)
        
        with engine.connect() as conn:
            conn.execute(text("PRAGMA foreign_keys = OFF;"))
            for table in reversed(meta.sorted_tables):
                conn.execute(table.delete())
            conn.execute(text("PRAGMA foreign_keys = ON;"))
            conn.commit()
            
        # VERY IMPORTANT: Commit the current session to ensure the current transaction sees the cleared DB
        db.commit()
            
        # Clear pipeline errors CSV if it exists
        error_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "pipeline_errors.csv")
        if os.path.exists(error_csv):
            try:
                with open(error_csv, 'w') as f:
                    f.write("")
            except:
                pass
                
        return {"message": "All local data cleared successfully"}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

@router.get("/batches", response_model=List[BatchResponse])
def list_batches(db: Session = Depends(get_db)):
    from app.models.raw import Base as RawBase
    RawBase.metadata.create_all(bind=db.get_bind())
    
    batches = db.query(SourceBatch).order_by(SourceBatch.created_at.desc()).all()
    return batches

@router.post("/upload")
async def upload_file(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
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

        # Create a dedicated independent session just for creating the batch record
        # This completely avoids FastAPI's Depends(get_db) auto-rollback issues
        dedicated_db = SessionLocal()
        try:
            batch = SourceBatch(filename=file.filename, status="processing")
            dedicated_db.add(batch)
            dedicated_db.commit()
            dedicated_db.refresh(batch)
            batch_id = batch.id
        finally:
            dedicated_db.close()
        
        # Dispatch background task
        background_tasks.add_task(process_csv_task, tmp_path, file.filename, batch_id)
        
        return {
            "batch_id": batch_id,
            "filename": file.filename,
            "message": "File uploaded successfully. Processing started in the background."
        }
    except Exception as e:
        traceback.print_exc()
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))
