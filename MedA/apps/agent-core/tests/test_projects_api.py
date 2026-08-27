from fastapi.testclient import TestClient

from app.main import app


def test_create_project_with_org_scope() -> None:
    client = TestClient(app)

    login = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "demo-hospital",
            "organization_name": "Demo Hospital",
            "user_id": "u-001",
            "display_name": "Dr. Chen",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    token = login.json()["token"]

    response = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
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
