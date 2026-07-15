from datetime import datetime, timedelta

from app.services.incremental_sync import IncrementalSyncService


def test_classify_change_prefers_delete_flag():
    svc = IncrementalSyncService(db=None)

    change_type = svc.classify_change(
        incoming={"business_key": "p1", "op_flag": "delete", "record_hash": "new"},
        current_snapshot={"business_key": "p1", "record_hash": "old", "source_version": "1"},
        window_start=datetime.utcnow() - timedelta(hours=1),
        window_end=datetime.utcnow(),
    )

    assert change_type == "delete"


def test_classify_change_marks_insert_when_key_missing_in_snapshot():
    svc = IncrementalSyncService(db=None)

    change_type = svc.classify_change(
        incoming={
            "business_key": "p2",
            "source_updated_at": datetime(2026, 7, 15, 10, 0, 0),
            "record_hash": "abc",
        },
        current_snapshot=None,
        window_start=datetime(2026, 7, 15, 9, 0, 0),
        window_end=datetime(2026, 7, 15, 11, 0, 0),
    )

    assert change_type == "insert"


def test_classify_change_marks_update_when_version_changes():
    svc = IncrementalSyncService(db=None)

    change_type = svc.classify_change(
        incoming={
            "business_key": "p3",
            "source_updated_at": datetime(2026, 7, 15, 10, 0, 0),
            "source_version": "2",
            "record_hash": "same",
        },
        current_snapshot={
            "business_key": "p3",
            "source_updated_at": datetime(2026, 7, 15, 9, 30, 0),
            "source_version": "1",
            "record_hash": "same",
        },
        window_start=datetime(2026, 7, 15, 9, 0, 0),
        window_end=datetime(2026, 7, 15, 11, 0, 0),
    )

    assert change_type == "update"


def test_classify_change_marks_update_when_hash_changes_in_window():
    svc = IncrementalSyncService(db=None)

    change_type = svc.classify_change(
        incoming={
            "business_key": "p4",
            "source_updated_at": datetime(2026, 7, 15, 10, 0, 0),
            "source_version": "1",
            "record_hash": "new",
        },
        current_snapshot={
            "business_key": "p4",
            "source_updated_at": datetime(2026, 7, 15, 9, 30, 0),
            "source_version": "1",
            "record_hash": "old",
        },
        window_start=datetime(2026, 7, 15, 9, 0, 0),
        window_end=datetime(2026, 7, 15, 11, 0, 0),
    )

    assert change_type == "update"


def test_classify_change_marks_unchanged_when_hash_matches():
    svc = IncrementalSyncService(db=None)

    change_type = svc.classify_change(
        incoming={
            "business_key": "p5",
            "source_updated_at": datetime(2026, 7, 15, 10, 0, 0),
            "source_version": "1",
            "record_hash": "same",
        },
        current_snapshot={
            "business_key": "p5",
            "source_updated_at": datetime(2026, 7, 15, 9, 30, 0),
            "source_version": "1",
            "record_hash": "same",
        },
        window_start=datetime(2026, 7, 15, 9, 0, 0),
        window_end=datetime(2026, 7, 15, 11, 0, 0),
    )

    assert change_type == "unchanged"
