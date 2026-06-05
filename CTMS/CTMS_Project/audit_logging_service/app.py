from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ctms_common.db import get_connection

app = FastAPI(title="Audit Logging Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class AuditRecord(BaseModel):
    operator_id: str = Field(min_length=2)
    operator_ip: str = Field(min_length=7)
    action: str = Field(min_length=3)
    details: str = Field(min_length=3)
    mfa_verified: bool = True
    signature: str = Field(min_length=6)


@app.on_event("startup")
def startup() -> None:
    conn = get_connection("audit_logging_service")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            operator_id TEXT NOT NULL,
            operator_ip TEXT NOT NULL,
            action TEXT NOT NULL,
            details TEXT NOT NULL,
            mfa_verified INTEGER NOT NULL,
            signature TEXT NOT NULL,
            timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


@app.post("/audit")
def create_audit(record: AuditRecord) -> dict:
    conn = get_connection("audit_logging_service")
    conn.execute(
        """
        INSERT INTO audit_logs (operator_id, operator_ip, action, details, mfa_verified, signature)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (record.operator_id, record.operator_ip, record.action, record.details, int(record.mfa_verified), record.signature),
    )
    conn.commit()
    return {"status": "logged"}


@app.get("/audit")
def list_audit() -> list[dict]:
    conn = get_connection("audit_logging_service")
    rows = conn.execute("SELECT * FROM audit_logs ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]
