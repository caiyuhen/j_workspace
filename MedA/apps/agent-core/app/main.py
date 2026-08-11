from fastapi import FastAPI

from app.db import init_db, SessionLocal
from app.routers.auth import router as auth_router
from app.routers.events import router as events_router
from app.routers.files import router as files_router
from app.routers.projects import router as projects_router
from app.routers.workspace import router as workspace_router

app = FastAPI(title="MedA Agent Core")
init_db()
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(events_router)
app.include_router(files_router)
app.include_router(workspace_router)


@app.on_event("startup")
async def _on_startup():
    from app.services.search_worker import start_worker_loop
    await start_worker_loop(lambda: SessionLocal)


@app.on_event("shutdown")
async def _on_shutdown():
    from app.services.search_worker import stop_worker_loop
    await stop_worker_loop(wait_timeout=2.0)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
