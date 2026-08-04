from fastapi.testclient import TestClient

from app.main import app


def test_stage_entry_returns_stage_specific_summary() -> None:
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

    project = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "Wave 4 stage entry",
        },
    )
    project_id = project.json()["id"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search",
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["stage_key"] == "search"
    assert body["stage_label"] == "检索"
    assert body["stage_goal"] == "完成检索式与来源配置"
    assert body["primary_action"]["label"] == "进入检索式管理"
    assert body["entry_cards"][0]["title"] == "检索式管理"
    assert body["assistant_suggestions"][0]["title"] == "补全数据库来源"
    assert body["guidance_notes"][0]["title"] == "输入要求"


def test_stage_entry_rejects_unknown_stage() -> None:
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

    project = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "Wave 4 invalid stage",
        },
    )
    project_id = project.json()["id"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/unknown",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "stage not found"


def test_stage_entry_supports_multiple_research_stages() -> None:
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

    project = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "Wave 4 stage coverage",
        },
    )
    project_id = project.json()["id"]

    topic_response = client.get(
        f"/api/workspace/projects/{project_id}/stages/topic",
        headers={"Authorization": f"Bearer {token}"},
    )
    output_response = client.get(
        f"/api/workspace/projects/{project_id}/stages/output",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert topic_response.status_code == 200
    assert topic_response.json()["stage_label"] == "选题"
    assert topic_response.json()["primary_action"]["label"] == "进入研究问题定义"

    assert output_response.status_code == 200
    assert output_response.json()["stage_label"] == "产出"
    assert output_response.json()["primary_action"]["label"] == "进入方案文档"
