from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ctms_common.db import get_connection

app = FastAPI(title="Monitoring Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class RiskMetric(BaseModel):
    project_id: int
    metric_name: str
    metric_value: float
    threshold: float


@app.on_event("startup")
def startup() -> None:
    conn = get_connection("monitoring_service")
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS risk_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            metric_name TEXT NOT NULL,
            metric_value REAL NOT NULL,
            threshold REAL NOT NULL,
            breached INTEGER NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()


@app.post("/risk/metrics")
def create_metric(payload: RiskMetric) -> dict:
    breached = payload.metric_value > payload.threshold
    conn = get_connection("monitoring_service")
    conn.execute(
        "INSERT INTO risk_metrics (project_id, metric_name, metric_value, threshold, breached) VALUES (?, ?, ?, ?, ?)",
        (payload.project_id, payload.metric_name, payload.metric_value, payload.threshold, int(breached)),
    )
    conn.commit()
    return {"breached": breached}


@app.get("/risk/dashboard")
def dashboard(project_id: int | None = None) -> dict:
    conn = get_connection("monitoring_service")
    if project_id is None:
        rows = conn.execute("SELECT * FROM risk_metrics ORDER BY id DESC").fetchall()
    else:
        rows = conn.execute("SELECT * FROM risk_metrics WHERE project_id = ? ORDER BY id DESC", (project_id,)).fetchall()
    return {"metrics": [dict(row) for row in rows], "prediction_window_days": 30}
