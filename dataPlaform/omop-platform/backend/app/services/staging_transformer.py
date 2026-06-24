from sqlalchemy.orm import Session
from typing import Dict, Any
from app.models.raw import RawRecord
from app.models.staging import StagingPerson, StagingVisitOccurrence, StagingObservation, StagingMeasurement, StagingConditionOccurrence, StagingDrugExposure
from app.services.cleaning_rules import CleaningRulesEngine
from datetime import datetime

class StagingTransformer:
    """
    Transforms RawRecords into OMOP Staging tables based on mapping configurations.
    """
    def __init__(self, db: Session):
        self.db = db
        self.cleaner = CleaningRulesEngine()

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
            for raw in raw_records:
                # 1. Base clean (empty strings to None)
                cleaned_row = self.cleaner.clean_empty_values(raw.row_data)
                
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

                # 6.3 Lab Results -> StagingMeasurement
                lab_val = cleaned_row.get("lab_results")
                if lab_val:
                    if "：" in lab_val:
                        try:
                            category, items_str = lab_val.split("：", 1)
                            items_str = " ".join(items_str.split())
                            items = items_str.split(" ")
                            
                            parsed_any = False
                            i = 0
                            while i < len(items):
                                item = items[i]
                                if ":" in item:
                                    test_name, test_val = item.split(":", 1)
                                    test_name = test_name.strip()
                                    test_val = test_val.strip()
                                    
                                    if not test_val and i + 1 < len(items) and ":" not in items[i+1]:
                                        test_val = items[i+1].strip()
                                        i += 1
                                        
                                    if test_val:
                                        parsed_any = True
                                        meas = StagingMeasurement(
                                            source_batch_id=batch_id,
                                            raw_record_id=raw.id,
                                            person_source_value=person.person_source_value,
                                            measurement_source_value=test_name,
                                            value_source_value=test_val,
                                            unit_source_value="" # 测试数据中暂时没有单位，预留
                                        )
                                        if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                                            meas.measurement_datetime = visit.visit_start_datetime
                                            meas.measurement_date = visit.visit_start_date
                                        staging_objects.append(meas)
                                i += 1
                                
                            if not parsed_any:
                                meas = StagingMeasurement(
                                    source_batch_id=batch_id,
                                    raw_record_id=raw.id,
                                    person_source_value=person.person_source_value,
                                    measurement_source_value=lab_val,
                                    value_source_value=""
                                )
                                staging_objects.append(meas)
                        except Exception:
                            pass
                    else:
                        meas = StagingMeasurement(
                            source_batch_id=batch_id,
                            raw_record_id=raw.id,
                            person_source_value=person.person_source_value,
                            measurement_source_value=lab_val,
                            value_source_value=""
                        )
                        staging_objects.append(meas)

                # 6.4 NLP/Notes -> StagingObservation
                nlp_keys = ["chief_complaint", "history_of_present_illness", "imaging_reports", "admission_record", "daily_course_record", "discharge_summary", "treatment_plan"]
                for k in nlp_keys:
                    val = cleaned_row.get(k)
                    if val:
                        obs = StagingObservation(
                            source_batch_id=batch_id,
                            raw_record_id=raw.id,
                            person_source_value=person.person_source_value,
                            observation_source_value=f"[{k}] {val}", # 保留原始列名提示
                            value_as_string=val
                        )
                        if visit and hasattr(visit, 'visit_start_datetime') and visit.visit_start_datetime:
                            obs.observation_datetime = visit.visit_start_datetime
                            obs.observation_date = visit.visit_start_date
                        staging_objects.append(obs)
            
            # 7. Bulk insert to staging
            if staging_objects:
                self.db.bulk_save_objects(staging_objects)
                self.db.commit()
                
            offset += BATCH_SIZE
