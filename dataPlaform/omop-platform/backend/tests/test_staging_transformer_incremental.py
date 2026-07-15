from app.models.raw import RawRecord, SourceBatch
from app.models.staging import StagingPerson
from app.services.staging_transformer import StagingTransformer


class DummyNERMapper:
    def extract_entities_batch(self, texts, batch_size=16):
        return [{} for _ in texts]


class TrackingDeleteTransformer(StagingTransformer):
    def __init__(self, db, ner_mapper=None):
        super().__init__(db, ner_mapper=ner_mapper)
        self.delete_calls = []

    def _delete_existing_staging_rows(self, batch_id: str, business_key: str) -> None:
        self.delete_calls.append((batch_id, business_key))


def test_transformer_only_reads_changed_rows(db_session):
    batch = SourceBatch(id="batch_inc", filename="inc.csv", batch_type="incremental")
    db_session.add(batch)
    db_session.add_all(
        [
            RawRecord(
                id="raw_insert",
                batch_id=batch.id,
                row_data={"patient_id": "P1"},
                business_key="P1",
                change_type="insert",
            ),
            RawRecord(
                id="raw_unchanged",
                batch_id=batch.id,
                row_data={"patient_id": "P2"},
                business_key="P2",
                change_type="unchanged",
            ),
        ]
    )
    db_session.commit()

    transformer = StagingTransformer(db_session, ner_mapper=DummyNERMapper())
    transformer.transform_batch_to_person(
        batch_id=batch.id,
        mapping_config={"person_source_value": "patient_id"},
    )

    staged_people = (
        db_session.query(StagingPerson)
        .filter(StagingPerson.source_batch_id == batch.id)
        .order_by(StagingPerson.person_source_value.asc())
        .all()
    )
    assert [row.person_source_value for row in staged_people] == ["P1"]


def test_transformer_routes_delete_rows_to_cleanup_hook(db_session):
    batch = SourceBatch(id="batch_delete", filename="delete.csv", batch_type="incremental")
    db_session.add(batch)
    db_session.add(
        RawRecord(
            id="raw_delete",
            batch_id=batch.id,
            row_data={"patient_id": "P3"},
            business_key="P3",
            change_type="delete",
        )
    )
    db_session.commit()

    transformer = TrackingDeleteTransformer(db_session, ner_mapper=DummyNERMapper())
    transformer.transform_batch_to_person(
        batch_id=batch.id,
        mapping_config={"person_source_value": "patient_id"},
    )

    assert transformer.delete_calls == [(batch.id, "P3")]
    assert (
        db_session.query(StagingPerson)
        .filter(StagingPerson.source_batch_id == batch.id)
        .count()
        == 0
    )
