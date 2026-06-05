from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ctms_common.client import call_service
from ctms_common.db import get_connection

app = FastAPI(title="Project Config Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2)
    randomization_enabled: bool
    protocol_reason: str = Field(default="Intervention")


class SwitchToggle(BaseModel):
    enabled: bool
    operator_id: str
    operator_ip: str
    signature: str
    mfa_verified: bool = True


class SiteCreate(BaseModel):
    project_id: int
    site_name: str
    planned_budget: float


@app.on_event("startup")
def startup() -> None:
    conn = get_connection("project_config_service")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            randomization_enabled INTEGER NOT NULL,
            protocol_reason TEXT NOT NULL,
            enrollment_started INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            site_name TEXT NOT NULL,
            planned_budget REAL NOT NULL
        )
        """
    )
    conn.commit()


@app.post("/projects")
def create_project(payload: ProjectCreate) -> dict:
    conn = get_connection("project_config_service")
    cursor = conn.execute(
        "INSERT INTO projects (name, randomization_enabled, protocol_reason) VALUES (?, ?, ?)",
        (payload.name, int(payload.randomization_enabled), payload.protocol_reason),
    )
    conn.commit()
    return {"project_id": cursor.lastrowid}


@app.get("/projects/{project_id}")
def get_project(project_id: int) -> dict:
    conn = get_connection("project_config_service")
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="project not found")
    return dict(row)


@app.put("/projects/{project_id}/start-enrollment")
def start_enrollment(project_id: int) -> dict:
    conn = get_connection("project_config_service")
    conn.execute("UPDATE projects SET enrollment_started = 1 WHERE id = ?", (project_id,))
    conn.commit()
    return {"status": "started"}


@app.put("/projects/{project_id}/randomization-switch")
def toggle_switch(project_id: int, payload: SwitchToggle) -> dict:
    conn = get_connection("project_config_service")
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="project not found")
    if row["enrollment_started"] == 1:
        call_service(
            "audit_logging_service",
            "POST",
            "/audit",
            {
                "operator_id": payload.operator_id,
                "operator_ip": payload.operator_ip,
                "action": "TOGGLE_BLOCKED",
                "details": f"project={project_id} blocked after enrollment started",
                "mfa_verified": payload.mfa_verified,
                "signature": payload.signature,
            },
        )
        raise HTTPException(status_code=400, detail="cannot switch after enrollment started")

    conn.execute("UPDATE projects SET randomization_enabled = ? WHERE id = ?", (int(payload.enabled), project_id))
    conn.commit()
    call_service(
        "audit_logging_service",
        "POST",
        "/audit",
        {
            "operator_id": payload.operator_id,
            "operator_ip": payload.operator_ip,
            "action": "TOGGLE_SUCCESS",
            "details": f"project={project_id} randomization={payload.enabled}",
            "mfa_verified": payload.mfa_verified,
            "signature": payload.signature,
        },
    )
    return {"status": "updated"}


@app.post("/sites")
def create_site(payload: SiteCreate) -> dict:
    conn = get_connection("project_config_service")
    cursor = conn.execute(
        "INSERT INTO sites (project_id, site_name, planned_budget) VALUES (?, ?, ?)",
        (payload.project_id, payload.site_name, payload.planned_budget),
    )
    conn.commit()
    return {"site_id": cursor.lastrowid}


@app.get("/sites")
def list_sites(project_id: int | None = None) -> list[dict]:
    conn = get_connection("project_config_service")
    if project_id is None:
        rows = conn.execute("SELECT * FROM sites ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM sites WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    return [dict(row) for row in rows]
