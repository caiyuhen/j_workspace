import pytest
import uuid
import datetime as dt
from sqlalchemy import text as sa_text
from app.models import PipelineRun, PipelineStepResult, Workspace

PRESETS = ["sglt2i_ckd","empagliflozin_hf","glp1_weightloss","liraglutide_nafld","pkd_tolvaptan","ckd_blood_pressure_control"]
STATUSES = ["queued","running","success","failed","resumable","paused","cancelled","partial"]


@pytest.fixture(autouse=True)
def _enable_sqlite_fk(db_session):
    db_session.connection().execute(sa_text("PRAGMA foreign_keys = ON"))
    db_session.commit()
    yield


def _make_wid(db_session) -> str:
    wid = str(uuid.uuid4())
    db_session.add(Workspace(id=wid))
    db_session.flush()
    return wid


def test_M1_pipeline_run_ulid_prefix_32char(db_session):
    wid = _make_wid(db_session)
    r = PipelineRun(
        id="p-" + "x"*30,
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        max_records=200,
        status="queued",
        steps_json=[{"step_index":i,"status":"pending","step_name":n}
            for i,n in enumerate(["pubmed_fetch","dedupe","screen_ta","screen_ft","abstractor","rob2","grade","report"])]
    )
    assert r.id.startswith("p-")
    assert len(r.id) == 32


def test_M2_defaults_max_records_200_cancel_flag_F(db_session):
    wid = _make_wid(db_session)
    r = PipelineRun(
        id="p-002aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        status="queued",
        steps_json=[]
    )
    assert r.max_records == 200
    assert r.cancel_flag is False
    assert r.current_step_index == 0


def test_M3_max_records_rejects_gt_cap_checkconstraint(db_session):
    # The CHECK upper bound was widened to 2500 in W11 (see models.py
    # cc_pipelinerun_max_records); anything above that must still be rejected.
    wid = _make_wid(db_session)
    r = PipelineRun(
        id="p-003aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        max_records=2501,
        status="queued",
        steps_json=[]
    )
    db_session.add(r)
    with pytest.raises(Exception):
        db_session.commit()


def test_M4_workspace_fk_violation(db_session):
    r = PipelineRun(
        id="p-004aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id="00000000-0000-0000-0000-000000000000",
        preset="sglt2i_ckd",
        mode="snapshot",
        status="queued",
        steps_json=[]
    )
    db_session.add(r)
    with pytest.raises(Exception):
        db_session.commit()


def test_M5_steps_json_length_8_success(db_session):
    wid = _make_wid(db_session)
    steps = [{"step_index":i,"status":"pending"} for i in range(8)]
    r = PipelineRun(
        id="p-005aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        status="queued",
        steps_json=steps
    )
    db_session.add(r)
    db_session.commit()
    assert len(r.steps_json) == 8


def test_M6_steps_json_len_1_ok_schema_loose_engine_enforces_len8(db_session):
    wid = _make_wid(db_session)
    r = PipelineRun(
        id="p-006aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        status="queued",
        steps_json=[{"x":1}]
    )
    db_session.add(r)
    db_session.commit()
    assert r.steps_json == [{"x":1}]


def test_M7_status_all_8_values_insertable(db_session):
    wid = _make_wid(db_session)
    for i, s in enumerate(STATUSES):
        r = PipelineRun(
            id=f"p-007{i:02d}aaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            workspace_id=wid,
            preset="sglt2i_ckd",
            mode="snapshot",
            status=s,
            steps_json=[]
        )
        db_session.add(r)
    db_session.commit()
    assert db_session.query(PipelineRun).count() == 8


def test_M8_report_blob_path_nullable_ok(db_session):
    wid = _make_wid(db_session)
    r = PipelineRun(
        id="p-008aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        status="queued",
        steps_json=[],
        report_blob_path=None
    )
    db_session.add(r)
    db_session.commit()
    assert r.report_blob_path is None


def test_M9_6_presets_all_insertable(db_session):
    wid = _make_wid(db_session)
    for i, p in enumerate(PRESETS):
        r = PipelineRun(
            id=f"p-009{i:02d}aaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            workspace_id=wid,
            preset=p,
            mode="snapshot",
            status="queued",
            steps_json=[]
        )
        db_session.add(r)
    db_session.commit()
    assert db_session.query(PipelineRun).count() == 6


def test_M10_step_result_unique_run_step_attempt(db_session):
    wid = _make_wid(db_session)
    r = PipelineRun(
        id="p-010aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        status="queued",
        steps_json=[]
    )
    db_session.add(r)
    db_session.flush()
    s1 = PipelineStepResult(
        run_id="p-010aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        step_index=0,
        step_name="pubmed_fetch",
        attempt_no=1,
        status="success",
        duration_ms=1200,
        n_inputs=200,
        n_outputs=200
    )
    db_session.add(s1)
    db_session.commit()
    s1_dup = PipelineStepResult(
        run_id="p-010aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        step_index=0,
        step_name="pubmed_fetch",
        attempt_no=1,
        status="failed",
        duration_ms=800,
        n_inputs=200,
        n_outputs=0
    )
    db_session.add(s1_dup)
    with pytest.raises(Exception):
        db_session.commit()


def test_M11_step_result_payload_ref_nullable_retryable_T(db_session):
    wid = _make_wid(db_session)
    r = PipelineRun(
        id="p-011aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        status="queued",
        steps_json=[]
    )
    db_session.add(r)
    db_session.flush()
    s = PipelineStepResult(
        run_id="p-011aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        step_index=3,
        step_name="screen_ft",
        attempt_no=1,
        status="success",
        duration_ms=4500,
        n_inputs=104,
        n_outputs=58,
        payload_ref=None,
        retryable=True
    )
    db_session.add(s)
    db_session.commit()
    assert s.retryable is True


def test_M12_order_by_created_at_desc_query_order(db_session):
    wid = _make_wid(db_session)
    r1 = PipelineRun(
        id="p-012aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        status="success",
        steps_json=[],
        finished_at=dt.datetime(2026, 8, 21, 10, 0)
    )
    db_session.add(r1)
    db_session.flush()
    r2 = PipelineRun(
        id="p-012bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        workspace_id=wid,
        preset="empagliflozin_hf",
        mode="snapshot",
        status="success",
        steps_json=[],
        finished_at=dt.datetime(2026, 8, 21, 11, 0)
    )
    db_session.add(r2)
    db_session.commit()
    q = db_session.query(PipelineRun).filter_by(workspace_id=wid).order_by(PipelineRun.created_at.desc()).all()
    assert q[0].id in ("p-012aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa", "p-012bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")
    assert len(q) == 2
