from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.raw import RawRecord, SourceBatch
from app.models.staging import StagingNote, StagingProcedureOccurrence
from app.services.staging_transformer import StagingTransformer


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class ProcedureNERMapper:
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
            }
            for _ in texts
        ]


def test_transformer_persists_note_and_procedure_entities():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        batch = SourceBatch(id="batch_proc", filename="proc.csv")
        db.add(batch)
        db.commit()

        raw = RawRecord(
            id="raw_proc",
            batch_id="batch_proc",
            row_data={
                "patient_id": "P100",
                "gender": "男",
                "chief_complaint": "胸闷胸痛",
                "daily_course_record": "建议完善冠脉CTA",
            },
        )
        db.add(raw)
        db.commit()

        mapping_config = {
            "person_source_value": "patient_id",
            "gender_source_value": "gender",
        }

        transformer = StagingTransformer(db, ner_mapper=ProcedureNERMapper())
        transformer.transform_batch_to_person(batch_id="batch_proc", mapping_config=mapping_config)

        assert db.query(StagingNote).count() == 2
        procedures = db.query(StagingProcedureOccurrence).all()
        assert len(procedures) == 2
        assert all(proc.procedure_source_value == "冠脉CTA" for proc in procedures)
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
