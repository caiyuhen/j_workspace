"""Wave82B T2 tests: _detect_duplicate Layer4 + dedupe auto exclude + confirm_unique clear screening.

Zero-network (local sqlite tmp_path); no 8.2A baseline touched.
"""
from __future__ import annotations
import json
import pytest
from sqlmodel import Session, SQLModel, create_engine
from app.models import LiteratureRecord, ResearchProject
from app.services.literature import (
    _detect_duplicate,
    confirm_record_unique,
    import_unified_entries,
)
from app.services.sources.protocol import UnifiedLiteratureEntry


@pytest.fixture(name="db_session")
def session_fixture(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/test_w82b_t2.db", echo=False)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        p = ResearchProject(
            organization_slug="demo-hospital",
            owner_user_id="u-test-001",
            name="w82b t2 proj",
            description="",
            workspace_key="ws-test",
        )
        s.add(p)
        s.commit()
        s.refresh(p)
        s.info["project_id"] = p.id
        yield s


# ---------------------------------------------------------------------------
# T2-1. Layer4 SimHash / CJK Jaccard near-duplicate (same year bucket)
# ---------------------------------------------------------------------------
def test_detect_duplicate_layer4_simhash_same_year_hit(db_session: Session):
    """Same year + near-identical English title (only punctuation/case diff)
    → Layer4 should pick it up as duplicate. (Hamming ≤ 5 or exact simhash equal)"""
    pid = db_session.info["project_id"]
    t_existing = "Effect of metformin monotherapy versus combination on HbA1c in type 2 diabetes: a randomized controlled trial"
    existing = LiteratureRecord(
        project_id=pid, title=t_existing, year=2023,
        authors="Smith et al", journal="Diabetes Care",
        doi="", pmid="", abstract="",
        source_key="pubmed", source_label="PubMed",
        dedupe_status="unique",
        pico_status="not_extracted",
    )
    db_session.add(existing)
    db_session.commit()
    db_session.refresh(existing)

    t_candidate = "Effect of Metformin Monotherapy vs Combination on HbA1c in Type 2 Diabetes. A Randomized Controlled Trial."
    candidate = LiteratureRecord(
        project_id=pid, title=t_candidate, year=2023,
        authors="Jones et al", journal="Diabetes Care",
        doi="", pmid="", abstract="",
        source_key="cnki", source_label="CNKI",
        dedupe_status="unique",
        pico_status="not_extracted",
    )
    dup_id = _detect_duplicate(db_session, pid, candidate)
    assert dup_id == existing.id, "Layer4 SimHash should catch same-year near-identical title"


def test_detect_duplicate_layer4_diff_year_skipped(db_session: Session):
    """Identical titles but diff year → Layer4 skips (no dedupe)."""
    pid = db_session.info["project_id"]
    t = "Aspirin for primary cardiovascular prevention"
    existing = LiteratureRecord(
        project_id=pid, title=t, year=2020, authors="A", journal="J",
        doi="", pmid="", abstract="",
        source_key="pubmed", source_label="PubMed",
        dedupe_status="unique",
        pico_status="not_extracted",
    )
    db_session.add(existing)
    db_session.commit()
    candidate = LiteratureRecord(
        project_id=pid, title=t, year=2021,
        authors="B", journal="J", doi="", pmid="", abstract="",
        source_key="pubmed", source_label="PubMed",
        dedupe_status="unique",
        pico_status="not_extracted",
    )
    assert _detect_duplicate(db_session, pid, candidate) is None


def test_detect_duplicate_layer4_cjk_jaccard_hit(db_session: Session):
    """中文临床标题仅差 1 个虚字「的」 → Layer4 CJK Jaccard ≥ 0.92 命中 duplicate."""
    pid = db_session.info["project_id"]
    existing = LiteratureRecord(
        project_id=pid,
        title="针刺治疗脑卒中后肩痛的随机对照研究",
        year=2024, authors="张等", journal="中国针灸",
        doi="", pmid="", abstract="",
        source_key="cnki", source_label="CNKI",
        dedupe_status="unique",
        pico_status="not_extracted",
    )
    db_session.add(existing)
    db_session.commit()
    db_session.refresh(existing)
    candidate = LiteratureRecord(
        project_id=pid,
        title="针刺治疗脑卒中后肩痛随机对照研究",  # 少一个「的」
        year=2024, authors="李等", journal="中国针灸",
        doi="", pmid="", abstract="",
        source_key="wanfang", source_label="Wanfang",
        dedupe_status="unique",
        pico_status="not_extracted",
    )
    dup_id = _detect_duplicate(db_session, pid, candidate)
    assert dup_id == existing.id, "Layer4 CJK Jaccard (去虚字后 J≥0.92) 应该命中中文近似标题"


# ---------------------------------------------------------------------------
# T2-2. import_unified_entries dedupe → auto fill screening_decision=exclude + preset_class:1
# ---------------------------------------------------------------------------
def test_import_unified_dup_auto_exclude_reason_preset1(db_session: Session):
    pid = db_session.info["project_id"]
    t = "RCT of aspirin in elderly patients"
    existing = LiteratureRecord(
        project_id=pid, title=t, year=2022, authors="A", journal="J",
        doi="10.1000/old", pmid="", abstract="",
        source_key="pubmed", source_label="PubMed",
        dedupe_status="unique",
        pico_status="not_extracted",
    )
    db_session.add(existing)
    db_session.commit()

    entry = UnifiedLiteratureEntry(title=t, authors="B", year=2022, doi="10.1000/new",
                         pmid="", journal="J", abstract="",
                         source_key="cnki", source_record_id="cnki-001")
    result = import_unified_entries(db_session, pid, "cnki", [entry])
    assert result.duplicate_count == 1
    # 直接查同 project_id 最新插入的 LiteratureRecord (非 existing那条)
    from sqlmodel import select as _sel
    rows = db_session.exec(
        _sel(LiteratureRecord)
        .where(LiteratureRecord.project_id == pid, LiteratureRecord.id != existing.id)
        .order_by(LiteratureRecord.id.desc())
        .limit(1)
    ).all()
    assert len(rows) == 1
    rec = rows[0]
    assert rec.dedupe_status == "duplicate"
    assert rec.duplicate_of_id == existing.id
    # Wave82B auto screening exclude reason preset=1 (重复文献)
    assert rec.screening_decision == "exclude"
    reason = json.loads(rec.exclude_reason_json) if rec.exclude_reason_json else {}
    assert reason.get("preset_class") == 1
    assert reason.get("stage") == "ta"
    assert reason.get("auto_by") == "dedupe_layer4"


# ---------------------------------------------------------------------------
# T2-3. confirm_record_unique → clear auto screening fields
# ---------------------------------------------------------------------------
def test_confirm_record_unique_clears_auto_screening(db_session: Session):
    pid = db_session.info["project_id"]
    dup = LiteratureRecord(
        project_id=pid, title="Duplicate", year=2023,
        authors="", journal="", doi="", pmid="", abstract="",
        source_key="pubmed", source_label="PubMed",
        dedupe_status="duplicate", duplicate_of_id=999,
        pico_status="not_extracted",
        screening_decision="exclude",
        exclude_reason_json=json.dumps({"preset_class": 1, "note": None, "stage": "ta"}),
    )
    db_session.add(dup)
    db_session.commit()
    db_session.refresh(dup)
    proj = db_session.get(ResearchProject, pid)
    confirm_record_unique(db_session, proj, dup.id)  # type: ignore[arg-type]
    after = db_session.get(LiteratureRecord, dup.id)
    assert after.dedupe_status == "confirmed_unique"
    assert after.duplicate_of_id is None
    assert after.screening_decision is None, "confirm_unique 必须清空 auto exclude decision"
    assert after.exclude_reason_json is None, "confirm_unique 必须清空 auto exclude reason"
