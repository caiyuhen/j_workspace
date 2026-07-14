from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.raw import RawRecord, SourceBatch
from app.models.staging import (
    StagingCareSite,
    StagingDeviceExposure,
    StagingNoteNlp,
    StagingSpecimen,
)
from app.services.staging_transformer import StagingTransformer


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DomainNERMapper:
    def extract_entities_batch(self, texts, batch_size=16):
        return [
            {
                "conditions": [],
                "medications": [],
                "procedures": [],
                "measurements": [],
                "symptoms_with_values": [],
                "times": [],
                "observations": [],
                "negations": [],
                "devices": ["冠脉支架"],
                "specimens": ["静脉血"],
                "death": [],
                "providers": [],
                "care_sites": ["心内科"],
                "note_nlp_items": [],
            }
            for _ in texts
        ]


def test_transformer_persists_note_nlp_and_new_domain_rows():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        batch = SourceBatch(id="batch_note_nlp", filename="note_nlp.csv")
        db.add(batch)
        db.commit()

        raw = RawRecord(
            id="raw_note_nlp",
            batch_id="batch_note_nlp",
            row_data={
                "patient_id": "P200",
                "gender": "女",
                "chief_complaint": "胸痛",
            },
        )
        db.add(raw)
        db.commit()

        mapping_config = {
            "person_source_value": "patient_id",
            "gender_source_value": "gender",
        }

        transformer = StagingTransformer(db, ner_mapper=DomainNERMapper())
        transformer.transform_batch_to_person(batch_id="batch_note_nlp", mapping_config=mapping_config)

        assert db.query(StagingDeviceExposure).count() == 1
        assert db.query(StagingSpecimen).count() == 1
        assert db.query(StagingCareSite).count() == 1

        note_nlp_rows = db.query(StagingNoteNlp).all()
        assert len(note_nlp_rows) == 3
        assert {row.nlp_domain for row in note_nlp_rows} == {"device", "specimen", "care_site"}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
