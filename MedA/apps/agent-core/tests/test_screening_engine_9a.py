"""Wave9a Task4: 10步漏斗 + 9项排除校验（S1~S10 + B1~B5，共15条）。"""
from __future__ import annotations
import pytest


class TestWave9aFunnel:
    def test_s1_n4_lt_n3_hamming_after_dupe(self):
        """S1: calc_funnel_from_records(n3=8651, n4_dupes_removed=1447) → N4=7204 < N3。"""
        from app.services.screening_engine import calc_funnel_from_records

        funnel = calc_funnel_from_records(n3=8651, n4_dupes_removed=1447)

        assert funnel["N3"] == 8651
        assert funnel["N4"] == 7204
        assert funnel["N4"] < funnel["N3"]

    def test_s2_e1_count_equals_n4_count(self):
        """S2: 相同输入 → E1 count == N4 count (= 7204)。"""
        from app.services.screening_engine import calc_funnel_from_records

        funnel = calc_funnel_from_records(n3=8651, n4_dupes_removed=1447)

        assert funnel["E1"] == funnel["N4"]
        assert funnel["E1"] == 7204

    def test_s3_screening_ta_exclude_id_6_raises_ta_allowed_false(self):
        """S3: validate_exclude_decision(stage='screening_ta', exclude_ids=[6], meta_json={}) → ValueError 含 ta_allowed=False。"""
        from app.services.screening_engine import validate_exclude_decision

        with pytest.raises(ValueError) as exc_info:
            validate_exclude_decision(
                stage="screening_ta",
                exclude_ids=[6],
                meta_json={},
            )
        assert "ta_allowed=False" in str(exc_info.value)

    # ── 新增 S4~S10 + B1~B5 ────────────────────────────────────────────

    def test_s4_exclude_8_requires_contact_attempts_ge_2(self):
        """S4: exclude #8 需 contact_attempts>=2 → 传 1 次 ValueError。"""
        from app.services.screening_engine import validate_exclude_decision

        with pytest.raises(ValueError) as exc_info:
            validate_exclude_decision(
                stage="screening_fulltext",
                exclude_ids=[8],
                meta_json={"contact_attempts": 1},
            )
        assert "requires_contact_attempts>=2" in str(exc_info.value)

    def test_s5_exclude_9_requires_rationale_ge_20_chars(self):
        """S5: exclude #9 需 rationale>=20 char → 传 10 chars ValueError。"""
        from app.services.screening_engine import validate_exclude_decision

        with pytest.raises(ValueError) as exc_info:
            validate_exclude_decision(
                stage="screening_ta",
                exclude_ids=[9],
                meta_json={"rationale": "0123456789"},
            )
        assert "requires_rationale_len>=20" in str(exc_info.value)

    def test_s6_e6_count_equals_e4_minus_e5_with_ft_exclusion(self):
        """S6: E6 count = E4 - E5 (含 FT exclusion)。"""
        from app.services.screening_engine import calc_funnel_from_records

        funnel = calc_funnel_from_records(
            n3=1000,
            n4_dupes_removed=100,
            e2=50,
            e4=700,
            e5=120,
        )

        assert funnel["E4"] == 700
        assert funnel["E5"] == 120
        assert funnel["E6"] == 700 - 120
        assert funnel["E6"] == 580

    def test_s7_step_n1_done_n2_unlocked_n3_zero_locks_all_downstream(self):
        """S7: step N1 完成后 N2 unlocked; N3=0 → N4/N5/E1.. 全都 locked=true。"""
        from app.services.screening_engine import calc_funnel_locks_integrity

        n1 = 5000
        n2 = n1
        n3 = 0
        n4_dupes = 0

        locks = calc_funnel_locks_integrity(
            n1=n1, n2=n2, n3=n3, n4_dupes_removed=n4_dupes
        )

        assert locks["N1"]["locked"] is False
        assert locks["N2"]["locked"] is False
        assert locks["N3"]["locked"] is False
        assert locks["N4"]["locked"] is True
        assert locks["E1"]["locked"] is True
        assert locks["E2"]["locked"] is True
        assert locks["E3"]["locked"] is True
        assert locks["E4"]["locked"] is True
        assert locks["E5"]["locked"] is True
        assert locks["E6"]["locked"] is True

    def test_s8_screened_total_equals_included_plus_excluded_ta(self):
        """S8: screened_total = included_TA + excluded_TA (integrity)。"""
        from app.services.screening_engine import calc_screening_integrity_from_counts

        result = calc_screening_integrity_from_counts(
            included_ta=800,
            excluded_ta=200,
            screened_pool=1000,
        )

        assert result["screened_total"] == 1000
        assert result["integrity_ok"] is True
        assert result["screened_total"] == result["included_ta"] + result["excluded_ta"]

        # Without an independent pool size there is nothing to compare the sum
        # against, so integrity is unknown rather than trivially satisfied.
        assert calc_screening_integrity_from_counts(
            included_ta=800, excluded_ta=200
        )["integrity_ok"] is None
        assert calc_screening_integrity_from_counts(
            included_ta=800, excluded_ta=200, screened_pool=1200
        )["integrity_ok"] is False

    def test_s9_exclude_6_7_requires_evidence_quotes_fulltext_stage(self):
        """S9: exclude #6/7 需 evidence_quotes → 传空 ValueError (Fulltext 阶段)。"""
        from app.services.screening_engine import validate_exclude_decision

        for rid in [6, 7]:
            with pytest.raises(ValueError) as exc_info:
                validate_exclude_decision(
                    stage="screening_fulltext",
                    exclude_ids=[rid],
                    meta_json={"evidence_quotes": [], "contact_attempts": 2},
                )
            assert "requires_evidence=True" in str(exc_info.value)

    def test_s10_big_e6_77_evidence_artifact_roundtrip(self, db_session):
        """S10-Big: 模拟 E6=77，DB 写入 EvidenceArtifact 77 rows screening_fulltext + include → query count=77。"""
        from app.services.screening_engine import (
            bulk_insert_evidence_artifacts,
            query_evidence_artifact_count,
        )
        from app.models import User, Organization, ResearchProject, LiteratureRecord
        from tests.conftest import create_test_user, create_test_project

        user = create_test_user(db_session)
        project = create_test_project(db_session, user)

        e6_count = 77
        lrs = []
        for i in range(e6_count):
            lr = LiteratureRecord(
                project_id=project.id,
                title=f"FT Include Rec {i}",
                source_key="pubmed",
                screening_stage="fulltext",
                screening_decision="include",
            )
            db_session.add(lr)
            lrs.append(lr)
        db_session.flush()

        artifacts = []
        for lr in lrs:
            artifacts.append(
                {
                    "literature_record_id": lr.id,
                    "stage": "screening_fulltext",
                    "decision": "include",
                    "confidence": 0.9,
                    "exclude_reason_ids": [],
                    "meta_json": {"source": "s10_big_test"},
                    "created_by": user.user_id,
                }
            )

        inserted = bulk_insert_evidence_artifacts(db_session, artifacts)
        assert inserted == e6_count

        db_session.commit()

        counted = query_evidence_artifact_count(
            db_session,
            stage="screening_fulltext",
            decision="include",
        )
        assert counted == e6_count

    def test_b1_exclude_2_allowed_any_stage(self):
        """B1: exclude #2 任何阶段（规则允许的阶段内）允许——即不需要 evidence/contact_attempts/rationale 额外限制。"""
        from app.services.screening_engine import validate_exclude_decision, EXCLUDE_REASONS

        try:
            validate_exclude_decision(
                stage="screening_ta",
                exclude_ids=[2],
                meta_json={},
            )
        except ValueError:
            pytest.fail("exclude #2 should be allowed at T/A stage with empty meta")

        r2 = EXCLUDE_REASONS[2]
        assert r2["requires_evidence"] is False
        assert r2["requires_contact_attempts"] is False
        assert r2["requires_rationale_len"] == 0
        assert r2["ta_allowed"] is True

    def test_b2_exclude_6_not_allowed_at_ta_stage(self):
        """B2: exclude #6 TA 阶段 不允许。"""
        from app.services.screening_engine import validate_exclude_decision

        with pytest.raises(ValueError) as exc_info:
            validate_exclude_decision(
                stage="screening_ta",
                exclude_ids=[6],
                meta_json={},
            )
        assert "ta_allowed=False" in str(exc_info.value)

    def test_b3_calc_funnel_defaults_n3_zero_all_steps_locked_and_zero(self):
        """B3: calc_funnel 参数缺省（n3=0）所有 step count=0 locked。"""
        from app.services.screening_engine import (
            calc_funnel_from_records,
            calc_funnel_locks_integrity,
        )

        funnel = calc_funnel_from_records()
        locks = calc_funnel_locks_integrity()

        for key in ["N1", "N2", "N3", "N4", "E1", "E2", "E3", "E4", "E5", "E6"]:
            assert funnel[key] == 0, f"funnel[{key}] should be 0 with default args"
            assert locks[key]["locked"] is True, f"locks[{key}] should be True with default args"

    def test_b4_funnel_order_literal_10_steps_exact(self):
        """B4: 10 step FUNNEL_ORDER 字面值准确 (N1 N2 N3 N4 E1 E2 E3 E4 E5 E6)。"""
        from app.services.screening_engine import FUNNEL_ORDER

        expected = ["N1", "N2", "N3", "N4", "E1", "E2", "E3", "E4", "E5", "E6"]
        assert FUNNEL_ORDER == expected

    def test_b5_validate_exclude_decision_empty_ids_passes(self):
        """B5: validate_exclude_decision 空 exclude_ids 通过 True。"""
        from app.services.screening_engine import validate_exclude_decision

        result = validate_exclude_decision(
            stage="screening_ta",
            exclude_ids=[],
            meta_json={},
        )
        assert result is True
