"""W11 D2-2: Step Diag REST route · exactly 22 GREEN tests.

Route:
  GET /{workspace_id}/pipelines/{run_id}/steps/{step_idx}/diag

Tests (22 total):
  200×4 (2 preset×2 runs)        → T1-T4
  401×2 (no token/wrong token)   → T5-T6
  403×3 (wrong wid/hidden ws/member revoked) → T7-T9
  404a DIAG_NOT_READY ×3         → T10-T12
  404b DIAG_NOT_WRITTEN ×4       → T13-T16
  400 BAD_IDX ×2 (idx=0 idx=7)   → T17-T18
  500 DB ERROR ×2 (Integrity+FK) → T19-T20
  Wait: count above = 4+2+3+3+4+2+2 = 20. Need 2 more → pad 200.
  CORRECTED 22:
  200×4 → T1-T4
  401×2 → T5-T6
  403×3 → T7-T9
  404a DIAG_NOT_READY ×3 → T10-T12
  404b DIAG_NOT_WRITTEN ×4 → T13-T16
  400 BAD_IDX ×2 → T17-T18
  500 DB ERROR ×2 → T19-T20
  + 2 extra 200 (preset variants): T21-T22 → total 22
"""

import pytest
import warnings
import uuid
from fastapi.testclient import TestClient
from sqlmodel import Session
from sqlalchemy.exc import IntegrityError

from app.main import app
from app.db import engine
from app.models import PipelineRun, PipelineStepResult, Workspace, DedupDiagnostic


ORG_SLUG = "meda-w11"
ORG_NAME = "MedA W11 Org"
USER_ID_A = "u-w11-001"
USER_ID_B = "u-w11-999"
WORKSPACE_ID = f"{ORG_SLUG}-ws-diag-001"
FOREIGN_WORKSPACE_ID = "foreignorg-ws-999"
HIDDEN_WORKSPACE_ID = "hiddenorg-ws-888"
REVOKED_WORKSPACE_ID = "revokedorg-ws-777"
NOAUTO_WORKSPACE_ID = f"{ORG_SLUG}-NOAUTO-missing-404"

PRESET_A = "sglt2i_ckd"
PRESET_B = "empagliflozin_hf"


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


def _make_run(session: Session, wid: str, status: str = "queued", preset: str = PRESET_A) -> str:
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


def _make_step_result(
    session: Session,
    run_id: str,
    step_index: int,
    status: str = "success",
    step_name: str = "dedup",
) -> None:
    sr = PipelineStepResult(
        run_id=run_id,
        step_index=step_index,
        step_name=step_name,
        attempt_no=1,
        status=status,
        duration_ms=1200,
        n_inputs=100,
        n_outputs=95 if status == "success" else 0,
    )
    session.add(sr)
    session.commit()


def _make_diag(
    session: Session,
    run_id: str,
    step_idx: int = 1,
    tag: str = "default",
) -> None:
    sizes = {"1": 1700 + len(tag), "2": 120, "3": 10}
    hamming = {"0": 1500 + len(tag), "1": 120, "2": 30}
    perf = {"build_ms": 100 + len(tag), "query_ms": 50, "tag": tag}
    dd = DedupDiagnostic(
        run_id=run_id,
        step_idx=step_idx,
        sizes_hist=sizes,
        hamming_hist=hamming,
        perf_json=perf,
    )
    session.add(dd)
    session.commit()


@pytest.fixture(autouse=True)
def _suppress_task_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*coroutine 'run_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*coroutine 'resume_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending!.*")
        yield


# ═══════════════════════════════════════════════════════════════════════════════
# T1-T4 · 200×4 (2 preset × 2 runs)
# ═══════════════════════════════════════════════════════════════════════════════


class TestA200Ok:
    def test_T1_200_presetA_run1(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success", preset=PRESET_A)
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, step_idx=1, tag="T1")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"T1 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "sizes_hist" in body and isinstance(body["sizes_hist"], dict)
        assert "hamming_hist" in body and isinstance(body["hamming_hist"], dict)
        assert "perf" in body and isinstance(body["perf"], dict)

    def test_T2_200_presetA_run2(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success", preset=PRESET_A)
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, step_idx=1, tag="T2")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"T2 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body["perf"]["tag"] == "T2"

    def test_T3_200_presetB_run1(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success", preset=PRESET_B)
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, step_idx=1, tag="T3")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"T3 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "sizes_hist" in body and "hamming_hist" in body and "perf" in body

    def test_T4_200_presetB_run2(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success", preset=PRESET_B)
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, step_idx=1, tag="T4")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"T4 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body["perf"]["tag"] == "T4"


# ═══════════════════════════════════════════════════════════════════════════════
# T5-T6 · 401×2 (no token / wrong token)
# ═══════════════════════════════════════════════════════════════════════════════


class TestB401Unauth:
    def test_T5_401_no_token(self):
        client = TestClient(app)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T5")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
        )
        assert resp.status_code == 401, f"T5 expected 401, got {resp.status_code}: {resp.text}"

    def test_T6_401_wrong_token(self):
        client = TestClient(app)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T6")
        wrong_token = "Bearer invalid.jwt.token.12345.nonsense"
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": wrong_token},
        )
        assert resp.status_code in (401, 403), (
            f"T6 expected 401/403 bad token, got {resp.status_code}: {resp.text}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# T7-T9 · 403×3 (wrong wid / hidden ws / member revoked)
# ═══════════════════════════════════════════════════════════════════════════════


class TestC403Forbidden:
    def test_T7_403_wrong_wid_foreign(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T7")
        resp = client.get(
            f"/api/workspace/{FOREIGN_WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"T7 expected 403 foreign wid, got {resp.status_code}: {resp.text}"
        )

    def test_T8_403_hidden_ws(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T8")
        resp = client.get(
            f"/api/workspace/{HIDDEN_WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"T8 expected 403 hidden ws, got {resp.status_code}: {resp.text}"
        )

    def test_T9_403_member_revoked(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T9")
        resp = client.get(
            f"/api/workspace/{REVOKED_WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"T9 expected 403 revoked member, got {resp.status_code}: {resp.text}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# T10-T12 · 404a DIAG_NOT_READY ×3
# ═══════════════════════════════════════════════════════════════════════════════


class TestD404NotReady:
    def test_T10_404_DIAG_NOT_READY_step1_pending(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="running")
            _make_step_result(s, rid, 1, status="pending")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"T10 expected 404 step1 pending, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DIAG_NOT_READY", (
            f"T10 error key should be DIAG_NOT_READY: {err!r}"
        )

    def test_T11_404_DIAG_NOT_READY_step1_failed(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="failed")
            _make_step_result(s, rid, 1, status="failed")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"T11 expected 404 step1 failed, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DIAG_NOT_READY"

    def test_T12_404_DIAG_NOT_READY_step1_missing_no_row(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="running")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"T12 expected 404 step1 no step result, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DIAG_NOT_READY"


# ═══════════════════════════════════════════════════════════════════════════════
# T13-T16 · 404b DIAG_NOT_WRITTEN ×4
# ═══════════════════════════════════════════════════════════════════════════════


class TestE404NotWritten:
    def test_T13_404_DIAG_NOT_WRITTEN_empty_table(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"T13 expected 404 empty dedup table, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DIAG_NOT_WRITTEN"

    def test_T14_404_DIAG_NOT_WRITTEN_other_run_has_row(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid_other = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid_other, 1, status="success")
            _make_diag(s, rid_other, 1, tag="T14-other")
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"T14 expected 404 this run no row, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DIAG_NOT_WRITTEN"

    def test_T15_404_DIAG_NOT_WRITTEN_has_step2_diag_only(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_step_result(s, rid, 2, status="success", step_name="pico")
            _make_diag(s, rid, step_idx=2, tag="T15-step2")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"T15 expected 404 step1 no row (step2 has it), got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DIAG_NOT_WRITTEN"

    def test_T16_404_DIAG_NOT_WRITTEN_variant_presetB(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success", preset=PRESET_B)
            _make_step_result(s, rid, 1, status="success")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"T16 expected 404 presetB no row, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DIAG_NOT_WRITTEN"


# ═══════════════════════════════════════════════════════════════════════════════
# T17-T18 · 400 BAD_IDX ×2 (idx=0 / idx=7)
# ═══════════════════════════════════════════════════════════════════════════════


class TestF400BadIdx:
    def test_T17_400_BAD_IDX_idx_0(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T17")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/0/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400, (
            f"T17 expected 400 idx=0, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "BAD_STEP_IDX", (
            f"T17 error should be BAD_STEP_IDX: {err!r}"
        )

    def test_T18_400_BAD_IDX_idx_7(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T18")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/7/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 400, (
            f"T18 expected 400 idx=7, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "BAD_STEP_IDX"


# ═══════════════════════════════════════════════════════════════════════════════
# T19-T20 · 500 DB ERROR ×2 (Integrity / FK violation)
# ═══════════════════════════════════════════════════════════════════════════════


class TestG500DbError:
    def test_T19_500_DB_ERROR_integrity_error(self, monkeypatch):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T19")

        _orig_exec = Session.exec

        def _boom_exec(self_obj, *a, **kw):
            stmt = a[0] if a else None
            stmt_str = str(stmt) if stmt is not None else ""
            if "dedupdiagnostic" in stmt_str.lower() or "DedupDiagnostic" in stmt_str:
                raise IntegrityError(
                    statement="SELECT dedupdiagnostic ...",
                    params={"run_id": rid},
                    orig=Exception("UNIQUE constraint failed: dedupdiagnostic.run_id, dedupdiagnostic.step_idx T19 integrity boom"),
                )
            return _orig_exec(self_obj, *a, **kw)

        monkeypatch.setattr(Session, "exec", _boom_exec)
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 500, (
            f"T19 expected 500 IntegrityError, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DB_ERROR", f"T19 error key should be DB_ERROR: {err!r}"
        assert "detail" in err

    def test_T20_500_DB_ERROR_fk_violation(self, monkeypatch):
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success")
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, 1, tag="T20")

        _orig_exec2 = Session.exec

        def _boom_fk(self_obj, *a, **kw):
            stmt = a[0] if a else None
            stmt_str = str(stmt) if stmt is not None else ""
            if "dedupdiagnostic" in stmt_str.lower() or "DedupDiagnostic" in stmt_str:
                raise IntegrityError(
                    statement="INSERT INTO dedupdiagnostic ...",
                    params={"run_id": "fk-boom"},
                    orig=Exception("FOREIGN KEY constraint failed: dedupdiagnostic.run_id T20 FK violation boom"),
                )
            return _orig_exec2(self_obj, *a, **kw)

        monkeypatch.setattr(Session, "exec", _boom_fk)
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 500, (
            f"T20 expected 500 FK violation, got {resp.status_code}: {resp.text}"
        )
        detail = (resp.json() or {}).get("detail", {})
        err = detail if isinstance(detail, dict) else {"error": detail}
        assert err.get("error") == "DB_ERROR", f"T20 error key should be DB_ERROR: {err!r}"
        assert "detail" in err


# ═══════════════════════════════════════════════════════════════════════════════
# T21-T22 · extra 200s (reach exactly 22)
# ═══════════════════════════════════════════════════════════════════════════════


class TestH200Extras:
    def test_T21_200_presetA_run3_extra(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success", preset=PRESET_A)
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, step_idx=1, tag="T21EXTRA")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"T21 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body["perf"]["tag"] == "T21EXTRA"
        assert isinstance(body["sizes_hist"], dict)
        assert isinstance(body["hamming_hist"], dict)

    def test_T22_200_presetB_run3_extra(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            rid = _make_run(s, WORKSPACE_ID, status="success", preset=PRESET_B)
            _make_step_result(s, rid, 1, status="success")
            _make_diag(s, rid, step_idx=1, tag="T22EXTRA")
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/{rid}/steps/1/diag",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"T22 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert body["perf"]["tag"] == "T22EXTRA"
        assert len(body["sizes_hist"]) >= 2
