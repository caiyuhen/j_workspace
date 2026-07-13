import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.raw import RawRecord, SourceBatch
from app.models.staging import StagingPerson
from app.services.staging_transformer import StagingTransformer


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    import app.models.raw
    import app.models.staging

    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


def test_transform_raw_to_person_staging(db_session):
    batch = SourceBatch(id="batch_1", filename="test.csv")
    db_session.add(batch)
    db_session.commit()

    raw_1 = RawRecord(
        id="raw_1",
        batch_id="batch_1",
        row_data={
            "patient_id": "P001",
            "gender": "男",
            "birth_date": "1990-05-15",
            "empty_field": "NA",
        },
    )
    raw_2 = RawRecord(
        id="raw_2",
        batch_id="batch_1",
        row_data={
            "patient_id": "P002",
            "gender": "Female",
            "birth_date": "1985/12/31",
            "empty_field": "",
        },
    )
    db_session.add_all([raw_1, raw_2])
    db_session.commit()

    mapping_config = {
        "person_source_value": "patient_id",
        "gender_source_value": "gender",
        "birth_datetime": "birth_date",
    }

    transformer = StagingTransformer(db_session)
    transformer.transform_batch_to_person(batch_id="batch_1", mapping_config=mapping_config)

    staging_persons = db_session.query(StagingPerson).order_by(StagingPerson.person_source_value).all()

    assert len(staging_persons) == 2

    p1 = staging_persons[0]
    assert p1.person_source_value == "P001"
    assert p1.raw_record_id == "raw_1"
    assert p1.source_batch_id == "batch_1"
    assert p1.gender_source_value == "男"
    assert p1.gender_concept_id == 8507
    assert p1.year_of_birth == 1990
    assert p1.month_of_birth == 5
    assert p1.day_of_birth == 15

    p2 = staging_persons[1]
    assert p2.person_source_value == "P002"
    assert p2.gender_concept_id == 8532
    assert p2.year_of_birth == 1985
    assert p2.month_of_birth == 12
    assert p2.day_of_birth == 31
