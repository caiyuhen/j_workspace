from fastapi.testclient import TestClient

from app.main import app
from app.services.source_catalog import (
    LANGUAGE_OPTIONS,
    SEARCH_FIELD_OPTIONS,
    SOURCE_CATALOG,
    source_labels_for_keys,
)


def test_source_catalog_contains_six_medical_databases() -> None:
    keys = [item.key for item in SOURCE_CATALOG]

    assert keys == ["pubmed", "embase", "cochrane", "wos", "cnki", "wanfang"]
    assert all(item.label for item in SOURCE_CATALOG)
    assert all(item.description for item in SOURCE_CATALOG)


def test_source_catalog_marks_full_text_support() -> None:
    support = {item.key: item.supports_full_text for item in SOURCE_CATALOG}

    assert support["pubmed"] is False
    assert support["cochrane"] is True
    assert support["cnki"] is True


def test_search_field_and_language_options_are_defined() -> None:
    assert [item.key for item in SEARCH_FIELD_OPTIONS] == [
        "title",
        "abstract",
        "keyword",
        "mesh",
        "full_text",
    ]
    assert [item.key for item in LANGUAGE_OPTIONS] == ["en", "zh"]


def test_source_labels_for_keys_maps_keys_to_display_labels() -> None:
    assert source_labels_for_keys(["pubmed", "embase"]) == ["PubMed", "Embase"]


def test_source_labels_for_keys_preserves_catalog_order() -> None:
    assert source_labels_for_keys(["cnki", "pubmed"]) == ["PubMed", "中国知网 CNKI"]


def test_source_labels_for_keys_ignores_unknown_keys() -> None:
    assert source_labels_for_keys(["pubmed", "nope"]) == ["PubMed"]


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
            "description": "Wave 6 source config",
        },
    )

    return token, project.json()["id"]


def test_source_catalog_endpoint_returns_options() -> None:
    client = TestClient(app)
    token, _ = _login_and_create_project(client)

    response = client.get(
        "/api/workspace/sources/catalog",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200
    assert [item["key"] for item in body["available_sources"]] == [
        "pubmed",
        "embase",
        "cochrane",
        "wos",
        "cnki",
        "wanfang",
    ]
    assert body["available_sources"][0]["label"] == "PubMed"
    assert body["available_sources"][0]["supports_full_text"] is False
    assert [item["key"] for item in body["search_field_options"]] == [
        "title",
        "abstract",
        "keyword",
        "mesh",
        "full_text",
    ]
    assert [item["key"] for item in body["language_options"]] == ["en", "zh"]


def test_source_config_creates_default_on_first_read() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["project"]["id"] == project_id
    assert body["stage_key"] == "search"
    assert body["enabled_source_keys"] == ["pubmed", "embase"]
    assert body["search_fields"] == ["title", "abstract"]
    assert body["year_from"] is None
    assert body["year_to"] is None
    assert body["languages"] == ["en"]
    assert "config_dirty" not in body
    assert body["impact_summary"]["enabled_count"] == 2
    assert body["validation_messages"] == []

    enabled = {item["key"]: item["enabled"] for item in body["available_sources"]}
    assert enabled["pubmed"] is True
    assert enabled["cochrane"] is False


def test_source_config_saves_and_persists() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
    )

    saved = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed", "cochrane", "cnki"],
            "search_fields": ["title", "abstract", "mesh"],
            "year_from": 2015,
            "year_to": 2025,
            "languages": ["en", "zh"],
        },
    )
    body = saved.json()

    assert saved.status_code == 200
    assert body["enabled_source_keys"] == ["pubmed", "cochrane", "cnki"]
    assert body["year_from"] == 2015
    assert body["impact_summary"]["enabled_count"] == 3

    reread = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert reread["enabled_source_keys"] == ["pubmed", "cochrane", "cnki"]
    assert reread["search_fields"] == ["title", "abstract", "mesh"]
    assert reread["year_to"] == 2025
    assert reread["languages"] == ["en", "zh"]


def test_source_config_rejects_unknown_source_key() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed", "not-a-database"],
            "search_fields": ["title"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )

    assert response.status_code == 422
    assert "not-a-database" in response.json()["detail"]


def test_source_config_rejects_unknown_search_field() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed"],
            "search_fields": ["title", "nope"],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )

    assert response.status_code == 422
    assert "nope" in response.json()["detail"]


def test_source_config_rejects_inverted_year_range() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed"],
            "search_fields": ["title"],
            "year_from": 2025,
            "year_to": 2015,
            "languages": ["en"],
        },
    )

    assert response.status_code == 422
    assert "year" in response.json()["detail"].lower()


def test_source_config_rejects_project_from_other_organization() -> None:
    client = TestClient(app)
    _, project_id = _login_and_create_project(client)

    other = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "other-hospital",
            "organization_name": "Other Hospital",
            "user_id": "u-002",
            "display_name": "Dr. Li",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    other_token = other.json()["token"]

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert response.status_code == 404


def test_source_config_flags_missing_sources() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
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
    body = response.json()
    codes = [item["code"] for item in body["validation_messages"]]

    assert response.status_code == 200
    assert body["impact_summary"]["enabled_count"] == 0
    assert "MISSING_SOURCE_CONFIG" in codes
    assert next(
        item["level"]
        for item in body["validation_messages"]
        if item["code"] == "MISSING_SOURCE_CONFIG"
    ) == "error"


def test_source_config_warns_on_empty_search_fields() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed"],
            "search_fields": [],
            "year_from": None,
            "year_to": None,
            "languages": ["en"],
        },
    )
    codes = [item["code"] for item in response.json()["validation_messages"]]

    assert response.status_code == 200
    assert "EMPTY_SEARCH_FIELDS" in codes


def test_source_config_notes_narrow_year_range() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.put(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "enabled_source_keys": ["pubmed"],
            "search_fields": ["title"],
            "year_from": 2024,
            "year_to": 2025,
            "languages": ["en"],
        },
    )
    codes = [item["code"] for item in response.json()["validation_messages"]]

    assert response.status_code == 200
    assert "NARROW_YEAR_RANGE" in codes


def test_source_config_keeps_single_row_per_project_stage() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    for _ in range(3):
        client.get(
            f"/api/workspace/projects/{project_id}/stages/search/sources",
            headers={"Authorization": f"Bearer {token}"},
        )
        client.put(
            f"/api/workspace/projects/{project_id}/stages/search/sources",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "enabled_source_keys": ["pubmed"],
                "search_fields": ["title"],
                "year_from": None,
                "year_to": None,
                "languages": ["en"],
            },
        )

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/sources",
        headers={"Authorization": f"Bearer {token}"},
    ).json()

    assert body["enabled_source_keys"] == ["pubmed"]
    assert "config_dirty" not in body
