from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.raw import RawRecord, SourceBatch
from app.models.staging import StagingNote, StagingNoteNlp
from app.services.staging_transformer import StagingTransformer


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class NoteNlpItemsMapper:
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
                "devices": [],
                "specimens": [],
                "death": [],
                "providers": [],
                "care_sites": [],
                "note_nlp_items": [
                    {
                        "domain": "procedure",
                        "text": "冠脉CTA",
                        "normalized_value": "冠状动脉CT血管成像",
                        "section": "daily_course_record",
                        "source_layer": "llm",
                        "negated": False,
                        "confidence": 0.91,
                        "offset_start": 2,
                        "offset_end": 7,
                    },
                    {
                        "domain": "observation",
                        "text": "右上腹压痛",
                        "normalized_value": "右上腹压痛",
                        "section": "查体",
                        "source_layer": "regex",
                        "negated": True,
                        "confidence": 0.88,
                        "offset_start": 10,
                        "offset_end": 15,
                    },
                ],
            }
            for _ in texts
        ]


class DuplicateStructuredNoteNlpMapper:
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
                "devices": [],
                "specimens": [],
                "death": [],
                "providers": [],
                "care_sites": [],
                "note_nlp_items": [
                    {
                        "domain": "procedure",
                        "text": "冠脉CTA",
                        "normalized_value": "冠脉CTA",
                        "section": "daily_course_record",
                        "source_layer": "llm",
                        "negated": False,
                        "confidence": 0.91,
                        "offset_start": 2,
                        "offset_end": 7,
                    }
                ],
            }
            for _ in texts
        ]


def test_transformer_persists_structured_note_nlp_items():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        batch = SourceBatch(id="batch_note_nlp_items", filename="note_nlp_items.csv")
        db.add(batch)
        db.commit()

        raw = RawRecord(
            id="raw_note_nlp_items",
            batch_id="batch_note_nlp_items",
            row_data={
                "patient_id": "P600",
                "gender": "女",
                "daily_course_record": "完善冠脉CTA，查体右上腹压痛。",
            },
        )
        db.add(raw)
        db.commit()

        mapping_config = {
            "person_source_value": "patient_id",
            "gender_source_value": "gender",
        }

        transformer = StagingTransformer(db, ner_mapper=NoteNlpItemsMapper())
        transformer.transform_batch_to_person(batch_id="batch_note_nlp_items", mapping_config=mapping_config)

        note = db.query(StagingNote).one()
        note_nlp_rows = db.query(StagingNoteNlp).order_by(StagingNoteNlp.id).all()

        assert len(note_nlp_rows) == 2
        assert {row.note_id for row in note_nlp_rows} == {note.id}

        first = note_nlp_rows[0]
        assert first.section_source_value == "daily_course_record"
        assert first.nlp_domain == "procedure"
        assert first.lexical_variant == "冠脉CTA"
        assert first.normalized_value == "冠状动脉CT血管成像"
        assert first.term_exists == "Y"
        assert first.note_nlp_concept_id == "0.91"
        assert first.source_layer == "llm"
        assert first.negated == "N"
        assert first.offset_start == 2
        assert first.offset_end == 7

        second = note_nlp_rows[1]
        assert second.source_layer == "regex"
        assert second.negated == "Y"
        assert second.term_exists == "N"
        assert second.section_source_value == "daily_course_record#查体"
        assert second.offset_start == 10
        assert second.offset_end == 15
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_transformer_dedupes_duplicate_structured_note_nlp_rows():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        batch = SourceBatch(id="batch_note_nlp_dedupe", filename="note_nlp_dedupe.csv")
        db.add(batch)
        db.commit()

        raw = RawRecord(
            id="raw_note_nlp_dedupe",
            batch_id="batch_note_nlp_dedupe",
            row_data={
                "patient_id": "P601",
                "gender": "男",
                "daily_course_record": "完善冠脉CTA。",
            },
        )
        db.add(raw)
        db.commit()

        mapping_config = {
            "person_source_value": "patient_id",
            "gender_source_value": "gender",
        }

        transformer = StagingTransformer(db, ner_mapper=DuplicateStructuredNoteNlpMapper())
        transformer.transform_batch_to_person(batch_id="batch_note_nlp_dedupe", mapping_config=mapping_config)

        note = db.query(StagingNote).one()
        note_nlp_rows = db.query(StagingNoteNlp).all()

        assert len(note_nlp_rows) == 1
        row = note_nlp_rows[0]
        assert row.note_id == note.id
        assert row.nlp_domain == "procedure"
        assert row.lexical_variant == "冠脉CTA"
        assert row.section_source_value == "daily_course_record"
        assert row.source_layer == "llm"
        assert row.note_nlp_concept_id == "0.91"
        assert row.offset_start == 2
        assert row.offset_end == 7
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
