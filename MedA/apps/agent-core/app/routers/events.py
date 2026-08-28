from fastapi import APIRouter, Depends

from app.deps.auth import SessionContext, require_admin
from app.services.events import broker

router = APIRouter(prefix="/api/events", tags=["events"])


@router.get("/drain")
def drain_events(
    _context: SessionContext = Depends(require_admin),
) -> dict[str, list[dict]]:
    # The broker is process-global and holds events from every organization, so
    # draining it is an admin-only operation.
    return {"events": broker.drain()}
