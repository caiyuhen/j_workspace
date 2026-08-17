"""Wave82B T3 Idempotent migration: 4 screening + 1 prisma_override nullable cols.

Run N times — safe (Python PRAGMA column_exists guard → skip already-added ALTER).
0 pip pure stdlib/sqlalchemy.text.
"""
from __future__ import annotations
from sqlalchemy import text


# (table, column_name, alter_statement)
_ALTER_QUEUE: list[tuple[str, str, str]] = [
    (
        "literaturerecord",
        "screening_stage",
        "ALTER TABLE literaturerecord ADD COLUMN screening_stage TEXT",
    ),
    (
        "literaturerecord",
        "screening_decision",
        "ALTER TABLE literaturerecord ADD COLUMN screening_decision TEXT",
    ),
    (
        "literaturerecord",
        "exclude_reason_json",
        "ALTER TABLE literaturerecord ADD COLUMN exclude_reason_json TEXT",
    ),
    (
        "literaturerecord",
        "screening_notes",
        "ALTER TABLE literaturerecord ADD COLUMN screening_notes TEXT",
    ),
    (
        "researchproject",
        "prisma_override_json",
        "ALTER TABLE researchproject ADD COLUMN prisma_override_json TEXT",
    ),
]


def _column_exists(engine, table: str, col: str) -> bool:
    with engine.connect() as c:
        rows = c.execute(text(f"PRAGMA table_info({table})")).fetchall()
        return any(r[1] == col for r in rows)


def apply_idempotent(engine) -> None:
    """Python 层 PRAGMA guard：列存在就跳过 → 100 次执行 0 副作用."""
    for table, col_name, stmt in _ALTER_QUEUE:
        if _column_exists(engine, table, col_name):
            continue
        with engine.connect() as c:
            c.execute(text(stmt))
            c.commit()


if __name__ == "__main__":  # pragma: no cover - manual runner
    from app.db import engine as default_engine

    apply_idempotent(default_engine)
