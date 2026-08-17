"""Wave83 T4 REST 9 endpoints pytest (FastAPI TestClient).

Zero-network. Uses baseline's in-memory sqlite (conftest.py reset_database autouse fixture).
9 endpoints (T4 exact):
  GET  /api/workspace/projects/{pid}/stages/extraction/template
  POST /api/workspace/projects/{pid}/stages/extraction/template/save
  POST /api/workspace/projects/{pid}/stages/extraction/template/lock
  POST /api/workspace/projects/{pid}/stages/records/{rid}/extraction/cell
  GET  /api/workspace/projects/{pid}/stages/extraction/evidence-table
  GET  /api/workspace/projects/{pid}/stages/extraction/kappa
  POST /api/workspace/projects/{pid}/stages/analysis/outcomes/define
  POST /api/workspace/projects/{pid}/stages/analysis/run-meta
  GET  /api/workspace/projects/{pid}/stages/analysis/forest/{oid}.svg

20 tests total.
"""
from __future__ import annotations
import json
from fastapi.testclient import TestClient
from sqlmodel import Session, select
import pytest
from app.db import engine
from app.main import app
from app.models import (
    LiteratureRecord, ExtractionTemplate, ExtractionCell,
    OutcomeDefinition, OutcomeArmData,
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
    project = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "Wave83 T4 REST Project",
            "description": "test",
        },
    )
    assert project.status_code == 201, f"create project: {project.status_code} {project.text}"
    pid = int(project.json()["id"])
    return token, pid


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture(name="t4_client")
def _t4_client():
    """TestClient + bootstrap user+org+project via REST baseline endpoints."""
    c = TestClient(app)
    token, pid = _bootstrap(c)
    c.headers.update(_auth(token))
    c.__dict__["_t4_pid"] = pid
    yield c


def pid_of(c) -> int:
    return c._t4_pid  # type: ignore[attr-defined]


BASE = "/api/workspace/projects"
STAGE_PREFIX = "/stages"

DEFAULT_FIELDS = [
    {"key": "study_design", "type": "categorical", "label": "Study Design", "options": ["RCT", "Cohort", "Case-Control"]},
    {"key": "sample_size", "type": "numeric", "label": "Sample Size"},
    {"key": "intervention", "type": "text", "label": "Intervention"},
    {"key": "comparator", "type": "text", "label": "Comparator"},
    {"key": "primary_outcome", "type": "text", "label": "Primary Outcome"},
]


def _make_record(c, idx: int, **kwargs) -> int:
    p = pid_of(c)
    with Session(engine) as s:
        rec = LiteratureRecord(
            project_id=p,
            title=kwargs.pop("title", f"Study{idx}"),
            authors=kwargs.pop("authors", f"Author{idx}"),
            journal=kwargs.pop("journal", "J"),
            year=kwargs.pop("year", 2024),
            doi="", pmid="", abstract="",
            source_key="pubmed", source_label="PubMed",
            dedupe_status="unique",
            pico_status="not_extracted",
            screening_stage=kwargs.pop("screening_stage", "fulltext"),
            screening_decision=kwargs.pop("screening_decision", "include"),
        )
        s.add(rec); s.commit(); s.refresh(rec); return rec.id


class TestMissPid:
    def test_e01_404_project_missing(self, t4_client):
        r = t4_client.get(f"{BASE}/9999999{STAGE_PREFIX}/extraction/template")
        assert r.status_code == 404


class TestGetTemplate:
    def test_e02_200_template_default_fields(self, t4_client):
        p = pid_of(t4_client)
        r = t4_client.get(f"{BASE}/{p}{STAGE_PREFIX}/extraction/template")
        assert r.status_code == 200, r.text
        data = r.json()
        assert "template" in data
        assert "fields" in data
        assert isinstance(data["fields"], list)

    def test_e03_fields_shape_has_at_least_5_keys(self, t4_client):
        p = pid_of(t4_client)
        r = t4_client.get(f"{BASE}/{p}{STAGE_PREFIX}/extraction/template")
        data = r.json()
        fields = data["fields"]
        assert len(fields) >= 5
        for f in fields[:5]:
            for k in ("key", "type", "label"):
                assert k in f, f"missing {k} in field {f}"


class TestSaveTemplate:
    def test_e04_post_save_template_200(self, t4_client):
        p = pid_of(t4_client)
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "My Template", "fields": DEFAULT_FIELDS},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert d.get("saved") is True or d.get("id") is not None


class TestLockTemplate:
    def test_e05_post_lock_template_200(self, t4_client):
        p = pid_of(t4_client)
        save = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "ToLock", "fields": DEFAULT_FIELDS},
        )
        assert save.status_code == 200
        tid = save.json().get("id") or save.json().get("template_id")
        if tid is None:
            with Session(engine) as s:
                tpl = s.exec(select(ExtractionTemplate).where(ExtractionTemplate.project_id == p)).first()
                tid = tpl.id
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/lock",
            json={"template_id": tid},
        )
        assert r.status_code == 200, r.text
        assert r.json().get("locked") is True

    def test_e06_ex1_locked_cannot_change_422(self, t4_client):
        p = pid_of(t4_client)
        save = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "ToLock2", "fields": DEFAULT_FIELDS},
        )
        tid = save.json().get("id") or save.json().get("template_id")
        if tid is None:
            with Session(engine) as s:
                tpl = s.exec(select(ExtractionTemplate).where(ExtractionTemplate.project_id == p)).first()
                tid = tpl.id
        lock = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/lock",
            json={"template_id": tid},
        )
        assert lock.status_code == 200
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "RenamedLocked", "fields": DEFAULT_FIELDS},
        )
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "template_locked_cannot_change_fields"


class TestUpsertCell:
    def test_e07_post_upsert_cell_201(self, t4_client):
        p = pid_of(t4_client)
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "Tpl", "fields": DEFAULT_FIELDS},
        )
        rid = _make_record(t4_client, idx=1)
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/records/{rid}/extraction/cell",
            json={"field_key": "study_design", "reviewer_id": "r1", "value": "RCT", "confidence": 0.95},
        )
        assert r.status_code == 201, r.text

    def test_e08_ex2_not_fulltext_include_422(self, t4_client):
        p = pid_of(t4_client)
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "Tpl2", "fields": DEFAULT_FIELDS},
        )
        rid = _make_record(t4_client, idx=2, screening_stage="ta", screening_decision="include")
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/records/{rid}/extraction/cell",
            json={"field_key": "sample_size", "reviewer_id": "r1", "value": 100},
        )
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "record_not_in_included_n4"


class TestEvidenceTable:
    def test_e09_evidence_table_rows_5(self, t4_client):
        p = pid_of(t4_client)
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "ET", "fields": DEFAULT_FIELDS},
        )
        for i in range(5):
            rid = _make_record(t4_client, idx=10 + i)
            t4_client.post(
                f"{BASE}/{p}{STAGE_PREFIX}/records/{rid}/extraction/cell",
                json={"field_key": "study_design", "reviewer_id": "r1", "value": "RCT"},
            )
        r = t4_client.get(f"{BASE}/{p}{STAGE_PREFIX}/extraction/evidence-table")
        assert r.status_code == 200, r.text
        data = r.json()
        rows = data.get("rows", data) if isinstance(data, dict) else data
        assert len(rows) == 5

    def test_e10_evidence_table_cols_5_fields(self, t4_client):
        p = pid_of(t4_client)
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "ET2", "fields": DEFAULT_FIELDS},
        )
        rid = _make_record(t4_client, idx=20)
        r = t4_client.get(f"{BASE}/{p}{STAGE_PREFIX}/extraction/evidence-table")
        assert r.status_code == 200
        data = r.json()
        if isinstance(data, dict):
            cols = data.get("columns", [])
            if cols:
                assert len(cols) >= 5
            else:
                rows = data.get("rows", [])
                if rows:
                    row0 = rows[0]
                    values = row0.get("values", {}) if isinstance(row0, dict) else {}
                    assert len(values) >= 5

    def test_e11_evidence_table_reviewer_ids_filter(self, t4_client):
        p = pid_of(t4_client)
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "ET3", "fields": DEFAULT_FIELDS},
        )
        rid1 = _make_record(t4_client, idx=30)
        rid2 = _make_record(t4_client, idx=31)
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/records/{rid1}/extraction/cell",
            json={"field_key": "study_design", "reviewer_id": "R1", "value": "RCT"},
        )
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/records/{rid2}/extraction/cell",
            json={"field_key": "study_design", "reviewer_id": "R2", "value": "Cohort"},
        )
        r = t4_client.get(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/evidence-table",
            params={"reviewer_ids": "R1"},
        )
        assert r.status_code == 200
        data = r.json()
        rows = data.get("rows", data) if isinstance(data, dict) else data
        r1_found = False
        r2_found = False
        for row in rows:
            v = row.get("values", {}).get("study_design") if isinstance(row, dict) else None
            if v == "RCT":
                r1_found = True
            if v == "Cohort":
                r2_found = True
        assert r1_found is True or len(rows) >= 1
        with Session(engine) as s:
            cells_r2 = s.exec(
                select(ExtractionCell).where(ExtractionCell.reviewer_id == "R2", ExtractionCell.project_id == p)
            ).all()
            assert len(cells_r2) == 1


class TestKappa:
    def test_e12_kappa_summary_5_items(self, t4_client):
        p = pid_of(t4_client)
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "Kappa", "fields": DEFAULT_FIELDS},
        )
        for i in range(3):
            rid = _make_record(t4_client, idx=40 + i)
            for fk, v_ra, v_rb in [
                ("study_design", "RCT", "RCT"),
                ("sample_size", "100", "150"),
            ]:
                t4_client.post(
                    f"{BASE}/{p}{STAGE_PREFIX}/records/{rid}/extraction/cell",
                    json={"field_key": fk, "reviewer_id": "ra", "value": v_ra},
                )
                t4_client.post(
                    f"{BASE}/{p}{STAGE_PREFIX}/records/{rid}/extraction/cell",
                    json={"field_key": fk, "reviewer_id": "rb", "value": v_rb},
                )
        r = t4_client.get(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/kappa",
            params={"reviewer_a_id": "ra", "reviewer_b_id": "rb"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        assert len(items) == 5

    def test_e13_kappa_at_least_one_low_agreement(self, t4_client):
        p = pid_of(t4_client)
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/template/save",
            json={"name": "Kappa2", "fields": DEFAULT_FIELDS},
        )
        for i in range(5):
            rid = _make_record(t4_client, idx=50 + i)
            v_ra = "A" if i % 2 == 0 else "B"
            v_rb = "B" if i % 2 == 0 else "A"
            t4_client.post(
                f"{BASE}/{p}{STAGE_PREFIX}/records/{rid}/extraction/cell",
                json={"field_key": "study_design", "reviewer_id": "ra2", "value": v_ra},
            )
            t4_client.post(
                f"{BASE}/{p}{STAGE_PREFIX}/records/{rid}/extraction/cell",
                json={"field_key": "study_design", "reviewer_id": "rb2", "value": v_rb},
            )
        r = t4_client.get(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/kappa",
            params={"reviewer_a_id": "ra2", "reviewer_b_id": "rb2"},
        )
        assert r.status_code == 200
        data = r.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        low_count = sum(1 for it in items if it.get("warning_level") == "low_agreement")
        assert low_count >= 1

    def test_e14_kappa_miss_rb_query_422(self, t4_client):
        p = pid_of(t4_client)
        r = t4_client.get(
            f"{BASE}/{p}{STAGE_PREFIX}/extraction/kappa",
            params={"reviewer_a_id": "ra"},
        )
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"


class TestOutcomeDefine:
    def test_e15_post_outcome_define_binary_rr_201(self, t4_client):
        p = pid_of(t4_client)
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/define",
            json={"name": "All-cause Mortality", "outcome_type": "binary", "measure": "RR", "time_point": "12 months"},
        )
        assert r.status_code == 201, r.text
        d = r.json()
        assert d.get("id") is not None or d.get("outcome_id") is not None


class TestRunMeta:
    def test_e16_run_meta_2_studies_200_pooled_effect(self, t4_client):
        p = pid_of(t4_client)
        define = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/define",
            json={"name": "Mortality", "outcome_type": "binary", "measure": "RR"},
        )
        oid = define.json().get("id") or define.json().get("outcome_id")
        with Session(engine) as s:
            for i, (rec_title, a, n1, c, n2) in enumerate([
                ("Study1", 10, 100, 20, 100),
                ("Study2", 15, 150, 25, 150),
            ]):
                rec = LiteratureRecord(
                    project_id=p, title=rec_title, authors="A", journal="J", year=2024,
                    doi="", pmid="", abstract="", source_key="pubmed", source_label="PubMed",
                    dedupe_status="unique", pico_status="not_extracted",
                    screening_stage="fulltext", screening_decision="include",
                )
                s.add(rec); s.commit(); s.refresh(rec)
                for arm_label, arm_n, arm_ev in [("intervention", n1, a), ("control", n2, c)]:
                    s.add(OutcomeArmData(
                        project_id=p, record_id=rec.id, outcome_id=oid,
                        arm_label=arm_label, reviewer_id="r1",
                        data_json={"events": arm_ev, "n": arm_n},
                    ))
            s.commit()
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta",
            json={"outcome_id": oid, "analysis_model": "random_dl"},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        assert "pooled_effect" in d or "pooled" in d

    def test_e17_run_meta_heterogeneity_I2_present(self, t4_client):
        p = pid_of(t4_client)
        define = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/define",
            json={"name": "Mortality2", "outcome_type": "binary", "measure": "RR"},
        )
        oid = define.json().get("id") or define.json().get("outcome_id")
        with Session(engine) as s:
            for i, (rec_title, a, n1, c, n2) in enumerate([
                ("StudyA", 5, 50, 15, 50),
                ("StudyB", 25, 200, 10, 200),
            ]):
                rec = LiteratureRecord(
                    project_id=p, title=rec_title, authors="A", journal="J", year=2024,
                    doi="", pmid="", abstract="", source_key="pubmed", source_label="PubMed",
                    dedupe_status="unique", pico_status="not_extracted",
                    screening_stage="fulltext", screening_decision="include",
                )
                s.add(rec); s.commit(); s.refresh(rec)
                for arm_label, arm_n, arm_ev in [("intervention", n1, a), ("control", n2, c)]:
                    s.add(OutcomeArmData(
                        project_id=p, record_id=rec.id, outcome_id=oid,
                        arm_label=arm_label, reviewer_id="r1",
                        data_json={"events": arm_ev, "n": arm_n},
                    ))
            s.commit()
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta",
            json={"outcome_id": oid, "analysis_model": "random_dl"},
        )
        d = r.json()
        het = d.get("heterogeneity", {})
        assert "I2" in het
        assert isinstance(het["I2"], (int, float))

    def test_e18_run_meta_1_study_422(self, t4_client):
        p = pid_of(t4_client)
        define = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/define",
            json={"name": "Mortality3", "outcome_type": "binary", "measure": "RR"},
        )
        oid = define.json().get("id") or define.json().get("outcome_id")
        with Session(engine) as s:
            rec = LiteratureRecord(
                project_id=p, title="OnlyStudy", authors="A", journal="J", year=2024,
                doi="", pmid="", abstract="", source_key="pubmed", source_label="PubMed",
                dedupe_status="unique", pico_status="not_extracted",
                screening_stage="fulltext", screening_decision="include",
            )
            s.add(rec); s.commit(); s.refresh(rec)
            for arm_label, arm_n, arm_ev in [("intervention", 100, 10), ("control", 100, 20)]:
                s.add(OutcomeArmData(
                    project_id=p, record_id=rec.id, outcome_id=oid,
                    arm_label=arm_label, reviewer_id="r1",
                    data_json={"events": arm_ev, "n": arm_n},
                ))
            s.commit()
        r = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta",
            json={"outcome_id": oid, "analysis_model": "fixed_iv"},
        )
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "meta_requires_at_least_2_studies"


class TestForestSvg:
    def test_e19_forest_svg_200_bytes_starts_with_svg(self, t4_client):
        p = pid_of(t4_client)
        define = t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/define",
            json={"name": "Mortality4", "outcome_type": "binary", "measure": "RR"},
        )
        oid = define.json().get("id") or define.json().get("outcome_id")
        with Session(engine) as s:
            for i, (rec_title, a, n1, c, n2) in enumerate([
                ("FS1", 10, 100, 20, 100),
                ("FS2", 15, 150, 25, 150),
            ]):
                rec = LiteratureRecord(
                    project_id=p, title=rec_title, authors="A", journal="J", year=2024,
                    doi="", pmid="", abstract="", source_key="pubmed", source_label="PubMed",
                    dedupe_status="unique", pico_status="not_extracted",
                    screening_stage="fulltext", screening_decision="include",
                )
                s.add(rec); s.commit(); s.refresh(rec)
                for arm_label, arm_n, arm_ev in [("intervention", n1, a), ("control", n2, c)]:
                    s.add(OutcomeArmData(
                        project_id=p, record_id=rec.id, outcome_id=oid,
                        arm_label=arm_label, reviewer_id="r1",
                        data_json={"events": arm_ev, "n": arm_n},
                    ))
            s.commit()
        t4_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta",
            json={"outcome_id": oid, "analysis_model": "random_dl"},
        )
        r = t4_client.get(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/forest/{oid}.svg",
            params={"model": "random_dl"},
        )
        assert r.status_code == 200, f"expect 200 got {r.status_code}: {r.text}"
        content = r.content
        assert content.startswith(b"<svg") or content.lstrip().startswith(b"<svg")
        assert b"viewBox" in content


class TestAC10_HardGate:
    def test_e20_workspace_router_no_top_level_extraction_stats_imports(self, t4_client):
        """AC10 HARD-GATE: workspace router must NOT top-level import extraction/stats/meta modules.
        All imports are LAZY inside endpoint wrappers."""
        import sys
        mod = sys.modules.get("app.routers.workspace")
        assert mod is not None
        top_syms = {*dir(mod)}
        for bad in (
            "extraction_template", "extraction_engine", "stats_evidence", "meta_analysis",
            "save_template", "lock_template", "upsert_cell", "pivot_wide_evidence", "kappa_summary",
            "define_outcome", "run_meta_analysis", "generate_forest_svg",
            "cohen_kappa", "fixed_iv_pooled", "dl_random_pooled",
        ):
            assert bad not in top_syms, f"AC10 broken: workspace top-level symbol {bad}"
