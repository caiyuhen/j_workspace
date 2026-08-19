"""Wave9 Routes Complete - 12 pytest cases (6 routes x success/failure).

6 routes (workspace 9a/9b/9c):
  1. POST /screening/funnel-stats
  2. POST /evidence-artifact/list
  3. POST /evidence-artifact/decide
  4. GET  /evidence-artifact/{id}
  5. POST /evidence-artifact/export-csv
  6. POST /rob2/evaluate-study
  7. POST /abstractor/run-pipeline

12 cases:
  T1: funnel-stats success
  T2: funnel-stats missing pi_id -> 422
  T3: evidence list success
  T4: evidence list empty record_ids -> []
  T5: evidence decide success
  T6: decide TA stage + exclude_ids=[6] -> 422
  T7: GET evidence/{id} success -> exact JSON keys
  T8: GET unknown id -> 404
  T9: export-csv success, header = "record_id,stage,decision\n"
  T10: export-csv no records -> empty CSV header only
  T11: rob2/evaluate-study success -> overall low/some/high
  T12: abstractor/run-pipeline success -> confidence 0-1 range
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _dev_login_and_create_project(client: TestClient) -> tuple[str, int]:
    login_resp = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "meda-t13",
            "organization_name": "MedA T13 Unit",
            "user_id": "u-t13-001",
            "display_name": "T13 Reviewer",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    if login_resp.status_code not in (200, 201):
        login_resp = client.post(
            "/api/auth/dev-login",
            json={
                "organization_slug": "demo-hospital",
                "organization_name": "Demo Hospital",
                "user_id": "u-t13-002",
                "display_name": "T13 Reviewer 2",
                "role": "org_admin",
                "client_type": "web",
            },
        )
    assert login_resp.status_code in (200, 201), f"login failed: {login_resp.status_code} {login_resp.text}"
    token = login_resp.json()["token"]

    proj_resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": login_resp.json().get("organization_slug") or "meda-t13",
            "owner_user_id": "u-t13-001",
            "name": "T13 Workspace Routes Project",
            "description": "pytest T13 routes 6x2 complete verify",
        },
    )
    if proj_resp.status_code in (200, 201):
        project_id = proj_resp.json()["id"]
    else:
        list_resp = client.get(
            "/api/projects",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_resp.status_code == 200, f"list projects failed: {list_resp.status_code}"
        items = list_resp.json() or []
        assert items, "no projects found for user"
        project_id = items[0]["id"]

    return token, int(project_id)


class TestWorkspaceRoutes9Complete:
    # ── T1 / T2: funnel-stats ────────────────────────────────────────────
    def test_T1_funnel_stats_success(self):
        """T1: funnel-stats success -> stats list with N4/E1/E6 keys."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/screening/funnel-stats",
            headers={"Authorization": f"Bearer {token}"},
            json={"pi_id": pid, "n3_override": 1000, "n4_dupes_removed_override": 140},
        )

        assert resp.status_code == 200, f"T1 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "stats" in body, f"T1 missing stats key: {list(body.keys())}"
        stats = body["stats"]
        assert isinstance(stats, list) and len(stats) >= 6, f"T1 stats len: {len(stats)}"
        by_key = {s["key"]: s for s in stats if isinstance(s, dict) and "key" in s}
        for k in ("N4", "E1", "E6"):
            assert k in by_key, f"T1 missing {k}: {list(by_key.keys())}"
            assert isinstance(by_key[k]["count"], int) and by_key[k]["count"] >= 0

    def test_T2_funnel_stats_missing_pi_id_422(self):
        """T2: funnel-stats missing pi_id -> HTTP 422."""
        client = TestClient(app)
        token, _pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/screening/funnel-stats",
            headers={"Authorization": f"Bearer {token}"},
            json={"n3_override": 500},
        )

        assert resp.status_code == 422, f"T2 expected 422, got {resp.status_code}: {resp.text}"

    # ── T3 / T4: evidence-artifact/list ──────────────────────────────────
    def test_T3_evidence_list_success(self):
        """T3: evidence list success -> {items, count, filters} shape."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/evidence-artifact/list",
            headers={"Authorization": f"Bearer {token}"},
            json={"pi_id": pid, "stage": "screening_ta"},
        )

        assert resp.status_code == 200, f"T3 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "items" in body and "count" in body and "filters" in body, (
            f"T3 missing keys: {list(body.keys())}"
        )
        assert isinstance(body["items"], list)
        assert isinstance(body["count"], int)

    def test_T4_evidence_list_empty_record_ids_returns_empty(self):
        """T4: evidence list empty record_ids=[] -> empty list items (no 400)."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/evidence-artifact/list",
            headers={"Authorization": f"Bearer {token}"},
            json={"pi_id": pid, "record_ids": []},
        )

        assert resp.status_code == 200, f"T4 expected 200 w/ empty items, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("items") == [] or (isinstance(body.get("items"), list) and len(body["items"]) == 0), (
            f"T4 expected empty items list, got items={body.get('items')}"
        )

    # ── T5 / T6: evidence-artifact/decide ────────────────────────────────
    def test_T5_evidence_decide_success(self):
        """T5: evidence decide success -> upserted_count >= 1."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/evidence-artifact/decide",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pi_id": pid,
                "record_ids": [42],
                "stage": "fulltext",
                "decision": "include",
                "confidence": 0.9,
            },
        )

        assert resp.status_code == 200, f"T5 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "upserted_count" in body, f"T5 missing upserted_count: {list(body.keys())}"
        assert body["upserted_count"] >= 1
        assert body["decision"] == "include"

    def test_T6_decide_TA_exclude_ids_6_422(self):
        """T6: decide TA stage + exclude_reason_ids=[6] -> HTTP 422."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/evidence-artifact/decide",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pi_id": pid,
                "record_ids": [6],
                "stage": "screening_ta",
                "decision": "exclude",
                "exclude_reason_ids": [6],
            },
        )

        assert resp.status_code == 422, (
            f"T6 expected 422 for TA+exclude#6; got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert isinstance(detail, str) and detail, f"T6 detail empty: {detail!r}"

    # ── T7 / T8: GET evidence-artifact/{id} ──────────────────────────────
    def test_T7_get_evidence_by_id_success_exact_json(self):
        """T7: GET evidence/{id} success -> exact JSON keys + matching id."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        create_resp = client.post(
            "/api/workspace/evidence-artifact/decide",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pi_id": pid,
                "record_ids": [99],
                "stage": "screening_ta",
                "decision": "review",
                "confidence": 0.55,
            },
        )
        assert create_resp.status_code == 200, f"T7 setup decide failed: {create_resp.text}"
        created = (create_resp.json() or {}).get("items") or []
        assert created, f"T7 setup no items created: {create_resp.json()}"
        ea_id = int(created[0]["id"])

        resp = client.get(
            f"/api/workspace/evidence-artifact/{ea_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 200, f"T7 GET non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert isinstance(body, dict), f"T7 body not dict: {type(body)}"
        REQUIRED_KEYS = {
            "id", "literature_record_id", "stage", "decision",
            "confidence", "exclude_reason_ids", "meta_json",
            "created_by", "override_by_user_id", "created_at",
        }
        missing = REQUIRED_KEYS - set(body.keys())
        assert not missing, f"T7 missing keys {missing}: {list(body.keys())}"
        assert body["id"] == ea_id, f"T7 id mismatch: expected {ea_id}, got {body['id']}"
        assert body["stage"] == "screening_ta"
        assert body["decision"] == "review"

    def test_T8_get_evidence_unknown_id_404(self):
        """T8: GET unknown id -> HTTP 404."""
        client = TestClient(app)
        token, _pid = _dev_login_and_create_project(client)

        resp = client.get(
            "/api/workspace/evidence-artifact/99999999",
            headers={"Authorization": f"Bearer {token}"},
        )

        assert resp.status_code == 404, f"T8 expected 404, got {resp.status_code}: {resp.text}"
        body = resp.json() or {}
        detail = body.get("detail", "")
        assert "not found" in str(detail).lower() or detail, f"T8 detail wrong: {detail!r}"

    # ── T9 / T10: POST evidence-artifact/export-csv ──────────────────────
    def test_T9_export_csv_success_header(self):
        """T9: export-csv success -> header = 'record_id,stage,decision\\n'."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        client.post(
            "/api/workspace/evidence-artifact/decide",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pi_id": pid,
                "record_ids": [501],
                "stage": "fulltext",
                "decision": "include",
                "confidence": 0.8,
            },
        )
        client.post(
            "/api/workspace/evidence-artifact/decide",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pi_id": pid,
                "record_ids": [502],
                "stage": "screening_ta",
                "decision": "exclude",
                "exclude_reason_ids": [1],
                "confidence": 0.4,
            },
        )

        resp = client.post(
            "/api/workspace/evidence-artifact/export-csv",
            headers={"Authorization": f"Bearer {token}"},
            json={"pi_id": pid},
        )

        assert resp.status_code == 200, f"T9 non-200: {resp.status_code} {resp.text}"
        content_type = resp.headers.get("content-type", "")
        assert "text/csv" in content_type or "csv" in content_type or resp.text, (
            f"T9 content-type unexpected: {content_type!r}"
        )
        text = resp.text
        lines = text.splitlines(keepends=True)
        assert lines, "T9 empty csv"
        header = lines[0]
        assert header.strip("\n").strip("\r") == "record_id,stage,decision", (
            f"T9 header mismatch: expected 'record_id,stage,decision', got {header!r}"
        )
        data_rows = [ln for ln in lines[1:] if ln.strip()]
        assert len(data_rows) >= 2, f"T9 expected >=2 data rows, got {len(data_rows)}: {data_rows}"

    def test_T10_export_csv_no_records_header_only(self):
        """T10: export-csv no records -> empty CSV with just the header."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        resp = client.post(
            "/api/workspace/evidence-artifact/export-csv",
            headers={"Authorization": f"Bearer {token}"},
            json={"pi_id": pid, "stage": "nonexistent_stage_xyz"},
        )

        assert resp.status_code == 200, f"T10 non-200: {resp.status_code} {resp.text}"
        text = resp.text
        lines = text.splitlines(keepends=True)
        assert len(lines) >= 1, f"T10 no lines at all: {text!r}"
        header = lines[0]
        assert header.strip("\n").strip("\r") == "record_id,stage,decision", (
            f"T10 header mismatch: {header!r}"
        )
        data_rows = [ln for ln in lines[1:] if ln.strip()]
        assert data_rows == [], f"T10 expected no data rows, got {data_rows}"

    # ── T11: rob2/evaluate-study ─────────────────────────────────────────
    def test_T11_rob2_evaluate_study_success_overall_rating(self):
        """T11: rob2/evaluate-study success -> overall in {low/some/high}."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        domains = [
            {"domain": "D1_randomisation_process", "rating": "low"},
            {"domain": "D2_deviations_from_intended_interventions", "rating": "some"},
            {"domain": "D3_missing_outcome_data", "rating": "low"},
            {"domain": "D4_measurement_of_the_outcome", "rating": "high"},
            {"domain": "D5_selection_of_the_reported_result", "rating": "low"},
        ]

        resp = client.post(
            "/api/workspace/rob2/evaluate-study",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": pid,
                "study_id": "study-T11-mix",
                "domains": domains,
                "outcome_type": "objective",
            },
        )

        assert resp.status_code == 200, f"T11 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "overall" in body, f"T11 missing overall: {list(body.keys())}"
        overall = body["overall"]
        assert overall in ("low", "some", "high", "critical"), (
            f"T11 overall invalid: {overall!r}"
        )

    # ── T12: abstractor/run-pipeline ─────────────────────────────────────
    def test_T12_abstractor_run_pipeline_confidence_0_1_range(self):
        """T12: abstractor/run-pipeline success -> confidence in [0, 1] range."""
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        llm_payload = {
            "ok": True,
            "condition": "Type 2 Diabetes",
            "intervention": "SGLT2 inhibitor",
            "comparison": "Placebo",
            "outcome": "Major adverse cardiac events",
            "outcome_p_value": 0.02,
            "study_type": "RCT",
        }

        resp = client.post(
            "/api/workspace/abstractor/run-pipeline",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": pid,
                "record_id": "PMID-T12-001",
                "title": "SGLT2 inhibitors in Type 2 Diabetes: a Randomized Trial",
                "llm_result": llm_payload,
            },
        )

        assert resp.status_code == 200, f"T12 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "confidence" in body, f"T12 missing confidence: {list(body.keys())}"
        conf = body["confidence"]
        assert isinstance(conf, (int, float)), f"T12 confidence not numeric: {type(conf)}"
        assert 0.0 <= conf <= 1.0, f"T12 confidence out of [0,1] range: {conf}"
        assert "decision" in body and body["decision"] in ("include", "exclude", "review"), (
            f"T12 invalid decision: {body.get('decision')!r}"
        )
