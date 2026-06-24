import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import UID
import datetime
import os

def create_dummy_dicom(filename):
    file_meta = FileMetaDataset()
    file_meta.MediaStorageSOPClassUID = UID('1.2.840.10008.5.1.4.1.1.2') # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = UID("1.2.3")
    file_meta.ImplementationClassUID = UID("1.2.3.4")

    ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0" * 128)
    ds.PatientName = "Test^Patient"
    ds.PatientID = "123456"
    ds.PatientBirthDate = "19900101"
    ds.PatientSex = "M"
    ds.StudyInstanceUID = "1.2.3.4.5.6.7"
    ds.StudyDate = datetime.datetime.now().strftime('%Y%m%d')
    ds.StudyTime = datetime.datetime.now().strftime('%H%M%S')
    ds.Modality = "CT"
    ds.BodyPartExamined = "CHEST"
    ds.InstitutionName = "Test Hospital"

    ds.is_little_endian = True
    ds.is_implicit_VR = True

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    ds.save_as(filename)
    print(f"Generated dummy DICOM at {filename}")

if __name__ == "__main__":
    create_dummy_dicom(r"d:\workspace\dataPlaform\omop-platform\inputdata\sample_image.dcm")