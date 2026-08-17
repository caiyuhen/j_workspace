"""Wave83 T5 15 pytest: Outcome CRUD + ArmData dual-mode + Rules EX3-EX8 + AnalysisRun cache.

Zero-network. Uses conftest reset_database autouse fixture.
15 tests grouped A-H (5+2+1+1+1+2+2+1=15).
"""
from __future__ import annotations
import json
import math
from fastapi.testclient import TestClient
from sqlmodel import Session, select
import pytest
from app.db import engine
from app.main import app
from app.models import (
    LiteratureRecord, OutcomeDefinition, OutcomeArmData, AnalysisRun,
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
    assert login.status_code == 200, f"dev-login: {login.status_code} {login.text}"
    token = login.json()["token"]
    project = client.post(
        "/api/projects",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "organization_slug": "demo-hospital",
            "owner_user_id": "u-001",
            "name": "Wave83 T5 Outcome Meta Project",
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
    c = TestClient(app)
    token, pid = _bootstrap(c)
    c.headers.update(_auth(token))
    c.__dict__["_t5_pid"] = pid
    yield c


def pid_of(c) -> int:
    return c._t5_pid  # type: ignore[attr-defined]


BASE = "/api/workspace/projects"
STAGE_PREFIX = "/stages"


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


def _define_outcome(c, name="Outcome A", outcome_type="binary", measure="RR", time_point=None):
    p = pid_of(c)
    r = c.post(
        f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/define",
        json={
            "name": name,
            "outcome_type": outcome_type,
            "measure": measure,
            **({"time_point": time_point} if time_point else {}),
        },
    )
    assert r.status_code == 201, f"define outcome: {r.status_code} {r.text}"
    return r.json()["id"]


def _upsert_arm(c, oid, rid, arm_label, binary_data=None, continuous_data=None):
    p = pid_of(c)
    payload = {
        "outcome_id": oid,
        "record_id": rid,
        "arm_label": arm_label,
        "reviewer_id": "r1",
    }
    if binary_data is not None:
        payload["binary_data"] = binary_data
    if continuous_data is not None:
        payload["continuous_data"] = continuous_data
    r = c.post(
        f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/{oid}/arm-data",
        json=payload,
    )
    return r


# ============================================================
# A) Outcome CRUD 5
# ============================================================

class TestA_OutcomeCRUD:
    def test_a1_define_outcome_binary_rr_201_with_id(self, t5_client):
        p = pid_of(t5_client)
        r = t5_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/define",
            json={"name": "All-cause Mortality", "outcome_type": "binary", "measure": "RR", "time_point": "12 months"},
        )
        assert r.status_code == 201, r.text
        d = r.json()
        assert "id" in d
        assert isinstance(d["id"], int)
        assert d["id"] > 0

    def test_a2_define_outcome_continuous_md_201(self, t5_client):
        p = pid_of(t5_client)
        r = t5_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/define",
            json={"name": "Systolic BP Reduction", "outcome_type": "continuous", "measure": "MD", "time_point": "6 months"},
        )
        assert r.status_code == 201, r.text
        d = r.json()
        assert "id" in d
        assert isinstance(d["id"], int)

    def test_a3_list_all_outcomes_count_2(self, t5_client):
        oid1 = _define_outcome(t5_client, name="Mortality", outcome_type="binary", measure="RR")
        oid2 = _define_outcome(t5_client, name="BP", outcome_type="continuous", measure="MD")
        p = pid_of(t5_client)
        r = t5_client.get(f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes")
        assert r.status_code == 200, r.text
        d = r.json()
        items = d.get("items", d) if isinstance(d, dict) else d
        assert len(items) == 2

    def test_a4_rename_outcome_success(self, t5_client):
        oid = _define_outcome(t5_client, name="Old Name", outcome_type="binary", measure="RR")
        p = pid_of(t5_client)
        r = t5_client.patch(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/{oid}",
            json={"name": "New Name"},
        )
        assert r.status_code == 200, r.text
        with Session(engine) as s:
            od = s.get(OutcomeDefinition, oid)
            assert od.label == "New Name"

    def test_a5_delete_outcome_count_0(self, t5_client):
        oid = _define_outcome(t5_client, name="To Delete", outcome_type="binary", measure="RR")
        p = pid_of(t5_client)
        r = t5_client.delete(f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes/{oid}")
        assert r.status_code == 200, r.text
        r2 = t5_client.get(f"{BASE}/{p}{STAGE_PREFIX}/analysis/outcomes")
        d = r2.json()
        items = d.get("items", d) if isinstance(d, dict) else d
        assert len(items) == 0


# ============================================================
# B) OutcomeArmData dual-mode RULE EX3-EX4 2
# ============================================================

class TestB_ArmDataDualModeMismatch:
    def test_b1_ex3_binary_received_continuous_422_literal(self, t5_client):
        oid = _define_outcome(t5_client, name="Mortality", outcome_type="binary", measure="RR")
        rid = _make_record(t5_client, idx=1)
        r = _upsert_arm(t5_client, oid, rid, "intervention", continuous_data={"mean_val": 5.2, "sd_val": 1.1, "n": 100})
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "outcome_type_mismatch_expected_binary_arms"

    def test_b2_ex4_continuous_received_binary_422_literal(self, t5_client):
        oid = _define_outcome(t5_client, name="BP", outcome_type="continuous", measure="MD")
        rid = _make_record(t5_client, idx=2)
        r = _upsert_arm(t5_client, oid, rid, "intervention", binary_data={"events": 10, "n": 100})
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "outcome_type_mismatch_expected_continuous"


# ============================================================
# C) OutcomeArmData binary RULE EX6 1
# ============================================================

class TestC_BinaryEventsGtTotal:
    def test_c1_ex6_a25_gt_n1_10_invalid_422_literal(self, t5_client):
        oid = _define_outcome(t5_client, name="Mortality", outcome_type="binary", measure="RR")
        rid = _make_record(t5_client, idx=3)
        r = _upsert_arm(t5_client, oid, rid, "intervention", binary_data={"events": 25, "n": 10})
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "2x2_events_gt_total_n_invalid"


# ============================================================
# D) OutcomeArmData continuous RULE EX7 1
# ============================================================

class TestD_ContinuousSdOrNInvalid:
    def test_d1_ex7_sd0_n1_nonpositive_422_literal(self, t5_client):
        oid = _define_outcome(t5_client, name="BP", outcome_type="continuous", measure="MD")
        rid = _make_record(t5_client, idx=4)
        r = _upsert_arm(t5_client, oid, rid, "intervention", continuous_data={"mean_val": 120.0, "sd_val": 0.0, "n": 1})
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "continuous_sd_or_n_invalid_nonpositive"


# ============================================================
# E) Run Meta RULE EX5 1
# ============================================================

class TestE_MetaRequires2Studies:
    def test_e1_ex5_k1_only_1_study_422_literal(self, t5_client):
        oid = _define_outcome(t5_client, name="Mortality", outcome_type="binary", measure="RR")
        rid = _make_record(t5_client, idx=5)
        _upsert_arm(t5_client, oid, rid, "intervention", binary_data={"events": 10, "n": 100})
        _upsert_arm(t5_client, oid, rid, "control", binary_data={"events": 20, "n": 100})
        p = pid_of(t5_client)
        r = t5_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta",
            json={"outcome_id": oid, "analysis_model": "fixed_iv"},
        )
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "meta_requires_at_least_2_studies"


# ============================================================
# F) Run Meta pooled + heterogeneity I2 2
# ============================================================

def _seed_2_binary_studies(c, oid):
    for i, (rec_title, a, n1, c_arm, n2) in enumerate([
        ("Study1", 10, 100, 20, 100),
        ("Study2", 15, 150, 25, 150),
    ]):
        rid = _make_record(c, idx=10 + i, title=rec_title)
        _upsert_arm(c, oid, rid, "intervention", binary_data={"events": a, "n": n1})
        _upsert_arm(c, oid, rid, "control", binary_data={"events": c_arm, "n": n2})


class TestF_PooledAndHeterogeneity:
    def test_f1_binary_rr_fixed_iv_pooled_effect_float_not_nan(self, t5_client):
        oid = _define_outcome(t5_client, name="Mortality", outcome_type="binary", measure="RR")
        _seed_2_binary_studies(t5_client, oid)
        p = pid_of(t5_client)
        r = t5_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta",
            json={"outcome_id": oid, "analysis_model": "fixed_iv"},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        pe = d.get("pooled_effect", {})
        val = pe.get("value")
        assert isinstance(val, (int, float))
        assert not (isinstance(val, float) and math.isnan(val))

    def test_f2_random_dl_tau2_ge0_I2_valid(self, t5_client):
        oid = _define_outcome(t5_client, name="Mortality", outcome_type="binary", measure="RR")
        _seed_2_binary_studies(t5_client, oid)
        p = pid_of(t5_client)
        r = t5_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta",
            json={"outcome_id": oid, "analysis_model": "random_dl"},
        )
        assert r.status_code == 200, r.text
        d = r.json()
        pe = d.get("pooled_effect", {})
        het = d.get("heterogeneity", {})
        tau2 = pe.get("tau2", het.get("tau2", -1.0))
        assert tau2 >= 0.0, f"tau2={tau2} expected >=0"
        i2 = het.get("I2", het.get("I2_pct", -1.0))
        assert isinstance(i2, (int, float))
        assert -0.01 <= i2 <= 100.01, f"I2={i2} expected in [0,100]"


# ============================================================
# G) AnalysisRun idempotent cache 2
# ============================================================

class TestG_AnalysisRunIdempotentCache:
    def test_g1_run_twice_same_model_cache_hit_same_result(self, t5_client):
        oid = _define_outcome(t5_client, name="Mortality", outcome_type="binary", measure="RR")
        _seed_2_binary_studies(t5_client, oid)
        p = pid_of(t5_client)
        payload = {"outcome_id": oid, "analysis_model": "fixed_iv"}
        r1 = t5_client.post(f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta", json=payload)
        assert r1.status_code == 200
        d1 = r1.json()
        run1_id = d1.get("id") or d1.get("result_json", {}).get("id")
        with Session(engine) as s:
            rows1 = list(s.exec(select(AnalysisRun).where(
                AnalysisRun.outcome_id == oid,
                AnalysisRun.method == "fixed_iv",
            )).all())
            assert len(rows1) == 1
            run1_created = rows1[0].created_at
        r2 = t5_client.post(f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta", json=payload)
        assert r2.status_code == 200
        d2 = r2.json()
        with Session(engine) as s:
            rows2 = list(s.exec(select(AnalysisRun).where(
                AnalysisRun.outcome_id == oid,
                AnalysisRun.method == "fixed_iv",
            )).all())
            assert len(rows2) == 1
            assert rows2[0].created_at == run1_created
        pooled1 = d1.get("pooled_effect", {}).get("value")
        pooled2 = d2.get("pooled_effect", {}).get("value")
        assert pooled1 == pooled2

    def test_g2_arms_updated_cache_cleared_new_result(self, t5_client):
        oid = _define_outcome(t5_client, name="Mortality", outcome_type="binary", measure="RR")
        _seed_2_binary_studies(t5_client, oid)
        p = pid_of(t5_client)
        payload = {"outcome_id": oid, "analysis_model": "fixed_iv"}
        r1 = t5_client.post(f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta", json=payload)
        assert r1.status_code == 200
        d1 = r1.json()
        pe1 = d1.get("pooled_effect", {}).get("value")
        with Session(engine) as s:
            rec3 = LiteratureRecord(
                project_id=p, title="Study3", authors="A3", journal="J", year=2024,
                doi="", pmid="", abstract="", source_key="pubmed", source_label="PubMed",
                dedupe_status="unique", pico_status="not_extracted",
                screening_stage="fulltext", screening_decision="include",
            )
            s.add(rec3); s.commit(); s.refresh(rec3)
            rid3 = rec3.id
        _upsert_arm(t5_client, oid, rid3, "intervention", binary_data={"events": 50, "n": 200})
        _upsert_arm(t5_client, oid, rid3, "control", binary_data={"events": 40, "n": 200})
        r2 = t5_client.post(f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta", json=payload)
        assert r2.status_code == 200
        d2 = r2.json()
        pe2 = d2.get("pooled_effect", {}).get("value")
        assert pe1 != pe2, f"expected different pooled values, both got {pe1}"


# ============================================================
# H) RULE EX8 Σwi=0 1
# ============================================================

class TestH_ZeroTotalWeight:
    def test_h1_ex8_infinite_se_all_zero_weight_422_literal(self, t5_client):
        oid = _define_outcome(t5_client, name="BP Extreme", outcome_type="continuous", measure="MD")
        rid1 = _make_record(t5_client, idx=20, title="Edge1")
        rid2 = _make_record(t5_client, idx=21, title="Edge2")
        huge_sd = float("1e200")
        _upsert_arm(t5_client, oid, rid1, "intervention", continuous_data={"mean_val": 120.0, "sd_val": huge_sd, "n": 5})
        _upsert_arm(t5_client, oid, rid1, "control", continuous_data={"mean_val": 125.0, "sd_val": huge_sd, "n": 5})
        _upsert_arm(t5_client, oid, rid2, "intervention", continuous_data={"mean_val": 118.0, "sd_val": huge_sd, "n": 5})
        _upsert_arm(t5_client, oid, rid2, "control", continuous_data={"mean_val": 122.0, "sd_val": huge_sd, "n": 5})
        p = pid_of(t5_client)
        r = t5_client.post(
            f"{BASE}/{p}{STAGE_PREFIX}/analysis/run-meta",
            json={"outcome_id": oid, "analysis_model": "fixed_iv"},
        )
        assert r.status_code == 422, f"expect 422 got {r.status_code}: {r.text}"
        assert r.json()["detail"] == "zero_total_weight_cannot_compute_pooled"
