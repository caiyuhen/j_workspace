from fastapi import FastAPI

from app.db import init_db
from app.routers.projects import router as projects_router

app = FastAPI(title="MedA Agent Core")
init_db()
app.include_router(projects_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
