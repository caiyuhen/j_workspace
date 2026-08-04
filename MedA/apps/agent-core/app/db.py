from collections.abc import Generator

from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def reset_db() -> None:
    SQLModel.metadata.drop_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
