from __future__ import annotations

import json
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.db import engine
from app.main import app
from app.models import LiteratureRecord, ResearchProject, User

from app.services.extraction_template import (
    get_project_template,
    save_template,
    lock_template,
)
from app.services.extraction_engine import (
    upsert_cell,
    pivot_wide_evidence,
    kappa_summary,
)


def _bootstrap(client: TestClient) -> tuple[str, int]:
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
    assert login.status_code == 200
    token = login.json()["token"]
    project = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "Wave83 T2 Extraction Project",
            "description": "test",
        },
    )
    assert project.status_code == 201
    pid = int(project.json()["id"])
    return token, pid


@pytest.fixture(name="t2_client")
def _t2_client():
    c = TestClient(app)
    _bootstrap(c)
    yield c


def _pid_of_client() -> int:
    with Session(engine) as s:
        p = s.exec(select(ResearchProject).order_by(ResearchProject.id.desc())).first()
        assert p is not None
        return p.id


def _five_fields():
    return [
        {"key": "f_pop", "type": "text", "label": "Population", "name": "Population",
         "pico_binding": "P", "required": True, "options": None,
         "description": "Study population", "help": "Describe the population"},
        {"key": "f_intv", "type": "text", "label": "Intervention", "name": "Intervention",
         "pico_binding": "I", "required": True, "options": None,
         "description": "Intervention arm", "help": "Describe intervention"},
        {"key": "f_comp", "type": "text", "label": "Comparator", "name": "Comparator",
         "pico_binding": "C", "required": True, "options": None,
         "description": "Comparator arm", "help": "Describe comparator"},
        {"key": "f_outc", "type": "categorical", "label": "Outcome", "name": "Outcome",
         "pico_binding": "O", "required": True,
         "options": ["mortality", "hf_hospitalization", "both"],
         "description": "Primary outcome", "help": "Primary endpoint"},
        {"key": "f_design", "type": "categorical", "label": "Study Design", "name": "Study Design",
         "pico_binding": None, "required": False,
         "options": ["RCT", "observational", "other"],
         "description": "Design type", "help": "Study design"},
    ]


# ============================================================================
# A) Template CRUD 7 tests
# ============================================================================
class TestTemplateCRUD:
    def test_a01_get_none_on_fresh_project(self, t2_client):
        pid = _pid_of_client()
        with Session(engine) as db:
            t = get_project_template(db, pid)
            assert t is None

    def test_a02_save_first_template(self, t2_client):
        pid = _pid_of_client()
        with Session(engine) as db:
            t = save_template(db, pid, name="T1 v1", fields=_five_fields(), created_by="u-001")
            assert t.id is not None
            assert t.project_id == pid
            assert t.name == "T1 v1"
            assert t.locked is False
            assert len(t.fields_json) == 5

    def test_a03_save_update_fields_before_lock(self, t2_client):
        pid = _pid_of_client()
        with Session(engine) as db:
            t1 = save_template(db, pid, name="T1 v1", fields=_five_fields(), created_by="u-001")
            f2 = _five_fields()
            f2[0]["label"] = "Pop v2"
            t2 = save_template(db, pid, name="T1 v2", fields=f2, created_by="u-001")
            assert t2.id == t1.id
            assert t2.name == "T1 v2"
            assert t2.fields_json[0]["label"] == "Pop v2"

    def test_a04_save_update_description_only_allowed_before_lock(self, t2_client):
        pid = _pid_of_client()
        with Session(engine) as db:
            t1 = save_template(db, pid, name="T1 v1", fields=_five_fields(), created_by="u-001")
            f2 = _five_fields()
            f2[0]["description"] = "New desc"
            f2[0]["help"] = "New help"
            t2 = save_template(db, pid, name="T1 v1", fields=f2, created_by="u-001")
            assert t2.id == t1.id
            assert t2.fields_json[0]["description"] == "New desc"
            assert t2.fields_json[0]["help"] == "New help"

    def test_a05_lock_returns_locked_true(self, t2_client):
        pid = _pid_of_client()
        with Session(engine) as db:
            t1 = save_template(db, pid, name="T1", fields=_five_fields(), created_by="u-001")
            t2 = lock_template(db, t1.id)
            assert t2.locked is True
            assert t2.id == t1.id

    def test_a06_lock_twice_is_noop(self, t2_client):
        pid = _pid_of_client()
        with Session(engine) as db:
            t1 = save_template(db, pid, name="T1", fields=_five_fields(), created_by="u-001")
            t2 = lock_template(db, t1.id)
            t3 = lock_template(db, t1.id)
            assert t2.locked is True
            assert t3.locked is True
            assert t2.id == t3.id

    def test_a07_save_second_template_upserts_same_project_only_one(self, t2_client):
        pid = _pid_of_client()
        with Session(engine) as db:
            t1 = save_template(db, pid, name="T1", fields=_five_fields(), created_by="u-001")
            f2 = _five_fields()
            f2[0]["label"] = "Pop v3"
            t2 = save_template(db, pid, name="T1 v3", fields=f2, created_by="u-001")
            assert t2.id == t1.id
            all_t = db.exec(select(ResearchProject)).all()
            from app.models import ExtractionTemplate
            cnt = db.exec(select(ExtractionTemplate).where(ExtractionTemplate.project_id == pid)).all()
            assert len(cnt) == 1


# ============================================================================
# B) Rule EX1 7 tests (locked -> changes 422 template_locked_cannot_change_fields)
# ============================================================================
class TestRuleEX1Locked:
    def _lock_template(self, pid):
        with Session(engine) as db:
            t = save_template(db, pid, name="LockedT", fields=_five_fields(), created_by="u-001")
            t = lock_template(db, t.id)
            return t

    def test_b01_locked_change_name_422(self, t2_client):
        pid = _pid_of_client()
        self._lock_template(pid)
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                save_template(db, pid, name="NEWNAME", fields=_five_fields(), created_by="u-001")
            assert "template_locked_cannot_change_fields" in str(exc.value)

    def test_b02_locked_change_field_key_422(self, t2_client):
        pid = _pid_of_client()
        self._lock_template(pid)
        bad_fields = _five_fields()
        bad_fields[0]["key"] = "f_pop_changed"
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                save_template(db, pid, name="LockedT", fields=bad_fields, created_by="u-001")
            assert "template_locked_cannot_change_fields" in str(exc.value)

    def test_b03_locked_change_field_type_422(self, t2_client):
        pid = _pid_of_client()
        self._lock_template(pid)
        bad_fields = _five_fields()
        bad_fields[0]["type"] = "categorical"
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                save_template(db, pid, name="LockedT", fields=bad_fields, created_by="u-001")
            assert "template_locked_cannot_change_fields" in str(exc.value)

    def test_b04_locked_change_field_pico_binding_422(self, t2_client):
        pid = _pid_of_client()
        self._lock_template(pid)
        bad_fields = _five_fields()
        bad_fields[0]["pico_binding"] = "I"
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                save_template(db, pid, name="LockedT", fields=bad_fields, created_by="u-001")
            assert "template_locked_cannot_change_fields" in str(exc.value)

    def test_b05_locked_change_field_required_422(self, t2_client):
        pid = _pid_of_client()
        self._lock_template(pid)
        bad_fields = _five_fields()
        bad_fields[0]["required"] = False
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                save_template(db, pid, name="LockedT", fields=bad_fields, created_by="u-001")
            assert "template_locked_cannot_change_fields" in str(exc.value)

    def test_b06_locked_change_field_options_422(self, t2_client):
        pid = _pid_of_client()
        self._lock_template(pid)
        bad_fields = _five_fields()
        bad_fields[3]["options"] = ["mortality"]
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                save_template(db, pid, name="LockedT", fields=bad_fields, created_by="u-001")
            assert "template_locked_cannot_change_fields" in str(exc.value)

    def test_b07_locked_remove_one_field_422(self, t2_client):
        pid = _pid_of_client()
        self._lock_template(pid)
        bad_fields = _five_fields()[:-1]
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                save_template(db, pid, name="LockedT", fields=bad_fields, created_by="u-001")
            assert "template_locked_cannot_change_fields" in str(exc.value)


# ============================================================================
# C) Rule EX2 3 tests (not include+fulltext -> 422 record_not_in_included_n4)
# ============================================================================
class TestRuleEX2NotIncludedN4:
    def _make_row(self, pid, **kw):
        with Session(engine) as s:
            rec = LiteratureRecord(
                project_id=pid,
                title="T", authors="A", journal="J", year=2024,
                doi="", pmid="", abstract="",
                source_key="pubmed", source_label="PubMed",
                dedupe_status="unique", pico_status="not_extracted",
                screening_stage=kw.get("screening_stage", None),
                screening_decision=kw.get("screening_decision", None),
            )
            s.add(rec); s.commit(); s.refresh(rec); return rec.id

    def _save_template_and_get_field(self, pid):
        with Session(engine) as db:
            save_template(db, pid, name="T", fields=_five_fields(), created_by="u-001")
        return "f_pop"

    def test_c01_decision_exclude_stage_ta_422(self, t2_client):
        pid = _pid_of_client()
        fk = self._save_template_and_get_field(pid)
        rid = self._make_row(pid, screening_decision="exclude", screening_stage="ta")
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                upsert_cell(db, pid, rid, fk, "r1", "hello")
            assert "record_not_in_included_n4" in str(exc.value)

    def test_c02_decision_none_stage_none_422(self, t2_client):
        pid = _pid_of_client()
        fk = self._save_template_and_get_field(pid)
        rid = self._make_row(pid, screening_decision=None, screening_stage=None)
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                upsert_cell(db, pid, rid, fk, "r1", "hello")
            assert "record_not_in_included_n4" in str(exc.value)

    def test_c03_decision_include_stage_ta_422(self, t2_client):
        pid = _pid_of_client()
        fk = self._save_template_and_get_field(pid)
        rid = self._make_row(pid, screening_decision="include", screening_stage="ta")
        with Session(engine) as db:
            with pytest.raises(Exception) as exc:
                upsert_cell(db, pid, rid, fk, "r1", "hello")
            assert "record_not_in_included_n4" in str(exc.value)


# ============================================================================
# D) Pivot Wide 4 tests
# ============================================================================
class TestPivotWideEvidence:
    def _setup_full(self):
        pid = _pid_of_client()
        rids = []
        with Session(engine) as s:
            save_template(s, pid, name="T", fields=_five_fields(), created_by="u-001")
            for i in range(5):
                rec = LiteratureRecord(
                    project_id=pid, title=f"Study{i}", authors=f"A{i}", journal="J", year=2024,
                    doi="", pmid="", abstract=f"abs{i}",
                    source_key="pubmed", source_label="PubMed",
                    dedupe_status="unique", pico_status="not_extracted",
                    screening_stage="fulltext", screening_decision="include",
                )
                s.add(rec); s.flush(); rids.append(rec.id)
            s.commit()
        fields = _five_fields()
        fkeys = [f["key"] for f in fields]
        reviewers = ["r_alice", "r_bob"]
        for rid in rids:
            for fk in fkeys:
                for rv in reviewers:
                    val = f"{rv}_{rid}_{fk}"
                    with Session(engine) as db:
                        upsert_cell(db, pid, rid, fk, rv, val)
        return pid, rids, fkeys, reviewers

    def test_d01_pivot_rows_equals_5(self, t2_client):
        pid, rids, _, _ = self._setup_full()
        with Session(engine) as db:
            rows = pivot_wide_evidence(db, pid)
            assert len(rows) == 5
            got_ids = sorted([r.record_id for r in rows])
            assert got_ids == sorted(rids)

    def test_d02_pivot_cols_are_5_field_keys(self, t2_client):
        pid, _, fkeys, _ = self._setup_full()
        with Session(engine) as db:
            rows = pivot_wide_evidence(db, pid)
            for r in rows:
                assert set(r.values.keys()) == set(fkeys)

    def test_d03_reviewer_ids_empty_merges_all_reviewers(self, t2_client):
        pid, rids, fkeys, reviewers = self._setup_full()
        with Session(engine) as db:
            rows = pivot_wide_evidence(db, pid, reviewer_ids=[])
            assert len(rows) == 5
            for r in rows:
                for fk in fkeys:
                    v = r.values[fk]
                    assert v is not None
                    val_str = str(v)
                    assert any(rv in val_str for rv in reviewers)

    def test_d04_reviewer_ids_R1_only_R1_values(self, t2_client):
        pid, rids, fkeys, reviewers = self._setup_full()
        R1 = reviewers[0]
        R2 = reviewers[1]
        with Session(engine) as db:
            rows = pivot_wide_evidence(db, pid, reviewer_ids=[R1])
            assert len(rows) == 5
            for r in rows:
                for fk in fkeys:
                    v = r.values[fk]
                    val_str = str(v) if v is not None else ""
                    assert R1 in val_str
                    assert R2 not in val_str


# ============================================================================
# E) Kappa Summary 2 tests
# ============================================================================
class TestKappaSummary:
    def _setup_kappa(self):
        pid = _pid_of_client()
        rids = []
        with Session(engine) as s:
            save_template(s, pid, name="T", fields=_five_fields(), created_by="u-001")
            for i in range(5):
                rec = LiteratureRecord(
                    project_id=pid, title=f"Study{i}", authors=f"A{i}", journal="J", year=2024,
                    doi="", pmid="", abstract=f"abs{i}",
                    source_key="pubmed", source_label="PubMed",
                    dedupe_status="unique", pico_status="not_extracted",
                    screening_stage="fulltext", screening_decision="include",
                )
                s.add(rec); s.flush(); rids.append(rec.id)
            s.commit()
        fkeys = [f["key"] for f in _five_fields()]
        R_A, R_B = "r_a", "r_b"
        for rid_idx, rid in enumerate(rids):
            for fk_idx, fk in enumerate(fkeys):
                if fk_idx == 0:
                    vA = vB = f"agree_{rid_idx}"
                elif fk_idx == 1:
                    if rid_idx % 2 == 0:
                        vA, vB = "x", "x"
                    else:
                        vA, vB = "x", "y"
                else:
                    vA = f"a{rid_idx}_{fk_idx}"
                    vB = f"b{rid_idx}_{fk_idx}"
                with Session(engine) as db:
                    upsert_cell(db, pid, rid, fk, R_A, vA)
                    upsert_cell(db, pid, rid, fk, R_B, vB)
        return pid, R_A, R_B, fkeys

    def test_e01_summary_len_equals_5_fields(self, t2_client):
        pid, R_A, R_B, fkeys = self._setup_kappa()
        with Session(engine) as db:
            summary = kappa_summary(db, pid, R_A, R_B)
            assert len(summary) == 5
            got_keys = sorted([s.field_key for s in summary])
            assert got_keys == sorted(fkeys)

    def test_e02_any_low_agreement_true(self, t2_client):
        pid, R_A, R_B, _ = self._setup_kappa()
        with Session(engine) as db:
            summary = kappa_summary(db, pid, R_A, R_B)
            warnings = [s for s in summary if s.warning_level == "low_agreement"]
            assert any(s.warning_level == "low_agreement" for s in summary) is True
            assert len(warnings) >= 1
