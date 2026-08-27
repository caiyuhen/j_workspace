from fastapi.testclient import TestClient
from sqlmodel import Session

from app.db import engine
from app.models import ArtifactRecord, ResearchTaskRecord
from app.main import app


def test_workspace_home_returns_project_scoped_summary() -> None:
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
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "糖尿病真实世界研究",
            "description": "Wave 3 workspace summary",
        },
    )
    project_id = project.json()["id"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/home",
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["project"]["id"] == project_id
    assert body["project"]["name"] == "糖尿病真实世界研究"
    assert body["project"]["current_stage"] == "方案设计"
    assert body["hero_cta"]["label"] == "继续上次研究"
    assert body["stages"][0]["key"] == "topic"
    assert body["recent_tasks"][0]["title"] == "完善纳排标准草案"
    assert body["recent_artifacts"][0]["title"] == "方案初稿 v0.3"
    assert body["assistant"]["headline"] == "MedA 助手建议"
    assert body["todos"][0]["title"] == "确认研究终点定义"


def test_workspace_home_prefers_project_records_when_available() -> None:
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
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "肿瘤队列研究",
            "description": "Persisted workspace summary",
        },
    )
    project_id = project.json()["id"]

    with Session(engine) as session:
        session.add(
            ResearchTaskRecord(
                project_id=project_id,
                title="整理真实随访口径",
                stage_key="analysis",
                status="in_progress",
            )
        )
        session.add(
            ArtifactRecord(
                project_id=project_id,
                artifact_type="analysis_output",
                title="分析摘要 v1.0",
            )
        )
        session.commit()

    response = client.get(
        f"/api/workspace/projects/{project_id}/home",
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["recent_tasks"][0]["title"] == "整理真实随访口径"
    assert body["recent_artifacts"][0]["title"] == "分析摘要 v1.0"
