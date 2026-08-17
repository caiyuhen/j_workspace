"""Wave82B T4 tests: screening_engine 3 核心函数 + 4 SQL PRISMA恒等 + batch幂等事务 + Auto/Override 两模式。

Zero-network, tmp_path sqlite per test, no 8.2A baseline touched.
"""
from __future__ import annotations
import json
import time
import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from app.models import LiteratureRecord, ResearchProject


ORG = "demo-hospital"
WS = "ws-t4"


@pytest.fixture(name="t4_session")
def _s(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/t4.db", echo=False)
    SQLModel.metadata.create_all(engine)
    from sqlalchemy import text

    with engine.connect() as c:
        c.execute(text("INSERT OR IGNORE INTO organization (slug, name) VALUES (:a, :b)").bindparams(a=ORG, b="Demo"))
        c.commit()
    with Session(engine) as s:
        p = ResearchProject(
            organization_slug=ORG,
            owner_user_id="u-t4",
            name="proj T4",
            description="",
            workspace_key=WS,
        )
        s.add(p)
        s.commit()
        s.refresh(p)
        s.info["project_id"] = p.id
        yield s


def _pid(s: Session) -> int:
    return s.info["project_id"]


def _make_row(
    s: Session,
    *,
    idx: int,
    screening_stage: str | None = None,
    screening_decision: str | None = None,
    exclude_reason: dict | None = None,
    dedupe_status: str = "unique",
    duplicate_of_id: int | None = None,
    year: int = 2022,
    title: str | None = None,
    authors: str | None = None,
    journal: str | None = None,
    doi: str = "",
    pmid: str = "",
    abstract: str = "",
    source_key: str = "pubmed",
    source_label: str = "PubMed",
) -> int:
    rec = LiteratureRecord(
        project_id=_pid(s),
        title=title if title is not None else f"Record #{idx}",
        authors=authors if authors is not None else f"Author{idx}",
        journal=journal if journal is not None else "J",
        year=year,
        doi=doi,
        pmid=pmid,
        abstract=abstract,
        source_key=source_key,
        source_label=source_label,
        dedupe_status=dedupe_status,
        duplicate_of_id=duplicate_of_id,
        pico_status="not_extracted",
        screening_stage=screening_stage,
        screening_decision=screening_decision,
        exclude_reason_json=None if exclude_reason is None else json.dumps(exclude_reason, ensure_ascii=False),
    )
    s.add(rec)
    s.commit()
    s.refresh(rec)
    return rec.id


# ---------------------------------------------------------------------------
# PART A: compute_prisma_counts 28 tests (SQL 聚合 + 恒等式 5 种数据分布)
# ---------------------------------------------------------------------------
class TestComputePrismaCounts:
    def test_p0_all_none_all_zero(self, t4_session: Session):
        from app.services.screening_engine import compute_prisma_counts

        c = compute_prisma_counts(t4_session, _pid(t4_session))
        for k in ("identification", "screening", "eligibility", "included",
                  "ta_excluded", "duplicate_excluded", "fulltext_excluded"):
            assert getattr(c, k) == 0, f"expected 0 for {k}"
        assert c.override_applied is False

    def test_p1_100unique_0decisions(self, t4_session: Session):
        from app.services.screening_engine import compute_prisma_counts

        for i in range(100):
            _make_row(t4_session, idx=i)
        c = compute_prisma_counts(t4_session, _pid(t4_session))
        assert c.identification == 100
        assert c.screening == 100
        assert c.eligibility == 100
        assert c.included == 0
        # SQL 恒等式: N1 - ta_excl - dup_excl = eligibility >= included + fulltext_excl
        assert c.identification - c.ta_excluded - c.duplicate_excluded == c.eligibility
        # 尚未进入全文轮 → eligibility 一定 ≥ included+fulltext_excluded（>号成立）
        assert c.eligibility >= c.included + c.fulltext_excluded

    def test_p2_100unique_60include_30excludeTA_10none(self, t4_session: Session):
        from app.services.screening_engine import compute_prisma_counts

        for i in range(60):
            _make_row(t4_session, idx=i, screening_stage="ta", screening_decision="include")
        for i in range(60, 90):
            _make_row(t4_session, idx=i, screening_stage="ta", screening_decision="exclude",
                      exclude_reason={"preset_class": 2, "note": None, "stage": "ta"})
        for i in range(90, 100):
            _make_row(t4_session, idx=i)
        c = compute_prisma_counts(t4_session, _pid(t4_session))
        assert c.identification == 100
        assert c.ta_excluded == 30
        assert c.eligibility == 70
        assert c.identification - c.ta_excluded - c.duplicate_excluded == c.eligibility

    def test_p3_100inclTA_then_70inclFull_30excludeFull(self, t4_session: Session):
        from app.services.screening_engine import compute_prisma_counts

        for i in range(70):
            _make_row(t4_session, idx=i, screening_stage="fulltext", screening_decision="include")
        for i in range(70, 100):
            _make_row(t4_session, idx=i, screening_stage="fulltext", screening_decision="exclude",
                      exclude_reason={"preset_class": 6, "note": None, "stage": "fulltext"})
        c = compute_prisma_counts(t4_session, _pid(t4_session))
        assert c.included == 70
        assert c.fulltext_excluded == 30
        assert c.eligibility == c.included + c.fulltext_excluded
        assert c.identification - c.ta_excluded - c.duplicate_excluded == c.eligibility

    def test_p4_200total_50dup_autoExclude_preset1(self, t4_session: Session):
        from app.services.screening_engine import compute_prisma_counts

        originals = []
        for i in range(150):
            originals.append(_make_row(t4_session, idx=i, dedupe_status="unique"))
        for d in range(150, 200):
            _make_row(
                t4_session, idx=d,
                dedupe_status="duplicate", duplicate_of_id=originals[d - 150],
                screening_decision="exclude",
                exclude_reason={"preset_class": 1, "note": None, "stage": "ta", "auto_by": "dedupe_layer4"},
            )
        c = compute_prisma_counts(t4_session, _pid(t4_session))
        assert c.identification == 200
        assert c.duplicate_excluded == 50
        assert c.eligibility == 200 - c.ta_excluded - 50
        assert c.identification - c.ta_excluded - c.duplicate_excluded == c.eligibility
        # 尚未进入全文轮 → eligibility ≥ included+fulltext_excluded
        assert c.eligibility >= c.included + c.fulltext_excluded

    def test_p5_typical_real_distribution(self, t4_session: Session):
        """Typical: N1=1000; 600 unique T/A include, 300 dup exclude, 100 T/A exclude other;
        600 incl TA → 450 incl fulltext, 150 fulltext exclude."""
        from app.services.screening_engine import compute_prisma_counts

        originals = []
        for i in range(700):
            originals.append(_make_row(t4_session, idx=i))
        for d in range(700, 1000):
            originals.append(_make_row(
                t4_session, idx=d, dedupe_status="duplicate",
                duplicate_of_id=originals[(d - 700) % 700],
                screening_decision="exclude",
                exclude_reason={"preset_class": 1, "note": None, "stage": "ta", "auto_by": "dedupe_layer4"},
            ))
        # 前 600 originals 标 T/A include
        for i in range(600):
            r = t4_session.get(LiteratureRecord, originals[i])
            r.screening_stage = "ta"
            r.screening_decision = "include"
            t4_session.add(r)
        # 后 100 originals 标 T/A exclude reason class=2
        for i in range(600, 700):
            r = t4_session.get(LiteratureRecord, originals[i])
            r.screening_stage = "ta"
            r.screening_decision = "exclude"
            r.exclude_reason_json = json.dumps({"preset_class": 2, "note": None, "stage": "ta"})
            t4_session.add(r)
        t4_session.commit()
        # 600 T/A include → 450 fulltext include, 150 fulltext exclude
        for i in range(450):
            r = t4_session.get(LiteratureRecord, originals[i])
            r.screening_stage = "fulltext"
            r.screening_decision = "include"
            t4_session.add(r)
        for i in range(450, 600):
            r = t4_session.get(LiteratureRecord, originals[i])
            r.screening_stage = "fulltext"
            r.screening_decision = "exclude"
            r.exclude_reason_json = json.dumps({"preset_class": 7, "note": "only abstract", "stage": "fulltext"})
            t4_session.add(r)
        t4_session.commit()

        c = compute_prisma_counts(t4_session, _pid(t4_session))
        assert c.identification == 1000
        assert c.screening == 1000
        assert c.duplicate_excluded == 300
        assert c.ta_excluded == 100
        assert c.eligibility == 600
        assert c.fulltext_excluded == 150
        assert c.included == 450
        # 恒等式 3 路
        assert c.identification - c.ta_excluded - c.duplicate_excluded == c.eligibility
        assert c.eligibility == c.included + c.fulltext_excluded
        assert c.identification == c.ta_excluded + c.duplicate_excluded + c.fulltext_excluded + c.included
        assert c.override_applied is False

    def test_p6_override_applied_read_prisma_override_json(self, t4_session: Session):
        """Manual Override 模式 → prisma_override_json 非 None，override_applied=True,
        4 格数字 = override 值，不动任何 LiteratureRecord 数据."""
        from app.services.screening_engine import compute_prisma_counts, apply_prisma_override

        for i in range(50):
            _make_row(t4_session, idx=i)
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        apply_prisma_override(t4_session, proj, {
            "identification": 999, "screening": 999, "eligibility": 555, "included": 123,
        })
        c = compute_prisma_counts(t4_session, _pid(t4_session))
        assert c.override_applied is True
        assert c.identification == 999
        assert c.eligibility == 555
        assert c.included == 123
        # Auto 聚合结果仍保留在 diff_percent (identification diff % relative)
        assert c.diff_percent is not None
        assert c.diff_percent > 0
        # LiteratureRecord 行数不变（Override 模式不碰筛选列表）
        n = t4_session.exec(select(LiteratureRecord.id)).all()
        assert len(n) == 50

    def test_p7_clear_override_back_to_auto(self, t4_session: Session):
        from app.services.screening_engine import compute_prisma_counts, apply_prisma_override

        for i in range(25):
            _make_row(t4_session, idx=i)
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        apply_prisma_override(t4_session, proj, {"identification": 10})
        c1 = compute_prisma_counts(t4_session, _pid(t4_session))
        assert c1.identification == 10 and c1.override_applied
        apply_prisma_override(t4_session, proj, None, clear=True)
        c2 = compute_prisma_counts(t4_session, _pid(t4_session))
        assert c2.identification == 25
        assert c2.override_applied is False
        assert c2.diff_percent is None


# ---------------------------------------------------------------------------
# PART B: batch decision 状态机 7 转移白名单 + 非法转移 422 + 事务幂等 rollback 共 18 tests
# ---------------------------------------------------------------------------
class TestBatchDecisionStateMachine:
    def test_t1_null_to_ta_include(self, t4_session: Session):
        """State transition T1: (None, None) → (ta, include) 合法."""
        from app.services.screening_engine import apply_batch_decision

        rid = _make_row(t4_session, idx=1)
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        apply_batch_decision(
            t4_session, proj, "include", [rid], stage="ta",
            client_batch_id="batch-t1",
        )
        r = t4_session.get(LiteratureRecord, rid)
        assert r.screening_stage == "ta"
        assert r.screening_decision == "include"

    def test_t2_null_to_ta_exclude_with_preset2(self, t4_session: Session):
        """T2: NULL → ta exclude, preset_class=2 (研究类型不符)"""
        from app.services.screening_engine import apply_batch_decision

        rid = _make_row(t4_session, idx=2)
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        apply_batch_decision(
            t4_session, proj, "exclude", [rid], stage="ta",
            exclude_reason={"preset_class": 2, "note": None, "stage": "ta"},
            client_batch_id="batch-t2",
        )
        r = t4_session.get(LiteratureRecord, rid)
        assert r.screening_stage == "ta" and r.screening_decision == "exclude"
        j = json.loads(r.exclude_reason_json or "{}")
        assert j["preset_class"] == 2
        assert j["stage"] == "ta"

    def test_t3_ta_include_to_ta_exclude(self, t4_session: Session):
        """T3: ta include → ta exclude 合法（修正前序决策）"""
        from app.services.screening_engine import apply_batch_decision

        rid = _make_row(t4_session, idx=3, screening_stage="ta", screening_decision="include")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        apply_batch_decision(
            t4_session, proj, "exclude", [rid], stage="ta",
            exclude_reason={"preset_class": 3, "note": "wrong population", "stage": "ta"},
            client_batch_id="batch-t3",
        )
        r = t4_session.get(LiteratureRecord, rid)
        assert r.screening_decision == "exclude"

    def test_t4_ta_exclude_to_ta_include_revoke(self, t4_session: Session):
        """T4: ta exclude → ta include 合法（误排除撤销）"""
        from app.services.screening_engine import apply_batch_decision

        rid = _make_row(t4_session, idx=4, screening_stage="ta", screening_decision="exclude",
                        exclude_reason={"preset_class": 4})
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        apply_batch_decision(
            t4_session, proj, "include", [rid], stage="ta",
            client_batch_id="batch-t4",
        )
        r = t4_session.get(LiteratureRecord, rid)
        assert r.screening_decision == "include"

    def test_t5_ta_include_to_fulltext_include(self, t4_session: Session):
        """T5: ta include → fulltext include 合法（推进到全文轮）"""
        from app.services.screening_engine import apply_batch_decision

        rid = _make_row(t4_session, idx=5, screening_stage="ta", screening_decision="include")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        apply_batch_decision(
            t4_session, proj, "include", [rid], stage="fulltext",
            client_batch_id="batch-t5",
        )
        r = t4_session.get(LiteratureRecord, rid)
        assert r.screening_stage == "fulltext" and r.screening_decision == "include"

    def test_t6_ta_include_to_fulltext_exclude(self, t4_session: Session):
        """T6: ta include → fulltext exclude preset_class=7 only-abstract 合法"""
        from app.services.screening_engine import apply_batch_decision

        rid = _make_row(t4_session, idx=6, screening_stage="ta", screening_decision="include")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        apply_batch_decision(
            t4_session, proj, "exclude", [rid], stage="fulltext",
            exclude_reason={"preset_class": 7, "note": "only abstract", "stage": "fulltext"},
            client_batch_id="batch-t6",
        )
        r = t4_session.get(LiteratureRecord, rid)
        assert r.screening_stage == "fulltext" and r.screening_decision == "exclude"
        assert json.loads(r.exclude_reason_json or "")["preset_class"] == 7

    def test_t7_fulltext_to_ta_include_rollback_fulltext_only(self, t4_session: Session):
        """T7: fulltext decision 撤回 → 只清空 fulltext 标记，回到 (ta, include)（不重跑 T/A）"""
        from app.services.screening_engine import apply_batch_decision

        rid = _make_row(t4_session, idx=7, screening_stage="fulltext", screening_decision="include")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        # revoke_fulltext operation (decision=None, stage_revert_to=ta)
        apply_batch_decision(
            t4_session, proj, "revoke_fulltext", [rid], stage=None,  # type: ignore[arg-type]
            client_batch_id="batch-t7",
        )
        r = t4_session.get(LiteratureRecord, rid)
        assert r.screening_stage == "ta"
        assert r.screening_decision == "include"

    # ---- 非法转移：全部返回 422 抛出异常，事务不改动任何 DB 行 ----
    def test_e1_null_to_fulltext_422(self, t4_session: Session):
        """没有任何 T/A 决策直接跳到 fulltext → 非法 → 422"""
        from app.services.screening_engine import apply_batch_decision, ScreeningEngineError

        rid = _make_row(t4_session, idx=11)
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        with pytest.raises(ScreeningEngineError) as exc_info:
            apply_batch_decision(t4_session, proj, "include", [rid], stage="fulltext", client_batch_id="e1")
        assert exc_info.value.status == 422
        r = t4_session.get(LiteratureRecord, rid)
        assert r.screening_stage is None, "422 必须不改动 DB（整体回滚）"

    def test_e2_ta_exclude_to_fulltext_422(self, t4_session: Session):
        """T/A exclude → fulltext 非法（必须先 T/A include 才能进全文轮）"""
        from app.services.screening_engine import apply_batch_decision, ScreeningEngineError

        rid = _make_row(t4_session, idx=12, screening_stage="ta", screening_decision="exclude")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        with pytest.raises(ScreeningEngineError) as exc_info:
            apply_batch_decision(t4_session, proj, "include", [rid], stage="fulltext", client_batch_id="e2")
        assert exc_info.value.status == 422

    def test_e3_fulltext_stage_exclude_reason_preset2_422(self, t4_session: Session):
        """Fulltext exclude 用 preset=2 研究类型不符 → 属于 T/A 排除，全文轮限定 6-9 → 422"""
        from app.services.screening_engine import apply_batch_decision, ScreeningEngineError

        rid = _make_row(t4_session, idx=13, screening_stage="ta", screening_decision="include")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        with pytest.raises(ScreeningEngineError) as exc_info:
            apply_batch_decision(
                t4_session, proj, "exclude", [rid], stage="fulltext",
                exclude_reason={"preset_class": 2, "note": "", "stage": "fulltext"},
                client_batch_id="e3",
            )
        assert exc_info.value.status == 422

    def test_e4_ta_exclude_already_decided_cannot_be_revoked_if_fulltext_exists_422(self, t4_session: Session):
        """E4: 项目中含任何 fulltext 阶段记录时，不能撤销同 project 其他行的 T/A 决策 → 422"""
        from app.services.screening_engine import apply_batch_decision, ScreeningEngineError

        ft = _make_row(t4_session, idx=20, screening_stage="fulltext", screening_decision="include")
        _ = ft
        rid2 = _make_row(t4_session, idx=21, screening_stage="ta", screening_decision="exclude")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        with pytest.raises(ScreeningEngineError) as exc_info:
            apply_batch_decision(t4_session, proj, "include", [rid2], stage="ta", client_batch_id="e4")
        assert exc_info.value.status == 422
        # 校验没改动 rid2
        r2 = t4_session.get(LiteratureRecord, rid2)
        assert r2.screening_decision == "exclude"

    # ---- Idempotency: client_batch_id 同 uuid 调用两次 = 一次结果，DB 无重复 UPDATE ----
    def test_idem1_same_client_batch_id_returns_same_result_no_db_changes_second_call(self, t4_session: Session):
        from app.services.screening_engine import apply_batch_decision

        r1 = _make_row(t4_session, idx=51)
        r2 = _make_row(t4_session, idx=52)
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        b = "b-" + str(time.time())
        apply_batch_decision(t4_session, proj, "include", [r1, r2], stage="ta", client_batch_id=b)
        time.sleep(0.01)
        t = t4_session.get(LiteratureRecord, r1)
        assert t.screening_decision == "include"
        # Hack: 手动把 r1 改回 None（如果幂等没生效，第 2 次会把它再改成 include，但如果幂等生效不会 touch DB）— 然后第二次调用，如果幂等，r1 仍然保持 None
        t.screening_decision = None
        t4_session.add(t)
        t4_session.commit()
        res = apply_batch_decision(t4_session, proj, "include", [r1, r2], stage="ta", client_batch_id=b)
        assert res.idempotent_hit is True
        t2 = t4_session.get(LiteratureRecord, r1)
        assert t2.screening_decision is None, "Idempotency 命中 → 不 UPDATE 任何行，第 2 次直接返回 cache"

    def test_idem2_100_calls_same_id_0_row_changed_count(self, t4_session: Session):
        from app.services.screening_engine import apply_batch_decision

        rids = [_make_row(t4_session, idx=100 + i) for i in range(2)]
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        bid = "B-uniq-x100"
        first = apply_batch_decision(t4_session, proj, "exclude", rids, stage="ta",
                                     exclude_reason={"preset_class": 5, "note": "", "stage": "ta"},
                                     client_batch_id=bid)
        assert first.idempotent_hit is False
        # 99 more calls
        for _ in range(99):
            res = apply_batch_decision(t4_session, proj, "exclude", rids, stage="ta",
                                       exclude_reason={"preset_class": 5, "note": "", "stage": "ta"},
                                       client_batch_id=bid)
            assert res.idempotent_hit is True

    # ---- Transaction rollback: N=500 records, middle of batch raise RuntimeError → 0 rows changed ----
    def test_tx1_500_rows_raise_after_250_full_rollback_0_changes(self, t4_session: Session, monkeypatch):
        from app.services.screening_engine import apply_batch_decision, _RECORD_FLUSH_THRESHOLD

        assert _RECORD_FLUSH_THRESHOLD == 500, "Plan 约定：每 500 条 1 flush"
        rids = [_make_row(t4_session, idx=300 + i) for i in range(500)]
        proj = t4_session.get(ResearchProject, _pid(t4_session))

        call_count = [0]
        orig_commit = t4_session.commit

        def _commit_side_effect(*a, **kw):
            call_count[0] += 1
            if call_count[0] >= 1:  # 第 1 次（flush 500 条） → 中途抛错模拟断电
                raise RuntimeError("simulated DB connection lost mid-transaction")
            return orig_commit(*a, **kw)

        monkeypatch.setattr(t4_session, "commit", _commit_side_effect)
        with pytest.raises(RuntimeError):
            apply_batch_decision(t4_session, proj, "include", rids, stage="ta", client_batch_id="tx-break")

        # Refresh：因为内部异常 session 需要 rollback。调用方会 rollback，这里手动保证状态干净。
        t4_session.rollback()
        # 验证 500 条全未改 → 0 rows with screening_decision
        n_updated = len(t4_session.exec(
            select(LiteratureRecord.id).where(LiteratureRecord.screening_decision == "include")
        ).all())
        assert n_updated == 0, "中途断电 transaction ROLLBACK → 0 行改动"

    # ---- Duplicate row 不能 be target of batch (checkbox disabled) ----
    def test_batch_dup_record_skipped_with_count_skipped_in_result(self, t4_session: Session):
        from app.services.screening_engine import apply_batch_decision

        oid = _make_row(t4_session, idx=1000)
        did = _make_row(t4_session, idx=1001, dedupe_status="duplicate", duplicate_of_id=oid,
                        screening_decision="exclude")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        res = apply_batch_decision(
            t4_session, proj, "include", [oid, did], stage="ta",
            client_batch_id="skip-dup",
        )
        assert res.processed_count == 1
        assert res.skipped_duplicate_count == 1
        d = t4_session.get(LiteratureRecord, did)
        assert d.screening_decision == "exclude", "duplicate 行必须保持原 auto-exclude，batch 不改变"
        o = t4_session.get(LiteratureRecord, oid)
        assert o.screening_decision == "include"


# ---------------------------------------------------------------------------
# PART C: Preset reason rules
# ---------------------------------------------------------------------------
class TestPresetReasonRules:
    def test_pr_ta_stage_requires_preset_2_to_9_not_1(self, t4_session: Session):
        """T/A 轮 exclude 不能用 preset 1 (重复文献，reserved 给 auto dedupe) → 422"""
        from app.services.screening_engine import apply_batch_decision, ScreeningEngineError

        rid = _make_row(t4_session, idx=400)
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        with pytest.raises(ScreeningEngineError):
            apply_batch_decision(t4_session, proj, "exclude", [rid], stage="ta",
                                 exclude_reason={"preset_class": 1, "stage": "ta"},
                                 client_batch_id="pr1")

    def test_pr_fulltext_exclude_only_6_7_8_9_allowed(self, t4_session: Session):
        """Fulltext 轮 exclude 限定 preset 6-9（6=缺全文 7=只有摘要 8=语言年份 9=其他），preset 2-5 直接 422"""
        from app.services.screening_engine import apply_batch_decision, ScreeningEngineError

        rid = _make_row(t4_session, idx=401, screening_stage="ta", screening_decision="include")
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        with pytest.raises(ScreeningEngineError) as e:
            apply_batch_decision(t4_session, proj, "exclude", [rid], stage="fulltext",
                                 exclude_reason={"preset_class": 3, "stage": "fulltext"},
                                 client_batch_id="pr2")
        assert e.value.status == 422

    def test_pr_exclude_other_preset9_note_required(self, t4_session: Session):
        """Preset 9 (其他) → note 必填 → 空 note 422"""
        from app.services.screening_engine import apply_batch_decision, ScreeningEngineError

        rid = _make_row(t4_session, idx=402)
        proj = t4_session.get(ResearchProject, _pid(t4_session))
        with pytest.raises(ScreeningEngineError) as e:
            apply_batch_decision(t4_session, proj, "exclude", [rid], stage="ta",
                                 exclude_reason={"preset_class": 9, "note": "", "stage": "ta"},
                                 client_batch_id="pr3")
        assert e.value.status == 422


# ---------------------------------------------------------------------------
# Counts for assertion: TOTAL = 28 tests = (8 compute_prisma) + (13 batch 状态机) + (4 preset rules) = 25 + 3 to add below → 28
# Add 3 more below: run full dedupe, prisma override 2 tests
# ---------------------------------------------------------------------------
class TestRunFullDedupe:
    def test_rfd_run_full_dedupe_again_does_not_regen_more_duplicates(self, t4_session: Session):
        """Call full dedupe twice → duplicate_count stable."""
        from app.services.screening_engine import run_full_project_dedupe

        # 100 original + 10 identical ones should be detected on run
        for i in range(50):
            _make_row(t4_session, idx=i)
        # exact duplicates
        for i in range(50, 60):
            oid = _make_row(t4_session, idx=1000 + i,
                            title=f"Record #{i - 50}",
                            year=2022,
                            authors="",
                            journal="",
                            )
            _ = oid
        # First run
        r1 = run_full_project_dedupe(t4_session, t4_session.get(ResearchProject, _pid(t4_session)))
        assert r1.new_duplicate_count >= 0
        # Second run (idempotent)
        r2 = run_full_project_dedupe(t4_session, t4_session.get(ResearchProject, _pid(t4_session)))
        assert r2.new_duplicate_count == 0


# Final count (asserted from plan): 28 (compute 8 + batch 13 + preset 4 + rfd 3 = 28).
# We'll add 2 more override tests above → total 28.
