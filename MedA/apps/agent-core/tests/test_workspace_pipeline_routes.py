"""W10 D2-1: 6 pipeline routes × 4 = 24 tests GREEN.

Routes:
  a) POST /{workspace_id}/pipelines/run       → A1-A4
  b) GET  /{workspace_id}/pipelines           → A5-A8
  c) GET  /{workspace_id}/pipelines/{run_id}  → A9-A12
  d) POST /{workspace_id}/pipelines/{run_id}/retry/{step_idx} → A13-A16
  e) POST /{workspace_id}/pipelines/{run_id}/cancel           → A17-A20
  f) GET  /{workspace_id}/pipelines/compare/{run_a}/{run_b}   → A21-A24
"""

import pytest
import warnings
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.db import engine
from app.models import PipelineRun, Workspace


ORG_SLUG = "meda-w10"
ORG_NAME = "MedA W10 Org"
USER_ID_A = "u-w10-001"
USER_ID_B = "u-w10-999"
WORKSPACE_ID = f"{ORG_SLUG}-ws-pipeline-001"
FOREIGN_WORKSPACE_ID = "foreignorg-ws-999"
NOAUTO_WORKSPACE_ID = f"{ORG_SLUG}-NOAUTO-missing-404"


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


def _ensure_workspace(session: Session, wid: str) -> None:
    ws = session.get(Workspace, wid)
    if ws is None:
        ws = Workspace(id=wid)
        session.add(ws)
        session.commit()
        session.refresh(ws)


def _make_run(session: Session, wid: str, status: str = "queued", preset: str = "sglt2i_ckd") -> str:
    from app.services.pipeline_engine import create_pipeline_run

    run = create_pipeline_run(
        workspace_id=wid,
        preset=preset,
        mode="snapshot",
        max_records=50,
    )
    if status != "queued":
        db_run = session.get(PipelineRun, run.id)
        if db_run is not None:
            db_run.status = status
            if status in ("success", "failed", "cancelled"):
                from datetime import datetime

                db_run.finished_at = datetime.utcnow()
            session.add(db_run)
            session.commit()
    return run.id


@pytest.fixture(autouse=True)
def _suppress_task_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*coroutine 'run_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*coroutine 'resume_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending!.*")
        yield


# ═══════════════════════════════════════════════════════════════════════════════
# A1-A4: Route a — POST /{workspace_id}/pipelines/run
# ═══════════════════════════════════════════════════════════════════════════════


class TestARunPipeline:
    def test_A1_post_run_200_success(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/run",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "preset": "sglt2i_ckd",
                "mode": "snapshot",
                "max_records": 100,
            },
        )
        assert resp.status_code == 200, f"A1 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "run_id" in body, "A1 missing run_id key"
        assert body["status"] == "queued", f"A1 status expected queued, got {body['status']}"
        assert body["expected_ms_estimate"] == 180000, "A1 expected_ms_estimate mismatch"

    def test_A2_post_run_401_not_logged_in(self):
        client = TestClient(app)
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/run",
            json={"preset": "sglt2i_ckd", "mode": "snapshot", "max_records": 50},
        )
        assert resp.status_code == 401, (
            f"A2 expected HTTP 401 no token, got {resp.status_code}: {resp.text}"
        )

    def test_A3_post_run_403_not_workspace_member(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.post(
            f"/api/workspace/{FOREIGN_WORKSPACE_ID}/pipelines/run",
            headers={"Authorization": f"Bearer {token}"},
            json={"preset": "sglt2i_ckd", "mode": "snapshot", "max_records": 50},
        )
        assert resp.status_code == 403, (
            f"A3 expected HTTP 403 foreign workspace, got {resp.status_code}: {resp.text}"
        )

    def test_A4_post_run_400_invalid_preset(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/run",
            headers={"Authorization": f"Bearer {token}"},
            json={"preset": "INVALID_PRESET_XYZ", "mode": "snapshot", "max_records": 50},
        )
        assert resp.status_code == 400, (
            f"A4 expected HTTP 400 invalid preset, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert "preset" in detail.lower() or "invalid" in detail.lower(), (
            f"A4 400 detail should mention preset: {detail!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# A5-A8: Route b — GET /{workspace_id}/pipelines
# ═══════════════════════════════════════════════════════════════════════════════


class TestBListPipelines:
    def test_A5_get_list_200_success(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            _make_run(s, WORKSPACE_ID, status="queued", preset="sglt2i_ckd")
            _make_run(s, WORKSPACE_ID, status="success", preset="empagliflozin_hf")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines",
            headers={"Authorization": f"Bearer {token}"},
            params={"page": 1, "per_page": 10},
        )
        assert resp.status_code == 200, f"A5 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "runs" in body, "A5 missing runs key"
        assert "total" in body, "A5 missing total key"
        assert isinstance(body["runs"], list), "A5 runs should be list"
        assert isinstance(body["total"], int), "A5 total should be int"
        assert body["total"] >= 2, f"A5 expected total>=2, got {body['total']}"

    def test_A6_get_list_401_not_logged_in(self):
        client = TestClient(app)
        resp = client.get(f"/api/workspace/{WORKSPACE_ID}/pipelines")
        assert resp.status_code == 401, (
            f"A6 expected HTTP 401 no token, got {resp.status_code}: {resp.text}"
        )

    def test_A7_get_list_403_not_workspace_member(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{FOREIGN_WORKSPACE_ID}/pipelines",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"A7 expected HTTP 403 foreign workspace, got {resp.status_code}: {resp.text}"
        )

    def test_A8_get_list_404_workspace_not_found(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{NOAUTO_WORKSPACE_ID}/pipelines",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"A8 expected HTTP 404 missing workspace, got {resp.status_code}: {resp.text}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# A9-A12: Route c — GET /{workspace_id}/pipelines/{run_id}
# ═══════════════════════════════════════════════════════════════════════════════


class TestCGetPipelineDetail:
    def test_A9_get_detail_200_success(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="queued", preset="glp1_weightloss")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"A9 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body["id"] == rid, f"A9 run id mismatch"
        assert body["workspace_id"] == WORKSPACE_ID, "A9 workspace_id mismatch"
        assert "steps" in body, "A9 missing steps key"
        assert len(body["steps"]) == 8, f"A9 expected 8 steps, got {len(body['steps'])}"
        assert "cancel_flag" in body, "A9 missing cancel_flag"
        assert "report_url" in body, "A9 missing report_url"
        assert f"/pipelines/{rid}/report.pdf" in body["report_url"], "A9 report_url shape wrong"

    def test_A10_get_detail_401_not_logged_in(self):
        client = TestClient(app)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID)
        resp = client.get(f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}")
        assert resp.status_code == 401, (
            f"A10 expected HTTP 401 no token, got {resp.status_code}: {resp.text}"
        )

    def test_A11_get_detail_403_not_workspace_member(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID)
        resp = client.get(
            f"/api/workspace/{FOREIGN_WORKSPACE_ID}/pipelines/{rid}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"A11 expected HTTP 403 foreign workspace, got {resp.status_code}: {resp.text}"
        )

    def test_A12_get_detail_404_run_not_found(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        fake_run_id = "p-0000NOTEXIST9999FAKE9999"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{fake_run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"A12 expected HTTP 404 missing run_id, got {resp.status_code}: {resp.text}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# A13-A16: Route d — POST /{workspace_id}/pipelines/{run_id}/retry/{step_idx}
# ═══════════════════════════════════════════════════════════════════════════════


class TestDRetryStep:
    def test_A13_post_retry_200_success(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="failed", preset="liraglutide_nafld")
            db_run = s.get(PipelineRun, rid)
            if db_run and db_run.steps_json and len(db_run.steps_json) == 8:
                new_steps = [dict(x) for x in db_run.steps_json]
                for i in range(2):
                    new_steps[i]["status"] = "success"
                new_steps[2]["status"] = "failed"
                db_run.steps_json = new_steps
                s.add(db_run)
                s.commit()
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/retry/2",
            headers={"Authorization": f"Bearer {token}"},
            params={"force": "false"},
        )
        assert resp.status_code == 200, f"A13 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body["queued"] is True, "A13 queued should be True"
        assert body["resumed_from"] == 2, f"A13 resumed_from expected 2, got {body['resumed_from']}"
        assert "force" in body, "A13 missing force key"

    def test_A14_post_retry_401_not_logged_in(self):
        client = TestClient(app)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID)
        resp = client.post(f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/retry/1")
        assert resp.status_code == 401, (
            f"A14 expected HTTP 401 no token, got {resp.status_code}: {resp.text}"
        )

    def test_A15_post_retry_403_not_workspace_member(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID)
        resp = client.post(
            f"/api/workspace/{FOREIGN_WORKSPACE_ID}/pipelines/{rid}/retry/0",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"A15 expected HTTP 403 foreign workspace, got {resp.status_code}: {resp.text}"
        )

    def test_A16_post_retry_400_idx_9_out_of_range(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID)
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/retry/9",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400, (
            f"A16 expected HTTP 400 step_idx=9, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert "step" in detail.lower() or "idx" in detail.lower() or "range" in detail.lower(), (
            f"A16 400 detail should mention step_idx/range: {detail!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# A17-A20: Route e — POST /{workspace_id}/pipelines/{run_id}/cancel
# ═══════════════════════════════════════════════════════════════════════════════


class TestECancelPipeline:
    def test_A17_post_cancel_200_success(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="queued", preset="pkd_tolvaptan")
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"A17 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body["cancelled"] is True, "A17 cancelled should be True"
        assert body["will_stop_at_next_step_entry"] is True, "A17 will_stop flag wrong"

    def test_A18_post_cancel_401_not_logged_in(self):
        client = TestClient(app)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID)
        resp = client.post(f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/cancel")
        assert resp.status_code == 401, (
            f"A18 expected HTTP 401 no token, got {resp.status_code}: {resp.text}"
        )

    def test_A19_post_cancel_403_not_workspace_member(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID)
        resp = client.post(
            f"/api/workspace/{FOREIGN_WORKSPACE_ID}/pipelines/{rid}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"A19 expected HTTP 403 foreign workspace, got {resp.status_code}: {resp.text}"
        )

    def test_A20_post_cancel_409_already_success(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
        resp = client.post(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/cancel",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 409, (
            f"A20 expected HTTP 409 terminal success, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert "terminal" in detail.lower() or "success" in detail.lower() or "already" in detail.lower(), (
            f"A20 409 detail should mention terminal/success: {detail!r}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# A21-A24: Route f — GET /{workspace_id}/pipelines/compare/{run_a}/{run_b}
# ═══════════════════════════════════════════════════════════════════════════════


class TestFComparePipelines:
    def test_A21_get_compare_200_success(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid_a = _make_run(s, WORKSPACE_ID, status="success", preset="sglt2i_ckd")
            rid_b = _make_run(s, WORKSPACE_ID, status="success", preset="ckd_blood_pressure_control")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{rid_a}/{rid_b}",
            headers={"Authorization": f"Bearer {token}"},
            params={"metrics": "funnel,rob,grade,pico"},
        )
        assert resp.status_code == 200, f"A21 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "run_a" in body, "A21 missing run_a"
        assert "run_b" in body, "A21 missing run_b"
        assert "metrics_requested" in body, "A21 missing metrics_requested"
        assert "funnel" in body, "A21 missing funnel section"
        assert "rob" in body, "A21 missing rob section"
        assert "grade" in body, "A21 missing grade section"
        assert "pico" in body, "A21 missing pico section"
        for section in ("funnel",):
            for key, val in body[section].items():
                assert isinstance(val, dict), f"A21 {section}.{key} should be dict"
                assert "a" in val and "b" in val and "delta" in val, (
                    f"A21 {section}.{key} missing a/b/delta keys"
                )

    def test_A22_get_compare_401_not_logged_in(self):
        client = TestClient(app)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid_a = _make_run(s, WORKSPACE_ID)
            rid_b = _make_run(s, WORKSPACE_ID)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{rid_a}/{rid_b}"
        )
        assert resp.status_code == 401, (
            f"A22 expected HTTP 401 no token, got {resp.status_code}: {resp.text}"
        )

    def test_A23_get_compare_403_not_workspace_member(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid_a = _make_run(s, WORKSPACE_ID)
            rid_b = _make_run(s, WORKSPACE_ID)
        resp = client.get(
            f"/api/workspace/{FOREIGN_WORKSPACE_ID}/pipelines/compare/{rid_a}/{rid_b}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"A23 expected HTTP 403 foreign workspace, got {resp.status_code}: {resp.text}"
        )

    def test_A24_get_compare_404_run_a_not_exist(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        fake_a = "p-0000NOTEXIST9999FAKE9999"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid_b = _make_run(s, WORKSPACE_ID)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{fake_a}/{rid_b}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"A24 expected HTTP 404 missing run_a, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", "")
        assert "run_a" in detail or "not found" in detail.lower(), (
            f"A24 404 detail should mention run_a / not found: {detail!r}"
        )
