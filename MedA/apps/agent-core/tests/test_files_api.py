from fastapi.testclient import TestClient

from app.main import app


def test_register_file_and_artifact_metadata() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/files/register",
        json={
            "project_id": 1,
            "kind": "source_file",
            "name": "paper.pdf",
            "storage_path": "s3://meda-local/source/paper.pdf",
            "checksum": "abc123",
        },
    )

    body = response.json()

    assert response.status_code == 201
    assert body["kind"] == "source_file"
    assert body["name"] == "paper.pdf"
    assert body["storage_path"] == "s3://meda-local/source/paper.pdf"
