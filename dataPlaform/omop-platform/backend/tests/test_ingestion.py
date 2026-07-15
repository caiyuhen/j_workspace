import os
from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, get_db
from app.models.raw import SourceBatch, RawRecord, ErrorRecord
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
from app.db.database import Base as DBBase
from app.main import app as main_app
from app.api import ingestion as ingestion_api

# Use a static file DB so it persists across requests within a test run if needed
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ingestion.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

client = TestClient(main_app)


def _noop_process_csv_task(tmp_path: str, filename: str, batch_id: str):
    return None

@pytest.fixture(autouse=True, scope="module")
def setup_db_module():
    import app.models.raw
    DBBase.metadata.create_all(bind=engine)
    main_app.dependency_overrides[get_db] = override_get_db
    original_session_local = ingestion_api.SessionLocal
    original_process_csv_task = ingestion_api.process_csv_task
    ingestion_api.SessionLocal = TestingSessionLocal
    ingestion_api.process_csv_task = _noop_process_csv_task
    yield
    ingestion_api.SessionLocal = original_session_local
    ingestion_api.process_csv_task = original_process_csv_task
    DBBase.metadata.drop_all(bind=engine)
    engine.dispose()
    main_app.dependency_overrides.clear()
    import os
    if os.path.exists("./test_ingestion.db"):
        try:
            os.remove("./test_ingestion.db")
        except PermissionError:
            pass

def test_upload_csv_file(tmp_path):
    # Create a valid CSV file
    file_path = tmp_path / "test_upload.csv"
    file_path.write_text(
        "id,name,age,gender,phone\n1,Alice,30,F,13800138000\n2,Bob,25,M,13800138001\n3,Charlie,40,M,13800138002\n",
        encoding="utf-8",
    )
    
    with open(file_path, "rb") as f:
        response = client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("test_upload.csv", f, "text/csv")}
        )
        
    assert response.status_code == 200
    data = response.json()
    assert "batch_id" in data
    assert data["filename"] == "test_upload.csv"
    assert "message" in data

def test_list_batches(tmp_path):
    # Need to upload first because tests might run in isolation depending on pytest setup
    file_path = tmp_path / "test_upload_list.csv"
    file_path.write_text(
        "id,name,age,gender,phone\n1,Alice,30,F,13800138000\n2,Bob,25,M,13800138001\n3,Charlie,40,M,13800138002\n",
        encoding="utf-8",
    )
    
    with open(file_path, "rb") as f:
        res = client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("test_upload_list.csv", f, "text/csv")}
        )
        assert res.status_code == 200

    response = client.get("/api/v1/ingestion/batches")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["filename"] == "test_upload_list.csv"
    assert "status" in data[0]
    assert data[0]["status"] in ["processing", "completed"]


def test_replay_endpoint_creates_incremental_batch():
    response = client.post(
        "/api/v1/ingestion/replay",
        json={
            "dataset_name": "ingestion",
            "trigger_mode": "manual",
            "window_start": "2026-07-15T09:00:00",
            "window_end": "2026-07-15T11:00:00",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["batch_id"]
    assert payload["batch_type"] == "replay"
    assert payload["dataset_name"] == "ingestion"
    assert payload["trigger_mode"] == "manual"
    assert payload["window_start"] == "2026-07-15T09:00:00"
    assert payload["window_end"] == "2026-07-15T11:00:00"
    assert payload["status"] in ["processing", "completed"]


def test_list_batches_includes_incremental_metadata(tmp_path):
    file_path = tmp_path / "test_upload_incremental.csv"
    file_path.write_text(
        "id,name,age,gender,phone\n1,Alice,30,F,13800138000\n",
        encoding="utf-8",
    )

    with open(file_path, "rb") as f:
        upload_response = client.post(
            "/api/v1/ingestion/upload",
            files={"file": ("test_upload_incremental.csv", f, "text/csv")},
        )

    assert upload_response.status_code == 200
    upload_batch_id = upload_response.json()["batch_id"]

    replay_response = client.post(
        "/api/v1/ingestion/replay",
        json={
            "dataset_name": "ingestion",
            "trigger_mode": "manual",
            "window_start": "2026-07-15T09:00:00",
            "window_end": "2026-07-15T11:00:00",
        },
    )
    assert replay_response.status_code == 200
    replay_batch_id = replay_response.json()["batch_id"]

    response = client.get("/api/v1/ingestion/batches")
    assert response.status_code == 200

    items = {item["id"]: item for item in response.json()}
    upload_batch = items[upload_batch_id]
    replay_batch = items[replay_batch_id]

    assert upload_batch["batch_type"] == "full"
    assert upload_batch["dataset_name"] == "ingestion"
    assert upload_batch["trigger_mode"] == "auto"
    assert upload_batch["window_start"] is None
    assert upload_batch["window_end"] is None
    assert upload_batch["inserted_rows"] >= 0
    assert upload_batch["updated_rows"] >= 0
    assert upload_batch["deleted_rows"] >= 0
    assert upload_batch["unchanged_rows"] >= 0

    assert replay_batch["batch_type"] == "replay"
    assert replay_batch["dataset_name"] == "ingestion"
    assert replay_batch["trigger_mode"] == "manual"
    assert replay_batch["window_start"] == "2026-07-15T09:00:00"
    assert replay_batch["window_end"] == "2026-07-15T11:00:00"
    assert replay_batch["inserted_rows"] == 0
    assert replay_batch["updated_rows"] == 0
    assert replay_batch["deleted_rows"] == 0
    assert replay_batch["unchanged_rows"] == 0
