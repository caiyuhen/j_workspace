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
    note_id = Column(Integer, index=True)
    
    # Metadata Specifics
    value_as_string = Column(String)           # Used to store JSON metadata string or file paths
    observation_concept_id = Column(Integer, default=0) # e.g. Concept ID for Imaging
    file_storage_path = Column(String)         # Physical MinIO/S3 storage path for DICOM
    
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
    note_id = Column(Integer, index=True)
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
    note_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class StagingDrugExposure(Base):
    __tablename__ = "stg_drug_exposure"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    drug_source_value = Column(String)
    form_source_value = Column(String)
    route_source_value = Column(String)
    dose_source_value = Column(String)         # 剂量
    frequency_source_value = Column(String)    # 服药频率
    drug_exposure_start_date = Column(Date)
    drug_exposure_start_datetime = Column(DateTime)
    note_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StagingProcedureOccurrence(Base):
    __tablename__ = "stg_procedure_occurrence"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    procedure_source_value = Column(String)
    procedure_source_concept_id = Column(String, default="0")
    procedure_date = Column(Date)
    procedure_datetime = Column(DateTime)
    note_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StagingNote(Base):
    __tablename__ = "stg_note"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    note_source_value = Column(String, index=True)
    note_text = Column(String)
    note_date = Column(Date)
    note_datetime = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class StagingNoteNlp(Base):
    __tablename__ = "stg_note_nlp"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    note_id = Column(Integer, index=True)
    section_source_value = Column(String, index=True)
    nlp_domain = Column(String, index=True)
    lexical_variant = Column(String)
    normalized_value = Column(String)
    term_exists = Column(String, default="Y")
    source_layer = Column(String, default="unknown")
    negated = Column(String, default="N")
    offset_start = Column(Integer, nullable=True)
    offset_end = Column(Integer, nullable=True)
    note_nlp_concept_id = Column(String, default="0")
    created_at = Column(DateTime, default=datetime.utcnow)


class StagingSpecimen(Base):
    __tablename__ = "stg_specimen"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    specimen_source_value = Column(String)
    specimen_source_concept_id = Column(String, default="0")
    specimen_date = Column(Date)
    specimen_datetime = Column(DateTime)
    note_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StagingDeviceExposure(Base):
    __tablename__ = "stg_device_exposure"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    device_source_value = Column(String)
    device_source_concept_id = Column(String, default="0")
    device_exposure_start_date = Column(Date)
    device_exposure_start_datetime = Column(DateTime)
    note_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StagingDeath(Base):
    __tablename__ = "stg_death"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    person_source_value = Column(String, index=True)
    death_date = Column(Date)
    death_datetime = Column(DateTime)
    death_type_source_value = Column(String)
    cause_source_value = Column(String)
    note_id = Column(Integer, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class StagingProvider(Base):
    __tablename__ = "stg_provider"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    provider_source_value = Column(String, index=True)
    provider_name = Column(String)
    specialty_source_value = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)


class StagingCareSite(Base):
    __tablename__ = "stg_care_site"
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_batch_id = Column(String, index=True)
    raw_record_id = Column(String, ForeignKey("raw_record.id"), index=True)
    care_site_source_value = Column(String, index=True)
    place_of_service_source_value = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
