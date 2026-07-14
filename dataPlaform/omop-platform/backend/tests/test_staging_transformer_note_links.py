from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.raw import RawRecord, SourceBatch
from app.models.staging import (
    StagingDeath,
    StagingDeviceExposure,
    StagingNote,
    StagingNoteNlp,
    StagingProcedureOccurrence,
    StagingSpecimen,
)
from app.services.staging_transformer import StagingTransformer


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class NoteLinkNERMapper:
    def extract_entities_batch(self, texts, batch_size=16):
        return [
            {
                "conditions": [],
                "medications": [],
                "procedures": ["冠脉CTA"],
                "measurements": [],
                "symptoms_with_values": [],
                "times": [],
                "observations": [],
                "negations": [],
                "devices": ["冠脉支架"],
                "specimens": ["静脉血"],
                "death": ["抢救无效死亡"],
                "providers": [],
                "care_sites": [],
                "note_nlp_items": [],
            }
            for _ in texts
        ]


def test_transformer_links_note_driven_entities_back_to_note():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        batch = SourceBatch(id="batch_note_link", filename="note_link.csv")
        db.add(batch)
        db.commit()

        raw = RawRecord(
            id="raw_note_link",
            batch_id="batch_note_link",
            row_data={
                "patient_id": "P400",
                "gender": "男",
                "daily_course_record": "患者于心内科完善冠脉CTA，留取静脉血，抢救无效死亡。",
            },
        )
        db.add(raw)
        db.commit()

        mapping_config = {
            "person_source_value": "patient_id",
            "gender_source_value": "gender",
        }

        transformer = StagingTransformer(db, ner_mapper=NoteLinkNERMapper())
        transformer.transform_batch_to_person(batch_id="batch_note_link", mapping_config=mapping_config)

        note = db.query(StagingNote).one()
        assert note.note_source_value == "daily_course_record"

        procedure = db.query(StagingProcedureOccurrence).one()
        device = db.query(StagingDeviceExposure).one()
        specimen = db.query(StagingSpecimen).one()
        death = db.query(StagingDeath).one()
        note_nlp_rows = db.query(StagingNoteNlp).all()

        assert procedure.note_id == note.id
        assert device.note_id == note.id
        assert specimen.note_id == note.id
        assert death.note_id == note.id
        assert {row.note_id for row in note_nlp_rows} == {note.id}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
