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
        headers={"Authorization": f"Bearer {token}"},
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


def test_query_builder_rejects_invalid_query_id_with_404() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder"
        "?query_id=99999&version=v1",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_query_builder_rejects_invalid_version_with_404() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    initial = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder"
        f"?query_id={initial['query_id']}&version=v99",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404


def test_query_builder_save_rejects_unknown_query_with_404() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    initial = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query_id": 99999,
            "query_name": "糖尿病检索式",
            "selected_sources": initial["selected_sources"],
            "grouped_terms": initial["grouped_terms"],
            "expression_blocks": initial["expression_blocks"],
        },
    )

    assert response.status_code == 404


def test_query_builder_query_id_only_opens_that_query_draft() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    initial = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/save",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "query_id": initial["query_id"],
            "query_name": "糖尿病检索式",
            "selected_sources": initial["selected_sources"],
            "grouped_terms": initial["grouped_terms"],
            "expression_blocks": initial["expression_blocks"],
        },
    )

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder"
        f"?query_id={initial['query_id']}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["query_id"] == initial["query_id"]
    assert response.json()["query_mode"] == "draft"
    assert response.json()["query_name"] == "糖尿病检索式"

    missing = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder"
        "?query_id=99999",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert missing.status_code == 404


def test_derived_draft_keeps_version_anchor_after_reload() -> None:
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

    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder/derive-draft",
        headers={"Authorization": f"Bearer {token}"},
        json={"query_id": initial["query_id"], "version_label": "v1"},
    )

    reloaded = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert reloaded.status_code == 200
    assert reloaded.json()["query_mode"] == "draft"
    assert reloaded.json()["query_version"] == "v1"


def test_query_builder_reads_sources_from_project_config() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed", "cochrane", "cnki"],
            "search_fields": ["title", "abstract"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert body["selected_sources"] == ["PubMed", "Cochrane Library", "中国知网 CNKI"]
    assert body["preview_summary"]["status"] == "available"
    assert body["preview_summary"]["database_scope_summary"] == (
        "PubMed, Cochrane Library, 中国知网 CNKI"
    )


def test_query_builder_preview_degrades_when_no_sources_enabled() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": [],
            "search_fields": ["title"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    codes = [item["code"] for item in body["validation_messages"]]

    assert body["selected_sources"] == []
    assert body["preview_summary"]["status"] == "unavailable"
    assert body["preview_summary"]["database_scope_summary"] == "未选择数据库"
    assert "MISSING_SOURCE_CONFIG" in codes
    assert next(
        item["level"]
        for item in body["validation_messages"]
        if item["code"] == "MISSING_SOURCE_CONFIG"
    ) == "error"


def test_version_snapshot_keeps_its_own_sources_after_config_change() -> None:
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

    client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["wanfang"],
            "search_fields": ["title"],
            "year_from": None,
            "year_to": None,
            "languages": ["zh"],
        },
    )

    snapshot = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder"
        f"?query_id={initial['query_id']}&version=v1",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    current = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/query-builder",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert snapshot["query_mode"] == "snapshot"
    assert snapshot["selected_sources"] == ["PubMed", "Embase"]
    assert current["selected_sources"] == ["万方数据"]


def test_stage_entry_points_sources_card_to_project_deep_page() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    sources_card = next(
        card for card in body["entry_cards"] if card["key"] == "sources"
    )

    assert sources_card["target"] == (
        f"/workspace/projects/{project_id}/stages/search/sources"
    )
