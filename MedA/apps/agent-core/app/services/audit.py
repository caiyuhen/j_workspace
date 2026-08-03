from sqlmodel import Session

from app.models import AuditEvent


def record_audit_event(
    session: Session,
    *,
    actor: str,
    organization_slug: str,
    resource_type: str,
    resource_id: str,
    action: str,
    client_type: str,
    trace_id: str,
) -> None:
    session.add(
        AuditEvent(
            actor=actor,
            organization_slug=organization_slug,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            client_type=client_type,
            trace_id=trace_id,
        )
    )
