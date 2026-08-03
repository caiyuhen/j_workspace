from fastapi.testclient import TestClient

from app.main import app


def test_create_project_with_org_scope() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "首个平台底座联调用例",
        },
    )

    body = response.json()

    assert response.status_code == 201
    assert body["organization_slug"] == "demo-hospital"
    assert body["owner_user_id"] == "u-001"
    assert body["name"] == "糖尿病真实世界研究"
    assert body["workspace_key"] == "demo-hospital/糖尿病真实世界研究"
