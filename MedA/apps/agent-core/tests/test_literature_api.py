from fastapi.testclient import TestClient

from app.main import app

TWO_ENTRIES = """title: Metformin and cardiovascular outcomes
authors: Chen L, Wang H
journal: Lancet
year: 2023
doi: 10.1016/S2213-8587
pmid: 37123456
---
title: SGLT2 inhibitors in heart failure
authors: Zhang Y
journal: NEJM
year: 2022
doi: 10.1056/NEJMoa2201234
"""


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
            "description": "Wave 7 literature library",
        },
    )

    return token, project.json()["id"]


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_literature_library_starts_empty() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/literature",
        headers=_auth(token),
    )
    body = response.json()

    assert response.status_code == 200
    assert body["project"]["id"] == project_id
    assert body["stage_key"] == "search"
    assert body["records"] == []
    assert body["stats"]["total_count"] == 0
    assert body["stats"]["unique_count"] == 0
    assert body["stats"]["duplicate_count"] == 0
    assert body["recent_batches"] == []
    assert body["last_import_result"] is None
    assert [item["key"] for item in body["available_sources"]][0] == "pubmed"


def test_import_creates_records_and_batch() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "pubmed", "raw_text": TWO_ENTRIES},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["last_import_result"]["imported_count"] == 2
    assert body["last_import_result"]["duplicate_count"] == 0
    assert body["last_import_result"]["skipped_count"] == 0

    titles = [record["title"] for record in body["records"]]
    assert "Metformin and cardiovascular outcomes" in titles
    assert "SGLT2 inhibitors in heart failure" in titles

    first = next(
        record
        for record in body["records"]
        if record["title"] == "Metformin and cardiovascular outcomes"
    )
    assert first["authors"] == "Chen L, Wang H"
    assert first["journal"] == "Lancet"
    assert first["year"] == 2023
    assert first["doi"] == "10.1016/S2213-8587"
    assert first["pmid"] == "37123456"
    assert first["source_key"] == "pubmed"
    assert first["source_label"] == "PubMed"
    assert first["dedupe_status"] == "unique"
    assert first["duplicate_of_id"] is None
    assert "abstract" not in first

    assert body["stats"]["total_count"] == 2
    assert body["stats"]["unique_count"] == 2
    assert len(body["recent_batches"]) == 1
    assert body["recent_batches"][0]["parsed_count"] == 2


def test_import_accepts_entry_with_title_only() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "embase", "raw_text": "title: Minimal entry"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["last_import_result"]["imported_count"] == 1
    assert body["records"][0]["title"] == "Minimal entry"
    assert body["records"][0]["year"] is None
    assert body["records"][0]["doi"] == ""


def test_import_skips_blocks_without_title_and_keeps_the_rest() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    raw = """title: Good one
year: 2020
---
authors: Missing Title
year: 2021
---
title: Good two
year: 2019
"""

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "pubmed", "raw_text": raw},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["last_import_result"]["imported_count"] == 2
    assert body["last_import_result"]["skipped_count"] == 1
    assert body["stats"]["total_count"] == 2


def test_import_rejects_unparseable_text_with_422() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "pubmed", "raw_text": "nothing useful here"},
    )

    assert response.status_code == 422
    assert "解析" in response.json()["detail"] or "parse" in response.json()["detail"].lower()


def test_import_rejects_unknown_source_key_with_422() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "not-a-database", "raw_text": "title: Some paper"},
    )

    assert response.status_code == 422
    assert "not-a-database" in response.json()["detail"]


def test_create_record_manually() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/records",
        headers=_auth(token),
        json={
            "title": "Hand entered paper",
            "authors": "Liu M",
            "journal": "BMJ",
            "year": 2021,
            "doi": "10.1136/bmj.n1234",
            "pmid": "",
            "abstract": "Manually typed abstract.",
            "source_key": "cochrane",
        },
    )
    body = response.json()

    assert response.status_code == 200
    assert body["records"][0]["title"] == "Hand entered paper"
    assert body["records"][0]["source_label"] == "Cochrane Library"
    assert body["records"][0]["dedupe_status"] == "unique"
    assert body["stats"]["total_count"] == 1
    assert body["recent_batches"] == []
    assert body["last_import_result"] is None


def test_create_record_rejects_blank_title_with_422() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/records",
        headers=_auth(token),
        json={
            "title": "   ",
            "authors": "",
            "journal": "",
            "year": None,
            "doi": "",
            "pmid": "",
            "abstract": "",
            "source_key": "pubmed",
        },
    )

    assert response.status_code == 422


def test_literature_stats_group_by_source() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "pubmed", "raw_text": TWO_ENTRIES},
    )
    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": "cnki", "raw_text": "title: A Chinese study\nyear: 2020"},
    )

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/literature",
        headers=_auth(token),
    ).json()
    by_source = {item["source_key"]: item["count"] for item in body["stats"]["by_source"]}

    assert body["stats"]["total_count"] == 3
    assert by_source["pubmed"] == 2
    assert by_source["cnki"] == 1
    assert len(body["recent_batches"]) == 2


def test_literature_rejects_project_from_other_organization() -> None:
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

    response = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/literature",
        headers=_auth(other.json()["token"]),
    )

    assert response.status_code == 404


def test_stage_entry_points_literature_card_to_project_deep_page() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search",
        headers=_auth(token),
    ).json()
    card = next(item for item in body["entry_cards"] if item["key"] == "literature")

    assert card["title"] == "文献条目库"
    assert card["target"] == (
        f"/workspace/projects/{project_id}/stages/search/literature"
    )
