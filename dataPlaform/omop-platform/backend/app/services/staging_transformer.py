from sqlalchemy.orm import Session
from typing import Dict, Any
from app.models.raw import RawRecord
from app.models.staging import StagingPerson
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
        mapping_config looks like: {"person_source_value": "patient_id", ...}
        """
        raw_records = self.db.query(RawRecord).filter(RawRecord.batch_id == batch_id).all()
        
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
            date_fields = [k for k in mapped_data.keys() if "date" in k.lower()]
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
            
        # 5. Bulk insert to staging
        if staging_objects:
            self.db.bulk_save_objects(staging_objects)
            self.db.commit()
