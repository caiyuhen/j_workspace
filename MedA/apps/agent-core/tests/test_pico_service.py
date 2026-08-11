from __future__ import annotations

from sqlmodel import Session, select

from app.models import LiteraturePico, LiteratureRecord
from app.services.pico import (
    PicoExtractionError,
    batch_extract_pico,
    extract_pico_for_record,
    suggest_pico_autofill,
)
from tests.conftest import create_test_project, create_test_user


def _insert_records(session: Session, project_id: int, specs):
    out = []
    for title, abstract, doi in specs:
        r = LiteratureRecord(
            project_id=project_id, title=title, authors="", journal="J",
            year=2024, doi=doi, pmid="", source_key="pubmed",
            source_label="PubMed", dedupe_status="unique", pico_status="not_extracted",
        )
        session.add(r)
        out.append(r)
    session.commit()
    for r in out:
        session.refresh(r)
    return out


def test_rct_sglti_cvd_rule_extracts_study_type_population_intervention(db_session: Session, monkeypatch) -> None:
    monkeypatch.setattr("app.services.pico._LLM_PROVIDER", None)

    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    [rec] = _insert_records(db_session, project.id, [
        (
            "SGLT2 Inhibitors and Cardiovascular Outcomes in T2DM: A Randomized Controlled Trial",
            "Background: T2DM patients ... Intervention: Empagliflozin 10mg daily vs. placebo ... Outcome: 3-point MACE (CV death, non-fatal MI, non-fatal stroke).",
            "10.1/sglt2i-cvd",
        ),
    ])

    pico = extract_pico_for_record(db_session, rec.id, method="rule_baseline")
    assert pico is not None
    assert pico.study_type == "rct"
    assert "T2DM" in (pico.population or "") or "糖尿病" in (pico.population or "")
    assert "SGLT" in (pico.intervention or "") or "Empagliflozin" in (pico.intervention or "")
    assert pico.extraction_method == "rule_baseline"
    assert 0 < (pico.confidence or 0) <= 1.0


def test_batch_skips_extracted_counts_failures(
    db_session: Session, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.pico._LLM_PROVIDER", None)

    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    specs = [
        ("Metformin vs placebo on T2DM (RCT)", "...", "10.1/m"),
        ("A prospective cohort of Dapagliflozin in CKD non-DM", "...", "10.1/d"),
    ]
    recs = _insert_records(db_session, project.id, specs)
    recs[1].pico_status = "extracted"
    session = db_session
    session.add(recs[1])
    session.commit()

    result = batch_extract_pico(session, [r.id for r in recs], method="rule_baseline")
    assert result.processed == 1
    assert result.already_had == 1
    assert result.failed == 0


def test_suggest_pico_returns_T2DM_in_SGLT2_out_with_supporting_ids(
    db_session: Session, monkeypatch
) -> None:
    monkeypatch.setattr("app.services.pico._LLM_PROVIDER", None)

    user = create_test_user(db_session)
    project = create_test_project(db_session, user)
    from app.models import SearchRun
    run = SearchRun(project_id=project.id, query_snapshot='{"p":"T2DM","i":"SGLT2i","boolean_text":"T2DM SGLT2i CVD RCT"}', selected_sources="pubmed", status="completed")
    db_session.add(run)
    db_session.flush()

    titles = [
        ("SGLT2i on CVD outcomes in patients with T2DM (RCT)", "...", "10.1/1"),
        ("Empagliflozin reduces HF hospitalization in T2DM CKD", "...", "10.1/2"),
        ("Influenza vaccine coverage 2023 (无关)", "...", "10.1/3"),
    ]
    for t, a, doi in titles:
        r = LiteratureRecord(project_id=project.id, title=t, authors="", journal="J", year=2024,
            doi=doi, pmid="", source_key="pubmed", source_label="PubMed",
            dedupe_status="unique", search_run_id=run.id, pico_status="not_extracted")
        db_session.add(r)
    db_session.commit()
    ids = list(r.id for r in db_session.exec(
        select(LiteratureRecord).where(LiteratureRecord.search_run_id == run.id)
    ).all())
    batch_extract_pico(db_session, ids, method="rule_baseline")

    draft = suggest_pico_autofill(db_session, run.id)
    assert "T2DM" in draft.p or "糖尿病" in draft.p
    assert "SGLT2" in draft.i or "Empagliflozin" in draft.i or "SGLT" in draft.i
    assert len(draft.supporting_record_ids) >= 2
