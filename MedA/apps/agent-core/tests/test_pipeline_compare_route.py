"""W10 D2-2: Pipeline Compare Delta Helpers + 20 tests C1-C20 GREEN.

Helpers: funnel / rob / grade / pico + orchestrator
Route:  GET /{workspace_id}/pipelines/compare/{run_a}/{run_b}
"""

import pytest
import warnings
from datetime import datetime
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.main import app
from app.db import engine
from app.models import PipelineRun, Workspace
from app.services.pipeline_engine import (
    compute_funnel_counts_for_run,
    compute_funnel_delta,
    compute_rob2_delta,
    compute_grade_delta,
    compute_pico_diff,
    compute_pipeline_compare,
    create_pipeline_run,
    included_study_ids,
)


ORG_SLUG = "meda-w10"
ORG_NAME = "MedA W10 Org"
USER_ID_A = "u-w10-001"
WORKSPACE_ID = f"{ORG_SLUG}-ws-pipeline-001"
FOREIGN_WORKSPACE_ID = "foreignorg-ws-999"


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


_FACTORS = [0.96, 0.86, 0.58, 0.56, 0.76, 0.98, 1.0, 1.0]


def _make_run_with_steps(
    preset: str = "sglt2i_ckd",
    max_records: int = 200,
    *,
    run_id: str | None = None,
    workspace_id: str = WORKSPACE_ID,
) -> PipelineRun:
    """Build an in-memory PipelineRun with n_out cascade set using the standard factors."""
    steps = []
    n_prev = max_records
    for i in range(8):
        if i == 0:
            n_in = max_records
        else:
            n_in = n_prev
        if i == 7:
            n_out = 1
        else:
            n_out = max(1, int(n_in * _FACTORS[i]))
        steps.append({
            "step_index": i,
            "status": "success",
            "n_in": n_in,
            "n_out": n_out,
        })
        n_prev = n_out
    rid = run_id or f"p-mock-{preset}-{max_records}-{id(steps) % 100000}"
    return PipelineRun(
        id=rid,
        workspace_id=workspace_id,
        preset=preset,
        mode="snapshot",
        max_records=max_records,
        status="success",
        current_step_index=8,
        cancel_flag=False,
        steps_json=steps,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        finished_at=datetime.utcnow(),
    )


@pytest.fixture(autouse=True)
def _suppress_task_warnings():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=".*coroutine 'run_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*coroutine 'resume_pipeline' was never awaited.*")
        warnings.filterwarnings("ignore", message=".*Task was destroyed but it is pending!.*")
        yield


# ═══════════════════════════════════════════════════════════════════════════════
# C1-C12: Unit tests of the 4 delta helpers (direct, no HTTP)
# ═══════════════════════════════════════════════════════════════════════════════


class TestC1C4FunnelCounts:
    def test_C1_same_run_funnel_delta_all_zero(self):
        run = _make_run_with_steps("sglt2i_ckd", 150)
        delta = compute_funnel_delta(run, run)
        assert len(delta) == 8, f"C1 expected 8 steps, got {len(delta)}"
        for i, row in enumerate(delta):
            assert row["diff"] == 0, (
                f"C1 step#{i} diff={row['diff']} should be 0 for same run"
            )
            assert row["a_n"] == row["b_n"], (
                f"C1 step#{i} a_n!=b_n for same run"
            )

    def test_C2_max_200_vs_100_step0_diff_ge_96(self):
        run_a = _make_run_with_steps("sglt2i_ckd", 200, run_id="p-runa-c2")
        run_b = _make_run_with_steps("sglt2i_ckd", 100, run_id="p-runb-c2")
        delta = compute_funnel_delta(run_a, run_b)
        step0 = delta[0]
        assert step0["step"] == "identify"
        assert step0["diff"] >= 96, (
            f"C2 step0 diff={step0['diff']} a_n={step0['a_n']} b_n={step0['b_n']}, expected >= 96"
        )

    def test_C3_funnel_counts_always_len_8_int_list(self):
        for preset, mx in [
            ("sglt2i_ckd", 50),
            ("glp1_weightloss", 3),
            ("pkd_tolvaptan", 200),
        ]:
            r = _make_run_with_steps(preset, mx)
            counts = compute_funnel_counts_for_run(r)
            assert isinstance(counts, list), f"C3 {preset} not list"
            assert len(counts) == 8, f"C3 {preset} len={len(counts)} != 8"
            for v in counts:
                assert isinstance(v, int), f"C3 {preset} value {v!r} not int"

    def test_C4_empty_steps_json_returns_zeros(self):
        r = PipelineRun(
            id="p-empty-steps",
            workspace_id=WORKSPACE_ID,
            preset="sglt2i_ckd",
            mode="snapshot",
            max_records=50,
            status="queued",
            current_step_index=0,
            cancel_flag=False,
            steps_json=[],
        )
        assert compute_funnel_counts_for_run(r) == [0, 0, 0, 0, 0, 0, 0, 0]


class TestC5C6Rob2Delta:
    def test_C5_rob2_delta_3_rows_correct_schema(self):
        r1 = _make_run_with_steps("empagliflozin_hf", 120, run_id="p-c5-1")
        r2 = _make_run_with_steps("empagliflozin_hf", 120, run_id="p-c5-2")
        result = compute_rob2_delta(r1, r2)
        assert len(result) == 3, f"C5 expected 3 rows, got {len(result)}"
        overalls = [row["overall"] for row in result]
        assert overalls == ["low", "some", "high"], f"C5 order wrong: {overalls}"
        for row in result:
            assert set(row.keys()) == {"overall", "a", "b"}, (
                f"C5 wrong keys: {list(row.keys())}"
            )
            assert isinstance(row["a"], int), f"C5 a not int: {row['a']!r}"
            assert isinstance(row["b"], int), f"C5 b not int: {row['b']!r}"

    def test_C6_rob2_sum_a_equals_step5_n_out_within_10(self):
        for preset, mx in [
            ("sglt2i_ckd", 200),
            ("glp1_weightloss", 80),
            ("liraglutide_nafld", 150),
        ]:
            r = _make_run_with_steps(preset, mx, run_id=f"p-c6-{preset}-{mx}")
            result = compute_rob2_delta(r, r)
            row_a_sum = sum(row["a"] for row in result)
            # Risk of bias is assessed for every included study and removes none of
            # them, so the three buckets have to account for the whole included set.
            assessed_n = len(included_study_ids(r))
            assert row_a_sum == assessed_n, (
                f"C6 {preset} mx={mx}: sum(a)={row_a_sum} vs assessed={assessed_n}"
            )


class TestC7C9GradeDelta:
    def test_C7_sglt2i_ckd_grade_delta_has_4_outcomes(self):
        r1 = _make_run_with_steps("sglt2i_ckd", 100, run_id="p-c7-1")
        r2 = _make_run_with_steps("sglt2i_ckd", 100, run_id="p-c7-2")
        result = compute_grade_delta(r1, r2)
        assert len(result) == 4, f"C7 expected 4 rows, got {len(result)}"
        first_outcomes = [row["outcome"] for row in result]
        assert "eGFR drop 40%" in first_outcomes, f"C7 missing ckd outcome1: {first_outcomes}"
        assert "all-cause death" in first_outcomes, f"C7 missing all-cause death: {first_outcomes}"

    def test_C8_grade_a_b_values_are_H_M_L_literals(self):
        r1 = _make_run_with_steps("empagliflozin_hf", 60, run_id="p-c8-1")
        r2 = _make_run_with_steps("empagliflozin_hf", 70, run_id="p-c8-2")
        result = compute_grade_delta(r1, r2)
        for i, row in enumerate(result):
            assert row["a"] in ("H", "M", "L"), (
                f"C8 row#{i} a={row['a']!r} not H/M/L"
            )
            assert row["b"] in ("H", "M", "L"), (
                f"C8 row#{i} b={row['b']!r} not H/M/L"
            )

    def test_C9_grade_reason_always_non_empty_string(self):
        for preset_a, preset_b in [
            ("sglt2i_ckd", "sglt2i_ckd"),
            ("glp1_weightloss", "glp1_weightloss"),
            ("ckd_blood_pressure_control", "sglt2i_ckd"),
        ]:
            r1 = _make_run_with_steps(preset_a, 80, run_id=f"p-c9-a-{preset_a}")
            r2 = _make_run_with_steps(preset_b, 90, run_id=f"p-c9-b-{preset_b}")
            result = compute_grade_delta(r1, r2)
            for i, row in enumerate(result):
                reason = row["reason"]
                assert isinstance(reason, str) and len(reason) > 0, (
                    f"C9 {preset_a}vs{preset_b} row#{i} reason empty/missing: {reason!r}"
                )


class TestC10C12PicoDiff:
    def test_C10_pico_diff_schema_three_keys_all_list_of_str(self):
        r1 = _make_run_with_steps("pkd_tolvaptan", 100, run_id="p-c10-1")
        r2 = _make_run_with_steps("pkd_tolvaptan", 90, run_id="p-c10-2")
        result = compute_pico_diff(r1, r2)
        assert isinstance(result, dict), "C10 not dict"
        keys_required = {"only_in_a_nct_ids", "only_in_b_nct_ids", "both"}
        assert keys_required.issubset(result.keys()), (
            f"C10 missing keys: {keys_required - set(result.keys())}"
        )
        for k in keys_required:
            lst = result[k]
            assert isinstance(lst, list), f"C10 {k} not list"
            for item in lst:
                assert isinstance(item, str), f"C10 {k} has non-str: {item!r}"
                assert item.startswith("NCT"), f"C10 {k} NCT prefix missing: {item}"

    def test_C11_pico_both_is_sorted_and_unique(self):
        r1 = _make_run_with_steps("sglt2i_ckd", 150, run_id="p-c11-1")
        r2 = _make_run_with_steps("sglt2i_ckd", 150, run_id="p-c11-2")
        result = compute_pico_diff(r1, r2)
        both = result["both"]
        assert both == sorted(both), "C11 pico.both not sorted"
        assert len(both) == len(set(both)), "C11 pico.both has duplicates"

    def test_C12_both_union_only_a_covers_full_a_set(self):
        r1 = _make_run_with_steps("liraglutide_nafld", 60, run_id="p-c12-1")
        r2 = _make_run_with_steps("liraglutide_nafld", 80, run_id="p-c12-2")
        result = compute_pico_diff(r1, r2)
        combined = sorted(set(result["both"]) | set(result["only_in_a_nct_ids"]))

        # The diff is over the studies run A actually included, so `both` plus
        # `only_in_a` has to be exactly that set.
        expected = sorted(set(included_study_ids(r1)))
        cap = min(len(expected), 200)
        assert combined == expected[:cap], (
            f"C12 combined len={len(combined)} vs expected[:{cap}] len={len(expected[:cap])}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# C13-C20: HTTP route tests of GET compare/{a}/{b}
# ═══════════════════════════════════════════════════════════════════════════════


def _persist_run_with_steps(session: Session, run: PipelineRun) -> PipelineRun:
    """Persist an in-memory PipelineRun (with steps_json) into DB so the route can fetch it."""
    ws = session.get(Workspace, run.workspace_id)
    if ws is None:
        session.add(Workspace(id=run.workspace_id))
        session.commit()
    db_run = session.get(PipelineRun, run.id)
    if db_run is None:
        session.add(run)
        session.commit()
        session.refresh(run)
        return run
    db_run.steps_json = run.steps_json
    db_run.preset = run.preset
    db_run.max_records = run.max_records
    db_run.status = run.status
    session.add(db_run)
    session.commit()
    session.refresh(db_run)
    return db_run


class TestC13C16RouteMetricsFiltering:
    def test_C13_default_metrics_returns_all_4_sections(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        ra_id = "p-c13-a"
        rb_id = "p-c13-b"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            ra = _make_run_with_steps("sglt2i_ckd", 120, run_id=ra_id, workspace_id=WORKSPACE_ID)
            rb = _make_run_with_steps("sglt2i_ckd", 130, run_id=rb_id, workspace_id=WORKSPACE_ID)
            _persist_run_with_steps(s, ra)
            _persist_run_with_steps(s, rb)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{ra_id}/{rb_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200, f"C13 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        for key in ("funnel_delta", "rob2_delta", "grade_delta", "pico"):
            assert key in body, f"C13 missing key {key}; keys={list(body.keys())}"

    def test_C14_metrics_funnel_only_excludes_rob_grade_pico(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        ra_id = "p-c14-a"
        rb_id = "p-c14-b"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            ra = _make_run_with_steps("sglt2i_ckd", 80, run_id=ra_id, workspace_id=WORKSPACE_ID)
            rb = _make_run_with_steps("sglt2i_ckd", 70, run_id=rb_id, workspace_id=WORKSPACE_ID)
            _persist_run_with_steps(s, ra)
            _persist_run_with_steps(s, rb)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{ra_id}/{rb_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"metrics": "funnel"},
        )
        assert resp.status_code == 200, f"C14 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "funnel_delta" in body, "C14 missing funnel_delta"
        for bad in ("rob2_delta", "grade_delta", "pico"):
            assert bad not in body, f"C14 should not have {bad}; keys={list(body.keys())}"

    def test_C15_metrics_rob_and_pico_only(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        ra_id = "p-c15-a"
        rb_id = "p-c15-b"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            ra = _make_run_with_steps("empagliflozin_hf", 90, run_id=ra_id, workspace_id=WORKSPACE_ID)
            rb = _make_run_with_steps("empagliflozin_hf", 95, run_id=rb_id, workspace_id=WORKSPACE_ID)
            _persist_run_with_steps(s, ra)
            _persist_run_with_steps(s, rb)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{ra_id}/{rb_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"metrics": "rob,pico"},
        )
        assert resp.status_code == 200, f"C15 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "rob2_delta" in body, "C15 missing rob2_delta"
        assert "pico" in body, "C15 missing pico"
        for bad in ("funnel_delta", "grade_delta"):
            assert bad not in body, f"C15 should not have {bad}; keys={list(body.keys())}"

    def test_C16_metrics_grade_returns_4_rows(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        ra_id = "p-c16-a"
        rb_id = "p-c16-b"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            ra = _make_run_with_steps("sglt2i_ckd", 110, run_id=ra_id, workspace_id=WORKSPACE_ID)
            rb = _make_run_with_steps("sglt2i_ckd", 100, run_id=rb_id, workspace_id=WORKSPACE_ID)
            _persist_run_with_steps(s, ra)
            _persist_run_with_steps(s, rb)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{ra_id}/{rb_id}",
            headers={"Authorization": f"Bearer {token}"},
            params={"metrics": "grade"},
        )
        assert resp.status_code == 200, f"C16 non-200: {resp.status_code} {resp.text}"
        body = resp.json()
        assert "grade_delta" in body, "C16 missing grade_delta"
        assert len(body["grade_delta"]) == 4, (
            f"C16 expected 4 grade rows, got {len(body['grade_delta'])}"
        )


class TestC17C20RouteErrorCodesAndPresets:
    def test_C17_run_b_nonexistent_returns_404(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        ra_id = "p-c17-a"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            ra = _make_run_with_steps("sglt2i_ckd", 50, run_id=ra_id, workspace_id=WORKSPACE_ID)
            _persist_run_with_steps(s, ra)
        fake_b = "p-0000NOTEXIST-C17-99999"
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{ra_id}/{fake_b}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404, (
            f"C17 expected 404 for missing run_b, got {resp.status_code}: {resp.text}"
        )

    def test_C18_unauthenticated_no_token_returns_401(self):
        client = TestClient(app)
        ra_id = "p-c18-a"
        rb_id = "p-c18-b"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            ra = _make_run_with_steps("sglt2i_ckd", 60, run_id=ra_id, workspace_id=WORKSPACE_ID)
            rb = _make_run_with_steps("sglt2i_ckd", 65, run_id=rb_id, workspace_id=WORKSPACE_ID)
            _persist_run_with_steps(s, ra)
            _persist_run_with_steps(s, rb)
        resp = client.get(
            f"/api/workspace/{WORKSPACE_ID}/pipelines/compare/{ra_id}/{rb_id}",
        )
        assert resp.status_code == 401, (
            f"C18 expected 401 no token, got {resp.status_code}: {resp.text}"
        )

    def test_C19_foreign_workspace_returns_403(self):
        client = TestClient(app)
        token = _dev_login(client, ORG_SLUG, ORG_NAME, USER_ID_A)
        ra_id = "p-c19-a"
        rb_id = "p-c19-b"
        with Session(engine) as s:
            _ensure_workspace(s, WORKSPACE_ID)
            ra = _make_run_with_steps("sglt2i_ckd", 60, run_id=ra_id, workspace_id=WORKSPACE_ID)
            rb = _make_run_with_steps("sglt2i_ckd", 55, run_id=rb_id, workspace_id=WORKSPACE_ID)
            _persist_run_with_steps(s, ra)
            _persist_run_with_steps(s, rb)
        resp = client.get(
            f"/api/workspace/{FOREIGN_WORKSPACE_ID}/pipelines/compare/{ra_id}/{rb_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403, (
            f"C19 expected 403 foreign workspace, got {resp.status_code}: {resp.text}"
        )

    def test_C20_different_presets_first_outcome_names_differ(self):
        run_sg = _make_run_with_steps("sglt2i_ckd", 100, run_id="p-c20-sg")
        run_gp = _make_run_with_steps("glp1_weightloss", 100, run_id="p-c20-gp")

        delta_sg = compute_grade_delta(run_sg, run_sg)
        delta_gp = compute_grade_delta(run_gp, run_gp)

        sg_first = delta_sg[0]["outcome"]
        gp_first = delta_gp[0]["outcome"]

        assert sg_first == "eGFR drop 40%", (
            f"C20 sglt2i_ckd first outcome expected 'eGFR drop 40%', got {sg_first!r}"
        )
        assert gp_first == "≥15% weight loss", (
            f"C20 glp1_weightloss first outcome expected '≥15% weight loss', got {gp_first!r}"
        )
        assert sg_first != gp_first, (
            "C20 two presets should have different 1st outcome names"
        )
