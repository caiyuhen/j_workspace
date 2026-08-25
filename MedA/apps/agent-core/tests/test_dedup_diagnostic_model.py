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


# ============================================================
# DM13-DM20 · D1-4 APPEND 8 tests · new DedupDiag hybrid fields
# perf_json: hybrid_version, stage_*_ms, lsh_candidate_count,
#            lsh_filter_ratio, over_prefix_count
# ============================================================

def test_DM13_hybrid_version_string_w12_hybrid_v1(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm13" + "x" * 27
    _make_run(db_session, wid, rid)
    perf_in = {
        "version": "w12-hybrid-v1",
        "hybrid_version": "w12-hybrid-v1",
        "n_records": 52000,
    }
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 50000},
        hamming_hist={"hd0": 1},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=1).first()
    assert q.perf_json.get("version") == "w12-hybrid-v1"
    assert q.perf_json.get("hybrid_version") == "w12-hybrid-v1"
    assert isinstance(q.perf_json["hybrid_version"], str)


def test_DM14_stage_minhash_ms_nonnegative_int_or_float(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm14" + "x" * 27
    _make_run(db_session, wid, rid)
    stage_ms_in = {
        "minhash_ms": 1234,
        "lsh_ms": 0,
        "oversample_ms": 0.0,
        "bk_ms": 567.89,
        "union_ms": 42,
        "total_ms": 1843.89,
    }
    perf_in = {"version": "w12-hybrid-v1", "stage_ms": stage_ms_in}
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 100},
        hamming_hist={},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=1).first()
    stage_ms = q.perf_json["stage_ms"]
    assert "minhash_ms" in stage_ms
    val = stage_ms["minhash_ms"]
    assert isinstance(val, (int, float))
    assert val >= 0
    assert val == 1234


def test_DM15_stage_lsh_ms_present_and_types_ok(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm15" + "x" * 27
    _make_run(db_session, wid, rid)
    perf_in = {
        "version": "w12-hybrid-v1",
        "stage_ms": {
            "minhash_ms": 100,
            "lsh_ms": 250.5,
            "oversample_ms": 50,
            "bk_ms": 800,
            "union_ms": 10,
            "total_ms": 1210.5,
        },
    }
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=2,
        sizes_hist={"1": 2000},
        hamming_hist={"hd0": 1},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=2).first()
    stage_ms = q.perf_json["stage_ms"]
    assert "lsh_ms" in stage_ms
    lsh_val = stage_ms["lsh_ms"]
    assert isinstance(lsh_val, (int, float))
    assert lsh_val >= 0
    assert abs(lsh_val - 250.5) < 1e-6


def test_DM16_stage_oversample_prefix_ms_key_exists(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm16" + "x" * 27
    _make_run(db_session, wid, rid)
    perf_in = {
        "version": "w12-hybrid-v1",
        "stage_ms": {
            "minhash_ms": 0,
            "lsh_ms": 0,
            "oversample_ms": 77.77,
            "oversample_prefix_ms": 77.77,
            "bk_ms": 0,
            "union_ms": 0,
            "total_ms": 77.77,
        },
    }
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 10000},
        hamming_hist={},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=1).first()
    stage_ms = q.perf_json["stage_ms"]
    has_oversample = "oversample_ms" in stage_ms or "oversample_prefix_ms" in stage_ms
    assert has_oversample, "oversample_ms or oversample_prefix_ms must exist in stage_ms"
    ov_val = stage_ms.get("oversample_prefix_ms", stage_ms.get("oversample_ms", -1))
    assert isinstance(ov_val, (int, float))
    assert ov_val >= 0


def test_DM17_stage_bk_ms_present_nonneg(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm17" + "x" * 27
    _make_run(db_session, wid, rid)
    perf_in = {
        "version": "w12-hybrid-v1",
        "stage_ms": {
            "minhash_ms": 10,
            "lsh_ms": 20,
            "oversample_ms": 5,
            "bk_ms": 9999.99,
            "union_ms": 1,
            "total_ms": 10035.99,
        },
    }
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=3,
        sizes_hist={"1": 50000},
        hamming_hist={"hd0": 10, "hd1": 2},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=3).first()
    stage_ms = q.perf_json["stage_ms"]
    assert "bk_ms" in stage_ms
    bk_val = stage_ms["bk_ms"]
    assert isinstance(bk_val, (int, float))
    assert bk_val >= 0
    assert abs(bk_val - 9999.99) < 1e-3


def test_DM18_lsh_candidate_count_integer_type(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm18" + "x" * 27
    _make_run(db_session, wid, rid)
    perf_in = {
        "version": "w12-hybrid-v1",
        "lsh_candidates": 12450,
        "lsh_candidate_count": 12450,
    }
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 50000},
        hamming_hist={"hd0": 100},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=1).first()
    has_count = "lsh_candidates" in q.perf_json or "lsh_candidate_count" in q.perf_json
    assert has_count, "lsh_candidates or lsh_candidate_count key missing in perf_json"
    cnt_val = q.perf_json.get("lsh_candidate_count", q.perf_json.get("lsh_candidates", -1))
    assert isinstance(cnt_val, int)
    assert cnt_val >= 0
    assert cnt_val == 12450


def test_DM19_lsh_filter_ratio_float_between_0_and_1(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm19" + "x" * 27
    _make_run(db_session, wid, rid)
    ratio_val = 0.001245
    perf_in = {
        "version": "w12-hybrid-v1",
        "lsh_candidate_filter_ratio": ratio_val,
        "lsh_filter_ratio": ratio_val,
    }
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 50000},
        hamming_hist={},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=1).first()
    has_ratio = "lsh_candidate_filter_ratio" in q.perf_json or "lsh_filter_ratio" in q.perf_json
    assert has_ratio, "lsh_candidate_filter_ratio or lsh_filter_ratio key missing"
    r_val = q.perf_json.get("lsh_filter_ratio", q.perf_json.get("lsh_candidate_filter_ratio", -1))
    assert isinstance(r_val, (int, float))
    assert 0.0 <= float(r_val) <= 1.0
    assert abs(float(r_val) - ratio_val) < 1e-6


def test_DM20_over_prefix_count_integer_nonnegative(db_session):
    wid = _make_wid(db_session)
    rid = "p-dm20" + "x" * 27
    _make_run(db_session, wid, rid)
    op_cnt = 8421
    perf_in = {
        "version": "w12-hybrid-v1",
        "oversample_prefix": True,
        "over_prefix_count": op_cnt,
        "oversample_prefix_pair_count": op_cnt,
    }
    dd = DedupDiagnostic(
        run_id=rid,
        step_idx=1,
        sizes_hist={"1": 50000},
        hamming_hist={"hd0": 10, "hd3": 1},
        perf_json=perf_in,
    )
    db_session.add(dd)
    db_session.commit()
    db_session.expire_all()
    q = db_session.query(DedupDiagnostic).filter_by(run_id=rid, step_idx=1).first()
    has_op = (
        "over_prefix_count" in q.perf_json
        or "oversample_prefix_pair_count" in q.perf_json
        or "oversample_prefix" in q.perf_json
    )
    assert has_op, "oversample-related key missing in perf_json (over_prefix_count / oversample_prefix_pair_count / oversample_prefix)"
    if "over_prefix_count" in q.perf_json:
        cnt = q.perf_json["over_prefix_count"]
        assert isinstance(cnt, int)
        assert cnt >= 0
        assert cnt == op_cnt
    elif "oversample_prefix_pair_count" in q.perf_json:
        cnt = q.perf_json["oversample_prefix_pair_count"]
        assert isinstance(cnt, int)
        assert cnt >= 0
        assert cnt == op_cnt
    else:
        assert q.perf_json["oversample_prefix"] is True or isinstance(q.perf_json["oversample_prefix"], bool)
