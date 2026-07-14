from app.models import staging


def test_staging_metadata_includes_new_omop_nlp_tables():
    expected_tables = {
        "stg_procedure_occurrence",
        "stg_note",
        "stg_note_nlp",
        "stg_specimen",
        "stg_device_exposure",
        "stg_death",
        "stg_provider",
        "stg_care_site",
    }

    metadata_tables = set(staging.Base.metadata.tables.keys())

    assert expected_tables.issubset(metadata_tables)


def test_staging_note_nlp_includes_traceability_columns():
    columns = staging.StagingNoteNlp.__table__.columns.keys()

    assert "source_layer" in columns
    assert "negated" in columns
