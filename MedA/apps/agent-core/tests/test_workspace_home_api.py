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
    # 新建项目没有任何落库记录，所以当前阶段停在第一个未完成阶段，且没有更新时间
    assert body["project"]["current_stage"] == "选题"
    assert body["project"]["updated_at_label"] == ""
    assert body["hero_cta"]["label"] == "继续上次研究"
    assert body["stages"][0]["key"] == "topic"
    assert all(stage["status"] == "pending" for stage in body["stages"])
    # 空态：没有任务/产物/活动/待办，不再用合成文案填充
    assert body["recent_tasks"] == []
    assert body["recent_artifacts"] == []
    assert body["activity"] == []
    assert body["todos"] == []
    assert body["assistant"]["headline"] == "MedA 助手建议"


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
