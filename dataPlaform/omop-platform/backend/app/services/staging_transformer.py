import json
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Dict, Any
from datetime import datetime
from app.core.logger import data_logger
from app.models.raw import RawRecord
from app.models.staging import StagingPerson, StagingVisitOccurrence, StagingObservation, StagingMeasurement, StagingConditionOccurrence, StagingDrugExposure
from app.services.cleaning_rules import CleaningRulesEngine
from app.services.transformers_ner import TransformersNERMapper

class StagingTransformer:
    """
    Transforms RawRecords into OMOP Staging tables based on mapping configurations.
    """
    def __init__(self, db: Session):
        self.db = db
        self.cleaner = CleaningRulesEngine()
        self.ner_mapper = TransformersNERMapper()

    def transform_batch_to_person(self, batch_id: str, mapping_config: Dict[str, str]):
        """
        Extracts records from RawZone, applies mapping/cleaning, and inserts to StagingPerson.
        Uses batching to significantly improve performance on large datasets.
        """
        # Process in batches of 10,000 to prevent memory exhaustion
        BATCH_SIZE = 10000
        offset = 0
        
        while True:
            raw_records = self.db.query(RawRecord).filter(RawRecord.batch_id == batch_id).limit(BATCH_SIZE).offset(offset).all()
            if not raw_records:
                break
                
            staging_objects = []
            import json
            # 6.4 Collect NLP tasks for batch processing later
            nlp_tasks = []
            
            for raw in raw_records:
                # 1. Base clean (empty strings to None)
                raw_dict = raw.row_data if isinstance(raw.row_data, dict) else json.loads(raw.row_data)
                cleaned_row = self.cleaner.clean_empty_values(raw_dict)
                
                # 2. Field Mapping
                mapped_data = {}
                for target_field, source_field in mapping_config.items():
                    mapped_data[target_field] = cleaned_row.get(source_field)
                
                # 3. Apply specific cleaning rules based on target domains
                # Date Parsing
                date_fields = [k for k in mapped_data.keys() if "date" in k.lower() or "datetime" in k.lower()]
                mapped_data = self.cleaner.parse_dates(mapped_data, date_fields)
                
                # Dictionary Mapping (e.g. mapping department/care_site to standard concepts)
                if "care_site_source_value" in mapped_data:
                    mapped_data["care_site_source_value"] = self.cleaner.map_dictionary_value(
                        "department", 
                        mapped_data["care_site_source_value"]
                    )
                
                # 4. Construct StagingPerson object
                person = StagingPerson(
                    source_batch_id=batch_id,
                    raw_record_id=raw.id,
                    person_source_value=mapped_data.get("person_source_value")
                )
                
                # Handle Gender Mapping
                gender_val = mapped_data.get("gender_source_value")
                person.gender_source_value = gender_val
                norm_gender = self.cleaner.normalize_gender(gender_val)
                if norm_gender == "M":
                    person.gender_concept_id = 8507
                elif norm_gender == "F":
                    person.gender_concept_id = 8532
                else:
                    person.gender_concept_id = 0 # Unknown
                    
                # Handle Dates mapping to Year/Month/Day
                birth_dt_str = mapped_data.get("birth_datetime")
                if birth_dt_str:
                    try:
                        dt = datetime.strptime(birth_dt_str, "%Y-%m-%d")
                        person.birth_datetime = dt
                        person.year_of_birth = dt.year
                        person.month_of_birth = dt.month
                        person.day_of_birth = dt.day
                    except ValueError:
                        pass
                
                staging_objects.append(person)

                # 5. Construct StagingVisitOccurrence object
                visit_val = mapped_data.get("visit_source_value")
                visit = None
                if visit_val or mapped_data.get("visit_start_datetime"):
                    visit = StagingVisitOccurrence(
                        source_batch_id=batch_id,
                        raw_record_id=raw.id,
                        person_source_value=person.person_source_value,
                        visit_source_value=visit_val
                    )
                    
                    visit_start_dt_str = mapped_data.get("visit_start_datetime")
                    if visit_start_dt_str:
                        try:
                            dt = datetime.strptime(visit_start_dt_str, "%Y-%m-%d")
                            visit.visit_start_datetime = dt
                            visit.visit_start_date = dt.date()
                        except ValueError:
                            pass
                            
                    visit_end_dt_str = mapped_data.get("visit_end_datetime")
                    if visit_end_dt_str:
                        try:
                            dt = datetime.strptime(visit_end_dt_str, "%Y-%m-%d")
                            visit.visit_end_datetime = dt
                            visit.visit_end_date = dt.date()
                        except ValueError:
                            pass
                    
                    staging_objects.append(visit)

                # 6. Extract into different domain models
                
                # 6.1 Diagnosis -> StagingConditionOccurrence
                diag_val = cleaned_row.get("icd_diagnosis")
                if diag_val:
                    # Example: "I20.9 心绞痛"
                    parts = diag_val.split(" ", 1)
                    code = parts[0] if len(parts) > 0 else ""
                    name = parts[1] if len(parts) > 1 else diag_val
                    
                    cond = StagingConditionOccurrence(
                        source_batch_id=batch_id,
                        raw_record_id=raw.id,
                        person_source_value=person.person_source_value,
                        condition_source_value=name,
                        condition_source_concept_id=code
                    )
                    if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                        cond.condition_start_datetime = visit.visit_start_datetime
                        cond.condition_start_date = visit.visit_start_date
                    staging_objects.append(cond)

                # 6.2 Medication -> StagingDrugExposure
                rx_val = cleaned_row.get("electronic_prescription")
                if rx_val:
                    # Example: "阿司匹林肠溶片 100mg qd"
                    parts = rx_val.split(" ")
                    name = parts[0] if len(parts) > 0 else rx_val
                    dose = parts[1] if len(parts) > 1 else ""
                    freq = parts[2] if len(parts) > 2 else ""
                    
                    # 简单提取剂型 (如果包含片/胶囊/颗粒等)
                    form = ""
                    for f in ["片", "胶囊", "颗粒", "注射液", "口服液"]:
                        if f in name:
                            form = f
                            break
                            
                    drug = StagingDrugExposure(
                        source_batch_id=batch_id,
                        raw_record_id=raw.id,
                        person_source_value=person.person_source_value,
                        drug_source_value=name,
                        dose_source_value=dose,
                        form_source_value=form,
                        frequency_source_value=freq
                    )
                    if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                        drug.drug_exposure_start_datetime = visit.visit_start_datetime
                        drug.drug_exposure_start_date = visit.visit_start_date
                    staging_objects.append(drug)

                # 6.3 Lab Results -> NLP processing (handled together with other notes)
                # Removed manual split logic to let TransformersNERMapper handle it cleanly.

                # 6.4 NLP/Notes -> Collect for Batch Processing
                nlp_keys = ["lab_results", "chief_complaint", "history_of_present_illness", "imaging_reports", "admission_record", "daily_course_record", "discharge_summary", "treatment_plan"]
                for k in nlp_keys:
                    val = cleaned_row.get(k)
                    if val:
                        nlp_tasks.append({
                            "person": person,
                            "visit": visit,
                            "batch_id": batch_id,
                            "raw_id": raw.id,
                            "key": k,
                            "text": val
                        })
            
            # 6.5 Execute Batch NLP Processing
            if nlp_tasks:
                import time
                t0 = time.time()
                texts_to_process = [task["text"] for task in nlp_tasks]
                
                # Batch size 16 is usually a sweet spot for RTX/GTX GPUs
                batch_results = self.ner_mapper.extract_entities_batch(texts_to_process, batch_size=16)
                
                for task, extracted_entities in zip(nlp_tasks, batch_results):
                    person = task["person"]
                    visit = task["visit"]
                    b_id = task["batch_id"]
                    r_id = task["raw_id"]
                    k = task["key"]
                    
                    # Process Conditions
                    for cond_val in extracted_entities.get("conditions", []):
                        cond = StagingConditionOccurrence(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person.person_source_value,
                            condition_source_value=cond_val
                        )
                        if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                            cond.condition_start_datetime = visit.visit_start_datetime
                            cond.condition_start_date = visit.visit_start_date
                        staging_objects.append(cond)
                        
                    # Process Medications
                    for med_val in extracted_entities.get("medications", []):
                        import re
                        match = re.search(r'药名：(.*?)\s+剂型：(.*?)\s+给药方式：(.*)', med_val)
                        if match:
                            d_name = match.group(1).strip()
                            d_form = match.group(2).strip()
                            d_route = match.group(3).strip()
                            drug = StagingDrugExposure(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                person_source_value=person.person_source_value,
                                drug_source_value=d_name,
                                form_source_value=d_form,
                                route_source_value=d_route
                            )
                        else:
                            drug = StagingDrugExposure(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                person_source_value=person.person_source_value,
                                drug_source_value=med_val
                            )
                        if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                            drug.drug_exposure_start_datetime = visit.visit_start_datetime
                            drug.drug_exposure_start_date = visit.visit_start_date
                        staging_objects.append(drug)
                        
                    # Process Measurements
                    for meas_val in extracted_entities.get("measurements", []):
                        import re
                        match = re.search(r'检查项：(.*?)\s+值:([^\s]+)(?:\s+单位:(.*))?', meas_val)
                        if match:
                            m_name = match.group(1).strip()
                            m_val = match.group(2).strip()
                            m_unit = match.group(3).strip() if match.group(3) else ""
                            meas = StagingMeasurement(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                person_source_value=person.person_source_value,
                                measurement_source_value=m_name,
                                value_source_value=m_val,
                                unit_source_value=m_unit
                            )
                            if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                                meas.measurement_datetime = visit.visit_start_datetime
                                meas.measurement_date = visit.visit_start_date
                            staging_objects.append(meas)
                            
                    # Process Symptoms with values
                    for sym_val in extracted_entities.get("symptoms_with_values", []):
                        import re
                        match = re.search(r'症状：(.*?)\s+值:([^\s]+)(?:\s+单位:(.*))?', sym_val)
                        if match:
                            s_name = match.group(1).strip()
                            s_val = match.group(2).strip()
                            s_unit = match.group(3).strip() if match.group(3) else ""
                            # 带有数值的症状（如体温）在 OMOP 中本质上属于 Measurement
                            meas = StagingMeasurement(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                person_source_value=person.person_source_value,
                                measurement_source_value=f"症状-{s_name}",
                                value_source_value=s_val,
                                unit_source_value=s_unit
                            )
                            if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                                meas.measurement_datetime = visit.visit_start_datetime
                                meas.measurement_date = visit.visit_start_date
                            staging_objects.append(meas)
                            
                    # Process Times
                    for time_val in extracted_entities.get("times", []):
                        obs = StagingObservation(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person.person_source_value,
                            observation_source_value=f"[{k}] 时间：{time_val}",
                            value_as_string=time_val
                        )
                        if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                            obs.observation_datetime = visit.visit_start_datetime
                            obs.observation_date = visit.visit_start_date
                        staging_objects.append(obs)

                    # Process generic observations and fallback
                    for obs_val in extracted_entities.get("observations", []):
                        obs = StagingObservation(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person.person_source_value,
                            observation_source_value=f"[{k}] {obs_val}",
                            value_as_string=obs_val
                        )
                        if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                            obs.observation_datetime = visit.visit_start_datetime
                            obs.observation_date = visit.visit_start_date
                        staging_objects.append(obs)

                    # Process negations
                    for val in extracted_entities.get("negations", []):
                        obs = StagingObservation(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person.person_source_value,
                            observation_source_value=f"[{k}] {val}",
                            value_as_string=val
                        )
                        if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                            obs.observation_datetime = visit.visit_start_datetime
                            obs.observation_date = visit.visit_start_date
                        staging_objects.append(obs)
                
                data_logger.info(f"[{batch_id}] 批量 NLP 推理完成 ({len(nlp_tasks)} 条文本片段), 耗时 {time.time() - t0:.2f}s")
            
            # 7. Bulk insert to staging
            if staging_objects:
                self.db.bulk_save_objects(staging_objects)
                self.db.commit()
                
            offset += BATCH_SIZE
