from fastapi.testclient import TestClient

from app.main import app


def test_project_list_requires_session_and_returns_org_scoped_projects() -> None:
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

    client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "Wave 2 auth workspace test",
        },
    )

    unauthorized = client.get("/api/projects")
    authorized = client.get(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json()[0]["workspace_key"] == "demo-hospital/糖尿病真实世界研究"
