from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ctms_common.client import call_service
from ctms_common.db import get_connection

app = FastAPI(title="Patient Management Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class PatientCreate(BaseModel):
    project_id: int
    name: str
    age: int
    severity: str
    operator_id: str
    operator_ip: str
    signature: str
    mfa_verified: bool = True


class EicfSign(BaseModel):
    patient_id: int
    operator_id: str
    operator_ip: str
    signature: str
    mfa_verified: bool = True


@app.on_event("startup")
def startup() -> None:
    conn = get_connection("patient_mgmt_service")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            severity TEXT NOT NULL,
            assigned_group TEXT NOT NULL,
            decision_id TEXT NOT NULL,
            eicf_signed INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.commit()


@app.post("/patients")
def enroll(payload: PatientCreate) -> dict:
    call_service("project_config_service", "PUT", f"/projects/{payload.project_id}/start-enrollment", None)
    conn = get_connection("patient_mgmt_service")
    cursor = conn.execute(
        "INSERT INTO patients (project_id, name, age, severity, assigned_group, decision_id, eicf_signed) VALUES (?, ?, ?, ?, ?, ?, 0)",
        (payload.project_id, payload.name, payload.age, payload.severity, "PENDING", "PENDING"),
    )
    patient_id = cursor.lastrowid
    decision = call_service(
        "randomization_service",
        "POST",
        "/randomize",
        {
            "project_id": payload.project_id,
            "patient_id": patient_id,
            "patient_data": {"age": payload.age, "severity": payload.severity},
            "operator_id": payload.operator_id,
            "operator_ip": payload.operator_ip,
            "signature": payload.signature,
            "mfa_verified": payload.mfa_verified,
        },
    )
    conn.execute("UPDATE patients SET assigned_group = ?, decision_id = ? WHERE id = ?", (decision["group"], decision["decision_id"], patient_id))
    conn.commit()
    return {"patient_id": patient_id, "assigned_group": decision["group"], "decision_id": decision["decision_id"]}


@app.get("/patients")
def list_patients(project_id: int | None = None) -> list[dict]:
    conn = get_connection("patient_mgmt_service")
    if project_id is None:
        rows = conn.execute("SELECT * FROM patients ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM patients WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    return [dict(row) for row in rows]


@app.post("/patients/eicf-sign")
def eicf_sign(payload: EicfSign) -> dict:
    conn = get_connection("patient_mgmt_service")
    patient = conn.execute("SELECT * FROM patients WHERE id = ?", (payload.patient_id,)).fetchone()
    if not patient:
        raise HTTPException(status_code=404, detail="patient not found")
    conn.execute("UPDATE patients SET eicf_signed = 1 WHERE id = ?", (payload.patient_id,))
    conn.commit()
    call_service(
        "audit_logging_service",
        "POST",
        "/audit",
        {
            "operator_id": payload.operator_id,
            "operator_ip": payload.operator_ip,
            "action": "EICF_SIGNED",
            "details": f"patient_id={payload.patient_id} eicf signed",
            "mfa_verified": payload.mfa_verified,
            "signature": payload.signature,
        },
    )
    return {"status": "signed"}
