from fastapi.testclient import TestClient

from app.main import app


def _login_and_create_project(client: TestClient) -> tuple[str, int]:
    login = client.post(
        "/api/auth/dev-login",
        json={
            "user_id": "files-tester",
            "display_name": "Files Tester",
            "organization_slug": "demo-hospital",
            "organization_name": "示范医院",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    assert login.status_code == 200, login.text
    token = login.json()["token"]

    created = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "files-tester",
            "name": "文件登记测试项目",
            "description": "for file register test",
        },
    )
    assert created.status_code == 201, created.text
    return token, int(created.json()["id"])


def test_register_file_and_artifact_metadata() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        "/api/files/register",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "project_id": project_id,
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


def test_register_file_requires_authentication() -> None:
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

    assert response.status_code == 401, response.text


def test_register_file_rejects_project_outside_organization() -> None:
    client = TestClient(app)
    _token, project_id = _login_and_create_project(client)

    other = client.post(
        "/api/auth/dev-login",
        json={
            "user_id": "outsider",
            "display_name": "Outsider",
            "organization_slug": "other-hospital",
            "organization_name": "其他医院",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    assert other.status_code == 200, other.text
    other_token = other.json()["token"]

    response = client.post(
        "/api/files/register",
        headers={"Authorization": f"Bearer {other_token}"},
        json={
            "project_id": project_id,
            "kind": "source_file",
            "name": "paper.pdf",
            "storage_path": "s3://meda-local/source/paper.pdf",
            "checksum": "abc123",
        },
    )

    assert response.status_code == 404, response.text
