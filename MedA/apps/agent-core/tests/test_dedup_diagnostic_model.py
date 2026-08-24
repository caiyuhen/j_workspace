import pytest
import uuid
import datetime as dt
from sqlalchemy import text as sa_text, inspect
from sqlalchemy.exc import IntegrityError
from app.models import PipelineRun, Workspace, DedupDiagnostic


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


def _make_run(db_session, wid: str, run_id: str, max_records: int = 200) -> PipelineRun:
    r = PipelineRun(
        id=run_id,
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        max_records=max_records,
        status="queued",
        steps_json=[],
    )
    db_session.add(r)
    db_session.flush()
    return r


def test_DM1_basic_insert_sizes_hist_success(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm1" + "x" * 28
    _make_run(db_session, wid, rid)
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 1724, "2": 121},
        hamming_hist={"0": 1800, "1": 45},
        perf_json={"phase": "build_bktree", "ms": 120},
    )
    db_session.add(dd)
    db_session.commit()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid).first()
    assert q is not None
    assert q.sizes_hist == {"1": 1724, "2": 121}


def test_DM2_cc_max_2000_2500_passes(db_session):
    wid = _make_wid(db_session)
    for val in (2000, 2500):
        rid = f"p-dm2-{val}" + "x" * 24
        r = PipelineRun(
            id=rid,
            workspace_id=wid,
            preset="sglt2i_ckd",
            mode="snapshot",
            max_records=val,
            status="queued",
            steps_json=[],
        )
        db_session.add(r)
    db_session.commit()
    assert db_session.query(PipelineRun).count() == 2


def test_DM3_cc_max_2501_fails_integrity(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm3" + "x" * 28
    r = PipelineRun(
        id=rid,
        workspace_id=wid,
        preset="sglt2i_ckd",
        mode="snapshot",
        max_records=2501,
        status="queued",
        steps_json=[],
    )
    db_session.add(r)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_DM4_delete_pipelinerun_cascade_deletes_dedup(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm4" + "x" * 28
    r = _make_run(db_session, wid, rid)
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 100},
        hamming_hist={"0": 100},
        perf_json={},
    )
    db_session.add(dd)
    db_session.commit()
    assert db_session.query(DedupDiagnostic).count() == 1
    db_session.delete(r)
    db_session.commit()
    assert db_session.query(DedupDiagnostic).count() == 0


def test_DM5_json_roundtrip_sizes_hamming_perf(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm5" + "x" * 28
    _make_run(db_session, wid, rid)
    sizes_in = {"0": 5, "1": 10, "2": 20, "3": 15}
    hamming_in = {"hd0": 1000, "hd1": 120, "hd2": 18}
    perf_in = {"build_ms": 512, "query_ms": 2048, "stages": ["tokenize", "hash", "bk"]}
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=2,
        sizes_hist=sizes_in,
        hamming_hist=hamming_in,
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=2).first()
    assert q.sizes_hist == sizes_in
    assert q.hamming_hist == hamming_in
    assert q.perf_json == perf_in


def test_DM6_unique_runid_stepidx_throws(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm6" + "x" * 28
    _make_run(db_session, wid, rid)
    dd1 = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 100},
        hamming_hist={"0": 100},
        perf_json={"ms": 10},
    )
    db_session.add(dd1)
    db_session.flush()
    dd2 = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 999},
        hamming_hist={"0": 999},
        perf_json={"ms": 99},
    )
    db_session.add(dd2)
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_DM7_perf_json_int_and_float_save_read(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm7" + "x" * 28
    _make_run(db_session, wid, rid)
    perf_in = {
        "records_processed": 2048,
        "avg_hamming_distance": 3.14159,
        "threshold": 7,
        "ratio": 0.618,
        "total_us": 1234567,
    }
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=3,
        sizes_hist={"a": 1},
        hamming_hist={"b": 2},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=3).first()
    assert q.perf_json["records_processed"] == 2048
    assert isinstance(q.perf_json["records_processed"], int)
    assert abs(q.perf_json["avg_hamming_distance"] - 3.14159) < 1e-9
    assert isinstance(q.perf_json["avg_hamming_distance"], float)
    assert q.perf_json["threshold"] == 7
    assert abs(q.perf_json["ratio"] - 0.618) < 1e-9
    assert q.perf_json["total_us"] == 1234567


def test_DM8_sizes_hist_values_sum_equals_n_in(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm8" + "x" * 28
    _make_run(db_session, wid, rid)
    n_in = 1724 + 121 + 50 + 5
    sizes_hist = {"1": 1724, "2": 121, "3": 50, "4": 5}
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=4,
        sizes_hist=sizes_hist,
        hamming_hist={"0": n_in},
        perf_json={"n_in": n_in},
    )
    db_session.add(dd)
    db_session.commit()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=4).first()
    assert sum(q.sizes_hist.values()) == n_in
    assert q.perf_json["n_in"] == n_in


def test_DM9_index_ix_dedup_run_id_query_works(db_session):
    insp = inspect(db_session.bind)
    indexes = insp.get_indexes("dedupdiagnostic")
    idx_names = [i["name"] for i in indexes]
    assert "ix_dedup_run_id" in idx_names, f"missing ix_dedup_run_id, got indexes={idx_names}"
    wid = _make_wid(db_session)
    rid_a = "p-dm9a" + "x" * 27
    rid_b = "p-dm9b" + "x" * 27
    _make_run(db_session, wid, rid_a)
    _make_run(db_session, wid, rid_b)
    for step in (0, 1, 2):
        db_session.add(DedupDiagnostic(
            run_id=rid_a, step_idx=step,
            sizes_hist={str(step): step * 10},
            hamming_hist={}, perf_json={},
        ))
    db_session.add(DedupDiagnostic(
        run_id=rid_b, step_idx=0,
        sizes_hist={"only": 1}, hamming_hist={}, perf_json={},
    ))
    db_session.commit()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid_a).all()
    assert len(q) == 3
    q2 = db_session.query(DedupDiagnostic).filter_by(run_id=rid_b).all()
    assert len(q2) == 1


def test_DM10_step_idx_outside_0_7_throws(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm10" + "x" * 27
    _make_run(db_session, wid, rid)
    bad_values = (-1, 8, 9, 100)
    for bad in bad_values:
        db_session.rollback()
        dd = DedupDiagnostic(
            run_id=rid,
            step_idx=bad,
            sizes_hist={"x": 1},
            hamming_hist={"y": 1},
            perf_json={},
        )
        db_session.add(dd)
        with pytest.raises(IntegrityError):
            db_session.commit()


def test_DM11_perf_empty_dict_allowed(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm11" + "x" * 27
    _make_run(db_session, wid, rid)
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=5,
        sizes_hist={"1": 10, "2": 5},
        hamming_hist={"hd0": 15},
        perf_json={},
    )
    db_session.add(dd)
    db_session.commit()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=5).first()
    assert q.perf_json == {}
    assert isinstance(q.perf_json, dict)


def test_DM12_created_at_auto_default_utc_now(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm12" + "x" * 27
    _make_run(db_session, wid, rid)
    t_before = dt.datetime.utcnow()
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=6,
        sizes_hist={"1": 1},
        hamming_hist={"0": 1},
        perf_json={"tag": "dm12"},
    )
    db_session.add(dd)
    db_session.flush()
    assert dd.created_at is not None
    db_session.commit()
    db_session.expire_all()
    t_after = dt.datetime.utcnow()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=6).first()
    assert q.created_at is not None
    assert t_before <= q.created_at <= t_after
    assert isinstance(q.created_at, dt.datetime)
