from fastapi import FastAPI

from app.db import init_db
from app.routers.auth import router as auth_router
from app.routers.events import router as events_router
from app.routers.files import router as files_router
from app.routers.projects import router as projects_router

app = FastAPI(title="MedA Agent Core")
init_db()
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(events_router)
app.include_router(files_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
