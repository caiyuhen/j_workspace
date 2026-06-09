<<<<<<< HEAD
<<<<<<< HEAD
import random
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ctms_common.client import call_service

app = FastAPI(title="Randomization Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class RandomizeRequest(BaseModel):
    project_id: int
    patient_id: int
    patient_data: dict
    operator_id: str
    operator_ip: str
    signature: str
    mfa_verified: bool = True


@app.post("/randomize")
def randomize(payload: RandomizeRequest) -> dict:
    project = call_service("project_config_service", "GET", f"/projects/{payload.project_id}")
    decision_id = str(uuid.uuid4())

    if project["randomization_enabled"] == 0:
        call_service(
            "audit_logging_service",
            "POST",
            "/audit",
            {
                "operator_id": payload.operator_id,
                "operator_ip": payload.operator_ip,
                "action": "DEFAULT_GROUP_ASSIGNED",
                "details": f"decision_id={decision_id}, patient_id={payload.patient_id}, group=Device Test",
                "mfa_verified": payload.mfa_verified,
                "signature": payload.signature,
            },
        )
        return {"decision_id": decision_id, "group": "Device Test"}

    result = call_service("data_validation_service", "POST", "/validate", {"patient_data": payload.patient_data})
    if not result["valid"]:
        call_service(
            "audit_logging_service",
            "POST",
            "/audit",
            {
                "operator_id": payload.operator_id,
                "operator_ip": payload.operator_ip,
                "action": "RANDOMIZATION_VALIDATION_FAILED",
                "details": f"decision_id={decision_id}, reason={result['reason']}",
                "mfa_verified": payload.mfa_verified,
                "signature": payload.signature,
            },
        )
        raise HTTPException(status_code=400, detail=result["reason"])

    assigned = random.choices(["Treatment", "Control"], weights=[2, 1], k=1)[0]
    call_service(
        "audit_logging_service",
        "POST",
        "/audit",
        {
            "operator_id": payload.operator_id,
            "operator_ip": payload.operator_ip,
            "action": "RANDOMIZED",
            "details": f"decision_id={decision_id}, patient_id={payload.patient_id}, group={assigned}",
            "mfa_verified": payload.mfa_verified,
            "signature": payload.signature,
        },
    )
    return {"decision_id": decision_id, "group": assigned}
=======
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
import random
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ctms_common.client import call_service

app = FastAPI(title="Randomization Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class RandomizeRequest(BaseModel):
    project_id: int
    patient_id: int
    patient_data: dict
    operator_id: str
    operator_ip: str
    signature: str
    mfa_verified: bool = True


@app.post("/randomize")
def randomize(payload: RandomizeRequest) -> dict:
    project = call_service("project_config_service", "GET", f"/projects/{payload.project_id}")
    decision_id = str(uuid.uuid4())

    if project["randomization_enabled"] == 0:
        call_service(
            "audit_logging_service",
            "POST",
            "/audit",
            {
                "operator_id": payload.operator_id,
                "operator_ip": payload.operator_ip,
                "action": "DEFAULT_GROUP_ASSIGNED",
                "details": f"decision_id={decision_id}, patient_id={payload.patient_id}, group=Device Test",
                "mfa_verified": payload.mfa_verified,
                "signature": payload.signature,
            },
        )
        return {"decision_id": decision_id, "group": "Device Test"}

    result = call_service("data_validation_service", "POST", "/validate", {"patient_data": payload.patient_data})
    if not result["valid"]:
        call_service(
            "audit_logging_service",
            "POST",
            "/audit",
            {
                "operator_id": payload.operator_id,
                "operator_ip": payload.operator_ip,
                "action": "RANDOMIZATION_VALIDATION_FAILED",
                "details": f"decision_id={decision_id}, reason={result['reason']}",
                "mfa_verified": payload.mfa_verified,
                "signature": payload.signature,
            },
        )
        raise HTTPException(status_code=400, detail=result["reason"])

    assigned = random.choices(["Treatment", "Control"], weights=[2, 1], k=1)[0]
    call_service(
        "audit_logging_service",
        "POST",
        "/audit",
        {
            "operator_id": payload.operator_id,
            "operator_ip": payload.operator_ip,
            "action": "RANDOMIZED",
            "details": f"decision_id={decision_id}, patient_id={payload.patient_id}, group={assigned}",
            "mfa_verified": payload.mfa_verified,
            "signature": payload.signature,
        },
    )
    return {"decision_id": decision_id, "group": assigned}
<<<<<<< HEAD
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
=======
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
