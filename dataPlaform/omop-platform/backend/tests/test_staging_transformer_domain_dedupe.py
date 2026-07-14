from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.raw import RawRecord, SourceBatch
from app.models.staging import StagingCareSite, StagingDeath, StagingNoteNlp, StagingProvider
from app.services.staging_transformer import StagingTransformer


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class DedupeNERMapper:
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
                "death": ["抢救无效死亡"],
                "providers": ["李主任"],
                "care_sites": ["心内科"],
                "note_nlp_items": [],
            }
            for _ in texts
        ]


def test_transformer_persists_death_and_dedupes_provider_and_care_site():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        batch = SourceBatch(id="batch_domain_dedupe", filename="domain_dedupe.csv")
        db.add(batch)
        db.commit()

        raw = RawRecord(
            id="raw_domain_dedupe",
            batch_id="batch_domain_dedupe",
            row_data={
                "patient_id": "P300",
                "gender": "男",
                "chief_complaint": "胸痛",
                "daily_course_record": "李主任于心内科查看患者，抢救无效死亡。",
            },
        )
        db.add(raw)
        db.commit()

        mapping_config = {
            "person_source_value": "patient_id",
            "gender_source_value": "gender",
        }

        transformer = StagingTransformer(db, ner_mapper=DedupeNERMapper())
        transformer.transform_batch_to_person(batch_id="batch_domain_dedupe", mapping_config=mapping_config)

        assert db.query(StagingDeath).count() == 2
        assert db.query(StagingProvider).count() == 1
        assert db.query(StagingCareSite).count() == 1

        note_nlp_rows = db.query(StagingNoteNlp).all()
        assert len(note_nlp_rows) == 6
        assert {row.nlp_domain for row in note_nlp_rows} == {"death", "provider", "care_site"}
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)
