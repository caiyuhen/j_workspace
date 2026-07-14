from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.raw import RawRecord, SourceBatch
from app.models.staging import (
    StagingConditionOccurrence,
    StagingDrugExposure,
    StagingMeasurement,
    StagingNote,
    StagingNoteNlp,
    StagingObservation,
)
from app.services.staging_transformer import StagingTransformer


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class LegacyTraceNERMapper:
    def extract_entities_batch(self, texts, batch_size=16):
        return [
            {
                "conditions": ["冠心病"],
                "medications": ["药名：阿司匹林 剂型：片 给药方式：口服"],
                "procedures": [],
                "measurements": ["检查项：空腹血糖 值:6.5 单位:mmol/L"],
                "symptoms_with_values": ["症状：胸闷 持续时间：1周"],
                "times": ["1周前"],
                "observations": ["右上腹压痛"],
                "negations": ["诊断：糖尿病 ，否定词：否认"],
                "devices": [],
                "specimens": [],
                "death": [],
                "providers": [],
                "care_sites": [],
                "note_nlp_items": [],
            }
            for _ in texts
        ]


def test_transformer_links_legacy_note_domains_and_mirrors_note_nlp():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        batch = SourceBatch(id="batch_legacy_trace", filename="legacy_trace.csv")
        db.add(batch)
        db.commit()

        raw = RawRecord(
            id="raw_legacy_trace",
            batch_id="batch_legacy_trace",
            row_data={
                "patient_id": "P500",
                "gender": "男",
                "chief_complaint": "胸闷1周，右上腹压痛。",
            },
        )
        db.add(raw)
        db.commit()

        mapping_config = {
            "person_source_value": "patient_id",
            "gender_source_value": "gender",
        }

        transformer = StagingTransformer(db, ner_mapper=LegacyTraceNERMapper())
        transformer.transform_batch_to_person(batch_id="batch_legacy_trace", mapping_config=mapping_config)

        note = db.query(StagingNote).one()

        condition = db.query(StagingConditionOccurrence).one()
        drug = db.query(StagingDrugExposure).one()
        measurements = db.query(StagingMeasurement).order_by(StagingMeasurement.id).all()
        observations = db.query(StagingObservation).order_by(StagingObservation.id).all()
        note_nlp_rows = db.query(StagingNoteNlp).all()

        assert condition.note_id == note.id
        assert drug.note_id == note.id
        assert {row.note_id for row in measurements} == {note.id}
        assert {row.note_id for row in observations} == {note.id}

        assert len(measurements) == 2
        assert len(observations) == 3
        assert len(note_nlp_rows) == 7
        assert {row.note_id for row in note_nlp_rows} == {note.id}
        assert {row.nlp_domain for row in note_nlp_rows} == {
            "condition",
            "medication",
            "measurement",
            "symptom",
            "time",
            "observation",
            "negation",
        }
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
