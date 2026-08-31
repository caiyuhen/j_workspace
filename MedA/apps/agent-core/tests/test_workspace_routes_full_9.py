"""Task 13: 6 routes × 2 pytest (success+failure) = 12 tests RED→GREEN full.

Routes covered:
  R1 POST /evidence-artifact/list          (2 tests)
  R2 GET  /evidence-artifact/{id}          (2 tests)
  R3 POST /evidence-artifact/decide         (2 tests)
  R4 POST /screening/funnel-stats           (2 tests)
  R5 POST /rob2/evaluate-study              (2 tests)
  R6 POST /abstractor/run-pipeline          (2 tests)
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.db import engine
from app.models import (
    EvidenceArtifact,
    LiteratureRecord,
    Organization,
    ResearchProject,
    User,
)


def _dev_login(client: TestClient, org_slug: str, org_name: str, user_id: str) -> str:
    resp = client.post(
        "/api/auth/dev-login",
        json={
            "organization_slug": org_slug,
            "organization_name": org_name,
            "user_id": user_id,
            "display_name": f"User {user_id}",
            "role": "org_admin",
            "client_type": "web",
        },
    )
    assert resp.status_code in (200, 201), f"login failed: {resp.status_code} {resp.text}"
    return resp.json()["token"]


def _create_project(
    client: TestClient, token: str, org_slug: str, owner_uid: str, name: str
) -> int:
    resp = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": org_slug,
            "owner_user_id": owner_uid,
            "name": name,
            "description": "T13 routes pytest",
        },
    )
    if resp.status_code in (200, 201):
        return int(resp.json()["id"])
    list_resp = client.get(
        "/api/projects", headers={"Authorization": f"Bearer {token}"}
    )
    assert list_resp.status_code == 200
    items = list_resp.json() or []
    assert items
    return int(items[0]["id"])


def _create_two_ea_records(pid: int, session: Session) -> tuple[int, int]:
    """Insert 2 EvidenceArtifact rows for project pid (stage=screening_ta).
    Returns the two ea ids (for R2 test) and also creates two LiteratureRecords.
    """
    lr1 = LiteratureRecord(
        project_id=pid, title="Study 1 RCT Dapagliflozin T2DM",
        abstract="RCT of dapagliflozin vs placebo in T2DM CKD patients.",
        source_key="pubmed", source_record_id="pm-t13-001",
    )
    lr2 = LiteratureRecord(
        project_id=pid, title="Study 2 RCT Empagliflozin T2DM",
        abstract="RCT of empagliflozin vs placebo in T2DM with CVD.",
        source_key="pubmed", source_record_id="pm-t13-002",
    )
    session.add_all([lr1, lr2])
    session.flush()

    ea1 = EvidenceArtifact(
        literature_record_id=lr1.id, stage="screening_ta",
        decision="include", confidence=0.92,
    )
    ea2 = EvidenceArtifact(
        literature_record_id=lr2.id, stage="screening_ta",
        decision="include", confidence=0.87,
    )
    session.add_all([ea1, ea2])
    session.commit()
    session.refresh(ea1)
    session.refresh(ea2)
    session.refresh(lr1)
    session.refresh(lr2)
    return ea1.id, ea2.id, lr1.id, lr2.id


# ──────────────────────────────────────────────────────────────────────────────
# R1: POST /evidence-artifact/list  (success + failure)
# ──────────────────────────────────────────────────────────────────────────────

class TestR1EvidenceList:
    def test_r1_list_success_two_records(self):
        """R1 success: 2 record_ids + stage=screening_ta → items len=2."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-001")
        pid = _create_project(client, token, "meda-t13", "u-t13-001", "R1 Success Project")

        with Session(engine) as s:
            ea1_id, ea2_id, lr1_id, lr2_id = _create_two_ea_records(pid, s)

        resp = client.post(
            "/api/workspace/evidence-artifact/list",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": pid,
                "record_ids": [lr1_id, lr2_id],
                "stage": "screening_ta",
            },
        )
        assert resp.status_code == 200, f"R1 list non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body.get("count") == 2, f"R1 expected count=2, got {body.get('count')}"
        items = body.get("items") or []
        assert len(items) == 2, f"R1 expected len(items)=2, got {len(items)}"
        record_ids_ret = [it.get("literature_record_id") for it in items]
        assert set(record_ids_ret) == {lr1_id, lr2_id}, (
            f"R1 record_ids mismatch: {record_ids_ret} vs expected {lr1_id, lr2_id}"
        )

    def test_r1_list_failure_empty_record_ids(self):
        """R1 failure: record_ids=[] → 400 BAD REQUEST."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-002")
        pid = _create_project(client, token, "meda-t13", "u-t13-002", "R1 Failure Project")

        resp = client.post(
            "/api/workspace/evidence-artifact/list",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": pid,
                "record_ids": [],
                "stage": "screening_ta",
            },
        )
        assert resp.status_code == 400, (
            f"R1 expected HTTP 400 for empty record_ids, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert "record_ids" in detail or "empty" in detail.lower(), (
            f"R1 400 detail should reference record_ids: {detail!r}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# R2: GET /evidence-artifact/{id}  (success + failure)
# ──────────────────────────────────────────────────────────────────────────────

class TestR2EvidenceGet:
    def test_r2_get_success(self):
        """R2 success: GET ea/{id} → returns correct literature_record_id."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-003")
        pid = _create_project(client, token, "meda-t13", "u-t13-003", "R2 Success Project")

        with Session(engine) as s:
            ea1_id, _, lr1_id, _ = _create_two_ea_records(pid, s)

        resp = client.get(
            f"/api/workspace/evidence-artifact/{ea1_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"R2 get non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body.get("id") == ea1_id, (
            f"R2 expected ea.id={ea1_id}, got {body.get('id')}"
        )
        assert body.get("literature_record_id") == lr1_id, (
            f"R2 expected literature_record_id={lr1_id}, got {body.get('literature_record_id')}"
        )
        assert body.get("stage") == "screening_ta"
        assert body.get("decision") == "include"

    def test_r2_get_failure_not_found(self):
        """R2 failure: GET ea/not_found (id=999999) → 404."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-004")
        _create_project(client, token, "meda-t13", "u-t13-004", "R2 Failure Project")

        fake_id = 999_999_999
        resp = client.get(
            f"/api/workspace/evidence-artifact/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"R2 expected HTTP 404 for id={fake_id}, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert "not found" in detail.lower(), (
            f"R2 404 detail missing 'not found': {detail!r}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# R3: POST /evidence-artifact/decide  (success + failure)
# ──────────────────────────────────────────────────────────────────────────────

class TestR3EvidenceDecide:
    def test_r3_decide_success_ta_include(self):
        """R3 success: decide TA include → 200 decision=include."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-005")
        pid = _create_project(client, token, "meda-t13", "u-t13-005", "R3 Success Project")

        with Session(engine) as s:
            lr = LiteratureRecord(
                project_id=pid, title="RCT Study Include T2DM",
                abstract="RCT for T2DM study to be included.",
                source_key="pubmed", source_record_id="pm-t13-r3-001",
            )
            s.add(lr)
            s.commit()
            s.refresh(lr)
            lr_id = lr.id

        resp = client.post(
            "/api/workspace/evidence-artifact/decide",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": pid,
                "record_ids": [lr_id],
                "stage": "screening_ta",
                "decision": "include",
                "confidence": 0.9,
            },
        )
        assert resp.status_code == 200, (
            f"R3 decide non-200: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        assert body.get("decision") == "include", (
            f"R3 expected decision=include, got {body.get('decision')}"
        )
        assert body.get("stage") == "screening_ta"
        assert body.get("upserted_count") == 1
        items = body.get("items") or []
        assert len(items) == 1
        assert items[0].get("decision") == "include"

    def test_r3_decide_failure_ta_exclude_6(self):
        """R3 failure: TA stage + exclude_reason_ids=[6] (ta_allowed=False) → 422 ValueError."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-006")
        pid = _create_project(client, token, "meda-t13", "u-t13-006", "R3 Failure Project")

        with Session(engine) as s:
            lr = LiteratureRecord(
                project_id=pid, title="RCT Study Exclude Wrong Outcome",
                abstract="Study with wrong outcome (PICO O mismatch).",
                source_key="pubmed", source_record_id="pm-t13-r3-002",
            )
            s.add(lr)
            s.commit()
            s.refresh(lr)
            lr_id = lr.id

        resp = client.post(
            "/api/workspace/evidence-artifact/decide",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "project_id": pid,
                "record_ids": [lr_id],
                "stage": "screening_ta",
                "decision": "exclude",
                "exclude_reason_ids": [6],
            },
        )
        assert resp.status_code == 422, (
            f"R3 expected HTTP 422 for exclude_reason_ids=[6] in TA; "
            f"got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert isinstance(detail, str)
        assert "ta_allowed=False" in detail, (
            f"R3 422 detail should contain 'ta_allowed=False': {detail!r}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# R4: POST /screening/funnel-stats  (success + failure)
# ──────────────────────────────────────────────────────────────────────────────

class TestR4FunnelStats:
    def test_r4_funnel_success_n4_eq_7204(self):
        """R4 success: N3=8651, dupes_removed=1447 → N4=7204, E1=7204."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-007")
        pid = _create_project(client, token, "meda-t13", "u-t13-007", "R4 Success Project")

        n3_input = 8651
        dupes_input = 1447
        expected_n4 = n3_input - dupes_input  # 7204

        resp = client.post(
            "/api/workspace/screening/funnel-stats",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pi_id": pid,
                "n3_override": n3_input,
                "n4_dupes_removed_override": dupes_input,
            },
        )
        assert resp.status_code == 200, (
            f"R4 funnel non-200: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        stats = body.get("stats") or []
        by_key = {s["key"]: s for s in stats if isinstance(s, dict) and "key" in s}

        n4_count = by_key.get("N4", {}).get("count")
        assert n4_count == expected_n4, (
            f"R4 N4 expected {expected_n4}, got {n4_count}"
        )
        e1_count = by_key.get("E1", {}).get("count")
        assert e1_count == expected_n4, (
            f"R4 E1 should equal N4 ({expected_n4}), got {e1_count}"
        )

    def test_r4_funnel_failure_no_permission_403(self):
        """R4 failure: project belongs to different org → 403 Forbidden."""
        client = TestClient(app)
        token_org_a = _dev_login(client, "meda-t13-a", "MedA T13 OrgA", "u-t13-008a")
        pid_org_a = _create_project(client, token_org_a, "meda-t13-a", "u-t13-008a", "R4 OrgA Project")

        token_org_b = _dev_login(client, "meda-t13-b", "MedA T13 OrgB", "u-t13-008b")

        resp = client.post(
            "/api/workspace/screening/funnel-stats",
            headers={"Authorization": f"Bearer {token_org_b}"},
            json={
                "pi_id": pid_org_a,
                "n3_override": 1000,
            },
        )
        assert resp.status_code == 403, (
            f"R4 expected HTTP 403 for cross-org access; "
            f"got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert isinstance(detail, str)
        assert "permission" in detail.lower(), (
            f"R4 403 detail should mention 'permission': {detail!r}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# R5: POST /rob2/evaluate-study  (success + failure)
# ──────────────────────────────────────────────────────────────────────────────

class TestR5RoB2Evaluate:
    def test_r5_rob2_success_overall_some(self):
        """R5 success: D1 some + D2..D5 low → overall=some."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-009")

        domains = [
            {"domain": "D1_randomization_process", "rating": "some"},
            {"domain": "D2_deviations_from_intended", "rating": "low"},
            {"domain": "D3_missing_outcome_data", "rating": "low"},
            {"domain": "D4_measurement_of_outcome", "rating": "low"},
            {"domain": "D5_selection_of_reported", "rating": "low"},
        ]

        resp = client.post(
            "/api/workspace/rob2/evaluate-study",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "study_id": 42,
                "domains": domains,
                "outcome_type": "objective",
            },
        )
        assert resp.status_code == 200, (
            f"R5 rob2 non-200: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        assert body.get("overall") == "some", (
            f"R5 expected overall=some (D1 some + 4 low); got {body.get('overall')}"
        )
        assert body.get("study_id") == 42
        ret_domains = body.get("domains") or []
        assert len(ret_domains) == 5

    def test_r5_rob2_failure_study_id_missing_422(self):
        """R5 failure: study_id missing → 422."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-010")

        domains = [
            {"domain": "D1_randomization_process", "rating": "low"},
        ]

        resp = client.post(
            "/api/workspace/rob2/evaluate-study",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "domains": domains,
            },
        )
        assert resp.status_code == 422, (
            f"R5 expected HTTP 422 for missing study_id; "
            f"got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert isinstance(detail, str)
        assert "study_id" in detail, (
            f"R5 422 detail should mention study_id: {detail!r}"
        )


# ──────────────────────────────────────────────────────────────────────────────
# R6: POST /abstractor/run-pipeline  (success + failure)
# ──────────────────────────────────────────────────────────────────────────────

class TestR6AbstractorPipeline:
    def test_r6_abstractor_success_perfect_pico_include(self):
        """R6 success: Perfect PICO via llm_result → decision=include, confidence>=0.85."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-011")
        pid = _create_project(client, token, "meda-t13", "u-t13-011", "T13 R6 Success")
        # 分诊结果会落成 EvidenceArtifact，外键指向真实文献记录，所以先插一条真实的
        with Session(engine) as s:
            lr = LiteratureRecord(
                project_id=pid,
                title="Dapagliflozin RCT in T2DM Patients with Cardiovascular Outcomes",
                abstract="Double-blind RCT of dapagliflozin vs placebo on CV outcomes.",
                source_key="pubmed",
                source_record_id="pm-t13-r6-ok",
            )
            s.add(lr)
            s.commit()
            s.refresh(lr)
            rid = lr.id

        perfect_pico = {
            "ok": True,
            "condition": "T2DM",
            "intervention": "SGLT2 inhibitor",
            "comparison": "placebo",
            "outcome": "cardiovascular events",
            "outcome_p_value": 0.001,
            "study_type": "RCT",
        }

        resp = client.post(
            "/api/workspace/abstractor/run-pipeline",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "record_id": rid,
                "title": "Dapagliflozin RCT in T2DM Patients with Cardiovascular Outcomes",
                "abstract_text": (
                    "This double-blind RCT evaluated SGLT2 inhibitor dapagliflozin vs "
                    "placebo on CV outcomes in 12,000 T2DM adults with established CVD."
                ),
                "llm_result": perfect_pico,
                "skip_simhash": True,
            },
        )
        assert resp.status_code == 200, (
            f"R6 abstractor non-200: {resp.status_code} {resp.text}"
        )
        body = resp.json()
        decision = body.get("decision")
        confidence = float(body.get("confidence") or 0.0)
        assert decision == "include", (
            f"R6 expected decision=include (perfect PICO); got {decision}"
        )
        assert confidence >= 0.85, (
            f"R6 expected confidence>=0.85; got {confidence}"
        )

    def test_r6_abstractor_failure_llm_2x_fallback_review(self):
        """R6 failure: llm_result None + fallback_times=2 → decision=review + failed_steps=['pico_llm']."""
        client = TestClient(app)
        token = _dev_login(client, "meda-t13", "MedA T13", "u-t13-012")
        pid = _create_project(client, token, "meda-t13", "u-t13-012", "T13 R6 Fallback")
        with Session(engine) as s:
            lr = LiteratureRecord(
                project_id=pid,
                title="Observational Study (no T2DM keywords)",
                abstract="Retrospective cohort of patients with general cardiovascular risk.",
                source_key="pubmed",
                source_record_id="pm-t13-r6-fallback",
            )
            s.add(lr)
            s.commit()
            s.refresh(lr)
            rid = lr.id

        resp = client.post(
            "/api/workspace/abstractor/run-pipeline",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "record_id": rid,
                "title": "Observational Study (no T2DM keywords)",
                "abstract_text": "Retrospective cohort of patients with general cardiovascular risk.",
                "llm_result": None,
                "fallback_times": 2,
                "skip_simhash": True,
            },
        )
        assert resp.status_code == 200, (
            f"R6 pipeline should still return 200 on fallback; got {resp.status_code}: {resp.text}"
        )
        body = resp.json()
        decision = body.get("decision")
        failed_steps = body.get("failed_steps") or []

        assert decision == "review", (
            f"R6 expected decision=review after 2x LLM failure; got {decision}"
        )
        assert isinstance(failed_steps, list) and len(failed_steps) > 0, (
            f"R6 expected non-empty failed_steps; got {failed_steps}"
        )
        assert "pico_llm" in failed_steps, (
            f"R6 failed_steps should include 'pico_llm'; got {failed_steps}"
        )
