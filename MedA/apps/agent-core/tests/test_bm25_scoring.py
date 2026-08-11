from __future__ import annotations
from sqlmodel import Session, select

from app.models import LiteratureRecord
from app.services.bm25_scoring import (
    compute_bm25_scores_for,
    recompute_bm25_for_search_run,
    tokenize_for_bm25,
)
from tests.conftest import create_test_project, create_test_user


def test_tokenize_preserves_chinese_and_alphanum_lowercase() -> None:
    tokens = tokenize_for_bm25("Metformin 对 2型糖尿病患者 CVD 结局的影响 (RCT).")
    assert "metformin" in tokens
    assert "cvd" in tokens
    assert "rct" in tokens
    for c in "对型糖尿病患者结局的影响":
        assert c in tokens


def test_bm25_scores_higher_for_relevant_titles(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    docs = [
        ("SGLT2i reduces heart failure hospitalizations in T2DM CKD", "...", 2024, "10.1/a"),
        ("Lifestyle intervention and metformin for prediabetes", "...", 2023, "10.1/b"),
        ("Totally unrelated orthopedic surgery study", "...", 2022, "10.1/c"),
    ]
    for title, abstract, year, doi in docs:
        db_session.add(LiteratureRecord(
            project_id=project.id, title=title, authors="", journal="J",
            year=year, doi=doi, pmid="", source_key="pubmed",
            source_label="PubMed", dedupe_status="unique", pico_status="not_extracted",
        ))
    db_session.commit()
    records = list(db_session.exec(
        select(LiteratureRecord).where(LiteratureRecord.project_id == project.id)
    ).all())

    query = "SGLT2i 心力衰竭 T2DM CKD".split()
    scores = compute_bm25_scores_for(records, query)
    assert len(scores) == len(records)
    order = sorted(range(len(records)), key=lambda i: -scores[i])
    assert order[0] == 0
    assert scores[order[0]] > scores[order[1]] >= scores[order[2]]


def test_recompute_writes_relevance_score_to_each_record(db_session: Session) -> None:
    user = create_test_user(db_session)
    project = create_test_project(db_session, user)

    from app.models import SearchRun
    run = SearchRun(project_id=project.id, query_snapshot='{"p":"T2DM","i":"SGLT2i","boolean_text":"SGLT2i T2DM"}', selected_sources="pubmed", status="running")
    db_session.add(run)
    db_session.flush()

    for i in range(4):
        db_session.add(LiteratureRecord(
            project_id=project.id, title=f"Paper {i} about SGLT2i T2DM" if i % 2 == 0 else f"Paper {i} about influenza vaccine",
            authors="", journal="J", year=2024, doi=f"10.1/x{i}", pmid="", source_key="pubmed",
            source_label="PubMed", dedupe_status="unique",
            search_run_id=run.id, pico_status="not_extracted",
        ))
    db_session.commit()
    recompute_bm25_for_search_run(db_session, run.id)
    recs = list(db_session.exec(
        select(LiteratureRecord).where(LiteratureRecord.search_run_id == run.id)
    ).all())
    scores = {r.title: r.relevance_score for r in recs}
    assert max(scores["Paper 0 about SGLT2i T2DM"], scores["Paper 2 about SGLT2i T2DM"]) > \
        max(scores["Paper 1 about influenza vaccine"], scores["Paper 3 about influenza vaccine"])
