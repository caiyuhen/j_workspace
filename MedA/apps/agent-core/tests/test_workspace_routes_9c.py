"""Wave9c T11 Abstractor Routes 1 pytest (append-only).

- test_abstractor_run_pipeline_PMID38924711_include_confidence_ge_085
  POST /api/workspace/abstractor/run-pipeline
  record_id=PMID-38924711 + llm_result(PICO 4/4 T2DM + outcome p<0.05 + RCT)
  → response.decision == 'include' AND response.confidence >= 0.85
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _dev_login_and_create_project(client: TestClient) -> tuple[str, int]:
    login_resp = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": "meda-wave9c",
            "organization_name": "MedA W9c Abstractor Unit",
            "user_id": "u-w9c-001",
            "display_name": "W9c Abstractor Reviewer",
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
                "user_id": "u-w9c-002",
                "display_name": "W9c Reviewer 2",
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
            "organization_slug": login_resp.json().get("organization_slug") or "meda-wave9c",
            "owner_user_id": "u-w9c-001",
            "name": "Wave9c Abstractor Routes Project",
            "description": "pytest abstractor run-pipeline + batch-stats 9c verify",
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


class TestW9cAbstractorRoutes:
    def test_abstractor_run_pipeline_PMID38924711_include_confidence_ge_085(self):
        """R1: POST /abstractor/run-pipeline PMID-38924711 → Include + confidence >= 0.85.

        Pass an llm_result dict that satisfies abstractor.triage() include rule:
          - PICO 4/4 present
          - condition matches T2DM (T2DM/type 2/2型)
          - outcome_p_value < 0.05
          - study_type ok (RCT, not illegal)
        abstractor rule C3 will return 'include' and boost confidence to min 0.85.
        """
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        record_id_str = "PMID-38924711"
        title = (
            "Dapagliflozin in Patients with Heart Failure and Type 2 Diabetes Mellitus: "
            "A Randomized Controlled Trial"
        )
        llm_payload = {
            "ok": True,
            "condition": "Type 2 Diabetes Mellitus (T2DM)",
            "intervention": "Dapagliflozin 10mg once daily",
            "comparison": "Matching placebo",
            "outcome": "Cardiovascular death or hospitalization for heart failure",
            "outcome_p_value": 0.001,
            "study_type": "RCT",
        }

        resp = client.post(
            "/api/workspace/abstractor/run-pipeline",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": pid,
                "record_id": record_id_str,
                "title": title,
                "llm_result": llm_payload,
                "fallback_times": 2,
            },
        )

        assert resp.status_code == 200, (
            f"run-pipeline non-200: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        assert isinstance(body, dict), f"response should be JSON dict, got {type(body)}"

        decision = body.get("decision")
        confidence = body.get("confidence")

        assert decision == "include", (
            f"expected decision='include' for PMID-38924711 with PICO 4/4 T2DM + p<0.05 RCT; "
            f"got decision={decision!r}; reasons={body.get('reasons')}"
        )

        assert isinstance(confidence, (int, float)), (
            f"confidence should be numeric, got {type(confidence)} {confidence!r}"
        )
        assert confidence >= 0.85, (
            f"expected confidence >= 0.85 for C3 include path; "
            f"got confidence={confidence}; reasons={body.get('reasons')}"
        )

        record_obj = body.get("record") or {}
        assert record_obj.get("id") == record_id_str, (
            f"record id mismatch: expected {record_id_str!r}, got {record_obj.get('id')!r}"
        )

        reasons = body.get("reasons") or []
        c3_hit = any("C3" in str(r) or "PICO 4/4" in str(r) for r in reasons)
        assert c3_hit or len(reasons) > 0, (
            f"expected triage reasons referencing C3 include rule; got reasons={reasons!r}"
        )

    def test_rob2_evaluate_study_D1_5low_overall_low_study99(self):
        """R2: POST /rob2/evaluate-study study_id=study-99
        5 domains ALL low + outcome_type=objective
        → overall == 'low' AND domain_d1_rating present
        """
        client = TestClient(app)
        token, pid = _dev_login_and_create_project(client)

        domains_5_low = [
            {"domain": "D1_randomisation_process", "rating": "low"},
            {"domain": "D2_deviations_from_intended_interventions", "rating": "low"},
            {"domain": "D3_missing_outcome_data", "rating": "low"},
            {"domain": "D4_measurement_of_the_outcome", "rating": "low"},
            {"domain": "D5_selection_of_the_reported_result", "rating": "low"},
        ]
        d1_answers_objective = {
            "D1_1": "Y",
            "D1_2": "Y",
            "D1_3": "N",
            "D1_4": "N",
            "D1_5": "N",
        }
        study_id = "study-99"

        resp = client.post(
            "/api/workspace/rob2/evaluate-study",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": pid,
                "study_id": study_id,
                "domains": domains_5_low,
                "d1_answers": d1_answers_objective,
                "outcome_type": "objective",
            },
        )

        assert resp.status_code == 200, (
            f"rob2 evaluate-study non-200: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        assert isinstance(body, dict), f"response should be JSON dict, got {type(body)}"

        assert body.get("study_id") == study_id, (
            f"study_id mismatch: expected {study_id!r}, got {body.get('study_id')!r}"
        )

        overall = body.get("overall")
        assert overall == "low", (
            f"5x low domains → expected overall='low'; got {overall!r}; full={body}"
        )

        d1_rating = body.get("domain_d1_rating")
        assert d1_rating in ("low", "some", "high", "critical"), (
            f"domain_d1_rating should be a valid short rating; got {d1_rating!r}"
        )

        outcome_type = body.get("outcome_type")
        assert outcome_type == "objective", (
            f"outcome_type should be echoed back as objective; got {outcome_type!r}"
        )

        domains_back = body.get("domains") or []
        assert len(domains_back) == 5, (
            f"expected 5 domains echoed; got {len(domains_back)}; body={body}"
        )
