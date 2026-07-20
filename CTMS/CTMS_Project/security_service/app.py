<<<<<<< HEAD
<<<<<<< HEAD
<<<<<<< HEAD
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ctms_common.db import get_connection

app = FastAPI(title="Security Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class RoleAssign(BaseModel):
    username: str
    role: str
    permission_group: str


class SensitiveOperation(BaseModel):
    username: str
    operation: str
    biometric_verified: bool
    otp_verified: bool


@app.on_event("startup")
def startup() -> None:
    conn = get_connection("security_service")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            permission_group TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS security_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            operation TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


@app.post("/rbac/assign")
def assign_role(payload: RoleAssign) -> dict:
    conn = get_connection("security_service")
    conn.execute(
        "INSERT INTO user_roles (username, role, permission_group) VALUES (?, ?, ?)",
        (payload.username, payload.role, payload.permission_group),
    )
    conn.commit()
    return {"assigned": True}


@app.get("/rbac/users")
def list_users() -> list[dict]:
    conn = get_connection("security_service")
    rows = conn.execute("SELECT * FROM user_roles ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


@app.post("/security/sensitive")
def sensitive_operation(payload: SensitiveOperation) -> dict:
    if not (payload.biometric_verified and payload.otp_verified):
        raise HTTPException(status_code=403, detail="double authentication required")
    conn = get_connection("security_service")
    conn.execute(
        "INSERT INTO security_audit (username, operation, status) VALUES (?, ?, ?)",
        (payload.username, payload.operation, "approved"),
    )
    conn.commit()
    return {"status": "approved"}
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ctms_common.db import get_connection

app = FastAPI(title="Security Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class RoleAssign(BaseModel):
    username: str
    role: str
    permission_group: str


class SensitiveOperation(BaseModel):
    username: str
    operation: str
    biometric_verified: bool
    otp_verified: bool


@app.on_event("startup")
def startup() -> None:
    conn = get_connection("security_service")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS user_roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            role TEXT NOT NULL,
            permission_group TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS security_audit (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            operation TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


@app.post("/rbac/assign")
def assign_role(payload: RoleAssign) -> dict:
    conn = get_connection("security_service")
    conn.execute(
        "INSERT INTO user_roles (username, role, permission_group) VALUES (?, ?, ?)",
        (payload.username, payload.role, payload.permission_group),
    )
    conn.commit()
    return {"assigned": True}


@app.get("/rbac/users")
def list_users() -> list[dict]:
    conn = get_connection("security_service")
    rows = conn.execute("SELECT * FROM user_roles ORDER BY id DESC").fetchall()
    return [dict(row) for row in rows]


@app.post("/security/sensitive")
def sensitive_operation(payload: SensitiveOperation) -> dict:
    if not (payload.biometric_verified and payload.otp_verified):
        raise HTTPException(status_code=403, detail="double authentication required")
    conn = get_connection("security_service")
    conn.execute(
        "INSERT INTO security_audit (username, operation, status) VALUES (?, ?, ?)",
        (payload.username, payload.operation, "approved"),
    )
    conn.commit()
    return {"status": "approved"}
<<<<<<< HEAD
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> origin/main
