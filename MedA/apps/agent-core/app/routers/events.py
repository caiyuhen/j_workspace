from fastapi import APIRouter

from app.services.events import broker

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/drain")
def drain_events() -> dict[str, list[dict]]:
    return {"events": broker.drain()}
