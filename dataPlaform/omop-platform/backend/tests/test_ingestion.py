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

@pytest.fixture(autouse=True, scope="module")
def setup_db_module():
    import app.models.raw
    DBBase.metadata.create_all(bind=engine)
    main_app.dependency_overrides[get_db] = override_get_db
    yield
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
    file_path.write_text("id,name,age\n1,Alice,30\n2,Bob,25\n3,Charlie", encoding="utf-8")
    
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
    file_path.write_text("id,name,age\n1,Alice,30\n2,Bob,25\n3,Charlie", encoding="utf-8")
    
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

