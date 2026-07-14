from app.models.staging import StagingMeasurement, StagingPerson
from app.services.staging_transformer import StagingTransformer


class FakeDB:
    def __init__(self):
        self.saved_batches = []
        self.commit_calls = 0

    def bulk_save_objects(self, objects):
        self.saved_batches.append(list(objects))

    def commit(self):
        self.commit_calls += 1


def test_bulk_save_grouped_groups_objects_by_model_type():
    db = FakeDB()
    objects = [
        StagingPerson(person_source_value="P1"),
        StagingMeasurement(measurement_source_value="血糖"),
        StagingPerson(person_source_value="P2"),
    ]

    StagingTransformer._bulk_save_grouped(db, objects)

    assert len(db.saved_batches) == 2
    assert all(isinstance(item, StagingPerson) for item in db.saved_batches[0])
    assert all(isinstance(item, StagingMeasurement) for item in db.saved_batches[1])
    assert len(db.saved_batches[0]) == 2
    assert len(db.saved_batches[1]) == 1
    assert db.commit_calls == 1
