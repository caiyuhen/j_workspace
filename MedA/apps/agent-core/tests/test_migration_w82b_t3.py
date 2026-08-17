"""Wave82B T3 tests: idempotent migration + schemas.py 4+8 PRISMA field append.

Zero-network (local sqlite tmp_path); real SQL PRAGMA guard verification.
"""
from __future__ import annotations
import json
import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from app.models import LiteratureRecord, ResearchProject
from app.schemas import LiteratureRecordSummary, LiteratureStats


@pytest.fixture(name="tmp_sqlite_engine")
def _eng(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/prod_like.db", echo=False)
    # 创建旧版 schema（不含 5 个 W82B 新列）：先 drop 所有再用 raw SQL 建旧版表
    from sqlalchemy import text

    with engine.connect() as c:
        c.execute(text("DROP TABLE IF EXISTS literaturerecord"))
        c.execute(text("DROP TABLE IF EXISTS researchproject"))
        c.execute(text("DROP TABLE IF EXISTS organization"))
        c.execute(
            text(
                """CREATE TABLE organization (slug TEXT PRIMARY KEY, name TEXT NOT NULL DEFAULT '')"""
            )
        )
        c.execute(
            text(
                """INSERT OR IGNORE INTO organization (slug, name) VALUES ('demo-hospital', 'Demo Hospital')"""
            )
        )
        # 旧版 ResearchProject（无 prisma_override_json）
        c.execute(
            text(
                """CREATE TABLE researchproject (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    organization_slug TEXT NOT NULL REFERENCES organization(slug),
                    owner_user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    workspace_key TEXT NOT NULL
                )"""
            )
        )
        # 旧版 LiteratureRecord（无 4 screening 字段）
        c.execute(
            text(
                """CREATE TABLE literaturerecord (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL REFERENCES researchproject(id),
                    title TEXT NOT NULL,
                    authors TEXT NOT NULL DEFAULT '',
                    journal TEXT NOT NULL DEFAULT '',
                    year INTEGER,
                    doi TEXT NOT NULL DEFAULT '',
                    pmid TEXT NOT NULL DEFAULT '',
                    abstract TEXT NOT NULL DEFAULT '',
                    source_key TEXT NOT NULL,
                    source_label TEXT NOT NULL DEFAULT '',
                    dedupe_status TEXT NOT NULL DEFAULT 'unique',
                    duplicate_of_id INTEGER REFERENCES literaturerecord(id),
                    import_batch_id INTEGER,
                    search_run_id INTEGER,
                    relevance_score REAL,
                    pico_status TEXT NOT NULL DEFAULT 'not_extracted'
                )"""
            )
        )
        c.commit()
    return engine


# ---------------------------------------------------------------------------
# T3-1. Idempotent migration script: 2 次执行不报错 / 列存在 / 数据保留
# ---------------------------------------------------------------------------
def _run_migration_script(engine) -> None:
    """调用 scripts/w82b_add_screening_fields.py main(engine) — 0 pip 纯 stdlib."""
    import importlib.util
    from pathlib import Path

    p = Path(__file__).parent.parent / "scripts" / "w82b_add_5_fields.py"
    spec = importlib.util.spec_from_file_location("w82b_add_5_fields_migration", str(p))
    if spec is None or spec.loader is None:
        raise FileNotFoundError(p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.apply_idempotent(engine)


def test_migration_twice_idempotent_no_duplicate_column_error(tmp_sqlite_engine):
    """幂等：第 2 次 apply 不应 raise OperationalError 'duplicate column name'."""
    # 旧版 schema → 初始没有 screening_stage
    from sqlalchemy import text

    with tmp_sqlite_engine.connect() as c:
        cols1 = [r[1] for r in c.execute(text("PRAGMA table_info(literaturerecord)")).fetchall()]
    assert "screening_stage" not in cols1
    _run_migration_script(tmp_sqlite_engine)
    # 第 2 次执行 → 必须 0 错误（幂等）
    _run_migration_script(tmp_sqlite_engine)


def test_migration_5_columns_all_present_and_data_intact(tmp_sqlite_engine):
    """迁移后：LiteratureRecord 4 + ResearchProject 1 共 5 列全部存在，旧数据不丢."""
    from sqlalchemy import text

    pid = 1
    with tmp_sqlite_engine.connect() as c:
        c.execute(
            text(
                "INSERT INTO researchproject (id, organization_slug, owner_user_id, name, description, workspace_key) "
                "VALUES (1, 'demo-hospital', 'u-001', 'projA', 'desc', 'ws-1')"
            )
        )
        c.execute(
            text(
                "INSERT INTO literaturerecord (id, project_id, title, source_key, dedupe_status, pico_status) "
                "VALUES (7, 1, 'OldRecord', 'pubmed', 'unique', 'not_extracted')"
            )
        )
        c.commit()
    _run_migration_script(tmp_sqlite_engine)
    with Session(tmp_sqlite_engine) as s:
        cols_lr = [
            r[1] for r in s.connection().execute(text("PRAGMA table_info(literaturerecord)")).fetchall()
        ]
        cols_rp = [
            r[1] for r in s.connection().execute(text("PRAGMA table_info(researchproject)")).fetchall()
        ]
        for col in ["screening_stage", "screening_decision", "exclude_reason_json", "screening_notes"]:
            assert col in cols_lr, f"Missing LiteratureRecord col: {col}"
        assert "prisma_override_json" in cols_rp
        # 旧行数据保留
        rec = s.get(LiteratureRecord, 7)
        assert rec is not None and rec.title == "OldRecord"
        assert rec.screening_decision is None  # 新增 nullable 默认 NULL
        proj = s.get(ResearchProject, pid)
        assert proj is not None and proj.name == "projA"
        assert proj.prisma_override_json is None


# ---------------------------------------------------------------------------
# T3-2. schemas.py 4+8 field serialize
# ---------------------------------------------------------------------------
def test_schemas_literature_summary_4_fields_prisma_stats_8_fields_serialize():
    """LiteratureRecordSummary 含 4 screening 字段；LiteratureStats 含 8 PRISMA 字段，model_dump JSON 可序列化无 Pydantic ValidationError."""
    rec_dict = dict(
        id=1,
        title="t",
        authors="a",
        journal="j",
        year=2023,
        doi="",
        pmid="",
        source_key="pubmed",
        source_label="PubMed",
        dedupe_status="unique",
        duplicate_of_id=None,
        # W82B new 4
        screening_stage="ta",
        screening_decision="include",
        exclude_reason_json=None,
        screening_notes="passed criteria",
    )
    r = LiteratureRecordSummary(**rec_dict)
    dumped1 = r.model_dump(mode="json")
    assert dumped1["screening_stage"] == "ta"
    assert dumped1["screening_decision"] == "include"
    assert dumped1["screening_notes"] == "passed criteria"

    s = LiteratureStats(
        total_count=10,
        unique_count=8,
        duplicate_count=2,
        by_source=[],
        # W82B new 8 PRISMA 2020 4 格 × 2 组 (n_count + excluded_count) = 8
        prisma_identification=10,
        prisma_screening=10,
        prisma_eligibility=7,
        prisma_included=4,
        prisma_ta_excluded=3,
        prisma_duplicate_excluded=0,
        prisma_fulltext_excluded=3,
        prisma_eligibility_unknown=0,
    )
    dumped2 = s.model_dump(mode="json")
    assert dumped2["prisma_identification"] == 10
    assert dumped2["prisma_included"] == 4
    # SQL 恒等式: N1 - TA_EXCL - DUP_EXCL = ELIGIBILITY = INCLUDED + FULLTEXT_EXCL
    assert (dumped2["prisma_identification"] - dumped2["prisma_ta_excluded"] - dumped2["prisma_duplicate_excluded"]
            == dumped2["prisma_eligibility"]
            == dumped2["prisma_included"] + dumped2["prisma_fulltext_excluded"])
    # JSON dumpable
    json.dumps(dumped1)
    json.dumps(dumped2)
