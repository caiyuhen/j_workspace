from fastapi.testclient import TestClient

from app.main import app
from app.services.events import EventBroker


def _dev_login(client: TestClient, user_id: str, role: str) -> str:
    response = client.post(
        "/api/auth/dev-login",
        json={
            "user_id": user_id,
            "display_name": user_id,
            "organization_slug": "demo-hospital",
            "organization_name": "示范医院",
            "role": role,
            "client_type": "web",
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["token"]


def test_project_creation_publishes_event() -> None:
    broker = EventBroker()

    broker.publish("project.created", {"workspace_key": "demo-hospital/糖尿病真实世界研究"})

    assert broker.drain() == [
        {
            "event_type": "project.created",
            "payload": {"workspace_key": "demo-hospital/糖尿病真实世界研究"},
        }
    ]


def test_drain_events_requires_authentication() -> None:
    client = TestClient(app)

    response = client.get("/api/events/drain")

    assert response.status_code == 401, response.text


def test_drain_events_rejects_non_admin_role() -> None:
    client = TestClient(app)
    token = _dev_login(client, "plain-member", "pi")

    response = client.get(
        "/api/events/drain",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403, response.text
    assert (response.json() or {}).get("detail") == "admin role required"


def test_drain_events_allows_admin_role() -> None:
    client = TestClient(app)
    token = _dev_login(client, "org-admin-user", "org_admin")

    response = client.get(
        "/api/events/drain",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200, response.text
    assert isinstance(response.json()["events"], list)
