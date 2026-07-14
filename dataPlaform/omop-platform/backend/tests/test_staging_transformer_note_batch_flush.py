from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.raw import RawRecord, SourceBatch
from app.models.staging import StagingConditionOccurrence, StagingNote
from app.services.staging_transformer import StagingTransformer


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class MultiNoteNERMapper:
    def extract_entities_batch(self, texts, batch_size=16):
        return [
            {
                "conditions": [f"诊断-{idx}"],
                "medications": [],
                "procedures": [],
                "measurements": [],
                "symptoms_with_values": [],
                "times": [],
                "observations": [],
                "negations": [],
                "devices": [],
                "specimens": [],
                "death": [],
                "providers": [],
                "care_sites": [],
                "note_nlp_items": [],
            }
            for idx, _ in enumerate(texts, start=1)
        ]


def test_transformer_flushes_notes_once_per_batch_and_keeps_note_links():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        batch = SourceBatch(id="batch_note_flush", filename="note_flush.csv")
        db.add(batch)
        db.commit()

        raw = RawRecord(
            id="raw_note_flush",
            batch_id="batch_note_flush",
            row_data={
                "patient_id": "P700",
                "gender": "男",
                "chief_complaint": "胸闷1周。",
                "daily_course_record": "冠心病复诊。",
            },
        )
        db.add(raw)
        db.commit()

        flush_calls = 0
        original_flush = db.flush

        def counting_flush(*args, **kwargs):
            nonlocal flush_calls
            flush_calls += 1
            return original_flush(*args, **kwargs)

        db.flush = counting_flush

        mapping_config = {
            "person_source_value": "patient_id",
            "gender_source_value": "gender",
        }

        transformer = StagingTransformer(db, ner_mapper=MultiNoteNERMapper())
        transformer.transform_batch_to_person(batch_id="batch_note_flush", mapping_config=mapping_config)

        notes = db.query(StagingNote).order_by(StagingNote.id).all()
        conditions = db.query(StagingConditionOccurrence).order_by(StagingConditionOccurrence.id).all()

        assert len(notes) == 2
        assert len(conditions) == 2
        assert flush_calls == 1
        assert {row.note_id for row in conditions} == {note.id for note in notes}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
