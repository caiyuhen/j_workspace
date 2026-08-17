from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Session, select

from app.models import ExtractionTemplate


_EX1_LOCKED_MSG = "template_locked_cannot_change_fields"


def get_project_template(db: Session, project_id: int) -> ExtractionTemplate | None:
    stmt = select(ExtractionTemplate).where(ExtractionTemplate.project_id == project_id)
    return db.exec(stmt).first()


def _fields_equal_allowing_description(a: dict[str, Any], b: dict[str, Any]) -> bool:
    immutable = ("key", "type", "pico_binding", "required", "options", "label", "name")
    for k in immutable:
        if a.get(k) != b.get(k):
            return False
    return True


def save_template(
    db: Session,
    project_id: int,
    name: str,
    fields: list[dict[str, Any]],
    created_by: str | None = None,
) -> ExtractionTemplate:
    existing = get_project_template(db, project_id)
    if existing is None:
        t = ExtractionTemplate(
            project_id=project_id,
            name=name,
            description=None,
            created_by=created_by,
            fields_json=list(fields),
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        return t

    if existing.locked:
        if existing.name != name:
            raise Exception(_EX1_LOCKED_MSG)
        old_fields = existing.fields_json
        if len(old_fields) != len(fields):
            raise Exception(_EX1_LOCKED_MSG)
        for i, of in enumerate(old_fields):
            nf = fields[i]
            if not _fields_equal_allowing_description(of, nf):
                raise Exception(_EX1_LOCKED_MSG)

    existing.name = name
    existing.fields_json = list(fields)
    if created_by is not None:
        existing.created_by = created_by
    db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def lock_template(db: Session, template_id: int) -> ExtractionTemplate:
    t = db.get(ExtractionTemplate, template_id)
    if t is None:
        raise Exception(f"template {template_id} not found")
    if not t.locked:
        t.locked = True
        t.locked_at = datetime.utcnow()
        db.add(t)
        db.commit()
        db.refresh(t)
    return t
