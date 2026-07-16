import json
import re
import time
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from collections import OrderedDict
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from app.core.logger import data_logger
from app.models.raw import RawRecord
from app.models.staging import (
    StagingPerson,
    StagingVisitOccurrence,
    StagingObservation,
    StagingMeasurement,
    StagingConditionOccurrence,
    StagingDrugExposure,
    StagingProcedureOccurrence,
    StagingNote,
    StagingNoteNlp,
    StagingSpecimen,
    StagingDeviceExposure,
    StagingCareSite,
    StagingDeath,
    StagingProvider,
)
from app.services.cleaning_rules import CleaningRulesEngine
from app.services.transformers_ner import TransformersNERMapper

class StagingTransformer:
    """
    Transforms RawRecords into OMOP Staging tables based on mapping configurations.
    """
    BATCH_SIZE = 10000
    NLP_BATCH_SIZE = 16
    NLP_KEYS = (
        "lab_results",
        "chief_complaint",
        "history_of_present_illness",
        "physical_examination",
        "icd_diagnosis",
        "electronic_prescription",
        "imaging_reports",
        "critical_values",
        "admission_record",
        "daily_course_record",
        "discharge_summary",
        "treatment_plan",
    )
    RX_FORMS = ("肠溶片", "分散片", "糖衣片", "薄膜衣片", "咀嚼片", "口腔崩解片", "软胶囊", "胶囊", "颗粒", "注射液", "口服液", "糖浆", "丸", "片")
    RX_ROUTES = ("静脉滴注", "静滴", "静脉注射", "静注", "肌肉注射", "肌注", "皮下注射", "皮注", "口服", "吞服", "含服", "舌下含服", "外用", "涂抹", "贴敷", "雾化吸入", "雾化", "滴眼", "滴鼻", "滴耳", "注射")
    RX_FREQUENCY_PATTERN = re.compile(r"\b(qd|bid|tid|qid|qod|qhs|qn|prn|st)\b|每日[一二三四五六七八九十0-9]+次|每[日天晚晨][一二三四五六七八九十0-9]*次", re.IGNORECASE)
    RX_DOSE_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|g|ug|mcg|μg|ml|mL|IU|iu|片|粒|袋|支|丸)\b", re.IGNORECASE)
    NLP_MEDICATION_PATTERN = re.compile(r"药名：(.*?)\s+剂型：(.*?)\s+给药方式：(.*?)(?:\s+剂量：(.*?))?(?:\s+频次：(.*))?$")
    NLP_MEASUREMENT_PATTERN = re.compile(r"检查项：(.*?)\s+值:([^\s]+)(?:\s+单位:(.*))?")
    NLP_SYMPTOM_PATTERN = re.compile(r"症状：(.*?)\s+持续时间：([^\s]+)")

    def __init__(self, db: Session, ner_mapper: Optional[TransformersNERMapper] = None):
        self.db = db
        self.cleaner = CleaningRulesEngine()
        self.ner_mapper = ner_mapper or TransformersNERMapper()

    @classmethod
    def _parse_nlp_medication_value(cls, med_val: str) -> Optional[Tuple[str, str, str]]:
        if not med_val:
            return None
        match = cls.NLP_MEDICATION_PATTERN.search(med_val)
        if not match:
            return None
        return match.group(1).strip(), match.group(2).strip(), match.group(3).strip()

    @classmethod
    def _parse_medication_components(cls, med_val: str) -> Optional[Dict[str, str]]:
        if not med_val:
            return None

        match = cls.NLP_MEDICATION_PATTERN.search(med_val)
        if match:
            return {
                "name": match.group(1).strip(),
                "form": match.group(2).strip(),
                "route": match.group(3).strip(),
                "dose": match.group(4).strip() if match.group(4) else "",
                "frequency": match.group(5).strip() if match.group(5) else "",
            }

        normalized = re.sub(r"[，,;；]+", " ", med_val).strip()
        if not normalized:
            return None

        dose_match = cls.RX_DOSE_PATTERN.search(normalized)
        freq_match = cls.RX_FREQUENCY_PATTERN.search(normalized)

        dose = dose_match.group(0).strip() if dose_match else ""
        frequency = freq_match.group(0).strip() if freq_match else ""

        route = ""
        for candidate in cls.RX_ROUTES:
            if candidate in normalized:
                route = candidate
                break

        stripped = normalized
        if dose:
            stripped = stripped.replace(dose, " ", 1)
        if frequency:
            stripped = re.sub(re.escape(frequency), " ", stripped, count=1, flags=re.IGNORECASE)
        if route:
            stripped = stripped.replace(route, " ", 1)
        stripped = re.sub(r"\s+", " ", stripped).strip()

        form = ""
        name = stripped
        for candidate in cls.RX_FORMS:
            if stripped.endswith(candidate):
                form = candidate
                name = stripped[: -len(candidate)].strip()
                break

        if not route:
            if "注射" in form:
                route = "注射"
            elif form:
                route = "口服"

        if not name:
            name = stripped

        return {
            "name": name,
            "form": form,
            "route": route,
            "dose": dose,
            "frequency": frequency.lower() if re.fullmatch(r"[A-Za-z]+", frequency or "") else frequency,
        }

    @classmethod
    def _parse_nlp_measurement_value(cls, meas_val: str) -> Optional[Tuple[str, str, str]]:
        if not meas_val:
            return None
        match = cls.NLP_MEASUREMENT_PATTERN.search(meas_val)
        if not match:
            return None
        unit = match.group(3).strip() if match.group(3) else ""
        return match.group(1).strip(), match.group(2).strip(), unit

    @classmethod
    def _parse_nlp_symptom_value(cls, sym_val: str) -> Optional[Tuple[str, str, str]]:
        if not sym_val:
            return None
        match = cls.NLP_SYMPTOM_PATTERN.search(sym_val)
        if not match:
            return None
        return match.group(1).strip(), match.group(2).strip(), "持续时间"

    @staticmethod
    def _apply_visit_start(obj: Any, visit: Optional[StagingVisitOccurrence], datetime_attr: str, date_attr: str) -> None:
        if not visit or not visit.visit_start_datetime:
            return
        setattr(obj, datetime_attr, visit.visit_start_datetime)
        setattr(obj, date_attr, visit.visit_start_date)

    @staticmethod
    def _append_observation(
        staging_objects: list,
        batch_id: str,
        raw_id: str,
        person_source_value: str,
        source_key: str,
        value: str,
        visit: Optional[StagingVisitOccurrence],
        prefix: str = "",
        note_id: Optional[int] = None,
    ) -> None:
        obs_value = f"[{source_key}] {prefix}{value}"
        obs = StagingObservation(
            source_batch_id=batch_id,
            raw_record_id=raw_id,
            person_source_value=person_source_value,
            observation_source_value=obs_value,
            value_as_string=value,
            note_id=note_id,
        )
        StagingTransformer._apply_visit_start(obs, visit, "observation_datetime", "observation_date")
        staging_objects.append(obs)

    @staticmethod
    def _append_note_nlp(
        staging_objects: list,
        batch_id: str,
        raw_id: str,
        person_source_value: str,
        section_source_value: str,
        nlp_domain: str,
        value: str,
        note_id: Optional[int] = None,
    ) -> None:
        staging_objects.append(
            StagingNoteNlp(
                source_batch_id=batch_id,
                raw_record_id=raw_id,
                person_source_value=person_source_value,
                note_id=note_id,
                section_source_value=section_source_value,
                nlp_domain=nlp_domain,
                lexical_variant=value,
                normalized_value=value,
                term_exists="Y",
            )
        )

    @staticmethod
    def _append_note_nlp_item(
        staging_objects: list,
        batch_id: str,
        raw_id: str,
        person_source_value: str,
        note_id: Optional[int],
        fallback_section: str,
        item: Dict[str, Any],
    ) -> None:
        if not isinstance(item, dict):
            return
        lexical_variant = str(item.get("text", "")).strip()
        if not lexical_variant:
            return
        normalized_value = str(item.get("normalized_value", lexical_variant)).strip() or lexical_variant
        item_section = str(item.get("section", "")).strip()
        if not item_section or item_section == fallback_section:
            section_source_value = fallback_section
        elif item_section.startswith(f"{fallback_section}#"):
            section_source_value = item_section
        else:
            section_source_value = f"{fallback_section}#{item_section}"
        nlp_domain = str(item.get("domain", "observation")).strip() or "observation"
        source_layer = str(item.get("source_layer", "unknown")).strip() or "unknown"
        negated = bool(item.get("negated", False))
        confidence = item.get("confidence")
        offset_start = item.get("offset_start")
        offset_end = item.get("offset_end")

        staging_objects.append(
            StagingNoteNlp(
                source_batch_id=batch_id,
                raw_record_id=raw_id,
                person_source_value=person_source_value,
                note_id=note_id,
                section_source_value=section_source_value,
                nlp_domain=nlp_domain,
                lexical_variant=lexical_variant,
                normalized_value=normalized_value,
                term_exists="N" if negated else "Y",
                source_layer=source_layer,
                negated="Y" if negated else "N",
                offset_start=int(offset_start) if offset_start is not None else None,
                offset_end=int(offset_end) if offset_end is not None else None,
                note_nlp_concept_id=str(confidence) if confidence is not None else "0",
            )
        )

    @staticmethod
    def _build_note_nlp_dedupe_key(row: StagingNoteNlp) -> Tuple[Any, ...]:
        return (
            row.source_batch_id,
            row.raw_record_id,
            row.person_source_value,
            row.note_id,
            row.section_source_value,
            row.nlp_domain,
            row.lexical_variant,
            row.normalized_value,
        )

    @staticmethod
    def _score_note_nlp_row(row: StagingNoteNlp) -> Tuple[int, int, int, int, int, int]:
        source_layer_score = 0 if not row.source_layer or row.source_layer == "unknown" else 1
        negated_score = 1 if row.negated == "Y" else 0
        offset_start_score = 1 if row.offset_start is not None else 0
        offset_end_score = 1 if row.offset_end is not None else 0
        concept_score = 0 if not row.note_nlp_concept_id or row.note_nlp_concept_id == "0" else 1
        normalized_score = 1 if row.normalized_value and row.normalized_value != row.lexical_variant else 0
        return (
            source_layer_score,
            negated_score,
            offset_start_score,
            offset_end_score,
            concept_score,
            normalized_score,
        )

    @classmethod
    def _dedupe_staging_objects(cls, staging_objects: list) -> list:
        deduped_objects = []
        note_nlp_positions: Dict[Tuple[Any, ...], int] = {}

        for obj in staging_objects:
            if not isinstance(obj, StagingNoteNlp):
                deduped_objects.append(obj)
                continue

            dedupe_key = cls._build_note_nlp_dedupe_key(obj)
            existing_position = note_nlp_positions.get(dedupe_key)
            if existing_position is None:
                note_nlp_positions[dedupe_key] = len(deduped_objects)
                deduped_objects.append(obj)
                continue

            existing_row = deduped_objects[existing_position]
            if cls._score_note_nlp_row(obj) > cls._score_note_nlp_row(existing_row):
                deduped_objects[existing_position] = obj

        return deduped_objects

    @staticmethod
    def _bulk_save_grouped(db: Session, staging_objects: list) -> None:
        if not staging_objects:
            return

        grouped_objects = OrderedDict()
        for obj in staging_objects:
            model_type = type(obj)
            if model_type not in grouped_objects:
                grouped_objects[model_type] = []
            grouped_objects[model_type].append(obj)

        for objects in grouped_objects.values():
            db.bulk_save_objects(objects)
        db.commit()

    @staticmethod
    def _build_provider_seen_key(batch_id: str, provider_value: str) -> str:
        return f"{batch_id}::{provider_value.strip()}"

    @staticmethod
    def _build_care_site_seen_key(batch_id: str, care_site_value: str) -> str:
        return f"{batch_id}::{care_site_value.strip()}"

    @staticmethod
    def _format_stage_timing_log(prefix: str, metrics: Dict[str, float], extra: Optional[Dict[str, Any]] = None) -> str:
        metric_parts = [f"{key}={value:.2f}" for key, value in metrics.items()]
        extra_parts = [f"{key}={value}" for key, value in (extra or {}).items()]
        return f"{prefix} {' '.join(metric_parts + extra_parts)}".strip()

    def _delete_existing_staging_rows(self, batch_id: str, business_key: str) -> None:
        if not business_key:
            return

        staging_models = (
            StagingPerson,
            StagingVisitOccurrence,
            StagingObservation,
            StagingMeasurement,
            StagingConditionOccurrence,
            StagingDrugExposure,
            StagingProcedureOccurrence,
            StagingNote,
            StagingNoteNlp,
            StagingSpecimen,
            StagingDeviceExposure,
            StagingDeath,
        )

        for model in staging_models:
            self.db.query(model).filter(
                model.source_batch_id == batch_id,
                model.person_source_value == business_key,
            ).delete(synchronize_session=False)

    def transform_batch_to_person(self, batch_id: str, mapping_config: Dict[str, str]):
        """
        Extracts records from RawZone, applies mapping/cleaning, and inserts to StagingPerson.
        Uses batching to significantly improve performance on large datasets.
        """
        offset = 0
        date_fields = [k for k in mapping_config.keys() if "date" in k.lower() or "datetime" in k.lower()]
        
        while True:
            raw_records = (
                self.db.query(RawRecord)
                .filter(RawRecord.batch_id == batch_id)
                .filter(
                    or_(
                        RawRecord.change_type.is_(None),
                        RawRecord.change_type.in_(["insert", "update", "delete"]),
                    )
                )
                .limit(self.BATCH_SIZE)
                .offset(offset)
                .all()
            )
            if not raw_records:
                break
                
            staging_objects = []
            provider_seen = set()
            care_site_seen = set()
            pending_notes = []
            # 6.4 Collect NLP tasks for batch processing later
            nlp_tasks = []
            
            for raw in raw_records:
                if raw.change_type == "delete":
                    self._delete_existing_staging_rows(batch_id=batch_id, business_key=raw.business_key or "")
                    continue

                # 1. Base clean (empty strings to None)
                raw_dict = raw.row_data if isinstance(raw.row_data, dict) else json.loads(raw.row_data)
                cleaned_row = self.cleaner.clean_empty_values(raw_dict)
                
                # 2. Field Mapping
                mapped_data = {}
                for target_field, source_field in mapping_config.items():
                    mapped_data[target_field] = cleaned_row.get(source_field)
                
                # 3. Apply specific cleaning rules based on target domains
                # Date Parsing
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
                    self._apply_visit_start(cond, visit, "condition_start_datetime", "condition_start_date")
                    staging_objects.append(cond)

                # 6.2 Medication -> StagingDrugExposure
                rx_val = cleaned_row.get("electronic_prescription")
                if rx_val:
                    parsed_rx = self._parse_medication_components(rx_val) or {
                        "name": rx_val,
                        "form": "",
                        "route": "",
                        "dose": "",
                        "frequency": "",
                    }
                    drug = StagingDrugExposure(
                        source_batch_id=batch_id,
                        raw_record_id=raw.id,
                        person_source_value=person.person_source_value,
                        drug_source_value=parsed_rx["name"],
                        dose_source_value=parsed_rx["dose"],
                        form_source_value=parsed_rx["form"],
                        route_source_value=parsed_rx["route"],
                        frequency_source_value=parsed_rx["frequency"]
                    )
                    self._apply_visit_start(drug, visit, "drug_exposure_start_datetime", "drug_exposure_start_date")
                    staging_objects.append(drug)

                # 6.3 Lab Results -> NLP processing (handled together with other notes)
                # Removed manual split logic to let TransformersNERMapper handle it cleanly.

                # 6.4 NLP/Notes -> Collect for Batch Processing
                for k in self.NLP_KEYS:
                    val = cleaned_row.get(k)
                    if val:
                        note = StagingNote(
                            source_batch_id=batch_id,
                            raw_record_id=raw.id,
                            person_source_value=person.person_source_value,
                            note_source_value=k,
                            note_text=val,
                        )
                        self._apply_visit_start(note, visit, "note_datetime", "note_date")
                        pending_notes.append(note)
                        nlp_tasks.append({
                            "person": person,
                            "visit": visit,
                            "batch_id": batch_id,
                            "raw_id": raw.id,
                            "key": k,
                            "text": val,
                            "note": note,
                        })

            if pending_notes:
                self.db.add_all(pending_notes)
                self.db.flush()
                for task in nlp_tasks:
                    task["note_id"] = task["note"].id
            
            # 6.5 Execute Batch NLP Processing
            nlp_infer_ms = 0.0
            if nlp_tasks:
                t0 = time.time()
                texts_to_process = [task["text"] for task in nlp_tasks]
                
                # Batch size 16 is usually a sweet spot for RTX/GTX GPUs
                batch_results = self.ner_mapper.extract_entities_batch(texts_to_process, batch_size=self.NLP_BATCH_SIZE)
                nlp_infer_ms = (time.time() - t0) * 1000
                
                for task, extracted_entities in zip(nlp_tasks, batch_results):
                    person = task["person"]
                    visit = task["visit"]
                    b_id = task["batch_id"]
                    r_id = task["raw_id"]
                    k = task["key"]
                    note_id = task["note_id"]
                    person_source_value = person.person_source_value
                    
                    # Process Conditions
                    for cond_val in extracted_entities.get("conditions", []):
                        cond = StagingConditionOccurrence(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person_source_value,
                            condition_source_value=cond_val,
                            note_id=note_id,
                        )
                        self._apply_visit_start(cond, visit, "condition_start_datetime", "condition_start_date")
                        staging_objects.append(cond)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "condition", cond_val, note_id=note_id)
                        
                    # Process Medications
                    for med_val in extracted_entities.get("medications", []):
                        parsed_med = self._parse_medication_components(med_val)
                        if parsed_med:
                            drug = StagingDrugExposure(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                person_source_value=person_source_value,
                                drug_source_value=parsed_med["name"],
                                form_source_value=parsed_med["form"],
                                route_source_value=parsed_med["route"],
                                dose_source_value=parsed_med["dose"],
                                frequency_source_value=parsed_med["frequency"],
                                note_id=note_id,
                            )
                        else:
                            drug = StagingDrugExposure(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                person_source_value=person_source_value,
                                drug_source_value=med_val,
                                note_id=note_id,
                            )
                        self._apply_visit_start(drug, visit, "drug_exposure_start_datetime", "drug_exposure_start_date")
                        staging_objects.append(drug)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "medication", med_val, note_id=note_id)

                    # Process Procedures
                    for proc_val in extracted_entities.get("procedures", []):
                        proc = StagingProcedureOccurrence(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person_source_value,
                            procedure_source_value=proc_val,
                            note_id=note_id,
                        )
                        self._apply_visit_start(proc, visit, "procedure_datetime", "procedure_date")
                        staging_objects.append(proc)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "procedure", proc_val, note_id=note_id)

                    # Process Devices
                    for device_val in extracted_entities.get("devices", []):
                        device = StagingDeviceExposure(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person_source_value,
                            device_source_value=device_val,
                            note_id=note_id,
                        )
                        self._apply_visit_start(device, visit, "device_exposure_start_datetime", "device_exposure_start_date")
                        staging_objects.append(device)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "device", device_val, note_id=note_id)

                    # Process Specimens
                    for specimen_val in extracted_entities.get("specimens", []):
                        specimen = StagingSpecimen(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person_source_value,
                            specimen_source_value=specimen_val,
                            note_id=note_id,
                        )
                        self._apply_visit_start(specimen, visit, "specimen_datetime", "specimen_date")
                        staging_objects.append(specimen)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "specimen", specimen_val, note_id=note_id)

                    # Process Care Sites
                    for care_site_val in extracted_entities.get("care_sites", []):
                        care_site_seen_key = self._build_care_site_seen_key(b_id, care_site_val)
                        if care_site_seen_key not in care_site_seen:
                            care_site_seen.add(care_site_seen_key)
                            care_site = StagingCareSite(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                care_site_source_value=care_site_val,
                            )
                            staging_objects.append(care_site)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "care_site", care_site_val, note_id=note_id)

                    # Process Providers
                    for provider_val in extracted_entities.get("providers", []):
                        provider_seen_key = self._build_provider_seen_key(b_id, provider_val)
                        if provider_seen_key not in provider_seen:
                            provider_seen.add(provider_seen_key)
                            provider = StagingProvider(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                provider_source_value=provider_val,
                                provider_name=provider_val,
                            )
                            staging_objects.append(provider)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "provider", provider_val, note_id=note_id)

                    # Process Death
                    for death_val in extracted_entities.get("death", []):
                        death = StagingDeath(
                            source_batch_id=b_id,
                            raw_record_id=r_id,
                            person_source_value=person_source_value,
                            death_type_source_value=death_val,
                            note_id=note_id,
                        )
                        self._apply_visit_start(death, visit, "death_datetime", "death_date")
                        staging_objects.append(death)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "death", death_val, note_id=note_id)
                        
                    # Process Measurements
                    for meas_val in extracted_entities.get("measurements", []):
                        parsed_measurement = self._parse_nlp_measurement_value(meas_val)
                        if parsed_measurement:
                            m_name, m_val, m_unit = parsed_measurement
                            meas = StagingMeasurement(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                person_source_value=person_source_value,
                                measurement_source_value=m_name,
                                value_source_value=m_val,
                                unit_source_value=m_unit,
                                note_id=note_id,
                            )
                            self._apply_visit_start(meas, visit, "measurement_datetime", "measurement_date")
                            staging_objects.append(meas)
                            self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "measurement", meas_val, note_id=note_id)
                            
                    # Process Symptoms with values
                    for sym_val in extracted_entities.get("symptoms_with_values", []):
                        parsed_symptom = self._parse_nlp_symptom_value(sym_val)
                        if parsed_symptom:
                            s_name, s_val, s_unit = parsed_symptom
                            meas = StagingMeasurement(
                                source_batch_id=b_id,
                                raw_record_id=r_id,
                                person_source_value=person_source_value,
                                measurement_source_value=f"症状-{s_name}",
                                value_source_value=s_val,
                                unit_source_value=s_unit,
                                note_id=note_id,
                            )
                            self._apply_visit_start(meas, visit, "measurement_datetime", "measurement_date")
                            staging_objects.append(meas)
                            self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "symptom", sym_val, note_id=note_id)
                            
                    # Process Times
                    for time_val in extracted_entities.get("times", []):
                        self._append_observation(staging_objects, b_id, r_id, person_source_value, k, time_val, visit, prefix="时间：", note_id=note_id)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "time", time_val, note_id=note_id)

                    # Process generic observations and fallback
                    for obs_val in extracted_entities.get("observations", []):
                        self._append_observation(staging_objects, b_id, r_id, person_source_value, k, obs_val, visit, note_id=note_id)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "observation", obs_val, note_id=note_id)

                    # Process negations
                    for val in extracted_entities.get("negations", []):
                        self._append_observation(staging_objects, b_id, r_id, person_source_value, k, val, visit, note_id=note_id)
                        self._append_note_nlp(staging_objects, b_id, r_id, person_source_value, k, "negation", val, note_id=note_id)

                    # Process structured note NLP items
                    for item in extracted_entities.get("note_nlp_items", []):
                        self._append_note_nlp_item(
                            staging_objects=staging_objects,
                            batch_id=b_id,
                            raw_id=r_id,
                            person_source_value=person_source_value,
                            note_id=note_id,
                            fallback_section=k,
                            item=item,
                        )
                
                data_logger.info(
                    self._format_stage_timing_log(
                        f"[{batch_id}] [STAGING_NLP]",
                        {"nlp_infer_ms": nlp_infer_ms},
                        {"texts": len(nlp_tasks)},
                    )
                )
            
            # 7. Bulk insert to staging
            if staging_objects:
                staging_objects = self._dedupe_staging_objects(staging_objects)
                orm_started_at = time.perf_counter()
                self._bulk_save_grouped(self.db, staging_objects)
                data_logger.info(
                    self._format_stage_timing_log(
                        f"[{batch_id}] [STAGING_ORM]",
                        {"orm_ms": (time.perf_counter() - orm_started_at) * 1000},
                        {"objects": len(staging_objects)},
                    )
                )
                
            offset += self.BATCH_SIZE
