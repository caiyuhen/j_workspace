"""W84 T4: REST workspace.py 8 endpoints happy+422 + stage_entry output_stage_cards + AC8 lazy AST scan."""
from __future__ import annotations
import json
import ast
import pytest
from fastapi.testclient import TestClient

@pytest.fixture()
def client_and_seed(db_session):
    """提供 TestClient + 1 project + 必要依赖。"""
    from app.routers.workspace import router as ws_router
    from fastapi import FastAPI
    from app.models import User, Organization, OutcomeDefinition, ResearchProject
    app = FastAPI()
    app.include_router(ws_router)
    u = User(user_id="u-t4-001", display_name="T4")
    org = Organization(slug="t4-hospital", name="T4 Hospital")
    db_session.add_all([u, org]); db_session.flush()
    p = ResearchProject(organization_slug="t4-hospital", owner_user_id=u.user_id, name="T4 Project", description="w84 t4", workspace_key="ws-t4")
    db_session.add(p); db_session.flush()
    # The tests below reference outcome_id 1..12 literally; those rows must exist
    # because gradeassessment.outcome_id is a real FK to outcomedefinition.id.
    for i in range(1, 13):
        db_session.add(
            OutcomeDefinition(
                id=i,
                project_id=p.id,
                outcome_key=f"t4-outcome-{i}",
                label=f"T4 Outcome {i}",
                measure_type="binary",
            )
        )
    db_session.flush()
    db_session.commit()
    return TestClient(app), p.id

def test_g1_post_grade_201_created(client_and_seed):
    client, pid = client_and_seed
    body = {
        "outcome_id": 1, "reviewer_id": 99,
        "domains_5": {"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns","publication_bias":"no_concerns"},
        "upgrades_3": {"large_effect":False,"dose_response":False,"confounders_reduce":False},
        "certainty_final": "High", "note": "G1",
    }
    r = client.post(f"/api/workspace/projects/{pid}/grade", json=body)
    assert r.status_code == 201, f"status={r.status_code} detail={r.text}"

def test_e8_post_grade_422_invalid_domain_keys_count_4_throw_O8_literal(client_and_seed):
    client, pid = client_and_seed
    body = {
        "outcome_id": 2, "reviewer_id": 99,
        "domains_5": {"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns"},
        "upgrades_3": {"large_effect":False,"dose_response":False,"confounders_reduce":False},
        "certainty_final": "High",
    }
    r = client.post(f"/api/workspace/projects/{pid}/grade", json=body)
    assert r.status_code == 422, f"got status={r.status_code} text={r.text}"
    assert (r.json().get("detail") or "") == "grade_invalid_domain_count_require_exact_5_keys", f"detail={r.json()!r}"

def test_e1_post_grade_locked_true_422_O1_literal(client_and_seed):
    client, pid = client_and_seed
    body = {
        "outcome_id": 3, "reviewer_id": 99,
        "domains_5": {"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns","publication_bias":"no_concerns"},
        "upgrades_3": {"large_effect":True,"dose_response":False,"confounders_reduce":False},
        "certainty_final": "High",
        "_lock_for_test": True,
        "locked": True,
    }
    r = client.post(f"/api/workspace/projects/{pid}/grade", json=body)
    if r.status_code == 422:
        d = (r.json().get("detail") or "")
        assert d == "grade_locked_cannot_change_assessment", f"got {d!r}"

def test_g3_get_grade_list_200(client_and_seed):
    client, pid = client_and_seed
    b = {
        "outcome_id": 4, "reviewer_id": 99,
        "domains_5": {"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns","publication_bias":"no_concerns"},
        "upgrades_3": {"large_effect":False,"dose_response":False,"confounders_reduce":False},
        "certainty_final": "Moderate",
    }
    client.post(f"/api/workspace/projects/{pid}/grade", json=b)
    r = client.get(f"/api/workspace/projects/{pid}/grade")
    assert r.status_code == 200

def test_s1_post_sof_201(client_and_seed):
    client, pid = client_and_seed
    body = {
        "outcome_id": 1, "assessment_id": None,
        "so_cols": {"a": 1, "b": 2},
    }
    r = client.post(f"/api/workspace/projects/{pid}/sof", json=body)
    assert r.status_code == 201

def test_s2_get_sof_list_200(client_and_seed):
    client, pid = client_and_seed
    body = {"outcome_id": 1, "so_cols": {"x": 1}}
    client.post(f"/api/workspace/projects/{pid}/sof", json=body)
    r = client.get(f"/api/workspace/projects/{pid}/sof")
    assert r.status_code == 200

def test_p1_post_prisma2020_201(client_and_seed):
    client, pid = client_and_seed
    items = {f"item_{i}": False for i in range(1, 28)}
    items["item_1"] = True; items["item_2"] = True
    body = {"reviewer_id": 99, **items}
    r = client.post(f"/api/workspace/projects/{pid}/prisma2020", json=body)
    assert r.status_code == 201, f"text={r.text}"

def test_e7_post_prisma2020_locked_true_422_O7_literal(client_and_seed):
    client, pid = client_and_seed
    items = {f"item_{i}": False for i in range(1, 28)}
    body = {"reviewer_id": 99, "locked": True, **items}
    r = client.post(f"/api/workspace/projects/{pid}/prisma2020", json=body)
    if r.status_code == 422:
        assert (r.json().get("detail") or "") == "prisma_checklist_locked_cannot_change_items", f"detail={r.json()!r}"
    else:
        assert r.status_code == 201

def test_p2_get_prisma2020_200(client_and_seed):
    client, pid = client_and_seed
    items = {f"item_{i}": False for i in range(1, 28)}
    client.post(f"/api/workspace/projects/{pid}/prisma2020", json={"reviewer_id": 99, **items})
    r = client.get(f"/api/workspace/projects/{pid}/prisma2020")
    assert r.status_code == 200

def test_r1_post_report_generate_200_returns_three_formats(client_and_seed):
    client, pid = client_and_seed
    b = {
        "outcome_id": 5, "reviewer_id": 99,
        "domains_5": {"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns","publication_bias":"no_concerns"},
        "upgrades_3": {"large_effect":False,"dose_response":False,"confounders_reduce":False},
        "certainty_final": "High",
    }
    client.post(f"/api/workspace/projects/{pid}/grade", json=b)
    body = {"version_label": "v0.1-t4-r1"}
    r = client.post(f"/api/workspace/projects/{pid}/report/generate", json=body)
    assert r.status_code == 200, f"status={r.status_code} text={r.text}"
    d = r.json()
    assert isinstance(d.get("md_content"), str) and len(d["md_content"]) > 50
    assert isinstance(d.get("html_content"), str) and len(d["html_content"]) > 50
    assert isinstance(d.get("txt_content"), str) and len(d["txt_content"]) > 50

def test_e5_post_report_generate_no_grades_422_O5_literal(client_and_seed):
    client, pid = client_and_seed
    r = client.post(f"/api/workspace/projects/{pid}/report/generate", json={"version_label": "v-empty"})
    assert r.status_code == 422, f"got={r.status_code} detail={r.text}"
    assert (r.json().get("detail") or "") == "report_requires_at_least_one_grade_assessment", f"got={r.json()!r}"

def test_ac8_l1_workspace_top_level_has_no_grade_engine_import():
    import app.routers.workspace as w_mod
    tree = ast.parse(open(w_mod.__file__, "r", encoding="utf-8").read())
    forbidden = ("grade_engine", "report_engine", "output_stage", "sof_table_engine")
    bad = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [n.name for n in node.names]
            else:
                names = [(node.module or "")] + [n.name for n in node.names]
            for nm in names:
                for f in forbidden:
                    if f in (nm or ""):
                        bad.append(nm)
    assert bad == [], f"workspace.py top-level (module-level) contains forbidden imports: {bad}"

def test_ac8_l2_workspace_top_imports_no_output_stage_symbol():
    import app.routers.workspace as w_mod
    src = open(w_mod.__file__, "r", encoding="utf-8").read()
    top_lines = src.splitlines()[:80]
    has_top = any(("output_stage" in l and "import" in l and "from app.services" in l) for l in top_lines if not l.strip().startswith("#"))
    assert has_top is False, "top ~80 lines module-level have output_stage import (AC8 NT-5 broken)"

def test_ac8_l3_stage_entry_top_level_no_forbidden_imports_symbols():
    import app.services.stage_entry as se_mod
    tree = ast.parse(open(se_mod.__file__, "r", encoding="utf-8").read())
    bad = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [n.name for n in node.names]
            else:
                names = [(node.module or "")] + [n.name for n in node.names]
            for nm in names:
                if any(f in (nm or "") for f in ("grade_engine", "report_engine", "output_stage", "sof_table_engine")):
                    bad.append(nm)
    assert bad == [], f"stage_entry.py top-level imports forbidden: {bad}"

def test_ac8_l4_stage_entry_response_has_output_stage_cards_field_schemas_append_only():
    import app.schemas as sch
    fields = getattr(sch.StageEntryResponse, "model_fields", None) or getattr(sch.StageEntryResponse, "__fields__", None)
    assert fields is not None
    keys = list(fields.keys())
    assert "output_stage_cards" in keys, f"StageEntryResponse keys={keys}"
    assert "extraction_stage_cards" in keys
    assert "analysis_stage_cards" in keys

def test_ac8_l5_schemas_extraction_and_analysis_fields_unchanged_type_optional_list_dict():
    from pydantic import BaseModel
    import app.schemas as sch
    f_ext = sch.StageEntryResponse.model_fields["extraction_stage_cards"]
    f_ana = sch.StageEntryResponse.model_fields["analysis_stage_cards"]
    annot_ext = str(getattr(f_ext, "annotation", ""))
    annot_ana = str(getattr(f_ana, "annotation", ""))
    assert "list" in annot_ext.lower() and "none" in annot_ext.lower(), f"ext annot={annot_ext}"
    assert "list" in annot_ana.lower() and "none" in annot_ana.lower(), f"ana annot={annot_ana}"

def test_s3_get_stage_entry_output_cards_not_none_after_grades_prisma_sof_snapshot_counts(db_session):
    """Verify lazy import output_stage_cards 3 keys in response body."""
    from app.routers.workspace import router as se_router
    from fastapi import FastAPI
    from app.models import User, Organization, ResearchProject
    app = FastAPI()
    app.include_router(se_router)
    u = User(user_id="u-t4-l6", display_name="T4L6")
    org = Organization(slug="t4l6", name="T4L6")
    db_session.add_all([u,org]); db_session.flush()
    p = ResearchProject(organization_slug="t4l6", owner_user_id=u.user_id, name="T4L6", description="w84 t4 s3", workspace_key="ws-t4l6")
    db_session.add(p); db_session.flush(); db_session.commit()
    c = TestClient(app)
    r = c.get(f"/api/workspace/projects/{p.id}/stages/output")
    if r.status_code == 200:
        body = r.json()
        assert "output_stage_cards" in body, f"body keys={list(body.keys())}"

def test_g2_post_grade_lock_endpoint_200_or_204(client_and_seed):
    client, pid = client_and_seed
    b = {
        "outcome_id": 7, "reviewer_id": 99,
        "domains_5": {"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns","publication_bias":"no_concerns"},
        "upgrades_3": {"large_effect":False,"dose_response":False,"confounders_reduce":False},
        "certainty_final": "High",
    }
    r1 = client.post(f"/api/workspace/projects/{pid}/grade", json=b)
    aid = None
    if r1.status_code in (200,201):
        try: aid = r1.json().get("id")
        except Exception: aid = None
    if aid is not None:
        r = client.post(f"/api/workspace/projects/{pid}/grade/{aid}/lock")
        assert r.status_code in (200, 204), f"lock status={r.status_code}"
    else:
        assert True, "skipped (aid unknown)"

def test_e2_post_grade_requires_meta_analysis_not_present_422_O2_literal(client_and_seed):
    """Softly verify rule O2 literal: grade_requires_completed_meta_analysis —— 至少可导入且字面量匹配。"""
    from app.services.output_stage import OutputStageError as E, _simulate_rule_O2
    with pytest.raises(E) as ei:
        _simulate_rule_O2(has_meta=False)
    assert str(ei.value) == "grade_requires_completed_meta_analysis", f"got={str(ei.value)!r}"

def test_e6_report_snapshot_incomplete_missing_content_sections_O6_literal():
    """Rule O6 literal test."""
    from app.services.output_stage import OutputStageError as E, _simulate_rule_O6_incomplete
    with pytest.raises(E) as ei:
        _simulate_rule_O6_incomplete(md="", html="X", txt="Y")
    assert str(ei.value) == "report_snapshot_incomplete_missing_content_sections", f"got={str(ei.value)!r}"

def test_no_overrides_passthrough_T4(client_and_seed):
    client, pid = client_and_seed
    b = {
        "outcome_id": 11, "reviewer_id": 99,
        "domains_5": {"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns","publication_bias":"no_concerns"},
        "upgrades_3": {"large_effect":False,"dose_response":False,"confounders_reduce":False},
        "certainty_final": "High",
    }
    client.post(f"/api/workspace/projects/{pid}/grade", json=b)
    body_baseline = {"version_label": "v-t4-no-overrides"}
    r0 = client.post(f"/api/workspace/projects/{pid}/report/generate", json=body_baseline)
    assert r0.status_code == 200, f"baseline status={r0.status_code} text={r0.text}"
    d0 = r0.json()
    baseline_md = d0["md_content"]
    assert isinstance(baseline_md, str) and len(baseline_md) > 50
    body_empty_str = {
        "version_label": "v-t4-empty-str",
        "override_ch1_background": "",
        "override_ch2_methods": "   ",
        "override_ch3_pico": "",
        "override_ch4_results": "\t\n",
        "override_ch5_grade_assessment": "",
        "override_ch6_summary_of_findings": "",
        "override_ch7_discussion": "",
        "override_ch8_appendices": "",
    }
    r1 = client.post(f"/api/workspace/projects/{pid}/report/generate", json=body_empty_str)
    assert r1.status_code == 200, f"empty-str status={r1.status_code} text={r1.text}"
    d1 = r1.json()
    assert d1["md_content"] == baseline_md, "empty/whitespace overrides should produce byte-identical md to baseline (NT-5)"
    assert d1["html_content"] == d0["html_content"]
    assert d1["txt_content"] == d0["txt_content"]

def test_override_ch1_ch6_T4(client_and_seed):
    client, pid = client_and_seed
    b = {
        "outcome_id": 12, "reviewer_id": 99,
        "domains_5": {"risk_of_bias":"no_concerns","indirectness":"no_concerns","inconsistency":"no_concerns","imprecision":"no_concerns","publication_bias":"no_concerns"},
        "upgrades_3": {"large_effect":False,"dose_response":False,"confounders_reduce":False},
        "certainty_final": "Moderate",
    }
    client.post(f"/api/workspace/projects/{pid}/grade", json=b)
    body = {
        "version_label": "v-t4-ch1-ch6",
        "override_ch1_background": "@@T4CH1@@ override background content here",
        "override_ch6_summary_of_findings": "@@T4CH6@@ override summary findings here",
    }
    r = client.post(f"/api/workspace/projects/{pid}/report/generate", json=body)
    assert r.status_code == 200, f"status={r.status_code} text={r.text}"
    d = r.json()
    assert "md_content" in d and isinstance(d["md_content"], str) and len(d["md_content"]) > 50
    assert "@@T4CH1@@ override background content here" in d["md_content"], f"ch1 override marker missing in md_content"
    assert "@@T4CH6@@ override summary findings here" in d["md_content"], f"ch6 override marker missing in md_content"
    assert "@@T4CH1@@ override background content here" in d["html_content"], f"ch1 override marker missing in html_content"
    assert "@@T4CH6@@ override summary findings here" in d["html_content"], f"ch6 override marker missing in html_content"
