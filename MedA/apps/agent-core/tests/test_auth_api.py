from fastapi.testclient import TestClient

from app.main import app


def test_dev_login_creates_session_and_returns_context() -> None:
    client = TestClient(app)

    response = client.post(
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

    body = response.json()

    assert response.status_code == 200
    assert body["token"].startswith("meda_")
    assert body["user"]["user_id"] == "u-001"
    assert body["user"]["display_name"] == "Dr. Chen"
    assert body["organization"]["slug"] == "demo-hospital"
    assert body["role"] == "org_admin"
