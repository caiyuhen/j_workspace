from collections.abc import Generator

from fastapi import Depends
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool
from sqlmodel import Session as SessionClass


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


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
