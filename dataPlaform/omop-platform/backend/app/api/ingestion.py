import asyncio
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os
import shutil
import tempfile
import traceback
import uuid
import json
from app.core.logger import data_logger
from app.services.csv_parser import CSVParser
from app.services.nlp_mapper import NLPMapper
from app.services.raw_persistence import RawPersistenceService
from app.services.staging_transformer import StagingTransformer
from app.services.profiler import DataProfiler
from app.db.database import get_db, SessionLocal, Base, ensure_sqlite_schema_compatibility
from app.models.raw import SourceBatch, ErrorRecord
from app.schemas.ingestion import BatchResponse, ReplayRequest, ReplayResponse
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
            data_logger.error(f"ERROR: Batch {batch_id} not found in background task session!")
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
            
        # Generate Profiling Data
        data_logger.info(f"[{batch_id}] Generating Data Profiling...")
        profiling_data = DataProfiler.generate_profiling(tmp_path)
        
        # We need to save profiling_data to the batch
        batch = db.query(SourceBatch).filter(SourceBatch.id == batch_id).first()
        if batch:
            batch.profiling_data = profiling_data
            db.commit()
            
        # Auto NLP Semantic Mapping Configuration
        auto_mapping = NLPMapper.generate_mapping(parser.headers)
        data_logger.info(f"[{batch_id}] NLP Auto-Generated Mapping: {auto_mapping}")
        
        if total_valid > 0:
            import time
            start_time = time.time()
            data_logger.info(f"[{batch_id}] 开始执行深度 NLP 实体提取与 Staging 转换...")

            schema_changes = ensure_sqlite_schema_compatibility(db.get_bind(), Base.metadata)
            if schema_changes["columns_added"] or schema_changes["indexes_added"]:
                data_logger.info(f"[{batch_id}] SQLite schema auto-repaired: {schema_changes}")

            transformer = StagingTransformer(db)
            transformer.transform_batch_to_person(batch_id, auto_mapping)
            
            end_time = time.time()
            duration = end_time - start_time
            data_logger.info(f"[{batch_id}] ✅ NLP 提取与转换完成! 耗时: {duration:.2f} 秒 (平均 {duration/total_valid:.2f} 秒/条)")
            
        # Complete the batch only AFTER all NLP and staging extraction is done
        persistence_svc.complete_batch(batch_id, total_rows=total_valid, error_rows=total_errors)
        
    except Exception as e:
        data_logger.error(f"====== BACKGROUND TASK CRASHED ======\n{traceback.format_exc()}\n=====================================")
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


def process_replay_task(
    batch_id: str,
    dataset_name: str,
    window_start=None,
    window_end=None,
    source_batch_id: str = None,
    business_keys: List[str] = None,
):
    db = SessionLocal()
    try:
        data_logger.info(
            f"[{batch_id}] Starting replay orchestration "
            f"(dataset={dataset_name}, window_start={window_start}, window_end={window_end}, "
            f"source_batch_id={source_batch_id}, business_keys={business_keys or []})"
        )
        persistence_svc = RawPersistenceService(db)
        persistence_svc.complete_batch(batch_id, total_rows=0, error_rows=0)
    except Exception:
        data_logger.error(f"====== REPLAY TASK CRASHED ======\n{traceback.format_exc()}\n=================================")
        persistence_svc = RawPersistenceService(db)
        persistence_svc.complete_batch(batch_id, total_rows=0, error_rows=0, status="failed")
    finally:
        db.close()

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
                # Don't drop tables, just delete rows
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
                
        # Clear MinIO dicom-images bucket
        try:
            from app.api.dicom import get_minio_client, MINIO_BUCKET
            from minio.deleteobjects import DeleteObject
            minio_client = get_minio_client()
            if minio_client.bucket_exists(MINIO_BUCKET):
                objects_to_delete = minio_client.list_objects(MINIO_BUCKET, recursive=True)
                delete_object_list = [DeleteObject(obj.object_name) for obj in objects_to_delete]
                if delete_object_list:
                    errors = minio_client.remove_objects(MINIO_BUCKET, delete_object_list)
                    for error in errors:
                        data_logger.error(f"Error deleting object from MinIO: {error}")
        except Exception as e:
            data_logger.error(f"Failed to clear MinIO data: {e}")
                
        return {"message": "All local data and MinIO files cleared successfully"}
    except Exception as e:
        data_logger.error(f"Failed to clear data: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to clear data: {str(e)}")

@router.get("/batches")
def list_batches(db: Session = Depends(get_db)):
    from app.models.raw import Base as RawBase
    RawBase.metadata.create_all(bind=db.get_bind())
    
    batches = db.query(SourceBatch).order_by(SourceBatch.created_at.desc()).all()
    # Pydantic is having trouble with the JSON column if it contains raw string instead of dict
    # So we manually serialize it
    result = []
    
    import sqlite3
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'omop_platform.db')
    
    for b in batches:
        prof_data = None
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # SQLite string UUID vs direct ID
            cursor.execute('SELECT profiling_data FROM source_batch WHERE id = ?', (b.id,))
            row = cursor.fetchone()
            if row and row[0]:
                if isinstance(row[0], str):
                    prof_data = json.loads(row[0])
                else:
                    prof_data = row[0]
            conn.close()
        except Exception as e:
            data_logger.error(f"Failed to load raw JSON: {e}")
            
        item = {
            "id": str(b.id),
            "filename": str(b.filename),
            "batch_type": str(b.batch_type or "full"),
            "dataset_name": str(b.dataset_name or "ingestion"),
            "trigger_mode": str(b.trigger_mode or "auto"),
            "window_start": b.window_start.isoformat() if b.window_start else None,
            "window_end": b.window_end.isoformat() if b.window_end else None,
            "total_rows": int(b.total_rows or 0),
            "error_rows": int(b.error_rows or 0),
            "inserted_rows": int(b.inserted_rows or 0),
            "updated_rows": int(b.updated_rows or 0),
            "deleted_rows": int(b.deleted_rows or 0),
            "unchanged_rows": int(b.unchanged_rows or 0),
            "status": str(b.status),
            "profiling_data": prof_data,
            "created_at": b.created_at.isoformat() if b.created_at else None
        }
        result.append(item)
    
    from fastapi.responses import JSONResponse
    return JSONResponse(content=result)

@router.get("/batches/{batch_id}/errors")
def list_batch_errors(batch_id: str, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Fetch the specific error rows (with their raw data and reasons) for a batch"""
    from app.models.raw import Base as RawBase
    RawBase.metadata.create_all(bind=db.get_bind())
    
    errors = db.query(ErrorRecord).filter(ErrorRecord.batch_id == batch_id).order_by(ErrorRecord.line_number.asc()).offset(skip).limit(limit).all()
    total_count = db.query(ErrorRecord).filter(ErrorRecord.batch_id == batch_id).count()
    
    result = []
    for err in errors:
        result.append({
            "line_number": err.line_number,
            "error_message": err.error_message,
            "raw_data": err.raw_data
        })
        
    return {"total": total_count, "items": result}


@router.post("/replay", response_model=ReplayResponse)
def replay_incremental_batch(
    payload: ReplayRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    persistence = RawPersistenceService(db)
    batch = persistence.create_batch(
        filename="manual-replay.csv",
        batch_type="replay",
        dataset_name=payload.dataset_name,
        trigger_mode=payload.trigger_mode,
        window_start=payload.window_start,
        window_end=payload.window_end,
    )
    background_tasks.add_task(
        process_replay_task,
        batch.id,
        payload.dataset_name,
        payload.window_start,
        payload.window_end,
        payload.batch_id,
        payload.business_keys,
    )
    return ReplayResponse(
        batch_id=batch.id,
        batch_type=batch.batch_type,
        dataset_name=batch.dataset_name,
        trigger_mode=batch.trigger_mode,
        window_start=batch.window_start,
        window_end=batch.window_end,
        status=batch.status,
    )

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
            batch = RawPersistenceService(dedicated_db).create_batch(filename=file.filename)
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
        data_logger.error(f"Upload file failed: {traceback.format_exc()}")
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=500, detail=str(e))
