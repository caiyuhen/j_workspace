from collections.abc import Generator

import pytest

from app.db import init_db, reset_db


@pytest.fixture(autouse=True)
def reset_database() -> Generator[None, None, None]:
    reset_db()
    init_db()
    yield
