from collections.abc import Generator
import os

from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session as SessionClass


DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite://")

_is_in_memory_sqlite = DATABASE_URL in ("sqlite://", "sqlite:///:memory:")

if DATABASE_URL.startswith("sqlite"):
    # An in-memory database only survives as long as its single connection, so
    # pin the pool to one connection; file-backed sqlite keeps the default pool.
    _engine_kwargs = {"connect_args": {"check_same_thread": False}}
    if _is_in_memory_sqlite:
        _engine_kwargs["poolclass"] = StaticPool
else:
    _engine_kwargs = {"pool_pre_ping": True}

engine = create_engine(DATABASE_URL, **_engine_kwargs)


@event.listens_for(engine, "connect")
def _sqlite_enable_foreign_keys(dbapi_connection, connection_record) -> None:
    """SQLite disables FK enforcement per connection by default.

    Enable it once at connect time so every session sees the same referential
    integrity rules; otherwise a single test flipping the PRAGMA leaks the
    setting to everyone else sharing the StaticPool connection.
    """
    if not DATABASE_URL.startswith("sqlite"):
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


class SessionLocal:
    def __call__(self):
        return Session(engine)

    def __enter__(self):
        self._session = Session(engine)
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()
        return False


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
