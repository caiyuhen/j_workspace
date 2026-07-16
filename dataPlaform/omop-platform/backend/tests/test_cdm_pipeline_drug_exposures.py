from sqlalchemy import create_engine, text
from app.services.cdm_pipeline import CDMPipelineService


def test_process_db_stream_keeps_drugs_under_drug_exposures():
    engine = create_engine("sqlite:///:memory:")

    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE stg_person (
                person_source_value TEXT,
                raw_record_id TEXT,
                source_batch_id TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE raw_record (
                id TEXT,
                row_data TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE source_batch (
                id TEXT,
                filename TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE stg_visit_occurrence (
                person_source_value TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE stg_measurement (
                person_source_value TEXT,
                measurement_source_value TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE stg_condition_occurrence (
                person_source_value TEXT,
                condition_source_value TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE stg_drug_exposure (
                person_source_value TEXT,
                drug_source_value TEXT,
                form_source_value TEXT,
                route_source_value TEXT,
                dose_source_value TEXT,
                frequency_source_value TEXT,
                drug_exposure_start_date TEXT
            )
        """))
        conn.execute(text("""
            CREATE TABLE stg_observation (
                person_source_value TEXT,
                observation_source_value TEXT
            )
        """))

        conn.execute(text("""
            INSERT INTO stg_person (person_source_value, raw_record_id, source_batch_id)
            VALUES ('P001', 'raw1', 'batch1')
        """))
        conn.execute(text("""
            INSERT INTO raw_record (id, row_data)
            VALUES ('raw1', '{"patient_id":"P001","electronic_prescription":"氨氯地平片 5mg qd"}')
        """))
        conn.execute(text("""
            INSERT INTO source_batch (id, filename)
            VALUES ('batch1', 'drug.csv')
        """))
        conn.execute(text("""
            INSERT INTO stg_drug_exposure (
                person_source_value, drug_source_value, form_source_value, route_source_value,
                dose_source_value, frequency_source_value, drug_exposure_start_date
            )
            VALUES ('P001', '氨氯地平', '片', '口服', '5mg', 'qd', '2026-07-15')
        """))

    inserted_records = []

    class FakeMongoCollection:
        def insert_many(self, docs):
            inserted_records.extend(docs)

    service = CDMPipelineService()
    service._align_concept_for_dict = lambda item_dict, source_field, pg_conn: None

    with engine.connect() as conn:
        ok = service.process_db_stream(conn, pg_conn=None, mongo_collection=FakeMongoCollection())

    assert ok is True
    assert len(inserted_records) == 1
    record = inserted_records[0]
    assert "drug_exposures" in record
    assert "medications" not in record
    assert record["drug_exposures"] == [
        {
            "drug_source_value": "氨氯地平",
            "form_source_value": "片",
            "route_source_value": "口服",
            "dose_source_value": "5mg",
            "frequency_source_value": "qd",
            "drug_exposure_start_date": "2026-07-15",
        }
    ]
