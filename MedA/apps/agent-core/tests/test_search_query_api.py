from fastapi.testclient import TestClient

from app.main import app


def _login_and_create_project(client: TestClient) -> tuple[str, int]:
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
            "description": "Wave 5 query builder",
        },
    )
    project_id = project.json()["id"]

    return token, project_id


def test_stage_entry_points_query_builder_to_project_deep_page() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert (
        response.json()["primary_action"]["target"]
        == f"/workspace/projects/{project_id}/stages/search/query-builder"
    )
    assert response.json()["entry_cards"][0]["target"] == (
        f"/workspace/projects/{project_id}/stages/search/query-builder"
    )


def test_query_builder_creates_default_draft_for_project() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    )

    body = response.json()

    assert response.status_code == 200
    assert body["project"]["id"] == project_id
    assert body["stage_key"] == "search"
    assert body["query_name"] == "检索式 1"
    assert body["query_mode"] == "draft"
    assert body["query_dirty"] is False
    assert body["query_version"] == "draft"
    assert body["selected_sources"] == ["PubMed", "Embase"]
    assert body["grouped_terms"][0]["group_key"] == "population"
    assert body["expression_blocks"][0]["block_type"] == "term"
    assert body["preview_summary"]["status"] == "available"
    assert body["preview_summary"]["database_scope_summary"] == "PubMed, Embase"


def test_query_builder_saves_draft_and_creates_version_snapshot() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    initial = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    save_response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query_id": initial["query_id"],
            "query_name": "糖尿病检索式",
            "selected_sources": ["PubMed", "Embase"],
            "grouped_terms": initial["grouped_terms"],
            "expression_blocks": initial["expression_blocks"],
        },
    )

    save_body = save_response.json()

    assert save_response.status_code == 200
    assert save_body["query_name"] == "糖尿病检索式"
    assert save_body["query_dirty"] is False

    version_response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/save-as-version",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query_id": initial["query_id"],
            "query_name": "糖尿病检索式",
            "selected_sources": ["PubMed", "Embase"],
            "grouped_terms": initial["grouped_terms"],
            "expression_blocks": initial["expression_blocks"],
        },
    )

    assert version_response.status_code == 200
    assert version_response.json()["query_version"] == "v1"
    assert version_response.json()["query_mode"] == "draft"


def test_query_builder_opens_snapshot_and_derives_new_draft() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    initial = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/save-as-version",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query_id": initial["query_id"],
            "query_name": initial["query_name"],
            "selected_sources": initial["selected_sources"],
            "grouped_terms": initial["grouped_terms"],
            "expression_blocks": initial["expression_blocks"],
        },
    )

    snapshot = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder?query_id={initial['query_id']}&version=v1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert snapshot.status_code == 200
    assert snapshot.json()["query_mode"] == "snapshot"
    assert snapshot.json()["query_version"] == "v1"

    derive = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/derive-draft",
        headers={"Authorization": f"Bearer {token}"},
        json={"query_id": initial["query_id"], "version_label": "v1"},
    )

    assert derive.status_code == 200
    assert derive.json()["query_mode"] == "draft"
    assert derive.json()["query_version"] == "v1"
