import os
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Any, Dict, List

# SQLite database file path
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
if not os.path.exists(DB_DIR):
    os.makedirs(DB_DIR)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'omop_platform.db')}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def _quote_sqlite_identifier(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def _sqlite_column_definition(column: Any, dialect: Any) -> str:
    column_type = column.type.compile(dialect=dialect)
    return f"{_quote_sqlite_identifier(column.name)} {column_type}"


def ensure_sqlite_schema_compatibility(engine: Any, metadata: MetaData) -> Dict[str, List[str]]:
    if engine.dialect.name != "sqlite":
        return {"columns_added": [], "indexes_added": [], "tables_created": []}

    changes = {"columns_added": [], "indexes_added": [], "tables_created": []}

    with engine.begin() as conn:
        existing_tables = {
            row[0]
            for row in conn.exec_driver_sql(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }

        for table in metadata.sorted_tables:
            if table.name not in existing_tables:
                table.create(bind=conn, checkfirst=True)
                changes["tables_created"].append(table.name)
                existing_tables.add(table.name)
                continue

            table_name_sql = _quote_sqlite_identifier(table.name)
            existing_columns = {
                row[1]
                for row in conn.exec_driver_sql(f"PRAGMA table_info({table_name_sql})").fetchall()
            }

            for column in table.columns:
                if column.primary_key or column.name in existing_columns:
                    continue
                column_sql = _sqlite_column_definition(column, engine.dialect)
                conn.exec_driver_sql(f"ALTER TABLE {table_name_sql} ADD COLUMN {column_sql}")
                changes["columns_added"].append(f"{table.name}.{column.name}")
                existing_columns.add(column.name)

            existing_indexes = {
                row[1]
                for row in conn.exec_driver_sql(f"PRAGMA index_list({table_name_sql})").fetchall()
            }
            for column in table.columns:
                if not getattr(column, "index", False) or column.name not in existing_columns:
                    continue
                index_name = f"ix_{table.name}_{column.name}"
                if index_name in existing_indexes:
                    continue
                index_name_sql = _quote_sqlite_identifier(index_name)
                column_name_sql = _quote_sqlite_identifier(column.name)
                conn.exec_driver_sql(
                    f"CREATE INDEX IF NOT EXISTS {index_name_sql} ON {table_name_sql} ({column_name_sql})"
                )
                changes["indexes_added"].append(index_name)

    return changes

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
