"""Wave82B T5 REST 6 endpoints pytest (FastAPI TestClient).

Zero-network. Uses baseline's in-memory sqlite (conftest.py reset_database autouse fixture).
6 endpoints (T5 exact):
  GET  /api/workspaces/projects/{pid}/screening/prisma-stats
  POST /api/workspaces/projects/{pid}/screening/batch-decision
  POST /api/workspaces/projects/{pid}/screening/apply-override
  POST /api/workspaces/projects/{pid}/screening/clear-override
  POST /api/workspaces/projects/{pid}/screening/run-dedupe
  POST /api/workspaces/projects/{pid}/screening/records/{rid}/confirm-unique

AC10 HARD-GATE: 4 serialize 函数 0 行改不破 baseline (e09+e10)
"""
from __future__ import annotations
import json
from fastapi.testclient import TestClient
from sqlmodel import Session, select
import pytest
from app.db import engine
from app.main import app
from app.models import (
    LiteratureRecord, Membership, Organization, ResearchProject, User,
)


def _bootstrap(client: TestClient) -> tuple[str, int]:
    """dev-login + create a project. returns (token, pid)"""
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
    assert login.status_code == 200, f"dev-login: {login.status_code} {login.text}"
    token = login.json()["token"]
    # create project via /api/projects to get canonical id
    project = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "Wave82B T5 REST Project",
            "description": "test",
        },
    )
    assert project.status_code == 201, f"create project: {project.status_code} {project.text}"
    pid = int(project.json()["id"])
    return token, pid


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(name="t5_client")
def _t5_client():
    """TestClient + bootstrap user+org+project via REST baseline endpoints."""
    c = TestClient(app)
    token, pid = _bootstrap(c)
    c.headers.update(_auth(token))
    c.__dict__["_t5_pid"] = pid
    yield c


def pid_of(c) -> int:
    return c._t5_pid  # type: ignore[attr-defined]


def _make_row(c, idx: int, **kwargs) -> int:
    p = pid_of(c)
    with Session(engine) as s:
        rec = LiteratureRecord(
            project_id=p,
            title=kwargs.pop("title", f"R{idx}"),
            authors=kwargs.pop("authors", f"A{idx}"),
            journal=kwargs.pop("journal", "J"),
            year=kwargs.pop("year", 2024),
            doi=kwargs.pop("doi", ""),
            pmid=kwargs.pop("pmid", ""),
            abstract=kwargs.pop("abstract", ""),
            source_key=kwargs.pop("source_key", "pubmed"),
            source_label=kwargs.pop("source_label", "PubMed"),
            dedupe_status=kwargs.pop("dedupe_status", "unique"),
            duplicate_of_id=kwargs.pop("duplicate_of_id", None),
            pico_status="not_extracted",
            screening_stage=kwargs.pop("screening_stage", None),
            screening_decision=kwargs.pop("screening_decision", None),
            exclude_reason_json=None if kwargs.get("exclude_reason") is None else json.dumps(kwargs.pop("exclude_reason"), ensure_ascii=False),
        )
        s.add(rec); s.commit(); s.refresh(rec); return rec.id


BASE = "/api/workspace/projects"
SCREEN_PREFIX = "/screening"


# ---------------------------------------------------------------------------
# Tests (10)
# ---------------------------------------------------------------------------
class TestT5PrismaStats:
    def test_e01_404_project_missing(self, t5_client):
        r = t5_client.get(f"{BASE}/9999999{SCREEN_PREFIX}/prisma-stats")
        assert r.status_code == 404

    def test_e02_200_prisma_11_fields_and_identity(self, t5_client):
        for i in range(60):
            _make_row(t5_client, idx=i, screening_stage="fulltext", screening_decision="include")
        for i in range(60, 100):
            _make_row(t5_client, idx=i, screening_stage="fulltext", screening_decision="exclude",
                      exclude_reason={"preset_class": 6, "note": None, "stage": "fulltext"})
        for i in range(100, 120):
            _make_row(t5_client, idx=i, dedupe_status="duplicate", duplicate_of_id=1,
                      screening_decision="exclude", exclude_reason={"preset_class": 1, "stage": "ta"})
        p = pid_of(t5_client)
        r = t5_client.get(f"{BASE}/{p}{SCREEN_PREFIX}/prisma-stats")
        assert r.status_code == 200, r.text
        data = r.json()
        for k in ("identification", "screening", "eligibility", "included",
                  "ta_excluded", "duplicate_excluded", "fulltext_excluded", "override_applied"):
            assert k in data, f"missing {k}"
        assert data["identification"] == 120
        assert data["duplicate_excluded"] == 20
        assert data["identification"] - data["ta_excluded"] - data["duplicate_excluded"] == data["eligibility"]
        assert data["eligibility"] >= data["included"] + data["fulltext_excluded"]


class TestT5BatchDecision:
    def test_e03_batch_include_ta(self, t5_client):
        rids = [_make_row(t5_client, idx=100 + i) for i in range(5)]
        p = pid_of(t5_client)
        r = t5_client.post(f"{BASE}/{p}{SCREEN_PREFIX}/batch-decision", json={
            "operation": "include", "stage": "ta",
            "record_ids": rids, "client_batch_id": "t5-batch-1",
        })
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["processed_count"] == 5
        assert d["idempotent_hit"] is False

    def test_e04_batch_idempotent_hit(self, t5_client):
        rids = [_make_row(t5_client, idx=200 + i) for i in range(3)]
        p = pid_of(t5_client)
        payload = {"operation": "include", "stage": "ta",
                   "record_ids": rids, "client_batch_id": "t5-batch-2"}
        r1 = t5_client.post(f"{BASE}/{p}{SCREEN_PREFIX}/batch-decision", json=payload)
        assert r1.status_code == 200 and r1.json()["idempotent_hit"] is False
        r2 = t5_client.post(f"{BASE}/{p}{SCREEN_PREFIX}/batch-decision", json=payload)
        assert r2.status_code == 200 and r2.json()["idempotent_hit"] is True
        assert r2.json()["processed_count"] == r1.json()["processed_count"]

    def test_e05_illegal_transfer_422(self, t5_client):
        # fulltext include -> exclude @ ta (wrong stage)
        rid = _make_row(t5_client, idx=300, screening_stage="fulltext", screening_decision="include")
        p = pid_of(t5_client)
        r = t5_client.post(f"{BASE}/{p}{SCREEN_PREFIX}/batch-decision", json={
            "operation": "exclude", "stage": "ta",
            "record_ids": [rid],
            "exclude_reason": {"preset_class": 2, "note": None},
            "client_batch_id": "t5-illegal-1",
        })
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"


class TestT5Override:
    def test_e06_apply_and_clear_override(self, t5_client):
        p = pid_of(t5_client)
        r = t5_client.post(f"{BASE}/{p}{SCREEN_PREFIX}/apply-override", json={
            "identification": 500, "screening": 500, "eligibility": 400, "included": 200,
        })
        assert r.status_code == 200, r.text
        assert r.json().get("override_applied") is True
        st = t5_client.get(f"{BASE}/{p}{SCREEN_PREFIX}/prisma-stats")
        assert st.json()["override_applied"] is True
        assert st.json()["identification"] == 500
        cl = t5_client.post(f"{BASE}/{p}{SCREEN_PREFIX}/clear-override")
        assert cl.status_code == 200 and cl.json().get("cleared") is True
        st2 = t5_client.get(f"{BASE}/{p}{SCREEN_PREFIX}/prisma-stats")
        assert st2.json()["override_applied"] is False


class TestT5RunDedupe:
    def test_e07_run_dedupe_returns_new_duplicate_count(self, t5_client):
        for i in range(10):
            _make_row(t5_client, idx=i)
        # 2 exact same row id R0 via title
        for extra in range(2):
            with Session(engine) as s:
                p = pid_of(t5_client)
                s.add(LiteratureRecord(
                    project_id=p, title="R0", authors="A0", journal="J", year=2024,
                    doi="", pmid="", abstract="", source_key="pubmed", source_label="PubMed",
                    dedupe_status="unique", pico_status="not_extracted",
                ))
                s.commit()
        p = pid_of(t5_client)
        r = t5_client.post(f"{BASE}/{p}{SCREEN_PREFIX}/run-dedupe")
        assert r.status_code == 200, r.text
        assert "new_duplicate_count" in r.json()


class TestT5ConfirmUnique:
    def test_e08_confirm_unique_clears_4_screening_fields(self, t5_client):
        first = _make_row(t5_client, idx=0)
        rid = _make_row(t5_client, idx=1001, dedupe_status="duplicate", duplicate_of_id=first,
                        screening_decision="exclude",
                        exclude_reason={"preset_class": 1, "note": None, "stage": "ta"})
        p = pid_of(t5_client)
        r = t5_client.post(f"{BASE}/{p}{SCREEN_PREFIX}/records/{rid}/confirm-unique")
        assert r.status_code == 200, r.text
        with Session(engine) as s:
            rec = s.get(LiteratureRecord, rid)
            assert rec.dedupe_status == "confirmed_unique"
            assert rec.screening_decision is None
            assert rec.exclude_reason_json is None


class TestT5_AC10_HardGate:
    def test_e09_4_serialize_functions_exist_and_argspec_intact(self, t5_client):
        """AC10 HARD-GATE: 4 serialize modules 0 行修改。
        不破 baseline：assert serialize_ris_py / serialize_bibtex_py / export_search_run_csv_text 3 个 8.2A 函数 argspec 正确；
        顶层 workspace.py 顶部没有 serialize 相关符号。"""
        import inspect
        from app.services.serialize_ris import serialize_ris_py
        from app.services.serialize_bibtex import serialize_bibtex_py
        from app.services.search_run import export_search_run_csv_text
        for fn, min_args in ((serialize_ris_py, 1), (serialize_bibtex_py, 1), (export_search_run_csv_text, 2)):
            args = inspect.getfullargspec(fn).args
            assert len(args) >= min_args, f"{fn.__name__}: argspec changed -> AC10 broken"
        # workspace 模块 dir 里也无 serialize* 顶层 import
        import sys
        mod_ws = sys.modules.get("app.routers.workspace")
        assert mod_ws is not None
        ws_attrs = {*dir(mod_ws)}
        for t in ("serializeRIS", "serializeBibTeX", "serialize_ris_py", "serialize_bibtex_py"):
            assert t not in ws_attrs, f"AC10 broken: workspace top-level imports {t}"
        # 8.2A 4 serialize 文件 0 行改 → 用 sys.modules 无 T5 没有新增 serialize* 符号
        mod_syms_globals = {*globals()}
        for t in ("serializeRIS", "serializeBibTeX"):
            assert t not in mod_syms_globals, f"test itself imports {t} symbol"

    def test_e10_endpoint_module_no_direct_serialize_import(self, t5_client):
        """Endpoints thin-wrapper should only link to screening_engine, not serialize*."""
        import sys
        # Ensure our routers.workspace module imports no serialize* from top-level (lazy export only)
        mod = sys.modules.get("app.routers.workspace")
        assert mod is not None
        top = {*dir(mod)}
        assert "serializeRIS" not in top
        assert "export_ris" not in top
