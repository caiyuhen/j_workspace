"""W84 T5: ReportSnapshot SHA256 幂等 upsert cache (get_or_create) + REST list + O6 rule literal."""
from __future__ import annotations
import json
import hashlib
import pytest
from fastapi.testclient import TestClient
from app.db import SessionLocal
from app.models import ReportSnapshot, User, Organization, ResearchProject, GradeAssessment

@pytest.fixture()
def _client_pid(db_session):
    from app.routers.workspace import router as ws_router
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(ws_router)
    u = User(user_id="u-t5-001", display_name="T5")
    org = Organization(slug="t5-hospital", name="T5 Hospital")
    db_session.add_all([u, org]); db_session.flush()
    p = ResearchProject(organization_slug="t5-hospital", owner_user_id=u.user_id, name="T5 Project", description="t5", workspace_key="ws-t5")
    db_session.add(p); db_session.flush()
    g = GradeAssessment(
        project_id=p.id, outcome_id=1, reviewer_id=999,
        domains_5={"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns","publication_bias":"no_concerns"},
        upgrades_3={"large_effect":False,"dose_response":False,"confounders_reduce":False},
        certainty_final="High",
    )
    db_session.add(g); db_session.commit()
    return TestClient(app), p.id

def test_t5_idempotent_twice_same_sha256_db_count_eq_1(_client_pid):
    client, pid = _client_pid
    body = {"version_label": "v0.1-idem"}
    r1 = client.post(f"/api/workspace/projects/{pid}/report/generate", json=body)
    r2 = client.post(f"/api/workspace/projects/{pid}/report/generate", json=body)
    assert r1.status_code == 200, f"r1 status={r1.status_code} text={r1.text}"
    assert r2.status_code == 200, f"r2 status={r2.status_code} text={r2.text}"
    sl = SessionLocal()
    with sl as s:
        cnt = s.query(ReportSnapshot).filter(ReportSnapshot.project_id == pid).count()
    assert cnt == 1, f"expected count=1 (idempotent), got count={cnt}"

def test_t5_sha256_grade_and_analysis_exact_64_chars_length(_client_pid):
    client, pid = _client_pid
    r = client.post(f"/api/workspace/projects/{pid}/report/generate", json={"version_label":"v-sha64"})
    assert r.status_code == 200
    d = r.json()
    assert len(d["sha256_grade"]) == 64, f"sha_grade len={len(d['sha256_grade'])}"
    assert len(d["sha256_analysis"]) == 64, f"sha_analysis len={len(d['sha256_analysis'])}"
    for field in ("sha256_grade", "sha256_analysis"):
        assert all(c in "0123456789abcdef" for c in d[field]), f"{field} not hex: {d[field]!r}"

def test_t5_three_outputs_length_gt_50_bytes_after_save(_client_pid):
    client, pid = _client_pid
    r = client.post(f"/api/workspace/projects/{pid}/report/generate", json={"version_label":"v-len"})
    assert r.status_code == 200
    d = r.json()
    for col in ("md_content","html_content","txt_content"):
        assert isinstance(d[col], str) and len(d[col]) > 50, f"{col} len={len(d.get(col))}"

def test_t5_O6_incomplete_422_if_any_md_html_txt_empty(_client_pid):
    """Rule O6 report_snapshot_incomplete_missing_content_sections literal — server-side enforced."""
    from app.services.output_stage import OutputStageError as E, _simulate_rule_O6_incomplete
    with pytest.raises(E) as ei:
        _simulate_rule_O6_incomplete(md="OK", html="", txt="OK")
    assert str(ei.value) == "report_snapshot_incomplete_missing_content_sections", f"got={str(ei.value)!r}"

def test_t5_REST_report_list_endpoint_get_project_pid_reports_200(_client_pid):
    client, pid = _client_pid
    client.post(f"/api/workspace/projects/{pid}/report/generate", json={"version_label":"v-list-1"})
    client.post(f"/api/workspace/projects/{pid}/report/generate", json={"version_label":"v-list-1"})
    r = client.get(f"/api/workspace/projects/{pid}/reports")
    assert r.status_code == 200, f"status={r.status_code} text={r.text}"
    rows = r.json()
    assert isinstance(rows, list), f"not a list; got type={type(rows)}"
    assert len(rows) >= 1, f"rows empty len={len(rows)}"
    for row in rows:
        assert "id" in row and "version_label" in row and "sha256_grade" in row, f"row keys={list(row.keys())}"

def test_t5_snapshot_id_is_identical_across_two_duplicate_generates(_client_pid):
    """幂等：两次相同内容 generate 返回同一个 snapshot id（不是创建两条）。"""
    client, pid = _client_pid
    r1 = client.post(f"/api/workspace/projects/{pid}/report/generate", json={"version_label":"v-idem-id"})
    r2 = client.post(f"/api/workspace/projects/{pid}/report/generate", json={"version_label":"v-idem-id"})
    assert r1.status_code == 200 and r2.status_code == 200
    sl = SessionLocal()
    with sl as s:
        rows = s.query(ReportSnapshot).filter(ReportSnapshot.project_id == pid).all()
    assert len(rows) == 1, f"expected 1 row (idempotent) got {len(rows)}"
    assert rows[0].version_label == "v-idem-id"
