from __future__ import annotations

import dataclasses
from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import ExtractionCell, ExtractionTemplate, LiteratureRecord
from app.services.stats_evidence import cohen_kappa


_EX2_NOT_INCLUDED_MSG = "record_not_in_included_n4"


@dataclasses.dataclass
class EvidenceWideRow:
    record_id: int
    study_label: str
    values: dict[str, Any]


@dataclasses.dataclass
class KappaFieldSummary:
    field_key: str
    kappa: float
    warning_level: str
    n_pairs: int


def _normalize_value(v: Any) -> str:
    if v is None:
        return "∅"
    s = str(v)
    return s.strip().casefold()


def upsert_cell(
    db: Session,
    project_id: int,
    record_id: int,
    field_key: str,
    reviewer_id: str,
    value: Any,
    confidence: float | None = None,
) -> ExtractionCell:
    rec = db.get(LiteratureRecord, record_id)
    if rec is None:
        raise Exception(f"record {record_id} not found")
    if not (rec.screening_decision == "include" and rec.screening_stage == "fulltext"):
        raise Exception(_EX2_NOT_INCLUDED_MSG)

    stmt = select(ExtractionCell).where(
        ExtractionCell.record_id == record_id,
        ExtractionCell.field_key == field_key,
        ExtractionCell.reviewer_id == reviewer_id,
    )
    cell = db.exec(stmt).first()
    if cell is None:
        cell = ExtractionCell(
            record_id=record_id,
            field_key=field_key,
            reviewer_id=reviewer_id,
            project_id=project_id,
            value_json=value,
            confidence=confidence,
        )
    else:
        cell.value_json = value
        cell.confidence = confidence
        cell.extracted_at = datetime.utcnow()
    db.add(cell)
    db.commit()
    db.refresh(cell)
    return cell


def pivot_wide_evidence(
    db: Session,
    project_id: int,
    reviewer_ids: list[str] | None = None,
) -> list[EvidenceWideRow]:
    tpl = db.exec(
        select(ExtractionTemplate).where(ExtractionTemplate.project_id == project_id)
    ).first()
    if tpl is None:
        return []
    field_keys = [f["key"] for f in tpl.fields_json]

    included_stmt = select(LiteratureRecord).where(
        LiteratureRecord.project_id == project_id,
        LiteratureRecord.screening_decision == "include",
        LiteratureRecord.screening_stage == "fulltext",
    )
    records = db.exec(included_stmt).all()
    record_ids = [r.id for r in records]

    cell_stmt = select(ExtractionCell).where(
        ExtractionCell.project_id == project_id,
        ExtractionCell.record_id.in_(record_ids),
    )
    if reviewer_ids is not None and len(reviewer_ids) > 0:
        cell_stmt = cell_stmt.where(ExtractionCell.reviewer_id.in_(reviewer_ids))
    cells = db.exec(cell_stmt).all()

    agg: dict[tuple[int, str], Any] = {}
    for c in cells:
        key = (c.record_id, c.field_key)
        agg[key] = c.value_json

    rows: list[EvidenceWideRow] = []
    for r in records:
        label = r.title or f"Record {r.id}"
        values: dict[str, Any] = {}
        for fk in field_keys:
            values[fk] = agg.get((r.id, fk), None)
        rows.append(EvidenceWideRow(record_id=r.id, study_label=label, values=values))
    return rows


def kappa_summary(
    db: Session,
    project_id: int,
    reviewer_a_id: str,
    reviewer_b_id: str,
) -> list[KappaFieldSummary]:
    tpl = db.exec(
        select(ExtractionTemplate).where(ExtractionTemplate.project_id == project_id)
    ).first()
    if tpl is None:
        return []
    field_keys = [f["key"] for f in tpl.fields_json]

    included_stmt = select(LiteratureRecord).where(
        LiteratureRecord.project_id == project_id,
        LiteratureRecord.screening_decision == "include",
        LiteratureRecord.screening_stage == "fulltext",
    )
    record_ids = [r.id for r in db.exec(included_stmt).all()]

    cells = db.exec(
        select(ExtractionCell).where(
            ExtractionCell.project_id == project_id,
            ExtractionCell.record_id.in_(record_ids),
            ExtractionCell.reviewer_id.in_([reviewer_a_id, reviewer_b_id]),
        )
    ).all()

    by_field_rec_a: dict[str, dict[int, str]] = {fk: {} for fk in field_keys}
    by_field_rec_b: dict[str, dict[int, str]] = {fk: {} for fk in field_keys}
    for c in cells:
        bucket = by_field_rec_a if c.reviewer_id == reviewer_a_id else by_field_rec_b
        bucket[c.field_key][c.record_id] = _normalize_value(c.value_json)

    results: list[KappaFieldSummary] = []
    for fk in field_keys:
        a_vals = by_field_rec_a[fk]
        b_vals = by_field_rec_b[fk]
        common_rids = sorted(set(a_vals.keys()) & set(b_vals.keys()))
        n_pairs = len(common_rids)
        if n_pairs == 0:
            results.append(KappaFieldSummary(field_key=fk, kappa=0.0, warning_level="ok", n_pairs=0))
            continue

        categories = sorted(set(a_vals[rid] for rid in common_rids) | set(b_vals[rid] for rid in common_rids))
        cat_idx = {c: i for i, c in enumerate(categories)}
        k = len(categories)
        table = [[0] * k for _ in range(k)]
        for rid in common_rids:
            i = cat_idx[a_vals[rid]]
            j = cat_idx[b_vals[rid]]
            table[i][j] += 1
        k_val = cohen_kappa(table)
        warning = "low_agreement" if k_val < 0.6 else "ok"
        results.append(KappaFieldSummary(field_key=fk, kappa=k_val, warning_level=warning, n_pairs=n_pairs))
    return results
