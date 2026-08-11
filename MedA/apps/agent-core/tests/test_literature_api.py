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


def _import(client: TestClient, token: str, project_id: int, raw: str, source: str = "pubmed"):
    return client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature/import",
        headers=_auth(token),
        json={"source_key": source, "raw_text": raw},
    ).json()


def test_same_doi_is_marked_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Original paper\ndoi: 10.1/abc")
    body = _import(
        client, token, project_id, "title: Different title\ndoi: 10.1/abc", "embase"
    )

    original = next(r for r in body["records"] if r["title"] == "Original paper")
    dup = next(r for r in body["records"] if r["title"] == "Different title")

    assert original["dedupe_status"] == "unique"
    assert dup["dedupe_status"] == "duplicate"
    assert dup["duplicate_of_id"] == original["id"]
    assert body["last_import_result"]["duplicate_count"] == 1
    assert body["stats"]["total_count"] == 2
    assert body["stats"]["unique_count"] == 1
    assert body["stats"]["duplicate_count"] == 1


def test_same_pmid_is_marked_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: First\npmid: 12345")
    body = _import(client, token, project_id, "title: Second\npmid: 12345", "embase")

    dup = next(r for r in body["records"] if r["title"] == "Second")
    original = next(r for r in body["records"] if r["title"] == "First")

    assert dup["dedupe_status"] == "duplicate"
    assert dup["duplicate_of_id"] == original["id"]


def test_normalized_title_with_same_year_is_marked_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Metformin in T2DM.\nyear: 2023")
    body = _import(
        client, token, project_id, "title: metformin in t2dm\nyear: 2023", "embase"
    )

    dup = next(r for r in body["records"] if r["title"] == "metformin in t2dm")

    assert dup["dedupe_status"] == "duplicate"
    assert body["stats"]["duplicate_count"] == 1


def test_same_title_with_different_year_is_not_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Shared title\nyear: 2020")
    body = _import(
        client, token, project_id, "title: Shared title\nyear: 2023", "embase"
    )

    assert body["stats"]["duplicate_count"] == 0
    assert body["stats"]["unique_count"] == 2


def test_same_title_with_one_unknown_year_is_not_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Shared title\nyear: 2020")
    body = _import(client, token, project_id, "title: Shared title", "embase")

    assert body["stats"]["duplicate_count"] == 0
    assert body["stats"]["unique_count"] == 2


def test_same_title_with_both_years_unknown_is_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: No year paper")
    body = _import(client, token, project_id, "title: No year paper", "embase")

    assert body["stats"]["duplicate_count"] == 1


def test_blank_doi_does_not_trigger_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Paper A\nyear: 2020")
    body = _import(client, token, project_id, "title: Paper B\nyear: 2021", "embase")

    assert body["stats"]["duplicate_count"] == 0


def test_blank_pmid_does_not_trigger_duplicate() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Paper C\nyear: 2020\npmid:")
    body = _import(
        client, token, project_id, "title: Paper D\nyear: 2021\npmid:", "embase"
    )

    assert body["stats"]["duplicate_count"] == 0


def test_duplicate_within_the_same_batch_is_detected() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    raw = """title: In batch original
doi: 10.9/xyz
---
title: In batch copy
doi: 10.9/xyz
"""
    body = _import(client, token, project_id, raw)

    original = next(r for r in body["records"] if r["title"] == "In batch original")
    dup = next(r for r in body["records"] if r["title"] == "In batch copy")

    assert original["dedupe_status"] == "unique"
    assert dup["dedupe_status"] == "duplicate"
    assert dup["duplicate_of_id"] == original["id"]
    assert body["last_import_result"]["duplicate_count"] == 1


def test_three_same_doi_records_all_point_to_the_first() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    raw = """title: First of three
doi: 10.7/dup
---
title: Second of three
doi: 10.7/dup
---
title: Third of three
doi: 10.7/dup
"""
    body = _import(client, token, project_id, raw)

    first = next(r for r in body["records"] if r["title"] == "First of three")
    second = next(r for r in body["records"] if r["title"] == "Second of three")
    third = next(r for r in body["records"] if r["title"] == "Third of three")

    assert first["dedupe_status"] == "unique"
    assert second["duplicate_of_id"] == first["id"]
    assert third["duplicate_of_id"] == first["id"]
    assert body["stats"]["duplicate_count"] == 2


def test_duplicates_are_not_deleted() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Kept original\ndoi: 10.5/keep")
    _import(client, token, project_id, "title: Kept copy\ndoi: 10.5/keep", "embase")

    body = client.get(
        f"/api/workspace/projects/{project_id}/stages/search/literature",
        headers=_auth(token),
    ).json()

    assert len(body["records"]) == 2
    assert body["stats"]["total_count"] == 2


def test_dedupe_does_not_cross_projects() -> None:
    client = TestClient(app)
    token, first_project_id = _login_and_create_project(client)

    second = client.post(
        "/api/projects",
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "第二个项目",
            "description": "cross project dedupe check",
        },
    )
    second_project_id = second.json()["id"]

    _import(client, token, first_project_id, "title: Shared across\ndoi: 10.3/cross")
    body = _import(client, token, second_project_id, "title: Shared across\ndoi: 10.3/cross")

    assert body["stats"]["duplicate_count"] == 0
    assert body["stats"]["unique_count"] == 1


def test_confirm_unique_clears_duplicate_marking() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Base paper\ndoi: 10.2/base")
    imported = _import(
        client, token, project_id, "title: Flagged paper\ndoi: 10.2/base", "embase"
    )
    dup_id = next(r for r in imported["records"] if r["title"] == "Flagged paper")["id"]

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature"
        f"/records/{dup_id}/confirm-unique",
        headers=_auth(token),
    )
    body = response.json()
    confirmed = next(r for r in body["records"] if r["id"] == dup_id)

    assert response.status_code == 200
    assert confirmed["dedupe_status"] == "confirmed_unique"
    assert confirmed["duplicate_of_id"] is None
    assert body["stats"]["unique_count"] == 2
    assert body["stats"]["duplicate_count"] == 0


def test_confirmed_unique_still_serves_as_dedupe_original() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    _import(client, token, project_id, "title: Anchor\ndoi: 10.4/anchor")
    imported = _import(
        client, token, project_id, "title: Rejected flag\ndoi: 10.4/anchor", "embase"
    )
    dup_id = next(r for r in imported["records"] if r["title"] == "Rejected flag")["id"]

    client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature"
        f"/records/{dup_id}/confirm-unique",
        headers=_auth(token),
    )

    body = _import(client, token, project_id, "title: Third copy\ndoi: 10.4/anchor", "cnki")
    third = next(r for r in body["records"] if r["title"] == "Third copy")

    assert third["dedupe_status"] == "duplicate"
    assert third["duplicate_of_id"] is not None


def test_confirm_unique_rejects_non_duplicate_record_with_422() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    imported = _import(client, token, project_id, "title: Plain unique paper")
    record_id = imported["records"][0]["id"]

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature"
        f"/records/{record_id}/confirm-unique",
        headers=_auth(token),
    )

    assert response.status_code == 422


def test_confirm_unique_rejects_unknown_record_with_404() -> None:
    client = TestClient(app)
    token, project_id = _login_and_create_project(client)

    response = client.post(
        f"/api/workspace/projects/{project_id}/stages/search/literature"
        "/records/99999/confirm-unique",
        headers=_auth(token),
    )

    assert response.status_code == 404
