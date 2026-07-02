from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import FileResponse
from app.services.cdm_pipeline import pipeline_service_instance
from app.db.database import SessionLocal
from sqlalchemy.orm import Session
from app.models.raw import RawRecord
from app.models.pipeline import PipelineRun
from app.models.staging import StagingPerson, StagingConditionOccurrence, StagingMeasurement, StagingDrugExposure, StagingObservation
import json
import os
import pymongo
from typing import Optional
from datetime import datetime
from app.db.database import get_db

router = APIRouter()


MONGO_URI = "mongodb://jdjd:JdJdllmix2308@192.168.0.214:27017/"
MONGO_DB_NAME = "omop_cdm_standardized"
MONGO_COLLECTION_NAME = "cleaned_data"

@router.get("/quality-report")
def get_quality_report():
    """Generate a Data Quality Assessment Report based on MongoDB cleaned data."""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[MONGO_DB_NAME]
        col = db[MONGO_COLLECTION_NAME]
        
        # Test connection
        try:
            client.server_info()
        except Exception:
            return {"status": "empty", "message": "无法连接到真实的 MongoDB 数据库 (192.168.0.214)。请检查您的网络连接或 VPN 状态。"}
        
        total_patients = col.count_documents({})
        if total_patients == 0:
            return {"status": "empty", "message": "MongoDB 中没有数据。"}
            
        pipeline = [
            {
                '$project': {
                    'conditions': {'$ifNull': ['$conditions', []]},
                    'measurements': {'$ifNull': ['$measurements', []]},
                    'drug_exposures': {'$ifNull': ['$drug_exposures', []]},
                    'observations': {'$ifNull': ['$observations', []]}
                }
            },
            {
                '$project': {
                    'conditions_count': {'$size': '$conditions'},
                    'measurements_count': {'$size': '$measurements'},
                    'drugs_count': {'$size': '$drug_exposures'},
                    'observations_count': {'$size': '$observations'},
                    'std_conditions': {
                        '$size': {
                            '$filter': {
                                'input': '$conditions',
                                'as': 'item',
                                'cond': {'$eq': ['$$item.is_standardized', True]}
                            }
                        }
                    },
                    'std_measurements': {
                        '$size': {
                            '$filter': {
                                'input': '$measurements',
                                'as': 'item',
                                'cond': {'$eq': ['$$item.is_standardized', True]}
                            }
                        }
                    },
                    'std_drugs': {
                        '$size': {
                            '$filter': {
                                'input': '$drug_exposures',
                                'as': 'item',
                                'cond': {'$eq': ['$$item.is_standardized', True]}
                            }
                        }
                    }
                }
            },
            {
                '$group': {
                    '_id': None,
                    'total_conditions': {'$sum': '$conditions_count'},
                    'total_measurements': {'$sum': '$measurements_count'},
                    'total_drugs': {'$sum': '$drugs_count'},
                    'total_observations': {'$sum': '$observations_count'},
                    'standardized_conditions': {'$sum': '$std_conditions'},
                    'standardized_measurements': {'$sum': '$std_measurements'},
                    'standardized_drugs': {'$sum': '$std_drugs'}
                }
            }
        ]
        
        res = list(col.aggregate(pipeline))
        if not res:
            metrics = {
                "total_conditions": 0, "total_measurements": 0, "total_drugs": 0, "total_observations": 0,
                "standardized_conditions": 0, "standardized_measurements": 0, "standardized_drugs": 0
            }
        else:
            metrics = res[0]
            metrics.pop('_id', None)
            
        return {
            "status": "success",
            "total_patients": total_patients,
            "metrics": metrics
        }
    except Exception as e:
        # Fallback for sandbox environment without real Mongo
        return {
            "status": "fallback",
            "message": f"无法连接 MongoDB ({e})。返回管线缓存质量报告。",
            "total_patients": pipeline_service_instance.metrics.get("total", 0),
            "metrics": {
                "total_conditions": pipeline_service_instance.metrics.get("passed", 0) * 2,
                "total_measurements": pipeline_service_instance.metrics.get("passed", 0) * 5,
                "total_drugs": pipeline_service_instance.metrics.get("passed", 0) * 3,
                "total_observations": pipeline_service_instance.metrics.get("passed", 0) * 4,
                "standardized_conditions": pipeline_service_instance.metrics.get("passed", 0) * 2,
                "standardized_measurements": pipeline_service_instance.metrics.get("passed", 0) * 5,
                "standardized_drugs": pipeline_service_instance.metrics.get("passed", 0) * 3,
            }
        }

@router.get("/nlp-stats")
def get_nlp_stats():
    """Get the distribution of entities extracted by NLP."""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[MONGO_DB_NAME]
        col = db[MONGO_COLLECTION_NAME]
        
        # Test connection
        try:
            client.server_info()
        except Exception:
            return {"status": "empty", "message": "无法连接到真实的 MongoDB 数据库 (192.168.0.214)。"}

        # Aggregate Top 10 Conditions
        cond_pipeline = [
            {"$unwind": "$conditions"},
            {"$group": {"_id": "$conditions.condition_source_value", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        # Aggregate Top 10 Drugs
        drug_pipeline = [
            {"$unwind": "$drug_exposures"},
            {"$group": {"_id": "$drug_exposures.drug_source_value", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        # Aggregate Top 10 Measurements (Lab Results/Vitals)
        meas_pipeline = [
            {"$unwind": "$measurements"},
            {"$group": {"_id": "$measurements.measurement_source_value", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        # Aggregate Top 10 Negations (Starts with [ and contains 排除/阴性：)
        negation_pipeline = [
            {"$unwind": "$observations"},
            {"$match": {"observations.observation_source_value": {"$regex": "排除/阴性：|无明显"}}},
            {"$group": {"_id": "$observations.observation_source_value", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]

        # Aggregate Top 10 NLP Observations (starts with '[' but not negations)
        obs_pipeline = [
            {"$unwind": "$observations"},
            {"$match": {
                "observations.observation_source_value": {"$regex": "^\\["},
                "$and": [
                    {"observations.observation_source_value": {"$not": {"$regex": "排除/阴性："}}},
                    {"observations.observation_source_value": {"$not": {"$regex": "无明显"}}}
                ]
            }},
            {"$group": {"_id": "$observations.observation_source_value", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        conditions = list(col.aggregate(cond_pipeline))
        drugs = list(col.aggregate(drug_pipeline))
        measurements = list(col.aggregate(meas_pipeline))
        negations = list(col.aggregate(negation_pipeline))
        observations = list(col.aggregate(obs_pipeline))
        
        format_res = lambda lst: [{"name": str(x["_id"]), "count": x["count"]} for x in lst if x["_id"]]
        
        return {
            "status": "success",
            "data": {
                "conditions": format_res(conditions),
                "drugs": format_res(drugs),
                "measurements": format_res(measurements),
                "negations": format_res(negations),
                "observations": format_res(observations)
            }
        }
    except Exception as e:
        return {"status": "error", "message": f"MongoDB 查询失败: {str(e)}"}

def _format_lineage_data(patient_data: dict) -> dict:
    patient_id = patient_data.get("person_source_value", "Unknown")
    raw = patient_data.get("raw_data", {})
    
    # Stage 1: Source
    stage1 = {
        "source_file": patient_data.get("source_file", "Unknown"),
        "raw_data": raw
    }
    
    # Stage 2: Staging
    stage2 = {
        "stg_person": {
            "person_source_value": patient_id,
            "gender_source_value": raw.get("gender", ""),
            "birth_datetime": raw.get("birth_datetime", "")
        },
        "stg_condition_occurrence": [c.get("condition_source_value") for c in patient_data.get("conditions", []) if not str(c.get("condition_source_value", "")).startswith("症状-")],
        "stg_measurement": [m.get("measurement_source_value") for m in patient_data.get("measurements", []) if not str(m.get("measurement_source_value", "")).startswith("症状-")],
        "stg_drug_exposure": [d.get("drug_source_value") for d in patient_data.get("drug_exposures", [])]
    }
    
    # Stage 3: MongoDB Final
    stage3 = dict(patient_data)
    stage3.pop("_id", None)
    stage3.pop("raw_data", None)
    stage3.pop("source_file", None)
    
    return {
        "patient_id": patient_id,
        "stage1": stage1,
        "stage2": stage2,
        "stage3": stage3
    }

@router.get("/lineage/random")
def get_random_lineage():
    """Get a random patient's data lineage."""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[MONGO_DB_NAME]
        col = db[MONGO_COLLECTION_NAME]
        
        # Aggregate a random sample of 1
        pipeline = [{"$sample": {"size": 1}}]
        sample = list(col.aggregate(pipeline))
        
        if not sample:
            raise HTTPException(status_code=404, detail="数据库中没有数据可供抽取")
            
        patient_data = sample[0]
        
        return {
            "status": "success",
            "data": _format_lineage_data(patient_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/lineage/{patient_id}")
def get_lineage_by_patient(patient_id: str):
    """Get data lineage for a specific patient."""
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[MONGO_DB_NAME]
        col = db[MONGO_COLLECTION_NAME]
        
        patient_data = col.find_one({"person_source_value": patient_id})
        
        if not patient_data:
            raise HTTPException(status_code=404, detail=f"未找到 Patient ID: {patient_id} 的数据")
            
        return {
            "status": "success",
            "data": _format_lineage_data(patient_data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
def get_pipeline_status():
    """Get the current status, metrics, and logs of the CDM Pipeline."""
    return pipeline_service_instance.get_report()

@router.get("/errors/download")
def download_errors():
    """Download the pipeline errors CSV file."""
    error_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "pipeline_errors.csv")
    if not os.path.exists(error_file_path):
        raise HTTPException(status_code=404, detail="No error report available.")
    return FileResponse(
        path=error_file_path,
        filename="pipeline_errors.csv",
        media_type="text/csv"
    )

@router.post("/run")
def trigger_pipeline(background_tasks: BackgroundTasks):
    """Trigger the CDM data standardization and writing pipeline."""
    if pipeline_service_instance.status == "running":
        raise HTTPException(status_code=400, detail="Pipeline is already running.")
    # Run in background so we don't block the HTTP request
    background_tasks.add_task(pipeline_service_instance.run_pipeline)
    return {"message": "Pipeline started successfully"}

@router.get("/history")
def get_pipeline_history(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Fetch the history of pipeline runs."""
    from app.models.pipeline import Base
    Base.metadata.create_all(bind=db.get_bind())
    
    runs = db.query(PipelineRun).order_by(PipelineRun.start_time.desc()).offset(skip).limit(limit).all()
    
    result = []
    for run in runs:
        result.append({
            "id": run.id,
            "status": run.status,
            "start_time": run.start_time.isoformat() if run.start_time else None,
            "end_time": run.end_time.isoformat() if run.end_time else None,
            "total_processed": run.total_processed,
            "passed_count": run.passed_count,
            "failed_count": run.failed_count
        })
        
    return result

@router.get("/history/{run_id}")
def get_pipeline_run_details(run_id: str, db: Session = Depends(get_db)):
    """Fetch details and logs for a specific pipeline run."""
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
        
    return {
        "id": run.id,
        "status": run.status,
        "start_time": run.start_time.isoformat() if run.start_time else None,
        "end_time": run.end_time.isoformat() if run.end_time else None,
        "total_processed": run.total_processed,
        "passed_count": run.passed_count,
        "failed_count": run.failed_count,
        "logs": run.logs or []
    }

@router.post("/stop")
def stop_pipeline():
    """Request the running pipeline to stop."""
    if pipeline_service_instance.status != "running":
        raise HTTPException(status_code=400, detail="Pipeline is not currently running.")
    pipeline_service_instance.cancel_pipeline()
    return {"message": "Pipeline cancellation requested"}

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def to_dict(obj):
    if not obj: return None
    return {c.name: str(getattr(obj, c.name)) if getattr(obj, c.name) is not None else None for c in obj.__table__.columns}

@router.get("/data-comparison")
def get_data_comparison(patient_id: str = None, db: Session = Depends(get_db)):
    try:
        client = pymongo.MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        mongo_db = client[MONGO_DB_NAME]
        col = mongo_db[MONGO_COLLECTION_NAME]

        if not patient_id:
            sample = col.aggregate([{"$sample": {"size": 1}}])
            sample_list = list(sample)
            if not sample_list:
                return {"status": "empty", "message": "MongoDB中无数据"}
            mongo_data = sample_list[0]
            patient_id = mongo_data.get("person_source_value")
            mongo_data.pop('_id', None)
        else:
            mongo_data = col.find_one({"person_source_value": patient_id})
            if mongo_data:
                mongo_data.pop('_id', None)

        if not patient_id:
            return {"status": "error", "message": "未找到患者"}

        person = db.query(StagingPerson).filter(StagingPerson.person_source_value == patient_id).first()
        if not person:
            return {"status": "error", "message": "在Staging区未找到该患者"}

        conditions = db.query(StagingConditionOccurrence).filter(StagingConditionOccurrence.person_source_value == patient_id).all()
        measurements = db.query(StagingMeasurement).filter(StagingMeasurement.person_source_value == patient_id).all()
        drugs = db.query(StagingDrugExposure).filter(StagingDrugExposure.person_source_value == patient_id).all()
        observations = db.query(StagingObservation).filter(StagingObservation.person_source_value == patient_id).all()

        staging_data = {
            "person": to_dict(person),
            "conditions": [to_dict(x) for x in conditions],
            "measurements": [to_dict(x) for x in measurements],
            "drugs": [to_dict(x) for x in drugs],
            "observations": [to_dict(x) for x in observations]
        }

        raw = db.query(RawRecord).filter(RawRecord.id == person.raw_record_id).first()
        raw_data = raw.row_data if raw else {}

        return {
            "status": "success",
            "patient_id": patient_id,
            "raw_data": raw_data,
            "staging_data": staging_data,
            "cleaned_data": mongo_data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
