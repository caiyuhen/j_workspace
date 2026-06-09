<<<<<<< HEAD
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Data Validation Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ValidateRequest(BaseModel):
    patient_data: dict


class CleanRequest(BaseModel):
    points: list[dict]


@app.post("/validate")
def validate(payload: ValidateRequest) -> dict:
    age = payload.patient_data.get("age", 0)
    severity = payload.patient_data.get("severity", "")
    if age < 18:
        return {"valid": False, "reason": "age must >= 18"}
    if severity not in {"low", "medium", "high"}:
        return {"valid": False, "reason": "severity invalid"}
    return {"valid": True}


@app.post("/clean")
def clean(payload: CleanRequest) -> dict:
    anomalies = []
    valid = []
    for point in payload.points:
        value = point.get("value")
        if value is None:
            anomalies.append({"id": point.get("id"), "issue": "missing"})
        elif isinstance(value, (int, float)) and (value < 0 or value > 1000):
            anomalies.append({"id": point.get("id"), "issue": "out_of_range"})
        else:
            valid.append(point)
    return {"valid_count": len(valid), "anomaly_count": len(anomalies), "anomalies": anomalies}
=======
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="Data Validation Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class ValidateRequest(BaseModel):
    patient_data: dict


class CleanRequest(BaseModel):
    points: list[dict]


@app.post("/validate")
def validate(payload: ValidateRequest) -> dict:
    age = payload.patient_data.get("age", 0)
    severity = payload.patient_data.get("severity", "")
    if age < 18:
        return {"valid": False, "reason": "age must >= 18"}
    if severity not in {"low", "medium", "high"}:
        return {"valid": False, "reason": "severity invalid"}
    return {"valid": True}


@app.post("/clean")
def clean(payload: CleanRequest) -> dict:
    anomalies = []
    valid = []
    for point in payload.points:
        value = point.get("value")
        if value is None:
            anomalies.append({"id": point.get("id"), "issue": "missing"})
        elif isinstance(value, (int, float)) and (value < 0 or value > 1000):
            anomalies.append({"id": point.get("id"), "issue": "out_of_range"})
        else:
            valid.append(point)
    return {"valid_count": len(valid), "anomaly_count": len(anomalies), "anomalies": anomalies}
>>>>>>> 9750b2979c0547a41eee960f69d088078d2151a8
