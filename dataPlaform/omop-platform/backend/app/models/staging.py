from sqlalchemy import Column, String, Integer, Date, ForeignKey, DateTime
from app.db.database import Base
from datetime import datetime

class StagingPerson(Base):
    """
    Staging table for OMOP PERSON domain.
    """
    __tablename__ = "stg_person"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Lineage tracking
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    
    # Core OMOP Person fields (mapped from Raw)
    person_source_value = Column(String, index=True)  # E.g., hospital patient ID
    gender_source_value = Column(String)              # Original gender string (男, M, 1, etc.)
    gender_concept_id = Column(Integer, default=0)    # Mapped to OMOP (e.g. 8507 for M)
    
    year_of_birth = Column(Integer)
    month_of_birth = Column(Integer)
    day_of_birth = Column(Integer)
    birth_datetime = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)

class StagingVisitOccurrence(Base):
    """
    Staging table for OMOP VISIT_OCCURRENCE domain.
    """
    __tablename__ = "stg_visit_occurrence"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    
    person_source_value = Column(String, index=True)
    visit_source_value = Column(String, index=True)   # E.g., admission number
    
    visit_start_date = Column(Date)
    visit_start_datetime = Column(DateTime)
    visit_end_date = Column(Date)
    visit_end_datetime = Column(DateTime)
    
    visit_type_concept_id = Column(Integer, default=0) # E.g., Inpatient vs Outpatient
    
    created_at = Column(DateTime, default=datetime.utcnow)

class StagingObservation(Base):
    """
    Staging table for OMOP OBSERVATION domain.
    Specifically used to store DICOM/Imaging metadata in this MVP.
    """
    __tablename__ = "stg_observation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    source_batch_id = Column(String, index=True)
    # Could be raw CSV record or a DICOM file metadata record
    raw_record_id = Column(String, index=True)
    
    person_source_value = Column(String, index=True)
    observation_source_value = Column(String)  # E.g. "CT Scan" or "StudyInstanceUID"
    observation_date = Column(Date)
    observation_datetime = Column(DateTime)
    
    # Metadata Specifics
    value_as_string = Column(String)           # Used to store JSON metadata string or file paths
    observation_concept_id = Column(Integer, default=0) # e.g. Concept ID for Imaging
    
class StagingMeasurement(Base):
    __tablename__ = "stg_measurement"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    
    measurement_source_value = Column(String)  # 检查项
    value_source_value = Column(String)        # 原始值
    unit_source_value = Column(String)         # 单位
    
    measurement_date = Column(Date)
    measurement_datetime = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class StagingConditionOccurrence(Base):
    __tablename__ = "stg_condition_occurrence"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    
    condition_source_value = Column(String)    # 诊断名称/原始数据
    condition_source_concept_id = Column(String) # ICD-10
    
    condition_start_date = Column(Date)
    condition_start_datetime = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class StagingDrugExposure(Base):
    __tablename__ = "stg_drug_exposure"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    
    drug_source_value = Column(String)         # 药名/原始数据
    dose_source_value = Column(String)         # 剂量
    form_source_value = Column(String)         # 剂型
    frequency_source_value = Column(String)    # 服药频率
    
    drug_exposure_start_date = Column(Date)
    drug_exposure_start_datetime = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
