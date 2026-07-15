from sqlalchemy import create_engine, text

from app.db.database import Base, ensure_sqlite_schema_compatibility


def _column_names(engine, table_name: str) -> list[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA table_info('{table_name}')")).fetchall()
    return [row[1] for row in rows]


def _index_names(engine, table_name: str) -> list[str]:
    with engine.connect() as conn:
        rows = conn.execute(text(f"PRAGMA index_list('{table_name}')")).fetchall()
    return [row[1] for row in rows]


def test_ensure_sqlite_schema_compatibility_adds_missing_staging_columns(tmp_path):
    import app.models.raw  # noqa: F401
    import app.models.incremental  # noqa: F401
    import app.models.staging  # noqa: F401

    db_path = tmp_path / "legacy_schema.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE stg_condition_occurrence (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_batch_id VARCHAR,
                    raw_record_id VARCHAR,
                    person_source_value VARCHAR,
                    condition_source_value VARCHAR,
                    condition_source_concept_id VARCHAR,
                    condition_start_date DATE,
                    condition_start_datetime DATETIME,
                    created_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE stg_note_nlp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_batch_id VARCHAR,
                    raw_record_id VARCHAR,
                    person_source_value VARCHAR,
                    section_source_value VARCHAR,
                    nlp_domain VARCHAR,
                    lexical_variant VARCHAR,
                    normalized_value VARCHAR,
                    term_exists VARCHAR,
                    created_at DATETIME
                )
                """
            )
        )

    assert "note_id" not in _column_names(engine, "stg_condition_occurrence")
    assert "source_layer" not in _column_names(engine, "stg_note_nlp")

    ensure_sqlite_schema_compatibility(engine, Base.metadata)

    condition_columns = _column_names(engine, "stg_condition_occurrence")
    note_nlp_columns = _column_names(engine, "stg_note_nlp")
    note_nlp_indexes = _index_names(engine, "stg_note_nlp")

    assert "note_id" in condition_columns
    assert "note_id" in note_nlp_columns
    assert "source_layer" in note_nlp_columns
    assert "negated" in note_nlp_columns
    assert "offset_start" in note_nlp_columns
    assert "offset_end" in note_nlp_columns
    assert "note_nlp_concept_id" in note_nlp_columns
    assert "ix_stg_note_nlp_note_id" in note_nlp_indexes


def test_ensure_sqlite_schema_compatibility_adds_incremental_columns_and_tables(tmp_path):
    import app.models.raw  # noqa: F401
    import app.models.incremental  # noqa: F401

    db_path = tmp_path / "legacy_incremental_schema.db"
    engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                CREATE TABLE source_batch (
                    id VARCHAR PRIMARY KEY,
                    filename VARCHAR,
                    total_rows INTEGER,
                    error_rows INTEGER,
                    status VARCHAR,
                    profiling_data JSON,
                    created_at DATETIME
                )
                """
            )
        )
        conn.execute(
            text(
                """
                CREATE TABLE raw_record (
                    id VARCHAR PRIMARY KEY,
                    batch_id VARCHAR,
                    row_data JSON,
                    created_at DATETIME
                )
                """
            )
        )

    assert "batch_type" not in _column_names(engine, "source_batch")
    assert "business_key" not in _column_names(engine, "raw_record")

    changes = ensure_sqlite_schema_compatibility(engine, Base.metadata)

    source_batch_columns = _column_names(engine, "source_batch")
    raw_record_columns = _column_names(engine, "raw_record")
    run_columns = _column_names(engine, "incremental_sync_run")
    summary_columns = _column_names(engine, "batch_analysis_summary")
    source_batch_indexes = _index_names(engine, "source_batch")
    raw_record_indexes = _index_names(engine, "raw_record")

    assert "source_batch.batch_type" in changes["columns_added"]
    assert "raw_record.business_key" in changes["columns_added"]
    assert "incremental_sync_run" in changes["tables_created"]
    assert "batch_analysis_summary" in changes["tables_created"]

    assert "batch_type" in source_batch_columns
    assert "dataset_name" in source_batch_columns
    assert "deleted_rows" in source_batch_columns
    assert "business_key" in raw_record_columns
    assert "record_hash" in raw_record_columns
    assert "change_type" in raw_record_columns
    assert "status" in run_columns
    assert "delete_count" in run_columns
    assert "processed_at" in summary_columns
    assert "deleted_rows" in summary_columns
    assert "ix_source_batch_batch_type" in source_batch_indexes
    assert "ix_raw_record_business_key" in raw_record_indexes
