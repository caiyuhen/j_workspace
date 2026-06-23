import pydicom
from typing import Dict, Any
import os

class DicomParser:
    """
    Parser for medical imaging files (DICOM).
    Extracts metadata to be mapped to OMOP CDM (Observation/Measurement tables),
    while the raw image file should be sent to Object Storage (MinIO).
    """
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_metadata(self) -> Dict[str, Any]:
        """
        Reads the DICOM header and extracts key metadata required for OMOP mapping.
        """
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(f"DICOM file not found: {self.file_path}")

        try:
            # stop_before_pixels=True ensures we don't load the heavy image matrix into memory
            # because we only need the metadata for ETL.
            ds = pydicom.dcmread(self.file_path, stop_before_pixels=True)
            
            metadata = {
                # Patient Info -> maps to Person
                "patient_id": getattr(ds, "PatientID", None),
                "patient_name": str(getattr(ds, "PatientName", "")) if getattr(ds, "PatientName", None) else None,
                "patient_sex": getattr(ds, "PatientSex", None),
                "patient_birth_date": getattr(ds, "PatientBirthDate", None),
                
                # Study Info -> maps to Visit / Procedure
                "study_instance_uid": getattr(ds, "StudyInstanceUID", None),
                "study_date": getattr(ds, "StudyDate", None),
                "study_time": getattr(ds, "StudyTime", None),
                "modality": getattr(ds, "Modality", None), # e.g., CT, MR, CR
                
                # Body Part -> maps to Observation/Measurement concept
                "body_part_examined": getattr(ds, "BodyPartExamined", None),
                
                # Equipment/Institution -> maps to Care_Site / Device
                "institution_name": getattr(ds, "InstitutionName", None),
                "manufacturer": getattr(ds, "Manufacturer", None),
            }
            return metadata
        except Exception as e:
            raise ValueError(f"Failed to parse DICOM file: {str(e)}")

    def deidentify_dicom(self, output_path: str, new_patient_id: str = None) -> str:
        """
        Removes PHI (Protected Health Information) from the DICOM header before saving to Object Storage.
        Returns the absolute path to the saved de-identified file.
        """
        ds = pydicom.dcmread(self.file_path)
        
        # Anonymize PHI tags
        if "PatientName" in ds:
            ds.PatientName = "ANONYMOUS"
        if "PatientBirthDate" in ds:
            # Mask to year only if possible, or completely anonymize
            birth_date = str(ds.PatientBirthDate)
            if len(birth_date) >= 4:
                ds.PatientBirthDate = f"{birth_date[:4]}0101"
            else:
                ds.PatientBirthDate = "19000101"
                
        if new_patient_id and "PatientID" in ds:
            ds.PatientID = new_patient_id
            
        # Optional: Anonymize Institution if required
        # if "InstitutionName" in ds:
        #     ds.InstitutionName = "UNKNOWN_INSTITUTION"
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        
        # Save the scrubbed DICOM
        ds.save_as(output_path)
        return output_path
