import sqlite3
from pathlib import Path

from ctms_common.config import load_config


def get_connection(service_name: str) -> sqlite3.Connection:
    config = load_config()
    base_dir = Path(config.get("database", "base_dir", fallback="./runtime_db"))
    base_dir.mkdir(parents=True, exist_ok=True)
    db_name = config.get(service_name, "database")
    conn = sqlite3.connect(base_dir / db_name, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
